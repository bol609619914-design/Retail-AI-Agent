import json
import re
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from app.api.routes.health import router as health_router
from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
PRODUCTS_FILE = BACKEND_DIR / "data" / "products.json"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


def load_products() -> list[dict[str, Any]]:
    if not PRODUCTS_FILE.exists():
        raise FileNotFoundError(f"Products file not found: {PRODUCTS_FILE}")

    with PRODUCTS_FILE.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def product_search_text(product: dict[str, Any]) -> str:
    searchable_fields = [
        product.get("name", ""),
        product.get("brand", ""),
        product.get("category", ""),
        product.get("feature", ""),
        product.get("benefit", ""),
        product.get("materials", ""),
        product.get("craftsmanship", ""),
        " ".join(product.get("signature_specs", [])),
        " ".join(product.get("scenarios", [])),
    ]
    return " ".join(str(field) for field in searchable_fields).lower()


def extract_search_tokens(text: str) -> list[str]:
    raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9-]{2,}", text.lower())
    expanded_tokens: list[str] = []

    for token in raw_tokens:
        expanded_tokens.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            if len(token) > 1:
                expanded_tokens.extend(token[i : i + 2] for i in range(len(token) - 1))
            expanded_tokens.extend(list(token))

    unique_tokens = list(dict.fromkeys(expanded_tokens))
    return [token for token in unique_tokens if token.strip()]


def search_products(keyword: str) -> list[dict[str, Any]]:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return []

    matched_products: list[dict[str, Any]] = []
    for product in load_products():
        searchable_text = product_search_text(product)
        if normalized_keyword in searchable_text:
            matched_products.append(product)

    return matched_products


def score_products(messages: list[ChatMessage]) -> list[tuple[int, dict[str, Any], list[str]]]:
    products = load_products()
    user_text = " ".join(message.content for message in messages if message.role == "user").lower()
    tokens = extract_search_tokens(user_text)

    scored_products: list[tuple[int, dict[str, Any], list[str]]] = []
    for product in products:
        searchable_text = product_search_text(product)
        matched_tokens: list[str] = []

        for token in tokens:
            if token in searchable_text:
                matched_tokens.append(token)

        score = len(matched_tokens)
        if score > 0:
            scored_products.append((score, product, list(dict.fromkeys(matched_tokens))))

    scored_products.sort(key=lambda item: item[0], reverse=True)
    return scored_products


