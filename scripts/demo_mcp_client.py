"""Call the project MCP server in memory to make the data flow visible."""

import argparse
import asyncio
import json
import logging
import sys

from mcp import Client

from game_config_agent.mcp_server import mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal MCP client demo")
    parser.add_argument("requirement", help="Natural-language shop requirement")
    parser.add_argument("--output-name", default="mcp_demo_offers.csv")
    return parser


async def run(requirement: str, output_name: str) -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("MCP discovered tools:")
        print(json.dumps([tool.name for tool in tools.tools], ensure_ascii=False, indent=2))

        result = await client.call_tool(
            "generate_shop_config",
            {"requirement": requirement, "output_name": output_name},
        )
        print("MCP tool result:")
        print(json.dumps(result.structured_content, ensure_ascii=False, indent=2))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.getLogger().setLevel(logging.WARNING)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.WARNING)
    logging.getLogger("langchain_openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    args = build_parser().parse_args()
    asyncio.run(run(args.requirement, args.output_name))


if __name__ == "__main__":
    main()
