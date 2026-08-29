"""Minimal MCP adapter around the existing LangGraph agent."""

from pathlib import Path
from typing import Annotated, Any

from mcp.server import MCPServer
from pydantic import BaseModel, ConfigDict, Field

from .agent import run_shop_agent
from .settings import PROJECT_ROOT


MCP_OUTPUT_DIR = PROJECT_ROOT / "outputs/mcp"


class GenerateShopConfigResult(BaseModel):
    """Stable result returned to MCP clients."""

    model_config = ConfigDict(extra="forbid")

    status: str
    offers: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    defaults_applied: list[dict[str, Any]] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    output_path: str | None = None


mcp = MCPServer(
    "Unity Shop Config",
    version="0.1.0",
    instructions=(
        "Generate validated Unity virtual-shop CSV files from natural-language "
        "requirements. Invalid or incomplete requests return clarification questions "
        "and do not create a CSV."
    ),
)


@mcp.tool(title="Generate Unity shop configuration")
def generate_shop_config(
    requirement: Annotated[
        str,
        Field(
            min_length=1,
            description="Natural-language virtual-shop requirement, including reward, price, and currency.",
        ),
    ],
    output_name: Annotated[
        str,
        Field(
            pattern=r"^[A-Za-z0-9_-]+\.csv$",
            description="Safe CSV filename written under the server-controlled outputs/mcp directory.",
        ),
    ] = "mcp_generated_offers.csv",
) -> GenerateShopConfigResult:
    """Run the existing Skill-driven LangGraph and return its business result."""

    output_path = MCP_OUTPUT_DIR / output_name
    state = run_shop_agent(requirement, output_path)
    return GenerateShopConfigResult(
        status=state.get("status", "runtime_error"),
        offers=state.get("offers", []),
        issues=state.get("issues", []),
        defaults_applied=state.get("defaults_applied", []),
        clarification_questions=state.get("clarification_questions", []),
        output_path=state.get("output_path"),
    )


def main() -> None:
    """Run the local MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
