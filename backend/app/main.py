import json
import re
import time
from pathlib import Path
from typing import Literal

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


def load_products() -> list[dict[str, object]]:
    if not PRODUCTS_FILE.exists():
        raise FileNotFoundError(f"Products file not found: {PRODUCTS_FILE}")

    with PRODUCTS_FILE.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def product_search_text(product: dict[str, object]) -> str:
    return " ".join(
        [
            str(product.get("name", "")),
            str(product.get("feature", "")),
            str(product.get("benefit", "")),
            " ".join(product.get("scenarios", [])),
        ]
    ).lower()


def extract_search_tokens(text: str) -> list[str]:
    raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9-]{2,}", text.lower())
    expanded_tokens: list[str] = []

    for token in raw_tokens:
        expanded_tokens.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            if len(token) > 1:
                expanded_tokens.extend(token[i : i + 2] for i in range(len(token) - 1))
            expanded_tokens.extend(list(token))

    # Keep order while de-duplicating.
    unique_tokens = list(dict.fromkeys(expanded_tokens))
    return [token for token in unique_tokens if token.strip()]


def search_products(keyword: str) -> list[dict[str, object]]:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return []

    matched_products: list[dict[str, object]] = []
    for product in load_products():
        searchable_text = product_search_text(product)
        if normalized_keyword in searchable_text:
            matched_products.append(product)

    return matched_products


def score_products(messages: list[ChatMessage]) -> list[tuple[int, dict[str, object]]]:
    products = load_products()
    user_text = " ".join(message.content for message in messages if message.role == "user").lower()
    tokens = extract_search_tokens(user_text)

    scored_products: list[tuple[int, dict[str, object]]] = []
    for product in products:
        searchable_text = product_search_text(product)
        score = 0
        for token in tokens:
            if token in searchable_text:
                score += 1

        if score > 0:
            scored_products.append((score, product))

    scored_products.sort(key=lambda item: item[0], reverse=True)
    return scored_products


def select_relevant_products(messages: list[ChatMessage]) -> list[dict[str, object]]:
    scored_products = score_products(messages)
    if scored_products:
        return [product for _, product in scored_products[:3]]
    return load_products()


def choose_recommended_product(messages: list[ChatMessage]) -> dict[str, object] | None:
    scored_products = score_products(messages)
    if not scored_products:
        return None

    best_score, product = scored_products[0]
    if best_score < 1:
        return None
    return product


def build_system_prompt(products: list[dict[str, object]], recommended_product: dict[str, object] | None) -> str:
    catalog_json = json.dumps(products, ensure_ascii=False, indent=2)
    recommendation_hint = ""
    if recommended_product:
        recommendation_hint = (
            "\n\u63a8\u8350\u7ea6\u675f\uff1a\u5982\u679c\u4fe1\u606f\u5df2\u7ecf\u8db3\u591f\uff0c"
            "\u8bf7\u4f18\u5148\u56f4\u7ed5\u8fd9\u6b3e\u4ea7\u54c1\u5f62\u6210\u6700\u7ec8\u5efa\u8bae\uff0c"
            f"\u5e76\u786e\u4fdd\u63a8\u8350\u5bf9\u8c61\u662f\u201c{recommended_product['name']}\u201d\u3002\n"
        )

    return (
        "\u4f60\u662f\u4e00\u4f4d\u5728\u9ad8\u7aef\u5546\u573a\u5de5\u4f5c\u7684\u4e13\u4e1a\u987e\u95ee\u3002"
        "\u4f60\u7684\u4efb\u52a1\u662f\u5148\u901a\u8fc7\u804a\u5929\u4e86\u89e3\u7528\u6237\u5bf9\u751f\u6d3b\u7684"
        "\u54c1\u8d28\u8981\u6c42\uff0c\u7136\u540e\u4ece\u6211\u63d0\u4f9b\u7684\u4ea7\u54c1\u5e93\u4e2d"
        "\u6311\u9009\u6700\u5408\u9002\u7684\u4e00\u6b3e\u63a8\u8350\u7ed9\u4ed6\u4eec\u3002"
        "\u8bf4\u8bdd\u8981\u4f18\u96c5\u3001\u514b\u5236\uff0c\u4e0d\u8981\u50cf\u63a8\u9500\u5458\u3002\n\n"
        "\u56de\u7b54\u89c4\u5219\uff1a\n"
        "1. \u6240\u6709\u5bf9\u5916\u56de\u590d\u90fd\u4ee5\u4e2d\u6587\u4e3a\u4e3b\uff0c"
        "\u81ea\u7136\u3001\u7b80\u6d01\u3001\u6709\u5206\u5bf8\u3002\n"
        "2. \u5982\u679c\u4fe1\u606f\u8fd8\u4e0d\u591f\uff0c\u8bf7\u5148\u63d0\u51fa\u4e00\u4e2a"
        "\u7b80\u6d01\u3001\u81ea\u7136\u7684\u95ee\u9898\u6765\u4e86\u89e3\u7528\u6237\u5bf9\u7a7a\u95f4\u3001"
        "\u6c1b\u56f4\u3001\u529f\u80fd\u6216\u751f\u6d3b\u65b9\u5f0f\u7684\u504f\u597d\u3002\n"
        "3. \u5f53\u4f60\u5df2\u7ecf\u6709\u8db3\u591f\u4fe1\u606f\u65f6\uff0c\u53ea\u63a8\u8350"
        "\u6700\u5408\u9002\u7684\u4e00\u6b3e\u4ea7\u54c1\uff0c\u4e0d\u8981\u540c\u65f6\u63a8\u8350\u591a\u6b3e\u3002\n"
        "4. \u63a8\u8350\u65f6\u8981\u81ea\u7136\u8bf4\u660e\u8fd9\u6b3e\u4ea7\u54c1\u7684\u6838\u5fc3\u529f\u80fd\u3001"
        "\u80fd\u5e26\u6765\u7684\u5229\u76ca\u4e0e\u9002\u7528\u573a\u666f\uff0c\u4f46\u8bed\u6c14\u4ecd\u9700"
        "\u514b\u5236\u3001\u50cf\u987e\u95ee\u800c\u4e0d\u662f\u9500\u552e\u3002\n"
        "5. \u53ea\u80fd\u57fa\u4e8e\u4e0b\u9762\u4ea7\u54c1\u5e93\u4e2d\u7684\u4fe1\u606f\u6765\u63a8\u8350\uff0c"
        "\u4e0d\u8981\u7f16\u9020\u4ea7\u54c1\u5e93\u4ee5\u5916\u7684\u4ea7\u54c1\u3002\n"
        "6. \u56de\u590d\u5c3d\u91cf\u63a7\u5236\u5728 2 \u5230 4 \u6bb5\u4ee5\u5185\uff0c"
        "\u4fdd\u6301\u9ad8\u7ea7\u611f\u548c\u53ef\u8bfb\u6027\u3002"
        f"{recommendation_hint}\n"
        f"\u4ea7\u54c1\u5e93\uff08JSON\uff09\uff1a\n{catalog_json}"
    )


