import json
import re
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from app.models import ChatMessage
from app.services.recommendation import PreferenceProfile, load_products


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)

BLOCKED_DOMAINS = {
    "duckduckgo.com",
    "www.amazon.com",
    "amazon.com",
    "reddit.com",
    "www.reddit.com",
    "youtube.com",
    "www.youtube.com",
    "bestbuy.com",
    "www.bestbuy.com",
    "walmart.com",
    "www.walmart.com",
    "ebay.com",
    "www.ebay.com",
}

FUNCTION_SEARCH_HINTS = {
    "照明": "premium reading desk lamp official",
    "音乐": "premium wireless speaker official product",
    "香氛": "premium diffuser official product",
    "咖啡": "premium coffee maker official product",
    "保温": "premium temperature control mug official product",
}

FUNCTION_DOMAIN_HINTS = {
    "照明": ["benq.com", "flos.com", "artemide.com"],
    "音乐": ["sonos.com", "bang-olufsen.com", "bose.com"],
    "香氛": ["vitruvi.com", "trudon.com", "aesop.com"],
    "咖啡": ["fellowproducts.com", "nespresso.com", "aarke.us"],
    "保温": ["ember.com", "fellowproducts.com"],
}

FUNCTION_CANDIDATE_URLS = {
    "照明": [
        "https://www.philips-hue.com/en-us/p/hue-white-and-color-ambiance-gradient-signe-table-lamp/046677803513",
        "https://www.benq.com/en-us/lighting/e-reading-desk-lamp/e-reading.html",
    ],
    "音乐": [
        "https://www.sonos.com/en-us/shop/move-2",
        "https://www.apple.com/shop/buy-homepod/homepod-mini/blue",
        "https://www.sonos.com/en-us/shop/era-300",
    ],
    "香氛": [
        "https://vitruvi.com/products/stone-essential-oil-diffuser",
    ],
    "咖啡": [
        "https://fellowproducts.com/products/aiden-precision-coffee-maker",
    ],
    "保温": [
        "https://ember.com/products/ember-mug-2",
    ],
}


