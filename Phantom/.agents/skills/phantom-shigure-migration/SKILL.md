---
name: phantom-shigure-migration
description: Shigure迁移工具：将用户提供的 Shigure JSON 规则与技能 Lua 迁移为 Phantom rotation，审计源顺序、条件语义、单位和宏；用于迁移及迁移结果复核，不扩展为职业循环优化。
---

# Shigure迁移工具

默认输入为**用户 JSON、对应技能 Lua、本 skill 已沉淀经验及 Phantom 现有规范**，不依赖外部 Shigure 仓库，也不编写通用转换器。用户指令与本次冻结决定优先；历史个案参数不自动成为下一次迁移的默认值。

遇到经验未覆盖的字段、版本或行为，先报告具体缺口并停止相关迁移，另获授权后才查外部源码。2026-09-19 的外部查阅是单次授权，不延续到未来任务。外部实现仅解释源语义，不作为官方 WoW API 证据；新获授权查阅得到的可复用结论须回写本 skill 的对应 reference。

本工具默认排除**插入法术类**规则，并在顺序对照中记明排除原因；保留同一技能在普通优先级中的其他规则。源距离条件默认使用**该步骤动作技能的射程检测**，避免使用 LibRangeCheck；特殊探针须单独确认，不给没有距离条件的动作额外加门控。玩家与敌方生命检测推荐统一使用 `use_predicted=true`。这些迁移政策与下面记录的源原始行为分开，不把两者写成完全等价。

## 迁移流程

1. **盘点输入。** 记录 JSON 版本、职业专精、英雄天赋适用范围、技能 Lua 标识；按原序号列出全部 `Rules` 的 `Enabled`、动作、`Unit`、主条件、`SubConditions`、引用及未识别字段。关联技能和光环的完整 ID 组，标明缺失定义。读 [源语义](references/source-semantics.md)；每条规则都有去向，所有未知项已列出，才完成盘点。
2. **冻结语义与顺序。** 将主条件与子条件组组合为 `主条件 and (子条件1 or 子条件2 …)`，保留表达式内 `&&` 高于 `||` 的结合关系；无子条件时只用主条件。按源序号建立保留、排除、合并及目标序号对照，逐项解释单位、量程、暂停和门控差异。疑似错误单列，不顺手修复；优先级审计必须覆盖多条件同时为真及前置无条件规则的遮蔽。全部改变均有用户决定后才落地；本次两坦克的冻结策略见 [迁移案例](references/confirmed-tank-migration.md)。
3. **核对插件契约。** 使用 [循环 skill](../phantom-rotation-dev/SKILL.md) 和 [内置条件目录](../phantom-plugin-dev/references/built-in-conditions.md)，逐一检查精确 `包名@版本` 的 `plugin.toml`、Python 及 Lua 实现，记录参数、返回类型、兜底、来源过滤和数值范围。新编写的光环秒数条件按[配置精度标准](../phantom-rotation-dev/references/configuration.md#光环时长的配置精度)显式选宽，用户指定值优先；剩余百分比条件选用固定五单位的 `duration_pct` 插件，不擅自改变源阈值单位。先复用已有插件；能力缺口先报告并获批准，再进入 [插件 skill](../phantom-plugin-dev/SKILL.md)。不把“参数近似”写成全域等价，不用新插件绕过尚未确认的语义。
4. **整理宏与规则。** 按 [宏参考](references/macros.md) 核对中文动作、物品多行宏、显式单位及检测 ID 与动作的差异；未写 `Unit` 时不擅加单位。保留已有配置 UUID，标题及作者信息遵循任务要求；条件和宏引用全部可解析、顺序对照全部闭合后，才完成 TOML。
5. **离线验证。** 先只读解析正式 TOML，再在测试副本调用 `load_rotation()`，允许且核对精确版本默认值的正常补写；内存 `render()` 并使用 `lupa.lua51` 检查每个 Lua chunk。按 [测试规则](../phantom-code-dev/references/testing.md) 验证条件边界、AND/OR、首命中、Idle、宏和多 ID 组，以及源序号到目标规则的完整对应。根据改动完成 pytest、类型与 ruff 检查，正式配置不得作为可能回写的验证输入。
6. **交付审计。** 报告输入版本、规则数变化、所有授权差异、疑似源错误、未验证项和检查结果。未知语义未解决时不能声称迁移完成。离线验证不启动运行器、不发送游戏按键、不安装插件；游戏内像素、秘密值路径和循环效果须单独验收。

## 按需参考

| 当前问题 | 读取 |
| --- | --- |
| Rules、单位、别名、量化值、控制开关、源版本差异 | [源语义与版本索引](references/source-semantics.md) |
| 物品、圣言祭礼、`[@unit]`、裸 `item:` 行 | [宏映射](references/macros.md) |
| 鲜血／防护的最终政策、顺序例外、参数与验收数量 | [2026-09-19 两坦克迁移](references/confirmed-tank-migration.md) |
| 比例时长、半秒量化、永久光环、已查但未采用的绝对显示路径 | [时长与 API 证据边界](references/duration-and-api-evidence.md) |

技术事实需要新核验时使用 [WoW API skill](../phantom-wow-api/SKILL.md)。本 skill 只完成相关迁移；新增职业策略、英雄天赋路由和其他优化须另立任务。
