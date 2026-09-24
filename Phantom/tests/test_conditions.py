import math

import numpy as np
import pytest

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output, Value
from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar


def empty_decoder() -> PixelDecoder:
    return PixelDecoder(np.zeros((20, 44, 3), dtype=np.uint8))


def cell(brightness: int) -> Cell:
    return Cell(1, 2, np.full((4, 4, 3), brightness, dtype=np.uint8))


@pytest.mark.parametrize(
    ("name", "args", "brightness", "expected"),
    [
        ("player_primary_power", {"max_power": 120}, 255, 120.0),
        ("player_primary_power", {"max_power": 120}, 85, 40.0),
        ("player_health_pct", {}, 0, 0.0),
        ("player_health_pct", {}, 255, 100.0),
        ("spec_power_rune", {}, 6, 6),
        ("spec_power_rune", {}, 0, 0),
        ("spec_power_rune", {}, 7, 0),
        ("spell_usable", {"spell_ids": [49998]}, 255, True),
        ("spell_overlay", {"spell_ids": [50841, 50842]}, 0, False),
        ("spell_overlay", {"spell_ids": [50842]}, 127, False),
    ],
)
def test_scalar_decode(name: str, args: dict[str, object], brightness: int, expected: Value) -> None:
    plugin = Registry().create(f"{name}@dev", args)
    allocate([plugin])
    result = plugin.value([cell(brightness)], [], [], decoder=empty_decoder())
    assert result == expected
    assert type(result) is type(expected)
    assert plugin.value([], [], [], decoder=empty_decoder()) == plugin.fallback_value()
    damaged = np.full((4, 4, 3), 255, dtype=np.uint8)
    damaged[1, 1] = [255, 0, 0]
    assert plugin.value([Cell(1, 2, damaged)], [], [], decoder=empty_decoder()) == plugin.fallback_value()


@pytest.mark.parametrize("name", ["spell_cooldown", "spell_gcd"])
@pytest.mark.parametrize(("brightness", "seconds"), [(255, 0), (205, 2.5), (155, 5), (130, 17.5), (105, 30), (80, 92.5), (55, 155), (30, 255), (0, 375)])
def test_cooldown_segments(name: str, brightness: int, seconds: float) -> None:
    args: dict[str, object] = {"spell_ids": [195292], "ignore_gcd": True} if name == "spell_cooldown" else {}
    plugin = Registry().create(f"{name}@dev", args)
    allocate([plugin])
    assert plugin.value([cell(brightness)], [], [], decoder=empty_decoder()) == seconds


@pytest.mark.parametrize(
    "name,args",
    [
        ("player_health_pct", {}),
        ("player_primary_power", {"max_power": 120}),
        ("spec_power_rune", {}),
        ("spell_cooldown", {"spell_ids": [195292], "ignore_gcd": True}),
        ("spell_gcd", {}),
        ("spell_usable", {"spell_ids": [49998]}),
        ("spell_overlay", {"spell_ids": [50842]}),
    ],
)
@pytest.mark.parametrize("damage", ["uniform_color", "mixed_gray", "mixed_color"])
def test_plugins_reject_invalid_cell_colors(name: str, args: dict[str, object], damage: str) -> None:
    plugin = Registry().create(f"{name}@dev", args)
    allocate([plugin])
    pixels = np.full((4, 4, 3), 255, dtype=np.uint8)
    if damage == "uniform_color":
        pixels[:] = (255, 0, 0)
    elif damage == "mixed_gray":
        pixels[1, 1] = 0
    else:
        pixels[1, 1] = (255, 0, 0)
    region = Cell(1, 2, pixels)
    decoder = empty_decoder()
    # 检查实际拒绝输入，避免 False 等兜底掩盖校验被删除。
    with pytest.raises(ValueError):
        plugin.decode_value([region], [], [], decoder=decoder)
    assert plugin.value([region], [], [], decoder=decoder) == plugin.fallback_value()


