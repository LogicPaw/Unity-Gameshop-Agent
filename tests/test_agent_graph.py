import json
import tempfile
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage

from game_config_agent.agent import create_shop_graph, run_shop_agent
from game_config_agent.catalog import ResourceCatalog
from game_config_agent.tools import OfferConfigTools


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = PROJECT_ROOT / "data/raw/unity_virtual_shop/official_snapshot.json"
ALIASES = PROJECT_ROOT / "data/reference/resource_aliases.zh-CN.json"


class FakeChatModel:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def invoke(self, messages):
        return AIMessage(content=json.dumps(self.payload, ensure_ascii=False))


def make_graph(payload: dict):
    catalog = ResourceCatalog.from_files(SNAPSHOT, ALIASES)
    return create_shop_graph(FakeChatModel(payload), OfferConfigTools(catalog))


class AgentGraphTests(unittest.TestCase):
    def test_valid_requirement_routes_to_export(self) -> None:
        graph = make_graph(
            {
                "offers": [
                    {
                        "item_name": "剑",
                        "reward_amount": 1,
                        "currency_name": "金币",
                        "cost_amount": 15,
                        "display_name": None,
                        "category": None,
                        "badge_text": None,
                        "enabled": None,
                    }
                ]
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "agent.csv"
            result = run_shop_agent("一把剑售价15金币", output, graph=graph)
            self.assertTrue(output.exists())

        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["offers"][0]["reward_id"], "SWORD")

    def test_unknown_resource_routes_to_clarification_without_csv(self) -> None:
        graph = make_graph(
            {
                "offers": [
                    {
                        "item_name": "水晶剑",
                        "reward_amount": 1,
                        "currency_name": "宝石",
                        "cost_amount": 200,
                        "display_name": None,
                        "category": None,
                        "badge_text": None,
                        "enabled": None,
                    }
                ]
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "must-not-exist.csv"
            result = run_shop_agent("水晶剑售价200宝石", output, graph=graph)
            self.assertFalse(output.exists())

        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["issues"][0]["code"], "UNKNOWN_REWARD")
        self.assertTrue(result["clarification_questions"])
        self.assertNotIn("output_path", result)

    def test_invalid_model_output_routes_to_clarification(self) -> None:
        graph = make_graph({"unexpected": []})
        with tempfile.TemporaryDirectory() as directory:
            result = run_shop_agent(
                "任意输入",
                Path(directory) / "must-not-exist.csv",
                graph=graph,
            )

        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual(result["issues"][0]["code"], "MODEL_EXTRACTION_FAILED")


if __name__ == "__main__":
    unittest.main()
