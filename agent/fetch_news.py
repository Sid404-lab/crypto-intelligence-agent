import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import requests

from config import NEWS_FEEDS, NEWS_LIMIT

HEADERS = {
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "User-Agent": "pulse-crypto-intelligence/1.0",
}

TAG_RE = re.compile(r"<[^>]+>")


def _local_name(tag):
    return tag.split("}")[-1] if tag else ""


def _child_text(node, names):
    for child in list(node):
        if _local_name(child.tag) in names:
            text = "".join(child.itertext()).strip()
            if text:
                return TAG_RE.sub("", text).strip()
    return ""


def _link(node):
    for child in list(node):
        if _local_name(child.tag) != "link":
            continue
        href = (child.get("href") or "").strip()
        if href:
            return href
        text = "".join(child.itertext()).strip()
        if text:
            return text
    return ""


def _parse_datetime(value):
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _category(title):
    text = f" {title.lower()} "
    if any(word in text for word in (" regulation", " regulator", " sec ", " lawsuit", " court", " congress", " lawmaker", " etf ")):
        return "Regulation"
    if any(word in text for word in (" listing", " listed", " lists ", " will list", " new pair")):
        return "Listings"
    return "Markets"


def _entries(root):
    entries = []
    for node in root.iter():
        if _local_name(node.tag) in ("item", "entry"):
            entries.append(node)
    return entries


def _parse_feed(source, xml_text):
    root = ET.fromstring(xml_text)
    items = []
    for node in _entries(root):
        title = _child_text(node, {"title"})
        url = _link(node)
        if not title or not url:
            continue
        published = _parse_datetime(
            _child_text(node, {"pubDate", "published", "updated", "date"})
        )
        items.append(
            {
                "title": title,
                "source": source,
                "url": url,
                "published_at": published.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "category": _category(title),
            }
        )
    return items


def _fetch_feed(feed):
    response = requests.get(feed["url"], headers=HEADERS, timeout=15)
    response.raise_for_status()
    return _parse_feed(feed["source"], response.content)


def fetch_news():
    collected = []
    errors = []
    for feed in NEWS_FEEDS:
        try:
            collected.extend(_fetch_feed(feed))
        except Exception as exc:
            errors.append(f"{feed['source']}: {exc}")

    unique = []
    seen = set()
    for item in collected:
        key = item["url"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    unique.sort(key=lambda item: item["published_at"], reverse=True)
    items = unique[:NEWS_LIMIT]
    if not items and errors:
        return None, errors
    return items, errors
