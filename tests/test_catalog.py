import unittest
from pathlib import Path

from game_config_agent.catalog import CatalogDataError, ResourceCatalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = PROJECT_ROOT / "data/raw/unity_virtual_shop/official_snapshot.json"
ALIASES = PROJECT_ROOT / "data/reference/resource_aliases.zh-CN.json"


class ResourceCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = ResourceCatalog.from_files(SNAPSHOT, ALIASES)

    def test_loads_exact_official_resource_ids(self) -> None:
        self.assertEqual(
            {resource.id for resource in self.catalog.resources},
            {"COIN", "GEM", "PEARL", "STAR", "SWORD", "SHIELD"},
        )

    def test_resolves_id_english_name_and_chinese_alias(self) -> None:
        self.assertEqual(self.catalog.resolve("SWORD").id, "SWORD")
        self.assertEqual(self.catalog.resolve("sword").id, "SWORD")
        self.assertEqual(self.catalog.resolve("剑").id, "SWORD")
        self.assertEqual(self.catalog.resolve("金币").id, "COIN")

    def test_unknown_resource_is_not_invented(self) -> None:
        self.assertIsNone(self.catalog.resolve("水晶剑"))

    def test_alias_must_point_to_official_resource(self) -> None:
        with self.assertRaises(CatalogDataError):
            ResourceCatalog(list(self.catalog.resources), {"水晶剑": "CRYSTAL_SWORD"})


if __name__ == "__main__":
    unittest.main()
