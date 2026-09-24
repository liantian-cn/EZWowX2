# 系统架构

## 运行边界

Phantom 分为游戏外 Python 端和游戏内 Lua 端。Lua 端只负责采集游戏状态、编码与渲染数据以及建立已配置的安全按钮绑定；Python 端负责生成、截图、解码、求值和发送按键。

```text
rotation TOML
    ↓
Python 生成器 ──→ WoW 插件（共享基础模块 + UUID Lua）
                       ↓
                 画面角落像素协议
                       ↓
Windows 截图插件 → 条件实例解码 → rotation 白名单求值 → 键盘插件发送按键
                                      │
                                      └─ 无命中：本轮无动作
```

## 组件职责

- 生成器：校验配置与插件参数，实例化条件，冻结布局，生成一个插件包。
- 条件插件：声明输出契约，按需生成本实例 Lua，读取分配区域并可通过同帧 PixelDecoder 读取额外坐标，转换为业务值。允许无 Lua、零新增像素区域。
- 截图插件：在 Windows 上捕获约定屏幕区域，向条件层提供 NumPy 数组。
- 像素解析：`phantom/core/pixels/` 提供 `PixelDecoder`、`Cell`、`ValueBar`、`IconTile`，将完整基板按 Lua 坐标切分为独立区域，读取通用原始值，不包含条件业务公式。
- rotation 执行器：读取条件值，按配置顺序求值，返回首个命中的宏名称。
- rotation 内核：从固定池按声明顺序为全部宏自动分配键位，保留键位字符串并解析为平台中立的 KeyCombination，选择至多一个宏后交给键盘插件。
- 键盘插件：只发送明确按键；各自负责设备编码与目标，PostMessageW 在插件内部查找窗口，未来驱动或串口不必具有窗口目标。
- Textual TUI：承载采集启停、游戏与采集状态、通用数据、业务日志及当前 rotation 同帧决策；通过应用配置选择多份 rotation 并共同生成（见 [tui.md](tui.md)）。

## Textual 通信与任务

界面通过 Textual 的消息机制与后台任务协作，项目当前采用以下方式：

