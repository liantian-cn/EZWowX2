import atexit
import json
import random
import datetime
import threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QInputDialog, QApplication, QLabel, QPushButton
from PySide6.QtCore import QThread, Signal, Qt, QUrl, QTimer
from PySide6.QtGui import QDesktopServices
from flask import Flask, jsonify
import numpy as np
import dxcam
from Dumper import find_template_bounds, PixelDumper, save_user_input_hash, hashstr_used


class WebServerWorker(QThread):
    """
    Flask Web 服务器工作线程
    监听 http://127.0.0.1:65131，提供 /api 接口返回 pixel_dump 数据
    """

    def __init__(self, pixel_dump):
        """
        初始化 Web 服务器工作线程
        :param pixel_dump: 主程序的 pixel_dump 字典
        """
        super().__init__()
        self.pixel_dump = pixel_dump
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """
        设置 Flask 路由
        定义 /api 接口，返回 pixel_dump 的 JSON 数据
        """

        @self.app.route('/api')
        def dump():
            """
            处理 /api 请求
            返回 pixel_dump 的 JSON 格式数据
            """
            return jsonify(self.pixel_dump)

    def run(self):
        """
        运行 Flask 服务器
        在 127.0.0.1:65131 上启动服务器
        """
        self.app.run(host='127.0.0.1', port=65131, debug=False, use_reloader=False)


class CameraWorker(QThread):
    """
    Camera 工作线程
    使用 dxcam 捕获屏幕指定区域，并通过信号发送图像数据
    """
    # 定义信号：返回图像数据和时间戳
    data_signal = Signal(np.ndarray, str)
    # 定义信号：返回日志信息
    log_signal = Signal(str)

    def __init__(self, camera, bounds, target_fps=15):
        """
        初始化 Camera 工作线程
        :param camera: dxcam 相机实例
        :param bounds: 屏幕捕获区域边界 (left, top, right, bottom)
        :param target_fps: 目标帧率，默认 15
        """
        super().__init__()
        self.running = True
        self.camera = camera
        left, top, right, bottom = bounds
        self.camera.start(region=(left, top, right, bottom), target_fps=target_fps)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] CameraWorker 初始化完成'
        self.log_signal.emit(log_message)

    def run(self):
        """
        运行 Camera 工作线程
        循环获取最新帧并通过信号发送图像数据和时间戳
        """
        while self.running:
            cropped_array = self.camera.get_latest_frame()
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.data_signal.emit(cropped_array, timestamp)

    def stop(self):
        """
        停止 Camera 工作线程
        停止相机捕获并清理资源
        """
        self.running = False
        self.camera.stop()
        del self.camera
        self.wait()


