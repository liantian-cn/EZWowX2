"""分别检查核心与非 Python 包名的精确版本插件，避免同名 condition 模块冲突。"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = sorted((root / "phantom/conditions").glob("*@*/condition.py"))
    sources += sorted((root / "phantom/captures").glob("*@*/capture.py"))
    sources += sorted((root / "phantom/keyboards").glob("*@*/keyboard.py"))
    commands = [[sys.executable, "-m", "mypy"]]
    commands.extend([sys.executable, "-m", "mypy", str(source)] for source in sources)
    failed = False
    for command in commands:
        if subprocess.run(command, cwd=root, check=False).returncode:
            failed = True
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
