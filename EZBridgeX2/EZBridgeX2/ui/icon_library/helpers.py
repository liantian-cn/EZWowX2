import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QPixmap

def create_icon_from_data(full_array: np.ndarray) -> QIcon:
    try:
        height, width = full_array.shape[:2]
        if len(full_array.shape) == 3 and full_array.shape[2] == 3:
            bytes_per_line: int = 3 * width
            image: QImage = QImage(full_array.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
        elif len(full_array.shape) == 2:
            image = QImage(full_array.data.tobytes(), width, height, width, QImage.Format.Format_Grayscale8)
        else:
            return QIcon()
        scaled_image: QImage = image.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio)
        pixmap: QPixmap = QPixmap.fromImage(scaled_image)
        return QIcon(pixmap)
    except Exception as error:
        print(f'[create_icon_from_data] 错误: {error}')
        return QIcon()
