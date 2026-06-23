import mss
import numpy as np


CAPTURE_WIDTH = 336
CAPTURE_HEIGHT = 112

_SCT = mss.mss()
_MONITOR = _SCT.monitors[1]
_REGION = {
    "left": _MONITOR["left"] + _MONITOR["width"] - CAPTURE_WIDTH,
    "top": _MONITOR["top"],
    "width": CAPTURE_WIDTH,
    "height": CAPTURE_HEIGHT,
}


def capture_rgb() -> np.ndarray:
    screenshot = _SCT.grab(_REGION)
    pixels = np.array(screenshot, dtype=np.uint8)
    return pixels[:, :, :3][:, :, ::-1]


def validate_capture_not_black(frame: np.ndarray) -> bool:
    return bool(np.any(frame))
