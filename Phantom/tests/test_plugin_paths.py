"""验证插件命名软规则与精确加载的文件系统边界。"""

from pathlib import Path

import pytest

from phantom.core.capture.registry import Registry as CaptureRegistry
from phantom.core.condition.registry import Registry as ConditionRegistry

CONDITION_SOURCE = """
from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output

class Plugin(Condition):
    def __init__(self, args):
        super().__init__(Output("cell", value_type=float))

    def decode_value(self, cells, value_bars, icon_tiles, *, decoder):
        return 1.0

    def fallback_value(self):
        return 0.0
"""

CAPTURE_SOURCE = """
from phantom.core.capture.contracts import CaptureResult

class Plugin:
    def __init__(self, fps=15):
        self.is_running = False

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def set_fps(self, fps=15):
        pass

    def get_latest_result(self):
        return CaptureResult()
"""


def install(root: Path, identifier: str, kind: str) -> Path:
    directory = root / identifier
    directory.mkdir(parents=True)
    source = CONDITION_SOURCE if kind == "condition" else CAPTURE_SOURCE
    (directory / f"{kind}.py").write_text(source, encoding="utf-8")
    if kind == "condition":
        (directory / "template.lua").write_text("-- test template", encoding="utf-8")
    return directory


def create(root: Path, identifier: str, kind: str) -> object:
    if kind == "condition":
        return ConditionRegistry(root).create(identifier, {})
    return CaptureRegistry(root).create(identifier)


@pytest.mark.parametrize("kind", ["condition", "capture"])
@pytest.mark.parametrize("identifier", ["sample@dev", "author.sample@1", "Any name"])
@pytest.mark.parametrize("metadata", [None, "this is invalid TOML ["])
def test_safe_names_load_without_reading_metadata(tmp_path: Path, kind: str, identifier: str, metadata: str | None) -> None:
    directory = install(tmp_path, identifier, kind)
    if metadata is not None:
        (directory / "plugin.toml").write_text(metadata, encoding="utf-8")
    assert create(tmp_path, identifier, kind) is not None


@pytest.mark.parametrize("kind", ["condition", "capture"])
@pytest.mark.parametrize("identifier", ["", ".", "..", "../outside", "nested/../sample", "nested\\sample", "C:sample", "sample.", "sample "])
def test_reject_path_aliases(tmp_path: Path, kind: str, identifier: str) -> None:
    install(tmp_path, "sample", kind)
    with pytest.raises(ValueError, match="安全目录名"):
        create(tmp_path, identifier, kind)


@pytest.mark.parametrize("kind", ["condition", "capture"])
def test_reject_absolute_path_even_to_an_installed_plugin(tmp_path: Path, kind: str) -> None:
    directory = install(tmp_path, "sample", kind)
    with pytest.raises(ValueError, match="安全目录名"):
        create(tmp_path, str(directory.resolve()), kind)


@pytest.mark.parametrize("kind", ["condition", "capture"])
@pytest.mark.parametrize("identifier", ["sample@1.0", "author.sample@beta", "author.sample@1.0"])
def test_missing_exact_identifier_does_not_alias_or_fall_back(tmp_path: Path, kind: str, identifier: str) -> None:
    install(tmp_path, "author.sample@dev", kind)
    with pytest.raises(ValueError, match="缺少精确版本"):
        create(tmp_path, identifier, kind)


def symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")


@pytest.mark.parametrize("kind,member", [("condition", ""), ("capture", ""), ("condition", "condition.py"), ("condition", "template.lua"), ("capture", "capture.py")])
def test_resolved_escape_is_rejected_without_link_privileges(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, member: str) -> None:
    """隔离测试 resolve 后的越界判断；真实链接由另外的文件系统测试覆盖。"""
    root = tmp_path / "plugins"
    directory = install(root, "sample", kind)
    outside = install(tmp_path, "outside", kind)
    redirected = directory / member if member else directory
    destination = outside / member if member else outside
    original_resolve = Path.resolve

    def resolve(path: Path, strict: bool = False) -> Path:
        if path == redirected:
            return original_resolve(destination, strict=strict)
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="目录"):
        create(root, "sample", kind)


@pytest.mark.parametrize("kind", ["condition", "capture"])
def test_reject_plugin_directory_escape(tmp_path: Path, kind: str) -> None:
    outside = install(tmp_path, "outside", kind)
    root = tmp_path / "plugins"
    root.mkdir()
    symlink_or_skip(root / "sample", outside)
    with pytest.raises(ValueError, match="目录"):
        create(root, "sample", kind)


@pytest.mark.parametrize("kind,filename", [("condition", "condition.py"), ("condition", "template.lua"), ("capture", "capture.py")])
def test_reject_source_or_template_escape(tmp_path: Path, kind: str, filename: str) -> None:
    outside = install(tmp_path, "outside", kind)
    root = tmp_path / "plugins"
    directory = root / "sample"
    directory.mkdir(parents=True)
    for source in outside.iterdir():
        if source.name != filename:
            (directory / source.name).write_bytes(source.read_bytes())
    symlink_or_skip(directory / filename, outside / filename)
    with pytest.raises(ValueError, match="精确版本目录"):
        create(root, "sample", kind)


@pytest.mark.parametrize("source", ["Plugin = 1", "raise RuntimeError('broken import')"])
def test_condition_interface_errors_keep_context(tmp_path: Path, source: str) -> None:
    directory = install(tmp_path, "author.sample@dev", "condition")
    (directory / "condition.py").write_text(source, encoding="utf-8")
    with pytest.raises(ValueError, match="author.sample@dev") as caught:
        create(tmp_path, "author.sample@dev", "condition")
    assert caught.value.__cause__ is not None
