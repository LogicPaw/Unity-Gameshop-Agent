import csv
import json
import tempfile
import unittest
from pathlib import Path

from game_config_agent.catalog import ResourceCatalog
from game_config_agent.models import CandidateOffer
from game_config_agent.tools import CSV_COLUMNS, ExportBlockedError, OfferConfigTools


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = PROJECT_ROOT / "data/raw/unity_virtual_shop/official_snapshot.json"
ALIASES = PROJECT_ROOT / "data/reference/resource_aliases.zh-CN.json"


class OfferConfigToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        catalog = ResourceCatalog.from_files(SNAPSHOT, ALIASES)
        self.tools = OfferConfigTools(catalog)

    def test_builds_three_official_offers(self) -> None:
        result = self.tools.build(
            [
                CandidateOffer(item_name="剑", currency_name="金币", cost_amount=15),
                CandidateOffer(
                    item_name="盾牌",
                    reward_amount=3,
                    currency_name="金币",
                    cost_amount=20,
                    badge_text="Best Value",
                ),
                CandidateOffer(
                    item_name="金币",
                    reward_amount=100,
                    currency_name="宝石",
                    cost_amount=7,
                ),
            ]
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(
            [offer.offer_id for offer in result.offers],
            [
                "VIRTUAL_SHOP_1_SWORD_FOR_COINS",
                "VIRTUAL_SHOP_3_SHIELD_FOR_COINS",
                "VIRTUAL_SHOP_100_COIN_FOR_GEMS",
            ],
        )
        self.assertEqual(result.offers[0].reward_amount, 1)
        self.assertEqual(result.offers[2].category, "Currencies")

        snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        official_by_id = {
            purchase["offer_id"]: purchase for purchase in snapshot["purchases"]
        }
        for offer in result.offers:
            expected = official_by_id[offer.offer_id]
            self.assertEqual(
                offer.model_dump(),
                {key: expected[key] for key in type(offer).model_fields},
            )

    def test_unknown_resource_and_missing_currency_block_export(self) -> None:
        result = self.tools.build(
            [CandidateOffer(item_name="水晶剑", cost_amount=200)]
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(
            {issue.code for issue in result.issues},
            {"UNKNOWN_REWARD", "MISSING_CURRENCY"},
        )
        with self.assertRaises(ExportBlockedError):
            self.tools.export_csv(result, "should-not-exist.csv")

    def test_invalid_values_and_non_currency_cost_are_rejected(self) -> None:
        result = self.tools.build(
            [
                CandidateOffer(
                    item_name="盾牌",
                    reward_amount=0,
                    currency_name="剑",
                    cost_amount=-5,
                )
            ]
        )
        self.assertEqual(
            {issue.code for issue in result.issues},
            {"INVALID_COST_TYPE", "INVALID_REWARD_AMOUNT", "INVALID_PRICE"},
        )

    def test_duplicate_offer_ids_are_rejected(self) -> None:
        candidate = CandidateOffer(
            item_name="剑",
            currency_name="金币",
            cost_amount=15,
        )
        result = self.tools.build([candidate, candidate])
        self.assertFalse(result.is_valid)
        self.assertEqual(
            [issue.code for issue in result.issues],
            ["DUPLICATE_OFFER_ID", "DUPLICATE_OFFER_ID"],
        )

    def test_exports_fixed_unity_csv_schema(self) -> None:
        result = self.tools.build(
            [CandidateOffer(item_name="剑", currency_name="金币", cost_amount=15)]
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "offers.csv"
            self.tools.export_csv(result, output)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(list(rows[0].keys()), CSV_COLUMNS)
        self.assertEqual(rows[0]["reward_id"], "SWORD")
        self.assertEqual(rows[0]["cost_amount"], "15")
        self.assertEqual(rows[0]["enabled"], "true")


if __name__ == "__main__":
    unittest.main()
