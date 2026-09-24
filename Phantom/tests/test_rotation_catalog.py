import os
import tomllib
from pathlib import Path
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

import phantom.core.rotation as rotation_module
import phantom.core.rotation_catalog as catalog_module
from phantom.core.configuration import AppConfig, load_config
from phantom.core.rotation_catalog import load_rotations
from phantom.core.specializations import SPECIALIZATION_BY_KEY, SPECIALIZATIONS

SHARED_UUID = "550e8400-e29b-41d4-a716-446655440000"


def write_rotation(path: Path, key: str = "deathknight.blood", *, identifier: str | None = None, defaults: bool = False, invalid: bool = False, crlf: bool = False) -> Path:
    spec = SPECIALIZATION_BY_KEY[key]
    source = f'''# 用户循环说明
schema_version = 1
uuid = "{identifier or uuid4()}" # 身份注释
macros = []
rotation = []
{"" if defaults else "conditions = []"}

[profile]
title = "{spec.class_name}-{spec.name}"
description = "用户描述"
unit_class = "{spec.unit_class}"
unit_spec = {spec.unit_spec}
'''
    if defaults:
        source += '\n[[conditions]]\ntitle = "生命"\nplugin = "player_health_pct@dev"\n'
    if invalid:
        source = source.replace("rotation = []", 'rotation = [{ condition = "未知", macro = "Idle" }]')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((source.replace("\n", "\r\n") if crlf else source).encode("utf-8"))
    return path


def config(tmp_path: Path, source: str = "# 配置说明\n[rotations]\n") -> AppConfig:
    (tmp_path / "phantom.toml").write_bytes(source.encode("utf-8"))
    return load_config(tmp_path)


def test_explicit_priority_and_unselected_candidates_have_no_side_effects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    unselected = write_rotation(tmp_path / "rotations/a.toml", defaults=True)
    chosen = write_rotation(tmp_path / "elsewhere/chosen.toml", defaults=True)
    bad_unselected = write_rotation(tmp_path / "rotations/z.toml", defaults=True, invalid=True)
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (unselected, bad_unselected)}
    app_config = config(tmp_path, '[rotations]\n"deathknight.blood" = "elsewhere/chosen.toml" # 固定选择\n')
    original_config = app_config.path.read_bytes()
    loader = Mock(wraps=rotation_module.load_rotation)
    monkeypatch.setattr(catalog_module, "load_rotation", loader)
    result = load_rotations(app_config)
    assert [rotation.path for rotation in result.rotations] == [chosen]
    assert not result.warnings
    assert loader.call_count == 1
    assert "use_predicted" in chosen.read_text(encoding="utf-8")
    assert app_config.path.read_bytes() == original_config
    for path, (content, modified) in before.items():
        assert path.read_bytes() == content
        assert path.stat().st_mtime_ns == modified


def test_discovery_skips_bad_candidates_and_selects_first_fully_valid_file(tmp_path: Path) -> None:
    invalid = write_rotation(tmp_path / "rotations/a-invalid.toml", defaults=True, invalid=True)
    (tmp_path / "rotations/b-broken.toml").write_text("not valid = [", encoding="utf-8")
    illegal = write_rotation(tmp_path / "rotations/c-illegal.toml")
    illegal.write_text(illegal.read_text(encoding="utf-8").replace("unit_spec = 1", "unit_spec = 4"), encoding="utf-8")
    selected = write_rotation(tmp_path / "rotations/d-valid.toml", defaults=True)
    ignored = write_rotation(tmp_path / "rotations/e-valid.toml", defaults=True)
    before = {path: path.read_bytes() for path in (invalid, illegal, ignored)}
    result = load_rotations(config(tmp_path))
    assert [rotation.path for rotation in result.rotations] == [selected]
    assert len(result.warnings) == 3
    assert load_config(tmp_path).rotation_paths == {"deathknight.blood": selected}
    for path, content in before.items():
        assert path.read_bytes() == content


