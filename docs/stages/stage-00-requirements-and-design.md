# 阶段 00 报告：需求分析与系统设计

> 阶段状态：已完成
> 完成日期：2026-08-29
> 下一阶段：阶段 01——LangGraph + Skill 原型

## 1. 阶段目标

确定项目要证明的能力、从小到大的演进路线、第一版业务场景，以及 Vibe Coding 过程的记录方式，为后续实现建立清晰边界。

## 2. 已确认的项目定位

项目是一个面向 Unity 游戏团队的配置填表 Agent。它从自然语言或需求文档生成经过校验的 Excel，后续逐步增加 MCP、Gradio、SVN 和 Unity 集成。

项目不仅用于展示代码实现，还要证明开发者能够进行需求分析、阶段规划、架构控制、测试设计和 AI 辅助开发管理。

## 3. 已确认的演进路线

1. 阶段 01：使用 LangGraph + Skill 验证自然语言到 Excel；
2. 阶段 02：加入 MCP + Gradio，让能力可复用且可由普通员工使用；
3. 阶段 03：加入 SVN + Unity，进入游戏生产管线；
4. 并发和进一步生产化能力根据前三阶段完成情况决定。

每个阶段必须能够独立测试和演示。后续阶段复用前一阶段已经验证的核心能力，不提前一次性实现完整系统。

## 4. MVP 场景决策

最终选择“Unity 游戏虚拟商店配置表”：运营或策划用自然语言描述商品上架需求，Agent 生成虚拟商店配置 Excel。

选择原因：

- 属于真实游戏 LiveOps 流程；
- 表格字段有限，但包含 ID、分类、数值、资源引用和展示文案；
- 可以客观测试获得资源与消耗资源的方向；
- Unity 官方公开项目提供真实、可复现的数据；
- 后续可以扩展到礼包、每日奖励、Battle Pass 和限时活动。

## 5. 数据来源

阶段 01 使用 Unity Technologies 的 Unity Gaming Services Use Cases 项目中 Virtual Shop 示例：

<https://github.com/Unity-Technologies/com.unity.services.samples.use-cases/blob/main/Assets/Use%20Case%20Samples/Virtual%20Shop/README.md>

已确认可使用的数据包括：

- 6 个 Economy 资源：`COIN`、`GEM`、`PEARL`、`STAR`、`SWORD`、`SHIELD`；
- 11 条 Virtual Purchase 交易；
- 商店分类和 `Best Value` 等 Remote Config 展示信息。

## 6. 阶段 01 的初始测试范围

计划建立 7 个测试案例：

1. 单条简单商品；
2. 批量阶梯商品；
3. 货币兑换；
4. 可选展示标签；
5. 缺失关键字段；
6. 无效资源引用；
7. 非法数值。

前四个以 Unity 官方配置为依据，后三个用于验证异常处理。

## 7. 关键架构原则

- 模型先输出结构化领域对象，再由确定性代码校验和导出 Excel；
- Skill 负责领域步骤、字段语义和操作规范，不代替硬性业务校验；
- LangGraph 负责状态、节点、分支和人工确认；
- 第一阶段不开发 MCP、Gradio、SVN、Unity、并发或多 Agent；
- 当前只实现 Excel 导出，为未来其他格式保留合理边界但不提前实现。

## 8. Vibe Coding 项目记忆决策

不引入 Spec Kit、OpenSpec、额外项目记忆 Skill 或其他复杂框架。

采用以下轻量方式：

- `PROJECT_PLAN.md` 保存当前状态、范围、决策和阶段报告索引；
- 每个阶段结束生成一份 `docs/stages/*.md`；
- 后续 Agent 只有在需要溯源时才读取对应历史报告；
- 阶段报告记录事实、技术要点和测试证据，不记录逐次对话。

## 9. 尚未完成、转入阶段 01 的事项

- 将 Unity 官方资源和交易整理成本地测试资产；
- 最终确认 Excel Schema、默认值和必填规则；
- 制作 Excel 模板；
- 写出 7 个测试案例的期望结果；
- 确定字段级评价方法；
- 选择具体模型和运行环境；
- 实现最小 LangGraph 和第一版 Skill。

## 10. 阶段结论

阶段 00 已完成项目定题、范围控制、路线规划、数据源选择和 MVP 场景选择。项目可以进入阶段 01，开始整理真实数据与测试资产，并在此基础上实现 LangGraph + Skill 原型。
