"""Small Gradio client for the project's MCP capability."""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

import gradio as gr
from mcp import Client

from .mcp_server import mcp


SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_-]+\.csv$")
OFFER_COLUMNS = [
    "offer_id",
    "display_name",
    "category",
    "reward_id",
    "reward_amount",
    "cost_id",
    "cost_amount",
    "badge_text",
    "enabled",
]


def _offer_rows(offers: list[dict[str, Any]]) -> list[list[Any]]:
    return [[offer.get(column, "") for column in OFFER_COLUMNS] for offer in offers]


async def call_shop_config_mcp(requirement: str, output_name: str) -> dict[str, Any]:
    """Call the public MCP tool instead of reaching into the Agent directly."""

    async with Client(mcp) as client:
        result = await client.call_tool(
            "generate_shop_config",
            {"requirement": requirement, "output_name": output_name},
        )
    if not isinstance(result.structured_content, dict):
        raise RuntimeError("MCP 工具没有返回结构化结果。")
    return result.structured_content


async def generate_from_ui(
    requirement: str,
    output_name: str,
    mcp_caller: Callable[[str, str], Awaitable[dict[str, Any]]] | None = None,
) -> tuple[str, list[list[Any]], dict[str, Any], str | None]:
    """Validate UI-only fields, call MCP, and map its result for display."""

    requirement = (requirement or "").strip()
    output_name = (output_name or "").strip()
    if not requirement:
        return "❌ 请输入商品需求。", [], {}, None
    if not SAFE_FILENAME.fullmatch(output_name):
        return (
            "❌ 文件名只能包含英文字母、数字、下划线或短横线，并以 `.csv` 结尾。",
            [],
            {},
            None,
        )

    caller = mcp_caller or call_shop_config_mcp
    try:
        state = await caller(requirement, output_name)
    except Exception as error:  # Keep the demo usable while preserving details for diagnosis.
        return f"❌ 运行失败：{error}", [], {}, None

    offers = state.get("offers", [])
    issues = state.get("issues", [])
    details = {
        "issues": issues,
        "defaults_applied": state.get("defaults_applied", []),
        "clarification_questions": state.get("clarification_questions", []),
    }
    if state.get("status") == "generated":
        return (
            f"✅ 已生成 {len(offers)} 条商品配置。",
            _offer_rows(offers),
            details,
            state.get("output_path"),
        )

    timed_out = any(
        issue.get("code") == "MODEL_EXTRACTION_FAILED"
        and "timed out" in str(issue.get("message", "")).lower()
        for issue in issues
    )
    if timed_out:
        return (
            "❌ 模型服务请求超时。需求本身不一定有问题，请稍后重试或拆成两批。",
            [],
            details,
            None,
        )

    questions = state.get("clarification_questions", [])
    question_text = "\n".join(f"- {question}" for question in questions)
    status = "⚠️ 需求需要补充，未生成 CSV。"
    if question_text:
        status += f"\n\n{question_text}"
    return status, _offer_rows(offers), details, None


async def generate_with_logs(
    requirement: str,
    output_name: str,
    mcp_caller: Callable[[str, str], Awaitable[dict[str, Any]]] | None = None,
):
    """Stream safe progress messages while the MCP request is running."""

    started_at = time.monotonic()
    logs = ["[1/4] 已接收需求，正在检查输入和输出文件名。"]
    yield "⏳ 正在准备请求……", [], {}, None, "\n".join(logs)

    requirement = (requirement or "").strip()
    output_name = (output_name or "").strip()
    if not requirement or not SAFE_FILENAME.fullmatch(output_name):
        result = await generate_from_ui(requirement, output_name, mcp_caller)
        logs.append("[结束] 输入检查未通过，尚未调用 MCP。")
        yield (*result, "\n".join(logs))
        return

    logs.append("[2/4] 输入检查通过，正在调用 MCP Tool：generate_shop_config。")
    logs.append("[3/4] MCP 已进入 LangGraph，模型正在提取候选商品。")
    yield "⏳ 模型正在理解商品需求……", [], {}, None, "\n".join(logs)

    task = asyncio.create_task(generate_from_ui(requirement, output_name, mcp_caller))
    while not task.done():
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=10)
        except TimeoutError:
            elapsed = int(time.monotonic() - started_at)
            heartbeat_logs = [
                *logs,
                f"[等待] 已运行 {elapsed} 秒；模型 SDK 可能会在请求超时时自动重试。",
            ]
            yield (
                f"⏳ 模型处理中，已等待 {elapsed} 秒……",
                [],
                {},
                None,
                "\n".join(heartbeat_logs),
            )

    result = task.result()
    elapsed = int(time.monotonic() - started_at)
    issue_codes = [
        issue.get("code", "UNKNOWN") for issue in result[2].get("issues", [])
    ]
    if result[3]:
        logs.append(f"[4/4] 校验通过并生成 CSV，总耗时 {elapsed} 秒。")
    elif issue_codes:
        logs.append(
            f"[4/4] 未生成 CSV；错误代码：{', '.join(issue_codes)}；总耗时 {elapsed} 秒。"
        )
    else:
        logs.append(f"[4/4] 请求结束但未生成 CSV，总耗时 {elapsed} 秒。")
    yield (*result, "\n".join(logs))


def build_app() -> gr.Blocks:
    """Build the UI without launching it, so construction stays testable."""

    with gr.Blocks(title="Unity 商店配置 Agent") as demo:
        gr.Markdown(
            "# Unity 商店配置 Agent\n"
            "把策划的自然语言需求转换为经过校验、可由 Unity 读取的 CSV。"
        )
        with gr.Row():
            with gr.Column(scale=2):
                requirement = gr.Textbox(
                    label="商品需求",
                    lines=7,
                    placeholder="例如：一把剑售价15金币；三个盾牌售价20金币并标记Best Value。",
                )
                output_name = gr.Textbox(
                    label="输出文件名",
                    value="gradio_generated_offers.csv",
                    info="使用英文、数字、下划线或短横线，并以 .csv 结尾。",
                )
                generate_button = gr.Button("生成并校验", variant="primary")
            with gr.Column(scale=1):
                status = gr.Markdown("等待输入。")
                download = gr.File(label="下载 CSV", interactive=False)
                logs = gr.Textbox(
                    label="运行日志",
                    value="等待任务开始。",
                    lines=7,
                    interactive=False,
                )

        offers = gr.Dataframe(
            headers=OFFER_COLUMNS,
            datatype=["str", "str", "str", "str", "number", "str", "number", "str", "bool"],
            label="正式商品配置预览",
            interactive=False,
        )
        details = gr.JSON(label="校验、默认值与补充问题")

        generate_button.click(
            fn=generate_with_logs,
            inputs=[requirement, output_name],
            outputs=[status, offers, details, download, logs],
            api_name="generate_shop_config",
            show_progress="full",
            concurrency_limit=1,
        )

    return demo


def main() -> None:
    """Launch the local team demo."""

    build_app().queue(default_concurrency_limit=1).launch(inbrowser=True)


if __name__ == "__main__":
    main()