class MainWindow(QWidget):
    """
    主窗口类
    包含所有 UI 组件和逻辑处理
    """

    def __init__(self):
        """
        初始化主窗口
        设置窗口属性、布局、工作线程等
        """
        super().__init__()
        self.pixel_dump = {}
        self.dialog_visible = False
        self.dialog_cooldown = False
        self.data_refresh_enabled = True
        self.setWindowTitle('PixelDumper')
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        self.resize(width, height)
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        self.move(x, y)
        self.setFixedHeight(height)
        self.init_ui()
        self.workers_initialized = False

    def init_ui(self):
        """
        初始化 UI 组件
        创建布局和控件
        """
        main_layout = QVBoxLayout()
        self.create_l1_layout()
        main_layout.addLayout(self.l1_layout)
        self.create_l2_layout()
        main_layout.addLayout(self.l2_layout)
        self.setLayout(main_layout)

    def create_l1_layout(self):
        """
        创建 L1Layout（第一层布局）
        包含 Label、只读的单行输入框和两个按钮
        """
        self.l1_layout = QHBoxLayout()
        self.l1_left_layout = QHBoxLayout()
        self.start_button = QPushButton('启动')
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.refresh_button = QPushButton('暂停刷新')
        self.refresh_button.clicked.connect(self.on_refresh_button_clicked)
        self.url_label = QLabel('API地址：')
        self.url_input = QLineEdit()
        self.url_input.setText('http://127.0.0.1:65131/api')
        self.url_input.setReadOnly(True)
        self.open_api_button = QPushButton('打开API')
        self.open_api_button.clicked.connect(self.on_open_api_button_clicked)
        self.l1_left_layout.addWidget(self.start_button)
        self.l1_left_layout.addWidget(self.refresh_button)
        self.l1_left_layout.addWidget(self.url_label)
        self.l1_left_layout.addWidget(self.url_input)
        self.l1_left_layout.addWidget(self.open_api_button)
        self.l1_right_layout = QHBoxLayout()
        self.github_button = QPushButton('Github')
        self.github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/liantian-cn/WowPixelDumper')))
        self.discord_button = QPushButton('Discord')
        self.discord_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://discord.gg/DX77uHc9')))
        self.l1_right_layout.addWidget(self.github_button)
        self.l1_right_layout.addWidget(self.discord_button)
        self.l1_layout.addLayout(self.l1_left_layout)
        self.l1_layout.addStretch()
        self.l1_layout.addLayout(self.l1_right_layout)

    def create_l2_layout(self):
        """
        创建 L2Layout（第二层布局）
        包含左侧的数据显示框（75%）和右侧的日志框（25%）
        """
        self.l2_layout = QHBoxLayout()
        self.l2l_layout = QVBoxLayout()
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.l2l_layout.addWidget(self.data_display)
        self.l2r_layout = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.l2r_layout.addWidget(self.log_display)
        self.l2_layout.addLayout(self.l2l_layout, 3)
        self.l2_layout.addLayout(self.l2r_layout, 1)

    def init_workers(self):
        """
        初始化工作线程
        创建并启动 WebServerWorker 和 CameraWorker
        返回初始化是否成功
        """
        try:
            self.camera = dxcam.create()
            frame = self.camera.grab()
            if frame is None:
                self.log_display.append('无法获取屏幕截图')
                return False
            bounds = find_template_bounds(frame, 'mark.png')
            if bounds is None:
                self.log_display.append('未找到标记')
                return False
            left, top, right, bottom = bounds
            self.log_display.append(f'找到标记构成的矩形边界: {bounds}')
            self.log_display.append(f'边界尺寸: {right - left} x {bottom - top}')
            self.web_server_worker = WebServerWorker(self.pixel_dump)
            self.camera_worker = CameraWorker(self.camera, bounds)
            self.camera_worker.data_signal.connect(self.handle_camera_data)
            self.camera_worker.log_signal.connect(self.handle_camera_log)
            self.web_server_worker.start()
            self.camera_worker.start()
            self.log_display.append('Web 服务器已启动: http://127.0.0.1:65131')
            self.log_display.append('Camera 工作线程已启动')
            self.workers_initialized = True
            return True
        except Exception as e:
            self.log_display.append(f'初始化工作线程失败: {str(e)}')
            self.workers_initialized = False
            return False

    def on_start_button_clicked(self):
        """
        处理启动按钮点击事件
        禁用按钮，执行 init_workers，根据结果决定是否恢复按钮可用状态
        """
        self.start_button.setDisabled(True)
        success = self.init_workers()
        if not success:
            self.start_button.setEnabled(True)

    def handle_camera_data(self, cropped_array, timestamp):
        """
        处理 CameraWorker 返回的数据
        更新 pixel_dump 字典和数据显示框
        :param cropped_array: 截取的图像数组
        :param timestamp: 时间戳
        """
        dumper = PixelDumper(cropped_array)
        si_node_1 = dumper.node(1, 17)
        si_node_2 = dumper.node(15, 1)
        si_node_3 = dumper.node(54, 14)
        if si_node_1.is_not_pure and si_node_2.is_not_pure and si_node_3.is_not_pure:
            if si_node_1.hash == si_node_2.hash == si_node_3.hash and (not hashstr_used(si_node_1.hash)):
                self.log_display.append(f'SI节点1、2、3颜色相同，哈希值为: {si_node_1.hash}\n为这个hash值绑定什么技能？')
                if not self.dialog_visible and (not self.dialog_cooldown):
                    self.show_hash_dialog(si_node_1.hash)
        dump_data = dumper.dump_all()
        dump_data['timestamp'] = timestamp
        self.pixel_dump.clear()
        self.pixel_dump.update(dump_data)
        if self.data_refresh_enabled:
            self.data_display.setText(json.dumps(self.pixel_dump, indent=8, ensure_ascii=False))

    def handle_camera_log(self, log_message):
        """
        处理 CameraWorker 返回的日志
        更新日志显示框
        :param log_message: 日志消息
        """
        self.log_display.append(log_message)

    def show_hash_dialog(self, hash_value):
        """
        显示 Hash 值标题输入对话框
        让用户输入 Hash 值对应的标题，并更新 pixel_dump
        :param hash_value: 要绑定标题的 Hash 值
        """
        self.dialog_visible = True
        self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 显示对话框")
        text, ok = QInputDialog.getText(self, '请输入Hash值对应的标题', f'标题({hash_value}):')
        if ok and text:
            save_user_input_hash(hash_value, text)
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户输入标题: {text}")
        elif ok:
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户未输入标题")
        else:
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户取消输入")
        self.dialog_visible = False
        self.dialog_cooldown = True
        QTimer.singleShot(3000, self.reset_dialog_cooldown)

    def reset_dialog_cooldown(self):
        """
        重置对话框冷却标志
        """
        self.dialog_cooldown = False
        self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 对话框冷却已恢复")

    def on_refresh_button_clicked(self):
        """
        处理暂停/恢复刷新按钮点击事件
        切换刷新状态并更新按钮文本
        """
        self.data_refresh_enabled = not self.data_refresh_enabled
        if self.data_refresh_enabled:
            self.refresh_button.setText('暂停刷新')
            self.data_display.setText(json.dumps(self.pixel_dump, indent=2, ensure_ascii=False))
        else:
            self.refresh_button.setText('恢复刷新')

    def on_open_api_button_clicked(self):
        """
        处理打开API地址按钮点击事件
        在浏览器中打开API地址
        """
        QDesktopServices.openUrl(QUrl('http://127.0.0.1:65131/api'))

    def closeEvent(self, event):
        """
        窗口关闭事件
        停止所有工作线程
        :param event: 关闭事件
        """
        self.camera_worker.stop()
        self.web_server_worker.terminate()
        self.web_server_worker.wait(1000)
        event.accept()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
