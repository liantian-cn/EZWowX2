"""等待 3 秒、采集 5 秒，展示同一帧的 Cell 亮度、ValueBar 比例及 IconTile hash。"""

from __future__ import annotations

import sys
from pathlib import Path
from time import sleep

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from phantom.core.capture.contracts import CaptureResult  # noqa: E402
from phantom.core.pixels import PixelDecoder  # noqa: E402


def describe_result(result: CaptureResult) -> list[str]:
    if result.status.has_error:
        raise ValueError(f"截图失败：{result.status.description}")
    if result.image is None:
        raise ValueError("截图没有返回图像")
    decoder = PixelDecoder(result.image)
    general_names = ("玩家职业", "专精索引", "启用", "爆发", "延迟")
    lines: list[str] = []
    for y in (1, 2):
        for x in range(1, 6):
            cell = decoder.getCell(x, y)
            name = general_names[x - 1] if y == 1 else "条件"
            lines.append(f"Cell x={x}, y={y} ({name}): mean={cell.mean:.6f}")
    bar = decoder.getValueBar(1, 2)
    lines.append(f"ValueBar x=1, width=2: ratio={bar.ratio:.6f}, percent={bar.percent:.6f}")
    for x in (1, 2):
        lines.append(f"IconTile x={x}: hash={decoder.getIconTile(x).hash}")
    return lines


def main() -> None:
    print("演示内容：解析游戏像素基板，输出 Cell(x=1–5, y=1–2) 的亮度、ValueBar(x=1, width=2) 的 ratio/percent 和 IconTile(x=1,2) 的 hash。", flush=True)
    # 与现有 demo 一样直接加载指定 GDI 版本，通用插件发现留待后续阶段。
    from phantom.core.capture.registry import Registry

    worker = Registry().create("gdi@dev", fps=15)
    print("3 秒后开始截图，采集 5 秒后输出最后结果。", flush=True)
    try:
        sleep(3)
        worker.start()
        sleep(5)
    finally:
        worker.stop()
    try:
        lines = describe_result(worker.get_latest_result())
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    print("\n".join(lines))


if __name__ == "__main__":
    main()
