"""High-level pixel protocol decoding."""

import traceback
from datetime import datetime
from typing import Any

from .node import GridCell, GridDecoder
from ..utils.image_utils import COLOR_MAP


def read_std_node(node: GridCell) -> dict[str, Any]:
    # Keep a stable shape for downstream JSON consumers.
    result: dict[str, Any] = {
        'is_pure': node.is_pure,
        'title': None,
        'hash': None,
        'color_string': None,
        'is_white': None,
        'percent': None,
        'mean': None,
        'decimal': None,
    }
    if node.is_pure:
        result.update(
            {
                'color_string': node.color_string,
                'is_white': node.is_white,
                'percent': node.percent,
                'mean': node.mean,
                'decimal': node.decimal,
            }
        )
        return result
    result.update({'title': node.title, 'hash': node.hash})
    return result


def extract_all_data(extractor: GridDecoder) -> dict[str, Any]:
    data: dict[str, Any] = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'misc': {},
        'spec': {},
        # Keep unitToken camelCase for game protocol compatibility.
        'player': {'unitToken': 'player'},
        'target': {'unitToken': 'target'},
        'focus': {'unitToken': 'focus'},
        'party': {},
        'signal': {}
    }
    try:
        #############################################
        # Misc
        #############################################
        data['misc']['ac'] = extractor.cell(34, 5).title
        data['misc']['on_chat'] = extractor.cell(35, 5).is_white
        data['misc']['is_targeting'] = extractor.cell(36, 5).is_white
        data['misc']['flash_node'] = extractor.cell(37, 5).color_string
        data['misc']['enemy_count'] = extractor.cell(34, 6).mean / 5
        data['misc']['delay'] = extractor.cell(35, 6).is_white
        #############################################
        # Player
        #############################################
        data['player']['aura'] = {'buff_sequence': [], 'buff': {}, 'debuff_sequence': [], 'debuff': {}}
        data['player']['aura']['buff_sequence'], data['player']['aura']['buff'] = extractor.read_aura_sequence(left=2, top=5, length=32)
        data['player']['aura']['debuff_sequence'], data['player']['aura']['debuff'] = extractor.read_aura_sequence(left=2, top=8, length=8)
        data['player']['spell_sequence'], data['player']['spell'] = extractor.read_spell_sequence(left=2, top=2, length=36)
        data['player']['status'] = {
            'unit_damage_absorbs': extractor.read_health_bar(left=38, top=2, length=8) * 100,
            'unit_heal_absorbs': extractor.read_health_bar(left=38, top=3, length=8) * 100,
            'unit_health': extractor.cell(45, 4).percent,
            'unit_power': extractor.cell(45, 5).percent,
            'unit_in_combat': extractor.cell(38, 4).is_white,
            'unit_in_movement': extractor.cell(39, 4).is_white,
            'unit_in_vehicle': extractor.cell(40, 4).is_white,
            'unit_is_empowering': extractor.cell(41, 4).is_white,
            'unit_cast_icon': None,
            'unit_cast_duration': None,
            'unit_channel_icon': None,
            'unit_channel_duration': None,
            'unit_class': 'NONE',
            'unit_role': 'NONE',
            'unit_is_dead_or_ghost': extractor.cell(40, 5).is_white,
            'unit_is_alive': extractor.cell(40, 5).is_black,
            'unit_in_range': True,
            # Keep combat_time key name to match existing game-side contract.
            "combat_time": extractor.cell(41, 5).mean
        }
        cast_icon_node: GridCell = extractor.cell(42, 4)
        if cast_icon_node.is_not_pure:
            data['player']['status']['unit_cast_icon'] = cast_icon_node.title
            data['player']['status']['unit_cast_duration'] = extractor.cell(43, 4).percent
        channel_icon_node: GridCell = extractor.cell(42, 5)
        if channel_icon_node.is_not_pure:
            data['player']['status']['unit_channel_icon'] = channel_icon_node.title
            data['player']['status']['unit_channel_duration'] = extractor.cell(43, 5).percent
        class_node: GridCell = extractor.cell(38, 5)
        if class_node.is_pure:
            data['player']['status']['unit_class'] = COLOR_MAP['Class'].get(class_node.color_string, 'NONE')
        role_node: GridCell = extractor.cell(39, 5)
        if role_node.is_pure:
            data['player']['status']['unit_role'] = COLOR_MAP['Role'].get(role_node.color_string, 'NONE')
        #############################################
        # Target
        #############################################
        data['target']['aura'] = {'debuff_sequence': [], 'debuff': {}}
        # target/focus keep exists under status for historical API compatibility.
        data['target']['status'] = {'exists': extractor.cell(38, 6).is_white}
        if data['target']['status']['exists']:
            data['target']['aura']['debuff_sequence'], data['target']['aura']['debuff'] = extractor.read_aura_sequence(left=10, top=8, length=16)
            data['target']['status'].update(
                {
                    'unit_can_attack': extractor.cell(39, 6).is_white,
                    'unit_is_self': extractor.cell(40, 6).is_white,
                    'unit_is_alive': extractor.cell(41, 6).is_white,
                    'unit_in_combat': extractor.cell(42, 6).is_white,
                    'unit_in_range': extractor.cell(43, 6).is_white,
                    'unit_health': extractor.cell(45, 6).percent,
                    'unit_cast_icon': None,
                    'unit_cast_duration': None,
                    'unit_cast_interruptible': None,
                    'unit_channel_icon': None,
                    'unit_channel_duration': None,
                    'unit_channel_interruptible': None
                }
            )
            target_cast_node: GridCell = extractor.cell(38, 7)
            if target_cast_node.is_not_pure:
                data['target']['status']['unit_cast_icon'] = target_cast_node.title
                data['target']['status']['unit_cast_duration'] = extractor.cell(39, 7).percent
                data['target']['status']['unit_cast_interruptible'] = extractor.cell(40, 7).is_white
            target_channel_node: GridCell = extractor.cell(41, 7)
            if target_channel_node.is_not_pure:
                data['target']['status']['unit_channel_icon'] = target_channel_node.title
                data['target']['status']['unit_channel_duration'] = extractor.cell(42, 7).percent
                data['target']['status']['unit_channel_interruptible'] = extractor.cell(43, 7).is_white
        #############################################
        # Focus
        #############################################
        data['focus']['aura'] = {'debuff_sequence': [], 'debuff': {}}
        # target/focus keep exists under status for historical API compatibility.
        data['focus']['status'] = {'exists': extractor.cell(38, 8).is_white}
        if data['focus']['status']['exists']:
            data['focus']['aura']['debuff_sequence'], data['focus']['aura']['debuff'] = extractor.read_aura_sequence(left=26, top=8, length=8)
            data['focus']['status'].update(
                {
                    'unit_can_attack': extractor.cell(39, 8).is_white,
                    'unit_is_self': extractor.cell(40, 8).is_white,
                    'unit_is_alive': extractor.cell(41, 8).is_white,
                    'unit_in_combat': extractor.cell(42, 8).is_white,
                    'unit_in_range': extractor.cell(43, 8).is_white,
                    'unit_health': extractor.cell(45, 8).percent,
                    'unit_cast_icon': None,
                    'unit_cast_duration': None,
                    'unit_cast_interruptible': None,
                    'unit_channel_icon': None,
                    'unit_channel_duration': None,
                    'unit_channel_interruptible': None
                }
            )
            focus_cast_node: GridCell = extractor.cell(38, 9)
            if focus_cast_node.is_not_pure:
                data['focus']['status']['unit_cast_icon'] = focus_cast_node.title
                data['focus']['status']['unit_cast_duration'] = extractor.cell(39, 9).percent
                data['focus']['status']['unit_cast_interruptible'] = extractor.cell(40, 9).is_white
            focus_channel_node: GridCell = extractor.cell(41, 9)
            if focus_channel_node.is_not_pure:
                data['focus']['status']['unit_channel_icon'] = focus_channel_node.title
                data['focus']['status']['unit_channel_duration'] = extractor.cell(42, 9).percent
                data['focus']['status']['unit_channel_interruptible'] = extractor.cell(43, 9).is_white
        #############################################
        # Party
        #############################################
        for i in range(1, 5):
            party_key: str = f'party{i}'
            # party keeps root-level exists/unitToken for old backend compatibility.
            data['party'][party_key] = {'exists': False, 'unitToken': party_key, 'status': {}, 'aura': {}}
            party_exist: bool = extractor.cell(12 * i - 2, 14).is_white
            data['party'][party_key]['exists'] = party_exist
            if party_exist:
                data['party'][party_key]['status'] = {
                    'exists': True,  # Keep duplicated status.exists for compatibility.
                    'unit_in_range': extractor.cell(12 * i - 1, 14).is_white,
                    'unit_health': extractor.cell(12 * i, 14).percent,
                    'unit_is_alive': extractor.cell(12 * i + 1, 14).is_white,
                    # selected key name is kept to avoid breaking existing consumers.
                    'selected': extractor.cell(12 * i, 15).is_white,
                    'unit_damage_absorbs': extractor.read_health_bar(left=12 * i - 10, top=14, length=8) * 100,
                    'unit_heal_absorbs': extractor.read_health_bar(left=12 * i - 10, top=15, length=8) * 100
                }
                party_class_node: GridCell = extractor.cell(12 * i - 2, 15)
                data['party'][party_key]['status']['unit_class'] = COLOR_MAP['Class'].get(party_class_node.color_string, 'NONE') if party_class_node.is_pure else 'NONE'
                party_role_node: GridCell = extractor.cell(12 * i - 1, 15)
                data['party'][party_key]['status']['unit_role'] = COLOR_MAP['Role'].get(party_role_node.color_string, 'NONE') if party_role_node.is_pure else 'NONE'
                data['party'][party_key]['aura'] = {'buff_sequence': [], 'buff': {}, 'debuff_sequence': [], 'debuff': {}}
                data['party'][party_key]['aura']['buff_sequence'], data['party'][party_key]['aura']['buff'] = extractor.read_aura_sequence(left=12 * i - 4, top=11, length=6)
                data['party'][party_key]['aura']['debuff_sequence'], data['party'][party_key]['aura']['debuff'] = extractor.read_aura_sequence(left=12 * i - 10, top=11, length=6)
        #############################################
        # Signal
        #############################################
        signal_nodes = [extractor.cell(x, 10) for x in range(38, 46)]
        data['signal'] = {i: read_std_node(node) for i, node in enumerate(signal_nodes, start=1)}
        spec_nodes = [extractor.cell(x, y) for x in range(34, 38) for y in range(8, 11)]
        data['spec'] = {i: read_std_node(node) for i, node in enumerate(spec_nodes, start=1)}
        icon_list_1_nodes = [extractor.cell(x, 0) for x in range(2, 50)]
        data['icon_list_1'] = [node.title for node in icon_list_1_nodes if node.is_not_pure]
        icon_list_2_nodes = [extractor.cell(x, 1) for x in range(2, 50)]
        data['icon_list_2'] = [node.title for node in icon_list_2_nodes if node.is_not_pure]
        icon_list_3_nodes = [extractor.cell(x, 16) for x in range(2, 50)]
        data['icon_list_3'] = [node.title for node in icon_list_3_nodes if node.is_not_pure]
        icon_list_4_nodes = [extractor.cell(x, 17) for x in range(2, 50)]
        data['icon_list_4'] = [node.title for node in icon_list_4_nodes if node.is_not_pure]

    except Exception as exc:
        print(f'[extract_all_data] 发生错误:\n{traceback.format_exc()}')
        data['error'] = f'数据提取失败: {str(exc)}'
    return data
