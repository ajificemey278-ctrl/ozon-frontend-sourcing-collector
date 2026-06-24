from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Evidence:
    kind: str
    text: str
    confidence: str = "medium"
    source: str | None = None


@dataclass(slots=True)
class ProductItem:
    title: str | None = None
    price_text: str | None = None
    currency: str | None = None
    price_value: float | None = None
    rating: str | None = None
    reviews_text: str | None = None
    sales_text: str | None = None
    delivery_text: str | None = None
    shop_name: str | None = None
    product_id: str | None = None
    product_url: str | None = None
    image_urls: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CollectionResult:
    platform: str
    source_url: str | None
    status: str
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    page_type: str | None = None
    items: list[ProductItem] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)