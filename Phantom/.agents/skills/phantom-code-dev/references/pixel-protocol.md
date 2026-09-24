# 像素协议

## 画布布局

游戏内输出固定为四行，总高度 20 像素：

| 行 | 内容 | 区域高度 | 排列规则 |
| --- | --- | ---: | --- |
| 1 | 通用 Cell | 4 | 按通用字段声明顺序从左到右紧密排列 |
| 2 | 条件 Cell | 4 | 按条件声明顺序从左到右紧密排列 |
| 3 | Value Bar | 4 | 按条件声明顺序，以含红色分隔的实际占位宽度从左到右紧密排列 |
| 4 | Icon Tile | 8 | 按条件声明顺序从左到右紧密排列 |

每一行独立从左侧起排，不因其他行的区域宽度产生空洞。画布总宽度取四行占用宽度的最大值。

需要分配像素的条件实例只能选择 `cell`、`value_bar`、`icon_tile` 中的一种，但可以连续占用多个同类区域。不新增区域时使用 `none`、数量为 0，冻结空布局；它不改变其他条件坐标或基板宽度。区域数量在插件参数通过校验后计算，并在布局完成时冻结；运行中不得改变。插件还可通过同帧 PixelDecoder 读取分配区域以外的有效坐标，见[插件系统](../../phantom-plugin-dev/references/conditions.md#基类契约)。

## Lua 背板与内容契约

`CellBackplate:New({x=..., y=...})`、`ValueBarBackplate:New(x, width)`、`IconTileBackplate:New(x)` 返回独立包装实例，公开 `Frame`（内容矩形）和 `BackgroundTexture`（固定不透明黑底）。ValueBar 背板另公开 `SeparatorFrame`、`SeparatorTexture`；红色分隔与黑色内容框体均直接挂在 `addonTable.BackgroundFrame` 下，保持兄弟关系及左右半个 Cell 红边。

背板唯一负责原有各行长度累计及每次构造一次 `BackgroundFrameResize()`，仍按构造次数累计，不改为最大坐标算法。内容组件不再重复登记。背板只有构造及字段，不提供生命周期或主题接口。

`Cell`、`ValueBar`、`IconTile` 保留构造方式、原公开字段与方法，仅新增 `.Backplate`。Cell 直接复用背板 Frame，颜色 Texture 使用 ARTWORK；IconTile 同样复用 Frame，旧 Background 引用背板黑底，Icon 为 ARTWORK、Border 为 OVERLAY。ValueBar.Frame 保持指向黑色内容框体，普通 StatusBar 为其直接子级，保留 0–100 范围、50 默认值及原反向填充语义。

静态 FrameLevel 统一为：Canvas=9500、Separator=9550、Backplate=9600、Content=9650、AuraContainer=9700、AuraButton=9750、AuraContent=9800、Overlay=9850、Marker=9900。旧键不保留别名；Overlay 仅预留。定位与检测标记使用 Marker，普通 StatusBar 与吸收条使用 Content。Texture 仅有 DrawLayer，不建立独立 FrameLevel，也不为 Cell/IconTile 增造内容 Frame。

光环消费者直接使用背板，父子保持背板→AuraContainer→AuraButton→StatusBar；槽内 StatusBar 在初始化时设置 AuraContent，不创建再隐藏无用默认数值条。保留光环自己的黑底纹理和官方显示 consumer，不通过秘密值判断或运行时层级修补调整布局。离线契约验证不代表真实游戏像素绘制验收。

## 基板两侧检测色块

基板高度为 `5 * SIZE.CELL`，初始宽度为 `2 * SIZE.CELL`；内容区域扩宽时，两侧各保留一列。
左上角与右下角各保留一个定位标记，其余八个位置用于检测色块。以下偏移均以 `SIZE.CELL` 为单位。

| 色块 | 色块与背景的对齐锚点 | 相对偏移 | RGB（各分量除以 255） |
| --- | --- | --- | --- |
| Cyan | TOPLEFT | `(0,-1)` | `(0,255,255)` |
| Magenta | TOPLEFT | `(0,-2)` | `(255,0,255)` |
| Yellow | TOPLEFT | `(0,-3)` | `(255,255,0)` |
| Flash | TOPLEFT | `(0,-4)` | 黑白交替 |
| Red | BOTTOMRIGHT | `(0,1)` | `(255,0,0)` |
| Green | BOTTOMRIGHT | `(0,2)` | `(0,255,0)` |
| Blue | BOTTOMRIGHT | `(0,3)` | `(0,0,255)` |
| Gray | BOTTOMRIGHT | `(0,4)` | `(127,127,127)` |

每个色块使用独立 Frame 及其自身创建的 Texture，宽高均为 `SIZE.CELL`，透明度固定为 1。
Flash 初始为黑色，由局部 `eventFrame` 在 `OnUpdate` 中累计时间，每秒切换一次黑白。
这些色块提供截图颜色校验画面，不属于业务 Cell，不计入内容区域长度，也不向 `addonTable` 暴露实例。

## Python 截图定位与校验

只识别非 DEBUG 输出，不自动调整游戏插件的 DEBUG 开关。完整基板包含左右检测列，高度固定 20 像素，宽度至少 8 且为 4 的倍数。
左上角与右下角的 4×4 定位符均由四个 2×2 色块组成，排列为 `0/1、1/0`，
RGB 分别为 `POINT_0=(15,25,20)`、`POINT_1=(25,15,20)`。全部 16 像素精确匹配，不使用相似度或容差。
按照高度和宽度约束配对，两个角标最外侧边界构成截图区域；多个几何合法候选视为歧义，不按首个匹配选择。

后端在交付图像前归一化为 RGB `uint8` 三通道数组。两侧八个检测块分别取中心 2×2，
四个像素必须全部精确等于表中指定 RGB。Flash 必须四像素全黑或全白，不接受黑白混合，也不检查跨帧交替。
校验结果、重新定位和错误交付行为见截图 worker 契约。

## Cell

Python 通用解析入口为 `phantom.core.pixels.PixelDecoder(pix_array)`，接收包含左右检测列的完整
RGB `uint8` 基板数组，高度为 20、宽度至少 8 且为 4 的倍数。三个读取方法采用 Lua 相同入参：

| 方法 | 左上像素坐标 | 完整区域宽×高 |
| --- | --- | --- |
| `getCell(x, y)` | `(4*x, 4*(y-1))` | `4×4` |
| `getValueBar(x, width)` | `(4*x, 8)` | `4*(width+1)×4` |
| `getIconTile(x)` | `(4+8*(x-1), 12)` | `8×8` |

`x`、`width` 必须是正整数，Cell 的 `y` 为 1 或 2；越过内容区或进入检测列的请求抛出异常。
Decoder 负责切分，区域构造器只分析已切分的 RGB 数组，坐标仅用于定位。
每个区域持有独立只读快照，后续输入变化不影响已有区域或 hash 缓存。
三个区域均通过只读属性 `pos`、`region` 返回相对完整基板的物理像素坐标，
矩形右下不包含；`pos_string`、`region_string` 为无括号、无空格的逗号分隔字符串。
例如 Cell(1,1) 的 region 为 `(4,0,8,4)`，region_string 为 `"4,0,8,4"`。

- 物理尺寸固定为 4×4。
- Python 读取 NumPy 数组时只信任中间 2×2，即 `cell_pix_array[1:3, 1:3]`。
- `Cell(x, y, pix_array)` 保存 `x`、`y`、完整 `pix_array` 和内部 `inner`。
- 只读属性 `mean` 为内部全部 RGB 分量的均值，`ratio = mean/255`，`percent = ratio*100`，均返回 Python `float`。
- `is_pure` 判断内部所有 RGB 像素一致，`is_not_pure` 取反；`color_string` 使用内部左上像素，格式为 `"r,g,b"`。`is_black`、`is_white` 要求内部全部像素严格为黑、白。
- 未来条件插件的 `raw_value()` 保留所需 RGB 原始信息；如何映射业务值由版本化编解码契约决定，当前 Cell 不提供该插件接口。

边缘像素不参与计算，因为游戏渲染、抗锯齿和缩放可能污染边缘。

### 第一行通用字段

首个字段固定为玩家职业，使用普通 `Cell`，坐标为 `x=1, y=1`，位于左侧定位列之后。
灰度值为 `select(3, UnitClass("player"))` 返回的 `classID`，RGB 三个分量均为 `classID / 255`，透明度为 1；未返回职业 ID 时使用灰度 0，表示暂不可用。
构造函数注册到 `UIInitFuncs`，沿用共享缩放、通用行计数和背景扩宽；构造完成立即刷新，之后由独立事件框架在 `PLAYER_LOGIN`、`PLAYER_ENTERING_WORLD` 刷新。初始化前到达的事件不访问未创建的 Cell。

第二个字段固定为玩家当前专精的顺序索引，使用普通 `Cell`，坐标为 `x=2, y=1`。
通过局部缓存的 `C_SpecializationInfo.GetSpecialization` 无参数读取 `specializationIndex`，RGB 三个分量均为 `(specializationIndex or 0) / 255`，透明度为 1；无返回值时使用黑色，数值索引直接保留，包括 5，不限制为 1–4。
构造函数同样注册到 `UIInitFuncs`，沿用共享缩放、计数和背景扩宽，构造完成立即刷新。独立事件框架监听 `PLAYER_LOGIN`、`PLAYER_ENTERING_WORLD`、`ACTIVE_PLAYER_SPECIALIZATION_CHANGED`，并使用 `RegisterUnitEvent("PLAYER_SPECIALIZATION_CHANGED", "player")` 过滤玩家专精事件；初始化前事件不访问未创建的 Cell。
该字段只显示当前专精，不改变 rotation 切换专精后需要 `/reload` 的规则。
多份运行器以严格灰度纯色读取前两个 Cell 路由；没有可用组合不发键，不通过 RGB 均值猜测职业专精。协议不新增已加载 rotation 身份或等待重载字段。2026-09-19 用户确认只通过游戏弹窗提示重载，接受切专精后当前索引可能先于 UUID Lua 布局变化的间隙，不额外隐藏画布或停键。

第三个字段为插件启用状态，坐标 `x=3, y=1`，每次读取 `addonTable.ENABLE`；第四个字段为爆发状态，坐标 `x=4, y=1`，每次调用 `addonTable.InBurst()`。两个字段均使用普通 `Cell:setCellBoolean`，true 为不透明白色，false 为不透明黑色；启用状态不影响爆发字段的独立输出。
两个构造函数注册到 `UIInitFuncs`，沿用共享缩放、计数和背景扩宽，构造完成保持默认黑色，等待错峰首次刷新。
每个文件各自使用独立事件框架和 `fastTimeElapsed = -random()`（`random` 为 `math.random`），通过 `HookScript("OnUpdate", ...)` 累加 `elapsed`；严格超过 `0.1` 秒时减去 `0.1` 并刷新一次，每帧最多一次，保留剩余累计时间。初始化前刷新安全返回，不增加其他事件刷新或修改随机种子。

第五个字段为延迟状态，坐标 `x=5, y=1`，每次调用 `addonTable.Delaying()`，使用普通 `Cell:setCellBoolean`：延迟中为不透明白色，否则为不透明黑色。该字段独立于 ENABLE 和爆发状态输出。
`DelayTime` 加载时初始化为 `GetTime()`，默认不延迟；`Delaying()` 判断截止时间是否严格晚于当前时间，`DelayRemaining()` 返回不小于 0 的实际剩余秒数，不限制上限。
第五个字段沿用上述状态 Cell 的 `UIInitFuncs` 初始化、初始黑色、独立事件框架、随机错峰和 0.1 秒节流规则。

## Value Bar

- 高度固定为 4 像素。构造入参 `width` 表示黑白内容宽度，以 Cell 为单位，由插件输出描述决定；内容宽度为 `4 * width` 像素。
- 每条 Bar 的内容左右各保留半个 Cell 的红色分隔，实际占位宽度为 `width + 1` 个 Cell，即 `4 * (width + 1)` 像素。布局与画布行宽计算必须包含分隔占位。
- 构造入参 `x` 表示包含左侧红色分隔的占位起点，相对背景左上角，以 Cell 为单位；黑白内容从 `x + 0.5` 个 Cell 处开始。下一条 Bar 的入参必须为 `next_x = x + width + 1`，不能只累加 `width`。
- `bar_pix_array` 覆盖该 Bar 的完整占位区域，包含两侧红色分隔；只读取中间两行：`inner_pix_array = bar_pix_array[1:3, :]`。
- 只有像素值严格等于 `(255, 255, 255)` 才计为白色，严格等于 `(0, 0, 0)` 才计为黑色；红色分隔及其他颜色均不参与分子或分母。
- 原始值是白色像素占黑色与白色像素总数的百分比，范围为 `0.0` 到 `100.0`；没有黑白像素时返回 `0.0`：

```python
white_mask = np.all(inner_pix_array == (255, 255, 255), axis=2)
black_mask = np.all(inner_pix_array == (0, 0, 0), axis=2)
white_count = int(np.count_nonzero(white_mask))
black_count = int(np.count_nonzero(black_mask))
total_count = white_count + black_count
result = 100.0 * white_count / total_count if total_count > 0 else 0.0
```

`ValueBar(x, width, pix_array)` 保存 `x`、`width`、完整 `pix_array` 与 `inner`。
只读属性 `ratio` 返回白色占有效黑白像素的 0–1 比例，`percent` 返回上述 0–100 百分数，
两者无有效黑白像素时均为 `0.0`；不提供含义模糊的 `value` 或反向参数。
未来插件可通过 `raw_value()` 读取百分比，再在 `decode_value()` 中缩放或转换。

## Icon Tile

- 每个 Icon Tile 物理尺寸固定为 8×8。
- Lua 构造入参 `x` 为从 1 开始的槽位编号；相对背景左边缘的偏移为 `SIZE.CELL + (x - 1) * 2 * SIZE.CELL`，跳过左侧检测列后紧密排列。调用方直接传入 1、2、3，不使用从 0 开始的编号或额外坐标换算。
- 只信任中间 6×6，即 `icon_tile_pix_array[1:7, 1:7]`。
- 中间区域全黑时，该槽位的原始值为 `None`。
- 否则先保证数组连续，再以 seed 0 计算 `xxh3_64_hexdigest`，返回 16 位小写字符串。
- `IconTile(x, pix_array)` 保存槽位 `x`、完整 `pix_array` 与内部 `inner`；`is_black`、`is_pure`、`is_not_pure` 均分析整个内部 6×6。`hash` 为只读属性，通过实例 `_hash_cache` 缓存非空结果。
- 多 Icon Tile 条件的 `raw_value()` 始终返回长度等于 `output_count` 的列表，并用 `None` 保留空槽位。

插件的 `value()` 可以删除空槽、重新组织列表或合并多个区域。业务列表的排序由插件契约定义，核心不附加统一顺序。

## 输出描述

每个条件实例必须分别声明：

- `output_type`：`cell`、`value_bar`、`icon_tile` 或 `none`；`none` 的 `output_count` 固定为 0，不分配区域。
- `output_count`：连续占用的同类区域数量。
- `value_type`：`bool`、`int`、`float` 或 `str`。
- `value_shape`：`scalar` 或 `list`。

像素区域数量与业务值形状是两个独立维度。多个区域既可以合成为高精度标量，也可以解码为列表。

## 待定事项

- 第一行除已确定的玩家职业、专精索引、启用状态、爆发状态和延迟状态字段之外，其余通用 Cell 的字段及语义；战斗状态只是候选项。
- Cell 的通用颜色约定和各条件的精度分段。
- Value Bar 百分比到具体业务值的编码规则。
