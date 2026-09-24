"""
Summary:
    将同帧通用 Cell 数据转换为 TUI 展示值。
Description:
    截图插件由核心按应用配置创建，UI 只解释采集结果。
    仅接收有效截图，将职业与专精两个 Cell 原始值一次性转换为表格展示数据。
Key Variables:
    GENERAL_FIELDS: 职业与专精 Cell 的固定展示顺序。
Change Log:
    2026-09-14: Changed 通用条件页仅展示职业与专精，其余状态由配置条件展示。
    2026-09-13: Changed 截图加载迁入核心，此处只保留通用数据展示。
    2026-09-12: Added 第 6 步采集展示适配。
"""

from dataclasses import dataclass

from phantom.core.capture.contracts import CaptureResult
from phantom.core.pixels import PixelDecoder

GENERAL_FIELDS = ("玩家职业", "玩家专精")


@dataclass(frozen=True)
class GeneralData:
    width: int
    height: int
    cells: tuple[tuple[str, str], ...]


def decode_general(result: CaptureResult) -> GeneralData:
    if result.status.has_error:
        raise ValueError(result.status.description)
    if result.image is None:
        raise ValueError("尚无有效截图")
    decoder = PixelDecoder(result.image)
    cells = [decoder.getCell(index, 1) for index in range(1, 3)]
    return GeneralData(width=result.image.shape[1], height=result.image.shape[0], cells=tuple((cell.color_string, f"{cell.mean:g}" if cell.is_pure else "—") for cell in cells))
