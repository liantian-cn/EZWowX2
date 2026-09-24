"""
Summary:
    加载时校验白名单表达式，运行时按已验证 AST 求值。
Description:
    类型校验禁止隐式真假转换；数值比较允许 int/float，成员判断要求元素类型一致。
    解释器仅实现声明的节点，布尔与链式比较短路，不调用 eval。
Key Variables:
    ValueType: 标量类型及列表形状，用于加载期推导。
Change Log:
    2026-09-13: Added 第 11 步表达式校验和解释器。
"""

import ast
import math
import operator
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

from phantom.core.condition.contracts import Output, Scalar, Value


@dataclass(frozen=True)
class ValueType:
    scalar: type[bool] | type[int] | type[float] | type[str] | None
    is_list: bool = False


BOOL = ValueType(bool)
COMPARISONS: dict[type[ast.cmpop], Callable[..., bool]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}


def parse_expression(source: str, outputs: Mapping[str, Output]) -> ast.Expression:
    expression = ast.parse(source, mode="eval")

    def infer(node: ast.AST) -> ValueType:
        if isinstance(node, ast.Constant):
            if type(node.value) not in (bool, int, float, str):
                raise ValueError("不允许此字面量")
            if isinstance(node.value, float) and not math.isfinite(node.value):
                raise ValueError("浮点字面量必须有限")
            return ValueType(type(cast(Scalar, node.value)))
        if isinstance(node, ast.Name):
            if node.id not in outputs:
                raise ValueError(f"表达式引用未知条件：{node.id}")
            output = outputs[node.id]
            return ValueType(output.value_type, output.value_shape == "list")
        if isinstance(node, ast.List):
            if any(not isinstance(item, ast.Constant) for item in node.elts):
                raise ValueError("列表只允许同类型标量字面量")
            items = [infer(item) for item in node.elts]
            if items and any(item != items[0] for item in items):
                raise ValueError("列表元素类型必须一致")
            return ValueType(items[0].scalar if items else None, True)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            if infer(node.operand) != BOOL:
                raise ValueError("not 需要布尔值")
            return BOOL
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            if any(infer(value) != BOOL for value in node.values):
                raise ValueError("and/or 需要布尔值")
            return BOOL
        if isinstance(node, ast.Compare):
            left = infer(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                right = infer(comparator)
                if type(operation) not in COMPARISONS:
                    raise ValueError("不允许此比较运算符")
                if isinstance(operation, (ast.In, ast.NotIn)):
                    valid = not left.is_list and right.is_list and right.scalar in (None, left.scalar)
                else:
                    numeric = left.scalar in (int, float) and right.scalar in (int, float)
                    valid = left == right or (numeric and not left.is_list and not right.is_list)
                    if isinstance(operation, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                        valid = valid and not left.is_list and left.scalar in (int, float, str)
                if not valid:
                    raise ValueError("比较操作数类型或形状不匹配")
                left = right
            return BOOL
        raise ValueError(f"不允许的表达式节点：{type(node).__name__}")

    if infer(expression.body) != BOOL:
        raise ValueError("条件表达式结果必须为布尔值")
    return expression


def evaluate(expression: ast.Expression, values: Mapping[str, Value]) -> bool:
    def visit(node: ast.AST) -> Value:
        if isinstance(node, ast.Constant):
            return cast(Scalar, node.value)
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.List):
            return [cast(Scalar, visit(item)) for item in node.elts]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not visit(node.operand)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(visit(value) for value in node.values)
            if isinstance(node.op, ast.Or):
                return any(visit(value) for value in node.values)
        if isinstance(node, ast.Compare):
            left = visit(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                right = visit(comparator)
                if not COMPARISONS[type(operation)](left, right):
                    return False
                left = right
            return True
        raise ValueError("表达式未经白名单校验")

    result = visit(expression.body)
    if type(result) is not bool:
        raise ValueError("表达式结果不是布尔值")
    return result
