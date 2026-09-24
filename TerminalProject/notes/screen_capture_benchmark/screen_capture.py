import mss
import numpy as np


_SCT = mss.mss()
_MONITOR = _SCT.monitors[1]
_REGION = {
    "left": _MONITOR["left"],
    "top": _MONITOR["top"],
    "width": _MONITOR["width"],
    "height": _MONITOR["height"],
}


def capture_rgb() -> np.ndarray:
    screenshot = _SCT.grab(_REGION)
    pixels = np.array(screenshot, dtype=np.uint8)
    return pixels[:, :, :3][:, :, ::-1]


def validate_capture_not_black(frame: np.ndarray) -> bool:
    return bool(np.any(frame))
