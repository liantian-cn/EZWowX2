import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .color_map import COLOR_MAP as _COLOR_MAP

def _resolve_app_dir() -> Path:
    runtime_dir: Path = Path(sys.argv[0]).resolve().parent
    if (runtime_dir / 'database.sqlite').exists():
        return runtime_dir
    package_dir: Path = Path(__file__).resolve().parents[2]
    if (package_dir / 'database.sqlite').exists():
        return package_dir
    return runtime_dir


app_dir: Path = _resolve_app_dir()
COLOR_MAP: dict[str, dict[str, str]] = _COLOR_MAP

def screenshot_to_array(screenshot: Image.Image) -> np.ndarray:
    if screenshot.mode != 'RGB':
        screenshot = screenshot.convert('RGB')
    screenshot_array: np.ndarray = np.array(screenshot)
    return screenshot_array

def load_template(template_path: str) -> np.ndarray:
    img: Image.Image = Image.open(template_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    template_array: np.ndarray = np.array(img)
    return template_array

def find_all_matches(screenshot_array: np.ndarray, template_array: np.ndarray, threshold: float=0.999) -> list[tuple[int, int]]:
    template_height: int
    template_width: int
    template_height, template_width = template_array.shape[:2]
    screenshot_height: int
    screenshot_width: int
    screenshot_height, screenshot_width = screenshot_array.shape[:2]
    if template_height > screenshot_height or template_width > screenshot_width:
        return []
    result: np.ndarray = cv2.matchTemplate(screenshot_array, template_array, cv2.TM_CCOEFF_NORMED)
    match_locations = np.where(result >= threshold)
    matches: list[tuple[int, int]] = [(int(x), int(y)) for y, x in zip(match_locations[0], match_locations[1])]
    matches.sort()
    return matches

def find_template_bounds(screenshot_array: np.ndarray, template_array: np.ndarray, threshold: float=0.999) -> tuple[int, int, int, int] | None:
    try:
        template_height: int
        template_width: int
        template_height, template_width = template_array.shape[:2]
        matches: list[tuple[int, int]] = find_all_matches(screenshot_array, template_array, threshold)
        if len(matches) != 2:
            print(f'[find_template_bounds] 需要找到 2 个标记，但找到 {len(matches)} 个')
            return None
        x1: int
        y1: int
        x2: int
        y2: int
        x1, y1 = matches[0]
        x2, y2 = matches[1]
        right1: int = x1 + template_width
        bottom1: int = y1 + template_height
        right2: int = x2 + template_width
        bottom2: int = y2 + template_height
        left: int = int(min(x1, x2))
        top: int = int(min(y1, y2))
        right: int = int(max(right1, right2))
        bottom: int = int(max(bottom1, bottom2))
        width: int = right - left
        height: int = bottom - top
        if width % 8 != 0 or height % 8 != 0:
            print(f'[find_template_bounds] 边界尺寸必须是 8 的倍数，但得到 {width} x {height}')
            return None
        return (left, top, right, bottom)
    except Exception as e:
        print(f'[find_template_bounds] 发生错误: {e}')
        return None
