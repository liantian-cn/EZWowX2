---
name: phantom-code-dev
description: 开发、修复或审查 Phantom 核心 Python/Lua、TUI、像素协议、生成器及循环引擎。插件实现使用 phantom-plugin-dev；仅编写循环配置使用 phantom-rotation-dev。
---

# Phantom 代码开发

先按改动定位源码和相关 references，不通读整套规范。下述源码路径相对 Phantom 仓库根目录；本组 skills 共同随仓库维护。

## 选择阅读范围

| 任务 | 源码入口 | 读取 |
| --- | --- | --- |
| 产品范围与架构 | `phantom/main.py`、`phantom/core/` | [项目说明](references/project-overview.md)、[架构](references/architecture.md) 中相关章节 |
| TUI、应用配置、游戏检测 | `phantom/ui/`、`phantom/core/configuration.py`、`phantom/core/game.py` | [TUI](references/tui.md) |
| 像素定位、裁剪、编解码 | `phantom/core/pixels/`、`phantom/core/capture/`、`phantom/lua/runtime/` | [像素协议](references/pixel-protocol.md) |
| 生成器、表达式或运行器 | `phantom/core/generator.py`、`rotation.py`、`expression.py`、`runtime.py` | [架构](references/architecture.md)、[配置契约](../phantom-rotation-dev/references/configuration.md) 中相关章节 |
| 帧处理性能 | `phantom/core/runtime.py`、`phantom/core/capture/` | [性能边界](references/runtime-performance.md) |

## 实现与验证

- 写代码时读取 [开发规则](references/development-rules.md)：Python 3.13、strict 类型要求、业务注释与文件头、接口变更边界。
- 修改手写 Lua 时追加 [Lua 开发规则](references/lua-development.md)；涉及 WoW API 或访问限制时使用 [phantom-wow-api](../phantom-wow-api/SKILL.md)。只修 Python/TUI 时不加载 WoW 资料。
- 插件实现使用 [phantom-plugin-dev](../phantom-plugin-dev/SKILL.md)；核心改动涉及插件契约时直接读取其对应 references，不复制另一套契约。
- 修改配置语义或像素、插件公共接口之前，同步对应规范和已确认迁移决定。待定功能不代表实施授权。
- 按 [测试规则](references/testing.md) 选择检查；报告离线、Windows 和游戏验收的实际边界。

## 仅历史追溯时读取

[历次验收](references/history/verification-history.md)、[旧 Flexoki 配色](references/history/flexoki.md)、[早期性能记录](references/history/performance-notes.md) 不定义当前行为。维护规则时更新所属 reference，不把详细规范塞回根 AGENTS.md。
