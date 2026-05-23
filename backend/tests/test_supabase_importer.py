from typing import Any

from app.services.supabase_importer import SupabaseOdooImporter, SupabaseVideo


class FakeOdooClient:
    def __init__(self) -> None:
        self.searches: list[tuple[str, list[Any] | None]] = []
        self.created: list[tuple[str, dict[str, Any]]] = []
        self.writes: list[tuple[str, int, dict[str, Any]]] = []
        self.existing_video: list[int] = []
        self.existing_course: list[int] = []
        self.existing_tag: list[int] = []

    def search(
        self,
        model: str,
        domain: list[Any] | None = None,
        limit: int | None = None,
    ) -> list[int]:
        self.searches.append((model, domain))
        if model == "slide.slide":
            return self.existing_video
        if model == "slide.channel":
            return self.existing_course
        if model == "slide.tag":
            return self.existing_tag
        return []

    def create(self, model: str, values: dict[str, Any]) -> int:
        self.created.append((model, values))
        return len(self.created)

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool:
        self.writes.append((model, record_id, values))
        return True

    def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if model == "slide.channel":
            return (
                [{"id": self.existing_course[0], "name": "Educação"}]
                if self.existing_course
                else []
            )
        if model == "slide.tag":
            return [{"id": self.existing_tag[0], "name": "tag one"}] if self.existing_tag else []
        if model == "slide.slide":
            if self.existing_video:
                return [
                    {
                        "id": self.existing_video[0],
                        "video_url": "https://www.youtube.com/watch?v=abc12345678",
                        "url": "https://www.youtube.com/watch?v=abc12345678",
                    }
                ]
            return []
        return []


def sample_row() -> dict[str, Any]:
    return {
        "id": "video-id",
        "youtube_id": "abc12345678",
        "title": "Original title",
        "description": "Original description",
        "channel_name": "Canal",
        "thumbnail_url": "https://img.youtube.com/vi/abc12345678/maxresdefault.jpg",
        "language": "pt",
        "category": "Educação",
        "optimized_title": "Optimized title",
        "summary_description": "AI summary",
        "short_summary": "Short AI summary",
        "semantic_tags": ["tag one", "tag two"],
        "cultural_relevance": "High",
    }


def test_supabase_video_prefers_ai_enrichment() -> None:
    video = SupabaseVideo.from_row(sample_row())
    assert video.odoo_title == "Optimized title"
    assert video.course_name == "Educação"
    assert "tag one" in video.tags
    assert "Educação" in video.tags


def test_importer_dry_run_builds_course_and_video_counts() -> None:
    client = FakeOdooClient()
    importer = SupabaseOdooImporter(client)  # type: ignore[arg-type]

    stats = importer.import_rows([sample_row()], dry_run=True)

    assert stats.total == 1
    assert stats.courses_created == 1
    assert stats.videos_created == 1
    assert stats.tags_created == 4
    assert client.created == []


def test_importer_updates_existing_video_without_duplicate() -> None:
    client = FakeOdooClient()
    client.existing_video = [99]
    client.existing_course = [10]
    importer = SupabaseOdooImporter(client)  # type: ignore[arg-type]

    stats = importer.import_rows([sample_row()], dry_run=False)

    assert stats.videos_updated == 1
    assert stats.videos_created == 0
    assert client.writes[-1][0] == "slide.slide"
    assert client.writes[-1][1] == 99
