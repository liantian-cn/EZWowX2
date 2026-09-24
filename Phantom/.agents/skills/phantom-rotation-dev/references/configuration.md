# Rotation 配置规范

## 应用配置与 rotation 配置的边界

启动工作目录下的 `phantom.toml` 是应用配置文件，保存截图/键盘插件选择、FPS、界面参数及各职业专精的 rotation 文件路径；它与 rotation TOML 是两种独立配置，其字段、默认值和错误规则见 [tui.md](../../phantom-code-dev/references/tui.md)。本文件只规定旋转（rotation）配置的 schema 与语义。

## 文件边界

一份 TOML 文件（`.toml`）表示一份 rotation。schema v1 的顶层字段固定为：

- `schema_version`
- `uuid`
- `profile`
- `conditions`
- `macros`
- `rotation`

字段名统一使用 `snake_case`。草案中的 `unitTalnet`、`bing_key` 等拼写不是兼容契约，不得作为别名保留。列表必须使用真正的 TOML 数组，不得用逗号拼接伪装列表。配置对象不使用数字 `id`。

`profile` 使用表；`conditions`、`macros` 和 `rotation` 使用表数组。每个 `[conditions.plugin_args]` 归属于最近声明的 `[[conditions]]` 条目。

## 完整示例

此处 `health_pct@dev` 是说明 `unit_token` 参数的假设插件，不是内置插件；正式配置示例见 `rotations/死亡骑士-鲜血.toml`。38 份历史 TXT 配置的来源和近似边界见 [辅助循环转换](assisted-rotations.md)，鲜血与防护的新 JSON 策略见 [Shigure 迁移记录](../../phantom-shigure-migration/references/confirmed-tank-migration.md)，两者不能相互套用授权。

```toml
schema_version = 1
uuid = "550e8400-e29b-41d4-a716-446655440000"

[profile]
title = "神圣骑士基础循环"
description = "优先治疗玩家，否则对有效目标使用审判。"
unit_class = "PALADIN"
unit_spec = 1

[[conditions]]
title = "玩家血量"
plugin = "health_pct@dev"
[conditions.plugin_args]
unit_token = "player"

[[conditions]]
title = "圣光术冷却时间"
plugin = "spell_cooldown@dev"
[conditions.plugin_args]
spell_ids = [82326, 82325]
ignore_gcd = true

[[conditions]]
title = "目标血量"
plugin = "health_pct@dev"
[conditions.plugin_args]
unit_token = "target"

[[conditions]]
title = "审判冷却时间"
plugin = "spell_cooldown@dev"
[conditions.plugin_args]
spell_ids = [12345]
ignore_gcd = true

[[macros]]
name = "对玩家释放圣光术"
macro_text = "/cast [@player] 圣光术"

[[macros]]
name = "审判"
macro_text = "/cast 审判"

[[rotation]]
condition = "玩家血量 < 70 and 圣光术冷却时间 == 0"
macro = "对玩家释放圣光术"

[[rotation]]
condition = "目标血量 > 0 and 审判冷却时间 == 0"
macro = "审判"
```

## 标识和引用