def select_relevant_products(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    scored_products = score_products(messages)
    if scored_products:
        return [product for _, product, _ in scored_products[:3]]
    return load_products()


def choose_recommended_candidate(messages: list[ChatMessage]) -> tuple[int, dict[str, Any], list[str]] | None:
    scored_products = score_products(messages)
    if not scored_products:
        return None

    best_score, product, matched_tokens = scored_products[0]
    if best_score < 1:
        return None
    return best_score, product, matched_tokens


def normalize_preference_labels(tokens: list[str]) -> list[str]:
    priority_keywords = [
        "卧室",
        "床头",
        "书房",
        "客厅",
        "安静",
        "柔和",
        "灯光",
        "香氛",
        "睡眠",
        "放松",
        "阅读",
        "办公",
        "空气",
        "穿搭",
        "咖啡",
        "送礼",
    ]

    labels: list[str] = []
    for keyword in priority_keywords:
        if any(keyword in token for token in tokens):
            labels.append(keyword)

    return labels[:4]


def build_recommendation_payload(
    messages: list[ChatMessage],
    recommended_candidate: tuple[int, dict[str, Any], list[str]] | None,
) -> dict[str, Any] | None:
    if not recommended_candidate:
        return None

    _, product, matched_tokens = recommended_candidate
    all_candidates = score_products(messages)
    alternative_candidates = [
        candidate_product["name"]
        for _, candidate_product, _ in all_candidates[1:3]
    ]

    preference_labels = normalize_preference_labels(matched_tokens)
    if not preference_labels:
        preference_labels = ["空间氛围", "日常舒适度"]

    why_this = [
        f"它更贴近你当前提到的偏好重点：{'、'.join(preference_labels)}。",
        f"从功能层面看，{product['feature']}",
        f"从体验层面看，它能{product['benefit']}",
    ]

    if alternative_candidates:
        why_not_others = (
            f"相比 {alternative_candidates[0]}"
            + (f" 和 {alternative_candidates[1]}" if len(alternative_candidates) > 1 else "")
            + "，这款产品与当前场景的契合度更集中，不需要你在多种方向之间摇摆。"
        )
    else:
        why_not_others = "目前这款产品与当前对话中的偏好方向最一致，因此没有再分散到其他选择。"

    return {
        "name": product["name"],
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "price_range": product.get("price_range", ""),
        "materials": product.get("materials", ""),
        "craftsmanship": product.get("craftsmanship", ""),
        "signature_specs": product.get("signature_specs", []),
        "image": product.get("image", ""),
        "feature": product["feature"],
        "benefit": product["benefit"],
        "scenarios": product["scenarios"],
        "matched_preferences": preference_labels,
        "why_this": why_this,
        "why_not_others": why_not_others,
        "consultant_summary": f"这款更像是在为你的生活方式补上一层稳定而克制的质感，而不是单纯增加一个功能设备。",
    }


def build_system_prompt(
    products: list[dict[str, Any]],
    recommended_product: dict[str, Any] | None,
    stage: str,
) -> str:
    catalog_json = json.dumps(products, ensure_ascii=False, indent=2)
    recommendation_hint = ""
    if recommended_product:
        recommendation_hint = (
            "\n推荐约束：如果信息已经足够，请优先围绕这款产品形成最终建议，"
            f"并确保推荐对象是“{recommended_product['name']}”。\n"
        )

    return (
        "你是一位在高端商场工作的专业顾问。你的任务是先通过聊天了解用户对生活的品质要求，"
        "然后从我提供的产品库中挑选最合适的一款推荐给他们。说话要优雅、克制，不要像推销员。\n\n"
        "回答规则：\n"
        "1. 所有对外回复都以中文为主，自然、简洁、有分寸。\n"
        "2. 对话节奏遵循顾问式追问：第一轮优先确认空间，第二轮收敛氛围或功能，第三轮再给出单品推荐。\n"
        "3. 如果当前信息还不足，请只问一个问题，不要连续追问多个问题。\n"
        "4. 当信息足够时，只推荐最合适的一款产品，不要同时推荐多款。\n"
        "5. 推荐后补一句柔和的延展建议，例如是否要继续收敛搭配方向。\n"
        "6. 只能基于下面产品库中的信息来推荐，不要编造产品库以外的产品。\n"
        f"当前阶段判断：{stage}\n"
        f"{recommendation_hint}\n"
        f"产品库（JSON）：\n{catalog_json}"
    )


def create_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def detect_conversation_stage(messages: list[ChatMessage], recommendation_payload: dict[str, Any] | None) -> str:
    user_messages = [message.content for message in messages if message.role == "user"]
    combined_text = " ".join(user_messages)

    spaces = ["卧室", "书房", "客厅", "玄关", "衣帽间", "办公桌", "床头", "咖啡角"]
    atmospheres = ["安静", "柔和", "放松", "香氛", "明亮", "睡眠", "氛围", "清新", "高级"]
    functions = ["灯光", "照明", "空气", "净化", "阅读", "办公", "穿搭", "咖啡", "助眠"]

    has_space = any(keyword in combined_text for keyword in spaces)
    has_atmosphere = any(keyword in combined_text for keyword in atmospheres)
    has_function = any(keyword in combined_text for keyword in functions)

    if recommendation_payload and has_space and (has_atmosphere or has_function):
        return "final_recommendation"
    if has_space:
        return "clarify_atmosphere_or_function"
    return "clarify_space"


def has_enough_context(stage: str) -> bool:
    return stage == "final_recommendation"


def mock_reply(stage: str, recommendation_payload: dict[str, Any] | None) -> str:
    if stage == "clarify_space":
        return "在继续往下收敛之前，我想先确认一下，你更希望我围绕哪个空间来考虑这件单品？例如卧室、书房、客厅，或某个更具体的角落。"

    if stage == "clarify_atmosphere_or_function":
        return "我已经大致理解了空间方向。接下来我想再收拢一步：你更在意的是氛围感，比如柔和、安静、放松，还是更明确的功能体验，比如照明、空气、香氛或阅读舒适度？"

    if not recommendation_payload:
        return "我已经接近形成判断了。如果你愿意，再补一句你最在意的感受关键词，我会更稳妥地收敛到一件单品。"

    return (
        f"如果从现有产品里只挑一款更合适的，我会倾向于推荐“{recommendation_payload['name']}”。\n\n"
        f"它之所以更适合你，不只是因为{recommendation_payload['feature']}，更因为它能{recommendation_payload['benefit']}\n\n"
        f"如果你愿意，我也可以继续帮你把这件单品放进更完整的空间搭配里，看看它与灯光、香氛或材质气质是否一致。"
    )


def sse_event(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def stream_mock_response(stage: str, recommendation_payload: dict[str, Any] | None):
    reply = mock_reply(stage, recommendation_payload)
    for char in reply:
        yield sse_event("chunk", {"text": char})
        time.sleep(0.01)

    if stage == "final_recommendation" and recommendation_payload:
        yield sse_event("product", {"product": recommendation_payload})

    yield sse_event("meta", {"mode": "mock", "stage": stage})
    yield sse_event("done", {"source": "mock"})


def stream_openai_response(
    messages: list[ChatMessage],
    recommendation_payload: dict[str, Any] | None,
    stage: str,
):
    products = select_relevant_products(messages)
    system_prompt = build_system_prompt(products, recommendation_payload, stage)
    client = create_openai_client()
    completion_stream = client.chat.completions.create(
        model=settings.openai_model,
        stream=True,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            *[{"role": message.role, "content": message.content} for message in messages],
        ],
    )

    for chunk in completion_stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield sse_event("chunk", {"text": delta})

    if stage == "final_recommendation" and recommendation_payload:
        yield sse_event("product", {"product": recommendation_payload})

    yield sse_event("meta", {"mode": "openai", "stage": stage})
    yield sse_event("done", {"source": "openai"})


def stream_chat_response(messages: list[ChatMessage]):
    recommended_candidate = choose_recommended_candidate(messages)
    recommendation_payload = build_recommendation_payload(messages, recommended_candidate)
    stage = detect_conversation_stage(messages, recommendation_payload)

    try:
        if settings.openai_api_key:
            yield from stream_openai_response(messages, recommendation_payload, stage)
            return
        yield from stream_mock_response(stage, recommendation_payload)
    except Exception as exc:
        yield sse_event("error", {"message": str(exc)})


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} backend is running."}


@app.get("/api/products/search")
async def product_search(keyword: str = Query(..., min_length=1)) -> dict[str, Any]:
    try:
        results = search_products(keyword)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "keyword": keyword,
        "count": len(results),
        "results": results,
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one message is required.")

    if not PRODUCTS_FILE.exists():
        raise HTTPException(status_code=500, detail=f"Products file not found: {PRODUCTS_FILE}")

    generator = stream_chat_response(request.messages)
    return StreamingResponse(
        generator,
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
