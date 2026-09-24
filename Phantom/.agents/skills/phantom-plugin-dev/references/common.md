# 插件公共规则

按本次类型继续读取 [条件](conditions.md)、[截图](captures.md) 或 [键盘](keyboards.md)，不同时加载无关类型。

## 职责与依赖

- 版本目录放插件实现、配套模板与供 Agent 阅读的 `plugin.toml`。公共条件设施位于 `phantom/core/condition/`，截图设施位于 `phantom/core/capture/`，键盘设施位于 `phantom/core/keyboard/`。
- 插件依赖核心的公开契约；核心不依赖具体技能、职业或专精规则，不按某个插件名称写分支。
- 不导入另一个插件版本目录。基础输入检查通过组合复用；业务字段、算法参数、业务范围和兜底留在本插件版本。
- 不在 UI 中加载具体后端文件或引用其具体实现类；使用核心注册器。
- 通用参数校验使用 `phantom.core.validation.Validator[T]`。条件插件在 `decode_value()` 中直接读取 `phantom.core.pixels` 的 `Cell`、`ValueBar`、`IconTile` 属性并完成必要校验和业务转换，不额外建立解码器包装层；`Condition` 基类负责生命周期与异常兜底边界。

## 版本与变更

以下是 Agent 开发规则，不由运行时代码或 CI 强制校验：

- 插件标识和文件夹名使用 `包名@版本号`，包名沿用英文 `snake_case`，不包含作者前缀。作者写入 `plugin.toml` 的 `author` 字段，本仓库使用 `liantian-cn`；`version` 字段为字符串，与目录的版本后缀一致。
- 数字或点分数字版本（如 `1`、`1.0`、`1.2.3`）是正式版本，接口参数和逻辑不得原地修改；需要修改时创建另一版本。
- 其余非数字版本是测试版本，例如 `dev`、`beta`、`1.0-beta`，允许修改接口参数和逻辑；仍需同步受影响配置、说明并验证业务行为。
- 内置条件、截图和键盘插件统一使用 `<名称>@dev`，不保留旧标识别名。同一类型内的包名与版本组合必须唯一，作者字段不参与目录定位。


已发布版本的历史迁移决定不构成未来修改其语义的通用授权。

## 插件标识与解析

当前标识例如：

- 条件：`player_health_pct@dev`
- 键盘：`post_message@dev`
- 截图：`gdi@dev`

解析器以完整标识查找精确目录，不校验包名或版本格式，不自动改名、降级、升级或回退到相近版本。多个版本可以并存，共享配置继续引用作者已测试的版本。
标识必须是单个安全目录名，禁止绝对路径、目录穿越和 Windows 路径别名；目录及源码、模板不得逃逸各自根目录。文件定位沿用宿主文件系统语义。

## 插件目录

| 类型 | 精确版本目录入口 | 配套文件 |
| --- | --- | --- |
| 条件 | `phantom/conditions/<完整标识>/condition.py` | 可选 `template.lua`、作者自述 `plugin.toml` |
| 截图 | `phantom/captures/<完整标识>/capture.py` | 作者自述 `plugin.toml` |
| 键盘 | `phantom/keyboards/<完整标识>/keyboard.py` | 作者自述 `plugin.toml` |

各入口导出 `Plugin`。条件的参数、解码和兜底在 Python 中，游戏端显示在可选模板中；模板缺失与模板损坏必须区分。

## AI Agent 自述

每个插件提供 `plugin.toml`，新增或修改插件时由 Agent 同步维护 `name`、`author` 和 `version` 及业务说明。这是开发约定：Python 运行代码不读取它，缺失或内容错误不作为插件加载失败条件，也不增加强制 CI 校验。

自述使用英文 TOML 字段与中文业务说明，推荐结构如下：

| 字段 | 内容 |
| --- | --- |
| `name` | 完整插件标识，与目录名一致 |
| `author` | 作者名称，使用原始名称；本仓库为 `liantian-cn`，无需转换为 Python 标识符 |
| `version` | 字符串版本号，与目录名的 `@` 后缀一致，如 `"dev"`、`"1.0"` |
| `display_name` | 简明中文插件名 |
| `description` | 中等详细用途：主要 API 名称、输入到输出转换、适用边界；无需 API 调用教程 |
| `recommended_condition_name` | 建议的条件标题；如 `{技能名称}的冷却时间`，占位符需替换，实际标题遵守 rotation 命名规则；截图填写“不适用” |
| `assisted_combat_rule_types` | 可选顶层字符串列表，记录完整 `ASSISTED_COMBAT_RULE_TYPE_*` 关联供检索；无关联时省略，运行时不读取，也不强制 schema。关联不承诺与官方规则等价，focus 可关联对应 target 规则 |
| `[parameters]` | 无参数时用 `description` 明确说明；有参数时使用下级表逐项描述 |
| `[parameters.<参数名>]` | `type`、`required`、`description`，仅有默认值时填写 `default`；说明含义与约束，不罗列内部临时变量 |
| `[returns]` | `type`、`description`，按业务需要填写 `unit`、`fallback`、输出形状与状态字段说明 |

内容必须与实际插件一致，不凭 API 名称推断更强的业务保证。WoW API 核验来源可用注释记录日期、版本、revision 和对应定义文件。完整源码说明要求仍见各插件专题。

## 文档、类型与验证

- 标识符使用英文，业务说明使用中文。解释业务步骤、边界和原因，不以注释数量为目标。
- 项目通用文件头、Type Hint、Lua 分区、API 文档与事实核验规则统一见 [开发规则](../../phantom-code-dev/references/development-rules.md)；插件专属说明见各专题。
- 注释必须与本实例和参数化行为一致，不能保留示例的固定坐标、固定宽度，或复制其他插件的兜底含义。
- 新增与修改插件时验证正常输入、边界、不可用输入及失败路径。条件须验证 Lua/Python 配对，截图须验证图像与生命周期，键盘须验证发送顺序和失败释放；检查方法见 [测试规则](../../phantom-code-dev/references/testing.md)。
- 完整类型检查使用 `.venv/Scripts/python scripts/check_types.py`，包括每个精确版本入口；新增插件不得依靠目录特殊字符避开检查。
- 离线测试、Windows 截图和游戏内验收分别记录，不把 API doubles 的结果写成游戏验证结论。

## 历史版本

仅追溯迁移时读取 [版本迁移记录](history/version-migrations.md)。
