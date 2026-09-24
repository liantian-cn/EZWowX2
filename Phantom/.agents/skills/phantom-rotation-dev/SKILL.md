---
name: phantom-rotation-dev
description: 编写、调整或审查 Phantom rotation TOML、条件组合、宏键位及战斗循环优先级。适用于循环配置与逻辑；新增插件转 phantom-plugin-dev，解析器、求值器或运行器改动转 phantom-code-dev。
---

# Phantom 循环开发

本 skill 负责循环配置和战斗优先级，不将配置需求自动扩大为插件或引擎开发。源码和配置路径相对 Phantom 仓库根目录。

## 编写或调整循环

1. 读取目标 TOML 与 [配置规范](references/configuration.md) 的相关章节。`rotations/死亡骑士-鲜血.toml` 是正式配置示例，不是所有职业的默认优先级；其余 38 份的历史 TXT 映射边界见 [辅助循环转换](references/assisted-rotations.md)。Shigure JSON 与技能 Lua 迁移使用 [Shigure迁移工具](../phantom-shigure-migration/SKILL.md)，先盘点源语义与授权差异。
2. 明确用户的职业专精、战斗场景、优先级及宏文本；仅对会改变策略的缺失信息追问。不凭现有示例推断其他技能、天赋或最优循环。
3. 按需查 [内置条件目录](../phantom-plugin-dev/references/built-in-conditions.md)，再核对候选 `phantom/conditions/<完整标识>/plugin.toml` 和实现，确认参数、返回类型、兜底和可用边界。光环时长按[配置精度标准](references/configuration.md#光环时长的配置精度)区分秒数与剩余百分比；秒数默认显式填写 `width=max(1,ceil(duration/2))`，用户指定宽度优先。不要给现有插件虚构参数或能力。
4. 宏仅需配置 `name` 和非空 `macro_text`；内核按声明顺序自动分配[固定宏键位池](references/key-syntax.md)，包括未引用宏。规则从上到下首条命中，每帧最多一个动作；启用、爆发、延迟均是显式条件，不自动添加隐藏门控。
5. 缺少所需条件能力时说明缺口，按任务授权范围使用 [插件开发](../phantom-plugin-dev/SKILL.md)；需要改表达式或运行引擎时使用 [代码开发](../phantom-code-dev/SKILL.md)。

只有需要核验 WoW API、技能标识或受限行为时，追加 [WoW 核验](../phantom-wow-api/SKILL.md)。循环效果不能仅凭 API 存在或配置加载成功来证明。

## 离线验证

- 在临时目录复制 TOML 后调用 `phantom.core.rotation.load_rotation()`；全部校验和内存布局成功后，该函数可能补写缺失的条件插件默认参数，不能对正式文件执行声称只读的检查。旧 `conditions[].layout` 兼容接收但忽略，不新增、更新或删除；完整回写边界见[配置规范](references/configuration.md#条件参数默认值与加载回写)。
- 用 `phantom.core.generator.render()` 在内存生成，并用已有 Lua 5.1 检查方式验证语法；不调用安装入口向游戏目录写入。
- 检查标题、引用、类型、精确插件参数、宏文本、自动键位分配及 Idle；对改动的优先级验证多个条件同时为真、全部未命中及关键兜底场景。测试方法见 [测试规则](../phantom-code-dev/references/testing.md)。
- 不启动 `RotationRuntime` 或发送实际游戏按键来完成离线检查。全部宏沿用已确认的运行期覆盖语义；该风险授权不包含实际游戏操作或其他外部动作。
