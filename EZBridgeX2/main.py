import ctypes
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from EZBridgeX2 import EZBridgeX2


def main() -> int:
    mutex_name: str = 'EZBridgeX2'
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.information(None, '提示', f'{mutex_name}已经在运行。')
        return 0
    try:
        bridge = EZBridgeX2()
        return bridge.run()
    finally:
        if mutex:
            ctypes.windll.kernel32.ReleaseMutex(mutex)
            ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == '__main__':
    sys.exit(main())
