from __future__ import annotations

from collections.abc import Callable
from threading import Event
from time import monotonic, sleep

import numpy as np
import pytest

from phantom.core.capture.contracts import Bounds, CaptureResult, RGBImage
from phantom.core.capture.imaging import find_bounds, markers_valid, validate_colors
from phantom.core.capture.worker import CaptureSession, ThreadCaptureWorker


def board(width: int = 32, flash: int = 0) -> RGBImage:
    image = np.full((20, width, 3), 73, dtype=np.uint8)
    # 独立按 Lua 的行列奇偶规则构造，避免测试从被测代码复制模板。
    for y in range(4):
        for x in range(4):
            color = (15, 25, 20) if (x // 2 + y // 2) % 2 == 0 else (25, 15, 20)
            image[y, x] = color
            image[16 + y, width - 4 + x] = color
    for y, color in enumerate(((0, 255, 255), (255, 0, 255), (255, 255, 0), (flash,) * 3)):
        image[(y + 1) * 4 : (y + 2) * 4, :4] = color
    for y, color in enumerate(((127, 127, 127), (0, 0, 255), (0, 255, 0), (255, 0, 0))):
        image[y * 4 : (y + 1) * 4, -4:] = color
    return image


def desktop(image: RGBImage, x: int = 12, y: int = 8) -> RGBImage:
    full = np.full((80, 160, 3), 31, dtype=np.uint8)
    full[y : y + 20, x : x + image.shape[1]] = image
    return full


class ImageBackend:
    def __init__(self, frames: list[RGBImage], origin: tuple[int, int] = (-80, -30)) -> None:
        self.frames: list[RGBImage] = frames
        self.origin: tuple[int, int] = origin
        self.requests: list[Bounds] = []
        self.closed: Event = Event()
        self.index: int = 0

    def desktop_bounds(self) -> Bounds:
        image = self.frames[0]
        x, y = self.origin
        return Bounds(x, y, x + image.shape[1], y + image.shape[0])

    def capture(self, bounds: Bounds) -> RGBImage:
        self.requests.append(bounds)
        image = self.frames[min(self.index, len(self.frames) - 1)]
        self.index += 1
        relative = bounds.translated(-self.origin[0], -self.origin[1])
        return image[relative.top : relative.bottom, relative.left : relative.right]

    def close(self) -> None:
        self.closed.set()


def await_result(worker: ThreadCaptureWorker, predicate: Callable[[CaptureResult], bool]) -> CaptureResult:
    deadline = monotonic() + 3
    while monotonic() < deadline:
        result = worker.get_latest_result()
        if predicate(result):
            return result
        sleep(0.005)
    pytest.fail("worker 没有在期限内交付预期图像结果")


def test_sequence_tracks_publication_not_pixels_or_snapshot_reads() -> None:
    worker = ThreadCaptureWorker(lambda: ImageBackend([desktop(board())]), fps=20)
    worker.start()
    try:
        first = await_result(worker, lambda result: result.image is not None)
        assert first.sequence is not None
        copied = worker.get_latest_result()
        assert copied.sequence is not None and copied.sequence >= first.sequence
        second = await_result(worker, lambda result: result.sequence != first.sequence)
        assert second.sequence is not None and second.sequence > first.sequence
        np.testing.assert_array_equal(first.image, second.image)
    finally:
        worker.stop()
    last = worker.get_latest_result()
    assert worker.get_latest_result().sequence == last.sequence
    worker.start()
    try:
        restarted = await_result(worker, lambda result: result.image is not None)
        assert restarted.sequence is not None and last.sequence is not None
        assert restarted.sequence > last.sequence
    finally:
        worker.stop()


@pytest.mark.parametrize("width", [8, 12, 32, 152])
@pytest.mark.parametrize("flash", [0, 255])
def test_full_image_localization_and_exact_crop(width: int, flash: int) -> None:
    expected = board(width, flash)
    image = desktop(expected, x=0, y=60)
    bounds, status = find_bounds(image)
    assert not status.has_error
    assert bounds == Bounds(0, 60, width, 80)
    assert bounds is not None
    region = image[bounds.top : bounds.bottom, bounds.left : bounds.right]
    np.testing.assert_array_equal(region, expected)
    assert not validate_colors(region).has_error


def test_missing_ambiguous_and_debug_images_are_not_accepted() -> None:
    blank = np.zeros((80, 160, 3), dtype=np.uint8)
    assert find_bounds(blank)[0] is None
    multiple = desktop(board())
    multiple[45:65, 90:122] = board()
    assert find_bounds(multiple)[0] is None
    assert find_bounds(multiple)[1].has_error
    debug = board()
    for y in range(4):
        for x in range(4):
            color = (0, 255, 0) if (x // 2 + y // 2) % 2 == 0 else (255, 0, 0)
            debug[y, x] = color
            debug[16 + y, 28 + x] = color
    assert find_bounds(desktop(debug))[0] is None
    enlarged = np.repeat(np.repeat(board(), 8, axis=0), 8, axis=1)
    assert find_bounds(enlarged)[0] is None


@pytest.mark.parametrize("shape", [(0, 0, 3), (19, 32, 3), (20, 7, 3), (20, 32), (20, 32, 4)])
def test_unusable_input_images(shape: tuple[int, ...]) -> None:
    image = np.zeros(shape, dtype=np.uint8)
    assert find_bounds(image)[1].has_error
    assert not markers_valid(image)
    assert validate_colors(image).has_error


@pytest.mark.parametrize("position", [(0, 0), (3, 3), (16, 28), (19, 31)])
def test_marker_single_pixel_corruption_rejects_frame(position: tuple[int, int]) -> None:
    image = board()
    image[position] = (16, 25, 20)
    assert not markers_valid(image)
    assert find_bounds(desktop(image))[0] is None


def test_invalid_board_geometry_and_noncontiguous_rgb() -> None:
    assert find_bounds(desktop(board(31)))[0] is None
    image = board()
    padded = np.zeros((20, 64, 3), dtype=np.uint8)
    padded[:, ::2] = image
    assert not padded[:, ::2].flags.c_contiguous
    assert not validate_colors(padded[:, ::2]).has_error
    assert find_bounds(padded[:, ::2])[0] == Bounds(0, 0, 32, 20)


@pytest.mark.parametrize("x,y", [(0, 4), (0, 8), (0, 12), (28, 12), (28, 8), (28, 4), (28, 0), (0, 16)])
def test_calibration_ignores_edges_but_rejects_one_bad_center_pixel(x: int, y: int) -> None:
    image = board()
    image[y, x : x + 4] = (123, 45, 67)
    image[y + 3, x : x + 4] = (123, 45, 67)
    image[y : y + 4, x] = (123, 45, 67)
    image[y : y + 4, x + 3] = (123, 45, 67)
    assert not validate_colors(image).has_error
    image[y + 1, x + 1] = (123, 45, 67)
    assert validate_colors(image).has_error


def test_flash_must_be_uniform_and_rgb_order_is_significant() -> None:
    mixed = board()
    mixed[17, 1] = 255
    assert validate_colors(mixed).has_error
    gray = board(flash=127)
    assert validate_colors(gray).has_error
    swapped = board()[:, :, ::-1].copy()
    assert not markers_valid(swapped)
    # 角标仍正确时，色块的 R/B 互换也必须失败。
    swapped[:4, :4] = board()[:4, :4]
    swapped[-4:, -4:] = board()[-4:, -4:]
    assert validate_colors(swapped).has_error


def test_image_sequence_search_lock_color_failure_recovery_and_relocation() -> None:
    blank = np.zeros((80, 160, 3), dtype=np.uint8)
    good = board()
    bad = good.copy()
    bad[5, 1] = 17
    backend = ImageBackend([blank, desktop(good), desktop(bad), desktop(good), desktop(good, x=80, y=35), desktop(good, x=80, y=35)])
    session = CaptureSession(backend)
    missing = session.capture_next()
    assert missing.image is None and missing.status.has_error
    valid = session.capture_next()
    assert not valid.status.has_error
    assert session.bounds == Bounds(-68, -22, -36, -2)
    np.testing.assert_array_equal(valid.image, good)
    invalid = session.capture_next()
    assert invalid.status.has_error
    np.testing.assert_array_equal(invalid.image, bad)
    assert session.bounds is not None
    assert not session.capture_next().status.has_error
    assert session.capture_next().status.has_error
    assert session.bounds is None
    relocated = session.capture_next()
    assert not relocated.status.has_error
    assert session.bounds == Bounds(0, 5, 32, 25)
    assert backend.requests == [backend.desktop_bounds(), backend.desktop_bounds(), Bounds(-68, -22, -36, -2), Bounds(-68, -22, -36, -2), Bounds(-68, -22, -36, -2), backend.desktop_bounds()]


def test_worker_latest_frame_ownership_stop_and_restart() -> None:
    first, last = board(), board(flash=255)
    first[:, 4:8] = 42
    last[:, 4:8] = 84
    backends: list[ImageBackend] = []

    def factory() -> ImageBackend:
        backend = ImageBackend([desktop(first), desktop(last)])
        backends.append(backend)
        return backend

    worker = ThreadCaptureWorker(factory, fps=1)
    assert not worker.is_running
    try:
        worker.start()
        assert worker.is_running
        worker.start()
        original = await_result(worker, lambda result: result.image is not None)
        assert original.image is not None
        np.testing.assert_array_equal(original.image, first)
        # 修改读者自己的副本不会破坏 worker 当前结果。
        original.image[:] = 9
        np.testing.assert_array_equal(worker.get_latest_result().image, first)
        started = monotonic()
        worker.set_fps(100)
        newest = await_result(worker, lambda result: result.image is not None and result.image[0, 4, 0] == 84)
        assert monotonic() - started < 0.8  # FPS 更新应唤醒原来的一秒等待。
        assert newest.image is not None and newest.image.flags.c_contiguous
        assert len(backends) == 1
        worker.set_fps(0.1)
        stopped = monotonic()
        worker.stop()
        assert monotonic() - stopped < 1  # stop 不等待十秒周期结束。
        assert not worker.is_running
        worker.stop()
        assert backends[0].closed.is_set()
        np.testing.assert_array_equal(worker.get_latest_result().image, last)
        worker.start()
        restarted = await_result(worker, lambda result: result.image is not None)
        np.testing.assert_array_equal(restarted.image, first)
        assert len(backends) == 2
        assert backends[1].requests == [backends[1].desktop_bounds()]
    finally:
        worker.stop()


def test_worker_delivers_capture_error_after_a_real_image_and_closes() -> None:
    class FailingBackend(ImageBackend):
        def capture(self, bounds: Bounds) -> RGBImage:
            if self.index > 0:
                raise OSError("模拟 GDI 截图失败")
            return super().capture(bounds)

    backend = FailingBackend([desktop(board())])
    worker = ThreadCaptureWorker(lambda: backend, fps=100)
    try:
        worker.start()
        assert backend.closed.wait(3)
        result = worker.get_latest_result()
        assert result.status.has_error and result.status.description
        assert result.image is None
        assert backend.requests == [backend.desktop_bounds()]
    finally:
        worker.stop()
