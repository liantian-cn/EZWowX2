import ctypes
import sys
from PySide6.QtWidgets import QMessageBox
from terminal.application import Termnal


def main() -> int:
    mutex_name: str = 'terminal'
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:
        # app = create_qapplication(sys.argv)
        QMessageBox.information(None, '提示', f'{mutex_name}已经在运行。')
        return 0
    try:
        termnal = Termnal()
        return termnal.run()
    finally:
        if mutex:
            ctypes.windll.kernel32.ReleaseMutex(mutex)
            ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == '__main__':
    sys.exit(main())
