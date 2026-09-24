"""
Summary:
    读取玩家首个匹配增益的原生剩余时长条百分比。
Description:
    aura_ids 必填且为非空正整数列表；player_only 为可选 bool，默认 True 使用 HELPFUL|PLAYER，False 使用 HELPFUL。
    不接受 duration 或 width；单个 ValueBar 输出 float scalar，固定内容宽度 5 Cell（20×4 像素），含红色分隔占 6 Cell（24×4）。
    官方 AuraSlot.SetDurationBar 使用 Immediate / RemainingTime 绑定原生时长显示；Lua 不读取或比较秘密光环时长。
    沿用 12.1.0 (69587)、revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58 的既有 API 基线，来源详见 template.lua。
    Python 原样返回 ValueBar.ratio * 100，范围 0.0–100.0，不舍入、不换算秒数、不硬量化为 5 的倍数。
    只统计中间两行的纯白和纯黑像素；灰色不进入分母，两行不一致或部分灰色时可产生非 5 倍数。
    无光环、无有效黑白像素或解码异常返回 0.0；永久光环交官方处理，不保证满条，游戏渲染需另行验收。
Key Variables:
    aura_ids: 官方槽候选光环 ID 集合，不保证按配置列表顺序首匹配。
    config_defaults: 构造与 rotation 默认值补写共用的 player_only 默认声明。
Change Log:
    2026-09-20: Added 固定 20 像素内容宽度的玩家增益剩余时长百分比插件。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, Items, PositiveInteger


class Plugin(Condition):
    """直接输出官方时长条的像素百分比。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"player_only": True}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"aura_ids"}), frozenset({"player_only"})).validate(args, "plugin_args")
        self.aura_ids: tuple[int, ...] = tuple(Items(PositiveInteger(), nonempty=True).validate(args["aura_ids"], "aura_ids"))
        self.player_only: bool = Boolean().validate(args.get("player_only", self.config_defaults["player_only"]), "player_only")
        # 固定内容宽度由输出契约交给布局器，模板不维护第二份宽度来源。
        super().__init__(Output("value_bar", value_type=float, widths=(5,)))

    def template_parameters(self) -> dict[str, str]:
        return {"aura_ids": ", ".join(str(value) for value in self.aura_ids), "aura_filter": '"HELPFUL|PLAYER"' if self.player_only else '"HELPFUL"'}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        # 5% 仅是两行一致且全部内容为黑白时的一整列名义步长，不额外量化。
        return value_bars[0].ratio * 100.0

    def fallback_value(self) -> float:
        return 0.0
