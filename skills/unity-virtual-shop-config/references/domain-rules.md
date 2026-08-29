# Unity Virtual Shop Domain Rules

## Purpose

This project generates virtual-shop transaction rows. A row defines what a player receives and what the player pays. It does not define item attributes, equipment restrictions, or character classes.

## Authoritative Data

Resource truth comes from:

```text
data/raw/unity_virtual_shop/official_snapshot.json
```

Chinese lookup aliases come from:

```text
data/reference/resource_aliases.zh-CN.json
```

Aliases help resolve user vocabulary but do not add resources. An unknown name such as `水晶剑` remains unresolved unless it is later added to authoritative master data through a separate workflow.

The pinned MVP resources are:

| ID | Name | Type |
|---|---|---|
| `COIN` | Coin | Currency |
| `GEM` | Gem | Currency |
| `PEARL` | Pearl | Currency |
| `STAR` | Star | Currency |
| `SWORD` | Sword | Inventory Item |
| `SHIELD` | Shield | Inventory Item |

## Transaction Semantics

- `reward_id` and `reward_amount` describe what the player receives.
- `cost_id` and `cost_amount` describe what the player pays.
- A reward may be an Inventory Item or Currency.
- In the MVP, a cost must be Currency.
- Reward and cost amounts must be positive integers.

Example:

> 100 金币售价 7 宝石

means:

```text
reward = COIN × 100
cost = GEM × 7
```

It must not be reversed.

## Required User Decisions

The user must provide:

- reward resource name;
- cost amount;
- cost currency name.

The reward amount may be omitted and then defaults to `1`. The deterministic tools, not the model, apply defaults and record them.

Other allowed defaults are:

| Field | Default |
|---|---|
| `badge_text` | empty string |
| `enabled` | `true` |
| `category` | `Items` for Inventory Item rewards; `Currencies` for Currency rewards |

Price and cost currency never receive defaults.

## System-Owned Fields

The deterministic Python core owns:

- resource-name to resource-ID lookup;
- category inference;
- default application;
- `offer_id` generation;
- fallback `display_name` generation;
- validation;
- formal CSV serialization.

The current ID convention is:

```text
VIRTUAL_SHOP_{reward_amount}_{reward_id}_FOR_{plural_cost_id}
```

For example:

```text
VIRTUAL_SHOP_1_SWORD_FOR_COINS
VIRTUAL_SHOP_100_COIN_FOR_GEMS
```

Price is intentionally excluded from the ID so a price update does not change the offer identity.

## Candidate Extraction Examples

### Complete offer with an omitted quantity

Input:

> 剑，15 金币一把。

Candidate:

```json
{
  "item_name": "剑",
  "reward_amount": 1,
  "currency_name": "金币",
  "cost_amount": 15,
  "display_name": null,
  "category": null,
  "badge_text": null,
  "enabled": null
}
```

The phrase `一把` explicitly states quantity `1`. If the input were only `剑，15 金币`, `reward_amount` should be `null`; the tools would later apply the default.

### Currency reward

Input:

> 100 金币售价 7 宝石。

Candidate:

```json
{
  "item_name": "金币",
  "reward_amount": 100,
  "currency_name": "宝石",
  "cost_amount": 7,
  "display_name": null,
  "category": null,
  "badge_text": null,
  "enabled": null
}
```

### Batch input

Input:

> 一把剑售价 15 金币；三个盾牌售价 20 金币并标记 Best Value。

Return two candidates in the same order. The second candidate has `reward_amount = 3` and `badge_text = "Best Value"`.

### Missing currency

Input:

> 一把剑售价 15。

Set `currency_name` to `null`. Do not assume Coin.

### Unknown resource

Input:

> 水晶剑售价 200 宝石。

Extract `item_name = "水晶剑"`; do not translate it into a fabricated ID. The resource tool will return `UNKNOWN_REWARD`, and the workflow should request clarification.

## Formal CSV Contract

The exporter writes exactly these columns in this order:

```text
offer_id,display_name,category,reward_id,reward_amount,cost_id,cost_amount,badge_text,enabled
```

Formal export is allowed only when the complete batch has no unresolved validation issues.
