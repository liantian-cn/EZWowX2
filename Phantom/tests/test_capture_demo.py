from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from demo import demo
from phantom.core.capture.contracts import CaptureResult, CaptureStatus


@pytest.mark.parametrize("has_error", [False, True])
def test_saved_last_image_preserves_rgb_dtype_and_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, has_error: bool) -> None:
    monkeypatch.setattr(demo, "__file__", str(tmp_path / "demo.py"))
    # 有空间结构且三个通道不同的区域，避免全黑图掩盖通道或裁剪错误。
    image = np.arange(20 * 32 * 3, dtype=np.uint16).astype(np.uint8).reshape(20, 32, 3)
    status = CaptureStatus(has_error, "颜色校验失败" if has_error else "")
    output = demo.save_result(CaptureResult(image, status))
    restored = np.load(output / "result.npy", allow_pickle=False)
    assert restored.dtype == np.uint8 and restored.shape == (20, 32, 3)
    np.testing.assert_array_equal(restored, image)
    assert json.loads((output / "result.txt").read_text(encoding="utf-8")) == {"has_error": has_error, "description": status.description}

    # 随后无图的采集不能沿用前一次保存的图像。
    missing = demo.save_result(CaptureResult(status=CaptureStatus(True, "未定位")))
    assert missing != output
    assert not (missing / "result.npy").exists()
    assert json.loads((missing / "result.txt").read_text(encoding="utf-8"))["has_error"]
    np.testing.assert_array_equal(np.load(output / "result.npy", allow_pickle=False), image)
