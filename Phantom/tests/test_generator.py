import os
import stat
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import numpy as np
import pytest
from lupa.lua51 import LuaRuntime  # type: ignore[import-untyped]

from phantom.core import generator
from phantom.core.condition.contracts import Region
from phantom.core.condition.registry import Registry
from phantom.core.generator import generate, generate_rotations, render, render_rotations
from phantom.core.macro_keys import MACRO_KEYS
from phantom.core.pixels import PixelDecoder
from phantom.core.rotation import Rotation, atomic_write, load_rotation, parse_macros
from phantom.core.specializations import SPECIALIZATION_BY_PROFILE

ROOT = Path(__file__).resolve().parents[1]


def specialization_files(sources: dict[str, str], rotation: Rotation) -> dict[str, str]:
    prefix = SPECIALIZATION_BY_PROFILE[(rotation.profile.unit_class, rotation.profile.unit_spec)].key.replace(".", "_") + "/"
    return {name: source for name, source in sources.items() if name.startswith(prefix)}


def assert_output_contract(sources: dict[str, str], rotations: tuple[Rotation, ...]) -> None:
    identifiers = [UUID(Path(name).stem) for name in sources]
    assert len(identifiers) == len(set(identifiers))
    assert all(identifier.version == 4 and str(identifier) == Path(name).stem for identifier, name in zip(identifiers, sources, strict=True))
    names = iter(sources)
    for directory in ("runtime", "general"):
        for path in sorted((generator.LUA_ROOT / directory).glob("*.lua")):
            name = next(names)
            assert Path(name).parent.as_posix() == directory
            original = path.read_text(encoding="utf-8")
            original_uuid = next(line for line in original.splitlines() if line.startswith("uuid: "))
            assert sources[name] == original.replace(original_uuid, f"uuid: {Path(name).stem}", 1)
    for rotation in rotations:
        expected_directory = SPECIALIZATION_BY_PROFILE[(rotation.profile.unit_class, rotation.profile.unit_spec)].key.replace(".", "_")
        for entry in rotation.conditions:
            name = next(names)
            assert Path(name).parent.as_posix() == expected_directory
            identifier = Path(name).stem
            assert f"uuid: {identifier}\n" in sources[name]
            # 模板原样追加到独立 chunk；空模板也保留有标识和守卫的文件。
            template = entry.instance.generate_lua(identifier)
            assert sources[name].endswith("local addonName, addonTable = ...\n\n" + template)
            assert f'~= "{rotation.profile.unit_class}"' in sources[name]
            assert f"~= {rotation.profile.unit_spec} then" in sources[name]
        macro_name = next(names)
        assert Path(macro_name).parent.as_posix() == expected_directory
        assert f"uuid: {Path(macro_name).stem}\n" in sources[macro_name]
        assert "local function BindMacro" in sources[macro_name]
    assert next(names, None) is None


def test_render_has_fresh_uuid4_files_and_dependency_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rotations = tuple(reversed(rotation_pair(tmp_path)))
    before = rotations[0].path.read_bytes()
    first = render_rotations(rotations, "Phantom")
    # 逆序 UUID 明确证明 TOC 不按随机文件名排序。
    identifiers = iter(UUID(int=index, version=4) for index in range(1000, 0, -1))
    monkeypatch.setattr(generator, "uuid4", lambda: next(identifiers))
    second = render_rotations(rotations, "Phantom")
    for sources in (first, second):
        lua_sources = {name: source for name, source in sources.items() if name.endswith(".lua")}
        assert_output_contract(lua_sources, rotations)
        toc = [line.replace("\\", "/") for line in sources["Phantom.toc"].splitlines() if line and not line.startswith("##")]
        assert toc == list(lua_sources)
    assert set(first).intersection(second) == {"Phantom.toc"}
    assert rotations[0].path.read_bytes() == before