@pytest.mark.parametrize("name", ["spell_cooldown", "spell_gcd"])
def test_cooldown_entire_brightness_range(name: str) -> None:
    args: dict[str, object] = {"spell_ids": [195292], "ignore_gcd": True} if name == "spell_cooldown" else {}
    plugin = Registry().create(f"{name}@dev", args)
    allocate([plugin])
    decoder = empty_decoder()
    for brightness in range(256):
        if brightness >= 155:
            expected = (255 - brightness) / 20
        elif brightness >= 105:
            expected = 5 + (155 - brightness) / 2
        elif brightness >= 55:
            expected = 30 + (105 - brightness) * 2.5
        else:
            expected = 155 + (55 - brightness) * 4
        assert plugin.decode_value([cell(brightness)], [], [], decoder=decoder) == expected


@pytest.mark.parametrize("white_columns", [0, 1, 2, 3, 4])
def test_charges_half_up_and_red_separator(white_columns: int) -> None:
    plugin = Registry().create("spell_charges@dev", {"spell_ids": [50842], "max_charges": 2})
    allocate([plugin])
    assert plugin.output.widths == (1,)
    pixels = np.zeros((4, 8, 3), dtype=np.uint8)
    pixels[:, :2] = [255, 0, 0]
    pixels[:, -2:] = [255, 0, 0]
    pixels[:, 2 : 2 + white_columns] = 255
    assert plugin.value([], [ValueBar(1, 1, pixels)], [], decoder=empty_decoder()) == math.floor(white_columns / 2 + 0.5)
    pixels[:] = [255, 0, 0]
    assert plugin.value([], [ValueBar(1, 1, pixels)], [], decoder=empty_decoder()) == 0


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("spell_gcd", {"spell_ids": [61304]}),
        ("spell_gcd", {"ignore_gcd": False}),
        ("player_primary_power", {"max_power": float("nan")}),
        ("player_primary_power", {"max_power": True}),
        ("spell_charges", {"spell_ids": [], "max_charges": 2}),
        ("spell_usable", {"spell_ids": [True]}),
        ("player_health_pct", {"unit": "player"}),
    ],
)
def test_plugin_arguments(name: str, args: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Registry().create(f"{name}@dev", args)


class Multi(Condition):
    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        return [icon.hash or "empty" for icon in icon_tiles]

    def fallback_value(self) -> Value:
        return []


def test_multi_output_layout_freeze_and_snapshots() -> None:
    bars = Multi(Output("value_bar", 2, str, "list", (2, 3)))
    cells = Multi(Output("cell", 3, str, "list"))
    icons = Multi(Output("icon_tile", 2, str, "list"))
    other_bar = Multi(Output("value_bar", 1, str, "list", (1,)))
    assert allocate([bars, cells, icons, other_bar]) == 44
    assert [region.x for region in bars.regions] == [1, 4]
    assert other_bar.regions[0].x == 8
    assert [region.x for region in icons.regions] == [1, 2]
    with pytest.raises(ValueError):
        allocate([bars])
    pixels = np.zeros((20, 44, 3), dtype=np.uint8)
    pixels[12:20, 12:20] = [0, 100, 0]
    decoder = PixelDecoder(pixels)
    raw = icons.raw_value(decoder)
    result = icons.value(*raw, decoder=decoder)
    assert isinstance(result, list) and result[0] == "empty" and len(str(result[1])) == 16
    pixels[:] = 0
    assert icons.value(*raw, decoder=decoder) == result
    assert [bar.width for bar in bars.raw_value(decoder)[1]] == [2, 3]


class WrongType(Multi):
    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        return True


class Exploding(Multi):
    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        raise RuntimeError("unreadable")


def test_wrong_type_and_exception_fallback() -> None:
    for plugin in (WrongType(Output("cell", value_type=str, value_shape="list")), Exploding(Output("cell", value_type=str, value_shape="list"))):
        allocate([plugin])
        assert plugin.value([cell(0)], [], [], decoder=empty_decoder()) == []


def test_registry_instances_are_independent() -> None:
    registry = Registry()
    first = registry.create("spell_gcd@dev", {})
    second = registry.create("spell_gcd@dev", {})
    assert first is not second and type(first) is type(second)
    allocate([first, second])
    assert first.regions[0].x == 1 and second.regions[0].x == 2