def _http_get(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _strip_tags(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _extract_meta(html: str, attr_name: str, attr_value: str) -> str:
    patterns = [
        rf'<meta[^>]+{attr_name}="{re.escape(attr_value)}"[^>]+content="([^"]+)"',
        rf"<meta[^>]+{attr_name}='{re.escape(attr_value)}'[^>]+content='([^']+)'",
        rf'<meta[^>]+content="([^"]+)"[^>]+{attr_name}="{re.escape(attr_value)}"',
        rf"<meta[^>]+content='([^']+)'[^>]+{attr_name}='{re.escape(attr_value)}'",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return unescape(match.group(1)).strip()
    return ""


def _extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _strip_tags(match.group(1))


def _extract_price(html: str) -> str:
    patterns = [
        r"(?:USD|\$)\s?\d[\d,]*(?:\.\d{2})?",
        r"(?:RMB|CNY|¥)\s?\d[\d,]*(?:\.\d{2})?",
        r"(?:EUR|€)\s?\d[\d,]*(?:\.\d{2})?",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return match.group(0).replace("USD", "USD ").replace("RMB", "RMB ").replace("CNY", "CNY ")
    return "以官网页面为准"


def _domain_brand(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    if not host:
        return "官方品牌"
    root = host.split(".")[0]
    return root.replace("-", " ").title()


def _clean_product_name(title: str, brand: str) -> str:
    name = title.split("|")[0].split("–")[0].split("—")[0].strip()
    if not name:
        name = title.strip()
    if brand.lower() in name.lower():
        return name
    return name


def _decode_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if "duckduckgo.com" not in parsed.netloc:
        return url
    query = parse_qs(parsed.query)
    uddg = query.get("uddg", [""])[0]
    if uddg:
        return unquote(uddg)
    return url


def _duckduckgo_search(query: str, max_results: int = 6) -> list[str]:
    html = _http_get(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}")
    links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', html, flags=re.IGNORECASE)
    results: list[str] = []
    for raw_url in links:
        url = _decode_duckduckgo_url(unescape(raw_url))
        host = urlparse(url).netloc.lower()
        if not host or host in BLOCKED_DOMAINS:
            continue
        if url not in results:
            results.append(url)
        if len(results) >= max_results:
            break
    return results


def _build_search_queries(messages: list[ChatMessage], profile: PreferenceProfile) -> list[str]:
    user_text = " ".join(message.content for message in messages if message.role == "user")
    queries: list[str] = []

    for function in profile.functions[:2]:
        hint = FUNCTION_SEARCH_HINTS.get(function)
        if hint:
            queries.append(hint)
        for domain in FUNCTION_DOMAIN_HINTS.get(function, []):
            queries.append(f"site:{domain} {hint or function}")

    if user_text.strip():
        queries.append(f"premium lifestyle product official {user_text}")

    if profile.spaces or profile.atmospheres:
        descriptors = " ".join(profile.spaces[:1] + profile.atmospheres[:2] + profile.functions[:1])
        queries.append(f"official product {descriptors} premium")

    seen: list[str] = []
    for query in queries:
        normalized = query.strip()
        if normalized and normalized not in seen:
            seen.append(normalized)
    return seen[:3]


def _extract_page_candidate(url: str, profile: PreferenceProfile) -> dict[str, Any] | None:
    try:
        html = _http_get(url)
    except Exception:
        return None

    title = _extract_meta(html, "property", "og:title") or _extract_title(html)
    image = _extract_meta(html, "property", "og:image")
    description = _extract_meta(html, "property", "og:description") or _extract_meta(html, "name", "description")
    canonical = _extract_meta(html, "property", "og:url") or url

    if not title or not image:
        return None

    brand = _domain_brand(canonical)
    category = profile.functions[0] if profile.functions else "生活方式单品"
    price = _extract_price(html)
    clean_name = _clean_product_name(title, brand)
    short_description = description[:220] if description else "以官网页面信息为准。"

    scenarios = profile.spaces[:2] or ["居家日常"]
    style_tags = profile.styles[:2] or ["现代", "克制"]
    room_tags = profile.spaces[:2]

    return {
        "name": clean_name,
        "brand": brand,
        "category": category,
        "price_range": price,
        "budget_tier": profile.budgets[0] if profile.budgets else "线上检索",
        "materials": "以官网页面信息为准",
        "craftsmanship": short_description,
        "signature_specs": [
            "实时联网检索结果",
            f"来源域名：{urlparse(canonical).netloc}",
            f"价格参考：{price}",
        ],
        "style_tags": style_tags,
        "room_tags": room_tags,
        "ideal_for": [
            "适合当前这轮对话里已经收敛出的生活方式需求",
            "更适合在意真实品牌与官网来源的人",
        ],
        "avoid_for": [
            "如果更希望完全离线推荐，可以继续用本地精选库",
        ],
        "pairing_note": short_description,
        "source_url": canonical,
        "image": urljoin(canonical, image),
        "feature": short_description,
        "benefit": short_description,
        "scenarios": scenarios,
    }


def search_live_products(
    messages: list[ChatMessage],
    profile: PreferenceProfile,
    local_products_file: Path,
    max_products: int = 4,
) -> list[dict[str, Any]]:
    queries = _build_search_queries(messages, profile)
    if not queries:
        return []

    local_names = {product["name"] for product in load_products(local_products_file)}
    preferred_domains = {
        domain
        for function in profile.functions
        for domain in FUNCTION_DOMAIN_HINTS.get(function, [])
    }
    live_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    candidate_urls = [
        url
        for function in profile.functions[:2]
        for url in FUNCTION_CANDIDATE_URLS.get(function, [])
    ]

    for url in candidate_urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        candidate = _extract_page_candidate(url, profile)
        if not candidate:
            continue
        if candidate["name"] in local_names:
            continue
        live_products.append(candidate)
        if len(live_products) >= max_products:
            return live_products

    for query in queries:
        for url in _duckduckgo_search(query):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            candidate = _extract_page_candidate(url, profile)
            if not candidate:
                continue
            if preferred_domains:
                host = urlparse(candidate["source_url"]).netloc.lower().replace("www.", "")
                if not any(host.endswith(domain) for domain in preferred_domains):
                    continue
            if candidate["name"] in local_names:
                continue
            live_products.append(candidate)
            if len(live_products) >= max_products:
                return live_products

    return live_products
