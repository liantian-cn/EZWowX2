import pytest

from phantom.core.validation import Boolean, Fields, Items, PositiveInteger, PositiveNumber, String, Table, Validator


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.5, "1", None])
def test_integer_rejects_non_positive_or_non_integer(value: object) -> None:
    with pytest.raises(ValueError, match="field"):
        PositiveInteger().validate(value, "field")


@pytest.mark.parametrize("value", [True, 0, -1, "1", float("nan"), float("inf"), 10**1000])
def test_number_rejects_nonfinite_and_coercion(value: object) -> None:
    with pytest.raises(ValueError, match="field"):
        PositiveNumber().validate(value, "field")


def test_nested_validation_preserves_order_and_error_context() -> None:
    validator = Items(PositiveInteger(), nonempty=True)
    assert validator.validate([8, 2, 8], "candidates") == [8, 2, 8]
    for value in ([], (1, 2), [1, False]):
        with pytest.raises(ValueError, match="candidates"):
            validator.validate(value, "candidates")
    fields = Fields(frozenset({"required"}), frozenset({"optional"}))
    assert fields.validate({"required": 1}, "args") == {"required": 1}
    assert fields.validate({"required": 1, "optional": 2}, "args")["optional"] == 2
    with pytest.raises(ValueError, match="未知字段"):
        fields.validate({"required": 1, "extra": 2}, "args")
    with pytest.raises(ValueError, match="缺少字段"):
        fields.validate({}, "args")
    assert Items(Table()).validate([{"a": 1}], "tables") == [{"a": 1}]


def test_primitive_types_and_abstract_contract() -> None:
    assert PositiveInteger().validate(1, "n") == 1
    assert type(PositiveNumber().validate(1, "n")) is float
    assert PositiveNumber().validate(0.5, "n") == 0.5
    assert Boolean().validate(False, "flag") is False
    with pytest.raises(ValueError):
        Boolean().validate(0, "flag")
    assert String(allow_empty=True).validate("", "text") == ""
    with pytest.raises(ValueError):
        String().validate("  ", "text")
    with pytest.raises(TypeError):
        Validator()  # type: ignore[abstract]
