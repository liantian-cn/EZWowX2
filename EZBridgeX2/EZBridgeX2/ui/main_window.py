import datetime
import re
import sys
import threading
import traceback
from pathlib import Path
from copy import deepcopy
from typing import Any, Protocol, TextIO, cast
import dxcam
import numpy as np
from PySide6.QtCore import Qt, QUrl, Signal, QObject
from PySide6.QtGui import QClipboard, QDesktopServices, QIcon, QIntValidator
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QInputDialog, QTabWidget, QTextEdit, QVBoxLayout, QWidget
from ..core.database import IconTitleRepository
from ..core.node import GridCell, GridDecoder
from ..core.node_extractor_data import extract_all_data
from ..utils.image_utils import find_template_bounds
from ..utils.img_mark import MARK8_TEMPLATE
from ..workers import CameraWorker, InfoDisplayWorker, WebServerWorker
from .info_display_tab import InfoDisplayTab
from .icon_library import IconLibraryDialog


class _DxCameraLike(Protocol):
    def grab(self) -> np.ndarray | None:
        ...

    def stop(self) -> None:
        ...

    def release(self) -> None:
        ...


class LogEmitter(QObject):
    log_signal = Signal(str)

    def __init__(self, log_display: QTextEdit) -> None:
        super().__init__()
        self.log_display: QTextEdit = log_display
        self.log_signal.connect(self._append_log)

    def _append_log(self, text: str) -> None:
        self.log_display.append(text)

    def emit_log(self, text: str) -> None:
        self.log_signal.emit(text)


class LogRedirector:

    def __init__(self, log_emitter: LogEmitter) -> None:
        self.log_emitter: LogEmitter = log_emitter
        self.original_stdout: TextIO = sys.stdout

    def write(self, text: str) -> None:
        self.original_stdout.write(text)
        if text.strip():
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_text: str = f'[{timestamp}] {text.rstrip()}'
            self.log_emitter.emit_log(formatted_text)

    def flush(self) -> None:
        self.original_stdout.flush()


