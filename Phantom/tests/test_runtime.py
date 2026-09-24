from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep

import numpy as np
import pytest

from phantom.core.capture.contracts import CaptureResult, CaptureStatus
from phantom.core.capture.registry import Registry as CaptureRegistry
from phantom.core.keyboard.contracts import KeyCombination, parse_key
from phantom.core.keyboard.registry import Registry as KeyboardRegistry
from phantom.core.macro_keys import MACRO_KEYS
from phantom.core.pixels import PixelDecoder
from phantom.core.rotation import Rotation, load_rotation, parse_macros, parse_rules
from phantom.core.runtime import RotationRuntime


def wait_for(predicate: Callable[[], bool]) -> None:
    deadline = monotonic() + 3
    while not predicate():
        assert monotonic() < deadline, "runtime did not publish expected result"
        sleep(0.005)


def rotation_copy(tmp_path: Path) -> Rotation:
    path = tmp_path / "blood.toml"
    path.write_bytes(Path("tests/fixtures/engine-rotation.toml").read_bytes())
    return load_rotation(path)


def frame(sequence: int, enabled: int = 255, delaying: int = 0) -> CaptureResult:
    image = np.zeros((20, 36, 3), dtype=np.uint8)
    for index, value in enumerate((6, 1, enabled, 0, delaying), 1):
        image[:4, index * 4 : index * 4 + 4] = value
    image[4:8, 20:24] = 255  # 死神的抚摩 ready; other rules do not match.
    return CaptureResult(image, sequence=sequence)


class Capture:
    def __init__(self) -> None:
        self.result: CaptureResult = CaptureResult()
        self.is_running: bool = True

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def set_fps(self, fps: float = 15) -> None:
        pass

    def get_latest_result(self) -> CaptureResult:
        return self.result


class Keyboard:
    def __init__(self) -> None:
        self.sent: list[KeyCombination] = []
        self.closed: bool = False
        self.entered: Event = Event()
        self.release: Event = Event()
        self.release.set()
        self.fail: bool = False

    def send(self, keys: KeyCombination) -> None:
        self.sent.append(keys)
        self.entered.set()
        assert self.release.wait(3)
        if self.fail:
            raise OSError("keyboard failed")

    def close(self) -> None:
        self.closed = True


def test_new_frames_idle_recovery_and_same_decision(tmp_path: Path) -> None:
    capture, keyboard = Capture(), Keyboard()
    runtime = RotationRuntime(capture, keyboard, rotation_copy(tmp_path), 100)
    runtime.start()
    try:
        capture.result = frame(1)
        wait_for(lambda: runtime.get_latest_result().decision is not None)
        decision = runtime.get_latest_result().decision
        assert decision is not None and decision.macro is not None
        assert keyboard.sent == [decision.macro.keys]
        sleep(0.05)
        assert len(keyboard.sent) == 1
        capture.result = frame(2)  # identical pixels, distinct capture
        wait_for(lambda: len(keyboard.sent) == 2)
        capture.result = frame(3, enabled=0)
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 3)
        decision = runtime.get_latest_result().decision
        assert decision is not None and decision.macro is None
        assert decision.rule_index == 1
        capture.result = CaptureResult(status=CaptureStatus(True, "bad frame"), sequence=4)
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 4)
        assert runtime.get_latest_result().decision is None
        capture.result = frame(5, delaying=255)
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 5)
        assert len(keyboard.sent) == 2
        capture.result = frame(6)
        wait_for(lambda: len(keyboard.sent) == 3)
    finally:
        runtime.stop()
    assert keyboard.closed


