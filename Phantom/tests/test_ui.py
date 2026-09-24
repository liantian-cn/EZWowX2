from __future__ import annotations

import asyncio
import re
from pathlib import Path
from threading import Event
from threading import enumerate as enumerate_threads

import numpy as np
import pytest
from textual.color import Color
from textual.widgets import Button, DataTable, Log, Static, TabbedContent

from phantom.core.capture.contracts import CaptureResult, CaptureStatus, RGBImage
from phantom.core.condition.contracts import Value
from phantom.core.configuration import AppConfig
from phantom.core.game import GameStatus
from phantom.core.generator import RotationGenerationResult, generate_rotations
from phantom.core.keyboard.contracts import KeyCombination
from phantom.core.rotation import Decision, Rotation
from phantom.core.runtime import RotationRuntime, RuntimeSnapshot
from phantom.ui.app import GameUpdated, PhantomApp
from phantom.ui.business_log import BusinessLog
from phantom.ui.capture import decode_general


class FakeCapture:
    def __init__(self) -> None:
        self.running: bool = False
        self.result: CaptureResult = CaptureResult()
        self.starts: int = 0
        self.stop_entered: Event = Event()
        self.stop_release: Event = Event()
        self.stop_release.set()

    @property
    def is_running(self) -> bool:
        return self.running

    def start(self) -> None:
        if not self.running:
            self.starts += 1
        self.running = True
        self.result = CaptureResult()

    def stop(self) -> None:
        self.stop_entered.set()
        assert self.stop_release.wait(5)
        self.running = False

    def set_fps(self, fps: float = 15) -> None:
        pass

    def get_latest_result(self) -> CaptureResult:
        return self.result


class FakeKeyboard:
    def __init__(self) -> None:
        self.sent: list[KeyCombination] = []

    def send(self, keys: KeyCombination) -> None:
        self.sent.append(keys)

    def close(self) -> None:
        pass


def general_image(values: tuple[int, ...] = (6, 1, 255, 0, 0)) -> RGBImage:
    image = np.zeros((20, 32, 3), dtype=np.uint8)
    for index, value in enumerate(values, start=1):
        image[0:4, index * 4 : index * 4 + 4] = value
    return image


def make_app(tmp_path: Path, capture: FakeCapture, game: bool = True) -> PhantomApp:
    return PhantomApp(AppConfig(tmp_path / "phantom.toml", log_max_lines=6), capture=capture, game_detector=lambda: GameStatus(game))


def test_decode_class_and_spec_purity_and_invalid_input() -> None:
    image = general_image()
    data = decode_general(CaptureResult(image))
    assert (data.width, data.height) == (32, 20)
    assert data.cells == (("6,6,6", "6"), ("1,1,1", "1"))
    image[1, 5] = (255, 0, 0)
    mixed = decode_general(CaptureResult(image))
    assert mixed.cells[0] == ("255,0,0", "—")
    assert data.cells[0] == ("6,6,6", "6")
    with pytest.raises(ValueError):
        decode_general(CaptureResult(image, CaptureStatus(True, "坏帧")))
    with pytest.raises(ValueError):
        decode_general(CaptureResult())
    with pytest.raises(ValueError):
        decode_general(CaptureResult(image[:, :12]))


def test_business_log_deduplicates_body_before_timestamp() -> None:
    lines: list[str] = []
    business_log = BusinessLog(lines.append)
    for message in ("A", "A", "B", "A", "first\nsecond"):
        business_log.log(message)
    assert len(lines) == 4
    assert all(re.match(r"^\[\d{2}:\d{2}:\d{2}\] ", line) for line in lines)
    assert lines[0][11:] == "A"
    assert lines[2][11:] == "A"
    assert len(lines[3].splitlines()) == 2


def test_monochrome_theme_is_applied(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path, FakeCapture())
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            theme = app.current_theme
            assert theme.name == "phantom-monochrome"
            assert theme.dark
            assert theme.primary == "#FFFFFF"
            assert app.screen.styles.background == Color.parse("#000000")
            assert app.query_one("#footer").styles.background == Color.parse("#111111")

    asyncio.run(scenario())


