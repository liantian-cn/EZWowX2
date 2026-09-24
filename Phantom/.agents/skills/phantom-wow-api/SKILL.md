---
name: phantom-wow-api
description: 为 Phantom 核验 WoW API、事件、Secret Values、Aura、渲染和受保护调用，查证目标版本源码及限制。仅在任务涉及这些技术事实时使用；纯 Python、TUI 或普通 TOML 编辑不默认加载。
---

# Phantom WoW 技术核验

先读取 [源码核验方法](references/source-verification.md)，确认本次目标 build 和实际源码 revision。以下英文专题是技术背景与证据，不覆盖项目契约。

| 当前问题 | 读取 |
| --- | --- |
| 版本变化、接口改名或不确定的可用性 | [WoW 12.1 changes](references/wow-12.1-changes.md) |
| 战斗数据或潜在秘密值的操作与显示 | [Secret Values](references/secret-values.md) |
| 光环筛选、AuraContainer、AuraSlot | [Aura](references/aura.md)，同时读取 Secret Values |
| Frame、纹理、StatusBar、Cell、IconTile | [Rendering](references/rendering.md) |
| 事件选择与游戏端刷新 | [Events](references/events-performance.md) |
| 战斗锁定、安全按钮、绑定或受保护操作 | [Security](references/security-api.md) |

## 形成可用结论

- 用精确标识搜索目标源码，核对签名、参数、返回、nil、secrecy 与访问限制，再查 Blizzard 的真实调用方式。
- 将 producer 到受支持显示 consumer 的路径和限制写清楚，不把秘密值转为普通 Lua 判断，不通过可见性、数量、布局或时序旁路读取。
- 记录日期、版本、revision 和具体文件；无法核实则明确标注，不能用旧实现或历史快照代替当前证据。源码缺失时遵循核验参考中的有界替代路径，不修改或更新外部仓库。
- 本任务要求实现时，把已核验结论用于对应 [代码](../phantom-code-dev/SKILL.md) 或 [插件](../phantom-plugin-dev/SKILL.md) 任务；仅请求核验时交付事实与限制，不擅自修改业务。

仅追溯过往证据时读取 [source snapshots](references/history/source-snapshots.md)。历史路径可能在当前机器不存在；文档迁移不意味着重新核验游戏。
