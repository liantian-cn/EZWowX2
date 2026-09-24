from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_MACRO_PATH = REPO_ROOT / "Terminal" / "terminal" / "rotation" / "PriestDiscipline.py"
LUA_MACRO_PATH = REPO_ROOT / "DejaVu" / "DejaVu_Priest" / "Discipline" / "Macro.lua"

PYTHON_MACRO_RE = re.compile(r'"([^"]+)":\s*"([^"]+)",')
LUA_MACRO_RE = re.compile(
    r'insert\(macroList,\s*\{\s*title = "([^"]+)",\s*key = "([^"]+)",\s*text = "((?:[^"\\]|\\.)*)"\s*\}\)'
)

UNIT_PREFIXES = ("player", "party1", "party2", "party3", "party4")
UNIT_HEAL_SPELLS = {
    "苦修": "苦修",
    "快速治疗": "快速治疗",
    "真言术盾": "真言术：盾",
    "纯净术": "纯净术",
    "耀": "真言术：耀",
    "灌注": "能量灌注",
}
ENEMY_SPELLS = {
    "痛": "暗言术：痛",
    "灭": "暗言术：灭",
    "心灵震爆": "心灵震爆",
    "苦修": "苦修",
    "惩击": "惩击",
}


def parse_python_macro_table() -> list[tuple[str, str]]:
    source = PYTHON_MACRO_PATH.read_text(encoding="utf-8")
    start = source.index("self.macroTable = {")
    end = source.index("\n        }\n", start)
    block = source[start:end]
    return PYTHON_MACRO_RE.findall(block)


def parse_lua_macro_list() -> list[tuple[str, str, str]]:
    source = LUA_MACRO_PATH.read_text(encoding="utf-8")
    macros: list[tuple[str, str, str]] = []
    for title, key, text in LUA_MACRO_RE.findall(source):
        parsed_text = text.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
        macros.append((title, key, parsed_text))
    return macros


def expected_text(title: str) -> str:
    if title == "reloadUI":
        return "/reload"

    for unit in UNIT_PREFIXES:
        if title.startswith(unit):
            spell_key = title[len(unit) :]
            spell_name = UNIT_HEAL_SPELLS[spell_key]
            return f"/focus {unit} \n/cast [@{unit}] {spell_name}"

    if title in ("绝望祷言", "福音"):
        return f"/cast {title}"

    if title.startswith("target"):
        spell_key = title[len("target") :]
        return f"/cast [@target] {ENEMY_SPELLS[spell_key]}"

    if title.startswith("focus"):
        spell_key = title[len("focus") :]
        return f"/cast [@focus] {ENEMY_SPELLS[spell_key]}"

    raise AssertionError(f"unexpected macro title: {title}")


def test_priest_discipline_macro_lua_matches_rotation_macro_table() -> None:
    python_macros = parse_python_macro_table()
    lua_macros = parse_lua_macro_list()

    assert lua_macros[0] == ("reloadUI", "CTRL-F12", "/reload")

    expected_titles_and_keys = [("reloadUI", "CTRL-F12"), *python_macros]
    actual_titles_and_keys = [(title, key) for title, key, _ in lua_macros]
    assert actual_titles_and_keys == expected_titles_and_keys

    expected_text_by_title = {
        title: expected_text(title) for title, _ in expected_titles_and_keys
    }
    actual_text_by_title = {title: text for title, _, text in lua_macros}
    assert actual_text_by_title == expected_text_by_title
