import sys
import random
import time
import ctypes
from typing import List, Any

import cv2
import numpy as np
import dxcam
from win32gui import EnumWindows, GetWindowText

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QLineEdit, QMessageBox


# ── 常量 ──────────────────────────────────────────────

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

KEY_COLOR_MAP = {
    '13, 255, 0': 'SHIFT-NUMPAD1',
    '0, 255, 64': 'SHIFT-NUMPAD2',
    '0, 255, 140': 'SHIFT-NUMPAD3',
    '0, 255, 217': 'SHIFT-NUMPAD4',
    '0, 217, 255': 'SHIFT-NUMPAD5',
    '0, 140, 255': 'SHIFT-NUMPAD6',
    '0, 64, 255': 'SHIFT-NUMPAD7',
    '13, 0, 255': 'SHIFT-NUMPAD8',
    '89, 0, 255': 'SHIFT-NUMPAD9',
    '166, 0, 255': 'SHIFT-NUMPAD0',
    '242, 0, 255': 'ALT-NUMPAD1',
    '255, 0, 191': 'ALT-NUMPAD2',
    '255, 0, 115': 'ALT-NUMPAD3',
    '255, 0, 38': 'ALT-NUMPAD4',
    '255, 38, 0': 'ALT-NUMPAD5',
    '255, 115, 0': 'ALT-NUMPAD6',
    '255, 191, 0': 'ALT-NUMPAD7',
    '242, 255, 0': 'ALT-NUMPAD8',
    '166, 255, 0': 'ALT-NUMPAD9',
    '89, 255, 0': 'ALT-NUMPAD0',
}

VK_DICT = {
    "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12,
    "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62,
    "NUMPAD3": 0x63, "NUMPAD4": 0x64, "NUMPAD5": 0x65,
    "NUMPAD6": 0x66, "NUMPAD7": 0x67, "NUMPAD8": 0x68,
    "NUMPAD9": 0x69,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F5": 0x74,
    "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78,
    "F10": 0x79, "F11": 0x7A,
}

MOD_MAP = {
    "CTRL": 0x0002, "CONTROL": 0x0002,
    "SHIFT": 0x0004, "ALT": 0x0001,
}


# ── 核心函数 ──────────────────────────────────────────

def find_all_matches(
    screenshot_array: np.ndarray,
    template_array: np.ndarray,
    threshold: float = 0.999,
) -> list[tuple[int, int]]:
    template_height, template_width = template_array.shape[:2]
    screenshot_height, screenshot_width = screenshot_array.shape[:2]
    if template_height > screenshot_height or template_width > screenshot_width:
        return []
    result = cv2.matchTemplate(screenshot_array, template_array, cv2.TM_CCOEFF_NORMED)
    match_locations = np.where(result >= threshold)
    matches = [(int(x), int(y)) for y, x in zip(match_locations[0], match_locations[1])]
    matches.sort()
    return matches


def find_template_bounds(
    screenshot_array: np.ndarray,
    threshold: float = 0.999,
) -> tuple[int, int, int, int] | None:
    try:
        template_array = np.array([
            [[255, 0, 0], [255, 0, 0], [0, 255, 0], [0, 255, 0]],
            [[255, 0, 0], [255, 0, 0], [0, 255, 0], [0, 255, 0]],
            [[0, 0, 0], [0, 0, 0], [0, 0, 255], [0, 0, 255]],
            [[0, 0, 0], [0, 0, 0], [0, 0, 255], [0, 0, 255]],
        ], dtype=np.uint8)
        template_height, template_width = template_array.shape[:2]
        matches = find_all_matches(screenshot_array, template_array, threshold)
        if len(matches) != 2:
            return None
        x1, y1 = matches[0]
        x2, y2 = matches[1]
        left = int(min(x1, x2))
        top = int(min(y1, y2))
        right = int(max(x1 + template_width, x2 + template_width))
        bottom = int(max(y1 + template_height, y2 + template_height))
        width, height = right - left, bottom - top
        if width % 4 != 0 or height % 4 != 0:
            return None
        return (left, top, right, bottom)
    except Exception:
        return None


def press_key_hwnd(hwnd: int, skey: str) -> None:
    key = VK_DICT.get(skey)
    if key is None:
        raise KeyError(f"Virtual key '{skey}' not found")
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYDOWN, key, 0)


def release_key_hwnd(hwnd: int, skey: str) -> None:
    key = VK_DICT.get(skey)
    if key is None:
        raise KeyError(f"Virtual key '{skey}' not found")
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYUP, key, 0)


def send_hot_key(hwnd: int, hot_key: str) -> None:
    key_list = hot_key.split("-")
    for skey in key_list:
        press_key_hwnd(hwnd, skey)
    time.sleep(0.01)
    for skey in reversed(key_list):
        release_key_hwnd(hwnd, skey)


def get_windows_by_title(title: str) -> List[int]:
    windows: List[tuple] = []

    def enum_callback(hwnd: int, _: Any) -> None:
        windows.append((hwnd, GetWindowText(hwnd)))

    EnumWindows(enum_callback, None)
    return [hwnd for hwnd, wt in windows if title.lower() in wt.lower()]


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False