- 消息与事件：游戏检测结果、业务日志和停止完成通过自定义 `Message` 与 `post_message` 从后台线程投递到界面线程，再由消息处理方法更新控件，参见[官方消息与事件文档](https://textual.textualize.io/guide/events/)。
- 后台任务：阻塞的截图停止与资源释放通过线程 Worker 执行，不在界面线程调用阻塞接口，参见[官方 Worker 文档](https://textual.textualize.io/guide/workers/)。
- 主题：用 `register_theme` 注册固定纯黑深色的 `phantom-monochrome` 主题，颜色角色集中定义在 `phantom/ui/theme.py`。
- 测试：用 `run_test` 驱动真实控件、按键和尺寸变化，验证标签页、按钮状态与数据刷新。

当前不使用 `Signal` 与响应式属性 `reactive`；状态更新由显式消息和刷新方法完成。

## 生成插件模型

多份选择由 phantom.toml 管理，采用 2026-09-19 用户确认的[选择与回写规则](tui.md#多份-rotation-与生成2026-09-19-确认)，不提供多选 UI。

一次生成操作可以选择多份 rotation，并产生一个 WoW 插件包：

- 包名读取 addon.name，必须匹配 `[A-Za-z][A-Za-z0-9_]*`。
- 插件目录和 `.toc` 文件使用完全相同的包名。
- 通用能力写入共享基础模块。
- 每份 rotation 使用 `Specialization.key` 将点替换为下划线的专精目录，例如 `druid_restoration/`；每个条件声明实例各生成一个随机 UUID4 Lua，另生成一个独立的随机 UUID4 宏绑定 Lua。
- 每个专精目录内的 Lua 在加载开头检查 `unit_class` 和 `unit_spec`；不匹配时立即 `return`，不加载其余逻辑。文件名 UUID 使用带连字符的标准 RFC 4122 文本，不使用 rotation 配置 UUID。
- `unit_spec` 是 `GetSpecialization()` 返回的专精顺序索引，取值为 1、2、3 或 4。
- 切换专精后需要执行 `/reload`。当前不支持运行期热切换。

每个 `(unit_class, unit_spec)` 最多加载一份，不同组合共同生成。UUID 冲突在启动加载阶段修复并持久化；生成器另行防御重复组合和 UUID，避免覆盖。

## 循环语义

每一轮执行以下业务步骤：

1. 截取像素画布。
2. 更新所需条件实例的原始数据与业务值。
3. 从上到下求值 `rotation` 列表。
4. 第一个条件为真的条目胜出，并发送其宏键位。
5. 全部未命中时不发送按键。

每轮最多执行一个动作。“暂停”表示某一轮没有动作，不是一个需要额外恢复的持久状态。

## 预定源码结构

以下目录是代码工程的职责划分；`phantom/ui`、`phantom/core`、`phantom/captures`、`phantom/lua` 和 `rotations` 已在使用，`phantom/conditions` 已实现版本化条件，`phantom/keyboards` 已实现首个版本化键盘插件：

```text
phantom/
  main.py
  ui/
  core/
    macro_keys.py
    condition/
    capture/
    keyboard/
    pixels/
  lua/
    runtime/
    general/
  conditions/
  keyboards/
  captures/
scripts/
rotations/
  死亡骑士-鲜血.toml  # 以及其余39份职业专精配置
```

`phantom/lua/runtime/` 保存生成器使用的共享 Lua 运行时源码。这些源码会进入生成后的 WoW 插件，为条件插件生成的实例 Lua 提供公共运行能力；条件专属模板仍保存在对应的 `phantom/conditions/<name>@<version>/template.lua` 中。该目录不保存生成后的插件产物。

`phantom/lua/general/` 保存第一行通用字段的 Lua 实现，在 TOC 中于 runtime 文件之后加载。通用 Cell 仍使用 runtime 提供的普通 `Cell`，通过 `UIInitFuncs` 延迟创建以沿用共享尺寸换算和背景初始化；不另设 GeneralCell 类型。首个实现为 `01_player_class.lua`，文件头 `index: 1` 表示通用文件顺序元数据。

## 截图基础运行边界

`python -m phantom.main` 是 Textual 主程序入口：读取启动工作目录的应用配置、运行界面，并在退出时等待后台线程释放。
截图与像素解析仍由 `demo/demo.py` 和 `demo/demo01.py` 独立验证，demo 不经过 TUI，也不读取应用配置。

共享图像算法与线程调度位于 `phantom/core/capture/`，`phantom/captures/` 只存放版本插件。后端只负责截图，线程负责全屏定位、局部截图、校验和交付最新结果。
UI 通过截图核心注册器按 capture.plugin 创建后端，默认 gdi@dev；不直接导入版本实现。
截图使用独立后台线程，不使用子进程。主线程通过快照接口取得最新图像与状态，不排队保留历史帧。
持续运行采用新帧驱动：后台读取最新截图，单帧至多解码、求值和发送一次，不补跑积压帧；采集及读取上限沿用 capture.fps（默认 15）。截图耗时和发送耗时可能降低实际频率。

## 待定事项

- 天赋感知的 rotation 路由和对应重载规则。


## 生成器落地

phantom/core/rotation.py 负责配置验证、内存布局分配与冻结，以及成功加载后的条件默认参数补写；core/condition/registry.py 负责精确加载，core/generator.py 负责生成。
phantom/core/macro_keys.py 以 MACRO_KEYS tuple 显式保存固定键位池；rotation.py 按宏声明顺序为每份 rotation 独立分配全部宏，包括未引用宏。分配与旧字段兼容规则见[宏与键位](../../phantom-rotation-dev/references/configuration.md#宏与键位)，固定顺序见[宏键位池](../../phantom-rotation-dev/references/key-syntax.md#固定宏键位池)。
所有 load_rotation 入口统一在完整验证和布局成功后补写 rotation，不修改 phantom.toml。默认值来自精确版本 Condition 的公开 config_defaults，构造与回写共享来源；仅补缺失键并递归补充已有嵌套字典，保留必填约束和所有显式值。无实际变更不写，使用源文件并发检查及原子替换，写入失败使加载失败；后续生成失败不回滚已补写参数。完整规则见 [配置规范](../../phantom-rotation-dev/references/configuration.md#条件参数默认值与加载回写)。
旧 conditions[].layout 兼容接收但忽略，加载器不新增、更新或删除；布局始终根据条件输出在内存重建，分配规则和运行期冻结语义不变。
集合入口输出 runtime/ 与 general/ 源码副本、完整 media/ 二进制资源、所有已加载组合的专精目录和同名 TOC；保留单份生成包装入口。不复制 examples。字体与纹理路径不变，由 Lua 路径访问，不加入 TOC。
runtime/、general/ 的每个原始 Lua 文件各输出一个随机 UUID4.lua，生成副本文件头 uuid 同步文件名，original 保留源码溯源；不修改手写源码 uuid。每次 render/generate 全部重新随机分配，包内 UUID 不碰撞；检测到碰撞立即失败，不能静默覆盖。rotation 配置 uuid 不因生成而变化。
生成所有声明的条件，不去重、不跳过未引用条件。每个条件单独作为 Lua chunk 加载，文件头包含 UUID 标识和职业专精守卫，并保留统一 namespace 兼容；生成器不再添加外围 do/end，模板内部结构不改。可选模板只插入经过校验的参数与固定位置，无模板时仍产出带标识和守卫的文件；零区域与模板有无相互独立。Lua 状态、面板及第一行五个 Cell 保留；enable、爆发、delay 的 Python 读取改为显式条件插件，框架只保留职业与专精匹配检查。
TOC 顺序为 runtime 源码文件名排序、general 源码文件名排序，然后按 rotation 输入顺序依次列该专精的条件声明顺序与宏文件；不按随机文件名排序。

背板与内容运行时按 `07_cell_backplate.lua`、`08_cell.lua`、`09_value_bar_backplate.lua`、`10_value_bar.lua`、`11_icon_tile_backplate.lua`、`12_icon_tile.lua`、`13_mask.lua`、`14_specialization_reload.lua` 加载。源 TOC 同步此列表；生成器仅从 TOC 模板读取 `##` 元数据，文件条目由源码排序生成。移动手写文件保留 uuid，同步 original 与 runtime_index。
完整校验、渲染、资源读取成功且输出路径与整个旧树安全检查通过后，清空本 addon 目录全部内容（含隐藏、手工文件和旧子目录），不触碰兄弟目录。拒绝插件根及中间 Interface/AddOns 路径、旧树内的 symlink/junction/reparse point；目录位置为普通文件也拒绝。预准备或检查失败保留旧包。清理或写入失败立即停止，不重试、不回滚；TOC 最后写入且仅列本次产物。每个目标文件使用同目录临时文件替换，避免单文件截断；不提供整个目录的事务或备份。
每专精独立宏文件为全部声明的宏生成安全按钮及自动键位的覆盖绑定，包括未引用宏；空宏列表也输出该文件，函数调用结构避免 148 宏触发 Lua chunk 局部变量上限。按钮名由插件包名、rotation UUID 与宏序号确定。宏文本经过 Lua 5.1 字符串转义后作为安全按钮属性，不作为可执行 Lua 插入。配置中的旧 key/bind_key 完全忽略，不控制生成。运行器按同帧职业专精自动路由；切专精通过标准不可取消弹窗要求手动确认 /reload，不增加等待重载停键机制。

## 单帧决策报告

`core/expression.py` 负责加载期白名单／类型校验和运行期 AST 解释；`Rotation.trial` 依次进行同帧条件解码与首条命中求值。
返回结果包含该帧条件值、命中规则与可选宏；Idle 的宏为空。
后台 RotationRuntime 与独立 `demo/demo02.py` 复用单帧决策入口。后台运行器在命中有键位宏时调用 keyboard.send，TUI 读取其同帧截图和决策；独立 demo 仍只报告，不发送按键。
