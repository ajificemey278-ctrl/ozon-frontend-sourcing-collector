from __future__ import annotations

import json
import re
from collections.abc import Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import CollectionResult, Evidence, ProductItem
from .safety import SafetyGate

PRICE_SYMBOL_BEFORE_RE = re.compile(r"(?P<symbol>[¥￥₽$])\s*(?P<value>\d+(?:[\s.,]\d+)*)")
PRICE_SYMBOL_AFTER_RE = re.compile(r"(?P<value>\d+(?:[\s.,]\d+)*)\s*(?P<symbol>[¥￥₽$])")
RATING_RE = re.compile(r"(?:рейтинг|rating|评分|星级)[:：\s]*([0-5](?:[.,]\d)?)", re.I)
REVIEWS_RE = re.compile(r"(\d+[\d\s.,]*\s*(?:отзыв\w*|reviews?|评价|好评))", re.I)
SALES_RE = re.compile(r"(已售\s*\d+[\d\s.,万+]*|\d+[\d\s.,万+]*\s*(?:件|pcs|шт)\s*(?:已售|sold)?)", re.I)
DELIVERY_RE = re.compile(
    r"(завтра|сегодня|\d{1,2}\s+[а-яё]+|достав\w+[^\n]{0,40}|包邮|运费[^\n]{0,20}|发货[^\n]{0,20})",
    re.I,
)
PRODUCT_ID_PATTERNS = (
    re.compile(r"/product/[^/?#]*-(\d+)(?:[/?#]|$)", re.I),
    re.compile(r"offer/(\d+)\.html", re.I),
    re.compile(r"id=(\d+)", re.I),
    re.compile(r"item/(\d+)\.html", re.I),
)


def clean_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def detect_currency(price_text: str | None) -> str | None:
    if not price_text:
        return None
    if "¥" in price_text or "￥" in price_text:
        return "CNY"
    if "₽" in price_text:
        return "RUB"
    if "$" in price_text:
        return "USD"
    return None


def _normalise_number(value_text: str) -> float | None:
    value_text = value_text.replace(" ", "").replace(",", ".")
    try:
        return float(value_text)
    except ValueError:
        return None


def parse_price(text: str) -> tuple[str | None, str | None, float | None]:
    candidates = []
    for pattern in (PRICE_SYMBOL_AFTER_RE, PRICE_SYMBOL_BEFORE_RE):
        for match in pattern.finditer(text):
            value = _normalise_number(match.group("value"))
            if value is None:
                continue
            price_text = clean_text(match.group(0))
            candidates.append((price_text, detect_currency(price_text), value, match.start()))
    if not candidates:
        return None, None, None
    candidates.sort(key=lambda item: item[3])
    price_text, currency, value, _ = candidates[0]
    return price_text, currency, value


def extract_product_id(url: str | None) -> str | None:
    if not url:
        return None
    for pattern in PRODUCT_ID_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def iter_json_ld(soup: BeautifulSoup) -> Iterable[dict]:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            yield data
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item


