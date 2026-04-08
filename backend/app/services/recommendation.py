import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models import ChatMessage


@dataclass
class PreferenceProfile:
    spaces: list[str]
    atmospheres: list[str]
    functions: list[str]
    styles: list[str]
    budgets: list[str]
    intents: list[str]
    constraints: list[str]
    keywords: list[str]


SPACE_TERMS = {
    "卧室": ["卧室", "床头", "睡房"],
    "书房": ["书房", "办公桌", "工作台"],
    "客厅": ["客厅", "起居室", "会客区"],
    "玄关": ["玄关", "门厅", "入户"],
    "衣帽间": ["衣帽间", "更衣区"],
    "咖啡角": ["咖啡角", "咖啡区", "吧台"],
}

ATMOSPHERE_TERMS = {
    "安静": ["安静", "静音", "不吵"],
    "柔和": ["柔和", "柔一点", "不刺眼"],
    "放松": ["放松", "松弛", "治愈"],
    "清新": ["清新", "干净", "通透"],
    "仪式感": ["仪式感", "精致", "高级感"],
    "明亮": ["明亮", "清亮", "提气"],
}

FUNCTION_TERMS = {
    "香氛": ["香氛", "香味", "扩香"],
    "照明": ["灯", "灯光", "照明", "夜读"],
    "空气": ["空气", "净化", "送风", "除味"],
    "穿搭": ["穿搭", "搭配", "试衣"],
    "咖啡": ["咖啡", "手冲", "萃取"],
    "助眠": ["睡眠", "助眠", "睡前"],
}

STYLE_TERMS = {
    "极简": ["极简", "简洁", "干净利落"],
    "温润": ["温润", "柔和", "不冰冷"],
    "现代": ["现代", "当代", "利落"],
    "酒店感": ["酒店感", "酒店式", "精品酒店"],
    "雕塑感": ["雕塑感", "造型感", "设计感"],
}

BUDGET_TERMS = {
    "入门奢享": ["三千内", "3000", "预算低一些", "别太贵"],
    "中高预算": ["五千左右", "5000", "预算中等"],
    "高预算": ["预算高", "万元内", "一万", "不太考虑预算"],
}

INTENT_TERMS = {
    "自用": ["自己用", "日常用", "长期用"],
    "送礼": ["送礼", "礼物", "送人"],
    "提升空间质感": ["空间质感", "整体氛围", "气质"],
    "提高效率": ["效率", "省时间", "方便"],
}

CONSTRAINT_TERMS = {
    "不想太占地方": ["别太占地方", "体积小一点", "不占地"],
    "不想太难打理": ["别太难打理", "好清洁", "省心"],
    "不要太冷硬": ["不要太冷硬", "别太冰冷", "不想太理性"],
    "不要太张扬": ["低调一点", "别太张扬", "克制"],
}


def load_products(products_file: Path) -> list[dict[str, Any]]:
    if not products_file.exists():
        raise FileNotFoundError(f"Products file not found: {products_file}")

    with products_file.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def extract_search_tokens(text: str) -> list[str]:
    raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9-]{2,}", text.lower())
    expanded_tokens: list[str] = []

    for token in raw_tokens:
        expanded_tokens.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            if len(token) > 1:
                expanded_tokens.extend(token[index : index + 2] for index in range(len(token) - 1))
            expanded_tokens.extend(list(token))

    unique_tokens = list(dict.fromkeys(expanded_tokens))
    return [token for token in unique_tokens if token.strip()]


def product_search_text(product: dict[str, Any]) -> str:
    searchable_fields = [
        product.get("name", ""),
        product.get("brand", ""),
        product.get("category", ""),
        product.get("budget_tier", ""),
        product.get("feature", ""),
        product.get("benefit", ""),
        product.get("materials", ""),
        product.get("craftsmanship", ""),
        product.get("pairing_note", ""),
        " ".join(product.get("signature_specs", [])),
        " ".join(product.get("style_tags", [])),
        " ".join(product.get("room_tags", [])),
        " ".join(product.get("ideal_for", [])),
        " ".join(product.get("avoid_for", [])),
        " ".join(product.get("scenarios", [])),
    ]
    return " ".join(str(field) for field in searchable_fields).lower()


def search_products(products_file: Path, keyword: str) -> list[dict[str, Any]]:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return []

    matched_products: list[dict[str, Any]] = []
    for product in load_products(products_file):
        if normalized_keyword in product_search_text(product):
            matched_products.append(product)

    return matched_products


def match_terms(text: str, term_map: dict[str, list[str]]) -> list[str]:
    matched_labels: list[str] = []
    for label, terms in term_map.items():
        if any(term in text for term in terms):
            matched_labels.append(label)
    return matched_labels


def extract_preference_profile(messages: list[ChatMessage]) -> PreferenceProfile:
    user_text = " ".join(message.content for message in messages if message.role == "user").lower()
    return PreferenceProfile(
        spaces=match_terms(user_text, SPACE_TERMS),
        atmospheres=match_terms(user_text, ATMOSPHERE_TERMS),
        functions=match_terms(user_text, FUNCTION_TERMS),
        styles=match_terms(user_text, STYLE_TERMS),
        budgets=match_terms(user_text, BUDGET_TERMS),
        intents=match_terms(user_text, INTENT_TERMS),
        constraints=match_terms(user_text, CONSTRAINT_TERMS),
        keywords=extract_search_tokens(user_text),
    )


