# 时长显示与 API 证据边界

本文沉淀 2026-09-19 已查询的显示知识。**本次只批准 Phantom 现有比例条方案**；绝对显示记录用于解释源语义和未来查证，不能凭此自行启用替代实现或新插件。

## 本次采用：比例条乘固定标尺

现有 duration 条以剩余比例乘配置的 `duration` 恢复估计量。刷新续时、实际总时长变化和像素量化均可改变估计，不能宣称返回精确绝对剩余秒数。本次参数见[冻结案例](confirmed-tank-migration.md#资源与光环)。

2026-09-20 起，新编写 rotation 的秒数条遵循[配置精度标准](../../phantom-rotation-dev/references/configuration.md#光环时长的配置精度)：默认显式 `width=max(1,ceil(duration/2))`，用户可覆盖。这是 skill 的配置建议，不改变插件省略宽度时的旧公式，也不追溯改写上面的冻结案例。若策略需要剩余百分比，使用固定 width=5、返回 `ratio×100` 的对应 buff/debuff `duration_pct` 插件；不以百分比自动替换已有秒数条件。

### 公开时长线索

| 对象 | 查询资料与结论 | 限制 |
| --- | --- | --- |
| 白骨之盾 `195181` | [Wowhead PTR](https://www.wowhead.com/ptr/spell=195181)：30 秒 | 网页没有精确 DBC build，不能与本地 PTR revision 混称 |
| 正义盾击增益 `132403` | [Wowhead PTR](https://www.wowhead.com/ptr/spell=132403)：基础 4.5 秒；[Icy Veins 12.1 防护入门](https://www.icy-veins.com/wow/protection-paladin-pve-tank-easy-mode)：续时上限 13.5 秒 | `duration=13.5` 为用户选定近似标尺，不是每个实例的真实分母 |
| 奉献站地 `188370` | [Wowhead PTR](https://www.wowhead.com/ptr/spell=188370)：`Duration n/a`、`Standing in Consecration` | 不能由动作 `26573` 的地面 12 秒推出站地光环倒计时 |

### 半秒步进的准确含义

Phantom `ValueBar width=2` 有 8 个内容列，采样中间两行。标准纯黑白条且两行一致时，白色比例为 `k/8`，乘 `duration=4` 得到 `0.5k`。解码只认纯白，灰色像素排除；实际像素边缘、两行不一致及渲染误差不保证每张截图严格半秒。因此这是**名义步进**，不是实际时间精度保证。

### 永久光环

用户期望无限时长光环显示满条。当前原生 `SetTimerDuration` 的零时长／`zeroDuration` 行为没有公开 C++ 实现可用于证明，本次也没有游戏实测；公开 API 的存在和 Lua 5.1 doubles 都不能证明它一定满条。保留此待验项，不把期望写成验收结论。

## 已查询但本次不采用：源绝对显示路径

源 `Fuyutsui/core/block.lua` 使用两层独立 AuraSlot：

1. 存在层输出 255，用于存在及永久光环的显示。
2. 上方计时层使用 `maxDuration=31536000` 排除永久，固定字符 `█`，把 `RemainingDuration` 绑定到颜色曲线：`0 → 1/255`、`1 → 1/255`、`255 → 1`，中间线性。

这是颜色编码，不是 OCR；`PixelScanner` 直接读取 `color.B`。C# 状态层没有再对秒数 `floor` 或 `ceil`。显示到 8 位颜色的最近整数只能作为渲染假设，不能据此将 `<=5` 宣称为真实 `<6` 秒。0 表示无光环、最小存在编码为 1，以及 255 的永久／饱和歧义，应与[源数值语义](source-semantics.md#数值哨兵与近似)一起理解。

源两层按 `Expiration`、`Normal` 排序，先添加计时槽再添加存在槽。源注释曾假设这种顺序用于防止相互抢占，但官方核验显示独立 static AuraSlot 各自选择光环，不互相抢占同一个条目；不能把源注释的猜测当官方行为。`maxDuration` 是**总时长过滤**，不是剩余时长阈值，并可用于排除永久。相关公开声明仅支持将秘密时长交给受支持显示消费者：不能回读秘密值，也不能通过 `IsShown`、`GetText` 或回调观察绕过限制。

## 官方核验记录

此次技术证据来自官方 UI 源码镜像 **PTR 12.1.0（69587）**，revision **`a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58`**。这是本次查阅记录，不代表未来版本，也不代表游戏像素已验收。Shigure 的 revision 只用于解释源实现，见[版本索引](source-semantics.md#已核验源版本)。

### 已确认的公开接口与限制

- AuraContainer 的 static AuraSlot 与 DurationText 公开显示接口可用于上述声明式路径；`maxDuration` 按总时长筛选，独立槽不会相互抢占。公开显示接口不能扩大为 Lua 可读的秘密剩余秒数。
- `UnitCastingInfo` 第 11 个返回值 `delayTimeMs`、`UnitChannelInfo` 第 9 个返回值 `isEmpowered` 是 `NeverSecret` 哨兵；`false` 也是有效的“有返回”值，不能用真假测试误判没有引导。`notInterruptible` 可能秘密，应交受支持的 `EvaluateColorFromBoolean`；本次复用现有施法／打断插件，不另建分立条件。
- `C_Spell.IsSpellInRange` 合法返回 nil；`SpellHasRange` 不能保证对指定单位检测一定有结果。具体技能返回 nil 未实测，不列推测的不支持清单。
- 官方 `C_Item.GetItemCooldown` 返回 `startTimeSeconds`、`durationSeconds`、布尔 `enableCooldownTimer`（本迁移称 `enabled`），不能按旧数字契约比较。`C_Item.GetItemCount` 数量查询显式设置 `includeBank=false`、`includeUses=false`、`includeReagentBank=false`、`includeAccountBank=false`，统计物品数量并排除各类银行；本次物品就绪条件的业务范围见[宏检测边界](macros.md#检测范围与宏范围)。
- 上述两个物品 API 的元数据是 `SecretArguments = "AllowedWhenUntainted"`，描述秘密参数接收边界，不是秘密返回标记或泛化的调用权限。本次使用固定公开物品 ID 的普通返回路径，不新增按秘密性检测输出业务值的分支。
- `AuraUtil.lua:274` 的 `PLAYER` 过滤包含玩家、玩家宠物和载具。`Blizzard_CustomAuraContainer.lua:400–420` 中 `AddAuraSlot()` 本身请求 `UpdateAllAuras()`；初始化只添加固定槽也有首次刷新请求，不必为了补首次显示读取光环或可见性。

### 定位入口

路径相对官方镜像根目录，具体字段以冻结 revision 为准：

- `Interface/AddOns/Blizzard_AuraContainer/Blizzard_CustomAuraContainer.lua`：static AuraSlot、`AddAuraSlot` 与选项校验；`Blizzard_AuraContainerUtil.lua:111–113`：`maxDuration` 比较总时长并排除 `duration == 0`。
- `Interface/AddOns/Blizzard_APIDocumentationGenerated/AuraContainerSharedDocumentation.lua`、`AuraContainerUtilDocumentation.lua`：相关公共类型与 API 声明。
- `Interface/AddOns/Blizzard_APIDocumentationGenerated/DurationTextBindingObjectAPIDocumentation.lua`、`DurationTextBindingSharedDocumentation.lua`：DurationText 显示绑定。
- `Interface/AddOns/Blizzard_APIDocumentationGenerated/LuaDurationObjectAPIDocumentation.lua`：时长对象的受支持消费者路径。
- `Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua`：施法／引导签名和 secrecy 标记。
- `Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellDocumentation.lua`、`ItemDocumentation.lua`：范围、冷却与物品计数契约。

未来需要启用其他显示方案时，先获取用户授权，再按 [WoW API 核验方法](../../phantom-wow-api/references/source-verification.md) 核对新目标版本与真实调用路径；路径存在不等于秘密值边界和像素效果已完成验收。