@pytest.mark.parametrize("failure", ["missing", "mismatch", "invalid"])
def test_bad_explicit_selection_falls_back_and_is_replaced(tmp_path: Path, failure: str) -> None:
    explicit = tmp_path / "explicit.toml"
    if failure != "missing":
        write_rotation(explicit, "mage.fire" if failure == "mismatch" else "deathknight.blood", defaults=True, invalid=failure == "invalid")
    before = explicit.read_bytes() if explicit.exists() else None
    fallback = write_rotation(tmp_path / "rotations/fallback.toml")
    result = load_rotations(config(tmp_path, '[rotations]\n"deathknight.blood" = "explicit.toml" # 用户选择\n'))
    assert [rotation.path for rotation in result.rotations] == [fallback]
    assert len(result.warnings) == 1
    assert load_config(tmp_path).rotation_paths["deathknight.blood"] == fallback
    assert "# 用户选择" in (tmp_path / "phantom.toml").read_text(encoding="utf-8")
    if before is not None:
        assert explicit.read_bytes() == before


def test_bad_explicit_without_replacement_preserves_original_value(tmp_path: Path) -> None:
    (tmp_path / "rotations").mkdir()
    source = '# 请保留\n[rotations]\n"deathknight.blood" = "missing.toml"\n"unknown.spec" = "user.toml"\n'
    app_config = config(tmp_path, source)
    before = app_config.path.read_bytes()
    result = load_rotations(app_config)
    assert result.rotations == ()
    assert len(result.warnings) == 3
    assert app_config.path.read_bytes() == before


@pytest.mark.parametrize("source", ["rotations = false\n", '[rotations]\n"deathknight.blood" = false\n', '[rotations]\ndeathknight.blood = "nested.toml"\n'])
def test_local_config_errors_still_allow_discovery(tmp_path: Path, source: str) -> None:
    selected = write_rotation(tmp_path / "rotations/a.toml")
    result = load_rotations(config(tmp_path, source))
    assert [rotation.path for rotation in result.rotations] == [selected]
    assert result.warnings
    assert load_config(tmp_path).rotation_paths["deathknight.blood"] == selected


@pytest.mark.parametrize("kind", ["missing", "empty", "nested-only"])
def test_missing_or_empty_scan_never_creates_samples(tmp_path: Path, kind: str) -> None:
    directory = tmp_path / "rotations"
    if kind != "missing":
        directory.mkdir()
    if kind == "nested-only":
        write_rotation(directory / "nested/a.toml")
    app_config = config(tmp_path)
    before = app_config.path.read_bytes()
    result = load_rotations(app_config)
    assert not result.rotations
    assert result.warnings
    assert app_config.path.read_bytes() == before
    assert list(directory.glob("*.toml")) == []
    assert directory.exists() == (kind != "missing")


def test_absolute_explicit_path_works_without_scan_directory(tmp_path: Path) -> None:
    selected = write_rotation(tmp_path / "external/chosen.toml")
    app_config = config(tmp_path, f"[rotations]\n\"deathknight.blood\" = '{selected}'\n")
    result = load_rotations(app_config)
    assert [rotation.path for rotation in result.rotations] == [selected]
    assert len(result.warnings) == 1


