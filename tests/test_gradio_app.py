"""Tests for the thin Gradio presentation layer."""

import unittest
from unittest.mock import patch

from game_config_agent.gradio_app import (
    call_shop_config_mcp,
    generate_from_ui,
    generate_with_logs,
)


class GradioAppTests(unittest.IsolatedAsyncioTestCase):
    async def test_gradio_client_reaches_agent_through_public_mcp_tool(self) -> None:
        fake_state = {
            "status": "generated",
            "offers": [{"offer_id": "VIRTUAL_SHOP_1_SWORD_FOR_COINS"}],
            "issues": [],
            "defaults_applied": [],
            "clarification_questions": [],
            "output_path": "C:/fake/from_gradio.csv",
        }

        with patch(
            "game_config_agent.mcp_server.run_shop_agent",
            return_value=fake_state,
        ) as agent:
            result = await call_shop_config_mcp("一把剑售价15金币", "from_gradio.csv")

        agent.assert_called_once()
        self.assertEqual(result["status"], "generated")
        self.assertEqual(
            result["offers"][0]["offer_id"],
            "VIRTUAL_SHOP_1_SWORD_FOR_COINS",
        )

    async def test_generated_result_is_mapped_to_table_and_download(self) -> None:
        async def fake_mcp_caller(requirement: str, output_name: str) -> dict:
            self.assertEqual(requirement, "一把剑售价15金币")
            self.assertEqual(output_name, "demo.csv")
            return {
                "status": "generated",
                "offers": [
                    {
                        "offer_id": "VIRTUAL_SHOP_1_SWORD_FOR_COINS",
                        "display_name": "Sword",
                        "category": "Inventory Item",
                        "reward_id": "SWORD",
                        "reward_amount": 1,
                        "cost_id": "COIN",
                        "cost_amount": 15,
                        "badge_text": "",
                        "enabled": True,
                    }
                ],
                "issues": [],
                "defaults_applied": [{"field": "reward_amount", "value": 1}],
                "clarification_questions": [],
                "output_path": "C:/fake/demo.csv",
            }

        status, rows, details, download = await generate_from_ui(
            "一把剑售价15金币", "demo.csv", fake_mcp_caller
        )

        self.assertIn("已生成 1 条", status)
        self.assertEqual(rows[0][3:7], ["SWORD", 1, "COIN", 15])
        self.assertEqual(details["issues"], [])
        self.assertTrue(download.endswith("demo.csv"))

    async def test_clarification_result_has_no_download(self) -> None:
        async def fake_mcp_caller(_requirement: str, _output_name: str) -> dict:
            return {
                "status": "needs_clarification",
                "offers": [],
                "issues": [{"code": "UNKNOWN_REWARD"}],
                "defaults_applied": [],
                "clarification_questions": ["水晶剑对应哪个资源 ID？"],
                "output_path": None,
            }

        status, rows, details, download = await generate_from_ui(
            "水晶剑售价200宝石", "demo.csv", fake_mcp_caller
        )

        self.assertIn("未生成 CSV", status)
        self.assertIn("水晶剑", status)
        self.assertEqual(rows, [])
        self.assertEqual(details["issues"][0]["code"], "UNKNOWN_REWARD")
        self.assertIsNone(download)

    async def test_unsafe_filename_is_rejected_before_mcp_call(self) -> None:
        called = False

        async def fake_mcp_caller(_requirement: str, _output_name: str) -> dict:
            nonlocal called
            called = True
            return {}

        status, _, _, download = await generate_from_ui(
            "一把剑售价15金币", "../escape.csv", fake_mcp_caller
        )

        self.assertIn("文件名", status)
        self.assertFalse(called)
        self.assertIsNone(download)

    async def test_progress_logs_wrap_the_mcp_call(self) -> None:
        async def fake_mcp_caller(_requirement: str, _output_name: str) -> dict:
            await __import__("asyncio").sleep(0)
            return {
                "status": "generated",
                "offers": [],
                "issues": [],
                "defaults_applied": [],
                "clarification_questions": [],
                "output_path": "C:/fake/logged.csv",
            }

        updates = [
            update
            async for update in generate_with_logs(
                "一把剑售价15金币", "logged.csv", fake_mcp_caller
            )
        ]

        self.assertGreaterEqual(len(updates), 3)
        self.assertIn("正在调用 MCP Tool", updates[1][4])
        self.assertIn("校验通过并生成 CSV", updates[-1][4])

    async def test_timeout_is_reported_as_service_error(self) -> None:
        async def fake_mcp_caller(_requirement: str, _output_name: str) -> dict:
            return {
                "status": "needs_clarification",
                "offers": [],
                "issues": [
                    {
                        "code": "MODEL_EXTRACTION_FAILED",
                        "message": "Request timed out.",
                    }
                ],
                "defaults_applied": [],
                "clarification_questions": ["请补充或修正"],
                "output_path": None,
            }

        status, _, _, download = await generate_from_ui(
            "复杂需求", "timeout.csv", fake_mcp_caller
        )

        self.assertIn("模型服务请求超时", status)
        self.assertNotIn("补充需求", status)
        self.assertIsNone(download)


if __name__ == "__main__":
    unittest.main()
