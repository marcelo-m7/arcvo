from typing import Any

from app.core.config import settings
from app.integrations.odoo.client import OdooClient, OdooCredentials
from app.integrations.youtube import YouTubeMetadata, normalize_youtube_url
from app.schemas.archive import ArchiveCourse, ArchiveDashboard, ArchiveVideo

COURSE_FIELDS = ["id", "name", "is_published", "website_published", "nbr_video", "website_url"]
VIDEO_FIELDS = [
    "id",
    "name",
    "url",
    "video_url",
    "youtube_id",
    "description",
    "channel_id",
    "is_published",
    "website_published",
    "website_url",
    "tag_ids",
]


class ArchiveService:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def dashboard(self) -> ArchiveDashboard:
        course_count = self.client.search_count("slide.channel")
        video_count = self.client.search_count("slide.slide", [["slide_category", "=", "video"]])
        published_video_count = self.client.search_count(
            "slide.slide",
            [["slide_category", "=", "video"], ["is_published", "=", True]],
        )
        return ArchiveDashboard(
            course_count=course_count,
            video_count=video_count,
            published_video_count=published_video_count,
            draft_video_count=max(video_count - published_video_count, 0),
        )

    def list_courses(self) -> list[ArchiveCourse]:
        rows = self.client.search_read(
            "slide.channel",
            fields=COURSE_FIELDS,
            limit=100,
            offset=0,
        )
        return [self._course_from_odoo(row) for row in rows]

    def create_course(self, name: str, publish: bool = False) -> ArchiveCourse:
        course_id = self.get_or_create_course(name=name, publish=publish)
        rows = self.client.search_read(
            "slide.channel",
            domain=[["id", "=", course_id]],
            fields=COURSE_FIELDS,
            limit=1,
        )
        return self._course_from_odoo(rows[0])

    def get_or_create_course(self, name: str, publish: bool = False) -> int:
        clean_name = name.strip()
        existing = self.client.search("slide.channel", [["name", "=", clean_name]], limit=1)
        if existing:
            return existing[0]

        values = {
            "name": clean_name,
            "channel_type": "training",
            "enroll": "public",
            "visibility": "public",
            "is_published": publish,
            "website_published": publish,
        }
        return self.client.create("slide.channel", values)

    def list_videos(self) -> list[ArchiveVideo]:
        rows = self.client.search_read(
            "slide.slide",
            domain=[["slide_category", "=", "video"]],
            fields=VIDEO_FIELDS,
            limit=100,
            offset=0,
        )
        return [self._video_from_odoo(row) for row in rows]

    def create_youtube_video(
        self,
        url: str,
        course_name: str,
        title: str,
        description: str,
        publish: bool,
        tags: list[str] | None = None,
    ) -> ArchiveVideo:
        normalized_url, _video_id = normalize_youtube_url(url)
        course_id = self.get_or_create_course(course_name, publish=publish)
        tag_ids = self._get_or_create_slide_tags(tags or [])
        values: dict[str, Any] = {
            "name": title.strip(),
            "channel_id": course_id,
            "slide_category": "video",
            "slide_type": "youtube_video",
            "source_type": "external",
            "video_url": normalized_url,
            "url": normalized_url,
            "description": description,
            "is_published": publish,
            "website_published": publish,
        }
        if tag_ids:
            values["tag_ids"] = [(6, 0, tag_ids)]

        video_id = self.client.create("slide.slide", values)
        return self._get_video(video_id)

    def create_from_metadata(
        self,
        metadata: YouTubeMetadata,
        course_name: str,
        title: str,
        description: str,
        publish: bool,
        tags: list[str] | None = None,
    ) -> ArchiveVideo:
        return self.create_youtube_video(
            url=metadata.url,
            course_name=course_name,
            title=title,
            description=description,
            publish=publish,
            tags=tags,
        )

    def update_video(
        self,
        video_id: int,
        title: str | None = None,
        description: str | None = None,
        publish: bool | None = None,
        tags: list[str] | None = None,
    ) -> ArchiveVideo:
        values: dict[str, Any] = {}
        if title is not None:
            values["name"] = title.strip()
        if description is not None:
            values["description"] = description
        if publish is not None:
            values["is_published"] = publish
            values["website_published"] = publish
        if tags is not None:
            values["tag_ids"] = [(6, 0, self._get_or_create_slide_tags(tags))]
        if values:
            self.client.write("slide.slide", video_id, values)
        return self._get_video(video_id)

    def _get_video(self, video_id: int) -> ArchiveVideo:
        rows = self.client.search_read(
            "slide.slide",
            domain=[["id", "=", video_id]],
            fields=VIDEO_FIELDS,
            limit=1,
        )
        return self._video_from_odoo(rows[0])

    def _get_or_create_slide_tags(self, tags: list[str]) -> list[int]:
        tag_ids: list[int] = []
        for tag in tags:
            clean = tag.strip()
            if not clean:
                continue
            existing = self.client.search("slide.tag", [["name", "=", clean]], limit=1)
            tag_id = existing[0] if existing else self.client.create("slide.tag", {"name": clean})
            tag_ids.append(tag_id)
        return tag_ids

    def _course_from_odoo(self, row: dict[str, Any]) -> ArchiveCourse:
        return ArchiveCourse(
            id=row["id"],
            name=row["name"],
            is_published=bool(row.get("is_published")),
            website_published=bool(row.get("website_published")),
            video_count=int(row.get("nbr_video") or 0),
            website_url=row.get("website_url") or None,
        )

    def _video_from_odoo(self, row: dict[str, Any]) -> ArchiveVideo:
        channel = row.get("channel_id")
        course = tuple(channel) if isinstance(channel, list) and len(channel) == 2 else None
        return ArchiveVideo(
            id=row["id"],
            name=row["name"],
            url=row.get("url") or None,
            video_url=row.get("video_url") or None,
            youtube_id=row.get("youtube_id") or None,
            description=row.get("description") or None,
            course=course,
            is_published=bool(row.get("is_published")),
            website_published=bool(row.get("website_published")),
            website_url=row.get("website_url") or None,
            tags=row.get("tag_ids") or [],
        )


def get_archive_service() -> ArchiveService:
    credentials = OdooCredentials(
        url=settings.odoo_url,
        database=settings.odoo_db,
        username=settings.odoo_user,
        api_key=settings.odoo_api_key,
        allow_self_signed_ssl=settings.odoo_allow_self_signed_ssl,
    )
    return ArchiveService(OdooClient(credentials))