@pytest.mark.parametrize("table", ['[rotations] # 选择表\n"unknown.spec" = "keep.toml" # 未知项\n', 'rotations = { "unknown.spec" = "keep.toml" } # 选择表\n'])
def test_selection_writeback_preserves_comments_crlf_and_restart_stability(tmp_path: Path, table: str) -> None:
    selected = write_rotation(tmp_path / "rotations/中文.toml", defaults=True, crlf=True)
    source = ("# 顶部注释\n" + table + "[custom]\nanswer = 42 # 保留字段\n[capture]\nfps = 12\n").replace("\n", "\r\n")
    result = load_rotations(config(tmp_path, source))
    assert result.rotations[0].path == selected
    path = tmp_path / "phantom.toml"
    saved = path.read_bytes().decode("utf-8")
    assert "\n" not in saved.replace("\r\n", "")
    assert "# 顶部注释\r\n" in saved and "# 选择表" in saved
    assert '"unknown.spec" = "keep.toml"' in saved
    assert "answer = 42 # 保留字段\r\n" in saved
    assert tomllib.loads(saved)["custom"]["answer"] == 42
    assert tomllib.loads(saved)["rotations"]["deathknight.blood"] == "rotations/中文.toml"
    before = {file: (file.read_bytes(), file.stat().st_mtime_ns) for file in (path, selected)}
    reloaded = load_rotations(load_config(tmp_path))
    assert [(item.path, item.uuid) for item in reloaded.rotations] == [(item.path, item.uuid) for item in result.rotations]
    for file, (content, modified) in before.items():
        assert file.read_bytes() == content
        assert file.stat().st_mtime_ns == modified


