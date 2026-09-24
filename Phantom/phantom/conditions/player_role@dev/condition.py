"""
Summary:
    玩家职责。
Description:
    参数：无参数；拒绝多余字段。
    输出：cell，1 个区域，str scalar；4×4 像素，采样内部 2×2。
    API：role = UnitGroupRolesAssigned("player")；返回职责字符串，单位身份受限时可能秘密。
    NONE/TANK/HEALER/DAMAGER 对应灰度字节 0/85/170/255；秘密职责显示 NONE。
    核验：2026-09-15，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：NONE/TANK/HEALER/DAMAGER 对应灰度字节 0/85/170/255；秘密职责显示 NONE。；不可用或异常兜底 "NONE"。
Key Variables:
    None
Change Log:
    2026-09-15: Added 按已确认的玩家条件迁移计划新增 player_role@dev。
"""

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Fields


class Plugin(Condition):
    """玩家职责；参数、像素解码及异常兜底均属于本插件。"""

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset()).validate(args, "plugin_args")
        super().__init__(Output("cell", value_type=str))

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> str:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        roles = {0: "NONE", 85: "TANK", 170: "HEALER", 255: "DAMAGER"}
        brightness = int(cell.mean)
        if brightness not in roles:
            raise ValueError("无效职责灰度")
        return roles[brightness]

    def fallback_value(self) -> str:
        """无法识别时表示职责未分配。"""
        return "NONE"
