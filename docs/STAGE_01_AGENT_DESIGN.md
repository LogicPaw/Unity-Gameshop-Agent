# 阶段 01：文字生成商店 CSV 的最小 Agent 设计

## 1. 设计目的

第一版 Agent 接收一段包含一条或多条商品信息的自然语言，生成已经过确定性校验、可由现有 Unity CSV 解析器读取的 CSV。

本设计只回答四个问题：

1. 最终生成什么数据；
2. 每个字段从哪里获得；
3. LangGraph 在一次任务中保存什么状态；
4. 每个节点负责什么，以及何时进入澄清分支。

## 2. MVP 输入与输出

示例输入：

> 把这些东西建立成表：1. 剑，15 金币一把；2. 盾牌，20 金币 3 个并标记 Best Value；3. 100 金币售价 7 宝石。

预期输出：

```csv
offer_id,display_name,category,reward_id,reward_amount,cost_id,cost_amount,badge_text,enabled
VIRTUAL_SHOP_1_SWORD_FOR_COINS,Virtual Shop 1 Sword for Coins,Items,SWORD,1,COIN,15,,true
VIRTUAL_SHOP_3_SHIELD_FOR_COINS,Virtual Shop 3 Shield for Coins,Items,SHIELD,3,COIN,20,Best Value,true
VIRTUAL_SHOP_100_COIN_FOR_GEMS,Virtual Shop 100 Coin for Gems,Currencies,COIN,100,GEM,7,,true
```

## 3. ShopOffer 数据契约

| 字段 | 类型 | 约束 |
|---|---|---|
| `offer_id` | string | 必填、唯一、符合大写下划线格式 |
| `display_name` | string | 必填；用户未提供时由确定性规则生成 |
| `category` | string | 必填，只允许 `Items` 或 `Currencies` |
| `reward_id` | string | 必填，必须存在于资源主数据 |
| `reward_amount` | integer | 必填，必须大于 0 |
| `cost_id` | string | 必填，必须是允许使用的货币 ID |
| `cost_amount` | integer | 必填，必须大于 0 |
| `badge_text` | string | 可选，缺失时为空字符串 |
| `enabled` | boolean | 必填，缺失时默认为 `true` |

CSV 的列名和顺序以本表为准，与已通过 Unity 验证的 `virtual_shop_one_offer.csv` 保持一致。

## 4. 字段来源与缺失处理

| 字段 | 来源 | 缺失或异常时如何处理 |
|---|---|---|
| `offer_id` | 确定性代码生成 | 发生重复时停止导出并报告冲突 |
| `display_name` | 用户输入或确定性代码生成 | 缺失时根据标准资源名称生成稳定名称 |
| `category` | 系统根据奖励资源类型推断 | Inventory Item → `Items`；Currency → `Currencies` |
| `reward_id` | 使用商品名称查询资源主数据 | 找不到或匹配多个资源时询问用户 |
| `reward_amount` | AI 从数量表达中提取 | 未提供时默认 `1`；非正整数时报错 |
| `cost_id` | 使用货币名称查询资源主数据 | 未提供或无法识别时询问用户 |
| `cost_amount` | AI 从价格表达中提取 | 未提供时询问用户；非正整数时报错 |
| `badge_text` | AI 从可选标签中提取 | 未提供时使用空字符串 |
| `enabled` | 用户输入或系统默认值 | 未提供时默认 `true` |

默认值必须在结果报告中可见。系统不得把默认值伪装成用户明确提供的内容。

## 5. MVP 测试资源主数据

当前以固定版本的 `data/raw/unity_virtual_shop/official_snapshot.json` 为唯一资源真相：

| 标准名称 | 资源 ID | 类型 |
|---|---|---|
| Coin | `COIN` | Currency |
| Gem | `GEM` | Currency |
| Pearl | `PEARL` | Currency |
| Star | `STAR` | Currency |
| Sword | `SWORD` | Inventory Item |
| Shield | `SHIELD` | Inventory Item |

中文“金币、宝石、剑、盾牌”等保存在独立别名表中，只用于输入查询，不能创造官方快照中不存在的资源。“水晶剑”等未知资源必须产生结构化错误并进入后续澄清分支。

未来可以把主数据来源替换为公司物品表、数据库、Unity 项目数据或 MCP 资源查询，Agent 的核心流程不应因此改变。

## 6. Offer ID 生成规则

