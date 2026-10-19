"""Vendor-neutral repair research media planner and presentation contract.

This is a SOURCE-ONLY adapter boundary: it does not browse YouTube/Google/
Yandex, authenticate provider APIs, download video or images, or display a UI.
Network clients and actual playback belong to the existing authorized Main
provider gateway and platform-specific UI; no duplicate research brain.
"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import re
from urllib.parse import parse_qs, urlsplit, urlunsplit

PROVIDERS = frozenset({
    "YOUTUBE", "GOOGLE", "YANDEX", "OEM", "TECHNICAL_FORUM",
    "GENERAL_WEB", "OTHER_VERIFIED",
})
MEDIA_TYPES = frozenset({"VIDEO", "IMAGE", "DOCUMENT", "WEBPAGE"})
ROLES = frozenset({"REPAIR", "EDUCATION"})
SOURCE_TIERS = frozenset({
    "MATCHED_OEM_MANUAL", "MATCHED_DATASHEET", "VERIFIED_SERVICE_BULLETIN",
    "UNVERIFIED_TUTORIAL", "COMMUNITY_EXPERIENCE", "UNKNOWN",
})
PROVIDER_HINTS = {
    "YOUTUBE": "OFFICIAL_YOUTUBE_DATA_API",
    "GOOGLE": "VERIFY_CURRENT_SUPPORTED_SEARCH_ACCESS",
    "YANDEX": "VERIFY_YANDEX_SEARCH_API_ACCOUNT_AND_TERMS",
    "OEM": "AUTHORIZED_OEM_DOCUMENT_RESOLVER",
    "TECHNICAL_FORUM": "RESPECT_SITE_API_AND_TERMS",
    "GENERAL_WEB": "CONFIGURED_LEGAL_SEARCH_PROVIDER",
    "OTHER_VERIFIED": "OWNER_APPROVED_CONNECTOR",
}
_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_BANNED_HOSTS = {"localhost", "localhost.localdomain", "metadata.google.internal"}


@dataclass(frozen=True)
class ResearchRequest:
    request_id: str
    purpose: str
    query: str
    authorized: bool
    internet_consent: bool
    providers: tuple[str, ...] = ("YOUTUBE", "GOOGLE", "YANDEX", "OEM")
    languages: tuple[str, ...] = ("tr", "en", "de")
    include_media: tuple[str, ...] = ("VIDEO", "IMAGE", "DOCUMENT", "WEBPAGE")
    contains_personal_device_data: bool = False


@dataclass(frozen=True)
class ProviderResearchPlan:
    state: str
    reason: str
    planned_providers: tuple[str, ...] = ()
    adapter_hints: tuple[tuple[str, str], ...] = ()
    query: str | None = None
    network_performed: bool = False
    video_or_image_rendered: bool = False
    source_only: bool = True


def plan_research(request: ResearchRequest) -> ProviderResearchPlan:
    """Plan non-secret queries for provider adapters. Does not search."""
    def stop(status: str, reason: str) -> ProviderResearchPlan:
        return ProviderResearchPlan(status, reason)
    if not isinstance(request, ResearchRequest):
        return stop("BLOCKED", "INVALID_REQUEST")
    if not isinstance(request.request_id, str) or not _KEY.fullmatch(request.request_id):
        return stop("BLOCKED", "INVALID_REQUEST_ID")
    if request.purpose not in ROLES:
        return stop("BLOCKED", "INVALID_RESEARCH_PURPOSE")
    if any(type(b) is not bool for b in (
        request.authorized, request.internet_consent,
        request.contains_personal_device_data
    )):
        return stop("BLOCKED", "INVALID_CONSENT_FLAGS")
    if not request.authorized:
        return stop("BLOCKED", "MAIN_AUTH_REQUIRED")
    if not request.internet_consent:
        return stop("BLOCKED", "EXTERNAL_SEARCH_CONSENT_REQUIRED")
    if request.contains_personal_device_data:
        return stop("BLOCKED", "REMOVE_IDENTIFIERS_BEFORE_EXTERNAL_SEARCH")
    if (not isinstance(request.query, str) or not 2 <= len(request.query.strip()) <= 250
        or any(ord(c) < 32 for c in request.query)):
        return stop("BLOCKED", "INVALID_QUERY")
    if (not isinstance(request.providers, (tuple, list)) or not request.providers
        or len(request.providers) > len(PROVIDERS)
        or any(p not in PROVIDERS for p in request.providers)
        or len(set(request.providers)) != len(request.providers)):
        return stop("BLOCKED", "INVALID_PROVIDER_LIST")
    if (not isinstance(request.languages, (tuple, list))
        or not request.languages or len(request.languages) > 8
        or any(not isinstance(l, str) or not re.fullmatch(r"[a-z]{2,3}", l)
               for l in request.languages)):
        return stop("BLOCKED", "INVALID_LANGUAGES")
    if (not isinstance(request.include_media, (tuple, list))
        or not request.include_media
        or any(m not in MEDIA_TYPES for m in request.include_media)):
        return stop("BLOCKED", "INVALID_MEDIA_TYPES")
    return ProviderResearchPlan(
        state="SOURCE_PLAN_ONLY", reason="GATEWAY_MUST_SEARCH_AND_ATTEST",
        planned_providers=tuple(request.providers),
        adapter_hints=tuple((p, PROVIDER_HINTS[p]) for p in request.providers),
        query=request.query.strip(),
    )


@dataclass(frozen=True)
class MediaCandidate:
    item_id: str
    provider: str
    media_type: str
    title: str
    source_url: str
    source_tier: str = "UNKNOWN"
    host_source_verified: bool = False
    device_revision_matched: bool = False
    embeddable_verified: bool = False
    display_allowed: bool = False
    external_thumbnail_url: str | None = None


@dataclass(frozen=True)
class MediaCard:
    item_id: str
    provider: str
    media_type: str
    title: str
    url: str
    presentation: str
    source_tier: str
    source_verified: bool
    device_revision_matched: bool
    preview_url: str | None = None
    thumbnail_url: str | None = None
    factually_authoritative: bool = False
    user_must_open_or_start_player: bool = True
    may_download_media: bool = False
    may_change_repair_plan: bool = False
    source_only: bool = True


@dataclass(frozen=True)
class MediaCollection:
    state: str
    cards: tuple[MediaCard, ...]
    rejected_count: int
    network_performed: bool = False
    media_rendered: bool = False
    source_only: bool = True


def _url(raw: object) -> str | None:
    """Validate a public https URL, never fetch; prevent scheme/host tricks."""
    if not isinstance(raw, str) or len(raw) > 2048:
        return None
    if any(ord(x) < 32 for x in raw) or "\\" in raw:
        return None
    try:
        u = urlsplit(raw)
        if u.scheme != "https" or not u.hostname or u.username or u.password:
            return None
        host = u.hostname.lower().rstrip(".")
        if host in _BANNED_HOSTS or not host or "." not in host:
            return None
        if host.endswith((".local", ".internal", ".localhost", ".test", ".invalid")):
            return None
        try:
            address = ip_address(host)
            if not address.is_global:
                return None
        except ValueError:
            # A domain isn't inherently trustworthy; only allowed to open
            # via host browser with further redirect/SSRF review.
            if not re.fullmatch(r"[a-z0-9.-]{3,253}", host) or ".." in host:
                return None
        if u.port not in (None, 443):
            return None
        return urlunsplit(("https", u.netloc.lower(), u.path or "/", u.query, ""))
    except (ValueError, TypeError):
        return None


def _youtube_id(url: str) -> str | None:
    u = urlsplit(url)
    host = (u.hostname or "").lower()
    candidate: str | None = None
    if host in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if u.path == "/watch":
            values = parse_qs(u.query).get("v", ())
            candidate = values[0] if len(values) == 1 else None
    elif host == "youtu.be":
        candidate = u.path.strip("/")
    return candidate if candidate and _VIDEO_ID.fullmatch(candidate) else None


def prepare_media_cards(candidates: object) -> MediaCollection:
    """Normalize already-retrieved hits for the app display, not web search.

    A result is not medical/electrical/automotive truth. OEM-level confidence
    requires separately verified provenance AND exact device revision.
    YouTube embed is only proposed when a legitimate video id is given AND
    host metadata says embedding is enabled. Actual UI still must verify.
    """
    if not isinstance(candidates, (list, tuple)) or len(candidates) > 100:
        return MediaCollection("INVALID_BATCH", (), 0)
    cards: list[MediaCard] = []
    seen: set[tuple[str, str]] = set()
    rejected = 0
    for c in candidates:
        if (not isinstance(c, MediaCandidate)
            or not isinstance(c.item_id, str) or not _KEY.fullmatch(c.item_id)
            or c.provider not in PROVIDERS or c.media_type not in MEDIA_TYPES
            or c.source_tier not in SOURCE_TIERS
            or not isinstance(c.title, str)
            or not 1 <= len(c.title.strip()) <= 250
            or any(ord(x) < 32 for x in c.title)):
            rejected += 1
            continue
        flags = (c.host_source_verified, c.device_revision_matched,
                 c.embeddable_verified, c.display_allowed)
        if any(type(flag) is not bool for flag in flags) or not c.display_allowed:
            rejected += 1
            continue
        source = _url(c.source_url)
        if not source:
            rejected += 1
            continue
        key = (c.media_type, source)
        if key in seen:
            rejected += 1
            continue
        # Provider-specific preview requires an official YouTube URL,
        # NOT an attacker-controlled page with a YouTube-looking video id.
        video_id = _youtube_id(source) if c.provider == "YOUTUBE" else None
        if c.provider == "YOUTUBE" and (c.media_type != "VIDEO" or not video_id):
            rejected += 1
            continue
        thumbnail = _url(c.external_thumbnail_url) if c.external_thumbnail_url else None
        preview = None
        if video_id and c.embeddable_verified:
            preview = "https://www.youtube.com/embed/" + video_id
            presentation = "OFFICIAL_EMBED_OPTION"
        elif c.media_type == "IMAGE":
            presentation = "HOST_SANDBOXED_IMAGE_PREVIEW"
        elif c.media_type == "DOCUMENT":
            presentation = "DOCUMENT_PREVIEW_OR_SOURCE_LINK"
        else:
            presentation = "SOURCE_LINK"
        authoritative = (
            c.host_source_verified and c.device_revision_matched
            and c.source_tier in {
                "MATCHED_OEM_MANUAL", "MATCHED_DATASHEET",
                "VERIFIED_SERVICE_BULLETIN"
            }
        )
        cards.append(MediaCard(
            item_id=c.item_id, provider=c.provider, media_type=c.media_type,
            title=c.title.strip(), url=source,
            presentation=presentation, source_tier=c.source_tier,
            source_verified=c.host_source_verified,
            device_revision_matched=c.device_revision_matched,
            preview_url=preview, thumbnail_url=thumbnail,
            factually_authoritative=authoritative,
        ))
        seen.add(key)
    return MediaCollection("SOURCE_CARDS_ONLY", tuple(cards), rejected)
