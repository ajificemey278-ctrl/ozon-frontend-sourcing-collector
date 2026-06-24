from __future__ import annotations

import time

import httpx

from .models import CollectionResult, Evidence
from .parsers import parse_html_snapshot, parse_visible_text
from .safety import SafetyGate

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,zh-CN;q=0.8,en;q=0.7",
}


def collect_visible_text(platform: str, source_url: str | None, text: str) -> CollectionResult:
    return parse_visible_text(platform, source_url, text)


def collect_html_snapshot(platform: str, source_url: str | None, html: str) -> CollectionResult:
    return parse_html_snapshot(platform, source_url, html)


def fetch_public_url(
    platform: str,
    url: str,
    *,
    allow_network: bool,
    delay_seconds: float = 8.0,
    timeout_seconds: float = 20.0,
) -> CollectionResult:
    if not allow_network:
        raise RuntimeError("network fetch requires explicit --allow-network")

    gate = SafetyGate(max_requests_per_host_per_run=1)
    gate.assert_allowed_url(platform, url)
    gate.register_request(url)

    time.sleep(max(delay_seconds, 0.0))
    try:
        with httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout_seconds) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        return CollectionResult(
            platform=platform,
            source_url=url,
            status="network_error",
            blocked_reasons=[str(exc)],
        )

    status_reasons = gate.inspect_status(response.status_code)
    text_reasons = gate.inspect_text(response.text[:200_000])
    if status_reasons or text_reasons:
        return CollectionResult(
            platform=platform,
            source_url=url,
            status="verification_required",
            blocked_reasons=status_reasons + text_reasons,
            evidence=[Evidence(kind="http_status", text=str(response.status_code), confidence="high")],
        )

    return parse_html_snapshot(platform, str(response.url), response.text)