# 历史验收记录

以下为原测试规范中的历史证据，日期、数量和环境限制按原记录保留。不能作为当前工作区或游戏环境已验证的结论。

## 玩家条件迁移验收（2026-09-15）

新增 23 个 `liantian_cn.player_*@dev` 条件插件，新增 159 项测试；完整 pytest 为 562 passed、5 skipped。
跳过项仍是 Windows 缺少符号链接权限的既有路径逃逸测试，不计为验证通过。
`scripts/check_types.py` 严格检查通过，包含全部 34 个条件版本入口及截图、键盘插件；Ruff check 与 format --check 通过。

- Python：参数缺失/多余/非法类型，ID 列表、饰品位置、零阈值及数值精度上限、驱散空表/全 false；灰度/黑白/图标解码与异常兜底。
- 配对：职责四值、近战计数 0–40、全部 player/party/raid 目标、施法与通道进度端点及中间值，IconTile hash 与空字符串。
- Lua 5.1：实际生成模板配合项目真实 Cell/IconTile 实现执行，验证提前到达的世界事件、单位过滤、下一帧移动刷新、独立随机错峰及余量、饰品双实例、施法/通道/蓄力转换、技能刷新取消和目标清理。
- 受管显示：AuraContainer doubles 检查固定 slot、候选过滤、白色贴图及公开刷新入口；StatusBar doubles 接收原始不透明秘密对象，验证 N/N+1 边界和秘密颜色/纹理直接传递。
- 生成：全部 23 个条件同份 rotation 的 Lua 5.1 语法、第二行 22 个 Cell 与第四行一个 IconTile 的独立布局、同帧 PixelDecoder 读取。

秘密对象 doubles 只能发现部分不允许的普通操作，不等价于 WoW 引擎的全部访问限制。AuraContainer doubles 验证声明的过滤和显示契约，不冒充真实光环筛选或游戏渲染。
本次未安装到游戏目录、未向游戏发送按键；实际 WoW 12.1 渲染与受限环境验收仍待游戏内验证。

## 同帧插件接口验收（2026-09-14）

当前完整 pytest 为 386 passed、5 skipped；跳过项均为 Windows 缺少符号链接创建权限的既有路径逃逸测试，不计为验证通过。`scripts/check_types.py` 严格检查核心、测试及十一种条件、截图和键盘版本入口通过；Ruff check 与 format --check 通过。

新增回归覆盖同帧 decoder 实例传递、跨帧更新、三类额外区域读取、分配区域越界先行失败、零区域冻结与兜底类型、可选/空/损坏 Lua 模板、生成 Lua 5.1 执行、显式条件声明与自由命名、三个状态插件的指定兜底及继续求值、两行通用 TUI 与十项配置条件展示。原有八个插件配对解码与新帧去重/Idle/恢复回归通过。

生成输出使用临时目录；未安装生成插件到游戏目录，未向游戏发送按键，未进行游戏内验收。完整测试中的 Windows 消息测试仅面向测试创建的隐藏窗口。

## 第 7–10 步离线验收（2026-09-12）

新增配置、布局、多区域、插件参数、灰度/充能/冷却解码、Lua 生成及 TUI 集成测试。
160 项 pytest 通过；mypy strict、Ruff check 与 format --check 通过。
`condition.py` 在含 @ 的精确版本目录下不能作为普通包被 mypy 合并扫描（会冲突为同名模块）。
统一类型检查入口为 `.venv/Scripts/python scripts/check_types.py`：先检查核心/tests/scripts，
再逐个检查八个精确版本 condition.py，任何失败都返回非零；不跳过插件检查。
Ruff 命令增加 scripts 目录。运行依赖新增 tomlkit==0.15.1，开发依赖新增 lupa==2.8。
测试使用 lupa.lua51 编译全部生成 Lua，执行真实生成条件模板与 API doubles，再把输出构造成完整 NumPy 基板验证 Python 业务值。
特别覆盖 GCD 不查询法术书、固定 61304/false、无 duration 输出黑色、普通技能筛选和职业专精不匹配不注册条件。
TUI run_test 覆盖无游戏生成、错误后修复重试、同帧条件值、暂停/专精不匹配清空、慢速生成期间响应与退出等待。
实际游戏安装目录下的 `Interface/AddOns/Phantom` 已生成 23 个文件（含 6 个 media 资源），TOC 引用 16 个存在的 Lua，全部通过 Lua 5.1 解析，未引用 examples。
没有启动游戏、安装宏绑定或发送按键；该记录仅证明离线生成与算法，不证明游戏端 API/渲染。

