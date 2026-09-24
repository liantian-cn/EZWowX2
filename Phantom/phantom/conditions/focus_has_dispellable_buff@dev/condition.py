"""
Summary:
    焦点是否有指定类型可驱散增益。
Description:
    参数：dispel_types 父表必填，键限定 Magic/Poison/Disease/Curse/Stealth/Special/Enrage；加载成功后补齐缺失子键为 false，空表或全 false 不匹配。
    输出：cell，1 个区域，bool scalar；4×4 像素，采样内部 2×2。
    API：AuraContainer:AddAuraSlot(key, "HELPFUL|RAID_PLAYER_DISPELLABLE", options)；options.candidateFilters.includeDispelTypes 为类型布尔映射，容器管理显示；UpdateAllAuras() 请求刷新。
    要求敌人单位、团队有人可驱散与类型匹配；不保证玩家本人能驱散，Enrage 键游戏待验；空表或全 false 匹配不到任何增益。不读取秘密 AuraData。
    核验：2026-09-18，@wow-ui-source，12.1.0.69587，
    revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58；具体来源和限制见 template.lua。
    解码：严格全黑/全白；不可用或异常兜底 False。
Key Variables:
    dispel_types: 键限定 Magic/Poison/Disease/Curse/Stealth/Special/Enrage；未列出为 false，空表或全 false 不匹配。
Change Log:
    2026-09-19: Changed 显式声明驱散子键默认值，保留父表必填并按实例合并校验。
    2026-09-18: Added 按已确认的焦点条件迁移计划新增 focus_has_dispellable_buff@dev。
"""

from collections.abc import Mapping
from typing import ClassVar

from phantom.core.condition.base import Condition
from phantom.core.condition.contracts import Output
from phantom.core.pixels import Cell, IconTile, PixelDecoder, ValueBar
from phantom.core.validation import Boolean, Fields, Table


class Plugin(Condition):
    """焦点是否有指定类型可驱散增益；参数、像素解码及异常兜底均属于本插件。"""

    config_defaults: ClassVar[Mapping[str, object]] = {"dispel_types": {"Magic": False, "Poison": False, "Disease": False, "Curse": False, "Stealth": False, "Special": False, "Enrage": False}}

    def __init__(self, args: dict[str, object]) -> None:
        Fields(frozenset({"dispel_types"})).validate(args, "plugin_args")
        defaults = Table().validate(self.config_defaults["dispel_types"], "config_defaults.dispel_types")
        allowed = frozenset(defaults)
        values = Table().validate(args["dispel_types"], "dispel_types")
        Fields(frozenset(), allowed).validate(values, "dispel_types")
        # 用户值覆盖默认值后严格校验；新字典保证实例独立且不修改默认声明。
        self.dispel_types: dict[str, bool] = {key: Boolean().validate(value, f"dispel_types.{key}") for key, value in (defaults | values).items()}
        super().__init__(Output("cell", value_type=bool))

    def template_parameters(self) -> dict[str, str]:
        """序列化已验证的配置；坐标由冻结布局注入。"""
        # 只序列化白名单键和已验证的布尔值，不接受任意 Lua 文本。
        entries = (f'["{key}"] = {str(value).lower()}' for key, value in sorted(self.dispel_types.items()))
        return {"dispel_types": ", ".join(entries)}

    def decode_value(self, cells: list[Cell], value_bars: list[ValueBar], icon_tiles: list[IconTile], *, decoder: PixelDecoder) -> bool:
        cell = cells[0]
        if not cell.is_black and not cell.is_white:
            raise ValueError("需要纯黑或纯白 Cell")
        return cell.is_white

    def fallback_value(self) -> bool:
        """无法识别时表示未确认条件成立。"""
        return False
