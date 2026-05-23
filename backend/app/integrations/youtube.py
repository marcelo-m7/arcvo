from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx


class YouTubeUrlError(ValueError):
    pass


@dataclass(frozen=True)
class YouTubeMetadata:
    url: str
    video_id: str
    title: str | None = None
    author_name: str | None = None
    thumbnail_url: str | None = None
    provider_name: str | None = None
    fetched: bool = False


def normalize_youtube_url(raw_url: str) -> tuple[str, str]:
    parsed = urlparse(raw_url.strip())
    host = parsed.netloc.lower().removeprefix("www.")

    video_id: str | None = None
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else None
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else None

    if not video_id or len(video_id) < 6:
        raise YouTubeUrlError("Invalid YouTube video URL")

    query = urlencode({"v": video_id})
    normalized = urlunparse(("https", "www.youtube.com", "/watch", "", query, ""))
    return normalized, video_id


async def fetch_youtube_metadata(raw_url: str) -> YouTubeMetadata:
    normalized_url, video_id = normalize_youtube_url(raw_url)
    endpoint = "https://www.youtube.com/oembed"
    params = {"url": normalized_url, "format": "json"}

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return YouTubeMetadata(url=normalized_url, video_id=video_id)

    return YouTubeMetadata(
        url=normalized_url,
        video_id=video_id,
        title=data.get("title"),
        author_name=data.get("author_name"),
        thumbnail_url=data.get("thumbnail_url"),
        provider_name=data.get("provider_name"),
        fetched=True,
    )
