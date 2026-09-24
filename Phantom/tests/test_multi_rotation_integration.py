import shutil
import tomllib
from pathlib import Path
from typing import Any
from uuid import UUID

from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core.configuration import load_config
from phantom.core.generator import generate_rotations
from phantom.core.rotation_catalog import load_rotations
from phantom.core.specializations import SPECIALIZATION_BY_PROFILE


def test_all_forty_rotations_discover_persist_and_generate_one_addon(tmp_path: Path) -> None:
    # 只加载正式循环的副本，验证完整集合且不把默认参数回写到仓库源文件。
    root = Path(__file__).resolve().parents[1]
    directory = tmp_path / "rotations"
    shutil.copytree(root / "rotations", directory)
    originals = {path.name: path.read_bytes() for path in directory.glob("*.toml")}
    config = load_config(tmp_path)
    loaded = load_rotations(config)
    assert not loaded.warnings
    assert len(loaded.rotations) == 40
    groups = {(item.profile.unit_class, item.profile.unit_spec) for item in loaded.rotations}
    assert len(groups) == 40 and len({item.profile.unit_class for item in loaded.rotations}) == 13
    assert ("DEMONHUNTER", 3) in groups and ("DRUID", 4) in groups
    assert len({item.uuid for item in loaded.rotations}) == 40
    # 旧配置不批量补参数，首次加载副本仅补入已批准的玩家来源默认值。
    for path in directory.glob("*.toml"):
        expected = tomllib.loads(originals[path.name].decode("utf-8"))
        for condition in expected["conditions"]:
            if condition["plugin"] in {"player_has_buff@dev", "aura_player_buff_stacks@dev", "aura_player_buff_duration@dev"}:
                condition.setdefault("plugin_args", {}).setdefault("player_only", True)
        assert tomllib.loads(path.read_text(encoding="utf-8")) == expected
        assert (root / "rotations" / path.name).read_bytes() == originals[path.name]
    normalized = {path.name: path.read_bytes() for path in directory.glob("*.toml")}

    saved = config.path.read_bytes()
    paths = tomllib.loads(saved.decode("utf-8"))["rotations"]
    assert len(paths) == 40
    assert {Path(value).name for value in paths.values()} == set(originals)
    assert paths["demonhunter.devourer"].endswith("恶魔猎手-噬灭.toml")
    restarted = load_rotations(load_config(tmp_path))
    assert not restarted.warnings and config.path.read_bytes() == saved
    assert normalized == {path.name: path.read_bytes() for path in directory.glob("*.toml")}
    assert [(item.path, item.uuid) for item in restarted.rotations] == [(item.path, item.uuid) for item in loaded.rotations]

    executable = tmp_path / "_retail_/Wow.exe"
    executable.parent.mkdir()
    executable.touch()
    generated = generate_rotations(loaded.rotations, executable)
    assert generated.rotations is loaded.rotations
    toc = (generated.directory / "Phantom.toc").read_text(encoding="utf-8")
    files = [line.replace("\\", "/") for line in toc.splitlines() if line and not line.startswith("##")]
    assert len(files) == len(set(files))
    shared_count = sum(len(list((root / "phantom/lua" / folder).glob("*.lua"))) for folder in ("runtime", "general"))
    assert len(files) == shared_count + sum(len(item.conditions) + 1 for item in loaded.rotations)
    assert len({Path(name).stem for name in files}) == len(files)
    assert all(UUID(Path(name).stem).version == 4 for name in files)
    expected_directories = {SPECIALIZATION_BY_PROFILE[(item.profile.unit_class, item.profile.unit_spec)].key.replace(".", "_") for item in loaded.rotations}
    assert {Path(name).parent.as_posix() for name in files} == {"runtime", "general"} | expected_directories
    offset = shared_count
    for item in loaded.rotations:
        directory_name = SPECIALIZATION_BY_PROFILE[(item.profile.unit_class, item.profile.unit_spec)].key.replace(".", "_")
        for name in files[offset : offset + len(item.conditions) + 1]:
            assert Path(name).parent.as_posix() == directory_name
        offset += len(item.conditions) + 1
    assert sum("original: runtime\\14_specialization_reload.lua" in (generated.directory / name).read_text(encoding="utf-8") for name in files) == 1
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) local chunk, err = loadstring(source); assert(chunk, err); return true end")
    for name in files:
        assert compile_lua((generated.directory / name).read_text(encoding="utf-8")), name