@pytest.mark.parametrize("collision_at", [1, 11, 16, 17])
def test_uuid_collision_rejects_package_before_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, collision_at: int) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotation,), executable)
    before = {name: (result.directory / name).read_bytes() for name in result.files}
    identifiers = [uuid4() for _ in range(collision_at)]
    identifiers.append(identifiers[0])
    sequence = iter(identifiers)
    monkeypatch.setattr(generator, "uuid4", lambda: next(sequence))
    with pytest.raises(ValueError, match="UUID 碰撞"):
        generate_rotations((rotation,), executable)
    assert before == {name: (result.directory / name).read_bytes() for name in result.files}


@pytest.mark.parametrize("count", [0, 2, 148])
def test_macro_bindings_preserve_text_and_bind_every_macro(tmp_path: Path, count: int) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    text = '/cast [@target] 测试\n/say "quote" \\123\r\t\x00123'
    macros = parse_macros([{"name": f"宏{index}", "macro_text": text + str(index), "key": "ALT-F4", "bind_key": False} for index in range(count)])
    rotation = replace(rotation, conditions=(), macros=macros)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state: Any = lua.execute("""
        local state = {buttons={}, bindings={}}
        UnitClass = function() return "死亡骑士", "DEATHKNIGHT" end
        C_SpecializationInfo = {GetSpecialization=function() return 1 end}
        CreateFrame = function(kind, name, parent, template)
            assert(kind == "Button" and template == "SecureActionButtonTemplate")
            local frame = {name=name, attributes={}}
            function frame:SetAttribute(key,value) self.attributes[key]=value end
            function frame:RegisterForClicks(down,up)
                assert(down=="AnyDown" and up=="AnyUp")
                self.registered = true
            end
            table.insert(state.buttons, frame)
            return frame
        end
        SetOverrideBindingClick = function(frame, priority, key, name)
            assert(priority and frame.name==name and frame.registered)
            table.insert(state.bindings, {key=key, frame=frame})
        end
        return state
    """)
    source = next(iter(specialization_files(render(rotation, "TestPhantom"), rotation).values()))
    execute: Any = lua.eval("function(source) assert(loadstring(source))('TestPhantom', {}) end")
    execute(source)
    assert len(state.buttons) == len(state.bindings) == count
    for index, macro in enumerate(macros, 1):
        assert state.buttons[index].attributes["type"] == "macro"
        assert state.buttons[index].attributes.macrotext == macro.macro_text
        assert state.bindings[index].key == macro.key == MACRO_KEYS[index - 1]
        assert state.buttons[index].name == "TestPhantomButton" + UUID(rotation.uuid).hex + str(index - 1)
    assert len({state.buttons[index].name for index in range(1, count + 1)}) == count


def copy_rotation(tmp_path: Path) -> Path:
    path = tmp_path / "blood.toml"
    path.write_bytes((ROOT / "tests/fixtures/engine-rotation.toml").read_bytes())
    return path


def fake_executable(tmp_path: Path) -> Path:
    executable = tmp_path / "_retail_/Wow.exe"
    executable.parent.mkdir()
    executable.touch()
    return executable


