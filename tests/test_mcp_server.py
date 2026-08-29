import asyncio
import unittest
from unittest.mock import patch

from mcp import Client

from game_config_agent.mcp_server import mcp


class McpServerTests(unittest.TestCase):
    def test_client_discovers_and_calls_generate_tool(self) -> None:
        fake_state = {
            "status": "generated",
            "offers": [{"offer_id": "VIRTUAL_SHOP_1_SWORD_FOR_COINS"}],
            "issues": [],
            "defaults_applied": [],
            "output_path": "C:/fake/mcp_test.csv",
        }

        async def exercise_protocol():
            with patch(
                "game_config_agent.mcp_server.run_shop_agent",
                return_value=fake_state,
            ):
                async with Client(mcp) as client:
                    listed = await client.list_tools()
                    names = [tool.name for tool in listed.tools]
                    result = await client.call_tool(
                        "generate_shop_config",
                        {
                            "requirement": "一把剑售价15金币",
                            "output_name": "mcp_test.csv",
                        },
                    )
                    return names, result.structured_content

        names, content = asyncio.run(exercise_protocol())
        self.assertEqual(names, ["generate_shop_config"])
        self.assertEqual(content["status"], "generated")
        self.assertEqual(
            content["offers"][0]["offer_id"],
            "VIRTUAL_SHOP_1_SWORD_FOR_COINS",
        )


if __name__ == "__main__":
    unittest.main()
