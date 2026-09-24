# 截图插件开发

## 入口与职责

版本目录内 `capture.py` 必须导出 `Plugin` 类；可用 `Plugin = GDIWorker` 这样的别名公开具体类。
构造接受 `fps=15`，不得在构造或模块导入时启动线程、占用桌面采集资源；加载器会在进入 UI 前检查签名、未启动状态和初始结果。

当前 `gdi@dev` 使用 `ctypes.WinDLL` 声明 Windows 函数签名，通过核心截图注册器接入；独立后端和 demo 已存在。

返回实例遵循 [截图 worker 契约](captures.md#截图-worker-契约)，包括只读 `is_running`、`start()`、`stop()`、`set_fps(fps=15)` 和 `get_latest_result()`。
方法名相同不等于业务契约满足，仍需生命周期和图像测试。

持续运行额外依赖 CaptureResult.sequence：每次发布递增的正整数，快照复制保留序号，不能用图像 hash 代替新帧身份。None 只适用于初始空结果、独立解码或旧离线用例；带图但无序号无法进入持续执行。ThreadCaptureWorker 自动维护序号，后端不重复实现。

可组合 `phantom.core.capture.worker.ThreadCaptureWorker`：版本内后端实现 `CaptureBackend` 的 `desktop_bounds()`、`capture(bounds)`、`close()`，公共 worker 负责定位、校验、FPS、最新结果与停止。
后端在采集线程内创建及关闭；释放资源后恢复该线程的 DPI 上下文。不要复制公共线程或定位算法到插件。

## 配置接入

应用通过 `capture.plugin` 选择精确版本，省略时默认 `gdi@dev`；加载入口为 `phantom.core.capture.registry.Registry.create(identifier, fps=...)`。
现有配置只读，修改后重启程序生效。不存在的版本或损坏插件明确失败，不换用 GDI。
独立 demo 显式指定 GDI 并使用同一注册器，不读取应用配置。

## Python 说明与验收

文件头及关键步骤应解释平台限制、坐标系、通道转换、缓冲区所有权、资源申请释放和失败结果。
GDI 尤其应说明负坐标虚拟桌面、位图选择/恢复、自顶向下读取、BGRA 到 RGB 转换。

使用合成图像验证定位和裁剪，使用真实 worker 验证启停、重启、错误和最新结果所有权。
注册器测试覆盖默认/显式精确版本、缺失文件、导入错误、非 Plugin 类与接口不完整；Windows smoke 单独验证真实后端调用。
当前只有 GDI 真实后端且不提供运行期切换；新增其他后端必须属于用户请求范围。

## 截图 worker 契约

- worker 提供只读 `is_running: bool`，构造后未运行；初始快照为 `CaptureResult()`。
- worker 实例化接受 `fps=15`，提供 `start()`、`stop()`、`set_fps(fps=15)`、`get_latest_result()`。
- FPS 必须为有限正数，允许运行中修改；GDI 实际应用上限，其他未来后端保留接口但可以不生效。
- 重复 `start()` 不创建重复线程；`stop()` 唤醒等待并等待资源释放，重复停止无副作用。重新启动清除旧结果并重新定位。
- `CaptureResult` 包含 `image`、`status` 和 `sequence`。图像为独立连续的 RGB `uint8` NumPy 数组，形状 `(height,width,3)`；未定位或底层截图失败时为 `None`。
- 状态固定为 `has_error: bool` 和 `description: str`。有效帧为 `false`、空描述；未定位、多候选、校验失败及底层错误均为 `true`，描述具体原因。
- 尚未启动的空结果为非错误；主动停止不改写最后采集结果。无效区域仍附图，不能作为有效业务输入。
- 主线程取得最新结果的独立快照，不积压历史帧，不共享可被后续截图改写的缓冲区。
- `sequence: int | None` 默认 None，表示尚无帧身份；纯解码及独立 demo 可使用无序号结果。持续执行要求有效图像带正整数序号，每次发布递增，重复读取保持原值；内容相同的新截图也递增。公共 worker 计数跨重启延续，初始空结果仍为 None。缺失、非法或倒退序号使执行暂停，不猜测图像是否为新帧。

GDI worker 搜索整个虚拟桌面，包含负坐标显示器，按物理像素坐标截图。定位成功后仅截取完整基板区域。
角标或尺寸失效时下一轮重新全屏搜索；角标有效但校验色错误时保持局部截图。定位与校验规则见像素协议。
搜索和区域截图均受 FPS 上限约束，处理耗时计入周期，不补跑积压帧；停止和 FPS 更新可以唤醒等待。
底层截图异常发布错误并结束本次运行、释放资源，后续可显式重新启动。

独立 `demo/demo.py` 先打印演示内容，等待 3 秒后开始，采集 5 秒后停止，保存最后结果。每次运行在项目根目录的 `demo/demo_results/` 下创建新目录，
有图时保存 `result.npy`（不使用 pickle），始终保存 UTF-8 `result.txt`，内容为两个状态字段的 JSON 对象。
无图时不生成 NPY，不退回保存历史有效帧；结果目录由 Git 忽略。

## 截图加载与配置

`phantom/core/capture/` 提供 contracts、worker、imaging 与 registry；`phantom/captures/` 只保存版本插件。
`Registry.create(identifier="gdi@dev", fps=15)` 返回 CaptureWorker，每次构造独立实例。标识精确匹配、源码限定在版本目录。
配置字段见 [TUI 应用配置](../../phantom-code-dev/references/tui.md#应用配置)。非法选择、导入失败或不满足调用接口抛出带标识的 CapturePluginError，入口在进入 UI 前报告并非零退出。
缺省配置采用 GDI；显式配置错误不回退。不提供热切换或热加载。
