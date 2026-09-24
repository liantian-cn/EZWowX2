from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output, Region, Value
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.generator import render
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.rotation import ConditionEntry, Rotation, load_rotation


def example(tmp_path: Path) -> Rotation:
    path = tmp_path / "rotation.toml"
    path.write_bytes(Path("tests/fixtures/engine-rotation.toml").read_bytes())
    return load_rotation(path)


def frame() -> PixelDecoder:
    pixels = np.zeros((20, 36, 3), dtype=np.uint8)
    pixels[:4, 4:8] = 6
    pixels[:4, 8:12] = 1
    pixels[4:8, 20:24] = 255  # Ready spell in the example.
    return PixelDecoder(pixels)


@pytest.mark.parametrize("name,x,fallback", [("enable", 3, True), ("in_burst", 4, False), ("delaying", 5, False)])
def test_state_plugins_read_existing_pixels_and_fallback(name: str, x: int, fallback: bool) -> None:
    plugin = Registry().create(f"{name}@dev", {})
    assert allocate([plugin]) == 28
    assert plugin.layout() == {"output_type": "none", "regions": []}
    assert plugin.generate_lua("instance") == ""
    decoder = frame()
    for brightness, expected in ((0, False), (255, True), (127, fallback)):
        decoder.pix_array[:4, x * 4 : x * 4 + 4] = brightness
        assert plugin.value(*plugin.raw_value(decoder), decoder=decoder) is expected
    decoder.pix_array[:4, x * 4 : x * 4 + 4] = 255
    decoder.pix_array[1, x * 4 + 1] = (255, 0, 0)
    with pytest.raises(ValueError):
        plugin.decode_value([], [], [], decoder=decoder)
    assert plugin.value([], [], [], decoder=decoder) is fallback
    decoder.pix_array[:4, x * 4 : x * 4 + 4] = (255, 0, 0)
    with pytest.raises(ValueError):
        plugin.decode_value([], [], [], decoder=decoder)
    assert plugin.value([], [], [], decoder=decoder) is fallback
    tiny = PixelDecoder(np.zeros((20, 12, 3), dtype=np.uint8))
    assert plugin.value([], [], [], decoder=tiny) is fallback
    with pytest.raises(ValueError):
        Registry().create(f"{name}@dev", {"x": x})


class Combined(Condition):
    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        return [str(cells[0].mean), str(decoder.getCell(3, 1).mean), str(decoder.getValueBar(1, 1).ratio), decoder.getIconTile(1).hash or "empty"]

    def fallback_value(self) -> Value:
        return ["fallback"]


