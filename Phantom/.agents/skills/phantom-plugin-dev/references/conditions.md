# 条件插件开发

## Python 实现流程

每个版本的 `condition.py` 导出 `Condition` 子类 `Plugin`，构造参数为 `args: dict[str, object]`。
依次验证参数、保存业务参数、声明 `Output`；布局、模板路径和异常兜底调用由核心负责。

| 内容 | 使用方式 |
| --- | --- |
| 生命周期 | `phantom.core.condition.base.Condition` |
| 输出与类型 | `phantom.core.condition.contracts.Output`、`Value`、`Region` |
| 参数字段 | `Fields(required, optional).validate(args, "plugin_args")`，字段集合用 `frozenset` |
| 基础输入 | `PositiveInteger`、`PositiveNumber`、`Boolean`、`String`、`Table`、`Items` |
| 像素读取 | `Cell.mean`、`Cell.ratio`、`Cell.percent`、`Cell.is_white`、`ValueBar.ratio`、`IconTile.hash` 等区域属性 |

`Validator.validate` 返回强类型合法值，失败抛出包含字段上下文的 `ValueError`。
例如 `SpellIDs` 在本插件内组合 `Items(PositiveInteger(), nonempty=True)`，保留技能候选顺序。业务解码直接写在 `decode_value()` 中，失败交由 Condition 的既有异常边界调用插件兜底。
当前灰度条件先检查 `Cell.is_pure` 及内部像素的 RGB 分量相等，再读取亮度或比例；布尔条件先检查严格全黑或全白，再读取 `Cell.is_white`。冷却条件直接使用本版本固定节点进行分段插值，业务范围、舍入与兜底保留在插件内。

