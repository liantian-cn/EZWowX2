"""
Summary:
    从完整 RGB 图像定位非 DEBUG 基板并校验两侧检测色块。
Description:
    精确筛选棋盘角标，按固定高度配对得到唯一基板；逐块验证中心 2×2。
    角标和几何失效与校验色错误分开，使调用方决定是否需要重新全屏搜索。
Key Variables:
    MARKER: 两种暗色组成的 4×4 非 DEBUG 棋盘定位符。
    CALIBRATION: 两侧检测色块的名称、位置与精确 RGB。
Change Log:
    2026-09-11: Added 非 DEBUG 图像定位与颜色校验。
"""

import numpy as np

from phantom.core.capture.contracts import Bounds, CaptureStatus, RGBImage

MARKER: RGBImage = np.array(
    [[[15, 25, 20], [15, 25, 20], [25, 15, 20], [25, 15, 20]], [[15, 25, 20], [15, 25, 20], [25, 15, 20], [25, 15, 20]], [[25, 15, 20], [25, 15, 20], [15, 25, 20], [15, 25, 20]], [[25, 15, 20], [25, 15, 20], [15, 25, 20], [15, 25, 20]]],
    dtype=np.uint8,
)
CALIBRATION: tuple[tuple[str, int, bool, tuple[int, int, int]], ...] = (
    ("Cyan", 4, False, (0, 255, 255)),
    ("Magenta", 8, False, (255, 0, 255)),
    ("Yellow", 12, False, (255, 255, 0)),
    ("Red", 12, True, (255, 0, 0)),
    ("Green", 8, True, (0, 255, 0)),
    ("Blue", 4, True, (0, 0, 255)),
    ("Gray", 0, True, (127, 127, 127)),
)


def is_rgb(image: RGBImage) -> bool:
    return image.dtype == np.uint8 and image.ndim == 3 and image.shape[2] == 3


def find_bounds(image: RGBImage) -> tuple[Bounds | None, CaptureStatus]:
    if not is_rgb(image):
        return None, CaptureStatus(True, "定位输入必须为 RGB uint8 三通道图像")
    height, width = image.shape[:2]
    if height < 20 or width < 8:
        return None, CaptureStatus(True, "图像尺寸不足以包含基板")

    # 先筛选角标首像素，仅对候选坐标比较完整 4×4，避免构造全屏滑窗张量。
    candidates = np.all(image[: height - 3, : width - 3] == MARKER[0, 0], axis=2)
    ys, xs = np.nonzero(candidates)
    for dy in range(4):
        for dx in range(4):
            matches = np.all(image[ys + dy, xs + dx] == MARKER[dy, dx], axis=1)
            ys, xs = ys[matches], xs[matches]

    rows: dict[int, list[int]] = {}
    for y, x in zip(ys.tolist(), xs.tolist(), strict=True):
        rows.setdefault(y, []).append(x)

    found: Bounds | None = None
    for top, lefts in rows.items():
        for left in lefts:
            for right_marker in rows.get(top + 16, []):
                frame_width = right_marker + 4 - left
                if frame_width >= 8 and frame_width % 4 == 0:
                    if found is not None:
                        return None, CaptureStatus(True, "存在多个候选基板，无法唯一定位")
                    found = Bounds(left, top, right_marker + 4, top + 20)
    if found is None:
        return None, CaptureStatus(True, "未找到非 DEBUG 基板定位标记")
    return found, CaptureStatus()


def markers_valid(image: RGBImage) -> bool:
    if not is_rgb(image):
        return False
    height, width = image.shape[:2]
    return height == 20 and width >= 8 and width % 4 == 0 and np.array_equal(image[:4, :4], MARKER) and np.array_equal(image[-4:, -4:], MARKER)


def validate_colors(image: RGBImage) -> CaptureStatus:
    if not markers_valid(image):
        return CaptureStatus(True, "基板尺寸或定位标记失效")
    for name, y, right, expected in CALIBRATION:
        x = image.shape[1] - 4 if right else 0
        center = image[y + 1 : y + 3, x + 1 : x + 3]
        if not np.all(center == expected):
            return CaptureStatus(True, f"{name} 中心 2×2 颜色不匹配，预期 RGB={expected}")
    flash = image[17:19, 1:3]
    if not (np.all(flash == 0) or np.all(flash == 255)):
        return CaptureStatus(True, "Flash 中心 2×2 必须全部为黑色或全部为白色")
    return CaptureStatus()
