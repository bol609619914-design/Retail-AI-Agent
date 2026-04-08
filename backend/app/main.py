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
from app.services.consultant_planner import ConsultantPlan, generate_consultant_plan
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
from app.services.web_catalog import search_live_products

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
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)


def create_openai_client() -> OpenAI:
    client_kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**client_kwargs)


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def sse_event(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def resolve_recommendation_payload(
    products_file: Path,
    profile: Any,
    shortlist: list[dict[str, Any]],
    planner: ConsultantPlan | None,
) -> dict[str, Any] | None:
    recommended_candidate = choose_recommended_candidate(products_file, profile)

    if planner and planner.recommended_product_name:
        shortlist_map = {product["name"]: product for product in shortlist}
        preferred_product = shortlist_map.get(planner.recommended_product_name)
        if preferred_product is not None:
            recommended_candidate = (999, preferred_product, [])

    return build_recommendation_payload(products_file, profile, recommended_candidate)


def merge_shortlists(
    primary_products: list[dict[str, Any]],
    secondary_products: list[dict[str, Any]],
    limit: int = 6,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for product in [*primary_products, *secondary_products]:
        name = product.get("name", "").strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        merged.append(product)
        if len(merged) >= limit:
            break

    return merged


def build_system_prompt(
    products: list[dict[str, Any]],
    recommendation_payload: dict[str, Any] | None,
    planner: ConsultantPlan | None,
    fallback_stage: str,
) -> str:
    catalog_json = json.dumps(products, ensure_ascii=False, indent=2)
    planner_summary = "；".join(planner.profile_summary) if planner and planner.profile_summary else "当前还在继续理解偏好。"
    action = planner.action if planner else ("recommend" if fallback_stage == "final_recommendation" else "ask")
    next_focus = planner.next_focus if planner else "继续理解用户最在意的生活场景。"
    reasoning = planner.reasoning if planner else "暂时使用规则层判断。"

    recommendation_hint = ""
    if recommendation_payload:
        recommendation_json = json.dumps(recommendation_payload, ensure_ascii=False, indent=2)
        recommendation_hint = (
            "\n唯一推荐约束：如果这一轮进入推荐，你必须只围绕下面这一款产品展开。\n"
            f"唯一推荐产品：{recommendation_payload['name']}\n"
            "不要换成别的产品，也不要把其他产品写成主推荐。\n"
            f"唯一推荐产品详情（JSON）：\n{recommendation_json}\n"
        )

    return f"""
你是一位在高端商场工作的专业顾问。
你的任务是先通过聊天了解用户对生活品质的要求，然后从我提供的产品库中挑选最合适的一款推荐给他们。
说话要优雅、克制，不要像推销员，也不要像客服。

回复要求：
1. 全程使用中文。
2. 先像真实顾问一样判断用户真正想解决的生活问题，再决定追问还是推荐。
3. 如果信息还不够，只问一个最有价值的问题，不要连问一串。
4. 如果已经足够推荐，就直接给出判断，并说明依据，不要堆参数。
5. 回答里尽量自然，不要提“根据系统”或“根据产品库”。
6. 推荐后可以补一句温和的延展建议，但不要喧宾夺主。

内部判断结果：
- 当前动作：{action}
- 当前收敛摘要：{planner_summary}
- 下一步焦点：{next_focus}
- 内部判断理由：{reasoning}
{recommendation_hint}

候选产品库（JSON）：
{catalog_json}
""".strip()


def mock_reply(
    planner: ConsultantPlan | None,
    recommendation_payload: dict[str, Any] | None,
) -> str:
    action = planner.action if planner else "ask"
    next_focus = planner.next_focus if planner else "继续理解用户此刻最在意的重点。"

    if action != "recommend" or not recommendation_payload:
        return (
            "我先不急着给出单品判断。"
            f" 这一轮我更想确认的是：{next_focus}"
            " 你可以顺着这个点再多说一句，我再继续往下收。"
        )

    return (
        f"如果现在只从现有产品里收拢出一款，我会更倾向于推荐 {recommendation_payload['name']}。\n\n"
        f"{recommendation_payload['consultant_summary']}\n\n"
        + "\n".join(f"- {reason}" for reason in recommendation_payload["why_this"])
        + f"\n\n至于为什么我没有把重点放在别的选择上：{recommendation_payload['why_not_others']}"
    )


def stream_mock_response(
    planner: ConsultantPlan | None,
    recommendation_payload: dict[str, Any] | None,
):
    reply = mock_reply(planner, recommendation_payload)
    for char in reply:
        yield sse_event("chunk", {"text": char})
        time.sleep(0.01)

    if planner and planner.action == "recommend" and recommendation_payload:
        yield sse_event("product", {"product": recommendation_payload})

    yield sse_event(
        "meta",
        {
            "mode": "mock",
            "stage": "final_recommendation" if planner and planner.action == "recommend" else "clarify_atmosphere_or_function",
            "profile_summary": planner.profile_summary if planner else [],
        },
    )
    yield sse_event("done", {"source": "mock"})


def stream_openai_response(
    messages: list[ChatMessage],
    planner: ConsultantPlan | None,
    recommendation_payload: dict[str, Any] | None,
    fallback_stage: str,
    shortlist: list[dict[str, Any]],
):
    system_prompt = build_system_prompt(shortlist, recommendation_payload, planner, fallback_stage)
    client = create_openai_client()
    completion_stream = client.chat.completions.create(
        model=settings.openai_model,
        stream=True,
        temperature=0.35,
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

    if planner and planner.action == "recommend" and recommendation_payload:
        yield sse_event("product", {"product": recommendation_payload})

    yield sse_event(
        "meta",
        {
            "mode": settings.llm_provider,
            "stage": "final_recommendation" if planner and planner.action == "recommend" else "clarify_atmosphere_or_function",
            "profile_summary": planner.profile_summary if planner else [],
        },
    )
    yield sse_event("done", {"source": settings.llm_provider})


def stream_chat_response(messages: list[ChatMessage]):
    profile = extract_preference_profile(messages)
    fallback_summary = profile_summary(profile)
    fallback_stage = infer_stage(profile)
    local_shortlist = select_relevant_products(PRODUCTS_FILE, profile)
    live_shortlist: list[dict[str, Any]] = []
    planner: ConsultantPlan | None = None

    if settings.openai_api_key:
        try:
            live_shortlist = search_live_products(messages, profile, PRODUCTS_FILE)
        except Exception:
            live_shortlist = []

    shortlist = merge_shortlists(live_shortlist, local_shortlist)

    try:
        if settings.openai_api_key:
            client = create_openai_client()
            planner = generate_consultant_plan(
                client=client,
                model=settings.openai_model,
                messages=messages,
                shortlist=shortlist,
                fallback_summary=fallback_summary,
                fallback_stage=fallback_stage,
            )
    except Exception:
        planner = None

    recommendation_payload = resolve_recommendation_payload(PRODUCTS_FILE, profile, shortlist, planner)

    try:
        if settings.openai_api_key:
            yield from stream_openai_response(messages, planner, recommendation_payload, fallback_stage, shortlist)
            return
        yield from stream_mock_response(planner, recommendation_payload)
    except Exception as exc:
        yield sse_event("error", {"message": str(exc)})


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} backend is running."}


@app.get("/debug/provider")
async def debug_provider() -> dict[str, str]:
    return {
        "llm_provider": settings.llm_provider,
        "openai_model": settings.openai_model,
        "openai_base_url": settings.openai_base_url,
        "openai_api_key_masked": mask_secret(settings.openai_api_key),
    }


@app.get("/api/products/search")
async def product_search(keyword: str = Query(..., min_length=1)) -> dict[str, Any]:
    try:
        results = search_products(PRODUCTS_FILE, keyword)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"keyword": keyword, "count": len(results), "results": results}


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