def test_tabs_keyboard_and_resizing_preserve_state(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = make_app(tmp_path, capture)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            assert not capture.running
            assert not app.query_one("#start", Button).disabled
            assert app.query_one("#generate", Button).disabled
            assert app.query_one("#footer").region.y == 45
            assert app.query_one("#footer").region.height == 1
            assert len(app.query_one("#footer").children) == 1
            pages = app.query_one("#pages", TabbedContent)
            for expected in ("general", "logs", "macros", "conditions", "overview"):
                await pilot.press("tab")
                assert pages.active == expected
            await pilot.press("shift+tab")
            assert pages.active == "conditions"
            await pilot.press("tab", "down", "space")
            assert app.collecting
            capture.result = CaptureResult(general_image())
            app.refresh_capture()
            await pilot.press("tab")
            await pilot.resize_terminal(119, 46)
            assert app.query_one("#size_notice").display
            assert not pages.display
            assert app.collecting
            await pilot.resize_terminal(140, 55)
            assert pages.display
            assert pages.active == "general"
            assert app.query_one("#footer").region.y == 54
            await pilot.press("shift+tab", "up", "enter")
            await pilot.pause()
            assert not app.collecting
            assert not capture.running
            await pilot.press("ctrl+q")
        assert not capture.running
        assert not any(thread.name == "phantom-game" for thread in enumerate_threads())

    asyncio.run(scenario())


def test_valid_failed_and_paused_data_never_reuse_old_frame(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = make_app(tmp_path, capture)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            await pilot.click("#start")
            table = app.query_one("#general_table", DataTable)
            capture.result = CaptureResult(general_image())
            app.refresh_capture()
            assert table.get_cell("0", "rgb") == "6,6,6"
            assert table.row_count == 2
            assert table.get_cell("1", "mean") == "1"
            assert all(table.get_cell(str(index), "display") == "" for index in range(2))
            capture.result = CaptureResult(general_image(), CaptureStatus(True, "校验失败"))
            app.refresh_capture()
            assert table.get_cell("0", "rgb") == "—"
            assert app.general_data is None
            capture.result = CaptureResult(general_image((3, 2, 0, 255, 255)))
            app.refresh_capture()
            assert table.get_cell("0", "mean") == "3"
            assert table.get_cell("1", "mean") == "2"
            await pilot.pause()
            assert any("采集已恢复" in line for line in app.query_one(Log).lines)
            await pilot.click("#stop")
            await pilot.pause()
            app.refresh_capture()
            assert table.get_cell("0", "rgb") == "—"
            assert all(table.get_cell(str(index), "display") == "" for index in range(2))
            await pilot.click("#start")
            app.refresh_capture()
            assert table.get_cell("0", "rgb") == "—"

    asyncio.run(scenario())


def test_game_loss_pauses_and_return_requires_manual_start(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = make_app(tmp_path, capture, game=False)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            assert app.query_one("#start", Button).disabled
            app.start_collection()
            assert capture.starts == 0
            app.post_message(GameUpdated(GameStatus(True)))
            await pilot.pause()
            await pilot.click("#start")
            capture.result = CaptureResult(general_image())
            app.refresh_capture()
            app.post_message(GameUpdated(GameStatus(False)))
            await pilot.pause()
            assert not app.collecting
            assert app.general_data is None
            assert app.query_one("#start", Button).disabled
            app.post_message(GameUpdated(GameStatus(True)))
            await pilot.pause()
            assert not app.collecting
            assert capture.starts == 1

    asyncio.run(scenario())


def test_slow_stop_keeps_ui_responsive_and_blocks_restart(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = make_app(tmp_path, capture)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            await pilot.click("#start")
            capture.stop_release.clear()
            try:
                await pilot.click("#stop")
                assert capture.stop_entered.is_set()
                assert app.stopping
                assert app.query_one("#start", Button).disabled
                await pilot.press("tab")
                assert app.query_one("#pages", TabbedContent).active == "general"
                app.start_collection()
                assert capture.starts == 1
            finally:
                capture.stop_release.set()
            await pilot.pause()
            assert not app.stopping
            assert not capture.running

    asyncio.run(scenario())


def test_capture_termination_pauses_and_explicit_restart_works(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = make_app(tmp_path, capture)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            await pilot.click("#start")
            capture.result = CaptureResult(status=CaptureStatus(True, "GDI 失败"))
            capture.running = False
            app.refresh_capture()
            await pilot.pause()
            assert not app.collecting
            assert app.capture_error == "GDI 失败"
            assert not app.query_one("#start", Button).disabled
            await pilot.click("#start")
            assert capture.starts == 2
            assert app.collecting

    asyncio.run(scenario())


@pytest.mark.parametrize("capture_running", [True, False])
def test_shutdown_refresh_ignores_removed_widgets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capture_running: bool) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = make_app(tmp_path, capture)
        close_all = app._close_all
        refreshed_during_shutdown = False

        async def close_all_and_refresh() -> None:
            nonlocal refreshed_during_shutdown
            await close_all()
            # Textual 已卸载屏幕，但尚未调用应用的 on_unmount。
            assert not app.is_running
            assert app.collecting and not app.closing
            capture.running = capture_running
            app.refresh_capture()
            refreshed_during_shutdown = True

        monkeypatch.setattr(app, "_close_all", close_all_and_refresh)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            await pilot.click("#start")
            assert app.collecting

        assert refreshed_during_shutdown
        assert app.closing and not app.collecting
        assert capture.stop_entered.is_set() and not capture.running
        assert not any(thread.name.startswith("phantom-") for thread in enumerate_threads())

    asyncio.run(scenario())


def test_logs_bound_history_even_when_tab_hidden(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path, FakeCapture())
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            for index in range(12):
                app.business_log.log(f"事件 {index}")
                app.business_log.log(f"事件 {index}")
            await pilot.pause()
            log = app.query_one("#business_log", Log)
            assert len(log.lines) == 6
            assert log.lines[0].endswith("事件 6")
            assert log.lines[-1].endswith("事件 11")
            await pilot.press("tab", "tab")
            assert log.region.height > 20
            assert log.max_lines == 6

    asyncio.run(scenario())


def rotation_app(tmp_path: Path, capture: FakeCapture, *, game: bool = False, keyboard: FakeKeyboard | None = None) -> PhantomApp:
    root = Path(__file__).resolve().parents[1]
    rotation_path = tmp_path / "blood.toml"
    rotation_path.write_bytes((root / "tests/fixtures/engine-rotation.toml").read_bytes())
    executable = tmp_path / "_retail_/Wow.exe"
    executable.parent.mkdir()
    executable.touch()
    (tmp_path / "phantom.toml").write_text('[rotations]\n"deathknight.blood" = "blood.toml"\n', encoding="utf-8")
    return PhantomApp(
        AppConfig(tmp_path / "phantom.toml", rotation_paths={"deathknight.blood": rotation_path}, wow_executable=executable),
        capture=capture,
        game_detector=lambda: GameStatus(game),
        keyboard=keyboard if keyboard is not None else FakeKeyboard(),
    )


def test_generation_without_game_uses_startup_snapshot_and_recovers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        app = rotation_app(tmp_path, FakeCapture())
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            assert app.query_one("#start", Button).disabled
            assert not app.query_one("#generate", Button).disabled
            table = app.query_one("#condition_table", DataTable)
            assert table.row_count == 0
            assert app.rotation is None and len(app.rotations) == 1
            loaded = app.rotations
            app.generate_addon()
            assert app.generating
            assert app.query_one("#generate", Button).disabled
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not app.generating
            assert (tmp_path / "_retail_/Interface/AddOns/Phantom/Phantom.toc").is_file()
            # 配置文件编辑只能在重启后生效，生成不能绕过该边界重读文件。
            loaded[0].path.write_text("invalid TOML =", encoding="utf-8")
            app.generate_addon()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not app.rotation_error and app.rotations is loaded

            def fail_generate(rotations: tuple[Rotation, ...], executable: Path, addon_name: str) -> RotationGenerationResult:
                raise ValueError("生成失败测试")

            with monkeypatch.context() as context:
                context.setattr("phantom.ui.app.generate_rotations", fail_generate)
                app.generate_addon()
                await app.workers.wait_for_complete()
                await pilot.pause()
                assert "生成失败测试" in app.rotation_error
                assert app.rotations is loaded
                assert not app.query_one("#generate", Button).disabled
            app.generate_addon()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not app.rotation_error and app.rotations is loaded
            assert table.row_count == 0

    asyncio.run(scenario())


def test_condition_values_same_frame_and_mismatch_clear(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = rotation_app(tmp_path, capture, game=True)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            app.on_game_updated(GameUpdated(GameStatus(True)))
            app.start_collection()
            assert app.query_one("#generate", Button).disabled
            table = app.query_one("#condition_table", DataTable)
            image = np.zeros((20, 36, 3), dtype=np.uint8)
            image[:4, 4:8] = 6
            image[:4, 8:12] = 1
            image[:4, 12:16] = 255
            for index, brightness in enumerate((85, 3, 255, 205, 255, 102, 255), 1):
                image[4:8, 4 * index : 4 * index + 4] = brightness
            image[8:12, 4:6] = [255, 0, 0]
            image[8:12, 6:10] = 255
            image[8:12, 14:16] = [255, 0, 0]
            capture.result = CaptureResult(image.copy(), sequence=1)
            await pilot.pause(0.15)
            app.refresh_capture()
            assert [table.get_cell(str(i), "value") for i in range(10)] == ["40.0", "3", "1", "True", "2.5", "0.0", "40.0", "True", "True", "False"]
            assert table.get_cell("8", "name") == "插件启用"
            assert table.get_cell("9", "name") == "正在延迟"
            assert app.decision is not None and app.decision.rule_index == 2
            assert app.decision.macro is not None
            assert app.decision.macro.name == "灵界打击"
            await pilot.pause()
            log = app.query_one("#business_log", Log)
            assert any("已派发宏：灵界打击" in line for line in log.lines)
            count = len(log.lines)
            app.refresh_capture()
            await pilot.pause()
            assert len(log.lines) == count
            image[:4, 8:12] = 2
            capture.result = CaptureResult(image.copy(), sequence=2)
            await pilot.pause(0.15)
            app.refresh_capture()
            assert table.row_count == 0 and app.rotation is None
            assert app.rotation_state == "无匹配"
            assert app.decision is None
            await pilot.pause()
            image[:4, 8:12] = 1
            capture.result = CaptureResult(image.copy(), sequence=3)
            await pilot.pause(0.15)
            app.refresh_capture()
            assert table.get_cell("0", "value") == "40.0"
            # 同一帧使全部规则为假，不能保留此前命中的宏。
            image[4:8, 8:12] = 0
            image[4:8, 12:16] = 0
            image[4:8, 20:24] = 0
            image[4:8, 28:32] = 0
            capture.result = CaptureResult(image.copy(), sequence=4)
            await pilot.pause(0.15)
            app.refresh_capture()
            assert app.decision is not None and app.decision.macro is None
            assert app.decision.rule.macro == "Idle"
            capture.result = CaptureResult(status=CaptureStatus(True, "截图不可用"))
            await pilot.pause(0.15)
            app.refresh_capture()
            assert app.decision is None
            app.stop_collection()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert table.row_count == 0
            assert not app.query_one("#generate", Button).disabled

    asyncio.run(scenario())


def test_condition_value_width_tracks_hash_and_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = rotation_app(tmp_path, capture, game=True)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            rotation = app.rotations[0]
            snapshot = RuntimeSnapshot(capture=CaptureResult(general_image(), sequence=1), rotation=rotation, specialization=(6, 1))
            app.runtime = RotationRuntime(capture, FakeKeyboard(), rotation, 15)
            monkeypatch.setattr(app.runtime, "get_latest_result", lambda: snapshot)
            capture.running = app.collecting = True
            app.query_one("#pages", TabbedContent).active = "conditions"
            app.refresh_capture()
            # 先完成占位值的列宽测量，确保测试覆盖后续更新而非首次建行。
            await pilot.pause()
            table = app.query_one("#condition_table", DataTable)
            assert table.get_cell("0", "value") == "—"

            icon_hash = "0123456789abcdef"
            hashes = [f"{index:016x}" for index in range(10)]
            values: tuple[Value, ...] = (icon_hash, [], [*hashes], "")
            for value in values:
                decision = Decision((value, *([False] * (len(rotation.conditions) - 1))), len(rotation.rules), rotation.rules[-1], None)
                snapshot = RuntimeSnapshot(capture=snapshot.capture, decision=decision, rotation=rotation, specialization=(6, 1))
                app.refresh_capture()
                await pilot.pause()
                assert table.get_cell("0", "value") == str(value)
                assert table.ordered_columns[-1].content_width >= len(str(value))
                assert all(row.height == 1 for row in table.rows.values())
                if value == icon_hash:
                    assert icon_hash in "\n".join(table.render_line(y).text for y in range(table.size.height))
                elif value == hashes:
                    assert table.max_scroll_x > 0
                    table.scroll_to(x=table.max_scroll_x, animate=False)
                    await pilot.pause()
                    assert hashes[-1] in "\n".join(table.render_line(y).text for y in range(table.size.height))

            app.stop_collection()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert table.get_cell("0", "value") == "—"

    asyncio.run(scenario())


def execution_frame(sequence: int) -> CaptureResult:
    image = np.zeros((20, 36, 3), dtype=np.uint8)
    image[:4, 4:8] = 6
    image[:4, 8:12] = 1
    image[:4, 12:16] = 255
    image[4:8, 20:24] = 255
    return CaptureResult(image, sequence=sequence)


def test_multiple_rotations_footer_generation_and_manual_pause(tmp_path: Path) -> None:
    directory = tmp_path / "rotations"
    directory.mkdir()
    (directory / "blood.toml").write_bytes(Path("tests/fixtures/engine-rotation.toml").read_bytes())
    mage_title = "火焰法师" * 40
    (directory / "fire.toml").write_text(
        f'''schema_version = 1
uuid = "660e8400-e29b-41d4-a716-446655440000"
[profile]
title = "{mage_title}"
description = "测试多份路由与长名称"
unit_class = "MAGE"
unit_spec = 2
[[conditions]]
title = "启用"
plugin = "enable@dev"
[[macros]]
name = "法师动作"
macro_text = "/say 测试"
[[rotation]]
condition = "启用"
macro = "法师动作"
''',
        encoding="utf-8",
    )
    config_path = tmp_path / "phantom.toml"
    config_path.write_text("[rotations]\n", encoding="utf-8")
    executable = tmp_path / "_retail_/Wow.exe"
    executable.parent.mkdir()
    executable.touch()

    async def scenario() -> None:
        capture, keyboard = FakeCapture(), FakeKeyboard()
        app = PhantomApp(AppConfig(config_path, wow_executable=executable), capture=capture, game_detector=lambda: GameStatus(True), keyboard=keyboard)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            assert len(app.rotations) == 2 and app.rotation is None
            assert "尚未识别" in str(app.query_one("#status_line", Static).render())
            app.generate_addon()
            await app.workers.wait_for_complete()
            await pilot.pause()
            toc = (executable.parent / "Interface/AddOns/Phantom/Phantom.toc").read_text(encoding="utf-8")
            references = [line for line in toc.splitlines() if line and not line.startswith("##")]
            assert sum(name.startswith("deathknight_blood\\") for name in references) == len(app.rotations[0].conditions) + 1
            assert sum(name.startswith("mage_fire\\") for name in references) == len(app.rotations[1].conditions) + 1

            app.start_collection()
            capture.result = execution_frame(1)
            await pilot.pause(0.2)
            app.refresh_capture()
            table = app.query_one("#condition_table", DataTable)
            assert app.rotation is not None and app.rotation.profile.unit_class == "DEATHKNIGHT"
            assert table.row_count == 10
            assert "引擎测试循环" in str(app.query_one("#status_line", Static).render())

            mage = execution_frame(2)
            assert mage.image is not None
            mage.image[:4, 4:8] = 8
            mage.image[:4, 8:12] = 2
            capture.result = mage
            await pilot.pause(0.2)
            app.refresh_capture()
            assert app.rotation is not None and app.rotation.profile.title == mage_title
            assert table.row_count == 1 and table.get_cell("0", "value") == "True"
            assert app.decision is not None and app.decision.macro is not None and app.decision.macro.name == "法师动作"
            assert mage_title in str(app.query_one("#status_line", Static).render())
            assert app.query_one("#footer").region.height == 1
            await pilot.resize_terminal(70, 30)
            assert app.query_one("#footer").region.height == 1
            await pilot.resize_terminal(120, 46)

            app.stop_collection()
            await app.workers.wait_for_complete()
            await pilot.pause()
            sent = len(keyboard.sent)
            capture.result = execution_frame(3)
            app.refresh_capture()
            await pilot.pause(0.15)
            assert not app.collecting and len(keyboard.sent) == sent
            assert app.rotation is not None and app.rotation.profile.title == mage_title
            assert app.decision is None and table.get_cell("0", "value") == "—"
            assert "程序：已暂停" in str(app.query_one("#status_line", Static).render())

            app.start_collection()
            missing = execution_frame(4)
            assert missing.image is not None
            missing.image[:4, 8:12] = 3
            capture.result = missing
            await pilot.pause(0.2)
            app.refresh_capture()
            assert app.collecting and app.rotation is None and table.row_count == 0
            assert "无匹配" in str(app.query_one("#status_line", Static).render())
            assert len(keyboard.sent) == sent
            capture.result = execution_frame(5)
            await pilot.pause(0.2)
            app.refresh_capture()
            assert app.rotation is not None and table.row_count == 10 and len(keyboard.sent) == sent + 1

    asyncio.run(scenario())


def test_keyboard_error_requires_manual_restart(tmp_path: Path) -> None:
    class FailingKeyboard(FakeKeyboard):
        fail: bool = True

        def send(self, keys: KeyCombination) -> None:
            super().send(keys)
            if self.fail:
                raise OSError("发送失败测试")

    async def scenario() -> None:
        capture, keyboard = FakeCapture(), FailingKeyboard()
        app = rotation_app(tmp_path, capture, game=True, keyboard=keyboard)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            app.start_collection()
            capture.result = execution_frame(1)
            await pilot.pause(0.25)
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not app.collecting and "发送失败测试" in app.capture_error
            assert not capture.is_running and app.decision is None
            keyboard.fail = False
            await pilot.pause(0.1)
            assert len(keyboard.sent) == 1
            app.start_collection()
            capture.result = execution_frame(1)
            await pilot.pause(0.2)
            assert len(keyboard.sent) == 2 and app.decision is not None
            app.stop_collection()
            await app.workers.wait_for_complete()
            await pilot.pause()
            # A later collection-only start must not reuse the prior runtime snapshot.
            app.rotations = ()
            app.start_collection()
            capture.result = CaptureResult(general_image())
            await pilot.pause(0.15)
            assert app.runtime is None and app.decision is None
            assert app.general_data is not None

    asyncio.run(scenario())


def test_capture_failure_clears_previously_matched_rotation(tmp_path: Path) -> None:
    async def scenario() -> None:
        capture = FakeCapture()
        app = rotation_app(tmp_path, capture, game=True)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            app.start_collection()
            capture.result = execution_frame(1)
            await pilot.pause(0.2)
            app.refresh_capture()
            assert app.rotation is not None and app.decision is not None
            capture.result = CaptureResult(status=CaptureStatus(True, "截图线程失败"))
            capture.running = False
            app.refresh_capture()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not app.collecting and app.rotation is None and app.decision is None
            assert app.query_one("#condition_table", DataTable).row_count == 0
            assert "引擎测试循环" not in str(app.query_one("#status_line", Static).render())
            assert "尚未识别" in str(app.query_one("#status_line", Static).render())

    asyncio.run(scenario())


def test_keyboard_release_does_not_block_ui_stop(tmp_path: Path) -> None:
    class SlowKeyboard(FakeKeyboard):
        def __init__(self) -> None:
            super().__init__()
            self.entered: Event = Event()
            self.release: Event = Event()

        def send(self, keys: KeyCombination) -> None:
            super().send(keys)
            self.entered.set()
            assert self.release.wait(5)

    async def scenario() -> None:
        capture, keyboard = FakeCapture(), SlowKeyboard()
        app = rotation_app(tmp_path, capture, game=True, keyboard=keyboard)
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            app.start_collection()
            capture.result = execution_frame(1)
            try:
                await pilot.pause(0.15)
                assert keyboard.entered.is_set()
                app.stop_collection()
                capture.result = execution_frame(2)
                await pilot.press("tab")
                assert app.query_one("#pages", TabbedContent).active == "general"
                assert app.stopping and app.query_one("#start", Button).disabled
                assert app.decision is None
            finally:
                keyboard.release.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert not capture.is_running and len(keyboard.sent) == 1
            assert not app.stopping and app.decision is None
        assert not any(thread.name == "phantom-rotation" for thread in enumerate_threads())

    asyncio.run(scenario())


def test_slow_generation_exit_waits_for_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    entered = Event()
    release = Event()

    def slow_generate(rotations: tuple[Rotation, ...], executable: Path, addon_name: str) -> RotationGenerationResult:
        entered.set()
        assert release.wait(5)
        return generate_rotations(rotations, executable, addon_name)

    monkeypatch.setattr("phantom.ui.app.generate_rotations", slow_generate)

    async def scenario() -> None:
        app = rotation_app(tmp_path, FakeCapture())
        async with app.run_test(size=(120, 46)) as pilot:
            await pilot.pause()
            app.generate_addon()
            try:
                await pilot.pause()
                assert entered.is_set()
                assert app.query_one("#start", Button).disabled
                await pilot.press("tab")
                assert app.query_one("#pages", TabbedContent).active == "general"
                await app.action_quit()
                assert app.closing
            finally:
                release.set()
            await app.workers.wait_for_complete()
        assert (tmp_path / "_retail_/Interface/AddOns/Phantom/Phantom.toc").is_file()

    asyncio.run(scenario())
