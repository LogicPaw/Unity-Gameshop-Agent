# Unity Virtual Shop 数据来源

## 来源

- 仓库：<https://github.com/Unity-Technologies/com.unity.services.samples.use-cases>
- 固定提交：[`575661c6f83e721e9f20d27f6c66e7249a929889`](https://github.com/Unity-Technologies/com.unity.services.samples.use-cases/commit/575661c6f83e721e9f20d27f6c66e7249a929889)
- 提交时间：2026-04-08T20:09:44Z
- 获取时间：2026-08-29
- Virtual Shop 说明：<https://github.com/Unity-Technologies/com.unity.services.samples.use-cases/blob/575661c6f83e721e9f20d27f6c66e7249a929889/Assets/Use%20Case%20Samples/Virtual%20Shop/README.md>

## 使用的官方机器配置

- Economy Currency：`Assets/Common/Config as Code/*.ecc`
- Economy Inventory：`Assets/Common/Config as Code/*.eci`
- Virtual Purchase：`Assets/Use Case Samples/Virtual Shop/Config as Code/*.ecv`
- Remote Config：`Assets/Use Case Samples/Virtual Shop/Config as Code/virtual_shop_config.rc`

`official_snapshot.json` 将这些文件中阶段一需要的字段合并为一个固定快照。它是测试数据，不是对 Unity 原始文件格式的替代。

## 数据核对发现

固定提交中的机器配置 `VIRTUAL_SHOP_2_SWORD_FOR_COINS.ecv` 表示 2 把剑消耗 20 金币，而同一提交的 README 表格写为 25 金币。

阶段一以机器配置文件为事实来源，因此快照采用 20。这个差异将保留为数据质量案例，证明测试数据需要从可执行配置中核验，不能只复制说明文档。