## 插件职责重构验收（2026-09-13）

核心与版本目录分离后，228 项 pytest 通过，scripts/check_types.py 严格检查核心及八个条件、一个截图入口通过；Ruff check 与 format --check 均通过。
新增校验器/解码器边界、临时截图插件精确加载与错误上下文、默认与显式配置、UI 前失败、非默认 Lua 坐标/宽度、冷却全区间配对测试。
Windows 使用核心截图注册器创建默认 GDI，以 5 FPS 完成两次启动和停止；均报告未找到非 DEBUG 基板，停止后没有 phantom- 线程。
该 smoke 验证真实 GDI 调用、错误交付与资源释放，未取得游戏基板，不代表游戏内验收。

## 第 11–13 步验收（2026-09-13）

275 项 pytest、`scripts/check_types.py`（核心及各精确版本入口）、Ruff check 与 format --check 通过。
表达式回归覆盖白名单、比较／成员／布尔组合、类型不匹配、禁止隐式真假值、加载失败不回写、短路与 AST 复用；rotation 回归验证首条命中与 Idle。
TUI 回归覆盖同帧条件及决策、宏名称日志去重、单次报告、无命中替换旧动作、截图失败／职业专精不匹配／暂停清空。

独立单次试运行：`.venv/Scripts/python demo/demo02.py [rotation.toml]`。
遵循 demo 的等待 3 秒、采集 5 秒流程，用最后结果解码求值一次，报告所有条件、命中规则、宏名称及键位，不发送按键。
真实游戏基板为 `(20,36,3)`，八项值为 `0.0, 6, 2, False, 0.0, 0.0, 100.0, False`，命中第 3 条“死神的抚摩冷却==0”，报告“死神的抚摩 / CTRL-NUMPAD3”。
Textual `run_test` 连接真实游戏检测与 GDI 得到相同结果，日志窗口存在宏名称及单次试运行详情，停止清空决策，退出后无 phantom 线程。
这是当前静态游戏帧与真实控件验证，不代表已覆盖新的游戏内动态场景或真实动作执行；未重生成／安装 Lua，也未发送游戏按键。

2026-09-13 后续调整：按用户要求移除 TUI 单次试运行按钮，决策与宏名称日志统一随启动后的采集刷新；独立 demo 保留。TUI 回归直接验证自动决策和日志。

2026-09-13 提交前复核：原 275 项测试中有两项在 Textual 卸载控件期间刷新失败。
刷新入口增加应用消息循环运行状态检查；新增两种截图线程状态下的真实界面卸载回归，修复前均复现 `#decision` 缺失，修复后完整 pytest 为 277 passed。
完整严格类型检查、Ruff check 与 format --check 通过；退出回归同时确认采集停止及无残留 phantom 线程。本次未重复真实游戏验证。

## 第 14–17 步离线与 Windows 消息验收（2026-09-14）

本次实现键盘插件、宏绑定生成、通用布尔表达式及新帧驱动运行。368 项 pytest 通过，5 项既有符号链接路径逃逸测试因 Windows 缺少创建链接权限跳过；不将跳过描述为已验证。完整 scripts/check_types.py 严格类型检查通过，包含八个条件、一个截图及一个键盘版本入口。

- 键位：合法/非法组合、全部声明键的 Windows 映射、精确插件加载、窗口标题精确唯一匹配、发送顺序和部分失败释放。
- Windows：真实 PostMessageW 仅发送至测试创建的隐藏窗口，验证 CTRL-1 / ALT-F4 的消息队列及逆序释放；未向实际游戏发键。
- 生成：Lua 5.1 解析、标准安全按钮/覆盖绑定 API doubles、多行/引号/反斜杠/控制字符文本保真、bind_key=false 不生成绑定、职业专精守卫。
- 运行：新帧去重、相同内容的新帧、Idle/恢复、无效截图、引用布尔变量的黑白校验、未引用字段不门控、停止等待释放、失败后手动重启、界面响应与清空。
- 双插件：精确加载的合成截图后端复用真实 ThreadCaptureWorker 定位裁剪与帧发布，再由实际 RotationRuntime 决策，交给精确加载的记录型键盘后端。无第二种真实截图或键盘设备实现。

