import json
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from app.api.routes.health import router as health_router
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = BASE_DIR / "data" / "products.json"

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

    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def search_products(keyword: str) -> list[dict[str, object]]:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return []

    matched_products: list[dict[str, object]] = []
    for product in load_products():
        searchable_text = " ".join(
            [
                str(product.get("name", "")),
                str(product.get("feature", "")),
                str(product.get("benefit", "")),
                " ".join(product.get("scenarios", [])),
            ]
        ).lower()

        if normalized_keyword in searchable_text:
            matched_products.append(product)

    return matched_products


def select_relevant_products(messages: list[ChatMessage]) -> list[dict[str, object]]:
    products = load_products()
    user_text = " ".join(message.content for message in messages if message.role == "user").lower()
    tokens = re.findall(r"[\u4e00-\u9fff]{1,}|[a-z0-9-]{2,}", user_text)

    scored_products: list[tuple[int, dict[str, object]]] = []
    for product in products:
        searchable_text = " ".join(
            [
                str(product.get("name", "")),
                str(product.get("feature", "")),
                str(product.get("benefit", "")),
                " ".join(product.get("scenarios", [])),
            ]
        ).lower()

        score = 0
        for token in tokens:
            if token in searchable_text:
                score += 1

        if score > 0:
            scored_products.append((score, product))

    if scored_products:
        scored_products.sort(key=lambda item: item[0], reverse=True)
        return [product for _, product in scored_products[:3]]

    return products


def build_system_prompt(products: list[dict[str, object]]) -> str:
    catalog_json = json.dumps(products, ensure_ascii=False, indent=2)
    return (
        "你是一位在高端商场工作的专业顾问。你的任务是先通过聊天了解用户对生活的品质要求，然后从我提供的产品库中"
        "挑选最合适的一款推荐给他们。说话要优雅、克制，不要像推销员。\n\n"
        "回答规则：\n"
        "1. 如果信息还不够，请先提出一个简洁、自然的问题来了解用户对空间、氛围、功能或生活方式的偏好。\n"
        "2. 当你已经有足够信息时，只推荐最合适的一款产品，不要同时推荐多款。\n"
        "3. 推荐时要自然说明这款产品的 Feature、Benefit 和适用场景，但语气仍需克制、像顾问而不是销售。\n"
        "4. 只能基于下面产品库中的信息来推荐，不要编造产品库以外的产品。\n"
        "5. 回答尽量简洁，保留高级感。\n\n"
        f"产品库（JSON）：\n{catalog_json}"
    )


def create_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def stream_chat_response(messages: list[ChatMessage]):
    try:
        products = select_relevant_products(messages)
        system_prompt = build_system_prompt(products)
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
                yield delta.encode("utf-8")
    except Exception as exc:
        error_message = f"\n[Stream error] {exc}"
        yield error_message.encode("utf-8")


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

    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the backend.")

    if not PRODUCTS_FILE.exists():
        raise HTTPException(status_code=500, detail=f"Products file not found: {PRODUCTS_FILE}")

    generator = stream_chat_response(request.messages)
    return StreamingResponse(
        generator,
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