def test_generate_real_tree_cleans_all_stale_files_and_preserves_siblings(tmp_path: Path) -> None:
    path = copy_rotation(tmp_path)
    executable = fake_executable(tmp_path)
    result = generate(path, executable, "TestPhantom")
    shared_count = sum(len(list((generator.LUA_ROOT / folder).glob("*.lua"))) for folder in ("runtime", "general"))
    media_count = sum(path.is_file() for path in (generator.LUA_ROOT / "media").rglob("*"))
    assert len(result.files) == shared_count + media_count + 2 + len(result.rotation.conditions)
    for name in ("old.lua", ".hidden", "old/nested/manual.txt", "runtime/manual.lua"):
        stale = result.directory / name
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("old", encoding="utf-8")
    sibling = result.directory.parent / "OtherAddon"
    sibling.mkdir()
    (sibling / "manual.lua").write_bytes(b"sibling")
    toc = result.directory / "TestPhantom.toc"
    toc.write_text("outdated", encoding="utf-8")
    regenerated = generate(path, executable, "TestPhantom")
    references = [line for line in toc.read_text(encoding="utf-8").splitlines() if line and not line.startswith("##")]
    assert len(references) == shared_count + 1 + len(result.rotation.conditions)
    assert all((result.directory / name.replace("\\", "/")).is_file() for name in references)
    assert all("examples" not in name and "old.lua" not in name for name in references)
    assert {file.relative_to(result.directory).as_posix() for file in result.directory.rglob("*") if file.is_file()} == set(regenerated.files)
    assert (sibling / "manual.lua").read_bytes() == b"sibling"
    assert references[-1].startswith("deathknight_blood\\")
    assert set(name for name in result.files if name.endswith(".lua")).isdisjoint(regenerated.files)
    assert regenerated.rotation.uuid == result.rotation.uuid
    for source in (ROOT / "phantom/lua/media").rglob("*"):
        if source.is_file():
            destination = result.directory / source.relative_to(ROOT / "phantom/lua")
            assert destination.read_bytes() == source.read_bytes()
    assert not any("media" in name for name in references)


def rotation_pair(tmp_path: Path) -> tuple[Rotation, Rotation]:
    path = copy_rotation(tmp_path)
    first = load_rotation(path)
    second = load_rotation(path)
    return first, replace(second, uuid=str(uuid4()), profile=replace(second.profile, unit_spec=2))


def test_generate_collection_writes_shared_files_once_and_toc_last(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rotations = rotation_pair(tmp_path)
    executable = fake_executable(tmp_path)
    writes: list[Path] = []

    def record_write(path: Path, content: str | bytes) -> None:
        writes.append(path)
        atomic_write(path, content)

    def reject_load(path: Path) -> Rotation:
        raise AssertionError(f"集合生成不得重读 rotation：{path}")

    monkeypatch.setattr(generator, "atomic_write", record_write)
    monkeypatch.setattr(generator, "load_rotation", reject_load)
    rotations[0].path.unlink()
    result = generate_rotations(rotations, executable, "TestPhantom")
    assert result.rotations is rotations
    assert len(writes) == len(set(writes)) == len(result.files)
    assert writes[-1].name == result.files[-1] == "TestPhantom.toc"
    references = [line.replace("\\", "/") for line in writes[-1].read_text(encoding="utf-8").splitlines() if line and not line.startswith("##")]
    sources = {name: (result.directory / name).read_text(encoding="utf-8") for name in references}
    assert_output_contract(sources, rotations)
    for asset in (generator.LUA_ROOT / "media").rglob("*"):
        if asset.is_file():
            name = asset.relative_to(generator.LUA_ROOT).as_posix()
            assert result.files.count(name) == 1
            assert (result.directory / name).read_bytes() == asset.read_bytes()


@pytest.mark.parametrize("conflict", ["group", "uuid"])
def test_collection_rejects_duplicates_before_render_or_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, conflict: str) -> None:
    first, second = rotation_pair(tmp_path)
    second = replace(second, profile=first.profile) if conflict == "group" else replace(second, uuid=first.uuid)
    executable = fake_executable(tmp_path)

    def reject_render(instance_id: str) -> str:
        raise AssertionError("重复集合不应开始渲染")

    monkeypatch.setattr(first.conditions[0].instance, "generate_lua", reject_render)
    message = "重复职业专精" if conflict == "group" else "重复 UUID"
    with pytest.raises(ValueError, match=message):
        render_rotations((first, second), "Phantom")
    with pytest.raises(ValueError, match=message):
        generate_rotations((first, second), executable)
    assert not (executable.parent / "Interface").exists()


def test_collection_rejects_empty_before_write(tmp_path: Path) -> None:
    executable = fake_executable(tmp_path)
    with pytest.raises(ValueError, match="不能为空"):
        render_rotations((), "Phantom")
    with pytest.raises(ValueError, match="不能为空"):
        generate_rotations((), executable)
    assert not (executable.parent / "Interface").exists()