完整检查使用 pytest、scripts/check_types.py、ruff check 和 ruff format --check（phantom rotations tests demo scripts）。独立 demo/demo02.py 继续只报告，不发送按键。

待有游戏环境后，使用普通键和组合键核对游戏动作、重载生成绑定并检查 bind_key 两种模式；验证启用/延迟表达式、Idle 后恢复、持续运行与停止。当前没有安装生成产物，也未验证真实游戏动作或持续闭环。

图像测试覆盖边界尺寸、精确角标、多基板歧义、DEBUG 拒绝、中心像素污染与边缘容忍、Flash 黑白、
负坐标桌面、色错保留区域与恢复、移动后重新定位、最新结果所有权、停止和重启、运行中更新 FPS 与底层错误交付。
数组保存测试应比较重新加载的 dtype、shape、RGB 内容及关联状态，不比较 JSON 排版。

Windows 可运行定时 demo 验证真实 GDI 调用、停止及文件输出。无非 DEBUG 基板时应得到 `has_error=true` 和未定位原因，不生成 NPY。
2026-09-12 用户确认第三步截图已测试成功；当日像素解析 demo 也成功读取当前游戏基板。
真实游戏验收使用非 DEBUG 画面；移动重定位等具体场景仍以各任务实际验证记录为准。
桌面 smoke test 与合成图像测试不能代替游戏验收。

像素解析测试见 `tests/test_pixels.py`，覆盖 Lua 坐标切分、边缘污染、严格黑白、无有效黑白像素、
空槽及非空 hash、非连续数组、独立只读快照和缓存、区域越界及 demo 错误结果拒绝。
运行 `python demo/demo01.py` 可验证同一游戏截图的十个 Cell、一个 ValueBar 和两个 IconTile。
2026-09-12 实测第一行亮度为 `6,1,255,0,0`，第二行为 `255,0,0,0,255`，
ValueBar ratio 为 `1.0`、percent 为 `100.0`，两个 IconTile 均为空槽 `None`。
非空 IconTile hash 已由合成图验证，本次游戏画面未覆盖非空图标。

TUI 与应用生命周期测试见 `tests/test_ui.py`、`tests/test_configuration.py` 和 `tests/test_game.py`。
它们使用 Textual 的 `run_test` 驱动真实控件、按键与尺寸变化，并用假截图 worker 覆盖标签切换、最小尺寸提示、
慢速停止、线程终止、游戏退出自动暂停和日志淘汰；游戏与路径判定使用伪造进程，不依赖游戏运行。
2026-09-12 在 Windows 执行 `python -m pytest` 得到 82 passed，`python -m mypy`（strict）与
`ruff check`／`ruff format --check` 均通过。

同日完成 Windows 桌面 smoke 验证：真实入口在启动工作目录创建默认 `phantom.toml`，界面以暂停状态打开，
未检测到游戏时“启动”保持禁用，标签顺序为综合→通用条件→日志→宏绑定→循环条件，Ctrl+Q 正常退出且不残留 `phantom-` 线程；
该次验证记录的浅色解析样式（Base `#eff1f5`、Text `#4c4f69`、Mantle `#e6e9ef`、Blue `#1e66f5`）在同日主题先后改为 Catppuccin Mocha 与 Flexoki 后失效。
纯黑主题通过 Textual 真实控件运行（`run_test`，120×46）重新解析：活动主题为 `phantom-monochrome`（dark，primary `#FFFFFF`，background `#000000`），
Screen 背景为 `#000000`、正文为 `#EDEDED`、容器为 `#111111`，状态行正常使用 `#4ADE80`，暂停和未运行使用 `#A1A1AA`。
本次环境无法分配交互式终端（ConPTY 创建失败），未重复桌面终端 smoke；以上深色证据来自真实控件的解析样式，不是终端截图。
同一环境直接启动 GDI 线程时，无基板会得到 `has_error=true`、原因“未找到非 DEBUG 基板定位标记”，线程保持运行并可正常停止。
以上 smoke 验证不带游戏画面，不能代替游戏内验收：第 6 步要求的“游戏内改变状态、TUI 随之变化”尚未执行。
