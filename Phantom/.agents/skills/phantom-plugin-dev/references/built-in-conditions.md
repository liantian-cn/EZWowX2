# 内置条件目录

用于筛选已有条件和查阅当前业务契约；确定具体参数、输出和限制时，再读取 `phantom/conditions/<完整标识>/plugin.toml` 与该版本实现。修改现有条件时同步维护对应条目。

## 基础条件

| 插件（统一为 名称@dev） | 参数 | 输出与解码 | 兜底 |
| --- | --- | --- | --- |
| player_primary_power | 有限正数 max_power | Cell ratio × max_power，float | 0.0 |
| spec_power_rune | 无 | Cell mean 四舍五入，0–6 int | 0 |
| spell_charges | spell_ids、正整数 max_charges，可选正整数 width | ValueBar 缺省宽=ceil(max_charges/2)，显式宽优先；ratio×量程四舍五入 | 0 |
| spell_overlay | spell_ids | Cell 严格黑白 bool | False |
| spell_usable | spell_ids | Cell 严格黑白 bool | False |
| player_health_pct | use_predicted（bool，默认 true） | Cell percent，生命百分比 float | 0.0 |
| target_health_pct / focus_health_pct | use_predicted（bool，默认 true） | Cell percent，生命百分比 float，无单位为零 | 0.0 |
| target_in_range / focus_in_range | 正整数 spell_id | 指定技能射程内，严格黑白 bool | False |
| spell_in_range | 正整数 spell_id、unit_token（target/focus/mouseover） | 指定技能对指定单位的射程结果，严格黑白 bool | False |
| spell_cooldown | spell_ids、布尔 ignore_gcd | Cell 分段剩余秒数 float | 375.0 |
| spell_gcd | 无 | Cell 分段剩余秒数 float | 375.0 |
| item_cooldown_ready | 正整数 item_id | 指定物品非银行库存大于零、有效冷却启用且无剩余时间，严格黑白 bool | False |

spell_ids 是非空正整数列表，普通法术取首个法术书匹配候选。
spell_gcd 固定 GetSpellCooldownDuration(61304,false)，不查询法术书，不接受技能或 ignore_gcd 参数。
无参插件可省略 plugin_args 或传空表，其他参数一律拒绝。前缀 player_/target_/focus_/spell_/spec_ 仅为建议。
冷却亮度 255/155/105/55/0 对应 0/5/30/155/375 秒，区间内线性反算；黑色同时表示饱和或无 duration。
灰度 Cell 必须纯灰，布尔必须纯黑/白；整数采用非负数四舍五入而非银行家舍入。
能量与血量直接把曲线返回颜色交给渲染，充能直接传秘密 currentCharges；符文仅统计非秘密 runeReady，不读取秘密事件参数。
事件与节流沿用对应模板；GCD 与普通冷却均独立随机错峰、严格超过 0.1 秒轮询。
生命条件使用单位生命、最大生命事件；预测模式追加预测治疗和吸收变化事件，目标/焦点切换同样刷新。
射程条件均以 0.1 秒随机错峰轮询；无效技能、无单位和普通 nil 为 False，潜在秘密 bool 直接转颜色；不代表实际距离。
`plugin.toml` 顶层 `assisted_combat_rule_types` 仅作关联检索，不代表与官方规则等价，不参与运行时加载。

## 通用状态读取插件

现有 Lua 状态、聊天命令、面板与第一行五个 Cell 保留。以下三个无参数条件插件没有 Lua、不分配新区域，仅在配置声明时实例化；条件标题完全由配置决定，不形成隐式执行门控。

| 插件 | 读取坐标 | 类型 | 非黑白值或解码异常兜底 |
| --- | --- | --- | --- |
| `enable@dev` | Cell(3, 1) | bool | True |
| `in_burst@dev` | Cell(4, 1) | bool | False |
| `delaying@dev` | Cell(5, 1) | bool | False |

兜底后继续求值；enable 与 delay 的上述兜底允许配置规则继续执行动作，这是已确认的业务语义。

## 玩家条件插件（2026-09-15）

以下 23 个插件统一使用 `<名称>@dev`。每个实例输出一个 scalar：除施法图标使用第四行一个 IconTile 外，其余均占第二行一个 Cell 区域。
AuraContainer 和吸收 StatusBar 是该区域的显示实现，不另分配 ValueBar，不改变核心像素协议。