def test_second_rotation_render_failure_preserves_all_existing_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rotations = rotation_pair(tmp_path)
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotations[0],), executable)
    old = {path.relative_to(result.directory): path.read_bytes() for path in result.directory.rglob("*") if path.is_file()}
    rendered: list[str] = []
    generate_first = rotations[0].conditions[0].instance.generate_lua

    def record_first(instance_id: str) -> str:
        rendered.append("first")
        return generate_first(instance_id)

    def fail_second(instance_id: str) -> str:
        rendered.append("second")
        raise ValueError("第二份渲染失败")

    monkeypatch.setattr(rotations[0].conditions[0].instance, "generate_lua", record_first)
    monkeypatch.setattr(rotations[1].conditions[0].instance, "generate_lua", fail_second)
    with pytest.raises(ValueError, match="第二份渲染失败"):
        generate_rotations(rotations, executable)
    assert rendered == ["first", "second"]
    assert old == {path.relative_to(result.directory): path.read_bytes() for path in result.directory.rglob("*") if path.is_file()}
    assert specialization_files(render(rotations[0], "Phantom"), rotations[0])


def test_single_rotation_wrappers_preserve_results(tmp_path: Path) -> None:
    path = copy_rotation(tmp_path)
    executable = fake_executable(tmp_path)
    single = generate(path, executable, "TestPhantom")
    collection = generate_rotations((single.rotation,), executable, "TestPhantom")
    assert single.directory == collection.directory
    assert len(single.files) == len(collection.files)
    assert single.rotation.uuid == collection.rotations[0].uuid
    assert collection.rotations[0] is single.rotation
    for sources in (render(single.rotation, "TestPhantom"), render_rotations((single.rotation,), "TestPhantom")):
        assert_output_contract({name: source for name, source in sources.items() if name.endswith(".lua")}, (single.rotation,))


@pytest.mark.parametrize(("unit_class", "spec", "active"), [("DEATHKNIGHT", 1, 0), ("DEATHKNIGHT", 2, 1), ("MAGE", 1, None)])
def test_collection_lua_guards_select_only_matching_rotation(tmp_path: Path, unit_class: str, spec: int, active: int | None) -> None:
    rotations = rotation_pair(tmp_path)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/conditions_harness.lua").read_text(encoding="utf-8"))
    state["class"] = unit_class
    state.spec = spec
    execute: Any = lua.eval("function(source, addon) assert(loadstring(source))('Phantom', addon) end")
    sources = render_rotations(rotations, "Phantom")
    for index, rotation in enumerate(rotations):
        before = len(state.frames)
        for source in specialization_files(sources, rotation).values():
            execute(source, addon)
        assert (len(state.frames) > before) == (index == active)


def test_invalid_generation_does_not_touch_existing_output(tmp_path: Path) -> None:
    path = copy_rotation(tmp_path)
    executable = fake_executable(tmp_path)
    result = generate(path, executable)
    old = {name: (result.directory / name).read_bytes() for name in result.files}
    path.write_text(path.read_text(encoding="utf-8").replace("max_power = 120", "max_power = 0"), encoding="utf-8")
    with pytest.raises(ValueError):
        generate(path, executable)
    assert old == {name: (result.directory / name).read_bytes() for name in result.files}
    with pytest.raises(ValueError):
        generate(path, executable, "../Other")


