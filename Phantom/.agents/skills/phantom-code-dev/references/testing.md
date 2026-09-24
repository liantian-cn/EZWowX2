# 测试规则

## 测试边界

Phantom 最终运行在 Windows，而日常开发环境是 WSL2 与 Docker。容器无法真实覆盖 GDI 截图、Windows 窗口消息和游戏内受保护 Lua 行为，因此不得为了形式完整而编造无效的跨平台集成测试。

这不代表跳过可验证逻辑。与平台无关、容易出错且影响协议一致性的算法必须测试。

## 优先测试内容

- TOML schema、唯一标题/宏名称、UUID、职业/专精和非空宏文本校验；schema_version 保持 1。
- 宏自动键位分配：固定池共 148 个唯一键位、仅使用 RCTRL/RALT/RSHIFT、分组顺序与标点顺序、RALT-F4 与 RALT-RSHIFT-F4 排除、全部宏按声明顺序分配（包括未引用宏）、每份 rotation 独立从池开头分配；空宏列表与 148 个宏允许，149 个宏拒绝加载且不回写。
- 旧 macros[].key/bind_key 的任意合法 TOML 值完全忽略、不校验、不警告、不自动清除；不能改变分配或生成结果，旧 bind_key=false 也必须提供非空 macro_text。默认参数回写保留残留字段，自动键位不写回配置。
- 全部声明的宏均生成安全按钮及覆盖绑定，未引用宏也包含在内；内部键位字符串、冻结的 KeyCombination、Lua 绑定与运行期发送保持一致。
- rotation 默认参数补写：全部校验及布局成功后才写、所有 load_rotation 入口一致、构造与回写共享 config_defaults、递归补充已有嵌套字典、保留 false/0/合法空值、拒绝非法显式值及缺失必填字段；dispel_types 整体必填且只补七个缺失子键为 false。
- 参数或模式派生的 width 不补写：多实例独立、显式宽度优先、量程与条宽分离、新缺省公式和非法宽度不回写。灵魂碎片 fractional 默认 false 可补写，小数模式宽度不补写；用合成完整区域验证0–50片段和1.5/4.0阈值。
- rotation 写入边界：无默认不创建空 plugin_args、无变更不写、保留注释和其他内容、原子替换、并发源检查、写入失败导致加载失败、后续生成失败不回滚；旧 conditions[].layout 兼容忽略且不增改删，内存布局保持原规则，phantom.toml 不受影响。
- 白名单 AST 的允许节点、拒绝节点、优先级、条件引用和类型检查。
- rotation 自上而下首个命中、每轮最多一个动作和无命中行为。
- Cell 中间 2×2 与 Icon Tile 中间 6×6 的裁剪。
- Value Bar 中间两行、严格纯白判断和 `0.0`–`100.0` 百分比。
- Icon Tile 全黑空值、连续数组 hash 和多槽位 `None` 占位。
- 插件参数校验、输出数量冻结、Lua/Python 成对编解码和兜底。
- 多行独立紧密布局、声明顺序和画布最大宽度。
- 背板纯构造、固定黑底和三类几何；ValueBar 红黑兄弟与半 Cell 红边；背板及普通组件混用时每次构造只计数/扩宽一次；普通组件默认颜色、半满/反向、图标清空保留；Aura 不创建无用默认条，静态层级与父子拓扑保持。入口为 `tests/test_backplates.py` 与 Aura 条件测试。
- WoW 连字符键位到 Windows 输入的映射；拒绝通用和左侧修饰键，验证右修饰通用 VK 配指定扫描码/扩展位、主键扫描码、导航与小键盘区别、按下/释放 lParam、失败清理。
- 应用配置的工作目录定位、缺失字段默认值、非法输入拒绝；多份选择按需回写并保留无关字段和注释，无实际选择变更不写。显式优先、失败回退、无候选保留原值、回写失败仍使用内存、只读发现、UUID 冲突修复及严格 40 组合须独立覆盖。
- 集合生成按 40 专精映射目录输出每个条件实例及独立宏文件；多实例不去重，未引用、无模板及零区域条件均覆盖。逐文件作为独立 Lua 5.1 chunk 加载，检查职业专精守卫和 0/2/148 宏绑定行为。TUI 生成复用启动快照，文件修改重启生效。
- 全部 Lua 每次 render/generate 使用全新随机 UUID4，包内唯一，模拟 UUID 碰撞必须拒绝；runtime/general 副本头 uuid 同步文件名，original 和手写源码不变，rotation uuid 不变。TOC 按共享源码顺序、rotation 输入及条件声明顺序、宏文件排序，不依赖随机文件名。
- 重复组合/UUID、空集合、后续项渲染或资源读取失败在清理前拒绝并保留旧包。成功生成清空本 addon 全部旧内容（隐藏、手工文件、旧子目录），兄弟目录不变。根、中间目录及旧树 symlink/junction/reparse、普通文件根均拒绝；真实链接按平台能力验证，另用 reparse double 覆盖路径位置。模拟清理失败不得写入，模拟写入失败不得继续发布 TOC，不重试、不回滚。
- 运行器 A→B→无匹配→非法像素→恢复的同帧路由、布局及决策一致；手动暂停不自动解除，底栏长名称保持单行。专精重载 Lua 使用 Lua 5.1 doubles 验证初始化不弹、真实变化弹、重复事件去重、无取消/Esc 关闭及点击 reload；游戏内表现另验。
- 游戏检测的 `wow.exe` 名称与 `_retail_` 直接父目录判定、无法核验的候选路径、游戏退出自动暂停与返回后手动启动。
- TUI 的标签切换、按钮可用性、最小尺寸提示、慢速停止期间的响应性、业务日志时间戳与连续去重、暂停或失败后清空旧数据。
- 截图线程终止与可恢复错误的区分、显式重新启动、退出后后台线程结束。