| 名称 | 必填参数 | Python 返回与业务含义 |
| --- | --- | --- |
| player_role | 无 | str：TANK、HEALER、DAMAGER、NONE |
| player_in_combat | 无 | bool：玩家处于战斗 |
| player_is_player_target | 无 | bool：玩家当前目标是自己 |
| player_is_moving | 无 | bool：玩家正在移动 |
| player_in_vehicle | 无 | bool：玩家处于载具或坐骑状态 |
| player_melee_enemies_count | spell_id；可选 combat_only=false | int：nameplate1–40 中存在、可攻击、非死亡、符合战斗筛选且在技能范围内的数量 |
| player_is_targeting_spell | 无 | bool：正在选择法术目标 |
| player_is_chatting | 无 | bool：任意键盘输入焦点存在，包含非聊天输入框 |
| player_in_group | 无 | bool：在队伍或团队中 |
| player_trinket_ready | slot_id | bool：13 或 14 位置的饰品冷却结束且可用 |
| player_healthstone_ready | 无 | bool：固定物品 224464 冷却结束且可用 |
| player_heal_potion_ready | 无 | bool：固定物品 258138 冷却结束且可用 |
| player_cast_progress | 无 | float：施法或通道已进行的百分比，0–100，空闲为 0.0 |
| player_is_empowering | 无 | bool：玩家正在蓄力通道 |
| player_cast_icon | 无 | str：IconTile 内部图像 hash；空槽为空字符串 |
| player_cast_target | 无 | str：player、party1–4、raid1–40；未知为空字符串 |
| player_has_big_defensive | 无 | bool：存在 HELPFUL\|BIG_DEFENSIVE 光环 |
| player_has_dispellable_debuff | dispel_types | bool：存在玩家可驱散且类型匹配的减益 |
| spell_known | spell_ids | bool：任一技能已知或在玩家法术书中 |
| talent_known | spell_ids | bool：与 spell_known 完全相同，按技能 ID 判断 |
| player_damage_absorb | threshold | bool：伤害吸收量严格超过阈值 |
| player_heal_absorb | threshold | bool：治疗吸收量严格超过阈值 |
| player_has_buff | buff_ids；可选 player_only=true | bool：任一指定增益存在，默认 HELPFUL\|PLAYER |

