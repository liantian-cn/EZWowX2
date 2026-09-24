"""验证固定快捷键池、宏声明顺序、旧字段忽略和容量边界。"""

from pathlib import Path

import pytest
import tomlkit

from phantom.core.keyboard.contracts import parse_key
from phantom.core.macro_keys import MACRO_KEYS
from phantom.core.rotation import RotationError, load_rotation, parse_macros


def test_fixed_pool_order_uniqueness_and_key_parsing() -> None:
    numpad = tuple(f"NUMPAD{digit}" for digit in "1234567890")
    function = tuple(f"F{number}" for number in range(1, 13))
    alt_function = tuple(key for key in function if key != "F4")
    punctuation = (",", ".", "/", ";", "'", "[", "]", "=")
    groups = (
        ("RCTRL", numpad),
        ("RSHIFT", numpad),
        ("RCTRL", function),
        ("RSHIFT", function),
        ("RALT", alt_function),
        ("RALT", numpad),
        ("RCTRL", punctuation),
        ("RALT", punctuation),
        ("RSHIFT", punctuation),
        ("RCTRL-RSHIFT", numpad),
        ("RALT-RSHIFT", numpad),
        ("RCTRL-RSHIFT", function),
        ("RALT-RSHIFT", alt_function),
        ("RCTRL-RSHIFT", punctuation),
        ("RALT-RSHIFT", punctuation),
    )
    assert MACRO_KEYS == tuple(f"{modifier}-{key}" for modifier, keys in groups for key in keys)
    assert len(MACRO_KEYS) == len(set(MACRO_KEYS)) == 148
    assert "RALT-F4" not in MACRO_KEYS and "RALT-RSHIFT-F4" not in MACRO_KEYS
    macros = parse_macros([{"name": f"宏{index}", "macro_text": f"/say {index}"} for index in range(148)])
    assert tuple(macro.key for macro in macros) == MACRO_KEYS
    assert tuple(macro.keys for macro in macros) == tuple(parse_key(key) for key in MACRO_KEYS)


@pytest.mark.parametrize("count", [0, 1, 148, 149])
def test_capacity_checked_before_load_writeback(tmp_path: Path, count: int) -> None:
    source = Path(__file__).parent / "fixtures/rotation-validation.toml"
    document = tomlkit.parse(source.read_text(encoding="utf-8"))
    document["macros"] = [{"name": f"宏{index}", "macro_text": "/say 测试"} for index in range(count)]
    document["rotation"] = []
    path = tmp_path / "rotation.toml"
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    before = path.read_bytes()
    if count > 148:
        with pytest.raises(RotationError, match="宏数量 149 超过快捷键容量 148"):
            load_rotation(path)
        assert path.read_bytes() == before
    else:
        rotation = load_rotation(path)
        assert tuple(macro.key for macro in rotation.macros) == MACRO_KEYS[:count]
        assert len(rotation.rules) == 1 and rotation.rules[0].macro == "Idle"
        saved = tomlkit.parse(path.read_text(encoding="utf-8"))
        assert all(set(macro) == {"name", "macro_text"} for macro in saved["macros"])


@pytest.mark.parametrize("legacy", [{"key": "ALT-F4", "bind_key": False}, {"key": "not a valid key", "bind_key": "not a boolean"}, {"key": 123, "bind_key": [1, 2]}, {"key": {"ignored": True}}, {"bind_key": 0}])
def test_legacy_fields_ignored_and_preserved(tmp_path: Path, legacy: dict[str, object]) -> None:
    document = tomlkit.parse((Path(__file__).parent / "fixtures/rotation-validation.toml").read_text(encoding="utf-8"))
    for name, value in legacy.items():
        document["macros"][0][name] = value
    path = tmp_path / "rotation.toml"
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    rotation = load_rotation(path)
    assert rotation.macros[0].key == "RCTRL-NUMPAD1"
    assert rotation.macros[0].keys == parse_key("RCTRL-NUMPAD1")
    saved = tomlkit.parse(path.read_text(encoding="utf-8"))
    for name, value in legacy.items():
        assert saved["macros"][0][name] == value


def test_declaration_order_is_independent_of_names_and_rule_order(tmp_path: Path) -> None:
    document = tomlkit.parse((Path(__file__).parent / "fixtures/rotation-validation.toml").read_text(encoding="utf-8"))
    document["macros"] = [{"name": name, "macro_text": "/say " + name} for name in ("Z", "未引用", "A")]
    document["rotation"] = [{"condition": "True", "macro": "A"}, {"condition": "True", "macro": "Z"}]
    for filename in ("first.toml", "second.toml"):
        path = tmp_path / filename
        path.write_text(tomlkit.dumps(document), encoding="utf-8")
        rotation = load_rotation(path)
        assert [(macro.name, macro.key) for macro in rotation.macros] == [("Z", "RCTRL-NUMPAD1"), ("未引用", "RCTRL-NUMPAD2"), ("A", "RCTRL-NUMPAD3")]
        assert [rule.macro for rule in rotation.rules] == ["A", "Z", "Idle"]
        assert load_rotation(path).macros == rotation.macros


@pytest.mark.parametrize("text", [None, "", " \n\t", False, 123])
def test_every_macro_requires_nonblank_text(text: object) -> None:
    table: dict[str, object] = {"name": "宏", "bind_key": False}
    if text is not None:
        table["macro_text"] = text
    with pytest.raises(ValueError):
        parse_macros([table])


def test_other_unknown_fields_still_rejected() -> None:
    with pytest.raises(ValueError, match="unknown"):
        parse_macros([{"name": "宏", "macro_text": "/say 测试", "unknown": True}])
