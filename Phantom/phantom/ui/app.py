"""
Summary:
    承载 Phantom 采集、多份 rotation 生成与同帧路由状态展示的 Textual 界面。
Description:
    content 展示五个标签页，底部 footer 只包含一行状态。
    游戏检测通过消息交付，采集读取最新快照；停止和退出等待后台资源释放。
    生成在独立 Worker 中执行，条件表格仅展示同一有效帧的匹配职业专精数据。
Key Variables:
    PhantomApp.collecting: 程序采集开关，独立于 Lua ENABLE。
    PhantomApp.stopping: 后台正在释放截图资源，期间禁止再次启动。
    PhantomApp.business_log: 主动业务日志入口，与 Textual 诊断日志分离。
Change Log:
    2026-09-19: Changed 启动加载职业专精集合，生成复用内存配置，底栏与条件表跟随同帧匹配项。
    2026-09-14: Changed 接入后台新帧运行器及键盘停止清理，展示实际同帧决策。
    2026-09-13: Fixed 在 Textual 停止消息循环后拒绝采集刷新，避免访问已卸载控件。
    2026-09-13: Changed 将同帧决策与宏名称日志整合进启动后的采集流程。
    2026-09-12: Added 第 5、6 步 Textual 界面与采集展示生命周期。
    2026-09-12: Changed 接入第 7–10 步单份 rotation 与八个条件实例。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from threading import Event
from typing import ClassVar

from rich.text import Text
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.geometry import Size
from textual.message import Message
from textual.widgets import Button, DataTable, Label, Log, Static, TabbedContent, TabPane

from phantom.core.capture.contracts import CaptureWorker
from phantom.core.capture.registry import Registry as CaptureRegistry
from phantom.core.configuration import AppConfig
from phantom.core.game import GameMonitor, GameStatus, detect_game
from phantom.core.generator import RotationGenerationResult, generate_rotations
from phantom.core.keyboard.contracts import Keyboard
from phantom.core.keyboard.registry import Registry as KeyboardRegistry
from phantom.core.pixels import PixelDecoder
from phantom.core.rotation import Decision, Rotation
from phantom.core.rotation_catalog import load_rotations
from phantom.core.runtime import RotationRuntime, decode_specialization
from phantom.ui.business_log import BusinessLog
from phantom.ui.capture import GENERAL_FIELDS, GeneralData, decode_general
from phantom.ui.theme import FLEXOKI, PHANTOM_THEME


class GameUpdated(Message):
    def __init__(self, status: GameStatus) -> None:
        super().__init__()
        self.status: GameStatus = status


class BusinessLogLine(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text: str = text


class CaptureStopped(Message):
    def __init__(self, error: str = "") -> None:
        super().__init__()
        self.error: str = error


class GenerationFinished(Message):
    def __init__(self, result: RotationGenerationResult | None, error: str = "") -> None:
        super().__init__()
        self.result: RotationGenerationResult | None = result
        self.error: str = error


class PageTabs(TabbedContent):
    def on_tab_pane_focused(self, event: TabPane.Focused) -> None:
        # 切页由 Tab/鼠标明确控制；延迟到达的旧页面焦点事件不能把新页面切回去。
        event.prevent_default()
        event.stop()


class PhantomApp(App[None]):
    CSS_PATH = "app.tcss"
    TITLE = "Phantom"
    AUTO_FOCUS = None
    ENABLE_COMMAND_PALETTE = False
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("tab", "switch_tab(1)", "下一页", show=False, priority=True),
        Binding("shift+tab", "switch_tab(-1)", "上一页", show=False, priority=True),
        Binding("up", "move_button(-1)", "上一个按钮", show=False, priority=True),
        Binding("down", "move_button(1)", "下一个按钮", show=False, priority=True),
        Binding("space", "press_button", "执行", show=False),
        Binding("ctrl+q", "quit", "退出", show=False, priority=True),
    ]
    TAB_IDS: ClassVar[tuple[str, ...]] = ("overview", "general", "logs", "macros", "conditions")

    def __init__(self, config: AppConfig, capture: CaptureWorker | None = None, game_detector: Callable[[], GameStatus] = detect_game, keyboard: Keyboard | None = None) -> None:
        super().__init__()
        self.config: AppConfig = config
        self.keyboard: Keyboard = keyboard if keyboard is not None else KeyboardRegistry().create(config.keyboard_plugin)
        self.runtime: RotationRuntime | None = None
        self.decision: Decision | None = None
        self._decision_log: str = ""
        self.rotation: Rotation | None = None
        self.rotation_state: str = "尚未识别"
        self.rotation_error: str = ""
        loaded = load_rotations(config)
        self.rotations: tuple[Rotation, ...] = loaded.rotations
        self.rotation_warnings: tuple[str, ...] = loaded.warnings
        self.generating: bool = False
        self._generation_done: Event = Event()
        self._generation_done.set()
        self.capture: CaptureWorker = capture if capture is not None else CaptureRegistry().create(config.capture_plugin, fps=config.fps)
        self.game_status: GameStatus = GameStatus(description="正在检测游戏")
        self.collecting: bool = False
        self.stopping: bool = False
        self.closing: bool = False
        self.capture_state: str = "已暂停"
        self.capture_error: str = ""
        self.general_data: GeneralData | None = None
        self._mounted_ui: bool = False
        self._small: bool = False
        self.business_log: BusinessLog = BusinessLog(self._publish_log)
        self.game_monitor: GameMonitor = GameMonitor(self._publish_game, game_detector)
        self.register_theme(PHANTOM_THEME)
        self.theme = PHANTOM_THEME.name
        self.animation_level = "none"

    def _publish_game(self, status: GameStatus) -> None:
        self.post_message(GameUpdated(status))

    def _publish_log(self, text: str) -> None:
        self.post_message(BusinessLogLine(text))

    def compose(self) -> ComposeResult:
        with Vertical(id="content"):
            yield Static("", id="size_notice", markup=False)
            with PageTabs(initial="overview", id="pages"):
                with TabPane("综合", id="overview"):
                    with Horizontal(id="overview_columns"):
                        with VerticalScroll(id="controls"):
                            yield Label("操作", classes="section_title")
                            yield Button("启动", id="start", disabled=True)
                            yield Button("关闭", id="stop", disabled=True)
                            yield Button("生成插件", id="generate", disabled=True)
                            yield Static("", id="generation_hint", classes="muted", markup=False)
                            yield Static("Tab / Shift+Tab  切换页面\n↑ / ↓  选择按钮\nEnter / Space  执行\nCtrl+Q  退出", id="keyboard_help")
                        with VerticalScroll(id="work_status"):
                            yield Label("当前工作状态", classes="section_title")
                            for name, title in (("program_state", "程序"), ("game_state", "游戏"), ("capture_state", "采集"), ("board_size", "画布尺寸"), ("capture_fps", "配置 FPS"), ("current_error", "当前问题")):
                                yield Label(title, classes="state_label")
                                yield Static("—", id=name, classes="state_value", markup=False)
                with TabPane("通用条件", id="general"):
                    yield Static("第一行通用 Cell · 原始采集值", classes="section_title")
                    yield DataTable[str](id="general_table", cursor_type="row", zebra_stripes=True)
                with TabPane("日志", id="logs"):
                    yield Log(id="business_log", max_lines=self.config.log_max_lines)
                with TabPane("宏绑定", id="macros"):
                    yield Static("宏绑定展示尚未实现", classes="placeholder")
                with TabPane("循环条件", id="conditions"):
                    yield Static("", id="rotation_title", markup=False)
                    yield Static("决策：—", id="decision", markup=False)
                    yield DataTable[str](id="condition_table", cursor_type="row", zebra_stripes=True)
        with Container(id="footer"):
            yield Static("", id="status_line")

    def on_mount(self) -> None:
        for button in self.query(Button):
            button.active_effect_duration = 0
        table = self.query_one("#general_table", DataTable)
        for title, key, width in (("项目", "name", 22), ("RGB", "rgb", 22), ("亮度值", "mean", 16), ("显示值", "display", 26)):
            table.add_column(title, key=key, width=width)
        for index, name in enumerate(GENERAL_FIELDS):
            table.add_row(name, "—", "—", "", key=str(index))
        condition_table = self.query_one("#condition_table", DataTable)
        for title, key in (("条件名称", "name"), ("插件名称", "plugin"), ("返回值", "value")):
            condition_table.add_column(title, key=key)
        self._populate_conditions()
        self._mounted_ui = True
        self._resize_content()
        self._refresh_status()
        self.game_monitor.start()
        self.set_interval(1 / self.config.fps, self.refresh_capture)
        self.business_log.log("程序已暂停")
        for warning in self.rotation_warnings:
            self.business_log.log(warning)
        self.business_log.log(f"已加载 {len(self.rotations)} 份 rotation；修改配置后需重启")

    def on_resize(self, event: events.Resize) -> None:
        if self._mounted_ui:
            self._resize_content(event.size)

    def _resize_content(self, size: Size | None = None) -> None:
        viewport = self.size if size is None else size
        was_small = self._small
        self._small = viewport.width < self.config.min_width or viewport.height < self.config.min_height
        self.query_one("#size_notice", Static).update(f"终端尺寸不足：当前 {viewport.width}×{viewport.height}\n请调整至至少 {self.config.min_width}×{self.config.min_height}\nCtrl+Q 退出")
        self.query_one("#size_notice").display = self._small
        self.query_one("#pages").display = not self._small
        if not self._small and (was_small or self.focused is None):
            self.call_after_refresh(self._focus_page)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in ("move_button", "press_button"):
            return self._mounted_ui and not self._small and self.query_one("#pages", TabbedContent).active == "overview"
        if action == "switch_tab":
            return self._mounted_ui and not self._small
        return True

    def action_switch_tab(self, direction: int) -> None:
        pages = self.query_one("#pages", TabbedContent)
        index = self.TAB_IDS.index(pages.active)
        pages.active = self.TAB_IDS[(index + direction) % len(self.TAB_IDS)]

    @on(TabbedContent.TabActivated)
    def tab_activated(self) -> None:
        if self._mounted_ui and not self._small:
            self.call_after_refresh(self._focus_page)

    def _focus_page(self) -> None:
        if self._small or self.closing:
            return
        active = self.query_one("#pages", TabbedContent).active
        if active == "overview":
            self.action_move_button(1)
        elif active == "general":
            self.query_one("#general_table", DataTable).focus()
        elif active == "logs":
            self.query_one("#business_log", Log).focus()
        elif active == "conditions":
            self.query_one("#condition_table", DataTable).focus()

    def action_move_button(self, direction: int) -> None:
        buttons = [button for button in self.query("#controls Button") if not button.disabled]
        if not buttons:
            return
        if self.focused in buttons:
            index = buttons.index(self.focused)
            buttons[(index + direction) % len(buttons)].focus()
        else:
            buttons[0 if direction > 0 else -1].focus()

    def action_press_button(self) -> None:
        if isinstance(self.focused, Button):
            self.focused.press()

    @on(Button.Pressed, "#start")
    def start_collection(self) -> None:
        if self.collecting or self.stopping or self.closing or self.generating or not self.game_status.running:
            return
        self.runtime = None
        self._select_rotation(None)
        self.collecting = True
        try:
            self.capture.start()
            if self.rotations:
                self.runtime = RotationRuntime(self.capture, self.keyboard, self.rotations, self.config.fps)
                self.runtime.start()
        except Exception as error:
            self._request_stop(f"启动失败：{error}")
            return
        self._set_capture_state("等待截图")
        self.business_log.log("程序已启动")
        self._refresh_status()
        if not self._small:
            self.query_one("#stop", Button).focus()

    @on(Button.Pressed, "#stop")
    def stop_collection(self) -> None:
        self._request_stop()

    def _decision_text(self, decision: Decision) -> str:
        action = f"宏：{decision.macro.name} · 键位：{decision.macro.key}" if decision.macro is not None else "Idle · 无动作"
        return f"第 {decision.rule_index} 条 · {decision.rule.condition or '兜底'} · {decision.rule.annotate} · {action}"

    def _show_decision(self, decision: Decision | None) -> None:
        self.decision = decision
        self.query_one("#decision", Static).update("决策：" + (self._decision_text(decision) if decision else "—"))
        message = f"已派发宏：{decision.macro.name}" if decision and decision.macro else "Idle：无动作" if decision else ""
        if message and message != self._decision_log:
            self.business_log.log(message)
        self._decision_log = message

    def _populate_conditions(self) -> None:
        self._show_decision(None)
        self.query_one("#rotation_title", Static).update(f"当前 rotation：{self.rotation.profile.title}" if self.rotation else f"当前 rotation：{self.rotation_state}（已加载 {len(self.rotations)} 份）")
        table = self.query_one("#condition_table", DataTable)
        table.clear()
        if self.rotation is not None:
            for index, entry in enumerate(self.rotation.conditions):
                table.add_row(entry.title, entry.plugin, "—", key=str(index))

    def _select_rotation(self, rotation: Rotation | None, state: str = "尚未识别") -> None:
        changed = self.rotation is not rotation or self.rotation_state != state
        self.rotation = rotation
        self.rotation_state = state
        if changed:
            self._populate_conditions()

    def _clear_conditions(self) -> None:
        self._show_decision(None)
        if self.rotation is not None:
            table = self.query_one("#condition_table", DataTable)
            for index in range(len(self.rotation.conditions)):
                table.update_cell(str(index), "value", "—")

    @on(Button.Pressed, "#generate")
    def generate_addon(self) -> None:
        if self.collecting or self.stopping or self.closing or self.generating or not self.rotations or self.config.wow_executable is None:
            return
        self.generating = True
        self._generation_done.clear()
        self._refresh_status()
        self._generate_addon()

    @work(thread=True, group="addon-generation")
    def _generate_addon(self) -> None:
        result = None
        error = ""
        try:
            assert self.config.wow_executable is not None
            result = generate_rotations(self.rotations, self.config.wow_executable, self.config.addon_name)
        except Exception as exception:
            error = f"生成插件失败：{exception}"
        finally:
            self._generation_done.set()
        self.post_message(GenerationFinished(result, error))

    def on_generation_finished(self, message: GenerationFinished) -> None:
        self.generating = False
        self._generation_done.set()
        if self.closing:
            return
        self.rotation_error = message.error
        if message.result is not None:
            self.business_log.log(f"插件已生成：{message.result.directory}（{len(message.result.rotations)} 份 rotation），请在游戏内 /reload")
        else:
            # 集合生成不重读或改写 rotation，生成失败不会使本次启动的内存布局失效。
            self.business_log.log(message.error)
        self._populate_conditions()
        self._refresh_status()

    def _request_stop(self, error: str = "") -> None:
        if not self.collecting:
            return
        self.collecting = False
        self.stopping = True
        if self.runtime is not None:
            self.runtime.request_stop()
        if error:
            # 仅用户正常暂停保留名称；致命停止不能把失效截图的身份继续当作当前项。
            self._select_rotation(None)
        self._show_data(None)
        self._set_capture_state("采集失败" if error else "已暂停", error)
        self.business_log.log("程序已暂停")
        self._refresh_status()
        self._stop_capture()

    @work(thread=True, group="capture-stop")
    def _stop_capture(self) -> None:
        error = ""
        try:
            if self.runtime is not None:
                self.runtime.stop()
                result = self.runtime.get_latest_result()
                if result.fatal:
                    error = result.error
        except Exception as exception:
            error = f"停止采集失败：{exception}"
        finally:
            try:
                self.capture.stop()
            except Exception as exception:
                error += f" 停止采集失败：{exception}"
        self.post_message(CaptureStopped(error))

    def on_capture_stopped(self, message: CaptureStopped) -> None:
        if self.closing:
            return
        self.stopping = False
        if message.error:
            self._set_capture_state("采集失败", message.error)
        self._refresh_status()
        if not self._small and self.query_one("#pages", TabbedContent).active == "overview":
            self._focus_page()

    def on_game_updated(self, message: GameUpdated) -> None:
        if self.closing or message.status == self.game_status:
            return
        self.game_status = message.status
        state = "已启动" if message.status.running else "未启动"
        self.business_log.log(f"游戏{state}" + (f"：{message.status.description}" if message.status.description else ""))
        if not message.status.running:
            self._request_stop()
            self._select_rotation(None)
        self._refresh_status()
        if self.focused is None and not self._small:
            self.call_after_refresh(self._focus_page)

    def on_business_log_line(self, message: BusinessLogLine) -> None:
        if not self.closing:
            self.query_one("#business_log", Log).write_lines(message.text.splitlines())

    def refresh_capture(self) -> None:
        # Textual 先停止消息循环并卸载控件，之后才调用应用的 on_unmount。
        if not self.is_running or not self.collecting or self.closing:
            return
        # 先检查存活，再取结果，保证线程结束时能读取它发布的最后错误。
        running = self.capture.is_running
        snapshot = self.runtime.get_latest_result() if self.runtime is not None else None
        if snapshot is not None and snapshot.fatal:
            self._request_stop(snapshot.error)
            return
        result = snapshot.capture if snapshot is not None else self.capture.get_latest_result()
        if not running:
            self._request_stop(result.status.description or "截图线程已结束")
            return
        if result.status.has_error:
            self._select_rotation(None)
            self._show_data(None)
            self._set_capture_state("采集失败", result.status.description)
        elif result.image is None:
            self._select_rotation(None)
            self._show_data(None)
            self._set_capture_state("等待截图")
        else:
            try:
                data = decode_general(result)
            except (ValueError, TypeError, IndexError) as error:
                self._select_rotation(None)
                self._show_data(None)
                self._set_capture_state("解析失败", f"通用数据解析失败：{error}")
            else:
                self._show_data(data)
                condition_error = ""
                if snapshot is not None:
                    self._select_rotation(snapshot.rotation, "无匹配" if snapshot.specialization is not None and snapshot.rotation is None else "尚未识别")
                    if snapshot.error:
                        self._clear_conditions()
                        condition_error = snapshot.error
                    elif snapshot.decision is not None:
                        decision = snapshot.decision
                        table = self.query_one("#condition_table", DataTable)
                        self._show_decision(decision)
                        for index, value in enumerate(decision.values):
                            table.update_cell(str(index), "value", str(value), update_width=True)
                else:
                    # 没有加载项时保留基础采集，只识别路由状态，不在界面中求值。
                    try:
                        decode_specialization(PixelDecoder(result.image))
                    except (ValueError, IndexError):
                        self._select_rotation(None)
                    else:
                        self._select_rotation(None, "无匹配")
                self._set_capture_state("条件不可用" if condition_error else "采集正常", condition_error)
        self._refresh_status()

    def _set_capture_state(self, state: str, error: str = "") -> None:
        previous_error = self.capture_error
        if error and error != previous_error:
            self.business_log.log(error)
        elif state == "采集正常" and previous_error:
            self.business_log.log("采集已恢复")
        self.capture_state = state
        self.capture_error = error

    def _show_data(self, data: GeneralData | None) -> None:
        if data is None:
            self._clear_conditions()
        if data == self.general_data:
            return
        self.general_data = data
        table = self.query_one("#general_table", DataTable)
        for index in range(len(GENERAL_FIELDS)):
            rgb, mean = data.cells[index] if data is not None else ("—", "—")
            table.update_cell(str(index), "rgb", rgb)
            table.update_cell(str(index), "mean", mean)

    def _refresh_status(self) -> None:
        if not self._mounted_ui or self.closing:
            return
        program = "已启动" if self.collecting else "已暂停"
        game = "已启动" if self.game_status.running else "未启动"
        status = Text(no_wrap=True, overflow="ellipsis")
        status.append(f"程序：{program}", style=FLEXOKI["green" if self.collecting else "subtext_1"])
        status.append(" · ", style=FLEXOKI["text"])
        status.append(f"游戏：{game}", style=FLEXOKI["green" if self.game_status.running else "subtext_1"])
        status.append(" · rotation：", style=FLEXOKI["text"])
        status.append(self.rotation.profile.title if self.rotation is not None else self.rotation_state, style=FLEXOKI["text" if self.rotation is not None else "subtext_1"])
        self.query_one("#status_line", Static).update(status)
        values = {
            "program_state": "正在停止" if self.stopping else program,
            "game_state": game,
            "capture_state": self.capture_state,
            "board_size": (f"{self.general_data.width} × {self.general_data.height} px" if self.general_data is not None else "—"),
            "capture_fps": f"{self.config.fps:g}",
            "current_error": self.rotation_error or self.capture_error or self.game_status.description or "无",
        }
        for identifier, value in values.items():
            self.query_one(f"#{identifier}", Static).update(value)
        self.query_one("#start", Button).disabled = self.collecting or self.stopping or self.closing or self.generating or not self.game_status.running
        self.query_one("#stop", Button).disabled = not self.collecting or self.closing
        missing = ""
        if not self.rotations:
            missing = "没有可用 rotation，请配置 [rotations] 或添加 rotations/*.toml 后重启"
        elif self.config.wow_executable is None:
            missing = "请配置 wow.executable"
        self.query_one("#generate", Button).disabled = bool(missing) or (self.collecting or self.stopping or self.closing or self.generating)
        self.query_one("#generation_hint", Static).update("正在生成插件…" if self.generating else missing or f"插件：{self.config.addon_name}")

    def close_resources(self) -> None:
        if self.runtime is not None:
            self.runtime.request_stop()
        try:
            self.game_monitor.stop()
        finally:
            try:
                if self.runtime is not None:
                    self.runtime.stop()
                else:
                    self.keyboard.close()
            finally:
                self.capture.stop()

    async def action_quit(self) -> None:
        if self.closing:
            return
        self.closing = True
        if self.runtime is not None:
            self.runtime.request_stop()
        self.collecting = False
        self._show_data(None)
        self._refresh_status()
        self._finish_exit()

    @work
    async def _finish_exit(self) -> None:
        await asyncio.to_thread(self._generation_done.wait)
        await asyncio.to_thread(self.close_resources)
        self.exit()

    async def on_unmount(self) -> None:
        self._mounted_ui = False
        self.closing = True
        self.collecting = False
        if self.runtime is not None:
            self.runtime.request_stop()
        await asyncio.to_thread(self._generation_done.wait)
        await asyncio.to_thread(self.close_resources)