- `schema_version` 当前必须为整数 `1`。未来结构升级通过显式迁移完成，不得猜测字段形状。
- `uuid` 必须是带连字符的标准 RFC 4122 UUID 文本，标识 rotation 并参与宏按钮命名；生成文件使用每次重新分配的随机 UUID4，不因生成修改配置 uuid。每个专精目录内每个条件实例独立一份 Lua，另有一个宏绑定 Lua，详见[生成器落地](../../phantom-code-dev/references/architecture.md#生成器落地)。
- `profile.unit_class` 使用 Blizzard 的大写职业 token。
- `profile.unit_spec` 使用 `GetSpecialization()` 的顺序索引；DRUID 允许 1–4，其余 12 个职业允许 1–3，总计固定 40 个组合，DEMONHUNTER 的 3 为 devourer。
- schema v1 不包含 `unit_talents`。
- 每个 `conditions[].title` 在文件内唯一；表达式直接引用该标题。
- 每个 `macros[].name` 在文件内唯一；循环项的 `macro` 直接引用该名称。
- `plugin_args` 的具体字段由精确版本插件定义，但字段名仍使用 `snake_case`。

条件标题必须符合 Python 标识符兼容规则：以中文字符或英文字母开头，后续只含中文字符、英文字母、数字或下划线；不得包含空白、运算符、括号或引号，也不得使用 Python 保留词，包括 `and`、`or` 和 `not`。标题可以是中文或英文，只要引用完全一致。

## 条件参数默认值与加载回写

所有 `load_rotation()` 入口使用相同规则，包括启动加载、单份生成包装和直接调用；TUI 集合生成复用启动已加载对象，不重读文件。只有整份配置的结构、插件参数、宏文本、宏数量与自动键位分配、表达式与引用等全部验证通过，且内存布局分配与冻结成功后，才向 rotation 文件补写缺失的条件插件默认参数。应用配置 `phantom.toml` 不参与此默认参数回写，其选择回写及 UUID 冲突修复另见 TUI 多份管理规范。

- 默认值唯一来源是精确版本 Python `Condition` 子类公开的 `config_defaults: ClassVar[Mapping[str, object]]`，基类默认为空映射；插件构造与配置回写共享此来源，具体契约见 [条件插件规范](../../phantom-plugin-dev/references/conditions.md#配置默认值)。不读取 `plugin.toml`，也不从模板参数推测默认值。
- 由其他参数或输出模式派生的布局宽度不属于静态默认补写范围，具体公式见上述条件插件规范。省略 `width` 时每次构造重新推导；显式填写时优先使用配置值，之后改变数值量程不会自动覆盖已有宽度。
- 只补缺失键，不覆盖任何显式值，包括 `false`、`0`、空字符串、空列表等；显式非法值仍报错，不能用默认值修复或绕过验证。已有嵌套字典按层递归补充缺失子键，保留已有值。
- 必填约束不因声明子键默认值而放宽。例如 `dispel_types` 整体仍必填，仅在已有字典内将缺失的 `Magic`、`Poison`、`Disease`、`Curse`、`Stealth`、`Special`、`Enrage` 补为 `false`；已有空表会补齐这七个子键，仍表示不匹配任何类型。
- 仅在确有默认参数需要补写时创建缺失的 `plugin_args`；无默认参数时不创建空表。没有实际补写内容时不写文件。
- 回写保留注释及其他配置内容，通过同目录临时文件原子替换；替换前检查源文件与本次读取内容是否一致，发现并发修改则加载失败，不覆盖新内容。写入或替换失败同样使本次加载失败。
- 配置验证或布局失败时不回写。加载成功并已补写后，后续 Lua 渲染或插件生成失败不回滚已保存的默认参数。

## 光环时长的配置精度

2026-09-20 确认的 **rotation 编写标准**：光环时长使用 ValueBar 剩余比例，按需求选秒数估计或剩余百分比。此标准指导新编写或经授权调整的条件参数，不修改现有插件的代码缺省公式，不批量更新既有 rotation，也不覆盖用户指定的宽度。

### 秒数：显式选择宽度

现有 `aura_player_buff_duration@dev`、`aura_target_debuff_duration@dev` 返回 `ratio × duration`。编写配置时默认使用：

```text
width = max(1, ceil(duration / 2))
名义秒数步长 = duration / (4 × width)
```

`width` 是正整数内容宽度单位，每单位 4 像素。2 秒量程、width=1 时，每个内容像素对应 0.5 秒；除不尽时向上取整，名义步长不超过 0.5 秒。该编写标准**没有 8 单位上限**，用户可以按需求自行缩短或加长。

| duration | 默认写入的 width |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 4 | 2 |
| 13.5 | 7 |
| 30 | 15 |

小数时长仍须符合所选精确插件的参数契约；当前只有玩家增益秒数插件接受有限正小数，目标减益秒数插件仍要求正整数。这份 skill 的推荐宽度不是 `config_defaults`：若配置省略 `width`，插件仍使用原有 `ceil(duration/4)` 并限制缺省宽度最多为 8 的实现。为落实本标准，应显式填写宽度，而不是依赖省略参数。

### 百分比：固定五单位

`aura_player_buff_duration_pct@dev` 与 `aura_target_debuff_duration_pct@dev` 输出**剩余**比例乘 100 的 float，范围 `0.0..100.0`，正常计时从 100 降至 0。两者固定内容宽度为 5，即 20 个内容像素，连同两侧分隔占 24 像素／6 个 Cell；不接受 `duration` 或 `width` 参数。标准纯黑白整列下的名义步长是 **5 个百分点**。所需来源过滤和兜底见[插件目录](../../phantom-plugin-dev/references/built-in-conditions.md#光环剩余百分比2026-09-20)。

按秒数和按百分比比较是不同策略，不能自动把既有秒数阈值换成百分比。ValueBar 仅按有效黑白像素计算比例，灰色像素会被排除；两采样行不一致时也可能产生非整列比例。上述步长描述标准输入的量化分辨率，不额外四舍五入或强制将百分比归为 5 的倍数。增加秒数条长度改善像素量化分辨率，不改变固定 `duration` 的量程含义。

## 条件表达式

加载配置时，执行器必须只解析和验证一次表达式 AST；运行期复用已验证结构，并读取 `conditions[title].value()`。不得使用 `eval`。

schema v1 支持：

- 字面量：整数、浮点数、`True`、`False`、带引号字符串和简单列表。
- 比较：`<`、`<=`、`>`、`>=`、`==`、`!=`。
- 布尔：`not`、`and`、`or`。
- 成员：`in`、`not in`。
- 用于改变结合顺序的括号。

优先级沿用 Python：比较与成员判断，然后 `not`，然后 `and`，最后 `or`。禁止属性访问、下标、函数调用、算术运算和其他 AST 节点。

列表字面量不得嵌套，元素必须为同一类型。成员判断的右侧也可以是另一个条件返回的列表；验证阶段必须确认右侧声明为列表、左侧声明为标量，且元素类型与左侧类型一致。字符串和数字之间不做隐式转换。

## 宏与键位

宏配置与自动分配遵循以下规则，`schema_version` 保持 `1`：

- 每个宏仅需 `name` 和非空 `macro_text`；`macro_text` 必须为非空字符串，不能省略。
- 配置不再需要 `key` 和 `bind_key`。旧字段允许残留，其值完全忽略，不校验类型或内容、不警告、不自动清除；条件默认参数回写也必须保留这些字段。旧 `bind_key = false` 不再跳过宏文本校验或生成绑定。
- 全部声明的宏（包括未被规则引用的宏）按声明顺序分配键位；每份 rotation 独立从[固定键位池](key-syntax.md#固定宏键位池)开头分配，不共享分配游标。最多允许 148 个宏，超过则拒绝加载；空宏列表继续允许。
- 自动键位只保存在内部宏数据中，不写回配置。内核保留键位字符串和解析后的 `KeyCombination`，分别供 Lua 绑定、展示和键盘发送使用；键盘后端不解释宏。
- 全部声明的宏均生成不可见 `SecureActionButtonTemplate`，设置 `type = "macro"` 与 `macrotext`，再通过 `SetOverrideBindingClick` 建立优先覆盖绑定。
- 上述绑定不创建 WoW 已保存宏槽位，也不改写玩家的持久键位设置；会直接覆盖分配键位在当前运行期的已有动作，不检查也不提示。用户已接受该运行期覆盖风险，授权不包含实际游戏操作或其他外部动作。

每个宏的生成代码必须保持以下调用语义；`macro.key` 是内部自动分配的键位，变量命名可以由生成器调整：

```lua
-- 示意已校验宏；实际生成器使用 rotation UUID 与宏序号确保名称唯一。
local buttonName = addonName .. "Button" .. rotationUUID .. macroIndex
local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
frame:SetAttribute("type", "macro")
frame:SetAttribute("macrotext", macro.macro_text)
frame:RegisterForClicks("AnyDown", "AnyUp")
SetOverrideBindingClick(frame, true, macro.key, buttonName)
```

## 执行顺序

表达式变量仅来自显式声明的 `conditions[].title`。`插件启用`、`爆发开启`、`正在延迟` 不再是内置变量或保留条件名；需要时声明对应的[状态读取插件](../../phantom-plugin-dev/references/built-in-conditions.md#通用状态读取插件)，标题可按现有命名规则自由设置。同一插件可用不同标题多次声明，未声明则不加载 Python 实例。

schema_version 仍为 1；旧配置中未声明的这三个名称按未知变量拒绝，加载失败不回写，不自动补齐条件。38 份历史 TXT 配置按其已授权策略显式声明 enable，长冷却动作另要求 burst、不添加 delay 门控；这不是所有正式配置的统一策略。新 JSON 迁移按各自冻结决定处理状态。引擎专用 fixture 独立保留 enable/delay 的测试场景。

这些条件不形成隐式门控。配置可以逐条显式加入启用条件，也可采用首条 `not 插件启用` → `Idle`；鲜血与防护采用后者并显式保留末尾 Idle。测试 fixture 也可通过首条 `not 插件启用 or 正在延迟` → `Idle` 验证跳过本轮。状态解码失败使用插件声明的兜底并继续求值。Idle 既可作为条件命中结果，也可作为末尾兜底；Sleep/Pass 仅为未来计划的 Idle 别名，本次不接入，也不增加等待语义。

`rotation` 从上到下求值，第一个为真的条目胜出。每轮最多发送一个键；全部为假时本轮不执行动作。

## 待定事项

- schema v1 之外的升级与迁移格式。
- 未来是否增加天赋路由字段。


## 单份生成阶段扩展（schema v1）

- profile.unit_class_id 可省略，按职业 token 推导；显式值必须一致。annotate 是 rotation 条目的可选字符串说明。
- Idle 是保留动作名，不得声明同名宏，不需要键位。空 condition 仅允许在末尾显式 Idle；省略时在内存追加隐含 Idle，不写回该条目。
- 条件布局仅在内存中分配和冻结，不作为配置回写内容。旧 `conditions[].layout` 字段兼容接收但忽略，不参与校验或布局决策；`load_rotation()` 不新增、更新或删除该字段。旧字段的清理由人工显式维护完成。
- 每次加载重新分配，分类后按条件原始顺序排列，ValueBar 包含分隔；输出区域及坐标语义不变。无新增区域的插件保持 `output_type="none"` 和空 regions，不移动其他条件的坐标。成功加载后的文件写入仅按上文规则补写缺失的条件插件默认参数。
- 本阶段校验所有结构、基本类型、UUID、职业专精、名称/引用与插件参数，加载时一次性完成表达式白名单、引用与类型校验，运行时复用 AST。
- 条件实例、宏和规则保持配置顺序；重复规则允许，条件标题与宏名称必须唯一。
- 自动分配的键位在加载时按键盘公共解析器解析并冻结为 KeyCombination；配置中残留的 key/bind_key 不参与解析或校验。固定池与内部语法见[宏键位语法](key-syntax.md)。
- 示例为 rotations/死亡骑士-鲜血.toml；每次生成所有声明的条件，包括尚未被规则引用的条件。

## 第 11–13 步求值边界

- 表达式最终结果、`not` 和 `and/or` 操作数必须为布尔，不使用数字或列表的隐式真假值。
- 数值比较允许 int 与 float；bool 不作为数值。字符串只与字符串比较。
- 列表字面量仅含同类型标量常量；空列表可用于成员判断。成员判断不混用 int/float。
- 支持链式比较及短路；列表仅允许同类型相等／不等判断，不支持排序比较。
- 负号属于未开放的一元算术节点；非有限浮点字面量被拒绝。
- 首条命中为 Idle 时本轮无宏；显式或内存追加的末尾 Idle 承接全部未命中。
- 第 11–13 步历史上仅报告；第 14–17 步已通过独立运行器接入发送，单帧求值函数本身仍无发送副作用。
