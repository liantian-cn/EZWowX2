from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal

from ..pixelcalc.extractor import extract_all_data
from ..pixelcalc.matrix import MatrixDecoder


class FrameDecodeWorker(QObject):
    """把截图帧解成 Matrix 和结构化数据。

    这个 worker 只做解码，不碰 UI，也不负责排队策略。
    主线程决定哪些帧要丢掉，这里只处理真正交进来的那一帧。
    """

    frame_decoded = Signal(int, object, object)
    frame_invalid = Signal(int, str)
    frame_failed = Signal(int, str)

    def submit_frame(self, frame: Any, frame_id: int) -> None:
        """解码一帧；校验不过就直接返回无效状态。"""

        matrix = MatrixDecoder(frame)
        flash_cell = matrix.getCell(54, 9)

        if not (flash_cell.is_black or flash_cell.is_white):
            self.frame_invalid.emit(frame_id, f'第 {frame_id} 帧校验失败: flash cell 不是纯黑或纯白。')
            return

        if not matrix.getCell(0, 0).is_pure:
            self.frame_invalid.emit(frame_id, f'第 {frame_id} 帧校验失败: 左上角锚点 cell 不是纯色。')
            return

        if not matrix.getCell(82, 2).is_white:
            self.frame_invalid.emit(frame_id, f'第 {frame_id} 帧校验失败: 右上角锚点 cell 不是白色。')
            return

        if matrix.readCharCell(0, 2) == 0:
            self.frame_invalid.emit(frame_id, f'第 {frame_id} 帧校验失败: 文字检测帧异常。尝试/reload')
            return

        try:
            data = extract_all_data(matrix)
        except Exception as error:
            self.frame_failed.emit(frame_id, f'第 {frame_id} 帧解析异常: {error}')
            return

        self.frame_decoded.emit(frame_id, matrix, data)
