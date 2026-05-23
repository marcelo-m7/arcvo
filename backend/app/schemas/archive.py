from typing import Any

from pydantic import BaseModel, Field


class ArchiveCourse(BaseModel):
    id: int
    name: str
    is_published: bool = False
    website_published: bool = False
    video_count: int = 0
    website_url: str | None = None


class ArchiveCourseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    publish: bool = False


class YouTubePreviewRequest(BaseModel):
    url: str = Field(min_length=8)


class YouTubePreview(BaseModel):
    url: str
    video_id: str
    title: str | None = None
    author_name: str | None = None
    thumbnail_url: str | None = None
    provider_name: str | None = None
    fetched: bool = False


class YouTubeVideoCreate(BaseModel):
    url: str = Field(min_length=8)
    course_name: str = Field(min_length=2, max_length=160)
    title: str = Field(min_length=2, max_length=220)
    description: str = ""
    publish: bool = False
    tags: list[str] = Field(default_factory=list)


class YouTubeVideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = None
    publish: bool | None = None
    tags: list[str] | None = None


class ArchiveVideo(BaseModel):
    id: int
    name: str
    url: str | None = None
    video_url: str | None = None
    youtube_id: str | None = None
    description: str | None = None
    course: tuple[int, str] | None = None
    is_published: bool = False
    website_published: bool = False
    website_url: str | None = None
    tags: list[Any] = Field(default_factory=list)


class ArchiveDashboard(BaseModel):
    course_count: int
    video_count: int
    published_video_count: int
    draft_video_count: int
