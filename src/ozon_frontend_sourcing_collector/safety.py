from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse

ALLOWED_HOST_SUFFIXES = {
    "ozon": ("ozon.ru",),
    "1688": ("1688.com",),
    "taobao": ("taobao.com", "tmall.com"),
    "yiwugo": ("yiwugo.com",),
}

BLOCK_PATTERNS = (
    "captcha",
    "verify",
    "verification",
    "access denied",
    "too many requests",
    "security check",
    "robot check",
    "login.taobao.com",
    "sec.taobao.com",
    "punish",
    "验证码",
    "滑块",
    "安全验证",
    "登录后",
    "请登录",
    "访问受限",
    "风控",
    "подтвердите",
    "проверка",
    "доступ ограничен",
)


@dataclass(slots=True)
class SafetyGate:
    max_requests_per_host_per_run: int = 1
    request_counts: Counter[str] = field(default_factory=Counter)

    def assert_allowed_url(self, platform: str, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"unsupported URL scheme: {parsed.scheme}")
        host = (parsed.hostname or "").lower()
        allowed = ALLOWED_HOST_SUFFIXES.get(platform)
        if not allowed:
            raise ValueError(f"unsupported platform: {platform}")
        if not any(host == suffix or host.endswith("." + suffix) for suffix in allowed):
            raise ValueError(f"URL host {host!r} is not allowed for platform {platform!r}")

    def register_request(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        self.request_counts[host] += 1
        if self.request_counts[host] > self.max_requests_per_host_per_run:
            raise RuntimeError(
                f"stopped: more than {self.max_requests_per_host_per_run} request(s) to {host} in one run"
            )

    def inspect_status(self, status_code: int) -> list[str]:
        if status_code in {401, 403, 407, 429}:
            return [f"HTTP {status_code}: verification, login, rate limit, or access block required"]
        if status_code >= 500:
            return [f"HTTP {status_code}: remote service error; stop and retry later manually"]
        return []

    def inspect_text(self, text: str) -> list[str]:
        lower = text.lower()
        return [f"blocked pattern detected: {pattern}" for pattern in BLOCK_PATTERNS if pattern in lower]