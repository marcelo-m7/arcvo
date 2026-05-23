import html
from dataclasses import dataclass, field
from typing import Any

from app.integrations.odoo.client import OdooClient

UNCATEGORIZED = "Não Classificados"


@dataclass(frozen=True)
class SupabaseVideo:
    id: str
    youtube_id: str
    title: str
    description: str | None
    channel_name: str
    thumbnail_url: str
    language: str
    category: str | None
    optimized_title: str | None
    summary_description: str | None
    short_summary: str | None
    semantic_tags: list[str] | None
    cultural_relevance: str | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SupabaseVideo":
        tags = row.get("semantic_tags")
        return cls(
            id=str(row["id"]),
            youtube_id=str(row["youtube_id"]),
            title=str(row["title"]),
            description=row.get("description"),
            channel_name=str(row.get("channel_name") or "YouTube"),
            thumbnail_url=str(row.get("thumbnail_url") or ""),
            language=str(row.get("language") or "und"),
            category=row.get("category") or UNCATEGORIZED,
            optimized_title=row.get("optimized_title"),
            summary_description=row.get("summary_description"),
            short_summary=row.get("short_summary"),
            semantic_tags=list(tags) if isinstance(tags, list) else [],
            cultural_relevance=row.get("cultural_relevance"),
        )

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def odoo_title(self) -> str:
        return (self.optimized_title or self.title).strip()

    @property
    def course_name(self) -> str:
        return (self.category or UNCATEGORIZED).strip() or UNCATEGORIZED

    @property
    def tags(self) -> list[str]:
        values = [*(self.semantic_tags or []), self.course_name, self.channel_name]
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            clean = " ".join(str(value).strip().split())
            key = clean.casefold()
            if clean and key not in seen:
                seen.add(key)
                result.append(clean[:64])
        return result[:15]


@dataclass
class ImportStats:
    total: int = 0
    courses_created: int = 0
    courses_reused: int = 0
    videos_created: int = 0
    videos_updated: int = 0
    videos_skipped: int = 0
    tags_created: int = 0
    tags_reused: int = 0
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "courses_created": self.courses_created,
            "courses_reused": self.courses_reused,
            "videos_created": self.videos_created,
            "videos_updated": self.videos_updated,
            "videos_skipped": self.videos_skipped,
            "tags_created": self.tags_created,
            "tags_reused": self.tags_reused,
            "failures": self.failures,
        }


