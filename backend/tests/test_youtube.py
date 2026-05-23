import pytest

from app.integrations.youtube import YouTubeUrlError, normalize_youtube_url


@pytest.mark.parametrize(
    ("raw_url", "video_id"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_normalize_youtube_url(raw_url: str, video_id: str) -> None:
    normalized, parsed_id = normalize_youtube_url(raw_url)
    assert parsed_id == video_id
    assert normalized == f"https://www.youtube.com/watch?v={video_id}"


def test_normalize_youtube_url_rejects_invalid_url() -> None:
    with pytest.raises(YouTubeUrlError):
        normalize_youtube_url("https://example.com/video")
