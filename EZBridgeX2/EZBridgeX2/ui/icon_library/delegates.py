from typing import Any, cast
import numpy as np
from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

class NodeImageDelegate(QStyledItemDelegate):

    def __init__(self, parent: QWidget | None=None, scale: int=4) -> None:
        super().__init__(parent)
        self.scale: int = scale

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> None:
        super().paint(painter, option, index)
        data = index.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return
        pixmap: QPixmap | None = self._array_to_pixmap(data)
        if pixmap:
            painter.save()
            rect = cast(Any, option).rect
            x: int = rect.x() + (rect.width() - pixmap.width()) // 2
            y: int = rect.y() + (rect.height() - pixmap.height()) // 2
            painter.drawPixmap(x, y, pixmap)
            painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        data = index.data(Qt.ItemDataRole.UserRole)
        if data is not None:
            height, width = data.shape[:2]
            return QSize(width * self.scale + 8, height * self.scale + 8)
        return super().sizeHint(option, index)

    def _array_to_pixmap(self, arr: np.ndarray) -> QPixmap | None:
        try:
            height: int
            width: int
            height, width = arr.shape[:2]
            image: QImage
            if len(arr.shape) == 3 and arr.shape[2] == 3:
                bytes_per_line: int = 3 * width
                image = QImage(arr.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            elif len(arr.shape) == 2:
                image = QImage(arr.data.tobytes(), width, height, width, QImage.Format.Format_Grayscale8)
            else:
                return None
            scaled: QImage = image.scaled(width * self.scale, height * self.scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            return QPixmap.fromImage(scaled)
        except Exception:
            return None

class HashDisplayDelegate(QStyledItemDelegate):

    def displayText(self, value: Any, locale: Any) -> str:
        if isinstance(value, str) and len(value) > 20:
            return f'{value[:8]}...{value[-8:]}'
        return super().displayText(value, locale)

class SimilarityDisplayDelegate(QStyledItemDelegate):

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: Any) -> None:
        value = index.data()
        if isinstance(value, (int, float)):
            color: QColor
            if value >= 0.95:
                color = QColor(0, 150, 0)
            elif value >= 0.9:
                color = QColor(200, 150, 0)
            else:
                color = QColor(200, 0, 0)
            opt = cast(Any, option)
            opt.palette.setColor(opt.palette.ColorRole.Text, color)
        super().paint(painter, option, index)

    def displayText(self, value: Any, locale: Any) -> str:
        if isinstance(value, (int, float)):
            return f'{value * 100:.2f}%'
        return super().displayText(value, locale)
