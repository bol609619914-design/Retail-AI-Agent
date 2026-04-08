import json
from dataclasses import dataclass
from typing import Any, Literal

from openai import OpenAI

from app.models import ChatMessage


PlannerAction = Literal["ask", "recommend"]


@dataclass
class ConsultantPlan:
    action: PlannerAction
    profile_summary: list[str]
    next_focus: str
    reasoning: str
    recommended_product_name: str | None = None


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Planner did not return a JSON object.")
    return json.loads(text[start : end + 1])


def _normalize_action(value: str | None, fallback_stage: str) -> PlannerAction:
    if value == "recommend":
        return "recommend"
    if value == "ask":
        return "ask"
    return "recommend" if fallback_stage == "final_recommendation" else "ask"


def build_planner_prompt(
    messages: list[ChatMessage],
    shortlist: list[dict[str, Any]],
    fallback_summary: list[str],
    fallback_stage: str,
) -> str:
    shortlist_json = json.dumps(shortlist, ensure_ascii=False, indent=2)
    transcript = "\n".join(f"{message.role}: {message.content}" for message in messages)
    summary_text = "；".join(fallback_summary) if fallback_summary else "当前还没有稳定收敛出的偏好。"

    return f"""
你是一位高端零售顾问背后的内部判断器。
你的任务不是直接回复用户，而是先判断这一轮最合适的顾问动作。

请严格阅读对话与候选产品，只输出一个 JSON 对象，不要输出 JSON 之外的任何内容。

判断原则：
1. 如果信息还不够，不要急着推荐，优先判断下一步最值得追问的点。
2. 如果用户已经明确说出空间、氛围、功能中的两到三项，而且偏好已经足够收敛，可以进入推荐。
3. 如果决定推荐，只能从候选产品中选一款。
4. 优先理解用户真正想要的生活方式，不要机械复读关键词。
5. 如果用户明确强调某个功能，例如阅读、照明、香氛、音乐、咖啡，请优先尊重功能主诉求。

输出 JSON 结构：
{{
  "action": "ask" 或 "recommend",
  "profile_summary": ["空间：卧室", "氛围：柔和", "功能：照明"],
  "next_focus": "下一步最该追问或解释的焦点，简短中文",
  "reasoning": "内部判断理由，简短中文",
  "recommended_product_name": "如果 action 是 recommend，这里必须是候选产品中的一个名字，否则为 null"
}}

当前规则层摘要：{summary_text}
当前规则层阶段：{fallback_stage}

最近对话：
{transcript}

候选产品：
{shortlist_json}
""".strip()


def generate_consultant_plan(
    client: OpenAI,
    model: str,
    messages: list[ChatMessage],
    shortlist: list[dict[str, Any]],
    fallback_summary: list[str],
    fallback_stage: str,
) -> ConsultantPlan:
    prompt = build_planner_prompt(messages, shortlist, fallback_summary, fallback_stage)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "你只输出 JSON，不要输出解释，不要使用 markdown 代码块。",
            },
            {"role": "user", "content": prompt},
        ],
    )

    content = completion.choices[0].message.content or "{}"
    payload = _extract_json_object(content)
    action = _normalize_action(payload.get("action"), fallback_stage)
    summary = payload.get("profile_summary") or fallback_summary
    next_focus = str(payload.get("next_focus") or "继续理解用户现在最在意的生活重点。")
    reasoning = str(payload.get("reasoning") or "基于当前对话做出的顾问判断。")
    recommended_product_name = payload.get("recommended_product_name")

    shortlist_names = {product.get("name") for product in shortlist}
    if action == "recommend" and recommended_product_name not in shortlist_names:
        recommended_product_name = shortlist[0]["name"] if shortlist else None

    return ConsultantPlan(
        action=action,
        profile_summary=summary[:6] if isinstance(summary, list) else fallback_summary,
        next_focus=next_focus,
        reasoning=reasoning,
        recommended_product_name=recommended_product_name,
    )
