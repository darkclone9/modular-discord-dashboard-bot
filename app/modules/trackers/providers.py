from datetime import datetime
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.modules.trackers.models import SocialTracker
from app.modules.trackers.service import TrackerItem

log = structlog.get_logger(__name__)

ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/schemas/2015}"
SUPPORTED_POLLING_PROVIDERS = {"youtube"}


async def fetch_latest_tracker_item(tracker: SocialTracker) -> TrackerItem | None:
    if tracker.provider == "youtube":
        return await fetch_latest_youtube_upload(tracker.source_id, tracker.source_url)
    log.info("tracker_provider_not_implemented", provider=tracker.provider, tracker_id=tracker.id)
    return None


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, TimeoutError, ConnectionError)),
    wait=wait_exponential_jitter(initial=0.5, max=5),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def fetch_latest_youtube_upload(
    source_id: str,
    source_url: str | None = None,
) -> TrackerItem | None:
    channel_id = extract_youtube_channel_id(source_id) or extract_youtube_channel_id(
        source_url or ""
    )
    if channel_id is None:
        log.warning("youtube_tracker_missing_channel_id", source_id=source_id)
        return None

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://www.youtube.com/feeds/videos.xml",
            params={"channel_id": channel_id},
        )
        response.raise_for_status()
    return parse_youtube_feed(response.text)


def extract_youtube_channel_id(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if value.startswith("UC") and len(value) >= 20:
        return value

    parsed = urlparse(value)
    if not parsed.netloc:
        return None
    query_channel = parse_qs(parsed.query).get("channel_id")
    if query_channel:
        return query_channel[0]
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "channel" and parts[1].startswith("UC"):
        return parts[1]
    return None


def parse_youtube_feed(xml_text: str) -> TrackerItem | None:
    root = ElementTree.fromstring(xml_text)
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        return None

    video_id = text_of(entry, f"{YT}videoId") or text_of(entry, f"{ATOM}id")
    title = text_of(entry, f"{ATOM}title") or "New YouTube upload"
    link = entry.find(f"{ATOM}link")
    url = link.attrib.get("href", "") if link is not None else ""
    published_at = parse_datetime(text_of(entry, f"{ATOM}published"))
    if not video_id or not url:
        return None
    return TrackerItem(
        external_id=video_id,
        title=title,
        url=url,
        published_at=published_at,
    )


def text_of(element: ElementTree.Element, path: str) -> str | None:
    found = element.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip()


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
