"""
Summary:
    管理条件配置默认值、布局冻结、原始区域读取与业务值兜底。
Description:
    参数校验和业务解码由插件组合实现；基类提供默认值声明入口并维护条件生命周期。
Key Variables:
    Condition._regions: 本实例冻结的输出区域。
Change Log:
    2026-09-19: Added 可持久化的配置默认值声明，未声明的插件保持空默认值。
    2026-09-14: Changed 支持同帧解码器、零区域冻结与可选 Lua 模板。
    2026-09-13: Changed 按确认计划拆分条件核心职责。
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from phantom.core.condition.contracts import Output, Raw, Region, Value
from phantom.core.condition.template import render_template
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar


class Condition(ABC):
    # 插件构造与 rotation 补写共用此声明；嵌套表按键补齐，不修改共享默认值。
    config_defaults: ClassVar[Mapping[str, object]] = {}

    def __init__(self, output: Output) -> None:
        self._output: Output = output
        self._regions: tuple[Region, ...] = ()
        self._frozen: bool = False
        self._template: Path | None = None

    @property
    def output(self) -> Output:
        return self._output

    @property
    def regions(self) -> tuple[Region, ...]:
        return self._regions

    def freeze(self, regions: tuple[Region, ...]) -> None:
        if self._frozen:
            raise ValueError("条件布局已冻结")
        if len(regions) != self.output.output_count:
            raise ValueError("布局数量与输出声明不符")
        if not self.output.accepts(self.fallback_value()):
            raise ValueError("插件兜底与业务类型声明不符")
        self._regions = regions
        self._frozen = True

    def set_template(self, path: Path) -> None:
        self._template = path

    def layout(self) -> dict[str, object]:
        return {"output_type": self.output.output_type, "regions": [region.metadata() for region in self.regions]}

    def raw_value(self, decoder: PixelDecoder) -> Raw:
        if not self._frozen:
            raise ValueError("条件尚未分配布局")
        cells: list[Cell] = []
        bars: list[ValueBar] = []
        icons: list[IconTile] = []
        for region in self.regions:
            if self.output.output_type == "cell":
                assert region.y is not None
                cells.append(decoder.getCell(region.x, region.y))
            elif self.output.output_type == "value_bar":
                assert region.width is not None
                bars.append(decoder.getValueBar(region.x, region.width))
            else:
                icons.append(decoder.getIconTile(region.x))
        return cells, bars, icons

    def value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        try:
            lengths = {"cell": len(cells), "value_bar": len(value_bars), "icon_tile": len(icon_tiles)}
            if any(length != (self.output.output_count if kind == self.output.output_type else 0) for kind, length in lengths.items()):
                raise ValueError("输入区域数量与输出声明不符")
            result = self.decode_value(cells, value_bars, icon_tiles, decoder=decoder)
            if not self.output.accepts(result):
                raise ValueError("解码返回值与声明不符")
            return result
        except Exception:
            return self.fallback_value()

    def generate_lua(self, instance_id: str) -> str:
        if not self._frozen:
            raise ValueError("布局尚未就绪")
        if self._template is None:
            return ""
        return render_template(self._template, self.regions, self.template_parameters(), instance_id)

    def template_parameters(self) -> dict[str, str]:
        return {}

    @abstractmethod
    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> Value:
        raise NotImplementedError

    @abstractmethod
    def fallback_value(self) -> Value:
        raise NotImplementedError
