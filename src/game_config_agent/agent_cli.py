"""Command-line entry point for the LangGraph shop configuration agent."""

import argparse
import json
import sys
from pathlib import Path

from .agent import run_shop_agent
from .settings import SettingsError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a natural-language shop requirement into validated Unity CSV."
    )
    parser.add_argument("requirement", help="Natural-language shop requirement")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/agent_generated_offers.csv"),
        help="Destination CSV path",
    )
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    try:
        result = run_shop_agent(args.requirement, args.output)
    except SettingsError as error:
        print(json.dumps({"status": "configuration_error", "error": str(error)}, ensure_ascii=False))
        return 2
    except Exception as error:
        print(json.dumps({"status": "runtime_error", "error": str(error)}, ensure_ascii=False))
        return 2

    visible_result = {
        key: result.get(key)
        for key in (
            "status",
            "candidates",
            "offers",
            "issues",
            "defaults_applied",
            "clarification_questions",
            "output_path",
        )
        if key in result
    }
    print(json.dumps(visible_result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "generated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
