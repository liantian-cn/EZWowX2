from pathlib import Path

import pytest

from phantom.core.configuration import AppConfig, ConfigurationError, load_config


def test_config_uses_launch_directory_and_preserves_existing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launch = tmp_path / "shortcut-start"
    program = tmp_path / "program"
    launch.mkdir()
    program.mkdir()
    monkeypatch.chdir(launch)
    config = load_config(Path.cwd())
    assert config.path == launch / "phantom.toml"
    assert config.fps == 15
    assert config.capture_plugin == "gdi@dev"
    assert config.rotation_paths == {}
    assert config.warnings == ()
    assert (config.min_width, config.min_height, config.log_max_lines) == (120, 46, 1000)
    assert not (program / "phantom.toml").exists()
    original = b"# keep comment\n[capture]\nfps = 7.5\n[ui]\nmin_width = 132\n"
    config.path.write_bytes(original)
    config = load_config(Path.cwd())
    assert (config.fps, config.min_width, config.min_height) == (7.5, 132, 46)
    assert config.capture_plugin == "gdi@dev"
    assert config.path.read_bytes() == original
    assert Path.cwd() == launch


@pytest.mark.parametrize(
    "content",
    [
        "[capture\nfps = 15",
        "[capture]\nfps = 0",
        "[capture]\nfps = -1",
        "[capture]\nfps = nan",
        "[capture]\nfps = inf",
        "[capture]\nfps = true",
        '[capture]\nfps = "15"',
        '[capture]\nplugin = ""',
        '[capture]\nplugin = "   "',
        "[capture]\nplugin = false",
        "[capture]\nplugin = 1",
        "capture = 1",
        "ui = []",
        "[ui]\nmin_width = false",
        "[ui]\nmin_height = 0",
        "[ui]\nlog_max_lines = 3.5",
    ],
)
def test_invalid_config_fails_without_rewriting(tmp_path: Path, content: str) -> None:
    path = tmp_path / "phantom.toml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigurationError, match="phantom.toml"):
        load_config(tmp_path)
    assert path.read_text(encoding="utf-8") == content


def test_unreadable_or_unwritable_config_fails_explicitly(tmp_path: Path) -> None:
    (tmp_path / "phantom.toml").mkdir()
    with pytest.raises(ConfigurationError):
        load_config(tmp_path)
    with pytest.raises(ConfigurationError):
        load_config(tmp_path / "missing-directory")


def test_rotation_paths_resolve_against_config_directory(tmp_path: Path) -> None:
    absolute = tmp_path / "outside" / "chosen.toml"
    source = f"""[rotations]
"deathknight.blood" = "rotations/血.toml"
"demonhunter.devourer" = '{absolute}'
[wow]
executable = "game/Wow.exe"
[addon]
name = "My_Addon1"
"""
    (tmp_path / "phantom.toml").write_text(source, encoding="utf-8")
    config = load_config(tmp_path)
    assert config.rotation_paths == {"deathknight.blood": tmp_path / "rotations/血.toml", "demonhunter.devourer": absolute}
    assert config.wow_executable == tmp_path / "game/Wow.exe"
    assert config.addon_name == "My_Addon1"
    assert not config.warnings


@pytest.mark.parametrize("legacy", ['[rotation]\npath = "old.toml"', "rotation = false"])
def test_legacy_rotation_is_ignored_without_validation_or_migration(tmp_path: Path, legacy: str) -> None:
    path = tmp_path / "phantom.toml"
    path.write_text(legacy, encoding="utf-8")
    before = path.read_bytes()
    config = load_config(tmp_path)
    assert config.rotation_paths == {}
    assert any("旧 [rotation].path" in warning for warning in config.warnings)
    assert path.read_bytes() == before


@pytest.mark.parametrize("value", ["false", "2", "[]", '""', '"   "', '"\\u0000"', "{}"])
def test_bad_rotation_entry_is_local_warning(tmp_path: Path, value: str) -> None:
    source = f'[rotations]\n"deathknight.blood" = {value}\n"mage.fire" = "fire.toml"\n"unknown.spec" = "other.toml"\n'
    path = tmp_path / "phantom.toml"
    path.write_text(source, encoding="utf-8")
    before = path.read_bytes()
    config = load_config(tmp_path)
    assert config.rotation_paths == {"mage.fire": tmp_path / "fire.toml"}
    assert len(config.warnings) == 2
    assert path.read_bytes() == before


@pytest.mark.parametrize("source", ["rotations = false", "rotations = []", '[rotations]\ndeathknight.blood = "nested.toml"'])
def test_bad_rotation_table_or_nested_key_is_warning(tmp_path: Path, source: str) -> None:
    (tmp_path / "phantom.toml").write_text(source, encoding="utf-8")
    config = load_config(tmp_path)
    assert config.rotation_paths == {}
    assert config.warnings


def test_app_config_default_mapping_is_independent(tmp_path: Path) -> None:
    first, second = AppConfig(tmp_path / "first.toml"), AppConfig(tmp_path / "second.toml")
    assert first.rotation_paths is not second.rotation_paths
    assert AppConfig(tmp_path / "third.toml", rotation_paths={"mage.fire": tmp_path / "fire.toml"}).rotation_paths["mage.fire"].name == "fire.toml"
