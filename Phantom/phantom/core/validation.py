"""
Summary:
    提供与业务字段无关的可组合输入校验器。
Description:
    校验器返回经过检查的强类型值；调用方决定字段名、范围和业务含义。
    不把 Python 的 bool 当作整数，不做字符串到数值的隐式转换。
Key Variables:
    Validator: 所有输入校验器的统一抽象接口。
Change Log:
    2026-09-13: Added 插件与配置共享的对象化基础校验。
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Validator[T](ABC):
    @abstractmethod
    def validate(self, value: object, name: str) -> T:
        """返回合法值；失败时抛出包含字段上下文的 ValueError。"""
        raise NotImplementedError


class PositiveNumber(Validator[float]):
    def validate(self, value: object, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} 必须为有限正数")
        try:
            result = float(value)
        except OverflowError as error:
            raise ValueError(f"{name} 必须为有限正数") from error
        if not math.isfinite(result) or result <= 0:
            raise ValueError(f"{name} 必须为有限正数")
        return result


class PositiveInteger(Validator[int]):
    def validate(self, value: object, name: str) -> int:
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} 必须为正整数")
        return value


class Boolean(Validator[bool]):
    def validate(self, value: object, name: str) -> bool:
        if type(value) is not bool:
            raise ValueError(f"{name} 必须为布尔值")
        return value


@dataclass(frozen=True)
class String(Validator[str]):
    allow_empty: bool = False

    def validate(self, value: object, name: str) -> str:
        if not isinstance(value, str) or (not self.allow_empty and not value.strip()):
            raise ValueError(f"{name} 必须为{'可空' if self.allow_empty else '非空'}字符串")
        return value


class Table(Validator[dict[str, object]]):
    def validate(self, value: object, name: str) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ValueError(f"{name} 必须为表")
        return {str(key): item for key, item in value.items()}


@dataclass(frozen=True)
class Fields(Validator[dict[str, object]]):
    required: frozenset[str]
    optional: frozenset[str] = frozenset()

    def validate(self, value: object, name: str) -> dict[str, object]:
        table = Table().validate(value, name)
        missing = self.required - table.keys()
        unknown = table.keys() - self.required - self.optional
        if missing or unknown:
            raise ValueError(f"{name} 缺少字段 {sorted(missing)}；未知字段 {sorted(unknown)}")
        return table


@dataclass(frozen=True)
class Items[T](Validator[list[T]]):
    item: Validator[T]
    nonempty: bool = False

    def validate(self, value: object, name: str) -> list[T]:
        if not isinstance(value, list) or (self.nonempty and not value):
            raise ValueError(f"{name} 必须为{'非空' if self.nonempty else ''}数组")
        return [self.item.validate(entry, f"{name}[{index}]") for index, entry in enumerate(value)]
