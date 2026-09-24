"""在截图里找两个 8x8 标记，再算出它们围出来的大框。

这个文件的用途很单纯: 
1. 在整张截图里找到两个固定小标记。
2. 用这两个标记的最外侧边界，反推出目标区域坐标。
3. 如果没找到、找到的数量不对，或者算出来的尺寸不合理，就返回 None。

这里故意写得直白一些，不做花哨抽象，方便以后自己回来读。
"""

import cv2
import numpy as np


__all__ = ["find_template_bounds"]

# 这个 8x8 模板就是我们要在截图里找的角标。
# 为了方便人眼理解，直接把两种颜色先起名，再按“4 格 + 4 格”拼出来。
MARK_COLOR_A = np.array([15, 25, 20], dtype=np.uint8)
MARK_COLOR_B = np.array([25, 15, 20], dtype=np.uint8)

MARK4_TEMPLATE = np.array(
    [
        [MARK_COLOR_A] * 4 + [MARK_COLOR_B] * 4,
        [MARK_COLOR_A] * 4 + [MARK_COLOR_B] * 4,
        [MARK_COLOR_A] * 4 + [MARK_COLOR_B] * 4,
        [MARK_COLOR_A] * 4 + [MARK_COLOR_B] * 4,
        [MARK_COLOR_B] * 4 + [MARK_COLOR_A] * 4,
        [MARK_COLOR_B] * 4 + [MARK_COLOR_A] * 4,
        [MARK_COLOR_B] * 4 + [MARK_COLOR_A] * 4,
        [MARK_COLOR_B] * 4 + [MARK_COLOR_A] * 4,
    ],
    dtype=np.uint8,
)

# simple.png 这种 JPEG 图片会有一点压缩误差，0.999 太严格，实测会漏掉。
MATCH_THRESHOLD = 0.999


def find_template_bounds(screenshot_array: np.ndarray) -> tuple[int, int, int, int] | None:
    """返回 (left, top, right, bottom)，找不到就返回 None。"""

    # 只接受正常的彩色图片数组，例如 (高, 宽, 3)。
    if screenshot_array.ndim != 3 or screenshot_array.shape[2] != 3:
        print("[find_template_bounds] 输入图片必须是三通道彩色数组")
        return None

    template_height, template_width = MARK4_TEMPLATE.shape[:2]
    screenshot_height, screenshot_width = screenshot_array.shape[:2]

    # 模板比截图还大时，不可能匹配成功，直接结束。
    if template_height > screenshot_height or template_width > screenshot_width:
        print("[find_template_bounds] 输入图片太小，装不下 8x8 模板")
        return None

    # 在整张图上滑动模板，得到每个位置的相似度。
    match_result = cv2.matchTemplate(screenshot_array, MARK4_TEMPLATE, cv2.TM_CCOEFF_NORMED)

    # 把所有超过门槛的位置都收集出来，按左上角坐标排序。
    match_y_list, match_x_list = np.where(match_result >= MATCH_THRESHOLD)
    matches = sorted((int(x), int(y)) for y, x in zip(match_y_list, match_x_list))

    # 我们只接受“刚好找到两个角标”的情况。
    if len(matches) != 2:
        print(f"[find_template_bounds] 需要找到 2 个标记，但找到 {len(matches)} 个")
        return None

    first_x, first_y = matches[0]
    second_x, second_y = matches[1]

    # 两个 8x8 标记一起围出一个大矩形。
    left = min(first_x, second_x)
    top = min(first_y, second_y)
    right = max(first_x + template_width, second_x + template_width)
    bottom = max(first_y + template_height, second_y + template_height)

    width = right - left
    height = bottom - top

    # 这个项目的矩阵按 8x8 小格切分，所以总宽高也应该能被 8 整除。
    if width % 4 != 0 or height % 4 != 0:
        print(f"[find_template_bounds] 边界尺寸必须是 4 的倍数，但得到 {width} x {height}")
        return None

    return (left, top, right, bottom)


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image

    # 独立运行时，直接拿仓库里的 simple.png 做一次最简单的手工检查。
    image_path = Path(__file__).resolve().parents[2] / "simple.png"
    crop_path = Path(__file__).resolve().parents[2] / "simple_crop.png"
    screenshot_array = np.array(Image.open(image_path).convert("RGB"))
    bounds = find_template_bounds(screenshot_array)

    if bounds is not None:
        left, top, right, bottom = bounds
        cropped_array = screenshot_array[top:bottom, left:right]
        Image.fromarray(cropped_array).save(crop_path)

    print(bounds)