@pytest.mark.parametrize("failure", ["toc", "asset", "missing_asset"])
def test_preparation_failure_preserves_existing_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotation,), executable)
    before = {name: (result.directory / name).read_bytes() for name in result.files}
    read_bytes = Path.read_bytes
    read_text = Path.read_text
    rglob = Path.rglob

    def read_asset(path: Path) -> bytes:
        if path == generator.LUA_ROOT / "media/UiFont.ttf":
            raise OSError("资源读取失败")
        return read_bytes(path)

    def read_toc(path: Path, *args: Any, **kwargs: Any) -> str:
        if path == generator.LUA_ROOT / "addonTemplateName.toc":
            raise OSError("TOC 读取失败")
        return read_text(path, *args, **kwargs)

    if failure == "toc":
        monkeypatch.setattr(Path, "read_text", read_toc)
    elif failure == "asset":
        monkeypatch.setattr(Path, "read_bytes", read_asset)
    else:
        monkeypatch.setattr(Path, "rglob", lambda path, pattern: iter(()) if path == generator.LUA_ROOT / "media" else rglob(path, pattern))
    with pytest.raises((OSError, ValueError), match="读取失败|资源缺失"):
        generate_rotations((rotation,), executable)
    assert before == {name: read_bytes(result.directory / name) for name in result.files}


@pytest.mark.parametrize("part", ["Interface", "Interface/AddOns", "Interface/AddOns/Phantom"])
def test_output_directory_file_is_rejected_before_cleanup(tmp_path: Path, part: str) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    target = executable.parent / part
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"keep")
    with pytest.raises(ValueError, match="不是目录"):
        generate_rotations((rotation,), executable)
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("part", ["Interface", "Interface/AddOns", "Interface/AddOns/Phantom", "Interface/AddOns/Phantom/unused/deep"])
def test_reparse_points_are_rejected_before_any_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, part: str) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotation,), executable)
    target = executable.parent / part
    target.mkdir(parents=True, exist_ok=True)
    before = {name: (result.directory / name).read_bytes() for name in result.files}
    lstat = Path.lstat

    class ReparseStat:
        st_mode = stat.S_IFDIR
        st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT

    def marked_lstat(path: Path, *args: Any, **kwargs: Any) -> Any:
        return ReparseStat() if path == target else lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", marked_lstat)
    with pytest.raises(ValueError, match="危险链接"):
        generate_rotations((rotation,), executable)
    assert before == {name: (result.directory / name).read_bytes() for name in result.files}


@pytest.mark.parametrize("part", ["Interface", "Interface/AddOns", "Interface/AddOns/Phantom", "Interface/AddOns/Phantom/old/link"])
def test_real_directory_links_are_rejected(tmp_path: Path, part: str) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    outside = tmp_path / "sibling"
    outside.mkdir()
    (outside / "keep").write_bytes(b"untouched")
    target = executable.parent / part
    target.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(outside), str(target))
    else:
        target.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="危险链接"):
            generate_rotations((rotation,), executable)
        assert (outside / "keep").read_bytes() == b"untouched"
        assert list(outside.iterdir()) == [outside / "keep"]
    finally:
        if os.name == "nt":
            target.rmdir()
        else:
            target.unlink()


@pytest.mark.skipif(os.name == "nt", reason="Windows 文件符号链接需要额外权限；Windows 使用 junction 和 reparse double 验证")
@pytest.mark.parametrize("dangling", [False, True])
def test_old_tree_file_symlink_is_rejected(tmp_path: Path, dangling: bool) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotation,), executable)
    outside = tmp_path / "outside.lua"
    if not dangling:
        outside.write_bytes(b"keep")
    (result.directory / ".old-link").symlink_to(outside)
    with pytest.raises(ValueError, match="危险链接"):
        generate_rotations((rotation,), executable)
    assert (result.directory / "Phantom.toc").is_file()
    assert outside.exists() is not dangling


@pytest.mark.parametrize("operation", ["unlink", "rmdir"])
def test_cleanup_failure_stops_without_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotation,), executable)
    (result.directory / "000-old").mkdir()
    (result.directory / "000-old/file").write_bytes(b"old")
    calls: list[Path] = []

    def fail_cleanup(path: Path, *args: object, **kwargs: object) -> None:
        calls.append(path)
        raise OSError("清理失败")

    def reject_write(path: Path, content: str | bytes) -> None:
        raise AssertionError("清理失败后不得写入")

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, operation, fail_cleanup)
        patcher.setattr(generator, "atomic_write", reject_write)
        with pytest.raises(OSError, match="清理失败"):
            generate_rotations((rotation,), executable)
    assert len(calls) == 1
    assert (result.directory / "Phantom.toc").is_file()


