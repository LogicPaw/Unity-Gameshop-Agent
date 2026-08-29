"""LangGraph orchestration for natural-language shop configuration."""

import json
from pathlib import Path
from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from .catalog import ResourceCatalog
from .models import (
    BuildResult,
    CandidateOffer,
    CandidateOfferBatch,
    DefaultApplied,
    ShopOffer,
    ValidationIssue,
)
from .settings import ModelSettings, PROJECT_ROOT
from .skill_loader import load_shop_skill
from .tools import OfferConfigTools


DEFAULT_SNAPSHOT = PROJECT_ROOT / "data/raw/unity_virtual_shop/official_snapshot.json"
DEFAULT_ALIASES = PROJECT_ROOT / "data/reference/resource_aliases.zh-CN.json"


class AgentState(TypedDict, total=False):
    requirement: str
    requested_output_path: str
    output_path: str
    candidates: list[dict[str, Any]]
    offers: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    defaults_applied: list[dict[str, Any]]
    clarification_questions: list[str]
    model_raw_output: str
    status: str


class ModelExtractionError(ValueError):
    """Raised when model output cannot become CandidateOffer data."""


def create_chat_model(settings: ModelSettings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.model,
        api_key=settings.api_key,
        base_url=settings.base_url,
        temperature=0,
        timeout=60,
        max_retries=2,
    )


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return str(content)


def _extract_first_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ModelExtractionError("模型没有返回可解析的 JSON 对象")


def parse_candidate_batch(text: str) -> CandidateOfferBatch:
    try:
        payload = _extract_first_json_object(text)
        return CandidateOfferBatch.model_validate(payload)
    except Exception as error:
        if isinstance(error, ModelExtractionError):
            raise
        raise ModelExtractionError(f"模型输出不符合 CandidateOffer Schema：{error}") from error


def create_shop_graph(llm: Any, config_tools: OfferConfigTools):
    skill_text = load_shop_skill()
    schema = json.dumps(
        CandidateOfferBatch.model_json_schema(),
        ensure_ascii=False,
        indent=2,
    )

    def extract_offers(state: AgentState) -> AgentState:
        system_prompt = f"""
You are the extraction node of a Unity virtual-shop configuration workflow.
Follow the project skill and domain rules below. Return only one JSON object that
matches the supplied schema. Do not resolve IDs, apply defaults, validate master
data, or write CSV. Preserve the order of batch offers.

<project_skill>
{skill_text}
</project_skill>

<output_schema>
{schema}
</output_schema>
""".strip()
        try:
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=state["requirement"]),
                ]
            )
            raw_output = _content_to_text(response.content)
            batch = parse_candidate_batch(raw_output)
            return {
                "candidates": [offer.model_dump() for offer in batch.offers],
                "issues": [],
                "model_raw_output": raw_output,
                "status": "extracted",
            }
        except Exception as error:
            issue = ValidationIssue(
                offer_index=0,
                code="MODEL_EXTRACTION_FAILED",
                field="requirement",
                message=str(error),
            )
            return {
                "candidates": [],
                "issues": [issue.model_dump()],
                "status": "extraction_failed",
            }

    def build_offers(state: AgentState) -> AgentState:
        if state.get("issues"):
            return {"status": "build_blocked"}

        candidates = [
            CandidateOffer.model_validate(candidate)
            for candidate in state.get("candidates", [])
        ]
        result = config_tools.build(candidates)
        return {
            "offers": [offer.model_dump() for offer in result.offers],
            "issues": [issue.model_dump() for issue in result.issues],
            "defaults_applied": [
                default.model_dump() for default in result.defaults_applied
            ],
            "status": "validated" if result.is_valid else "validation_failed",
        }

    def route_after_build(state: AgentState) -> Literal["clarify", "export"]:
        return "clarify" if state.get("issues") else "export"

    def clarify(state: AgentState) -> AgentState:
        questions = []
        for raw_issue in state.get("issues", []):
            issue = ValidationIssue.model_validate(raw_issue)
            questions.append(
                f"第 {issue.offer_index + 1} 条配置：{issue.message}。请补充或修正。"
            )
        return {
            "clarification_questions": questions,
            "status": "needs_clarification",
        }

    def export(state: AgentState) -> AgentState:
        result = BuildResult(
            offers=[ShopOffer.model_validate(item) for item in state.get("offers", [])],
            issues=[],
            defaults_applied=[
                DefaultApplied.model_validate(item)
                for item in state.get("defaults_applied", [])
            ],
        )
        output = config_tools.export_csv(result, state["requested_output_path"])
        return {"output_path": str(output.resolve()), "status": "generated"}

    builder = StateGraph(AgentState)
    builder.add_node("extract", extract_offers)
    builder.add_node("build", build_offers)
    builder.add_node("clarify", clarify)
    builder.add_node("export", export)
    builder.add_edge(START, "extract")
    builder.add_edge("extract", "build")
    builder.add_conditional_edges(
        "build",
        route_after_build,
        {"clarify": "clarify", "export": "export"},
    )
    builder.add_edge("clarify", END)
    builder.add_edge("export", END)
    return builder.compile()


def create_default_graph(env_path: str | Path | None = None):
    settings = ModelSettings.from_env(env_path)
    llm = create_chat_model(settings)
    catalog = ResourceCatalog.from_files(DEFAULT_SNAPSHOT, DEFAULT_ALIASES)
    return create_shop_graph(llm, OfferConfigTools(catalog))


def run_shop_agent(
    requirement: str,
    output_path: str | Path,
    *,
    graph: Any | None = None,
) -> AgentState:
    runnable = graph or create_default_graph()
    return runnable.invoke(
        {
            "requirement": requirement,
            "requested_output_path": str(output_path),
            "status": "started",
        }
    )