## 测试质量

- 测试业务与算法结果，不写只比较大段固定字符串的脆弱测试。
- 生成代码测试应检查结构、契约和关键语义，不依赖无意义的空格或换行。
- 每个已知边界至少覆盖正常值、边界值和不可用输入。
- 固定布局与优先级的引擎/TUI 测试使用独立 fixture，不依赖正式职业循环的动作或条件数。全部 40 份正式配置做集合、schema、精确插件参数、UUID、宏、布局与 Lua 语法通用验证；其中 38 份 TXT 配置保留冻结 fixture 的独立语义回归，鲜血／防护两份 JSON 迁移另做对应语义测试。常驻测试不依赖外部参考仓库。
- `load_rotation()` 只加载副本。插件新增默认参数时，副本正常补写不应导致“必须字节不变”的误报；只允许精确插件及指定缺失键发生预期变化，保留显式值与其余内容，正式文件仍不得借验证回写。此次玩家光环 `player_only=true` 的默认补入不要求批量修改其余配置。
- catch-all 解码兜底不能代替插件单元测试；确定性编程错误仍须被测试发现。
- 所有手写 Python 源码必须通过 mypy strict 静态类型检查。
- 截图测试输入完整合成图像或图像序列，验证定位、裁剪、中心颜色及 worker 的业务状态流转；不写简单字符串或算术测试。

## 分层验证

| 层级 | 执行环境 | 目标 |
| --- | --- | --- |
| 纯 Python 单元测试 | Windows、WSL2、容器 | 表达式、布局、schema、编解码、键位映射 |
| NumPy 图像算法测试 | Windows、WSL2、容器 | 裁剪、白色占比、空 Icon Tile、hash |
| 生成产物结构检查 | Windows、WSL2、容器 | TOC、共享模块、UUID Lua 和条件提前返回 |
| Windows GDI/PostMessage 集成 | Windows | 在 Windows 环境验证窗口定位、截图和按键发送 |
| WoW 游戏内验证 | 安装目标游戏的 Windows | 在目标 12.1 build 验证 API、渲染、安全按钮和保护状态 |

只有后两层才能证明完整端到端行为；容器测试结果不得被描述为已经验证 Windows 或游戏运行。

## 工程检查

在仓库根目录执行，按改动选择相关检查；业务改动应完成相应测试：

```powershell
.venv/Scripts/python -m pytest
.venv/Scripts/python scripts/check_types.py
.venv/Scripts/python -m ruff check phantom rotations tests demo scripts
.venv/Scripts/python -m ruff format --check phantom rotations tests demo scripts
```

`scripts/check_types.py` 先检查核心、测试与脚本，再逐个检查精确版本插件入口。单独运行 mypy 会遗漏含 `@` 的版本目录；不能因模块同名冲突而跳过插件。

## 按改动选择验证

| 改动 | 现有验证入口和重点 |
| --- | --- |
| 像素和截图 | `tests/test_pixels.py`、截图相关测试；合成图像、定位、裁剪、所有权、启动停止和错误结果 |
| TUI 和应用配置 | `tests/test_ui.py`、`tests/test_configuration.py`、`tests/test_game.py`；真实控件、消息、清空过期数据和退出 |
| 条件插件 | `tests/test_conditions.py`、`tests/test_player_conditions.py`、`tests/test_condition_frame.py`；同帧 decoder、参数、兜底、Lua/Python 配对 |
| 生成和循环 | `tests/test_generator.py`、表达式与 rotation 测试；Lua 5.1、类型白名单、首条命中、Idle、新帧去重 |
| 键盘 | 键盘与 runtime 测试；按下/逆序释放、部分失败、停止等待和窗口唯一性 |

生成 Lua 使用 `lupa.lua51` 解析，现有 API doubles 配合真实 Cell/IconTile 等消费者验证；doubles 不能证明 WoW 的全部秘密值和访问限制。
rotation 离线检查使用临时副本：`load_rotation()` 可能补写缺失的条件插件默认参数，不能把正式配置当成只读验证输入；旧 layout 字段只兼容接收并忽略，不回写布局。
Windows 消息测试仅对测试创建的隐藏窗口发送。真实游戏按键、宏绑定、渲染和闭环验收单独报告。

独立 demo 统一先说明演示内容、等待 3 秒、采集 5 秒：`demo/demo.py` 验证截图，`demo/demo01.py` 验证像素，`demo/demo02.py [rotation.toml]` 用最后结果解码求值并只报告，不发送按键。
数组保存验证重新加载后的 dtype、shape、RGB 内容及状态，不比较 JSON 排版。桌面 smoke 和合成图像不能代替游戏验收。

## 待定事项

- 覆盖率工具。
- Windows 手工验证清单与可重复测试环境。
- WoW 12.1 build 的兼容矩阵和回归频率。

## 历史证据

仅追溯过去验收时读取 [历史验收记录](history/verification-history.md)；旧数量和游戏结果不是当前保证。