MVP 使用与 Unity 官方样例一致的确定性格式：

```text
VIRTUAL_SHOP_{reward_amount}_{reward_id}_FOR_{cost_id_plural}
```

例如：

```text
VIRTUAL_SHOP_1_SWORD_FOR_COINS
```

价格不进入 ID，避免调价时产生新的商品身份。MVP 不允许相同 `reward_id + reward_amount + cost_id` 同时出现多个售卖项；出现时进入冲突分支，不自动追加随机后缀。

## 7. Graph State

一次 LangGraph 任务只需要保存：

| 状态字段 | 用途 |
|---|---|
| `raw_requirement` | 用户原始输入，便于追溯 |
| `candidate_offers` | AI 提取但尚未完全校验的候选商品 |
| `resolved_offers` | 已完成资源映射和默认值处理的商品 |
| `validation_errors` | 确定性校验错误 |
| `clarification_questions` | 需要用户补充或确认的问题 |
| `defaults_applied` | 本次使用了哪些默认值 |
| `csv_path` | 校验通过后的最终文件路径 |

状态不保存无关聊天历史，也不把 CSV 文本作为唯一业务数据来源。

## 8. LangGraph 节点边界

### `extract_offers`

- 调用模型理解自然语言；
- 提取商品名称、数量、价格、货币、标签等候选字段；
- 不生成正式 ID；
- 不判断资源是否真实存在；
- 不写 CSV。

### `resolve_fields`

- 查询资源主数据；
- 将“金币”“宝石”等名称映射为标准 ID；
- 应用允许的默认值；
- 使用确定性规则生成 `offer_id`；
- 记录使用过的默认值和无法解析的字段。

### `validate_offers`

- 检查必填字段、字段类型和正整数；
- 检查资源引用；
- 检查 `offer_id` 格式与唯一性；
- 只返回结构化错误，不直接修改用户数据。

### `request_clarification`

- 将缺失信息、未知资源和冲突转换为明确问题；
- 不生成正式 CSV；
- 用户补充后重新进入提取和校验流程。

### `export_csv`

- 只接收已经通过校验的 `ShopOffer`；
- 严格按照固定列名和顺序导出；
- 不调用模型；
- 返回输出路径和简要生成报告。

## 9. 条件路由

```text
extract_offers
      ↓
resolve_fields
      ↓
validate_offers
      ↓
是否存在错误或待确认字段？
      ├─ 是 → request_clarification → 等待用户补充
      └─ 否 → export_csv → 完成
```

LangGraph 的核心价值是保存任务状态并控制条件分支，确保未经校验的数据不能进入正式 CSV。

## 10. 第一版测试重点

至少覆盖以下路径：

1. 三条完整商品一次生成，验证批量正常路径；
2. 未写商品数量，验证默认数量 `1`；
3. 缺少货币类型，进入澄清分支；
4. 未知商品名称，进入资源确认分支；
5. 价格为负数，确定性校验失败；
6. 两条商品生成相同 `offer_id`，阻止导出；
7. 正常生成的 CSV 能继续被现有 Unity 解析器读取。

## 11. 当前明确不做

- 不接入 SVN；
- 不开发 Gradio 或 MCP；
- 不生成 ScriptableObject；
- 不支持任意游戏配置表；
- 不引入多 Agent 或并发；
- 不让模型直接写 CSV；
- 不自动创建未经确认的资源 ID。

## 12. 实现状态与下一步

已经完成：

1. `CandidateOffer`、`ShopOffer`、错误和默认值记录模型；
2. 基于官方快照的 `ResourceCatalog`；
3. 中文名称别名查询；
4. 默认值、ID 生成和确定性校验；
5. 固定 Schema 的 CSV 导出器；
6. 人可直接运行的命令行入口；
7. 主数据、正常路径和异常路径的自动化测试。
8. 项目内 `unity-virtual-shop-config` Skill 及领域规则引用。
9. OpenCode Go 模型接入与最小 LangGraph 条件分支；
10. 正常输入进入 CSV 导出、异常输入进入澄清分支的真实接口验证。

接下来：

1. 用 Unity 对三条工具生成数据做一次回归验证；
2. 使用 Unity 对 LangGraph 生成的三条商品 CSV 做回归验证；
3. 增加可恢复的人工澄清 checkpoint；
4. 补齐 Golden Cases 和字段级评价。
