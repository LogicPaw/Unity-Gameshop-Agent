"""Deterministic tools used by humans now and by the agent later."""

import csv
from pathlib import Path

from .catalog import ResourceCatalog
from .models import (
    BuildResult,
    CandidateOffer,
    DefaultApplied,
    ShopOffer,
    ValidationIssue,
)


CSV_COLUMNS = [
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


class ExportBlockedError(ValueError):
    """Raised when an invalid build result is passed to the exporter."""


class OfferConfigTools:
    """Resolve, validate, and export shop offers without using an LLM."""

    def __init__(self, catalog: ResourceCatalog) -> None:
        self.catalog = catalog

    def build(self, candidates: list[CandidateOffer]) -> BuildResult:
        offers: list[ShopOffer] = []
        offer_source_indexes: list[int] = []
        issues: list[ValidationIssue] = []
        defaults: list[DefaultApplied] = []

        for index, candidate in enumerate(candidates):
            offer, item_issues, item_defaults = self._build_one(candidate, index)
            issues.extend(item_issues)
            defaults.extend(item_defaults)
            if offer is not None:
                offers.append(offer)
                offer_source_indexes.append(index)

        duplicates: dict[str, list[int]] = {}
        for source_index, offer in zip(offer_source_indexes, offers, strict=True):
            duplicates.setdefault(offer.offer_id, []).append(source_index)
        for offer_id, indexes in duplicates.items():
            if len(indexes) > 1:
                for index in indexes:
                    issues.append(
                        ValidationIssue(
                            offer_index=index,
                            code="DUPLICATE_OFFER_ID",
                            field="offer_id",
                            message=f"生成了重复的 offer_id：{offer_id}",
                        )
                    )

        return BuildResult(
            offers=offers,
            issues=issues,
            defaults_applied=defaults,
        )

    def _build_one(
        self,
        candidate: CandidateOffer,
        index: int,
    ) -> tuple[ShopOffer | None, list[ValidationIssue], list[DefaultApplied]]:
        issues: list[ValidationIssue] = []
        defaults: list[DefaultApplied] = []

        reward = self.catalog.resolve(candidate.item_name)
        if not candidate.item_name:
            issues.append(self._issue(index, "MISSING_REWARD", "item_name", "缺少商品名称"))
        elif reward is None:
            issues.append(
                self._issue(
                    index,
                    "UNKNOWN_REWARD",
                    "item_name",
                    f"资源主数据中不存在：{candidate.item_name}",
                )
            )

        cost = self.catalog.resolve(candidate.currency_name)
        if not candidate.currency_name:
            issues.append(
                self._issue(index, "MISSING_CURRENCY", "currency_name", "缺少货币类型")
            )
        elif cost is None:
            issues.append(
                self._issue(
                    index,
                    "UNKNOWN_CURRENCY",
                    "currency_name",
                    f"资源主数据中不存在：{candidate.currency_name}",
                )
            )
        elif cost.resource_type != "Currency":
            issues.append(
                self._issue(
                    index,
                    "INVALID_COST_TYPE",
                    "currency_name",
                    f"{cost.id} 不是货币，不能作为当前 MVP 的支付资源",
                )
            )

        reward_amount = candidate.reward_amount
        if reward_amount is None:
            reward_amount = 1
            defaults.append(
                DefaultApplied(
                    offer_index=index,
                    field="reward_amount",
                    value=1,
                    reason="用户未提供一组数量，使用 MVP 默认值",
                )
            )
        elif reward_amount <= 0:
            issues.append(
                self._issue(
                    index,
                    "INVALID_REWARD_AMOUNT",
                    "reward_amount",
                    "奖励数量必须是正整数",
                )
            )

        if candidate.cost_amount is None:
            issues.append(self._issue(index, "MISSING_PRICE", "cost_amount", "缺少价格"))
        elif candidate.cost_amount <= 0:
            issues.append(
                self._issue(
                    index,
                    "INVALID_PRICE",
                    "cost_amount",
                    "价格必须是正整数",
                )
            )

        enabled = candidate.enabled
        if enabled is None:
            enabled = True
            defaults.append(
                DefaultApplied(
                    offer_index=index,
                    field="enabled",
                    value=True,
                    reason="用户未指定启用状态，使用 MVP 默认值",
                )
            )

        badge_text = candidate.badge_text
        if badge_text is None:
            badge_text = ""
            defaults.append(
                DefaultApplied(
                    offer_index=index,
                    field="badge_text",
                    value="",
                    reason="用户未提供展示标签，使用空字符串",
                )
            )

        if reward is not None:
            inferred_category = (
                "Items" if reward.resource_type == "Inventory Item" else "Currencies"
            )
            if candidate.category is not None and candidate.category != inferred_category:
                issues.append(
                    self._issue(
                        index,
                        "CATEGORY_MISMATCH",
                        "category",
                        f"资源 {reward.id} 应属于 {inferred_category}，不是 {candidate.category}",
                    )
                )
        else:
            inferred_category = None

        if issues or reward is None or cost is None or inferred_category is None:
            return None, issues, defaults

        cost_token = cost.id if cost.id.endswith("S") else f"{cost.id}S"
        offer_id = f"VIRTUAL_SHOP_{reward_amount}_{reward.id}_FOR_{cost_token}"
        display_name = candidate.display_name or (
            f"Virtual Shop {reward_amount} {reward.name} for {cost.name}s"
        )

        offer = ShopOffer(
            offer_id=offer_id,
            display_name=display_name,
            category=inferred_category,
            reward_id=reward.id,
            reward_amount=reward_amount,
            cost_id=cost.id,
            cost_amount=candidate.cost_amount,
            badge_text=badge_text,
            enabled=enabled,
        )
        return offer, issues, defaults

    @staticmethod
    def _issue(index: int, code: str, field: str, message: str) -> ValidationIssue:
        return ValidationIssue(
            offer_index=index,
            code=code,
            field=field,
            message=message,
        )

    @staticmethod
    def export_csv(result: BuildResult, output_path: str | Path) -> Path:
        if not result.is_valid:
            raise ExportBlockedError("存在未解决的配置问题，禁止生成正式 CSV")

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for offer in result.offers:
                row = offer.model_dump()
                row["enabled"] = str(row["enabled"]).lower()
                writer.writerow(row)
        return destination
