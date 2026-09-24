"""读取单份 rotation，采集游戏基板后只求值一次，报告条件和拟执行宏。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import sleep

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from phantom.core.capture.contracts import CaptureResult  # noqa: E402
from phantom.core.capture.registry import Registry  # noqa: E402
from phantom.core.pixels import PixelDecoder  # noqa: E402
from phantom.core.rotation import Rotation, load_rotation  # noqa: E402


def describe_result(rotation: Rotation, result: CaptureResult) -> list[str]:
    if result.status.has_error:
        raise ValueError(f"截图失败：{result.status.description}")
    if result.image is None:
        raise ValueError("截图没有返回图像")
    decision = rotation.trial(PixelDecoder(result.image))
    lines = [f"当前 rotation：{rotation.profile.title} · 画布：{result.image.shape}"]
    lines.extend(f"{entry.title}：{value}" for entry, value in zip(rotation.conditions, decision.values))
    lines.append(f"命中第 {decision.rule_index} 条：{decision.rule.condition or '兜底'} · {decision.rule.annotate}")
    lines.append(f"拟执行宏：{decision.macro.name} · 键位：{decision.macro.key}（仅报告）" if decision.macro else "Idle：无动作")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rotation", nargs="?", type=Path, default=PROJECT_ROOT / "rotations/死亡骑士-鲜血.toml")
    args = parser.parse_args()
    print("演示内容：同帧解码条件并按优先级单次求值，只报告宏和键位，不发送按键。", flush=True)
    try:
        rotation = load_rotation(args.rotation)
        worker = Registry().create("gdi@dev", fps=15)
        print("3 秒后开始截图，采集 5 秒后用最后结果执行一次试运行。", flush=True)
        try:
            sleep(3)
            worker.start()
            sleep(5)
            result = worker.get_latest_result()
            if not worker.is_running:
                raise ValueError(result.status.description or "截图线程已结束")
        finally:
            worker.stop()
        print("\n".join(describe_result(rotation, result)))
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
