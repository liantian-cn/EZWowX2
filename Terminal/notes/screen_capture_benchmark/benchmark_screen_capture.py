from __future__ import annotations

import importlib.util
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TEST_DURATION_SECONDS = 60
SCRIPT_FILES = [
    "screen_capture.py",
    "screen_capture_small.py",
    "screen_capture_optimized.py",
    "screen_capture_optimized_small.py",
]


def load_module(script_name: str):
    module_path = BASE_DIR / script_name
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_result(
    script_name: str,
    captures: int,
    black_failures: int,
    elapsed_seconds: float,
    cpu_seconds: float,
) -> dict[str, float | int | str]:
    captures_per_second = captures / elapsed_seconds if elapsed_seconds else 0.0
    average_cpu_percent = (cpu_seconds / elapsed_seconds * 100.0) if elapsed_seconds else 0.0
    return {
        "script": script_name,
        "captures": captures,
        "black_failures": black_failures,
        "elapsed_seconds": elapsed_seconds,
        "cpu_seconds": cpu_seconds,
        "captures_per_second": captures_per_second,
        "average_cpu_percent": average_cpu_percent,
    }


def benchmark_module(script_name: str) -> dict[str, float | int | str]:
    module = load_module(script_name)
    started_at = time.perf_counter()
    cpu_started_at = time.process_time()
    captures = 0
    black_failures = 0

    while True:
        now = time.perf_counter()
        if now - started_at >= TEST_DURATION_SECONDS:
            break

        frame = module.capture_rgb()
        captures += 1

        if not module.validate_capture_not_black(frame):
            black_failures += 1

    elapsed = time.perf_counter() - started_at
    cpu_seconds = time.process_time() - cpu_started_at
    return build_result(
        script_name=script_name,
        captures=captures,
        black_failures=black_failures,
        elapsed_seconds=elapsed,
        cpu_seconds=cpu_seconds,
    )


def main():
    print(f"Benchmark duration per script: {TEST_DURATION_SECONDS} seconds")
    print("")

    results = [benchmark_module(script_name) for script_name in SCRIPT_FILES]

    for result in results:
        print(f"script: {result['script']}")
        print(f"captures: {result['captures']}")
        print(f"black_failures: {result['black_failures']}")
        print(f"elapsed_seconds: {result['elapsed_seconds']:.2f}")
        print(f"cpu_seconds: {result['cpu_seconds']:.2f}")
        print(f"captures_per_second: {result['captures_per_second']:.2f}")
        print(f"average_cpu_percent: {result['average_cpu_percent']:.2f}")
        print("")


if __name__ == "__main__":
    main()