# ── 工作线程 ──────────────────────────────────────────

class WorkerThread(QThread):
    log_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, hwnd: int):
        super().__init__()
        self.hwnd = hwnd
        self._running = False

    def run(self):
        self._running = True
        try:
            camera = dxcam.create()
            frame = camera.grab()
            if frame is None:
                self.error_signal.emit("无法抓取屏幕帧")
                return

            bounds = find_template_bounds(frame)
            if bounds is None:
                self.error_signal.emit("未找到模板")
                camera.release()
                camera.stop()
                del camera
                return

            left, top, right, bottom = bounds
            if not ((right - left) == 12 and (bottom - top) == 4):
                self.error_signal.emit("模板大小不正确")
                camera.release()
                camera.stop()
                del camera
                return

            region = (left + 4, top, right - 4, bottom)
            camera.release()
            camera.stop()
            del camera

            camera = dxcam.create(region=region)
            camera.start(target_fps=30)

            while self._running:
                time.sleep(random.uniform(0.1, 0.2))
                cropped_frame = camera.get_latest_frame()
                if cropped_frame is None:
                    continue
                if np.all(cropped_frame == cropped_frame[0, 0]):
                    pix = cropped_frame[0, 0]
                    if pix[0] == 255 and pix[1] == 255 and pix[2] == 255:
                        self.log_signal.emit("纯白")
                    elif pix[0] == 0 and pix[1] == 0 and pix[2] == 0:
                        self.log_signal.emit("纯黑")
                    else:
                        color_key = f"{pix[0]}, {pix[1]}, {pix[2]}"
                        key = KEY_COLOR_MAP.get(color_key)
                        if key is not None:
                            send_hot_key(self.hwnd, key)
                            self.log_signal.emit(f"发送按键: {key}")
                        else:
                            self.log_signal.emit(f"未知颜色: {color_key}")
                else:
                    self.log_signal.emit("不是纯色")

            camera.stop()
            camera.release()
            del camera
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def stop(self):
        self._running = False


# ── 主窗口 ────────────────────────────────────────────

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker: WorkerThread | None = None
        self.setWindowTitle("EZAssistedX2")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._init_ui()
        self._refresh_windows()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 第一行：下拉框 + 刷新 + 开始 + 停止
        row1 = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.currentIndexChanged.connect(self._on_selection_changed)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self._refresh_windows)

        self.btn_start = QPushButton("开始")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._start)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)

        row1.addWidget(self.combo, 1)
        row1.addWidget(self.btn_refresh)
        row1.addWidget(self.btn_start)
        row1.addWidget(self.btn_stop)

        # 第二行：日志
        self.log_line = QLineEdit()
        self.log_line.setReadOnly(True)
        self.log_line.setPlaceholderText("日志输出...")

        layout.addLayout(row1)
        layout.addWidget(self.log_line)

    def _refresh_windows(self):
        self.combo.clear()
        hwnds = get_windows_by_title("魔兽世界")
        for hwnd in hwnds:
            self.combo.addItem(f"魔兽世界{hwnd}", hwnd)
        self.btn_start.setEnabled(self.combo.count() > 0)

    def _on_selection_changed(self, index: int):
        self.btn_start.setEnabled(index >= 0 and self.worker is None)

    def _start(self):
        hwnd = self.combo.currentData()
        if hwnd is None:
            return
        self.worker = WorkerThread(hwnd)
        self.worker.log_signal.connect(self._on_log)
        self.worker.error_signal.connect(self._on_error)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_refresh.setEnabled(False)
        self.combo.setEnabled(False)
        self.log_line.setText("已启动")

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            self.log_line.setText("正在停止...")

    def _on_log(self, msg: str):
        self.log_line.setText(msg)

    def _on_error(self, msg: str):
        self.log_line.setText(f"错误: {msg}")

    def _on_finished(self):
        self.worker = None
        self.btn_start.setEnabled(self.combo.count() > 0)
        self.btn_stop.setEnabled(False)
        self.btn_refresh.setEnabled(True)
        self.combo.setEnabled(True)
        self.log_line.setText("已停止")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        event.accept()


# ── 入口 ──────────────────────────────────────────────

def main():
    # Mutex 单实例检查
    mutex_name = "EZAssistedX2"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    already_running = ctypes.windll.kernel32.GetLastError() == 183

    app = QApplication(sys.argv)

    if already_running:
        QMessageBox.information(None, "EZAssistedX2", "程序已在运行中。")
        sys.exit(0)

    if not is_admin():
        QMessageBox.information(None, "EZAssistedX2", "必须以UAC管理员身份运行。")
        sys.exit(0)

    window = MainWindow()
    window.show()
    ret = app.exec()

    ctypes.windll.kernel32.ReleaseMutex(mutex)
    ctypes.windll.kernel32.CloseHandle(mutex)
    sys.exit(ret)


if __name__ == "__main__":
    main()
