"""冻结迁移清单的联合布局及生成测试，不替代真实客户端验证。"""

from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.condition.layout import allocate
from phantom.core.condition.registry import Registry
from phantom.core.generator import render
from phantom.core.pixels import PixelDecoder
from phantom.core.rotation import ConditionEntry, load_rotation

ROOT = Path(__file__).resolve().parents[1]


def migration_cases() -> dict[str, dict[str, object]]:
    cases: dict[str, dict[str, object]] = {
        "spell_known": {"spell_ids": [100]},
        "talent_known": {"spell_ids": [100]},
        "spec_power_rune": {},
        "player_health_pct": {},
        "player_has_pet": {},
        "spell_in_range": {"spell_id": 100, "unit_token": "mouseover"},
        "player_melee_enemies_count": {"spell_id": 100},
        "player_range_aura_units_count": {"spell_id": 100, "aura_id": 200},
    }
    for unit in ("target", "focus"):
        cases[f"{unit}_in_range"] = {"spell_id": 100}
        for suffix in ("is_enemy", "can_assist", "health_pct"):
            cases[f"{unit}_{suffix}"] = {}
        for suffix in ("has_buff", "has_debuff"):
            cases[f"{unit}_{suffix}"] = {"aura_ids": [200, 201]}
    for owner in ("player_buff", "target_debuff"):
        cases[f"aura_{owner}_duration"] = {"aura_ids": [200, 201], "duration": 15}
        cases[f"aura_{owner}_stacks"] = {"aura_ids": [200, 201], "max_value": 30, "min_value": 0, "width": 2}
    for power in ("mana", "rage", "focus", "energy", "runic_power", "lunar_power", "maelstrom", "insanity", "fury", "pain"):
        cases[f"spec_power_{power}"] = {"max_power": 100}
    for power in ("combo_points", "soul_shards", "holy_power", "chi", "essence", "arcane_charges"):
        cases[f"spec_power_{power}"] = {}
    return cases


def test_migration_plugins_generate_together(tmp_path: Path) -> None:
    entries = tuple(ConditionEntry(name, f"{name}@dev", Registry().create(f"{name}@dev", args)) for name, args in migration_cases().items())
    board_width = allocate([entry.instance for entry in entries])
    next_cell = 1
    next_bar = 1
    for entry in entries:
        plugin = entry.instance
        assert plugin.output.output_count == 1
        region = plugin.regions[0]
        if plugin.output.output_type == "value_bar":
            assert region.x == next_bar
            next_bar += plugin.output.widths[0] + 1
        else:
            assert plugin.output.output_type == "cell"
            assert region.x == next_cell
            next_cell += 1
    assert board_width == (max(5, next_cell - 1, next_bar - 1) + 2) * 4
    rotation_path = tmp_path / "engine.toml"
    rotation_path.write_bytes((ROOT / "tests/fixtures/engine-rotation.toml").read_bytes())
    rotation = replace(load_rotation(rotation_path), conditions=entries, macros=(), board_width=board_width)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) assert(loadstring(source)); return true end")
    for filename, source in render(rotation, "PhantomMigrationTest").items():
        if filename.endswith(".lua"):
            assert "{{" not in source, filename
            assert compile_lua(source), filename
    decoder = PixelDecoder(np.zeros((20, board_width, 3), dtype=np.uint8))
    for entry in entries:
        plugin = entry.instance
        assert plugin.output.accepts(plugin.value(*plugin.raw_value(decoder), decoder=decoder))