def test_write_failure_stops_without_publishing_toc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    executable = fake_executable(tmp_path)
    result = generate_rotations((rotation,), executable)
    calls: list[Path] = []

    def fail_second_write(path: Path, content: str | bytes) -> None:
        calls.append(path)
        if len(calls) == 2:
            raise OSError("写入失败")
        atomic_write(path, content)

    monkeypatch.setattr(generator, "atomic_write", fail_second_write)
    with pytest.raises(OSError, match="写入失败"):
        generate_rotations((rotation,), executable)
    assert len(calls) == 2
    assert not (result.directory / "Phantom.toc").exists()
    assert {path for path in result.directory.rglob("*") if path.is_file()} == {calls[0]}


def test_lua51_syntax_for_every_generated_file(tmp_path: Path) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    compile_lua: Any = lua.eval("function(source) local f,err=loadstring(source); assert(f,err); return true end")
    for name, content in render(rotation, "Phantom").items():
        assert "{{" not in content, name
        if name.endswith(".lua"):
            assert compile_lua(content), name


def test_generated_lua_roundtrip_gcd_and_events(tmp_path: Path) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    sources = specialization_files(render(rotation, "Phantom"), rotation)
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state: Any
    addon: Any
    state, addon = lua.execute((ROOT / "tests/lua/conditions_harness.lua").read_text(encoding="utf-8"))
    execute: Any = lua.eval("function(source, addon) local f=assert(loadstring(source)); f('Phantom', addon) end")
    for source in sources.values():
        execute(source, addon)
    state.initialize(state)
    state.update(state)
    assert state.queries[61304] == 1
    assert state.queries[195292] == 1
    pixels = np.zeros((20, rotation.board_width, 3), dtype=np.uint8)
    pixels[:4, 4:8] = 6
    pixels[:4, 8:12] = 1
    for index in range(1, 8):
        pixels[4:8, index * 4 : index * 4 + 4] = round(state.cells[index].brightness)
    pixels[8:12, 4:6] = [255, 0, 0]
    pixels[8:12, 6:10] = 255
    pixels[8:12, 14:16] = [255, 0, 0]
    assert state.bars[1].value == 1
    assert rotation.values(PixelDecoder(pixels)) == [40.0, 3, 1, True, 2.5, 0.0, 40.0, True, False, False]
    state.runes = 5
    state.event(state, "RUNE_POWER_UPDATE")
    state.flushTimers(state)
    assert state.cells[2].brightness == 5
    state.power = 1
    state.event(state, "UNIT_DISPLAYPOWER")
    state.flushTimers(state)
    assert state.cells[1].brightness == 255
    state.charges = 2
    state.event(state, "SPELL_UPDATE_CHARGES")
    state.flushTimers(state)
    assert state.bars[1].value == 2
    state.remaining[61304] = None
    state.update(state)
    assert state.cells[4].brightness == 0
    state.remaining[61304] = 0
    state.update(state)
    assert state.cells[4].brightness == 255
    state.known[195292] = False
    state.event(state, "SPELLS_CHANGED")
    state.flushTimers(state)
    state.update(state)
    assert state.cells[5].brightness == 0


@pytest.mark.parametrize(("unit_class", "spec"), [("MAGE", 1), ("DEATHKNIGHT", 2)])
def test_lua_guard_registers_no_conditions(tmp_path: Path, unit_class: str, spec: int) -> None:
    rotation = load_rotation(copy_rotation(tmp_path))
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state: Any
    addon: Any
    state, addon = lua.execute((ROOT / "tests/lua/conditions_harness.lua").read_text(encoding="utf-8"))
    state["class"] = unit_class
    state.spec = spec
    run: Any = lua.eval("function(source, addon) assert(loadstring(source))('Phantom',addon) end")
    for source in specialization_files(render(rotation, "Phantom"), rotation).values():
        run(source, addon)
    assert len(addon.UIInitFuncs) == 0
    assert len(state.frames) == 0


