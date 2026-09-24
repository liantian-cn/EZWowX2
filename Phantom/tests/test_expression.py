import ast
from pathlib import Path

import pytest

from phantom.core.condition.contracts import Output, Value
from phantom.core.expression import evaluate, parse_expression
from phantom.core.rotation import RotationError, load_rotation

OUTPUTS = {"数量": Output("cell", value_type=int), "比例": Output("cell", value_type=float), "启用": Output("cell", value_type=bool), "名称": Output("cell", value_type=str), "列表": Output("cell", value_type=int, value_shape="list")}
VALUES: dict[str, Value] = {"数量": 2, "比例": 2.0, "启用": True, "名称": "火", "列表": [1, 2]}


@pytest.mark.parametrize(
    "source, expected",
    [
        ("数量 == 比例", True),
        ("0 < 数量 <= 2", True),
        ("数量 > 2 or 启用 and not False", True),
        ("not 数量 == 2", False),
        ("(数量 != 2 or False) and 启用", False),
        ("数量 in 列表", True),
        ("数量 not in [3, 4]", True),
        ("名称 in ['火', '冰']", True),
        ("数量 in []", False),
        ("数量 >= 2 and 比例 < 3.0", True),
        ("名称 == '冰'", False),
        ("True", True),
        ("False", False),
    ],
)
def test_allowed(source: str, expected: bool) -> None:
    assert evaluate(parse_expression(source, OUTPUTS), VALUES) is expected


@pytest.mark.parametrize(
    "source",
    [
        "数量.real == 2",
        "列表[0] == 1",
        "len(列表) == 2",
        "数量 + 1 == 3",
        "数量 is 2",
        "数量 is not 2",
        "(x := True)",
        "lambda: True",
        "[x for x in 列表]",
        "{1, 2}",
        "{'x': 1}",
        "(1, 2)",
        "None",
        "数量 == '2'",
        "启用 == 1",
        "数量 and 启用",
        "not 数量",
        "数量",
        "名称 in '火'",
        "列表 in [1, 2]",
        "数量 in [1, 2.0]",
        "数量 in [[1]]",
        "数量 in [数量]",
        "比例 in 列表",
        "未知 == 1",
        "数量 == -1",
        "数量 < True",
        "列表 < [1, 2]",
        "比例 == 1e999",
        "b'x' == b'x'",
    ],
)
def test_rejected(source: str) -> None:
    with pytest.raises((ValueError, SyntaxError)):
        parse_expression(source, OUTPUTS)


def test_short_circuit_and_reuse(monkeypatch: pytest.MonkeyPatch) -> None:
    expression = parse_expression("False and 启用 or True", OUTPUTS)

    def no_parse(*args: object, **kwargs: object) -> ast.Expression:
        raise AssertionError("运行时不能解析")

    monkeypatch.setattr(ast, "parse", no_parse)
    assert evaluate(expression, {})
    assert evaluate(expression, {})


def test_priority_idle_and_types(tmp_path: Path) -> None:
    path = tmp_path / "rotation.toml"
    path.write_bytes(Path("tests/fixtures/engine-rotation.toml").read_bytes())
    rotation = load_rotation(path)
    values: list[Value] = [100.0, 6, 2, True, 0.0, 0.0, 40.0, True, True, False]
    decision = rotation.decide(values)
    assert decision.rule_index == 2 and decision.macro is not None
    assert decision.macro.name == "灵界打击"
    values[7] = False
    assert rotation.decide(values).rule_index == 3
    values = [0.0, 0, 0, False, 0.0, 3.0, 100.0, False, True, False]
    decision = rotation.decide(values)
    assert decision.macro is None and decision.rule.macro == "Idle"
    with pytest.raises(ValueError):
        rotation.decide(values[:-1])
    values[0] = "0"
    with pytest.raises(ValueError):
        rotation.decide(values)


def test_invalid_expression_does_not_write_layout(tmp_path: Path) -> None:
    path = tmp_path / "rotation.toml"
    source = Path("tests/fixtures/engine-rotation.toml").read_text(encoding="utf-8")
    source = source.replace("符文数量>=1", "符文数量 + 1 > 0").replace("x = 7", "x = 99")
    path.write_text(source, encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(RotationError, match=r"rotation\[6\]"):
        load_rotation(path)
    assert path.read_bytes() == before


def test_trial_rejects_failed_or_missing_capture(tmp_path: Path) -> None:
    from demo.demo02 import describe_result
    from phantom.core.capture.contracts import CaptureResult, CaptureStatus

    path = tmp_path / "rotation.toml"
    path.write_bytes(Path("tests/fixtures/engine-rotation.toml").read_bytes())
    rotation = load_rotation(path)
    for result in (CaptureResult(), CaptureResult(status=CaptureStatus(True, "失败"))):
        with pytest.raises(ValueError):
            describe_result(rotation, result)
