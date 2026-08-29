---
name: unity-virtual-shop-config
description: Convert natural-language Unity virtual-shop requirements into candidate offer data, resolve them against project resource master data, and generate validated shop CSV files. Use for creating or checking virtual-shop offers; do not use for defining item stats, equipment restrictions, or new game resources.
---

# Unity Virtual Shop Config

Convert shop requirements into configuration without allowing inferred or invalid data to bypass the deterministic project tools.

Before extracting or validating an offer, read [references/domain-rules.md](references/domain-rules.md). It contains the authoritative field semantics, allowed defaults, resource constraints, and examples for this project.

## Workflow

1. Identify every requested offer and preserve its input order.
2. Extract each offer into the project `CandidateOffer` fields. Do not generate `offer_id`, `reward_id`, `cost_id`, category, or a fallback price in the model response.
3. Leave genuinely missing information as `null`. Do not hide missing price or currency information behind a guess.
4. Pass candidates to the deterministic `ResourceCatalog` and `OfferConfigTools` in `src/game_config_agent/`. They own resource lookup, defaults, technical ID generation, validation, and CSV export.
5. If the tools return issues, do not create a formal CSV. Convert each issue into a concise, offer-specific clarification question or correction request.
6. If validation passes, export the fixed nine-column CSV and report the generated offers plus every applied default.

## Extraction Contract

Extract only these `CandidateOffer` fields:

- `item_name`: the reward resource as the user named it;
- `reward_amount`: the quantity the player receives, or `null` when omitted;
- `currency_name`: the resource used to pay;
- `cost_amount`: the required payment amount, or `null` when omitted;
- `display_name`: only when the user explicitly provides one;
- `category`: only when the user explicitly provides one;
- `badge_text`: only when the user explicitly provides a badge or label;
- `enabled`: only when the user explicitly specifies the state.

For batch input, return one candidate per offer. Keep reward and cost direction exact: the player receives the reward and pays the cost.

## Boundaries

- Never invent a resource ID or silently create a new resource.
- Never let the model write the formal CSV directly.
- Never export a partial batch while unresolved issues remain.
- Do not treat item stats, character-class restrictions, or equipment rules as shop-offer fields.
- Do not connect SVN, modify a Unity project, or commit files unless a separate task explicitly requests it.
