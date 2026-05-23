from typing import Any

from app.services.archive_service import ArchiveService


class FakeOdooClient:
    def __init__(self) -> None:
        self.created: list[tuple[str, dict[str, Any]]] = []
        self.search_results: list[int] = []

    def search(
        self,
        model: str,
        domain: list[Any] | None = None,
        limit: int | None = None,
    ) -> list[int]:
        return self.search_results

    def create(self, model: str, values: dict[str, Any]) -> int:
        self.created.append((model, values))
        return len(self.created)

    def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": 1,
                "name": "Video",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "youtube_id": "dQw4w9WgXcQ",
                "description": "Description",
                "channel_id": [1, "Course"],
                "is_published": False,
                "website_published": False,
                "website_url": "/slides/video-1",
                "tag_ids": [],
            }
        ]


def test_create_youtube_video_builds_elearning_payload() -> None:
    client = FakeOdooClient()
    service = ArchiveService(client)  # type: ignore[arg-type]

    service.create_youtube_video(
        url="https://youtu.be/dQw4w9WgXcQ",
        course_name="Pajuba",
        title="Video",
        description="Description",
        publish=False,
        tags=[],
    )

    course_model, course_values = client.created[0]
    video_model, video_values = client.created[1]
    assert course_model == "slide.channel"
    assert course_values["channel_type"] == "training"
    assert course_values["enroll"] == "public"
    assert course_values["visibility"] == "public"
    assert video_model == "slide.slide"
    assert video_values["slide_category"] == "video"
    assert video_values["slide_type"] == "youtube_video"
    assert video_values["source_type"] == "external"
    assert video_values["video_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
