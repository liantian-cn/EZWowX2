---
name: phantom-plugin-dev
description: 创建、修改或审查 Phantom 条件、截图、键盘插件及其模板、版本契约和 plugin.toml。适用于 phantom/conditions、captures、keyboards；不用于安装 Codex 插件或仅编写循环 TOML。
---

# Phantom 插件开发

先读取 [公共规则](references/common.md)，确认精确插件版本及现有参数、返回值和生命周期，再只读取本次插件类型：

| 类型 | 仓库源码入口 | 读取 |
| --- | --- | --- |
| 条件 | `phantom/conditions/<完整标识>/condition.py` 与可选 `template.lua` | [条件契约与开发](references/conditions.md) |
| 截图 | `phantom/captures/<完整标识>/capture.py` | [截图契约与开发](references/captures.md) |
| 键盘 | `phantom/keyboards/<完整标识>/keyboard.py` | [键盘契约与开发](references/keyboards.md) |

## 完成一个插件改动

1. 按公共规则使用不含作者前缀的 `包名@版本号` 目录，核对该版本 `plugin.toml` 的 `name`、`author`、`version` 和实现。选择或理解内置条件时按需查 [内置条件目录](references/built-in-conditions.md)，不为每次插件改动加载全部目录。
2. 读取共享 [开发规则](../phantom-code-dev/references/development-rules.md)；有 Lua 修改才追加 [Lua 格式](../phantom-code-dev/references/lua-development.md)，涉及像素才追加 [像素协议](../phantom-code-dev/references/pixel-protocol.md)。不必加载整个代码 skill。
3. 涉及 WoW 调用、事件、秘密值或受保护对象时使用 [phantom-wow-api](../phantom-wow-api/SKILL.md)，按专题核验后实现。
4. 业务参数、算法与兜底留在本版本，复用核心公开设施；同步作者自述及受影响的配置、规范。
5. 按本类型参考及共享 [测试规则](../phantom-code-dev/references/testing.md) 验证正常、边界、不可用和失败路径，类型检查覆盖精确版本入口。

正式数字版本的接口和逻辑不得原地修改；测试版本允许修改但仍需同步配套内容。历史迁移仅在 [版本记录](references/history/version-migrations.md) 查阅，不能当成未来修改正式版本的授权。