def create_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def has_enough_context(messages: list[ChatMessage], recommended_product: dict[str, object] | None) -> bool:
    user_messages = [message.content for message in messages if message.role == "user"]
    if not user_messages or not recommended_product:
        return False

    combined_text = " ".join(user_messages)
    meaningful_keywords = [
        "\u5367\u5ba4",
        "\u5e8a\u5934",
        "\u9605\u8bfb",
        "\u529e\u516c",
        "\u9999\u6c1b",
        "\u7761\u7720",
        "\u5ba2\u5385",
        "\u5b89\u9759",
        "\u706f",
        "\u5496\u5561",
        "\u7a7f\u642d",
        "\u7a7a\u6c14",
    ]
    hit_count = sum(1 for keyword in meaningful_keywords if keyword in combined_text)
    return len(user_messages) >= 2 or hit_count >= 2 or len(combined_text) >= 18


def mock_reply(messages: list[ChatMessage], recommended_product: dict[str, object] | None) -> str:
    latest_user_message = next((message.content for message in reversed(messages) if message.role == "user"), "")
    if not has_enough_context(messages, recommended_product) or not recommended_product:
        return (
            "\u6211\u60f3\u5148\u66f4\u51c6\u786e\u5730\u7406\u89e3\u4f60\u7684\u751f\u6d3b\u504f\u597d\u3002"
            "\u4f60\u66f4\u5728\u610f\u7684\u662f\u7a7a\u95f4\u6c1b\u56f4\u3001\u65e5\u5e38\u529f\u80fd\uff0c"
            "\u8fd8\u662f\u67d0\u79cd\u66f4\u5177\u4f53\u7684\u4f7f\u7528\u573a\u666f\uff0c"
            "\u6bd4\u5982\u5367\u5ba4\u3001\u4e66\u623f\u6216\u5ba2\u5385\uff1f"
        )

    scenarios = "\u3001".join(recommended_product["scenarios"])
    return (
        f"\u5982\u679c\u4ece\u73b0\u6709\u4ea7\u54c1\u91cc\u53ea\u6311\u4e00\u6b3e\u66f4\u5408\u9002\u7684\uff0c"
        f"\u6211\u4f1a\u503e\u5411\u4e8e\u63a8\u8350\u201c{recommended_product['name']}\u201d\u3002\n\n"
        f"\u5b83\u7684\u6838\u5fc3\u4f18\u52bf\u5728\u4e8e\uff1a{recommended_product['feature']}"
        f"\u3002\u5bf9\u4f60\u6765\u8bf4\uff0c\u66f4\u91cd\u8981\u7684\u662f\u5b83\u80fd"
        f"{recommended_product['benefit']}\n\n"
        f"\u5982\u679c\u4f60\u7684\u91cd\u70b9\u63a5\u8fd1\u201c{latest_user_message}\u201d\uff0c"
        f"\u90a3\u4e48\u5b83\u4f1a\u6bd4\u8f83\u81ea\u7136\u5730\u878d\u5165\u8fd9\u4e9b\u573a\u666f\uff1a{scenarios}\u3002"
    )


def sse_event(event: str, data: dict[str, object]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def stream_mock_response(messages: list[ChatMessage], recommended_product: dict[str, object] | None):
    reply = mock_reply(messages, recommended_product)
    for char in reply:
        yield sse_event("chunk", {"text": char})
        time.sleep(0.012)

    if has_enough_context(messages, recommended_product) and recommended_product:
        yield sse_event("product", {"product": recommended_product})

    yield sse_event("done", {"source": "mock"})


def stream_openai_response(messages: list[ChatMessage], recommended_product: dict[str, object] | None):
    products = select_relevant_products(messages)
    system_prompt = build_system_prompt(products, recommended_product)
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

    if has_enough_context(messages, recommended_product) and recommended_product:
        yield sse_event("product", {"product": recommended_product})

    yield sse_event("done", {"source": "openai"})


def stream_chat_response(messages: list[ChatMessage]):
    recommended_product = choose_recommended_product(messages)
    try:
        if settings.openai_api_key:
            yield from stream_openai_response(messages, recommended_product)
            return
        yield from stream_mock_response(messages, recommended_product)
    except Exception as exc:
        yield sse_event("error", {"message": str(exc)})


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} backend is running."}


@app.get("/api/products/search")
async def product_search(keyword: str = Query(..., min_length=1)) -> dict[str, object]:
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
