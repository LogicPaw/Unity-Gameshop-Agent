# 配置表进入 SVN 与 Unity 的准入说明

## 1. 两个不同问题

“能进入 SVN”和“能被 Unity 使用”不是一回事。

- SVN 可以版本化几乎任何文件，包括 `.xlsx`、`.csv`、`.json`、`.asset` 和图片；
- Unity 只能直接识别其支持的资源格式，或通过项目提供的导入器读取其他格式；
- 因此判断标准不是文件能否提交，而是是否存在稳定的解析、校验、差异审查和导入流程。

## 2. 格式建议

| 格式 | SVN | Unity | 建议定位 |
|---|---|---|---|
| `.xlsx` | 可以，但内容级 Diff 和合并较差 | 默认不能直接作为游戏配置，需要自定义 Editor 导入器或外部转换工具 | 策划编辑源 |
| `.csv` | 适合，文本 Diff 清楚 | 可作为 TextAsset 或由自定义导入器读取 | 简单单表交换格式 |
| `.json` | 适合，结构和 Diff 清楚 | 可作为 TextAsset 并由代码解析 | 推荐的机器交换格式 |
| Unity `.asset` / ScriptableObject | 可以，需连同 `.meta` 提交 | Unity 原生使用 | Unity 导入后的项目资产 |
| `.unity` / `.prefab` | 可以，建议 Force Text | Unity 原生使用 | 不作为本项目第一版自动生成目标 |

## 3. 本项目建议的数据链

阶段一：

```text
自然语言需求
→ 结构化领域对象
→ 经过校验的 .xlsx
```

阶段三进入 Unity 时：

```text
.xlsx（策划编辑源）
→ 确定性导出器
→ .json / .csv（机器交换格式）
→ Unity Editor 导入器
→ ScriptableObject 或项目运行时数据
→ Unity 校验
```

`.xlsx` 可以提交 SVN，但不应仅凭“已经提交”就认为 Unity 可以消费。进入阶段三之前，必须明确导入器、Schema、校验规则和输出目录。

## 4. 配置表准入清单

一张表只有满足以下条件，才可以称为“可进入 SVN–Unity 流程”：

- Schema 固定，列名、类型和必填规则明确；
- 每条记录存在稳定、唯一的 ID；
- 对资源 ID、商品 ID 等外部引用进行校验；
- 数值范围、枚举值和重复记录能够被确定性代码检查；
- 生成过程具有幂等性，相同输入不会制造重复或漂移数据；
- 存在从表格到 Unity 数据的确定性转换方式；
- Unity 侧有导入成功、引用有效和运行时可读的验证；
- 自动写入目录明确，不覆盖人工维护区域；
- 提交前可以查看变更，并由人工确认；
- 失败时不会提交半成品。

## 5. Unity 项目版本控制设置

- Unity 项目使用外部版本控制时，应保留可见的 `.meta` 文件并与对应资源一起提交；
- `Assets`、`Packages`、`ProjectSettings` 属于通常需要版本化的项目内容；
- `Library`、`Temp`、日志和构建缓存等生成目录不应作为源数据提交；
- 对 Unity 序列化资源建议使用 Force Text，便于差异审查与合并；
- Scene 和 Prefab 冲突需要使用 UnityYAMLMerge 或人工处理，本项目第一版不自动修改它们。

参考：

- Unity 外部版本控制：<https://docs.unity3d.com/Manual/ExternalVersionControlSystemSupport.html>
- Unity Editor 资源序列化设置：<https://docs.unity3d.com/Manual/class-EditorManager.html>
- Unity TextAsset：<https://docs.unity3d.com/Manual/class-TextAsset.html>

## 6. 当前阶段结论

阶段一生成 `.xlsx` 是合理的，因为它用于验证策划需求到配置表的转换能力，也可以被 SVN 保存。

当前不承诺 Unity 直接读取 `.xlsx`。阶段三将通过导出器和 Unity Editor 导入器建立正式接口，并使用 Unity 项目侧测试决定该表是否真正具备生产准入资格。