def test_routes_rotation_and_decision_from_same_frame(tmp_path: Path) -> None:
    first = rotation_copy(tmp_path)
    macros = parse_macros([{"name": "法师测试", "macro_text": "/say 法师"}])
    second = replace(first, profile=replace(first.profile, title="火焰法师", unit_class="MAGE", unit_class_id=8, unit_spec=2), conditions=(), macros=macros, rules=parse_rules([{"condition": "True", "macro": "法师测试"}], {}, {"法师测试"}))
    capture, keyboard = Capture(), Keyboard()
    runtime = RotationRuntime(capture, keyboard, (first, second), 100)
    runtime.start()
    try:
        capture.result = frame(1)
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 1)
        snapshot = runtime.get_latest_result()
        assert snapshot.rotation is first and snapshot.specialization == (6, 1)
        assert snapshot.decision is not None and len(snapshot.decision.values) == len(first.conditions)

        changed = frame(2)
        assert changed.image is not None
        changed.image[:4, 4:8] = 8
        changed.image[:4, 8:12] = 2
        capture.result = changed
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 2)
        snapshot = runtime.get_latest_result()
        assert snapshot.rotation is second and snapshot.specialization == (8, 2)
        assert snapshot.decision is not None and snapshot.decision.macro == macros[0]
        assert snapshot.decision.values == () and len(keyboard.sent) == 2
        assert snapshot.capture.image is not None
        snapshot.capture.image[:] = 0
        assert runtime.get_latest_result().specialization == (8, 2)
        assert changed.image[0, 4, 0] == 8

        missing = frame(3)
        assert missing.image is not None
        missing.image[:4, 8:12] = 3
        capture.result = missing
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 3)
        snapshot = runtime.get_latest_result()
        assert snapshot.rotation is None and snapshot.decision is None
        assert snapshot.specialization == (6, 3) and snapshot.error and not snapshot.fatal
        assert len(keyboard.sent) == 2

        invalid = frame(4)
        assert invalid.image is not None
        invalid.image[:4, 4:8] = (5, 6, 7)  # 均值为职业 6 的纯彩色不是合法路由。
        capture.result = invalid
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 4)
        snapshot = runtime.get_latest_result()
        assert snapshot.rotation is None and snapshot.specialization is None and snapshot.decision is None
        assert len(keyboard.sent) == 2

        capture.result = frame(5)
        wait_for(lambda: runtime.get_latest_result().capture.sequence == 5)
        assert runtime.get_latest_result().rotation is first and len(keyboard.sent) == 3
    finally:
        runtime.stop()


def test_runtime_rejects_duplicate_specialization(tmp_path: Path) -> None:
    rotation = rotation_copy(tmp_path)
    with pytest.raises(ValueError, match="同一职业专精"):
        RotationRuntime(Capture(), Keyboard(), (rotation, rotation), 100)


@pytest.mark.parametrize("index", [0, 65, 121, 147])
def test_runtime_sends_automatically_assigned_key(tmp_path: Path, index: int) -> None:
    # 隔离条件布局，只验证已冻结的自动键位确实传给键盘后端。
    macros = parse_macros([{"name": f"宏{number}", "macro_text": "/say 测试", "bind_key": False, "key": "ALT-F4"} for number in range(148)])
    rules = parse_rules([{"condition": "True", "macro": macros[index].name}], {}, {macro.name for macro in macros})
    rotation = replace(rotation_copy(tmp_path), conditions=(), macros=macros, rules=rules)
    capture, keyboard = Capture(), Keyboard()
    capture.result = frame(1)
    runtime = RotationRuntime(capture, keyboard, rotation, 100)
    runtime.start()
    try:
        wait_for(lambda: runtime.get_latest_result().decision is not None)
        assert keyboard.sent == [parse_key(MACRO_KEYS[index])]
        decision = runtime.get_latest_result().decision
        assert decision is not None and decision.macro == macros[index]
    finally:
        runtime.stop()


def test_stop_waits_for_release_and_drops_backlog(tmp_path: Path) -> None:
    capture, keyboard = Capture(), Keyboard()
    keyboard.release.clear()
    capture.result = frame(1)
    runtime = RotationRuntime(capture, keyboard, rotation_copy(tmp_path), 100)
    runtime.start()
    stopped = Event()

    def stop_runtime() -> None:
        runtime.stop()
        stopped.set()

    stopper = Thread(target=stop_runtime)
    try:
        assert keyboard.entered.wait(3)
        capture.result = frame(2)
        runtime.request_stop()
        stopper.start()
        assert not stopped.wait(0.05)
    finally:
        keyboard.release.set()
        runtime.stop()
        if stopper.ident is not None:
            stopper.join()
    assert len(keyboard.sent) == 1 and keyboard.closed
    # Restart is a new run, so the latest frame may be considered again.
    restarted = RotationRuntime(capture, keyboard, rotation_copy(tmp_path), 100)
    restarted.start()
    try:
        wait_for(lambda: len(keyboard.sent) == 2)
    finally:
        restarted.stop()


def test_send_failure_stops_without_retry(tmp_path: Path) -> None:
    capture, keyboard = Capture(), Keyboard()
    keyboard.fail = True
    capture.result = frame(1)
    runtime = RotationRuntime(capture, keyboard, rotation_copy(tmp_path), 100)
    runtime.start()
    try:
        wait_for(lambda: runtime.get_latest_result().fatal)
        assert "keyboard failed" in runtime.get_latest_result().error
        capture.result = frame(2)
        sleep(0.04)
        assert len(keyboard.sent) == 1
    finally:
        runtime.stop()


