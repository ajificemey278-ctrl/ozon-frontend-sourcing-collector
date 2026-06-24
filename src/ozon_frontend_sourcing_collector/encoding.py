from __future__ import annotations

from urllib.parse import quote

SUPPORTED_PLATFORMS = ("ozon", "1688", "taobao", "yiwugo")


def encode_1688_keyword(keyword: str) -> str:
    """1688 search expects legacy Chinese encoding for stable visible search text."""
    return "".join(f"%{byte:02X}" for byte in keyword.encode("gb18030"))


def build_search_url(platform: str, keyword: str) -> str:
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("keyword is required")
    if platform == "ozon":
        return f"https://www.ozon.ru/search/?from_global=true&text={quote(keyword)}"
    if platform == "1688":
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={encode_1688_keyword(keyword)}"
    if platform == "taobao":
        return f"https://s.taobao.com/search?q={quote(keyword)}"
    if platform == "yiwugo":
        return f"https://www.yiwugo.com/search/s.html?keyword={quote(keyword)}"
    raise ValueError(f"unsupported platform: {platform}")