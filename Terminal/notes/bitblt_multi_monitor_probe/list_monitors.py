from __future__ import annotations

import importlib.util
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROBE_PATH = BASE_DIR / "probe_bitblt_multi_monitor.py"


def load_probe_module():
    spec = importlib.util.spec_from_file_location(PROBE_PATH.stem, PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_summary_lines(monitors: list[dict[str, int]], virtual_desktop: dict[str, int]) -> list[str]:
    lines = [f"screen_count: {len(monitors)}"]
    for monitor in monitors:
        lines.append(
            f"monitor_{monitor['index']}: "
            f"left={monitor['left']} top={monitor['top']} right={monitor['right']} bottom={monitor['bottom']} "
            f"width={monitor['width']} height={monitor['height']}"
        )
    lines.append(
        "virtual_desktop: "
        f"left={virtual_desktop['left']} top={virtual_desktop['top']} right={virtual_desktop['right']} bottom={virtual_desktop['bottom']} "
        f"width={virtual_desktop['width']} height={virtual_desktop['height']}"
    )
    return lines


def main() -> None:
    probe_module = load_probe_module()
    monitors = probe_module.enumerate_monitors()
    virtual_desktop = probe_module.build_virtual_desktop_info(monitors)
    for line in build_summary_lines(monitors, virtual_desktop):
        print(line)


if __name__ == "__main__":
    main()