def test_state_fallback_and_undeclared_burst(tmp_path: Path) -> None:
    rotation = rotation_copy(tmp_path)
    result = frame(1)
    assert result.image is not None
    result.image[:4, 16:20] = 123  # burst is not referenced by the example
    assert rotation.trial(PixelDecoder(result.image)).macro is not None
    result.image[1, 13] = 254
    decision = rotation.trial(PixelDecoder(result.image))
    assert decision.macro is not None
    assert decision.values[-2:] == (True, False)
    ungated = replace(rotation, rules=rotation.rules[1:])
    assert ungated.trial(PixelDecoder(result.image)).macro is not None


def test_duplicate_condition_name_rejected_before_write(tmp_path: Path) -> None:
    path = tmp_path / "blood.toml"
    source = Path("tests/fixtures/engine-rotation.toml").read_text(encoding="utf-8")
    source = source.replace('title = "符文能量"', 'title = "插件启用"')
    path.write_text(source, encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="条件标题"):
        load_rotation(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("sequence", [None, 0, -1, True])
def test_runtime_rejects_unusable_frame_identity(tmp_path: Path, sequence: int | None) -> None:
    capture, keyboard = Capture(), Keyboard()
    capture.result = replace(frame(1), sequence=sequence)
    runtime = RotationRuntime(capture, keyboard, rotation_copy(tmp_path), 100)
    runtime.start()
    try:
        wait_for(lambda: runtime.get_latest_result().fatal)
        assert not keyboard.sent
    finally:
        runtime.stop()


def test_exact_capture_and_keyboard_plugins_in_continuous_loop(tmp_path: Path) -> None:
    capture_directory = tmp_path / "captures/test.capture@dev"
    keyboard_directory = tmp_path / "keyboards/test.keyboard@dev"
    capture_directory.mkdir(parents=True)
    keyboard_directory.mkdir(parents=True)
    # Exact-loaded synthetic producer uses the real shared capture worker and pixel protocol.
    (capture_directory / "capture.py").write_text(
        """
import numpy as np
from phantom.core.capture.contracts import Bounds
from phantom.core.capture.worker import ThreadCaptureWorker
class Backend:
    def desktop_bounds(self): return Bounds(0,0,36,20)
    def capture(self, bounds):
        image = np.zeros((20,36,3), dtype=np.uint8)
        for y in range(4):
            for x in range(4):
                color = (15,25,20) if (x//2+y//2)%2==0 else (25,15,20)
                image[y,x] = color
                image[16+y,32+x] = color
        for y,color in enumerate(((0,255,255),(255,0,255),(255,255,0),(0,0,0))):
            image[(y+1)*4:(y+2)*4,:4] = color
        for y,color in enumerate(((127,127,127),(0,0,255),(0,255,0),(255,0,0))):
            image[y*4:(y+1)*4,-4:] = color
        for x,value in enumerate((6,1,255,0,0),1): image[:4,x*4:x*4+4] = value
        image[4:8,20:24] = 255
        return image
    def close(self): pass
class Plugin(ThreadCaptureWorker):
    def __init__(self, fps=15): super().__init__(Backend, fps)
""",
        encoding="utf-8",
    )
    (keyboard_directory / "keyboard.py").write_text(
        """
class Plugin:
    def __init__(self): self.sent = []; self.closed = False
    def send(self, keys): self.sent.append(keys)
    def close(self): self.closed = True
""",
        encoding="utf-8",
    )
    capture = CaptureRegistry(tmp_path / "captures").create("test.capture@dev", fps=40)
    keyboard = KeyboardRegistry(tmp_path / "keyboards").create("test.keyboard@dev")
    runtime = RotationRuntime(capture, keyboard, rotation_copy(tmp_path), 100)
    capture.start()
    runtime.start()
    try:
        wait_for(lambda: len(getattr(keyboard, "sent")) >= 3)
        snapshot = runtime.get_latest_result()
        assert snapshot.decision is not None and snapshot.decision.macro is not None
        assert snapshot.decision.macro.name == "死神的抚摩"
        assert not snapshot.capture.status.has_error
        assert snapshot.capture.sequence is not None
    finally:
        runtime.stop()
        capture.stop()
    assert getattr(keyboard, "closed")
