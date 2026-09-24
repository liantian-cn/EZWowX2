"""
Summary:
    玩家预测生命值百分比。
Description:
    参数：use_predicted 为 bool，默认 true；无单位为 0。
    输出：cell，1 个区域，float scalar；4×4 像素。
    API：UnitHealthPercent；UnitDocumentation.lua。秘密生命值经颜色曲线直接渲染。
    核验：2026-09-12，@wow-ui-source，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58，12.1.0.69587。
    解码：Cell.percent。
    不可用或解码异常兜底 0.0。
Key Variables:
    None
Change Log:
    2026-09-19: Changed 显式声明配置默认值，构造与配置补写共用默认来源。
    2026-09-18: Changed 增加 use_predicted 参数，与目标及焦点生命条件统一。
    2026-09-14: Changed 直接读取像素属性并在插件内完成校验和业务转换，移除解码器封装。
    2026-09-14: Changed 解码接口接收同帧 PixelDecoder，保留原有业务解码。
    2026-09-13: Changed 组合校验器与解码器，保持 @1.0 配对语义。
    2026-09-12: Added player_health_pct@1.0 配对编解码。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields


class Plugin(Condition):
    """校验实例参数，声明输出，再将像素解释为本条件业务值。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"use_predicted": True}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset(), frozenset({"use_predicted"})).validate(args, "plugin_args")
        self.use_predicted: bool = Boolean().validate(args.get("use_predicted", self.config_defaults["use_predicted"]), "use_predicted")
        # 输出声明只依赖已验证参数，随后由核心分配并冻结区域。
        super().__init__(Output("cell", value_type=float))

    def template_parameters(self) -> dict[str, str]:
        return {"use_predicted": str(self.use_predicted).lower()}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> float:
        cell = cells[0]
        if not cell.is_pure or not bool((cell.inner[0, 0] == cell.inner[0, 0, 0]).all()):
            raise ValueError("需要纯灰色 Cell")
        return cell.percent

    def fallback_value(self) -> float:
        """本版本的不可用业务值，亦用于核心捕获的解码异常。"""
        return 0.0
