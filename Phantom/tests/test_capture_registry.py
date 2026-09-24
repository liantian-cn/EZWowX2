from pathlib import Path

import pytest

from phantom.core.capture.registry import CapturePluginError, Registry
from phantom.core.configuration import load_config
from phantom.main import main
from phantom.ui.app import PhantomApp

PLUGIN_SOURCE = """
import numpy as np
from phantom.core.capture.contracts import CaptureResult

class Plugin:
    def __init__(self, fps: float = 15) -> None:
        self.fps: float = fps
        self.is_running: bool = False

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def set_fps(self, fps: float = 15) -> None:
        self.fps = fps

    def get_latest_result(self) -> CaptureResult:
        return CaptureResult(np.full((20, 8, 3), int(self.fps), dtype=np.uint8))
"""


def install(root: Path, identifier: str, source: str = PLUGIN_SOURCE) -> None:
    directory = root / identifier
    directory.mkdir(parents=True)
    (directory / "capture.py").write_text(source, encoding="utf-8")


def test_exact_capture_selection_and_independent_instances(tmp_path: Path) -> None:
    install(tmp_path, "gdi@dev")
    install(tmp_path, "alternate@2.0", PLUGIN_SOURCE.replace("int(self.fps)", "99"))
    registry = Registry(tmp_path)
    first = registry.create(fps=7)
    other = registry.create("alternate@2.0", fps=8)
    second = registry.create(fps=9)
    assert first is not second and type(first) is type(second)
    for worker, brightness in ((first, 7), (other, 99), (second, 9)):
        image = worker.get_latest_result().image
        assert image is not None and (image == brightness).all()
    first.start()
    assert first.is_running and not second.is_running
    first.stop()
    assert not first.is_running
    with pytest.raises(CapturePluginError, match="alternate@1.0"):
        registry.create("alternate@1.0")


def test_same_identifier_in_different_roots(tmp_path: Path) -> None:
    install(tmp_path / "one", "example@1.0")
    install(tmp_path / "two", "example@1.0", PLUGIN_SOURCE.replace("int(self.fps)", "88"))
    first = Registry(tmp_path / "one").create("example@1.0")
    second = Registry(tmp_path / "two").create("example@1.0")
    assert type(first) is not type(second)
    first_image, second_image = first.get_latest_result().image, second.get_latest_result().image
    assert first_image is not None and second_image is not None
    assert (first_image == 15).all() and (second_image == 88).all()


@pytest.mark.parametrize("identifier", ["GDI@1.0", "gdi", "../gdi@dev", "gdi@1.1", "gdi@1"])
def test_invalid_or_missing_capture_never_falls_back(tmp_path: Path, identifier: str) -> None:
    install(tmp_path, "gdi@dev")
    with pytest.raises(CapturePluginError):
        Registry(tmp_path).create(identifier)


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        ("raise RuntimeError('broken import')", "broken import"),
        ("Plugin = 1", "Plugin 类"),
        (PLUGIN_SOURCE.replace("fps: float = 15) -> None:", ") -> None:", 1), "fps"),
        (PLUGIN_SOURCE.replace("def stop(self)", "def missing_stop(self)"), "stop"),
        (PLUGIN_SOURCE.replace("def start(self)", "def start(self, required)"), "required"),
        (PLUGIN_SOURCE.replace("self.is_running: bool = False", "self.is_running: bool = True"), "未启动"),
        (PLUGIN_SOURCE.replace("return CaptureResult(np.full((20, 8, 3), int(self.fps), dtype=np.uint8))", "return None"), "CaptureResult"),
    ],
)
def test_broken_capture_reports_plugin_and_cause(tmp_path: Path, source: str, reason: str) -> None:
    install(tmp_path, "broken@1.0", source)
    with pytest.raises(CapturePluginError, match=reason) as caught:
        Registry(tmp_path).create("broken@1.0")
    assert "broken@1.0" in str(caught.value)
    assert caught.value.__cause__ is not None


def test_config_selection_reaches_ui_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install(tmp_path / "plugins", "alternate@2.0")
    content = '[capture]\nplugin = "alternate@2.0"\nfps = 23\n'
    path = tmp_path / "phantom.toml"
    path.write_text(content, encoding="utf-8")
    registry = Registry(tmp_path / "plugins")
    monkeypatch.setattr("phantom.ui.app.CaptureRegistry", lambda: registry)
    app = PhantomApp(load_config(tmp_path))
    try:
        image = app.capture.get_latest_result().image
        assert image is not None and (image == 23).all()
        assert path.read_text(encoding="utf-8") == content
    finally:
        app.close_resources()


def test_bad_selection_exits_before_ui(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    content = '[capture]\nplugin = "missing@9.9"\n'
    path = tmp_path / "phantom.toml"
    path.write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def forbidden_run(self: PhantomApp) -> None:
        pytest.fail("invalid capture must fail before UI starts")

    monkeypatch.setattr(PhantomApp, "run", forbidden_run)
    with pytest.raises(SystemExit) as caught:
        main()
    assert caught.value.code == 1
    assert "missing@9.9" in capsys.readouterr().err
    assert path.read_text(encoding="utf-8") == content