def infer_stage(profile: PreferenceProfile) -> str:
    if profile.spaces and (profile.atmospheres or profile.functions or profile.styles):
        return "final_recommendation"
    if profile.spaces:
        return "clarify_atmosphere_or_function"
    return "clarify_space"


def profile_summary(profile: PreferenceProfile) -> list[str]:
    summary: list[str] = []
    for label in profile.spaces[:2]:
        summary.append(f"空间：{label}")
    for label in profile.atmospheres[:2]:
        summary.append(f"氛围：{label}")
    for label in profile.functions[:2]:
        summary.append(f"功能：{label}")
    for label in profile.styles[:1]:
        summary.append(f"风格：{label}")
    for label in profile.constraints[:1]:
        summary.append(f"限制：{label}")
    return summary[:6]


def score_product(product: dict[str, Any], profile: PreferenceProfile) -> tuple[int, list[str]]:
    score = 0
    matched_preferences: list[str] = []
    product_text = product_search_text(product)

    def add_points(labels: list[str], weight: int) -> None:
        nonlocal score
        for label in labels:
            if label.lower() in product_text:
                score += weight
                matched_preferences.append(label)

    add_points(profile.spaces, 4)
    add_points(profile.atmospheres, 3)
    add_points(profile.functions, 4)
    add_points(profile.styles, 2)
    add_points(profile.intents, 2)

    budget_tier = product.get("budget_tier", "")
    if profile.budgets and budget_tier in profile.budgets:
        score += 2
        matched_preferences.append(budget_tier)

    for token in profile.keywords:
        if token in product_text:
            score += 1

    avoid_for = " ".join(product.get("avoid_for", []))
    for constraint in profile.constraints:
        if constraint in avoid_for:
            score -= 3

    unique_preferences = list(dict.fromkeys(matched_preferences))
    return score, unique_preferences


def rank_products(products_file: Path, profile: PreferenceProfile) -> list[tuple[int, dict[str, Any], list[str]]]:
    ranked: list[tuple[int, dict[str, Any], list[str]]] = []

    for product in load_products(products_file):
        score, matched_preferences = score_product(product, profile)
        if score > 0:
            ranked.append((score, product, matched_preferences))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def select_relevant_products(products_file: Path, profile: PreferenceProfile) -> list[dict[str, Any]]:
    ranked = rank_products(products_file, profile)
    if ranked:
        return [product for _, product, _ in ranked[:3]]
    return load_products(products_file)


def choose_recommended_candidate(
    products_file: Path,
    profile: PreferenceProfile,
) -> tuple[int, dict[str, Any], list[str]] | None:
    ranked = rank_products(products_file, profile)
    if not ranked:
        return None
    return ranked[0]


def build_recommendation_payload(
    products_file: Path,
    profile: PreferenceProfile,
    recommended_candidate: tuple[int, dict[str, Any], list[str]] | None,
) -> dict[str, Any] | None:
    if not recommended_candidate:
        return None

    _, product, matched_preferences = recommended_candidate
    ranked = rank_products(products_file, profile)
    alternatives = [candidate_product["name"] for _, candidate_product, _ in ranked[1:3]]

    normalized_preferences = matched_preferences[:4] or ["空间氛围", "日常舒适度"]
    why_this = [
        f"它与当前对话里反复出现的重点更一致：{'、'.join(normalized_preferences)}。",
        f"从使用体验来看，{product['benefit']}",
        f"从产品气质来看，{product['pairing_note']}",
    ]

    if alternatives:
        why_not_others = (
            f"相比 {alternatives[0]}"
            + (f" 和 {alternatives[1]}" if len(alternatives) > 1 else "")
            + "，这款更集中地回应了你现在最在意的空间感受，不需要再在多个方向之间折返。"
        )
    else:
        why_not_others = "以当前的偏好信息来看，这款的方向已经足够集中，没有必要再分散到其他选择。"

    consultant_summary = (
        f"{product['name']} 更像是一件把 {product['category']} 融进空间气质里的单品，"
        "重点不是参数堆得多，而是它进入日常之后会不会让使用感受更顺。"
    )

    return {
        "name": product["name"],
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "price_range": product.get("price_range", ""),
        "budget_tier": product.get("budget_tier", ""),
        "materials": product.get("materials", ""),
        "craftsmanship": product.get("craftsmanship", ""),
        "signature_specs": product.get("signature_specs", []),
        "style_tags": product.get("style_tags", []),
        "room_tags": product.get("room_tags", []),
        "ideal_for": product.get("ideal_for", []),
        "avoid_for": product.get("avoid_for", []),
        "pairing_note": product.get("pairing_note", ""),
        "image": product.get("image", ""),
        "feature": product["feature"],
        "benefit": product["benefit"],
        "scenarios": product["scenarios"],
        "matched_preferences": normalized_preferences,
        "why_this": why_this,
        "why_not_others": why_not_others,
        "consultant_summary": consultant_summary,
    }
