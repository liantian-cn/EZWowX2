"""
Summary:
    目标当前施法图标。
Description:
    参数：无参数；拒绝多余字段。
    输出：icon_tile，1 个区域，str scalar；8×8 像素，采样内部 6×6。
    API：UnitCastingInfo/UnitChannelInfo("target") 第 3 项返回可能秘密的 textureID；用 NeverSecret 的 delayTimeMs/isEmpowered 判断状态。
    秘密纹理通过 IconTile:SetIcon 直接显示，不消费 SetTexture 返回值；沿用玩家样式，角标不表示打断许可。
    核验：2026-09-18，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：内部 6×6 RGB hash，空槽或解码异常返回 ""；单位消失或无施法时清空，不保证纹理设置失败时隐藏角标。
Key Variables:
    None
Change Log:
    2026-09-18: Added 按已确认的目标条件迁移计划新增 target_cast_icon@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """目标当前施法图标；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("icon_tile", value_type=str))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> str:
        return icon_tiles[0].hash or ""

    def fallback_value(self) -> str:
        """无法识别时表示没有可报告的目标或图标。"""
        return ""