def meta_content(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(tag["content"])
    return None


def collect_images(soup: BeautifulSoup, base_url: str | None, limit: int = 12) -> list[str]:
    images: list[str] = []
    for tag in soup.find_all("img"):
        src = tag.get("src") or tag.get("data-src") or tag.get("data-original")
        if not src:
            continue
        full = urljoin(base_url or "", src)
        if full not in images:
            images.append(full)
        if len(images) >= limit:
            break
    return images


def extract_common_fields(text: str) -> dict[str, str | float | None]:
    price_text, currency, price_value = parse_price(text)
    rating_match = RATING_RE.search(text)
    reviews_match = REVIEWS_RE.search(text)
    sales_match = SALES_RE.search(text)
    delivery_match = DELIVERY_RE.search(text)
    return {
        "price_text": price_text,
        "currency": currency,
        "price_value": price_value,
        "rating": clean_text(rating_match.group(1)) if rating_match else None,
        "reviews_text": clean_text(reviews_match.group(1)) if reviews_match else None,
        "sales_text": clean_text(sales_match.group(1)) if sales_match else None,
        "delivery_text": clean_text(delivery_match.group(1)) if delivery_match else None,
    }


def extract_attribute_hints(text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    patterns = {
        "dimension": r"\d+(?:[.,]\d+)?\s*[xх*×]\s*\d+(?:[.,]\d+)?\s*(?:см|cm|厘米|mm|мм)",
        "weight": r"\d+(?:[.,]\d+)?\s*(?:g|kg|г|кг|克|千克)",
        "battery": r"\d+\s*(?:mah|мАч|毫安|mAh)",
        "quantity": r"\d+\s*(?:шт|pcs|件|个|只|张)",
        "remote": r"(?:пульт|遥控|remote)",
        "usb": r"(?:usb|USB|юсб)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        if match:
            hints[key] = clean_text(match.group(0))
    return hints


def parse_visible_text(platform: str, source_url: str | None, text: str) -> CollectionResult:
    gate = SafetyGate()
    blocked = gate.inspect_text(text)
    if blocked:
        return CollectionResult(
            platform=platform,
            source_url=source_url,
            status="verification_required",
            blocked_reasons=blocked,
            evidence=[Evidence(kind="visible_text", text=text[:500], confidence="high")],
        )

    fields = extract_common_fields(text)
    item = ProductItem(
        title=clean_text(text.splitlines()[0] if text.splitlines() else text[:160])[:220],
        product_id=extract_product_id(source_url),
        product_url=source_url,
        attributes=extract_attribute_hints(text),
        evidence=[Evidence(kind="visible_text", text=text[:1000], confidence="medium")],
        **fields,
    )
    return CollectionResult(
        platform=platform,
        source_url=source_url,
        status="ok",
        page_type="visible_text",
        items=[item],
    )


def parse_html_snapshot(platform: str, source_url: str | None, html: str) -> CollectionResult:
    gate = SafetyGate()
    blocked = gate.inspect_text(html[:200_000])
    if blocked:
        return CollectionResult(
            platform=platform,
            source_url=source_url,
            status="verification_required",
            blocked_reasons=blocked,
            evidence=[Evidence(kind="html", text=clean_text(html[:500]), confidence="high")],
        )

    soup = BeautifulSoup(html, "lxml")
    full_text = clean_text(soup.get_text(" ", strip=True))
    title = meta_content(soup, "og:title", "twitter:title")
    if not title and soup.title:
        title = clean_text(soup.title.get_text(" ", strip=True))
    description = meta_content(soup, "og:description", "description")
    page_url = meta_content(soup, "og:url") or source_url
    fields = extract_common_fields(" ".join(x for x in (title, description, full_text[:5000]) if x))

    jsonld_items = list(iter_json_ld(soup))
    for data in jsonld_items:
        if data.get("name") and not title:
            title = clean_text(str(data["name"]))
        offers = data.get("offers")
        if isinstance(offers, dict):
            if offers.get("price") and not fields["price_value"]:
                try:
                    fields["price_value"] = float(str(offers["price"]).replace(",", "."))
                except ValueError:
                    pass
            if offers.get("priceCurrency") and not fields["currency"]:
                fields["currency"] = clean_text(str(offers["priceCurrency"]))

    item = ProductItem(
        title=title,
        product_id=extract_product_id(page_url),
        product_url=page_url,
        image_urls=collect_images(soup, source_url),
        attributes=extract_attribute_hints(full_text),
        evidence=[Evidence(kind="html_text", text=full_text[:1000], confidence="medium")],
        **fields,
    )
    if description:
        item.evidence.append(Evidence(kind="meta_description", text=description[:1000], confidence="medium"))

    link_items: list[ProductItem] = []
    seen_hrefs: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        text = clean_text(anchor.get_text(" ", strip=True))
        href = urljoin(source_url or "", anchor["href"])
        if len(text) < 8 or not urlparse(href).netloc or href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        price_text, currency, price_value = parse_price(text)
        link_items.append(
            ProductItem(
                title=text[:220],
                price_text=price_text,
                currency=currency,
                price_value=price_value,
                product_id=extract_product_id(href),
                product_url=href,
                attributes=extract_attribute_hints(text),
                evidence=[Evidence(kind="search_card_link", text=text[:500], confidence="low")],
            )
        )
        if len(link_items) >= 20:
            break

    items = [item]
    if link_items and len(full_text) > 1500:
        item.warnings.append("page may be a search/results page; card extraction is approximate")
        items.extend(link_items[:10])

    return CollectionResult(
        platform=platform,
        source_url=source_url,
        status="ok",
        page_type="html_snapshot",
        items=items,
    )