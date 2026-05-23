from typing import Any

import httpx


class SupabaseClientError(RuntimeError):
    pass


class SupabaseArchiveClient:
    def __init__(self, url: str, publishable_key: str) -> None:
        self.url = url.rstrip("/")
        self.publishable_key = publishable_key

    def fetch_youtube_archive(self) -> list[dict[str, Any]]:
        videos = self._get_all(
            "videos",
            {
                "select": (
                    "id,youtube_id,title,description,channel_name,duration_seconds,"
                    "thumbnail_url,language,created_at,categories(name,slug)"
                ),
                "order": "created_at.asc",
            },
        )
        enrichments = self._get_all(
            "ai_enrichments",
            {
                "select": (
                    "video_id,optimized_title,summary_description,semantic_tags,"
                    "suggested_category_id,language,cultural_relevance,short_summary,"
                    "created_at,reprocessed_at"
                ),
            },
        )
        latest_by_video = self._latest_enrichments(enrichments)
        rows: list[dict[str, Any]] = []
        for video in videos:
            category = video.get("categories") or {}
            enrichment = latest_by_video.get(video["id"], {})
            rows.append(
                {
                    "id": video["id"],
                    "youtube_id": video["youtube_id"],
                    "title": video["title"],
                    "description": video.get("description"),
                    "channel_name": video.get("channel_name"),
                    "duration_seconds": video.get("duration_seconds"),
                    "thumbnail_url": video.get("thumbnail_url"),
                    "language": enrichment.get("language") or video.get("language"),
                    "category": category.get("name"),
                    "category_slug": category.get("slug"),
                    "optimized_title": enrichment.get("optimized_title"),
                    "summary_description": enrichment.get("summary_description"),
                    "short_summary": enrichment.get("short_summary"),
                    "semantic_tags": enrichment.get("semantic_tags") or [],
                    "cultural_relevance": enrichment.get("cultural_relevance"),
                }
            )
        return rows

    def _get_all(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        page_size = 1000
        headers = {
            "apikey": self.publishable_key,
            "Authorization": f"Bearer {self.publishable_key}",
            "Accept": "application/json",
        }
        with httpx.Client(timeout=60, headers=headers) as client:
            while True:
                query = {**params, "limit": str(page_size), "offset": str(offset)}
                response = client.get(f"{self.url}/rest/v1/{table}", params=query)
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise SupabaseClientError(response.text) from exc
                page = response.json()
                if not isinstance(page, list):
                    raise SupabaseClientError(f"Unexpected Supabase response for {table}")
                rows.extend(page)
                if len(page) < page_size:
                    return rows
                offset += page_size

    def _latest_enrichments(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in rows:
            video_id = row.get("video_id")
            if not video_id:
                continue
            current = latest.get(video_id)
            if current is None or self._row_timestamp(row) > self._row_timestamp(current):
                latest[video_id] = row
        return latest

    def _row_timestamp(self, row: dict[str, Any]) -> str:
        return str(row.get("reprocessed_at") or row.get("created_at") or "")