class MainWindow(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self._pixel_dump_lock = threading.Lock()
        self.pixel_dump: dict[str, Any] = {'error': '相机尚未启动'}
        self.setWindowTitle('EZBridgeX2')
        self._setup_window_icon()
        self._setup_window_flags()
        screen = QApplication.primaryScreen()  # pyright: ignore[reportReturnType] - may be None on headless
        if screen is None:  # type: ignore[redundant-expr]  # Qt stubs say non-None, but headless can return None
            raise RuntimeError('无法获取主屏幕信息，请确保系统有可用的显示器')
        screen_geometry = screen.availableGeometry()
        width: int = int(screen_geometry.width() * 0.8)
        height: int = int(screen_geometry.height() * 0.8)
        self.resize(width, height)
        x: int = (screen_geometry.width() - width) // 2
        y: int = (screen_geometry.height() - height) // 2
        self.move(x, y)
        self.setFixedHeight(height)
        self.camera: _DxCameraLike | None = None
        self.camera_worker: CameraWorker | None = None
        self.camera_running: bool = False
        self.current_fps: int = 10
        self.device_idx: int = 0
        self.output_idx: int = 0
        self.monitor_list: list[tuple[int, int, str]] = []
        self.title_repository: IconTitleRepository = IconTitleRepository()
        GridCell.set_title_repository(self.title_repository)
        self.web_server: WebServerWorker | None = None
        self.info_display_worker: InfoDisplayWorker | None = None
        self.icon_library_dialog: IconLibraryDialog | None = None
        self.init_ui()
        self._start_info_display_worker()
        self._start_web_server()
        self.refresh_device_info()

    def _setup_window_flags(self) -> None:
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

    def _setup_window_icon(self) -> None:
        icon_path: Path = Path(__file__).resolve().parents[1] / 'icon.ico'
        self.setWindowIcon(QIcon(str(icon_path)))

    def _start_web_server(self) -> None:
        self.web_server = WebServerWorker(self._get_pixel_dump)
        self.web_server.start()

    def _start_info_display_worker(self) -> None:
        self.info_display_worker = InfoDisplayWorker(self._get_pixel_dump, interval_ms=200)
        self.info_display_worker.data_signal.connect(self.info_display_tab.update_from_pixel_dump)
        self.info_display_worker.start()

    def _get_pixel_dump(self) -> dict[str, Any]:
        with self._pixel_dump_lock:
            return deepcopy(self.pixel_dump)

    def _set_pixel_dump(self, value: dict[str, Any]) -> None:
        with self._pixel_dump_lock:
            self.pixel_dump = value

    def init_ui(self) -> None:
        main_layout: QVBoxLayout = QVBoxLayout()
        self.create_control_layout()
        main_layout.addLayout(self.l1_layout)
        self.create_display_layout()
        main_layout.addLayout(self.l2_layout)
        self.setLayout(main_layout)

    def create_control_layout(self) -> None:
        self.l1_layout: QHBoxLayout = QHBoxLayout()
        self.l1_left_layout: QHBoxLayout = QHBoxLayout()
        self.api_label: QLabel = QLabel('API地址：')
        self.api_url_input: QLineEdit = QLineEdit()
        self.api_url_input.setText('http://127.0.0.1:65131')
        self.api_url_input.setReadOnly(True)
        self.api_url_input.setFixedWidth(180)
        self.api_url_input.selectionChanged.connect(self._on_api_url_selected)
        self.api_visit_button: QPushButton = QPushButton('访问API')
        self.api_visit_button.clicked.connect(self._on_visit_api_clicked)
        self.l1_left_layout.addWidget(self.api_label)
        self.l1_left_layout.addWidget(self.api_url_input)
        self.l1_left_layout.addWidget(self.api_visit_button)
        self.l1_left_layout.addSpacing(20)
        self.monitor_label: QLabel = QLabel('选择显示器：')
        self.monitor_combo: QComboBox = QComboBox()
        self.monitor_combo.setFixedWidth(400)
        self.monitor_combo.currentIndexChanged.connect(self.on_monitor_selected)
        self.fps_label: QLabel = QLabel('FPS：')
        self.fps_input: QLineEdit = QLineEdit()
        self.fps_input.setValidator(QIntValidator(1, 60))
        self.fps_input.setText('15')
        self.fps_input.setFixedWidth(60)
        self.fps_input.textChanged.connect(self.on_fps_changed)
        self.refresh_info_button: QPushButton = QPushButton('刷新显示器列表')
        self.refresh_info_button.clicked.connect(self.refresh_device_info)
        self.camera_toggle_button: QPushButton = QPushButton('启动')
        self.camera_toggle_button.clicked.connect(self.toggle_camera)
        self.icon_library_button: QPushButton = QPushButton('管理图标库')
        self.icon_library_button.clicked.connect(self.open_icon_library)
        self.l1_left_layout.addWidget(self.monitor_label)
        self.l1_left_layout.addWidget(self.monitor_combo)
        self.l1_left_layout.addWidget(self.fps_label)
        self.l1_left_layout.addWidget(self.fps_input)
        self.l1_left_layout.addWidget(self.refresh_info_button)
        self.l1_left_layout.addWidget(self.camera_toggle_button)
        self.l1_left_layout.addWidget(self.icon_library_button)
        self.l1_left_layout.addStretch()
        self.l1_layout.addLayout(self.l1_left_layout)
        self.l1_layout.addStretch()

    def create_display_layout(self) -> None:
        self.l2_layout: QVBoxLayout = QVBoxLayout()
        self.l2l_layout: QVBoxLayout = QVBoxLayout()
        self.l2_tab_widget: QTabWidget = QTabWidget()
        self.info_display_tab: InfoDisplayTab = InfoDisplayTab()
        self.info_display_tab.setObjectName('info_display_tab')
        self.l2_tab_widget.addTab(self.info_display_tab, '信息')
        log_tab: QWidget = QWidget()
        log_tab_layout: QVBoxLayout = QVBoxLayout(log_tab)
        log_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.log_display: QTextEdit = QTextEdit()
        self.log_display.setReadOnly(True)
        log_tab_layout.addWidget(self.log_display)
        self.l2_tab_widget.addTab(log_tab, '日志')
        self.l2_tab_widget.setCurrentIndex(0)
        self.l2l_layout.addWidget(self.l2_tab_widget)
        self.l2_layout.addLayout(self.l2l_layout)
        log_emitter: LogEmitter = LogEmitter(self.log_display)
        sys.stdout = LogRedirector(log_emitter)
        self.info_display_tab.update_from_pixel_dump(self._get_pixel_dump())

    def open_icon_library(self) -> None:
        if self.icon_library_dialog is None or not self.icon_library_dialog.isVisible():
            self.icon_library_dialog = IconLibraryDialog(self.title_repository, self)
            self.icon_library_dialog.setWindowIcon(self.windowIcon())
            self.icon_library_dialog.show()
            self.icon_library_dialog.raise_()
            self.icon_library_dialog.activateWindow()
        else:
            self.icon_library_dialog.raise_()
            self.icon_library_dialog.activateWindow()

    def on_monitor_selected(self, index: int) -> None:
        if index < 0 or index >= len(self.monitor_list):
            return
        device_idx, output_idx, _ = self.monitor_list[index]
        self.device_idx = device_idx
        self.output_idx = output_idx
        timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_display.append(f'[{timestamp}] 选择显示器: Device[{device_idx}] Output[{output_idx}]')

    def on_fps_changed(self, text: str) -> None:
        if text == '':
            return
        try:
            fps: int = int(text)
            if fps < 1 or fps > 60:
                return
            self.current_fps = fps
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message: str = f'[{timestamp}] FPS 设置为 {fps}'
            self.log_display.append(log_message)
        except ValueError:
            return

    def refresh_device_info(self) -> None:
        try:
            output_info: str = dxcam.output_info()
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f'[{timestamp}] DXCam 输出信息：')
            self.log_display.append(output_info)
            self.monitor_list = self._parse_output_info(output_info)
            self.monitor_combo.clear()
            for device_idx, output_idx, display_text in self.monitor_list:
                self.monitor_combo.addItem(display_text, (device_idx, output_idx))
            if self.monitor_list:
                self.device_idx = self.monitor_list[0][0]
                self.output_idx = self.monitor_list[0][1]
                self.log_display.append(f'[{timestamp}] 找到 {len(self.monitor_list)} 个显示器')
            else:
                self.log_display.append(f'[{timestamp}] 未找到显示器')
        except Exception as e:
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f'[{timestamp}] 设备信息获取失败: {e}')

    def _parse_output_info(self, output_info: str) -> list[tuple[int, int, str]]:
        monitors: list[tuple[int, int, str]] = []
        pattern = 'Device\\[(\\d+)\\]\\s+Output\\[(\\d+)\\]:\\s+(.+)'
        for line in output_info.strip().split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                device_idx = int(match.group(1))
                output_idx = int(match.group(2))
                info = match.group(3).strip()
                display_text = f'Device[{device_idx}] Output[{output_idx}]: {info}'
                monitors.append((device_idx, output_idx, display_text))
        return monitors

    def toggle_camera(self) -> None:
        if not self.camera_running:
            if not self.monitor_list:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] 未检测到显示器，请先刷新显示器列表并选择')
                return
            try:
                self.camera = cast(_DxCameraLike, dxcam.create(device_idx=self.device_idx, output_idx=self.output_idx))
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] DXCam 相机创建成功 (device={self.device_idx}, output={self.output_idx})')
            except Exception as e:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] 相机初始化失败: {e}')
                return
            try:
                camera: _DxCameraLike = self.camera
                frame: np.ndarray | None = camera.grab()
                if frame is None:
                    timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log_display.append(f'[{timestamp}] 屏幕捕获失败，请检查显示器是否可用')
                    self._cleanup_camera()
                    return
            except Exception as e:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] 屏幕捕获异常: {e}')
                self._cleanup_camera()
                return
            try:
                bounds: tuple[int, int, int, int] | None = find_template_bounds(frame, MARK8_TEMPLATE)
                if bounds is None:
                    timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log_display.append(f'[{timestamp}] 未检测到游戏标记，请确保游戏内插件已启用并可见')
                    self._cleanup_camera()
                    return
            except Exception as e:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                error_msg: str = f'[{timestamp}] 标记识别异常:\n{traceback.format_exc()}'
                self.log_display.append(error_msg)
                self._cleanup_camera()
                return
            left, top, right, bottom = bounds
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 找到标记位置: ({left}, {top}, {right}, {bottom})")
            self.camera_worker = CameraWorker(self.camera, self.current_fps, bounds)
            self.camera_worker.data_signal.connect(self.process_captured_frame)
            self.camera_worker.log_signal.connect(self.append_camera_log)
            self.camera_worker.start()
            self.camera_running = True
            self.camera_toggle_button.setText('停止')
            self.monitor_combo.setEnabled(False)
            self.fps_input.setEnabled(False)
            self.refresh_info_button.setEnabled(False)
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CameraWorker 启动")
        else:
            if self.camera_worker:
                self.camera_worker.stop()
                self.camera_worker = None
            self._cleanup_camera()
            self.camera_running = False
            self.camera_toggle_button.setText('启动')
            self.monitor_combo.setEnabled(True)
            self.fps_input.setEnabled(True)
            self.refresh_info_button.setEnabled(True)
            self._set_pixel_dump({'error': '已停止'})
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CameraWorker 停止")

    def _cleanup_camera(self) -> None:
        if self.camera is not None:
            try:
                self.camera.stop()
            except Exception:
                pass
            try:
                self.camera.release()
            except Exception:
                pass
            del self.camera
            self.camera = None

    def process_captured_frame(self, frame: np.ndarray, camera_status: str) -> None:
        if camera_status == 'ok':
            try:
                extractor: GridDecoder = GridDecoder(frame)
                node_1_16 = extractor.cell(1, 16)
                node_50_1 = extractor.cell(50, 1)
                node_1_1 = extractor.cell(1, 1)
                node_50_16 = extractor.cell(50, 16)
                node_51_4 = extractor.cell(51, 4)
                node_flash = extractor.cell(37, 5)
                validation_errors: list[str] = []
                if not node_1_16.is_black:
                    validation_errors.append(f'(1,16)应为黑色')
                if not node_50_1.is_black:
                    validation_errors.append(f'(50,1)应为黑色')
                if not node_1_1.is_pure:
                    validation_errors.append(f'(1,1)应为纯色(参考色)')
                if not node_50_16.is_pure:
                    validation_errors.append(f'(50,16)应为纯色(参考色)')
                if node_1_1.is_pure and node_50_16.is_pure:
                    if node_1_1.color_string != node_50_16.color_string:
                        validation_errors.append(f'(1,1)和(50,16)颜色不匹配: {node_1_1.color_string} != {node_50_16.color_string}')
                if node_51_4.is_pure:
                    validation_errors.append(f'(51,4)应为非纯色(数据区)')
                if not (node_flash.is_black or node_flash.is_white):
                    validation_errors.append(f'闪烁node处于过渡中{node_flash.color_string}')
                if validation_errors:
                    # details is intentionally a list for in-frame validation failures.
                    error_dump: dict[str, Any] = {'error': '游戏窗口被遮挡或插件未加载，请检查游戏窗口是否可见', 'details': validation_errors}
                    self._set_pixel_dump(error_dump)
                    return
                dump_data: dict[str, Any] = extract_all_data(extractor)
                self._set_pixel_dump(dump_data)
            except Exception:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                error_msg: str = f'[{timestamp}] 数据处理异常:\n{traceback.format_exc()}'
                self.log_display.append(error_msg)
        else:
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f'[{timestamp}] 捕获失败，状态: {camera_status}')

    def append_camera_log(self, log_message: str) -> None:
        self.log_display.append(log_message)

    def _on_api_url_selected(self) -> None:
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(self.api_url_input.text())

    def _on_visit_api_clicked(self) -> None:
        QDesktopServices.openUrl(QUrl(self.api_url_input.text()))

    def closeEvent(self, event: Any) -> None:
        text, ok = QInputDialog.getText(self, '确认退出', '输入 exit 以关闭程序：')
        if not ok or text != 'exit':
            event.ignore()
            return
        if self.camera_worker:
            self.camera_worker.stop()
            self.camera_worker = None
        self._cleanup_camera()
        if self.web_server:
            self.web_server.stop()
            self.web_server = None
        if self.info_display_worker:
            self.info_display_worker.stop()
            self.info_display_worker = None
        event.accept()
