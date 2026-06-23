from __future__ import annotations

import time
from typing import Any

import numpy as np
from PySide6.QtCore import QThread, QTime, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QInputDialog, QMainWindow, QTabWidget

from ..capture import get_monitors
from ..keyboard import get_windows_by_title, send_hot_key
from ..pixelcalc.title_manager import get_default_title_manager
from ..rotation.base import BaseRotation
from ..rotation.hot_reload import HotReloadEvent, RotationHotReloadTracker
from ..workers import CaptureWorker, FrameDecodeWorker, RotationWorker
from .dialogs import TitleEditorDialog
from .tabs import AdvancedSettingsTab, DebugTab, HomeTab, OtherTab, PlayerAuraTab, PlayerStatusTab, PluginSpecTab, SpellTab, TargetStatusTab, TeammatesTab


class MainWindow(QMainWindow):
    """程序主窗口。"""

    request_worker_start = Signal(object, int)
    request_worker_stop = Signal()
    request_worker_fps = Signal(int)
    request_decode_frame = Signal(object, int)
    request_rotation_evaluate = Signal(object, int, object)

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Transcendental Entelechy Revelation Machine for Instinct Neural Awakening Link")
        self._setup_window_flags()
        self.setFixedSize(1600, 1200)

        self.is_running = False
        self.monitor_region: dict[str, int] | None = None
        self.selected_rotation_class: type[BaseRotation] | None = None
        self.selected_window_handle: int | None = None
        self.capture_success = False
        self.capture_error = '相机未启动'
        self.capture_frame: Any = None
        self.decoded_matrix: Any = None
        self.decoded_data: dict[str, Any] | None = None
        self.decode_state = 'idle'
        self.decode_error = '尚未解析'
        self.decode_result_is_stale = False
        self.fps = 20

        self._capture_worker: CaptureWorker | None = None
        self._capture_worker_thread: QThread | None = None
        self._decode_worker: FrameDecodeWorker | None = None
        self._decode_worker_thread: QThread | None = None
        self._rotation_worker: RotationWorker | None = None
        self._rotation_worker_thread: QThread | None = None
        self._capture_frame_id = 0
        self._decode_in_flight = False
        self._pending_decode_frame: Any = None
        self._pending_decode_frame_id = 0
        self._rotation_in_flight = False
        self._pending_rotation_data: dict[str, Any] | None = None
        self._pending_rotation_frame_id = 0
        self._last_invalid_reason_key: str | None = None
        self._last_action_signature: tuple[str, str] | None = None
        self._wait_until_monotonic = 0.0

        self.title_manager = get_default_title_manager()
        self.title_editor_dialog: TitleEditorDialog | None = None

        self.home_tab = HomeTab()
        self.player_aura_tab = PlayerAuraTab()
        self.player_status_tab = PlayerStatusTab()
        self.spell_tab = SpellTab()
        self.target_status_tab = TargetStatusTab()
        self.teammates_tab = TeammatesTab()
        self.plugin_spec_tab = PluginSpecTab()
        self.other_tab = OtherTab()
        self.advanced_settings_tab = AdvancedSettingsTab()
        self.debug_tab = DebugTab()
        self.advanced_settings_tab.set_title_manager(self.title_manager)
        self._rotation_hot_reload = RotationHotReloadTracker(self.home_tab.current_rotation_class())

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.home_tab, '首页')
        self.tab_widget.addTab(self.player_aura_tab, '玩家增益/减益')
        self.tab_widget.addTab(self.player_status_tab, '玩家状态')
        self.tab_widget.addTab(self.spell_tab, '技能')
        self.tab_widget.addTab(self.target_status_tab, '目标状态')
        self.tab_widget.addTab(self.teammates_tab, '队友')
        self.tab_widget.addTab(self.plugin_spec_tab, '插件/专精')
        self.tab_widget.addTab(self.other_tab, '其他')
        self.tab_widget.addTab(self.advanced_settings_tab, '高级设置')
        self.tab_widget.addTab(self.debug_tab, 'debug')
        self.setCentralWidget(self.tab_widget)

        self._ui_refresh_timer = QTimer(self)
        self._ui_refresh_timer.setInterval(300)
        self._ui_refresh_timer.timeout.connect(self._refresh_visible_data_tab)
        self._ui_refresh_timer.start()

        self._load_monitors_from_system()
        self._load_windows_from_system()
        self._connect_signals()
        self.home_tab.set_running_state(False)

    def _setup_window_flags(self) -> None:
        flags = (
            Qt.WindowType.Window
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)

    def _connect_signals(self) -> None:
        self.home_tab.start_clicked.connect(self._handle_start_requested)
        self.home_tab.stop_clicked.connect(self._handle_stop_requested)
        self.home_tab.monitor_changed.connect(self._handle_monitor_changed)
        self.home_tab.open_title_editor_clicked.connect(self._handle_open_title_editor_requested)
        self.home_tab.refresh_windows_clicked.connect(self._handle_refresh_windows_requested)
        self.home_tab.rotation_combo.currentIndexChanged.connect(self._handle_rotation_changed)
        self.advanced_settings_tab.fps_changed.connect(self._handle_fps_changed)
        self.tab_widget.currentChanged.connect(self._handle_tab_changed)

    def _load_monitors_from_system(self) -> None:
        monitor_list = get_monitors()
        monitors = monitor_list[1:] if monitor_list else []
        self.home_tab.set_monitors(monitors)
        self.monitor_region = self.home_tab.current_monitor_region()

    def _load_windows_from_system(self) -> None:
        previous_handle = self.home_tab.current_window_handle()
        windows = get_windows_by_title()
        self.home_tab.set_windows(windows)

        if previous_handle is None:
            return

        for index in range(self.home_tab.window_combo.count()):
            if self.home_tab.window_combo.itemData(index) == previous_handle:
                self.home_tab.window_combo.setCurrentIndex(index)
                return

    def _handle_monitor_changed(self, monitor_region: dict[str, int] | None) -> None:
        self.monitor_region = monitor_region

    def _handle_refresh_windows_requested(self) -> None:
        self._load_windows_from_system()

    def _handle_rotation_changed(self, index: int) -> None:
        del index
        self.selected_rotation_class = self.home_tab.current_rotation_class()
        self._rotation_hot_reload.set_rotation_class(self.selected_rotation_class)

    def _handle_open_title_editor_requested(self) -> None:
        if self.title_editor_dialog is None:
            self.title_editor_dialog = TitleEditorDialog(self.title_manager, self)
        self.title_editor_dialog.show()
        self.title_editor_dialog.raise_()
        self.title_editor_dialog.activateWindow()

    def _handle_start_requested(self) -> None:
        self.monitor_region = self.home_tab.current_monitor_region()
        self.selected_rotation_class = self.home_tab.current_rotation_class()
        self._rotation_hot_reload.set_rotation_class(self.selected_rotation_class)
        self.selected_window_handle = self.home_tab.current_window_handle()

        if self.monitor_region is None:
            self._append_log('当前没有可用显示器，无法启动截图。')
            return

        if self.selected_rotation_class is None:
            self._append_log('当前没有可用 rotation，无法启动 rotation。')
            return

        if self.selected_window_handle is None:
            self._append_log('当前没有可用游戏窗口，无法启动 rotation。')
            return

        self.is_running = True
        self.capture_success = False
        self.capture_error = '相机未启动'
        self.capture_frame = None
        self._capture_frame_id = 0
        self._reset_decode_state(clear_result=True)
        self._reset_decode_queue()
        self._reset_rotation_state()
        self.home_tab.set_running_state(True)
        self._refresh_visible_data_tab()
        self._append_log('收到启动请求。')
        self._start_worker_capture(self.monitor_region, self.fps)

    def _handle_stop_requested(self) -> None:
        self.is_running = False
        self.capture_success = False
        self.capture_error = '相机未启动'
        self.capture_frame = None
        self._capture_frame_id = 0
        self._reset_decode_state(clear_result=True)
        self._reset_decode_queue()
        self._reset_rotation_state()
        self.home_tab.set_running_state(False)
        self._refresh_visible_data_tab()
        self._append_log('收到停止请求。')
        self._stop_worker_capture()

    def _handle_fps_changed(self, value: int) -> None:
        self.fps = value
        if self.is_running:
            self._forward_fps_to_worker(value)

    def _handle_tab_changed(self, index: int) -> None:
        del index
        self._refresh_visible_data_tab()

    def _append_log(self, message: str) -> None:
        timestamp = QTime.currentTime().toString('HH:mm:ss.zzz')
        self.home_tab.append_log(f'{timestamp} {message}')

    def _log_rotation_hot_reload_event(self, event: HotReloadEvent) -> None:
        self._append_log(event.message)

    def _start_worker_capture(self, monitor_region: dict[str, int], fps: int) -> None:
        self._ensure_capture_worker_thread()
        self.request_worker_fps.emit(fps)
        self.request_worker_start.emit(monitor_region, fps)

    def _stop_worker_capture(self) -> None:
        if self._capture_worker_thread is None:
            return

        self.request_worker_stop.emit()

    def _forward_fps_to_worker(self, value: int) -> None:
        if self._capture_worker_thread is None:
            return

        self.request_worker_fps.emit(value)

    def _ensure_capture_worker_thread(self) -> None:
        if self._capture_worker_thread is not None:
            return

        self._capture_worker_thread = QThread(self)
        self._capture_worker = CaptureWorker()
        self._capture_worker.moveToThread(self._capture_worker_thread)

        self.request_worker_start.connect(self._capture_worker.start_capture)
        self.request_worker_stop.connect(self._capture_worker.stop_capture)
        self.request_worker_fps.connect(self._capture_worker.set_fps)

        self._capture_worker.log_message.connect(self._append_log)
        self._capture_worker.capture_started.connect(self._handle_capture_started)
        self._capture_worker.capture_ready.connect(self._handle_capture_ready)
        self._capture_worker.capture_failed.connect(self._handle_capture_failed)
        self._capture_worker.capture_stopped.connect(self._handle_capture_stopped)

        self._capture_worker_thread.finished.connect(self._capture_worker.deleteLater)
        self._capture_worker_thread.start()

    def _ensure_decode_worker_thread(self) -> None:
        if self._decode_worker_thread is not None:
            return

        self._decode_worker_thread = QThread(self)
        self._decode_worker = FrameDecodeWorker()
        self._decode_worker.moveToThread(self._decode_worker_thread)

        self.request_decode_frame.connect(self._decode_worker.submit_frame)

        self._decode_worker.frame_decoded.connect(self._handle_decode_succeeded)
        self._decode_worker.frame_invalid.connect(self._handle_decode_invalid_frame)
        self._decode_worker.frame_failed.connect(self._handle_decode_failed)

        self._decode_worker_thread.finished.connect(self._decode_worker.deleteLater)
        self._decode_worker_thread.start()

    def _ensure_rotation_worker_thread(self) -> None:
        if self._rotation_worker_thread is not None:
            return

        self._rotation_worker_thread = QThread(self)
        self._rotation_worker = RotationWorker()
        self._rotation_worker.moveToThread(self._rotation_worker_thread)

        self.request_rotation_evaluate.connect(self._rotation_worker.evaluate_rotation)

        self._rotation_worker.rotation_ready.connect(self._handle_rotation_ready)
        self._rotation_worker.rotation_failed.connect(self._handle_rotation_failed)

        self._rotation_worker_thread.finished.connect(self._rotation_worker.deleteLater)
        self._rotation_worker_thread.start()

    def _handle_capture_started(self, bounds: dict[str, int]) -> None:
        self._append_log(
            '找到截图区域: '
            f"left={bounds['left']} top={bounds['top']} right={bounds['right']} bottom={bounds['bottom']}"
        )

    def _handle_capture_ready(self, frame: Any) -> None:
        self.capture_frame = frame
        self.capture_success = True
        self.capture_error = ''
        self._capture_frame_id += 1
        self._submit_frame_to_decode_worker(frame, self._capture_frame_id)

    def _submit_frame_to_decode_worker(self, frame: Any, frame_id: int) -> None:
        if not self.is_running:
            return

        self._ensure_decode_worker_thread()
        if self._decode_in_flight:
            self._pending_decode_frame = frame
            self._pending_decode_frame_id = frame_id
            return

        self._decode_in_flight = True
        self.request_decode_frame.emit(frame, frame_id)

    def _submit_data_to_rotation_worker(self, data: dict[str, Any], frame_id: int) -> None:
        if not self.is_running or self.selected_rotation_class is None:
            return

        if self._wait_until_monotonic > time.monotonic():
            return

        runtime_rotation_class, reload_event = self._rotation_hot_reload.get_runtime_rotation_class()
        if reload_event is not None:
            self._log_rotation_hot_reload_event(reload_event)
        if runtime_rotation_class is None:
            return
        self.selected_rotation_class = runtime_rotation_class

        self._ensure_rotation_worker_thread()
        if self._rotation_in_flight:
            self._pending_rotation_data = data
            self._pending_rotation_frame_id = frame_id
            return

        self._rotation_in_flight = True
        self.request_rotation_evaluate.emit(data, frame_id, runtime_rotation_class)

    def _handle_capture_failed(self, reason: str) -> None:
        self.is_running = False
        self.capture_success = False
        self.capture_error = reason
        self.capture_frame = None
        self._capture_frame_id = 0
        self._reset_decode_state(clear_result=True)
        self._reset_decode_queue()
        self._reset_rotation_state()
        self.home_tab.set_running_state(False)
        self._refresh_visible_data_tab()
        self._append_log(reason)

    def _handle_capture_stopped(self) -> None:
        self._append_log('worker 已停止。')

    def _handle_decode_succeeded(self, frame_id: int, matrix: Any, data: dict[str, Any]) -> None:
        if not self.is_running:
            return

        pending_utf_title_record = data.pop('_pending_utf_title_record', None)
        if pending_utf_title_record is not None:
            self.title_manager.add_record(
                valid_array=np.array(pending_utf_title_record['valid_array'], dtype=np.uint8),
                title_type=str(pending_utf_title_record['title_type']),
                title=str(pending_utf_title_record['title']),
                hash=str(pending_utf_title_record['hash']),
            )
            if self.title_editor_dialog is not None:
                self.title_editor_dialog.refresh_database_tabs()
                self.title_editor_dialog.refresh_live_tabs(force=True)

        self.decoded_matrix = matrix
        self.decoded_data = data
        self.decode_state = 'success'
        self.decode_error = ''
        self.decode_result_is_stale = False
        self._last_invalid_reason_key = None
        self._submit_data_to_rotation_worker(data, frame_id)
        self._finish_decode_cycle()

    def _handle_decode_invalid_frame(self, frame_id: int, reason: str) -> None:
        if not self.is_running:
            return

        self.decode_state = 'invalid_frame'
        self.decode_error = reason
        self.decode_result_is_stale = True

        reason_key = self._normalize_invalid_reason(reason)
        if reason_key != self._last_invalid_reason_key:
            self._append_log(reason)
            self._last_invalid_reason_key = reason_key

        self._finish_decode_cycle()

    def _handle_decode_failed(self, frame_id: int, reason: str) -> None:
        if not self.is_running:
            return

        self.decode_state = 'error'
        self.decode_error = reason
        self.decode_result_is_stale = True
        self._last_invalid_reason_key = None
        self._append_log(reason)
        self._finish_decode_cycle()

    def _handle_rotation_ready(
        self,
        frame_id: int,
        action: str,
        macro_name: str | None,
        macro_key: str | None,
        wait_seconds: float,
        message: str,
    ) -> None:
        del frame_id
        if not self.is_running:
            return

        if action == 'cast':
            if macro_name is None:
                self._finish_rotation_cycle()
                return
            if macro_key is None:
                self._append_log(f'cast: {macro_name}，还没配置按键。')
                self._finish_rotation_cycle()
                return
            signature = ('cast', macro_name)
            if signature != self._last_action_signature:
                self._append_log(f'cast: {macro_name}')
                self._last_action_signature = signature
            if self.selected_window_handle is not None:
                send_hot_key(self.selected_window_handle, macro_key)
            self._finish_rotation_cycle()
            return

        if action == 'wait':
            self._wait_until_monotonic = time.monotonic() + wait_seconds
            self._append_log(f'wait {wait_seconds:.2f}s: {message}')
            self._last_action_signature = ('wait', message)
            self._finish_rotation_cycle()
            return

        signature = ('idle', message)
        if signature != self._last_action_signature:
            self._append_log(f'idle: {message}')
            self._last_action_signature = signature
        self._finish_rotation_cycle()

    def _handle_rotation_failed(self, frame_id: int, reason: str) -> None:
        del frame_id
        if not self.is_running:
            return

        self._append_log(reason)
        self._finish_rotation_cycle()

    def _finish_decode_cycle(self) -> None:
        if self._pending_decode_frame is None:
            self._decode_in_flight = False
            return

        next_frame = self._pending_decode_frame
        next_frame_id = self._pending_decode_frame_id
        self._pending_decode_frame = None
        self._pending_decode_frame_id = 0
        self.request_decode_frame.emit(next_frame, next_frame_id)

    def _finish_rotation_cycle(self) -> None:
        self._rotation_in_flight = False
        if self._pending_rotation_data is None:
            return

        next_data = self._pending_rotation_data
        next_frame_id = self._pending_rotation_frame_id
        self._pending_rotation_data = None
        self._pending_rotation_frame_id = 0
        self._submit_data_to_rotation_worker(next_data, next_frame_id)

    def _refresh_visible_data_tab(self) -> None:
        current_widget = self.tab_widget.currentWidget()
        refresh_method = getattr(current_widget, 'refresh_from_decode_snapshot', None)
        if callable(refresh_method):
            refresh_method(self._build_decode_snapshot())

    def _build_decode_snapshot(self) -> dict[str, Any]:
        return {
            'decoded_data': self.decoded_data,
            'decode_state': self.decode_state,
            'decode_error': self.decode_error,
            'decode_result_is_stale': self.decode_result_is_stale,
        }

    def _normalize_invalid_reason(self, reason: str) -> str:
        if ': ' in reason:
            return reason.split(': ', 1)[1].strip()
        if ':' in reason:
            return reason.split(':', 1)[1].strip()
        return reason.strip()

    def _reset_decode_state(self, clear_result: bool) -> None:
        if clear_result:
            self.decoded_matrix = None
            self.decoded_data = None
        self.decode_state = 'idle'
        self.decode_error = '尚未解析'
        self.decode_result_is_stale = False
        self._last_invalid_reason_key = None

    def _reset_decode_queue(self) -> None:
        self._decode_in_flight = False
        self._pending_decode_frame = None
        self._pending_decode_frame_id = 0

    def _reset_rotation_state(self) -> None:
        self._rotation_in_flight = False
        self._pending_rotation_data = None
        self._pending_rotation_frame_id = 0
        self._wait_until_monotonic = 0.0
        self._last_action_signature = None

    def _shutdown_capture_worker_thread(self) -> None:
        if self._capture_worker_thread is None:
            return

        self.request_worker_stop.emit()
        self._capture_worker_thread.quit()
        self._capture_worker_thread.wait(2000)
        self._capture_worker_thread = None
        self._capture_worker = None

    def _shutdown_decode_worker_thread(self) -> None:
        if self._decode_worker_thread is None:
            return

        self._decode_worker_thread.quit()
        self._decode_worker_thread.wait(2000)
        self._decode_worker_thread = None
        self._decode_worker = None
        self._reset_decode_queue()

    def _shutdown_rotation_worker_thread(self) -> None:
        if self._rotation_worker_thread is None:
            return

        self._rotation_worker_thread.quit()
        self._rotation_worker_thread.wait(2000)
        self._rotation_worker_thread = None
        self._rotation_worker = None
        self._reset_rotation_state()

    def _shutdown_worker_thread(self) -> None:
        self._shutdown_capture_worker_thread()
        self._shutdown_decode_worker_thread()
        self._shutdown_rotation_worker_thread()

    def closeEvent(self, event: QCloseEvent) -> None:
        text, ok = QInputDialog.getText(self, '确认关闭', '输入 exit 以关闭程序: ')
        if not ok or text != 'exit':
            event.ignore()
            return

        if self.title_editor_dialog is not None:
            self.title_editor_dialog.close()
        self._shutdown_worker_thread()
        event.accept()
