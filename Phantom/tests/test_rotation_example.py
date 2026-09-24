"""验证正式配置仅在副本补入已批准的新默认参数，第二次加载不再回写。"""

import tomllib
from pathlib import Path
from typing import Any

import pytest

from phantom.core.macro_keys import MACRO_KEYS
from phantom.core.rotation import load_rotation

ROTATIONS = Path(__file__).resolve().parents[1] / "rotations"
PLAYER_AURA_PLUGINS = {"player_has_buff@dev", "aura_player_buff_stacks@dev", "aura_player_buff_duration@dev"}
MIGRATED_STEMS = {"死亡骑士-鲜血", "圣骑士-防护"}


def with_approved_defaults(source: bytes) -> dict[str, Any]:
    """只允许补入本次新增的默认来源过滤，不掩盖其他缺失参数。"""
    document: dict[str, Any] = tomllib.loads(source.decode("utf-8"))
    for condition in document["conditions"]:
        if condition["plugin"] in PLAYER_AURA_PLUGINS:
            condition.setdefault("plugin_args", {}).setdefault("player_only", True)
    return document


@pytest.mark.parametrize("source_path", sorted(ROTATIONS.glob("*.toml")), ids=lambda path: path.stem)
def test_formal_rotation_has_no_layout_and_only_approved_default_writeback(tmp_path: Path, source_path: Path) -> None:
    source = source_path.read_bytes()
    document = tomllib.loads(source.decode("utf-8"))
    assert all("layout" not in condition for condition in document["conditions"])
    assert all(set(macro) == {"name", "macro_text"} for macro in document["macros"])
    path = tmp_path / source_path.name
    path.write_bytes(source)
    modified = path.stat().st_mtime_ns

    rotation = load_rotation(path)

    assert len(rotation.conditions) == len(document["conditions"])
    assert any(entry.instance.regions for entry in rotation.conditions)
    assert [macro.key for macro in rotation.macros] == list(MACRO_KEYS[: len(rotation.macros)])
    assert tomllib.loads(path.read_text(encoding="utf-8")) == with_approved_defaults(source)
    if source_path.stem in MIGRATED_STEMS:
        assert path.read_bytes() == source
        assert path.stat().st_mtime_ns == modified
    normalized = path.read_bytes()
    normalized_modified = path.stat().st_mtime_ns
    load_rotation(path)
    assert path.read_bytes() == normalized
    assert path.stat().st_mtime_ns == normalized_modified
    assert source_path.read_bytes() == source


def test_formal_directory_contains_only_forty_specializations() -> None:
    files = list(ROTATIONS.glob("*.toml"))
    assert len(files) == 40
    assert all(not path.stem.isascii() for path in files)


def test_preserved_observation_fixture_only_receives_approved_defaults(tmp_path: Path) -> None:
    source = (ROTATIONS.parent / "tests/fixtures/condition-observations.toml").read_bytes()
    path = tmp_path / "observations.toml"
    path.write_bytes(source)
    rotation = load_rotation(path)
    assert len(rotation.conditions) > 10
    assert len(rotation.macros) == 4
    assert tomllib.loads(path.read_text(encoding="utf-8")) == with_approved_defaults(source)
    normalized = path.read_bytes()
    load_rotation(path)
    assert path.read_bytes() == normalized