def test_same_decoder_across_instances_and_new_frames(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rotation = example(tmp_path)
    plugins: list[Condition] = [Combined(Output("cell", value_type=str, value_shape="list")) for _ in range(2)]
    allocate(plugins)
    rotation = replace(rotation, conditions=tuple(ConditionEntry(f"reader{index}", "test", plugin) for index, plugin in enumerate(plugins)))
    current = frame()
    original = Combined.decode_value
    seen: list[int] = []

    def observe(self: Combined, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        assert decoder is current
        seen.append(id(decoder))
        return original(self, cells, value_bars, icon_tiles, decoder=decoder)

    monkeypatch.setattr(Combined, "decode_value", observe)
    previous = rotation.values(current)
    assert previous == [["0.0", "0.0", "0.0", "empty"]] * 2
    current = frame()
    current.pix_array[4:8, 4:12] = 42
    current.pix_array[:4, 12:16] = 255
    current.pix_array[8:12, 4:12] = 255
    current.pix_array[12:20, 4:12] = (10, 20, 30)
    icon_hash = current.getIconTile(1).hash
    assert rotation.values(current) == [["42.0", "255.0", "1.0", icon_hash]] * 2
    assert len(seen) == 4 and seen[0] == seen[1] and seen[2] == seen[3] and seen[0] != seen[2]
    assert previous == [["0.0", "0.0", "0.0", "empty"]] * 2


def test_allocated_bounds_fail_before_any_plugin_decodes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rotation = example(tmp_path)
    invalid = Combined(Output("cell", value_type=str, value_shape="list"))
    invalid.freeze((Region(100, 2),))
    rotation = replace(rotation, conditions=(*rotation.conditions, ConditionEntry("invalid", "test", invalid)))
    calls: list[str] = []

    def unexpected(*args: object, **kwargs: object) -> Value:
        calls.append("decode")
        return False

    monkeypatch.setattr(Condition, "value", unexpected)
    with pytest.raises(ValueError, match="请求区域"):
        rotation.values(frame())
    assert calls == []


@pytest.mark.parametrize("output", [Output("none", 0, bool), Output("cell", value_type=bool)])
@pytest.mark.parametrize("template", [None, "", "addonTable.visits = (addonTable.visits or 0) + 1"])
def test_optional_lua_independent_of_layout(tmp_path: Path, output: Output, template: str | None) -> None:
    directory = tmp_path / "plugins/test@dev"
    directory.mkdir(parents=True)
    source = f"""
from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
class Plugin(Condition):
    def __init__(self, args):
        super().__init__(Output({output.output_type!r}, {output.output_count}, bool))
    def decode_value(self, cells, value_bars, icon_tiles, *, decoder):
        return decoder.getCell(3, 1).is_white
    def fallback_value(self):
        return False
"""
    (directory / "condition.py").write_text(source, encoding="utf-8")
    if template is not None:
        (directory / "template.lua").write_text(template, encoding="utf-8")
    plugin = Registry(directory.parent).create("test@dev", {})
    decoder = frame()
    with pytest.raises(ValueError):
        plugin.raw_value(decoder)
    with pytest.raises(ValueError):
        plugin.generate_lua("instance")
    allocate([plugin])
    with pytest.raises(ValueError, match="已冻结"):
        plugin.freeze(plugin.regions)
    assert plugin.value(*plugin.raw_value(decoder), decoder=decoder) is False
    decoder.pix_array[:4, 12:16] = 255
    assert plugin.value(*plugin.raw_value(decoder), decoder=decoder) is True
    rotation = replace(example(tmp_path), conditions=(ConditionEntry("reader", "test@dev", plugin),), macros=())
    files = {name: source for name, source in render(rotation, "Test").items() if name.startswith("deathknight_blood/")}
    assert len(files) == 2
    name, generated = next(iter(files.items()))
    assert f"uuid: {Path(name).stem}\n" in generated
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('UnitClass = function() return "", "DEATHKNIGHT" end; C_SpecializationInfo = {GetSpecialization=function() return 1 end}')
    run: Any = lua.eval('function(source) local addon={visits=0}; assert(loadstring(source))("Test", addon); return addon.visits end')
    assert run(generated) == (1 if template else 0)
    assert "\ndo\n" not in generated
    if not template:
        assert generated.endswith("local addonName, addonTable = ...\n\n")


def test_none_output_validation_and_mixed_layout() -> None:
    for count in (1, -1, True):
        with pytest.raises(ValueError):
            Output("none", count)
    with pytest.raises(ValueError):
        Output("none", 0, widths=(1,))
    with pytest.raises(ValueError):
        Output("cell", 0)
    reader = Registry().create("enable@dev", {})
    cell = Registry().create("spell_gcd@dev", {})
    assert allocate([reader, cell]) == 28
    assert cell.regions == (Region(1, 2),)
    assert reader.regions == ()


def test_zero_regions_still_validate_fallback_before_freezing() -> None:
    invalid = Combined(Output("none", 0, bool))
    with pytest.raises(ValueError, match="兜底"):
        invalid.freeze(())


def test_existing_template_errors_are_not_treated_as_optional(tmp_path: Path) -> None:
    directory = tmp_path / "test@dev"
    directory.mkdir()
    (directory / "condition.py").write_bytes(Path("phantom/conditions/enable@dev/condition.py").read_bytes())
    template = directory / "template.lua"
    template.mkdir()
    with pytest.raises(ValueError, match="template.lua"):
        Registry(tmp_path).create("test@dev", {})
    template.rmdir()
    template.write_text("local unknown = {{missing}}", encoding="utf-8")
    plugin = Registry(tmp_path).create("test@dev", {})
    allocate([plugin])
    with pytest.raises(ValueError, match="模板缺少参数"):
        plugin.generate_lua("instance")


@pytest.mark.parametrize("name", ["插件启用", "正在延迟", "爆发开启"])
def test_old_implicit_names_rejected_without_rewriting(tmp_path: Path, name: str) -> None:
    rotation = example(tmp_path)
    source = rotation.path.read_text(encoding="utf-8")
    start = source.index('[[conditions]]\ntitle = "插件启用"')
    end = source.index("[[macros]]", start)
    source = (source[:start] + source[end:]).replace("not 插件启用 or 正在延迟", name)
    rotation.path.write_text(source, encoding="utf-8")
    before = rotation.path.read_bytes()
    with pytest.raises(ValueError, match="未知条件"):
        load_rotation(rotation.path)
    assert rotation.path.read_bytes() == before


def test_renamed_duplicate_and_omitted_states(tmp_path: Path) -> None:
    rotation = example(tmp_path)
    source = rotation.path.read_text(encoding="utf-8").replace("插件启用", "允许执行").replace("正在延迟", "等待中")
    source = source.replace("[[macros]]", '[[conditions]]\ntitle = "另一开关"\nplugin = "enable@dev"\n\n[[conditions]]\ntitle = "爆发开启"\nplugin = "in_burst@dev"\n\n[[macros]]', 1)
    rotation.path.write_text(source, encoding="utf-8")
    rotation = load_rotation(rotation.path)
    assert rotation.board_width == 36
    assert [entry.title for entry in rotation.conditions[-4:]] == ["允许执行", "等待中", "另一开关", "爆发开启"]
    assert rotation.conditions[-4].instance is not rotation.conditions[-2].instance
    files = {name: source for name, source in render(rotation, "Test").items() if name.startswith("deathknight_blood/")}
    assert len(files) == len(rotation.conditions) + 1
    # 同插件不同声明不去重，未被表达式引用的状态实例也占独立文件。
    condition_sources = list(files.values())[:-1]
    assert all(source.endswith("local addonName, addonTable = ...\n\n") for source in condition_sources[-4:])
    assert len(set(condition_sources[-4:])) == 4
    decoder = frame()
    assert rotation.trial(decoder).macro is None
    decoder.pix_array[:4, 12:16] = 255
    decision = rotation.trial(decoder)
    assert decision.macro is not None and decision.values[-4:] == (True, False, True, False)
    decoder.pix_array[:4, 12:24] = 127
    decision = rotation.trial(decoder)
    assert decision.macro is not None and decision.values[-4:] == (True, False, True, False)
    # With no state plugins declared, those pixels never gate the remaining rules.
    omitted = replace(rotation, conditions=rotation.conditions[:-4], rules=rotation.rules[1:])
    decoder.pix_array[:4, 12:24] = 0
    assert omitted.trial(decoder).macro is not None
