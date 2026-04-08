import json
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.models import ChatMessage, ChatRequest
from app.services.recommendation import (
    build_recommendation_payload,
    choose_recommended_candidate,
    extract_preference_profile,
    infer_stage,
    load_products,
    profile_summary,
    search_products,
    select_relevant_products,
)

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


def build_system_prompt(
    products: list[dict[str, Any]],
    recommended_product: dict[str, Any] | None,
    stage: str,
    summary: list[str],
) -> str:
    catalog_json = json.dumps(products, ensure_ascii=False, indent=2)
    recommendation_hint = ""
    if recommended_product:
        recommendation_hint = (
            "\n推荐约束：如果信息已经足够，请优先围绕这款产品形成最终建议，"
            f"并确保推荐对象是“{recommended_product['name']}”。\n"
        )

    summary_text = "；".join(summary) if summary else "当前还在收集偏好信息"
    return (
        "你是一位在高端商场工作的专业顾问。你的任务是先通过聊天了解用户对生活的品质要求，"
        "然后从我提供的产品库中挑选最合适的一款推荐给他们。说话要优雅、克制，不要像推销员。\n\n"
        "回答规则：\n"
        "1. 所有对外回复都以中文为主，自然、简洁、有分寸。\n"
        "2. 对话节奏遵循顾问式追问：第一轮优先确认空间，第二轮收敛氛围或功能，第三轮再给出单品推荐。\n"
        "3. 如果当前信息还不足，请只问一个问题，不要连续追问多个问题。\n"
        "4. 当信息足够时，只推荐最合适的一款产品，不要同时推荐多款。\n"
        "5. 推荐时要解释判断依据，重点放在体验与适配性，不要堆砌参数。\n"
        "6. 推荐后补一句柔和的延展建议，例如是否要继续收敛搭配方向。\n"
        "7. 只能基于下面产品库中的信息来推荐，不要编造产品库以外的产品。\n"
        f"当前阶段判断：{stage}\n"
        f"当前已提炼的偏好摘要：{summary_text}\n"
        f"{recommendation_hint}\n"
        f"产品库（JSON）：\n{catalog_json}"
    )


def create_openai_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def mock_reply(stage: str, recommendation_payload: dict[str, Any] | None, summary: list[str]) -> str:
    if stage == "clarify_space":
        return "在继续往下收拢之前，我想先确认一下，你更希望我围绕哪个空间来考虑这件单品？例如卧室、书房、客厅，或某个更具体的角落。"

    if stage == "clarify_atmosphere_or_function":
        intro = f"我先记下目前比较清楚的方向：{'，'.join(summary)}。\n\n" if summary else ""
        return intro + "接下来我想再收一步：你更在意的是氛围感，比如柔和、安静、放松，还是更明确的功能体验，比如照明、空气、香氛或阅读舒适度？"

    if not recommendation_payload:
        return "我已经接近形成判断了。如果你愿意，再补一句你最在意的感受关键词，我会更稳妥地收敛到一件单品。"

    return (
        f"如果从现有产品里只挑一款更合适的，我会倾向于推荐“{recommendation_payload['name']}”。\n\n"
        f"{recommendation_payload['consultant_summary']}\n\n"
        f"更具体地说，它适合你的原因主要有三点：\n"
        + "\n".join(f"- {reason}" for reason in recommendation_payload["why_this"])
        + "\n\n"
        + f"至于为什么我暂时不把重点放在别的选择上，原因是：{recommendation_payload['why_not_others']}\n\n"
        + "如果你愿意，我也可以继续帮你把这件单品放进更完整的空间搭配里，看看它和灯光、材质或香气方向是不是一致。"
    )


def sse_event(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def stream_mock_response(stage: str, recommendation_payload: dict[str, Any] | None, summary: list[str]):
    reply = mock_reply(stage, recommendation_payload, summary)
    for char in reply:
        yield sse_event("chunk", {"text": char})
        time.sleep(0.01)

    if stage == "final_recommendation" and recommendation_payload:
        yield sse_event("product", {"product": recommendation_payload})

    yield sse_event("meta", {"mode": "mock", "stage": stage, "profile_summary": summary})
    yield sse_event("done", {"source": "mock"})


def stream_openai_response(
    messages: list[ChatMessage],
    recommendation_payload: dict[str, Any] | None,
    stage: str,
    summary: list[str],
):
    profile = extract_preference_profile(messages)
    products = select_relevant_products(PRODUCTS_FILE, profile)
    system_prompt = build_system_prompt(products, recommendation_payload, stage, summary)
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

    yield sse_event("meta", {"mode": "openai", "stage": stage, "profile_summary": summary})
    yield sse_event("done", {"source": "openai"})


def stream_chat_response(messages: list[ChatMessage]):
    profile = extract_preference_profile(messages)
    summary = profile_summary(profile)
    recommended_candidate = choose_recommended_candidate(PRODUCTS_FILE, profile)
    recommendation_payload = build_recommendation_payload(PRODUCTS_FILE, profile, recommended_candidate)
    stage = infer_stage(profile)

    try:
        if settings.openai_api_key:
            yield from stream_openai_response(messages, recommendation_payload, stage, summary)
            return
        yield from stream_mock_response(stage, recommendation_payload, summary)
    except Exception as exc:
        yield sse_event("error", {"message": str(exc)})


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} backend is running."}


@app.get("/api/products/search")
async def product_search(keyword: str = Query(..., min_length=1)) -> dict[str, Any]:
    try:
        results = search_products(PRODUCTS_FILE, keyword)
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

    try:
        load_products(PRODUCTS_FILE)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

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