`decode_value(cells, value_bars, icon_tiles, *, decoder: PixelDecoder)` 的同帧参数及异常边界见 [基类契约](#基类契约)。插件可用 `decoder.getCell(x, y)`、`decoder.getValueBar(x, width)`、`decoder.getIconTile(x)` 读取额外区域，坐标与宽度沿用像素协议。
每个插件解释其 `fallback_value()` 的业务含义；框架分配区域越界和插件解码异常的不同处理见 [核心边界](#核心边界)。

## 配置默认值

`Condition` 公开类属性 `config_defaults: ClassVar[Mapping[str, object]]`，基类默认空映射。精确版本插件通过该属性声明可补写到 rotation 的参数默认值，构造时的缺省值与加载回写必须共享此来源，不维护两套默认常量。它与解码失败时的 `fallback_value()` 是不同契约。

- 默认值使用 TOML 可表示的 Python 原生值，嵌套表使用 `dict`；不得放入布局、Lua 字符串片段或运行期对象，也不得在实例构造或回写时修改共享默认声明。
- 声明只描述默认值，不替代字段、类型、范围及必填检查；已有显式值一律保留，非法值仍拒绝。不得用真假值判断代替缺失键判断，`false`、`0` 和合法空值都不是缺失。
- 支持在已有嵌套字典中递归补充缺失子键；不得以默认字典替换已有显式值或修复非法类型。`dispel_types` 整体仍必填，只有其已有字典内的七种类型子键默认 `false`，缺少整个字段仍报错。
- 不声明默认值的插件沿用空映射，缺失的 `plugin_args` 不因此生成空表。默认值来自 Python 公开契约，不读取作者自述 `plugin.toml`，不反推 `template_parameters()` 或 Lua 模板。
- 参数或输出模式派生的布局值是明确例外：时长、充能及小数碎片的缺省 `width` 由精确插件在构造时计算，不放入静态 `config_defaults`，也不自动补写。显式 `width` 始终优先且必须通过正整数校验；不得修改共享默认映射或在核心中按插件名分支。时长缺省为 `min(8, max(1, ceil(duration / 4)))`，充能缺省为 `max(1, ceil(max_charges / 2))`，小数碎片缺省为 25。公式中的上限不是显式宽度上限。
- 所有 `load_rotation()` 入口在整份配置验证及布局冻结成功后统一补写；无变更不写、源文件并发检查、原子替换与失败语义见 [配置规范](../../phantom-rotation-dev/references/configuration.md#条件参数默认值与加载回写)。条件插件构造本身不负责写配置文件。

## 无 Lua 与零区域插件

`template.lua` 可省略，生成器仍为每个声明实例输出独立的随机 UUID4 Lua，包含标识、职业专精守卫与统一 namespace。每个实例独立 chunk 加载，无外围 `do/end`，不去重、不跳过未引用实例；存在模板时原样追加渲染内容并检查路径与占位符错误，不将损坏模板当成缺失模板。模板内部结构不改。
不新增像素区域时使用 `Output("none", output_count=0, value_type=...)`，不声明 widths；框架冻结空 regions，向解码方法传三个空列表。仍必须声明业务值类型、形状和兜底。
模板与区域分配相互独立：零区域插件可以提供 Lua；有分配区域的插件也可以省略模板，但插件作者须确保该区域有实际有效的数据来源。
三个状态读取插件示例见 [内置条件目录](built-in-conditions.md#通用状态读取插件)。它们依赖保留的第一行 Cell，不调用 WoW API、不重复生成 Cell。

## 模板参数与常量

模板沿用项目 Lua 分区。在 `logical code` 开头、创建曲线或事件框架等逻辑之前，集中声明：

- 实例坐标、宽度和所有配置参数。
- 刷新间隔、固定技能 ID、数量上限、编码节点及其他业务常量。

`uuid` 是文件头元数据占位符，由生成器为本次实例分配随机 UUID4，与该实例文件名一致，每次生成重新分配。业务模板只动态生成坐标、宽度及循环中必要的可配置变量（如 `spell_ids`、`ignore_gcd`）；这些占位符只用于头部参数声明。`template_parameters()` 只返回已校验的必要配置参数，不接收任意 Lua 代码。
固定曲线、节点、算法和固定业务常量直接写在源码中，不通过 Python 序列化或模板占位符生成。集中声明不等于动态生成。
`uuid`、`xN`、适用的 `yN` 与 `widthN` 由核心从冻结布局注入，插件不得覆盖；不要把固定第二行重新写成另一份布局来源。

```lua
--[[  logical code  ]]
local POSITION_Y = {{y1}} -- 冻结布局的行
local POSITION_X = {{x1}} -- 冻结布局的横向位置

local runeCell -- 在 UIInitFuncs 回调中创建
local function InitializeRunes()
    runeCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
end
```

多区域使用编号对应的声明。函数临时变量保留在局部；运行期状态不能为了“集中声明”变成加载期快照，必须保留原初始化时机。
头部常量不意味着新增用户可配置字段。例如 GCD 的固定技能 ID 仍不接受 `plugin_args`。

## 配对与说明

Lua 编码和 Python 解码属于同一版本契约。缩放、精度节点、饱和、不可用表示、区域合并与列表过滤必须配对；固定的 Lua 编码曲线和 Python 解码节点分别写在各自源码中，通过配对测试确保一致；不得为了共用静态数据而动态生成固定曲线或算法。

除通用 Python 文件头外，每个条件插件必须说明：

- 用途、业务语义及 `plugin_args` 的字段、类型与约束。
- 输出类型、数量、业务类型、形状和物理尺寸。
- WoW API、核验来源与 Secret Value 的处理边界。
- 解码算法、业务不可用状态及异常兜底含义。
- 已知的插件版本变化，不编造历史。

在参数到输出的映射、解码舍入/区间、模板序列化等关键步骤解释原因。冷却的黑色含义不能复制到血量、能量或布尔插件。

## 刷新写法

仅借用区域几何与黑底的 Lua 插件直接使用 `CellBackplate` 或 `ValueBarBackplate`，不构造再隐藏普通组件内容；需要颜色/数值/图标方法的消费者继续使用原组件。背板字段、唯一计数责任及静态显示层级见[像素协议](../../phantom-code-dev/references/pixel-protocol.md#lua-背板与内容契约)。

- 事件刷新缓存 `local After = C_Timer.After`，通过 `After(0, function() update() end)` 延至下一帧；依赖事件参数的逻辑保留参数和过滤。
- 定时刷新缓存 `local random = math.random`，头部常量统一命名 `UPDATE_INTERVAL`：兜底为 1 秒，持续轮询为 0.1 秒。
- 在 `eventFrame:SetScript("OnUpdate", ...)` 前以 `local fastTimeElapsed = -random()` 初始化；累计 `elapsed`，严格超过间隔时扣除一个间隔并调用 `update()`，保留余量且每帧最多刷新一次。

## 条件实例生命周期

每次在配置中使用条件插件都会创建独立实例。核心维护 `conditions[title] = instance`。实例必须按以下顺序建立：

1. 校验 `plugin_args`，缺省参数使用本版本 `config_defaults`，保留必填约束和显式值验证。
2. 根据参数计算 `output_type`、`output_count`、`value_type` 和 `value_shape`。
3. 由布局器分配连续区域并冻结位置与数量。
4. 生成本实例对应的 Lua。
5. 运行时从截图区域读取 `raw_value(decoder)`。
6. 由 `value(cells, value_bars, icon_tiles, *, decoder)` 调用同签名的插件 `decode_value`，得到普通 Python 业务值。

冻结状态独立记录，包含 [零区域插件](#无-lua-与零区域插件) 在内，每个实例也只能冻结一次。

## 基类契约

- 基类公开 `raw_value(decoder)`，按冻结的输出描述读取原始区域。
- 基类公开 `value(cells, value_bars, icon_tiles, *, decoder)`，前三项均为列表，未使用的类型传空列表，并交给插件实现的同签名 `decode_value`。
- `decoder: PixelDecoder` 为必填关键字参数，所有实例收到本轮 rotation 使用的同一个解码器；插件可按公开坐标接口读取任意有效区域，不得修改帧数据或持有解码器供以后帧使用。
- 每个条件插件必须实现 `decode_value` 和 `fallback_value()`；任一缺失时，该插件类保持抽象，不能实例化。不保留旧签名兼容层。
- `decode_value` 中的额外读取或业务解码抛出任何异常时，`value()` 必须捕获异常并返回 `fallback_value()`。
- 插件可以在识别到业务不可用状态时主动返回自己的兜底值。
- `value()` 必须始终返回与声明的 `value_type` 和 `value_shape` 相符的值；核心不使用通用 `None` 业务值。

捕获全部解码异常会隐藏部分插件编程错误，这是用户明确接受的行为。插件仍应通过有效测试发现确定性错误。

兜底规则由插件版本按业务含义定义，必须与该版本的说明和 Python 返回类型一致；具体内置值见 [内置条件目录](built-in-conditions.md)。

## 核心边界

`phantom/core/condition/` 分别以 contracts.py、base.py、layout.py、template.py 和 registry.py 提供输出契约、生命周期、布局、渲染和精确加载。
Registry 按标识缓存类，实例不共享；非法标识、版本缺失、模块或参数错误均附带插件名称。精确版本、组合复用和核心职责见 [公共规则](common.md)。
output_count 与 value_shape 独立，ValueBar 的 widths 为每条内容宽度，支持单实例多区域。
冻结前验证兜底类型；输入列表数量错误、解码异常或业务类型不符返回已声明兜底。
框架分配区域的越界由调用层报告，不将整个错误布局伪装为正常业务值；插件通过 decoder 主动额外读取的异常在插件解码兜底边界内处理。
