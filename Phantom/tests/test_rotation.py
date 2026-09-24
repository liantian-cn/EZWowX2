from pathlib import Path

import pytest
import tomlkit

from phantom.core.rotation import RotationError, load_rotation
from phantom.core.specializations import CLASS_IDS, SPECIALIZATION_BY_KEY, SPECIALIZATIONS

FIXTURE = Path(__file__).parent / "fixtures/rotation-validation.toml"


def fixture_copy(tmp_path: Path) -> Path:
    path = tmp_path / "rotation.toml"
    path.write_bytes(FIXTURE.read_bytes())
    return path


def test_memory_layout_idempotent_and_optional_class_id(tmp_path: Path) -> None:
    path = fixture_copy(tmp_path)
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    del document["profile"]["unit_class_id"]
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    rotation = load_rotation(path)
    assert rotation.profile.unit_class_id == 6
    assert rotation.board_width == 28
    assert len(rotation.rules) == 3
    assert len(rotation.macros) == 2
    assert rotation.conditions[5].plugin == "spell_gcd@dev"
    assert [e.instance.regions[0].x for e in rotation.conditions] == [1, 2, 3, 1, 4, 5]
    saved = tomlkit.parse(path.read_text(encoding="utf-8"))
    assert "unit_class_id" not in saved["profile"]
    assert "layout" not in path.read_text(encoding="utf-8")
    old = path.read_bytes()
    modified = path.stat().st_mtime_ns
    load_rotation(path)
    assert path.read_bytes() == old
    assert path.stat().st_mtime_ns == modified


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("schema_version = 1", "schema_version = true"),
        ("schema_version = 1", "schema_version = 2"),
        ("550e8400-e29b-41d4-a716-446655440000", "not-a-uuid"),
        ("unit_class_id = 6", "unit_class_id = 1"),
        ("unit_spec = 1", "unit_spec = 5"),
        ("unit_spec = 1", "unit_spec = 4"),
        ("unit_spec = 1", "unit_spec = true"),
        ('unit_class = "DEATHKNIGHT"', 'unit_class = "deathknight"'),
        ('title = "符文数量"', 'title = "符文能量"'),
        ('title = "符文数量"', 'title = "and"'),
        ('name = "心脏打击"', 'name = "灵界打击"'),
        ('name = "心脏打击"', 'name = "Idle"'),
        ('macro = "心脏打击"', 'macro = "未知宏"'),
        ('condition = "符文数量>=1"', 'condition = "未知条件>=1"'),
        ('condition = "符文数量>=1"', 'condition = "("'),
        ('condition = "符文数量>=1"', 'condition = ""'),
        ("player_primary_power@dev", "player_primary_power@2.0"),
        ("player_primary_power@dev", "../player_primary_power@dev"),
        ("max_power = 120", "max_power = -1"),
        ("max_charges = 2", "max_charges = 2.0"),
        ("ignore_gcd = true", 'ignore_gcd = "true"'),
        ('macro_text = "/cast 心脏打击"', ""),
        ('macro_text = "/cast 心脏打击"', 'macro_text = "  "'),
        ('macro_text = "/cast 心脏打击"', "macro_text = false"),
        ("schema_version = 1", "schema_version = 1\nunknown = 42"),
    ],
)
def test_invalid_config_not_rewritten(tmp_path: Path, old: str, new: str) -> None:
    path = fixture_copy(tmp_path)
    source = path.read_text(encoding="utf-8")
    assert old in source
    path.write_text(source.replace(old, new), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(RotationError):
        load_rotation(path)
    assert path.read_bytes() == before


def test_implicit_idle_not_persisted_and_legacy_layout_preserved(tmp_path: Path) -> None:
    path = fixture_copy(tmp_path)
    source = path.read_text(encoding="utf-8")
    legacy = 'layout = { output_type = "invalid", regions = [{ x = 99, y = -1 }] } # 旧坐标\n'
    source = source.replace('plugin = "player_health_pct@dev"\n', 'plugin = "player_health_pct@dev"\n' + legacy) + "\n# 保留用户注释\n"
    path.write_text(source, encoding="utf-8")
    rotation = load_rotation(path)
    saved = path.read_text(encoding="utf-8")
    assert rotation.rules[-1].macro == "Idle"
    assert "# 保留用户注释" in saved
    assert 'macro = "Idle"' not in saved
    assert legacy in saved
    assert rotation.conditions[0].instance.regions[0].x == 1
    assert 'macro_text = "/cast 心脏打击"' in saved


@pytest.mark.parametrize("key", [specialization.key for specialization in SPECIALIZATIONS])
def test_all_forty_specializations_are_loadable(tmp_path: Path, key: str) -> None:
    specialization = SPECIALIZATION_BY_KEY[key]
    path = fixture_copy(tmp_path)
    source = path.read_text(encoding="utf-8").replace('unit_class = "DEATHKNIGHT"', f'unit_class = "{specialization.unit_class}"')
    source = source.replace("unit_class_id = 6", f"unit_class_id = {specialization.unit_class_id}").replace("unit_spec = 1", f"unit_spec = {specialization.unit_spec}")
    path.write_text(source, encoding="utf-8")
    rotation = load_rotation(path)
    assert (rotation.profile.unit_class, rotation.profile.unit_spec) == (specialization.unit_class, specialization.unit_spec)


@pytest.mark.parametrize("token", [token for token in CLASS_IDS if token != "DRUID"])
def test_fourth_specialization_is_rejected_for_non_druids(tmp_path: Path, token: str) -> None:
    path = fixture_copy(tmp_path)
    source = path.read_text(encoding="utf-8").replace('unit_class = "DEATHKNIGHT"', f'unit_class = "{token}"')
    source = source.replace("unit_class_id = 6", f"unit_class_id = {CLASS_IDS[token]}").replace("unit_spec = 1", "unit_spec = 4")
    path.write_text(source, encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(RotationError, match="合法专精"):
        load_rotation(path)
    assert path.read_bytes() == before


def test_specialization_table_matches_contract() -> None:
    assert len(CLASS_IDS) == 13
    assert len(SPECIALIZATIONS) == len(SPECIALIZATION_BY_KEY) == 40
    assert [(item.unit_class_id, item.unit_spec) for item in SPECIALIZATIONS] == sorted((item.unit_class_id, item.unit_spec) for item in SPECIALIZATIONS)
    assert SPECIALIZATION_BY_KEY["demonhunter.devourer"].unit_spec == 3
    assert SPECIALIZATION_BY_KEY["druid.restoration"].unit_spec == 4
