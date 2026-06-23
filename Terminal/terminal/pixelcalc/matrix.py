from typing import Any

import numpy as np

from .cell import Cell, MegaCell, BadgeCell, CharCell
from .color_map import COLOR_MAP

__all__ = ['MatrixDecoder']


class MatrixDecoder(object):
    """矩阵解码器，用于将像素矩阵解码为字符矩阵。
    对应插件端 DejaVu\\03_matrix\\01_matrix_frame.lua"""

    def __init__(self, martix_pix_array: np.ndarray) -> None:
        self.martix_pix_array: np.ndarray = martix_pix_array

    def getCell(self, x: int, y: int) -> Cell:
        """DejaVu\\03_matrix\\02_cell.lua"""
        start_x: int = x * 4
        start_y: int = y * 4
        end_x: int = start_x + 4
        end_y: int = start_y + 4
        cell_pix_array: np.ndarray = self.martix_pix_array[start_y:end_y, start_x:end_x]
        return Cell(x, y, cell_pix_array)

    def getMegaCell(self, x: int, y: int) -> MegaCell:
        """DejaVu\\03_matrix\\03_mega_cell.lua"""
        start_x: int = x * 4
        start_y: int = y * 4
        end_x: int = start_x + 8
        end_y: int = start_y + 8
        cell_pix_array: np.ndarray = self.martix_pix_array[start_y:end_y, start_x:end_x]
        return MegaCell(x, y, cell_pix_array)

    def getBadgeCell(self, x: int, y: int) -> BadgeCell:
        """DejaVu\\03_matrix\\04_badge_cell.lua"""
        start_x: int = x * 4
        start_y: int = y * 4
        end_x: int = start_x + 8
        end_y: int = start_y + 8
        cell_pix_array: np.ndarray = self.martix_pix_array[start_y:end_y, start_x:end_x]
        return BadgeCell(x, y, cell_pix_array)

    def readCharCell(self, x: int, y: int) -> int:
        """DejaVu\\03_matrix\\05_char_cell.lua"""
        start_x: int = x * 4
        start_y: int = y * 4
        end_x: int = start_x + 8
        end_y: int = start_y + 8
        cell_pix_array: np.ndarray = self.martix_pix_array[start_y:end_y, start_x:end_x]
        cell = CharCell(x, y, cell_pix_array)
        return cell.count

    def readBarValue(self, x: int, y: int, length: int) -> float:
        """读取 DejaVu\\03_matrix\\06_bar_cell.lua 定义的bar的值"""
        # nodes_middle_pix: list[np.ndarray] = [self.cell(x, top).full.array[3:5, :] for x in range(left, left + length)]
        start_x: int = x * 4
        start_y: int = y * 4
        end_x: int = start_x + length * 4
        end_y: int = start_y + 4
        bar_pix_array: np.ndarray = self.martix_pix_array[start_y:end_y, start_x:end_x]
        inner_pix_array: np.ndarray = bar_pix_array[1:3, :]
        white_mask = np.all(inner_pix_array == (255, 255, 255), axis=2)
        white_count: int = int(np.count_nonzero(white_mask))
        total_count: int = int(inner_pix_array.shape[0] * inner_pix_array.shape[1])
        return 100.0 * white_count / total_count if total_count > 0 else 0.0

    def readCooldownSpell(self, x: int = 2, y: int = 0, length: int = 40) -> list[dict[str, Any]]:
        """读取 DejaVu\\05_slots\\12_cooldown_spell.lua 定义的冷却技能"""
        result: list[dict[str, Any]] = []
        for i in range(length):
            pos_x = x + i*2
            pos_y = y
            icon_cell = self.getBadgeCell(pos_x, pos_y)
            if icon_cell.footnote.is_pure and icon_cell.footnote.is_black:
                continue
            cooldown_cell = self.getCell(pos_x, pos_y+2)
            highlight_cell = self.getCell(pos_x+1, pos_y+2)
            usable_cell = self.getCell(pos_x, pos_y+3)
            known_cell = self.getCell(pos_x+1, pos_y+3)
            spell = {
                "is_charge": False,
                "charges": 0,
                "title": icon_cell.title,
                "cooldown": cooldown_cell.remaining,
                "highlight": highlight_cell.is_not_black,
                "is_usable": usable_cell.is_not_black,
                "is_known": known_cell.is_not_black,
            }
            result.append(spell)

        return result

    def readChargeSpell(self, x: int = 62, y: int = 4, length: int = 11) -> list[dict[str, Any]]:
        """读取 DejaVu\\05_slots\\13_charge_spell.lua 定义的充电技能"""
        result: list[dict[str, Any]] = []
        for i in range(length):
            pos_x = x + i*2
            pos_y = y
            icon_cell = self.getBadgeCell(pos_x, pos_y)
            if icon_cell.footnote.is_pure and icon_cell.footnote.is_black:
                continue
            cooldown_cell = self.getCell(pos_x, pos_y+2)
            highlight_cell = self.getCell(pos_x+1, pos_y+2)
            usable_cell = self.getCell(pos_x, pos_y+3)
            known_cell = self.getCell(pos_x+1, pos_y+3)
            charge_cell = self.readCharCell(pos_x, pos_y+4)
            spell = {
                "is_charge": True,
                "charges": charge_cell,
                "title": icon_cell.title,
                "cooldown": cooldown_cell.remaining,
                "highlight": highlight_cell.is_not_black,
                "is_usable": usable_cell.is_not_black,
                "is_known": known_cell.is_not_black,
            }
            result.append(spell)
        return result

    def readSpell(self) -> list[dict[str, Any]]:
        """读取 DejaVu\\05_slots\\13_charge_spell.lua 定义的技能"""

        spell_list: list[dict[str, Any]] = []
        spell_list.extend(self.readCooldownSpell())
        spell_list.extend(self.readChargeSpell())
        return spell_list

    def readAura(self, x: int, y: int, length: int = 11) -> list[dict[str, Any]]:
        """读取 DejaVu\\05_slots\\21_aura_sequence.lua 定义的法术"""
        aura_list: list[dict[str, Any]] = []
        for i in range(length):
            pos_x = x + i*2
            pos_y = y
            icon_cell = self.getBadgeCell(pos_x, pos_y)
            if icon_cell.footnote.is_pure and icon_cell.footnote.is_black:
                continue
            remain_cell = self.getCell(pos_x, pos_y+2)
            type_cell = self.getCell(pos_x+1, pos_y+2)
            count_cell = self.readCharCell(pos_x, pos_y+3)
            auraData = {
                "title": icon_cell.title,
                "remain": remain_cell.remaining,
                "color_string": type_cell.color_string,
                "type": COLOR_MAP["SPELL_TYPE"].get(type_cell.color_string, "UNKNOWN"),
                "count": count_cell,
            }
            aura_list.append(auraData)

        return aura_list

    def readBadgeCellList(self, x: int, y: int, length: int) -> list[str]:
        """读取类似DejaVu\\06_spec\\51_dispel_blacklist.lua的BadgeCell列表"""
        result:  list[str] = []
        for i in range(length):
            pos_x = x + i*2
            pos_y = y
            icon_cell = self.getBadgeCell(pos_x, pos_y)
            if icon_cell.footnote.is_pure and icon_cell.footnote.is_black:
                continue
            if not icon_cell.footnote.is_pure:
                continue
            result.append(icon_cell.title)
        return result

    def readCellList(self, x: int, y: int, length: int) -> dict[str, dict[str, Any] | None]:
        """
        为SPEC和SETTING服务，因为每个Cell在不同条件下，内容的意义不一样，所以干脆读出来。
        """
        result: dict[str, dict[str, Any] | None] = {}
        for i in range(length):
            pos_x = x + i
            pos_y = y
            cell = self.getCell(pos_x, pos_y)
            if cell.is_pure:
                result[f"{i}"] = {
                    "pure": True,
                    "mean": cell.mean,
                    "percent": cell.percent,
                    "decimal": cell.decimal,
                    "is_black": cell.is_black,
                    "is_white": cell.is_white,
                    "color_string": cell.color_string,
                }
            else:
                result[f"{i}"] = None
        return result

    def readUTFhash(self, x: int, y: int) -> str | None:
        icon_cell = self.getBadgeCell(x, y)
        if not icon_cell.footnote.is_pure:
            return None
        return icon_cell.hash

    def readUTFString(self, x: int, y: int, length: int) -> str | None:
        char_list = []

        def rgb_to_char(r: int, g: int, b: int) -> str:
            byte_list = [value for value in (r, g, b) if value != 0] or [0]
            return bytes(byte_list).decode("utf-8")

        try:
            for i in range(length):
                pos_x = x + i
                pos_y = y
                cell = self.getCell(pos_x, pos_y)
                if not cell.is_pure:
                    return None
                r, g, b = cell.color
                char_list.append(rgb_to_char(r, g, b))

            result = "".join(char_list)
            start = result.find("*#")
            if start == -1:
                return None

            end = result.find("*#", start + 2)
            if end == -1:
                return None

            return result[start + 2:end]
        except Exception:
            return None