参数约束：`spell_id` 为正整数；`spell_ids`、`buff_ids` 为非空正整数列表；`slot_id` 只接受 13/14。
`threshold` 为 0–9007199254740990 的整数，保证 Lua 数值中的 N 和 N+1 可精确区分；拒绝布尔值、小数和负数。
`dispel_types` 为必填 bool 映射，键限定 Magic、Poison、Disease、Curse、Stealth、Special、Enrage；未列出为 false，空表和全 false 均不匹配。成功加载 rotation 时仅补写已有映射内缺失的七种类型子键为 false；整体缺失仍报错，显式值不覆盖，详见[配置默认值](conditions.md#配置默认值)。
所有插件拒绝多余字段，参数名称统一使用 snake_case。
`player_has_buff@dev` 增加可选 `player_only`，默认 true：使用 `HELPFUL|PLAYER`；false 使用 `HELPFUL`。PLAYER 包含玩家、玩家宠物和载具。

布尔值必须严格全黑/全白，异常兜底 False。职责灰度字节 0/85/170/255 分别表示 NONE/TANK/HEALER/DAMAGER，其他值或秘密职责返回 NONE。
近战计数灰度为 count/40，Python 用非负数四舍五入恢复；秘密或 nil 的距离结果不计数。进度通过黑白颜色曲线求值后直接渲染，Python 读取 Cell.percent。
无效技能的近战计数为零；只报告可观察姓名板，不能代表全部附近敌人。目标周围指定距离计数仍是能力缺口，未实现。
计数和进度的异常兜底分别为 0、0.0。施法目标编码 0=未知、1=player、2–5=party、6–45=raid，乘 5 后作为灰度字节；非法编码兜底空字符串。
图标直接读取 IconTile.hash，把底层空槽 None 转成空字符串，解码异常同样为空字符串。

本节的玩家 Lua 插件独立注册 PLAYER_ENTERING_WORLD；统一刷新写法见 [条件插件](conditions.md#刷新写法)。支持单位过滤的旧事件只注册 player。
AuraContainer 在世界事件调用公开的 UpdateAllAuras，平时由官方容器管理更新，不自行轮询或检查 AuraData/可见性。

光环沿用固定 AuraSlot 白色覆盖黑底；指定增益由 includeSpellIDs 筛选，大防御使用 BigDefensive/Normal 排序。
驱散过滤为 `HARMFUL|RAID_PLAYER_DISPELLABLE` 加 includeDispelTypes，同时要求当前玩家可驱散与类型匹配。
吸收量直接传入白色 StatusBar，最小 N、最大 N+1，Lua 不比较秘密吸收量。

施法目标完整保留旧项目按名称匹配、秘密目标暂留旧值、成功/停止/失败清空和每秒兜底清空行为，因此长施法也可能提前变为空字符串。
三种物品就绪条件使用 enabled、零冷却、usable 且 not noMana，不增加背包数量检查。
`item_cooldown_ready@dev` 是独立的通用单物品条件：`C_Item.GetItemCount(item_id, false, false, false, false) > 0`，且 `GetItemCooldown` 的 start/duration 为非负有限数、enabled 为 bool true、无剩余冷却才为 True。不查 usable、不计各类银行或物品使用次数。仅使用静态公开 ID 的已核验普通返回路径，API 异常或普通数据无效均表示未确认就绪；两个 API 的 `SecretArguments = "AllowedWhenUntainted"` 是参数秘密性元数据，当前定义未标记秘密返回，不增加秘密性检测或输出映射。事件下一帧刷新，另有一秒随机错峰兜底。
技能/天赋只判断 IsSpellKnown 或 IsSpellInSpellBook，不解析天赋树；后者可包含覆盖技能，不保证技能此刻可施放。

## 官方辅助条件关联迁移（2026-09-18）

以下新增插件均为 `@dev`，参数以对应 `plugin.toml` 和实现为准。关联标签仅用于搜索相似能力，不构成官方规则的完整复现。

| 插件 | 参数 | 输出与限制 |
| --- | --- | --- |
| target_is_enemy / focus_is_enemy | 无 | `UnitIsEnemy` 布尔值；无单位为 False |
| target_can_assist / focus_can_assist | 无 | 默认参数的 `UnitCanAssist` 布尔值；无单位为 False |
| player_has_pet | 无 | pet 存在且存活才为 True，不统计没有 pet token 的临时召唤物 |
| target_has_buff / focus_has_buff | aura_ids | 单槽匹配指定 Buff，仅用于可辅助侧 |
| target_has_debuff / focus_has_debuff | aura_ids | 单槽匹配指定 Debuff，仅用于不可辅助侧 |
| player_range_aura_units_count | spell_id、aura_id；combat_only=false | 可观察 nameplate1–40 中存活、可攻击、在技能范围内且有指定 Debuff 的数量 |
| aura_player_buff_duration | aura_ids、有限正数 duration；可选正整数 width、player_only=true | 缺省宽=min(8,max(1,ceil(duration/4)))，显式宽优先；返回 ratio × duration 的 float 估计 |
| aura_target_debuff_duration | aura_ids、正整数 duration，可选正整数 width | 缺省宽=min(8,ceil(duration/4))，显式宽优先；返回 ratio × duration 的 float 估计 |
| aura_player_buff_stacks / aura_target_debuff_stacks | aura_ids、max_value；min_value=0、width=2 | ValueBar 返回 ratio × max_value 的 float 估计；当前 min_value 仅允许 0 |

Aura 身份分类与普通可辅助条件的语义不同：过滤使用 `UnitCanAssist("player", unit, true, true)`，可辅助侧允许指定 Buff，不可辅助侧允许指定 Debuff。多个 ID 使用官方单槽首个匹配，不承诺列表优先级。日常更新由官方 AuraContainer 管理。

`target_has_debuff@dev`、`focus_has_debuff@dev`、`aura_target_debuff_duration@dev`、`aura_target_debuff_duration_pct@dev`、`aura_target_debuff_stacks@dev` 固定使用 `PLAYER|HARMFUL`；官方 PLAYER 包含玩家、玩家宠物和载具。没有 `player_only` 参数；重新生成后排除其他来源的同技能减益。驱散条件不使用 PLAYER 过滤。

玩家增益存在、层数、秒数时长和剩余百分比插件均接受 `player_only`，默认 true 使用 `HELPFUL|PLAYER`，显式 false 使用 `HELPFUL`。这是已确认的默认语义变化，不批量为其他循环补参数；加载时仍遵循通用默认值补写契约。

时长条直接使用官方 `SetDurationBar` 的立即插值与剩余时间方向，不特殊处理永久或无限 DurationObject，也不保证其满条。玩家增益 duration 允许有限正小数，拒绝 bool、NaN、Inf；目标减益 duration 仍只允许正整数。配置 duration 必须与实际时长匹配才能准确换算；名义像素步长为 `duration/(4×width)`，不保证延长或时长变体的绝对秒数精度。时长与充能的派生宽度不补写，显式宽度可超过默认公式的上限；宽度改变不改变数值量程。

本次玩家时长配置量程为白骨之盾 duration=30/width=8、正义盾击 duration=13.5/width=4、奉献 duration=4/width=2。奉献条的8个内容像素对应0..4秒，每增加一列纯白像素换算0.5秒；这是解码量程验证，不代表游戏中实际光环时长或永久光环渲染已验收。

新编写秒数条件应按[rotation 配置精度标准](../../phantom-rotation-dev/references/configuration.md#光环时长的配置精度)显式选择宽度；该 skill 建议不同于本节插件代码的缺省公式，不修改以上已经确认的个案参数。

层数条使用官方 `SetApplicationBar`，实际量程为 0..max_value，名义层数步长为 `max_value / (4 * width)`。保留 min_value 参数但仅允许 0；Warcraft Wiki 将 `minApplications` 标记为 12.1.5 新增，当前实现不使用它。零填充无法区分无光环与应用层数为零的光环。

范围 Debuff 计数只接受 NeverSecret 的 aura_id；游戏初始化发现不满足条件会直接报错并中止后续初始化，不能把此状态当作正常零计数。combat_only 表示单位自身处于战斗，不保证正与玩家交战。技能射程与姓名板子集不代表几何半径内的完整单位集合。

### 光环剩余百分比（2026-09-20）

| 插件 | 参数 | 固定输出 |
| --- | --- | --- |
| `aura_player_buff_duration_pct@dev` | 必填 `aura_ids`；可选 `player_only=true` | 单个 ValueBar，内容 width=5；float 剩余百分比 |
| `aura_target_debuff_duration_pct@dev` | 仅必填 `aura_ids` | 同上，固定目标 `PLAYER\|HARMFUL` |

`aura_ids` 为非空正整数列表；两者均拒绝 `duration` 和 `width`，目标版也拒绝 `player_only`。输出为 `ratio×100`，范围 `0.0..100.0`；正常计时从 100 降至 0，不是已过百分比。玩家版来源默认 `HELPFUL|PLAYER`，显式 false 为 `HELPFUL`；目标版沿用存在且不可辅助的容器门控，不额外要求敌对或可攻击。无光环、目标门控无效或插件解码异常为 `0.0`；分配区域越界仍遵循核心错误边界，不伪装成合法 0。

固定五单位对应 20 个内容像素，两侧红色分隔合计 4 像素，完整占位 24×4／6 个 Cell。两采样行一致的纯黑白整列图像对应 `0,5,…,100`，名义步长 5 个百分点；部分灰色像素从分母排除或两行不一致时，原样返回现有比例算法结果，不额外量化。Lua 继续使用官方 `SetDurationBar`、`Immediate`、`RemainingTime`，永久光环行为由官方显示绑定负责，不新增特殊分支。

### 固定资源

| 插件 | 参数 | 输出 |
| --- | --- | --- |
| spec_power_mana / spec_power_rage / spec_power_focus / spec_power_energy | max_power | 固定资源类型的亮度比例 × 配置最大值，float |
| spec_power_runic_power / spec_power_lunar_power / spec_power_maelstrom | max_power | 同上 |
| spec_power_insanity / spec_power_fury / spec_power_pain | max_power | 同上 |
| spec_power_combo_points / spec_power_holy_power | 无 | 直接灰度字节解码，int |
| spec_power_soul_shards | fractional=false；小数模式可选正整数 width，缺省25 | 默认 Cell 整碎片 int；fractional=true 用 ValueBar 显示原始0–50片段，Python恢复十分位碎片 float，兜底0.0 |
| spec_power_chi / spec_power_essence / spec_power_arcane_charges | 无 | 直接灰度字节解码，int |

主要资源最大值由配置提供，不从秘密值计算；灰度量化步长约为 max_power/255。直接 Cell 编码的次要资源在执行数值运算前检查秘密值，再检查编码范围，异常直接报错，不静默转为零。灵魂碎片的小数模式是显示路径例外：将原始片段直接传给 StatusBar，不在 Lua 中检查或计算秘密资源；Python按最近整数片段恢复十分位。width仅小数模式可用且不自动补写，fractional=false仍沿用旧Cell。以上资源使用固定 Enum.PowerType，不随当前主要资源类型自动切换。

迁移删除旧标识 `player_has_spell@dev`、`player_has_talent@dev`、`spec_dk_rune@dev`；外部配置须自行改为 spell_known、talent_known、spec_power_rune 并重新生成。历史版本记录不改写。

目标周围指定距离计数仍未支持。本地参数、像素、生成和 Lua 替身测试不能代替实际客户端的秘密值、受管 Aura 显示与生命周期验收。

## 目标／焦点与黑名单（2026-09-18）

以下 target/focus 成对提供独立 `@dev` 条件，固定单位；无单位时一律使用各自兜底。

| 名称（两种前缀） | 参数 | 输出与兜底 |
| --- | --- | --- |
| target_is_exists / focus_is_exists | 无 | UnitExists，bool；False |
| target_is_alive / focus_is_alive | 无 | 存在且非死亡／灵魂，bool；False |
| target_can_attack / focus_can_attack | 无 | UnitCanAttack(player, unit)，不等同敌对或不可辅助；False |
| target_in_combat / focus_in_combat | 无 | 单位处于战斗，不保证与玩家交战；False |
| target_cast_progress / focus_cast_progress | 无 | 已完成百分比 0–100 float，空闲／失败 0.0 |
| target_cast_interruptible / focus_cast_interruptible | 无 | 当前有施法或引导且可中断，普通 nil 保守 False；不表示玩家一定能打断 |
| target_cast_icon / focus_cast_icon | 无 | 一个 IconTile 内部 6×6 hash，空槽／解码异常空字符串；单位消失或无施法时清空，角标不表示许可 |
| target_has_dispellable_buff / focus_has_dispellable_buff | 必填 dispel_types 布尔映射 | 存在、UnitIsEnemy 且匹配指定类型的 HELPFUL\|RAID_PLAYER_DISPELLABLE，bool；False |

驱散七键为 Magic、Poison、Disease、Curse、Stealth、Special、Enrage。空表／全 false 不匹配；官方过滤表示团队有人能驱散，并非玩家本人当前能驱散。映射键原样传给 `candidateFilters.includeDispelTypes`；Enrage 对应实际 `dispelName` 的本地证据不足，标为游戏待验，不猜测转换为空字符串或其他键。

施法通过 NeverSecret 的 delayTimeMs／isEmpowered ~= nil 哨兵识别状态，普通引导的 false 有效。Duration 的 EvaluateElapsedPercent 直接渲染进度；纹理直接 SetTexture；可中断经 EvaluateColorFromBoolean 显示。事件延后一帧，进度 0.1 秒持续轮询，基础布尔和可中断 1 秒兜底，图标事件刷新，Aura 由官方容器管理。

`interrupt_blacklist_icons@dev` 无参数，固定十个 IconTile，输出 `list[str]`：过滤空槽、保留顺序和重复 hash，全空／异常为 `[]`。**每份循环只允许声明一次**，固定共享 `interrupt_blacklist` 配置，不支持独立多份黑名单。加载期登记一个 panel 编辑入口，按档案保存并通过 Config 回调刷新；默认只由 panel 应用一次，初始化主动渲染。

黑名单默认 ID 为 468962、1248327、1254669、1258436、1262510、1262526，不覆盖已有列表。可保存超过十项；按 ID 数值升序选前十个固定槽，纹理失败留空并清角标、不补位、不删配置、不循环请求，不使用 panel 的问号纹理。初始化／配置／档案变化请求数据；成功且仍在配置中的加载事件仅刷新，不再次请求。有效图标使用黄色 `COLOR.SPELL_TYPE.INTERRUPTIBLE` 角标，纯类别，不表示打断许可或当前施法状态；本插件不匹配施法、不执行动作。

可复制的最小配置片段见 [目标／焦点示例](target-focus-example.md)。核验基线为本地 12.1.0.69587、revision `a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58`；UnitTokenPvPRestrictedForAddOns、实际客户端和 Enrage 显示均需另行游戏验收。

目标／焦点施法图标沿用玩家的 `IconTile:SetIcon` 显示路径，直接传递秘密纹理，不消费 `Texture:SetTexture` 返回值。2026-09-19 纠正此前“未标记秘密即可判断返回值”的结论：上述 build 允许秘密参数并声明 bool 返回，不保证返回值可用于普通 Lua 分支。单位消失或无施法时清空图标和角标；已撤销设置失败必定同时隐藏角标的保证，空槽／解码异常仍返回空字符串。异步资源加载及实际客户端秘密值行为仍待游戏验收。黑名单使用普通技能纹理的既有返回值检查不在此次修复范围；不通过纹理身份、可见性或加载时序旁路读取秘密值。