def test_config_writeback_failure_preserves_loaded_memory_and_original(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = write_rotation(tmp_path / "rotations/selected.toml")
    app_config = config(tmp_path)
    before = app_config.path.read_bytes()
    monkeypatch.setattr(catalog_module, "write_toml", Mock(side_effect=OSError("模拟保存失败")))
    result = load_rotations(app_config)
    assert [rotation.path for rotation in result.rotations] == [selected]
    assert any("内存选择仍有效" in warning for warning in result.warnings)
    assert app_config.path.read_bytes() == before


def test_config_concurrent_edit_since_startup_is_not_overwritten(tmp_path: Path) -> None:
    selected = write_rotation(tmp_path / "rotations/selected.toml")
    app_config = config(tmp_path)
    changed = app_config.path.read_bytes() + b"\n# concurrent edit\n"
    app_config.path.write_bytes(changed)
    result = load_rotations(app_config)
    assert result.rotations[0].path == selected
    assert any("加载期间被修改" in warning for warning in result.warnings)
    assert app_config.path.read_bytes() == changed


def test_no_changes_do_not_attempt_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = write_rotation(tmp_path / "rotations/selected.toml")
    app_config = config(tmp_path, '[rotations]\n"deathknight.blood" = "rotations/selected.toml"\n')
    writer = Mock(side_effect=AssertionError("不应写入"))
    monkeypatch.setattr(rotation_module, "atomic_write", writer)
    assert load_rotations(app_config).rotations[0].path == selected
    writer.assert_not_called()


def test_all_forty_groups_load_in_stable_order(tmp_path: Path) -> None:
    for index, spec in enumerate(reversed(SPECIALIZATIONS)):
        write_rotation(tmp_path / f"rotations/{index:02}.toml", spec.key)
    result = load_rotations(config(tmp_path))
    assert [(item.profile.unit_class, item.profile.unit_spec) for item in result.rotations] == [(spec.unit_class, spec.unit_spec) for spec in SPECIALIZATIONS]
    assert not result.warnings
    assert len(load_config(tmp_path).rotation_paths) == 40


def test_uuid_conflict_is_persisted_after_validation_and_stable_on_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = write_rotation(tmp_path / "rotations/z-warrior.toml", "warrior.arms", identifier=SHARED_UUID)
    second = write_rotation(tmp_path / "rotations/a-blood.toml", identifier=SHARED_UUID, defaults=True, crlf=True)
    ignored = write_rotation(tmp_path / "rotations/b-blood.toml", identifier=SHARED_UUID, defaults=True)
    untouched = {path: path.read_bytes() for path in (first, ignored)}
    new_uuid = uuid4()
    generator = Mock(side_effect=[UUID(SHARED_UUID), new_uuid])
    monkeypatch.setattr(rotation_module, "uuid4", generator)
    result = load_rotations(config(tmp_path))
    assert [item.path for item in result.rotations] == [first, second]
    assert [item.uuid for item in result.rotations] == [SHARED_UUID, str(new_uuid)]
    assert generator.call_count == 2
    assert any("UUID 冲突已保存修复" in warning for warning in result.warnings)
    saved = second.read_bytes().decode("utf-8")
    assert tomllib.loads(saved)["uuid"] == str(new_uuid)
    assert "# 身份注释\r\n" in saved and "# 用户循环说明\r\n" in saved
    assert "\n" not in saved.replace("\r\n", "")
    assert tomllib.loads(saved)["conditions"][0]["plugin_args"] == {"use_predicted": True}
    for path, content in untouched.items():
        assert path.read_bytes() == content
    before = second.stat().st_mtime_ns
    reloaded = load_rotations(load_config(tmp_path))
    assert [item.uuid for item in reloaded.rotations] == [SHARED_UUID, str(new_uuid)]
    assert not reloaded.warnings
    assert second.stat().st_mtime_ns == before


def test_invalid_full_candidate_is_not_uuid_repaired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = write_rotation(tmp_path / "rotations/z-warrior.toml", "warrior.arms", identifier=SHARED_UUID)
    invalid = write_rotation(tmp_path / "rotations/a-invalid.toml", identifier=SHARED_UUID, defaults=True, invalid=True)
    fallback = write_rotation(tmp_path / "rotations/b-valid.toml")
    before = invalid.read_bytes()
    generator = Mock(side_effect=AssertionError("非法候选不得修改 UUID"))
    monkeypatch.setattr(rotation_module, "uuid4", generator)
    result = load_rotations(config(tmp_path))
    assert [item.path for item in result.rotations] == [first, fallback]
    assert invalid.read_bytes() == before
    generator.assert_not_called()


@pytest.mark.parametrize("with_fallback", [False, True])
def test_uuid_save_failure_rejects_candidate_and_tries_replacement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, with_fallback: bool) -> None:
    first = write_rotation(tmp_path / "rotations/z-warrior.toml", "warrior.arms", identifier=SHARED_UUID)
    conflicting = write_rotation(tmp_path / "rotations/a-conflict.toml", identifier=SHARED_UUID, defaults=True)
    fallback = write_rotation(tmp_path / "rotations/b-valid.toml") if with_fallback else None
    app_config = config(tmp_path, '[rotations]\n"deathknight.blood" = "rotations/a-conflict.toml"\n')
    before = conflicting.read_bytes()
    original = rotation_module.atomic_write

    def write(path: Path, content: str | bytes) -> None:
        if path == conflicting:
            raise OSError("模拟 UUID 保存失败")
        original(path, content)

    monkeypatch.setattr(rotation_module, "atomic_write", write)
    result = load_rotations(app_config)
    assert [item.path for item in result.rotations] == [first] + ([fallback] if fallback is not None else [])
    assert conflicting.read_bytes() == before
    assert any("模拟 UUID 保存失败" in warning for warning in result.warnings)
    assert load_config(tmp_path).rotation_paths["deathknight.blood"] == (fallback or conflicting)


def test_uuid_concurrent_edit_is_preserved_and_fallback_loaded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_rotation(tmp_path / "rotations/z-warrior.toml", "warrior.arms", identifier=SHARED_UUID)
    conflicting = write_rotation(tmp_path / "rotations/a-conflict.toml", identifier=SHARED_UUID)
    fallback = write_rotation(tmp_path / "rotations/b-valid.toml")
    changed = conflicting.read_bytes() + b"\n# concurrent edit\n"

    def replacement_uuid() -> UUID:
        conflicting.write_bytes(changed)
        return uuid4()

    monkeypatch.setattr(rotation_module, "uuid4", replacement_uuid)
    result = load_rotations(config(tmp_path))
    assert result.rotations[-1].path == fallback
    assert conflicting.read_bytes() == changed
    assert any("加载期间被修改" in warning for warning in result.warnings)


