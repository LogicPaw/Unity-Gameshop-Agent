"""Human-operated CLI for exercising the deterministic configuration tools."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from .catalog import ResourceCatalog
from .models import CandidateOffer
from .tools import ExportBlockedError, OfferConfigTools


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = PROJECT_ROOT / "data/raw/unity_virtual_shop/official_snapshot.json"
DEFAULT_ALIASES = PROJECT_ROOT / "data/reference/resource_aliases.zh-CN.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a validated Unity shop CSV from structured JSON input."
    )
    parser.add_argument("input", type=Path, help="JSON file containing a list of candidate offers")
    parser.add_argument("output", type=Path, help="Destination CSV path")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    try:
        raw_input = json.loads(args.input.read_text(encoding="utf-8"))
        candidates = TypeAdapter(list[CandidateOffer]).validate_python(raw_input)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        print(json.dumps({"status": "invalid_input", "error": str(error)}, ensure_ascii=False))
        return 2

    catalog = ResourceCatalog.from_files(args.snapshot, args.aliases)
    tools = OfferConfigTools(catalog)
    result = tools.build(candidates)

    if not result.is_valid:
        print(
            json.dumps(
                {
                    "status": "needs_clarification",
                    "issues": [issue.model_dump() for issue in result.issues],
                    "defaults_applied": [
                        default.model_dump() for default in result.defaults_applied
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    try:
        output_path = tools.export_csv(result, args.output)
    except ExportBlockedError as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, ensure_ascii=False))
        return 1

    print(
        json.dumps(
            {
                "status": "generated",
                "offer_count": len(result.offers),
                "output": str(output_path.resolve()),
                "defaults_applied": [
                    default.model_dump() for default in result.defaults_applied
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