class SupabaseOdooImporter:
    def __init__(
        self,
        client: OdooClient,
        publish: bool = True,
        update_existing: bool = True,
    ) -> None:
        self.client = client
        self.publish = publish
        self.update_existing = update_existing
        self.stats = ImportStats()
        self._course_cache: dict[str, int] = {}
        self._tag_cache: dict[str, int] = {}
        self._video_cache: dict[str, int] = {}

    def import_rows(self, rows: list[dict[str, Any]], dry_run: bool = True) -> ImportStats:
        self.stats = ImportStats(total=len(rows))
        videos = [SupabaseVideo.from_row(row) for row in rows]
        self._preload_odoo_state()

        for video in videos:
            try:
                self._import_video(video, dry_run=dry_run)
            except Exception as exc:
                self.stats.failures.append(f"{video.youtube_id}: {exc}")

        return self.stats

    def _import_video(self, video: SupabaseVideo, dry_run: bool) -> None:
        existing = self._find_existing_video(video)
        if existing and not self.update_existing:
            self.stats.videos_skipped += 1
            return

        course_id = self._get_or_create_course(video, dry_run=dry_run)
        tag_ids = self._get_or_create_tags(video.tags, dry_run=dry_run)
        values = self._video_values(video, course_id=course_id, tag_ids=tag_ids)

        if existing:
            if dry_run:
                self.stats.videos_updated += 1
                return
            self.client.write("slide.slide", existing[0], values)
            self.stats.videos_updated += 1
            return

        if dry_run:
            self.stats.videos_created += 1
            return

        self.client.create("slide.slide", values)
        self.stats.videos_created += 1

    def _find_existing_video(self, video: SupabaseVideo) -> list[int]:
        existing = self._video_cache.get(video.youtube_url)
        return [existing] if existing else []

    def _get_or_create_course(self, video: SupabaseVideo, dry_run: bool) -> int:
        name = video.course_name
        if name in self._course_cache:
            self.stats.courses_reused += 1
            return self._course_cache[name]

        existing = self._course_cache.get(name)
        if existing:
            self.stats.courses_reused += 1
            if not dry_run:
                self.client.write("slide.channel", existing, self._course_values(name))
            return existing

        self.stats.courses_created += 1
        if dry_run:
            dry_id = -len(self._course_cache) - 1
            self._course_cache[name] = dry_id
            return dry_id

        course_id = self.client.create("slide.channel", self._course_values(name))
        self._course_cache[name] = course_id
        return course_id

    def _get_or_create_tags(self, tags: list[str], dry_run: bool) -> list[int]:
        tag_ids: list[int] = []
        for tag in tags:
            if tag in self._tag_cache:
                self.stats.tags_reused += 1
                tag_ids.append(self._tag_cache[tag])
                continue
            existing = self._tag_cache.get(tag)
            if existing:
                self.stats.tags_reused += 1
                tag_ids.append(existing)
                continue
            self.stats.tags_created += 1
            if dry_run:
                dry_id = -len(self._tag_cache) - 1
                self._tag_cache[tag] = dry_id
                tag_ids.append(dry_id)
                continue
            tag_id = self.client.create("slide.tag", {"name": tag})
            self._tag_cache[tag] = tag_id
            tag_ids.append(tag_id)
        return tag_ids

    def _preload_odoo_state(self) -> None:
        channels = self.client.search_read("slide.channel", fields=["id", "name"], limit=10000)
        self._course_cache = {str(row["name"]): int(row["id"]) for row in channels}

        tags = self.client.search_read("slide.tag", fields=["id", "name"], limit=10000)
        self._tag_cache = {str(row["name"]): int(row["id"]) for row in tags}

        slides = self.client.search_read(
            "slide.slide",
            domain=[["slide_category", "=", "video"]],
            fields=["id", "video_url", "url"],
            limit=10000,
        )
        video_cache: dict[str, int] = {}
        for slide in slides:
            slide_id = int(slide["id"])
            for key in [slide.get("video_url"), slide.get("url")]:
                if key:
                    video_cache[str(key)] = slide_id
        self._video_cache = video_cache

    def _course_values(self, name: str) -> dict[str, Any]:
        description = (
            f"<p>Curso importado do acervo Supabase Open2 para o eLearning Odoo.</p>"
            f"<p>Categoria original: <strong>{html.escape(name)}</strong>.</p>"
        )
        return {
            "name": name,
            "channel_type": "training",
            "enroll": "public",
            "visibility": "public",
            "description": description,
            "description_short": f"Acervo YouTube: {name}",
            "description_html": description,
            "website_meta_title": f"{name} | Acervo YouTube",
            "website_meta_description": f"Curso gerado a partir da categoria {name} do acervo.",
            "is_published": self.publish,
            "website_published": self.publish,
        }

    def _video_values(
        self,
        video: SupabaseVideo,
        course_id: int,
        tag_ids: list[int],
    ) -> dict[str, Any]:
        values: dict[str, Any] = {
            "name": video.odoo_title,
            "channel_id": course_id,
            "slide_category": "video",
            "slide_type": "youtube_video",
            "source_type": "external",
            "video_url": video.youtube_url,
            "url": video.youtube_url,
            "description": self._video_description(video),
            "website_meta_title": video.odoo_title,
            "website_meta_description": (
                video.short_summary or video.summary_description or video.title
            )[:300],
            "website_meta_keywords": ", ".join(video.tags),
            "website_meta_og_img": video.thumbnail_url,
            "is_published": self.publish,
            "website_published": self.publish,
        }
        if tag_ids:
            values["tag_ids"] = [(6, 0, tag_ids)]
        return values

    def _video_description(self, video: SupabaseVideo) -> str:
        parts = [
            f"<p>{html.escape(video.summary_description or video.description or video.title)}</p>",
        ]
        if video.short_summary:
            short_summary = html.escape(video.short_summary)
            parts.append(f"<p><strong>Resumo curto:</strong> {short_summary}</p>")
        parts.append("<ul>")
        parts.append(f"<li><strong>Título original:</strong> {html.escape(video.title)}</li>")
        parts.append(f"<li><strong>Canal:</strong> {html.escape(video.channel_name)}</li>")
        parts.append(f"<li><strong>Idioma:</strong> {html.escape(video.language)}</li>")
        parts.append(f"<li><strong>Categoria:</strong> {html.escape(video.course_name)}</li>")
        if video.cultural_relevance:
            parts.append(
                f"<li><strong>Relevância cultural:</strong> "
                f"{html.escape(video.cultural_relevance)}</li>"
            )
        parts.append(
            f'<li><strong>YouTube:</strong> '
            f'<a href="{video.youtube_url}">{video.youtube_url}</a></li>'
        )
        parts.append("</ul>")
        if video.tags:
            parts.append(f"<p><strong>Tags:</strong> {html.escape(', '.join(video.tags))}</p>")
        return "".join(parts)