def test_same_path_under_multiple_keys_is_not_reloaded_or_uuid_changed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = write_rotation(tmp_path / "rotations/shared.toml", "warrior.arms", identifier=SHARED_UUID)
    app_config = config(tmp_path, '[rotations]\n"warrior.arms" = "rotations/shared.toml"\n"deathknight.blood" = "rotations/../rotations/shared.toml"\n')
    before = selected.read_bytes()
    loader = Mock(wraps=rotation_module.load_rotation)
    monkeypatch.setattr(catalog_module, "load_rotation", loader)
    result = load_rotations(app_config)
    assert [item.path for item in result.rotations] == [selected]
    assert loader.call_count == 1
    assert selected.read_bytes() == before
    assert any("已由其他职业专精选用" in warning for warning in result.warnings)


def test_wrong_key_does_not_prevent_later_correct_key_from_loading_same_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = write_rotation(tmp_path / "rotations/shared.toml", defaults=True)
    app_config = config(tmp_path, '[rotations]\n"warrior.arms" = "rotations/shared.toml"\n"deathknight.blood" = "rotations/shared.toml"\n')
    loader = Mock(wraps=rotation_module.load_rotation)
    monkeypatch.setattr(catalog_module, "load_rotation", loader)
    result = load_rotations(app_config)
    assert [item.path for item in result.rotations] == [selected]
    assert loader.call_count == 1
    assert any("职业专精与配置组合 warrior.arms 不符" in warning for warning in result.warnings)


def test_selection_atomic_replace_failure_keeps_original_and_cleans_temporary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = write_rotation(tmp_path / "rotations/selected.toml")
    app_config = config(tmp_path)
    before = app_config.path.read_bytes()
    monkeypatch.setattr(os, "replace", Mock(side_effect=OSError("模拟原子替换失败")))
    result = load_rotations(app_config)
    assert [item.path for item in result.rotations] == [selected]
    assert any("模拟原子替换失败" in warning for warning in result.warnings)
    assert app_config.path.read_bytes() == before
    assert list(tmp_path.glob(".phantom.toml.*")) == []


def test_uuid_repair_requires_successful_reload_of_saved_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = write_rotation(tmp_path / "rotations/z-warrior.toml", "warrior.arms", identifier=SHARED_UUID)
    conflicting = write_rotation(tmp_path / "rotations/a-conflict.toml", identifier=SHARED_UUID)
    fallback = write_rotation(tmp_path / "rotations/b-valid.toml")
    app_config = config(tmp_path)
    # 集合入口已持有初次加载函数；模块中的函数仅在 UUID 保存后的重新加载时调用。
    reloader = Mock(side_effect=rotation_module.RotationError("模拟修复后重新加载失败"))
    monkeypatch.setattr(rotation_module, "load_rotation", reloader)
    result = load_rotations(app_config)
    assert [item.path for item in result.rotations] == [first, fallback]
    reloader.assert_called_once()
    assert tomllib.loads(conflicting.read_text(encoding="utf-8"))["uuid"] != SHARED_UUID
    assert any("模拟修复后重新加载失败" in warning for warning in result.warnings)


def test_non_table_array_candidate_falls_back_without_crashing(tmp_path: Path) -> None:
    invalid = write_rotation(tmp_path / "rotations/a-invalid.toml")
    invalid.write_text(invalid.read_text(encoding="utf-8").replace("conditions = []", 'conditions = [{ title = "生命", plugin = "player_health_pct@dev" }]'), encoding="utf-8")
    fallback = write_rotation(tmp_path / "rotations/b-valid.toml")
    before = invalid.read_bytes()
    result = load_rotations(config(tmp_path))
    assert [item.path for item in result.rotations] == [fallback]
    assert invalid.read_bytes() == before
    assert any("[[conditions]]" in warning for warning in result.warnings)
