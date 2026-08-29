# Unity CSV 最小冒烟测试

## 1. 目的

用一条来自 Unity 官方 Virtual Shop 示例的商品数据，验证本项目定义的 CSV：

- 可以被放入 Unity 项目的 `Assets` 目录；
- 可以被 Unity 识别为文本资源；
- 内容在导入后没有乱码或列错位；
- 可以和自动生成的 `.meta` 文件一起进入版本控制。

这一步只验证文件格式和 Unity 资产管线兼容性，不代表 CSV 已经转换成游戏业务对象。业务级验证将在后续通过确定性的 Unity Editor 导入器完成。

## 2. 测试文件

文件：`data/examples/unity_import/virtual_shop_one_offer.csv`

数据含义：在 `Items` 分类中上架 1 把剑，售价 15 金币。

## 3. 手动导入步骤

1. 打开一个 Unity 项目。
2. 在 Project 窗口的 `Assets` 下创建目录 `GameData/Import`（若已存在则直接使用）。
3. 将 `virtual_shop_one_offer.csv` 拖入 `Assets/GameData/Import/`。
4. 等待 Unity 完成资源刷新。
5. 在 Project 窗口选中该 CSV，检查 Inspector 中的文本内容。
6. 查看文件所在目录，确认 Unity 自动生成了 `virtual_shop_one_offer.csv.meta`。
7. 关闭并重新打开 Unity 项目，确认文件仍能正常显示。

## 4. 通过标准

- Project 窗口中能看到 CSV 文件；
- Console 没有与该文件导入有关的错误；
- Inspector 中能看到 9 个列名和 1 行数据；
- 中文系统环境下没有乱码；
- Unity 自动生成对应的 `.meta` 文件；
- 重启项目后资源仍然存在并可查看。

以上全部满足，记录为“CSV → Unity TextAsset 兼容性验证通过”。

## 5. 本测试不能证明什么

本测试尚不能证明：

- 字段类型和必填规则经过 Unity 侧校验；
- `SWORD`、`COIN` 等 ID 在目标项目中真实存在；
- CSV 已转换为 ScriptableObject 或运行时配置；
- 游戏运行时能够读取并应用这条商品配置。

因此，下一次 Unity 验证应只增加一个很小的 Editor 导入器：读取该行、执行 Schema 校验，并生成一个可在 Inspector 中查看的配置对象。

## 6. SVN 注意事项

当前手动验证无需连接 SVN。未来提交到 SVN 时，应同时提交 CSV 与 Unity 自动生成的 `.meta` 文件；不要手工复制其他项目中已有的 `.meta` 文件。

参考：<https://docs.unity3d.com/Manual/class-TextAsset.html>
