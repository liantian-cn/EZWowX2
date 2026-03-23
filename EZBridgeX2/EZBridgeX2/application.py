import sys
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow


class EZBridgeX2:

    def __init__(self) -> None:
        self.app: QApplication | None = None
        self.window: MainWindow | None = None

    def run(self) -> int:
        self.app = QApplication(sys.argv)
        icon_path: Path = Path(__file__).resolve().with_name('icon.ico')
        self.app.setWindowIcon(QIcon(str(icon_path)))
        self.window = MainWindow()
        self.window.show()
        return self.app.exec()
