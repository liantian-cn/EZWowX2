"""
Summary:
    对最新截图逐帧执行一次解码、优先级决策及键盘发送。
Description:
    独立线程串行处理业务，不积压旧帧；界面只读取该轮结果，不另行求值。
    临时图像不可用跳过本轮；插件及未预期异常结束本次运行，必须手动重新启动。
Key Variables:
    RuntimeSnapshot: 同一轮的截图、职业专精、所选 rotation、决策和错误。
    RotationRuntime._stop: 停止新一轮派发并唤醒等待。
Change Log:
    2026-09-19: Changed 按同帧职业专精自动路由已加载集合，无匹配时保持检测且不发键。
    2026-09-14: Added 第 15 步新帧驱动持续执行及停止生命周期。
"""

from dataclasses import dataclass
from threading import Event, Lock, Thread

from phantom.core.capture.contracts import CaptureResult, CaptureWorker
from phantom.core.keyboard.contracts import Keyboard
from phantom.core.pixels import PixelDecoder
from phantom.core.rotation import Decision, Rotation
from phantom.core.validation import PositiveNumber


@dataclass(frozen=True)
class RuntimeSnapshot:
    capture: CaptureResult = CaptureResult()
    decision: Decision | None = None
    error: str = ""
    fatal: bool = False
    rotation: Rotation | None = None
    specialization: tuple[int, int] | None = None


def decode_specialization(decoder: PixelDecoder) -> tuple[int, int]:
    """职业与专精均须为严格灰度纯色，不能把彩色像素均值当成路由值。"""
    values: list[int] = []
    for x in (1, 2):
        cell = decoder.getCell(x, 1)
        value = int(cell.inner[0, 0, 0])
        if value == 0 or not bool((cell.inner == value).all()):
            raise ValueError("无法识别截图职业或专精")
        values.append(value)
    return values[0], values[1]


class RotationRuntime:
    def __init__(self, capture: CaptureWorker, keyboard: Keyboard, rotation: Rotation | tuple[Rotation, ...], fps: float) -> None:
        self.capture: CaptureWorker = capture
        self.keyboard: Keyboard = keyboard
        rotations = (rotation,) if isinstance(rotation, Rotation) else rotation
        self.rotations: dict[tuple[int, int], Rotation] = {}
        for item in rotations:
            key = (item.profile.unit_class_id, item.profile.unit_spec)
            if key in self.rotations:
                raise ValueError("同一职业专精不能运行多份 rotation")
            self.rotations[key] = item
        self._interval: float = 1 / PositiveNumber().validate(fps, "runtime fps")
        self._stop: Event = Event()
        self._gate: Lock = Lock()
        self._lock: Lock = Lock()
        self._latest: RuntimeSnapshot = RuntimeSnapshot()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("每次运行必须创建新的 RotationRuntime")
        self._thread = Thread(target=self._run, name="phantom-rotation", daemon=False)
        self._thread.start()

    def request_stop(self) -> None:
        # 这里只关闭派发入口，不等待已开始的插件调用，避免阻塞 UI。
        with self._gate:
            self._stop.set()

    def stop(self) -> None:
        self.request_stop()
        if self._thread is not None:
            self._thread.join()

    def get_latest_result(self) -> RuntimeSnapshot:
        with self._lock:
            result = self._latest
            capture = result.capture
            return RuntimeSnapshot(CaptureResult(None if capture.image is None else capture.image.copy(), capture.status, capture.sequence), result.decision, result.error, result.fatal, result.rotation, result.specialization)

    def _publish(self, result: RuntimeSnapshot) -> None:
        with self._lock:
            self._latest = result

    def _run(self) -> None:
        last_sequence: int | None = None
        result = CaptureResult()
        try:
            while not self._stop.is_set():
                running = self.capture.is_running
                result = self.capture.get_latest_result()
                if not running:
                    raise RuntimeError(result.status.description or "截图线程已结束")
                if result.image is None or result.status.has_error:
                    self._publish(RuntimeSnapshot(result))
                elif result.sequence is None:
                    raise RuntimeError("截图插件未提供帧序号，无法执行新帧循环")
                elif type(result.sequence) is not int or result.sequence < 1:
                    raise RuntimeError("截图帧序号必须为正整数")
                elif last_sequence is not None and result.sequence < last_sequence:
                    raise RuntimeError("截图帧序号倒退")
                elif result.sequence != last_sequence:
                    last_sequence = result.sequence
                    rotation = None
                    specialization = None
                    try:
                        decoder = PixelDecoder(result.image)
                        specialization = decode_specialization(decoder)
                        rotation = self.rotations.get(specialization)
                        if rotation is None:
                            raise ValueError(f"当前职业专精没有可用 rotation：职业 {specialization[0]}，专精 {specialization[1]}")
                        decision = rotation.trial(decoder)
                    except (ValueError, IndexError) as error:
                        self._publish(RuntimeSnapshot(result, error=str(error), rotation=rotation, specialization=specialization))
                    else:
                        # 锁内完成派发接纳；停止后不再接纳新组合。
                        with self._gate:
                            if self._stop.is_set():
                                break
                        if decision.macro is not None:
                            self.keyboard.send(decision.macro.keys)
                        if not self._stop.is_set():
                            self._publish(RuntimeSnapshot(result, decision, rotation=rotation, specialization=specialization))
                self._stop.wait(self._interval)
        except Exception as error:
            self._publish(RuntimeSnapshot(result, error=f"运行失败：{error}", fatal=True))
        finally:
            try:
                self.keyboard.close()
            except Exception as error:
                previous = self.get_latest_result()
                self._publish(RuntimeSnapshot(result, error=previous.error + f" 关闭键盘失败：{error}", fatal=True))