@pytest.mark.parametrize(
    ("identifier", "args"),
    [
        ("spec_power_rune", {}),
        ("player_primary_power", {"max_power": 120}),
        ("player_health_pct", {}),
        ("spell_overlay", {"spell_ids": [50842]}),
        ("spell_usable", {"spell_ids": [49998]}),
        ("spell_gcd", {}),
        ("spell_cooldown", {"spell_ids": [195292], "ignore_gcd": True}),
    ],
)
def test_templates_use_frozen_xy(identifier: str, args: dict[str, object]) -> None:
    plugin = Registry().create(f"{identifier}@dev", args)
    # 非默认行揭示模板中隐藏的 y=2；注册器本身不决定布局策略。
    plugin.freeze((Region(7, 1),))
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/conditions_harness.lua").read_text(encoding="utf-8"))
    run: Any = lua.eval("function(source, addon) assert(loadstring(source))('Phantom',addon) end")
    run(plugin.generate_lua("instance"), addon)
    assert len(state.cells) == 0  # 构造仍延迟到 UIInitFuncs。
    state.initialize(state)
    assert (state.cells[7].x, state.cells[7].y) == (7, 1)


@pytest.mark.parametrize("identifier", ["spell_cooldown", "spell_gcd"])
@pytest.mark.parametrize("seconds", [0.0, 2.5, 5.0, 17.5, 30.0, 92.5, 155.0, 265.0, 375.0])
def test_generated_cooldown_curve_roundtrips_all_segments(identifier: str, seconds: float) -> None:
    args: dict[str, object] = {"spell_ids": [195292], "ignore_gcd": True} if identifier == "spell_cooldown" else {}
    plugin = Registry().create(f"{identifier}@dev", args)
    plugin.freeze((Region(1, 2),))
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/conditions_harness.lua").read_text(encoding="utf-8"))
    state.remaining[195292 if identifier == "spell_cooldown" else 61304] = seconds
    run: Any = lua.eval("function(source, addon) assert(loadstring(source))('Phantom',addon) end")
    run(plugin.generate_lua("instance"), addon)
    state.initialize(state)
    state.update(state)
    pixels = np.zeros((20, 32, 3), dtype=np.uint8)
    pixels[4:8, 4:8] = round(state.cells[1].brightness)
    # 像素量化在最慢区间每级为 4 秒，误差最多半级。
    decoder = PixelDecoder(pixels)
    assert plugin.value(*plugin.raw_value(decoder), decoder=decoder) == pytest.approx(seconds, abs=2.0)


def test_charge_template_uses_nondefault_width_and_position() -> None:
    plugin = Registry().create("spell_charges@dev", {"spell_ids": [50842], "max_charges": 5, "width": 5})
    plugin.freeze((Region(4, width=5),))
    lua: Any = LuaRuntime(unpack_returned_tuples=True)
    state, addon = lua.execute((ROOT / "tests/lua/conditions_harness.lua").read_text(encoding="utf-8"))
    setup: Any = lua.eval("""function(addon, state)
        addon.ValueBar.New = function(self, x, width, reverse)
            assert(reverse == false)
            local bar = {x=x, width=width}
            function bar:setMinMaxValues(low, high) self.low=low; self.high=high end
            function bar:setValue(value) self.value=value end
            state.bars[x]=bar
            return bar
        end
    end""")
    setup(addon, state)
    run: Any = lua.eval("function(source, addon) assert(loadstring(source))('Phantom',addon) end")
    run(plugin.generate_lua("instance"), addon)
    state.initialize(state)
    bar = state.bars[4]
    assert (bar.x, bar.width, bar.low, bar.high, bar.value) == (4, 5, 0, 5, 1)
