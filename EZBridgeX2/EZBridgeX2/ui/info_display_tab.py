from __future__ import annotations
from typing import Any, Callable, cast
from PySide6.QtCore import QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QCursor, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import QApplication, QAbstractItemView, QGraphicsOpacityEffect, QGroupBox, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class CopyPathLabel(QLabel):
    def __init__(self, text: str, copy_path: str, on_copy: Callable[[str], None], parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._copy_path: str = copy_path
        self._on_copy: Callable[[str], None] = on_copy
        self.setToolTip(copy_path)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._copy_path:
            self._on_copy(self._copy_path)
        super().mousePressEvent(event)


class CopyPathLineEdit(QLineEdit):
    def __init__(self, copy_path: str, on_copy: Callable[[str], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._copy_path: str = copy_path
        self._on_copy: Callable[[str], None] = on_copy
        self.setToolTip(copy_path)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._copy_path:
            self._on_copy(self._copy_path)
        super().mousePressEvent(event)


class InfoDisplayTab(QWidget):
    MAIN_TABLE_MAX_ROWS: int = 15
    PARTY_TABLE_MAX_ROWS: int = 6

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.field_edits: dict[str, QLineEdit] = {}
        self.field_copy_paths: dict[str, str] = self._build_field_copy_paths()
        self.party_tables: dict[str, dict[str, QTableWidget]] = {}
        self.copy_hint_label: QLabel | None = None
        self.copy_hint_effect: QGraphicsOpacityEffect | None = None
        self.copy_hint_animation: QPropertyAnimation | None = None
        self._init_ui()
        self._init_copy_hint()

    @staticmethod
    def _build_field_copy_paths() -> dict[str, str]:
        paths: dict[str, str] = {
            'timestamp': 'timestamp',
            'error': 'error',
            'misc_ac': 'misc.ac',
            'misc_on_chat': 'misc.on_chat',
            'misc_is_targeting': 'misc.is_targeting',
            'misc_enemy_count': 'misc.enemy_count',
            'misc_delay': 'misc.delay',
            'player_class': 'player.status.unit_class',
            'player_role': 'player.status.unit_role',
            'player_health': 'player.status.unit_health',
            'player_power': 'player.status.unit_power',
            'player_damage_absorbs': 'player.status.unit_damage_absorbs',
            'player_heal_absorbs': 'player.status.unit_heal_absorbs',
            'player_dead': 'player.status.unit_is_dead_or_ghost',
            'player_in_combat': 'player.status.unit_in_combat',
            'player_combat_time': 'player.status.combat_time',
            'player_in_movement': 'player.status.unit_in_movement',
            'player_in_vehicle': 'player.status.unit_in_vehicle',
            'player_is_empowering': 'player.status.unit_is_empowering',
            'player_cast_icon': 'player.status.unit_cast_icon',
            'player_cast_remaining': 'player.status.unit_cast_duration',
            'target_exists': 'target.status.exists',
            'target_health': 'target.status.unit_health',
            'target_in_range': 'target.status.unit_in_range',
            'target_in_combat': 'target.status.unit_in_combat',
            'target_can_attack': 'target.status.unit_can_attack',
            'target_is_alive': 'target.status.unit_is_alive',
            'target_cast_icon': 'target.status.unit_cast_icon',
            'target_cast_remaining': 'target.status.unit_cast_duration',
            'focus_exists': 'focus.status.exists',
            'focus_health': 'focus.status.unit_health',
            'focus_in_range': 'focus.status.unit_in_range',
            'focus_in_combat': 'focus.status.unit_in_combat',
            'focus_can_attack': 'focus.status.unit_can_attack',
            'focus_is_alive': 'focus.status.unit_is_alive',
            'focus_cast_icon': 'focus.status.unit_cast_icon',
            'focus_cast_remaining': 'focus.status.unit_cast_duration',
        }
        for index in range(1, 5):
            party_key: str = f'party{index}'
            base_path: str = f'party.{party_key}'
            paths[f'{party_key}_exists'] = f'{base_path}.exists'
            paths[f'{party_key}_class'] = f'{base_path}.status.unit_class'
            paths[f'{party_key}_role'] = f'{base_path}.status.unit_role'
            paths[f'{party_key}_health'] = f'{base_path}.status.unit_health'
            paths[f'{party_key}_in_range'] = f'{base_path}.status.unit_in_range'
            paths[f'{party_key}_is_alive'] = f'{base_path}.status.unit_is_alive'
            paths[f'{party_key}_selected'] = f'{base_path}.status.selected'
            paths[f'{party_key}_damage_absorbs'] = f'{base_path}.status.unit_damage_absorbs'
            paths[f'{party_key}_heal_absorbs'] = f'{base_path}.status.unit_heal_absorbs'
        return paths

    def _init_ui(self) -> None:
        root_layout: QVBoxLayout = QVBoxLayout(self)
        root_layout.setSpacing(10)
        top_groups_layout: QHBoxLayout = QHBoxLayout()
        misc_specs: list[tuple[str, str]] = [('timestamp', '时间戳'), ('error', '错误信息'), ('misc_ac', '一键辅助推荐'), ('misc_on_chat', '正在对话'), ('misc_is_targeting', '选择目标'), ('misc_enemy_count', '敌人数'), ('misc_delay', '延迟')]
        player_specs: list[tuple[str, str]] = [('player_class', '玩家职业'), ('player_role', '玩家职责'), ('player_health', '玩家生命值'), ('player_power', '玩家能量值'), ('player_damage_absorbs', '伤害吸收'), ('player_heal_absorbs', '治疗吸收'), ('player_dead', '已死亡'), ('player_in_combat', '战斗中'), ('player_combat_time', '战斗时长'), ('player_in_movement', '在移动'), ('player_in_vehicle', '在载具'), ('player_is_empowering', '蓄力中'), ('player_cast_icon', '施法技能'), ('player_cast_remaining', '施法剩余')]
        target_specs: list[tuple[str, str]] = [('target_exists', '目标存在'), ('target_health', '目标生命值'), ('target_in_range', '目标在范围'), ('target_in_combat', '目标战斗中'), ('target_can_attack', '目标可攻击'), ('target_is_alive', '目标存活'), ('target_cast_icon', '施法技能'), ('target_cast_remaining', '施法剩余')]
        focus_specs: list[tuple[str, str]] = [('focus_exists', '焦点存在'), ('focus_health', '焦点生命值'), ('focus_in_range', '焦点在范围'), ('focus_in_combat', '焦点战斗中'), ('focus_can_attack', '焦点可攻击'), ('focus_is_alive', '焦点存活'), ('focus_cast_icon', '施法技能'), ('focus_cast_remaining', '施法剩余')]
        top_groups_layout.addWidget(self._create_info_group('杂项', misc_specs, columns_per_row=1), 1)
        top_groups_layout.addWidget(self._create_info_group('玩家信息', player_specs, columns_per_row=2), 2)
        top_groups_layout.addWidget(self._create_info_group('目标信息', target_specs, columns_per_row=1), 1)
        top_groups_layout.addWidget(self._create_info_group('焦点信息', focus_specs, columns_per_row=1), 1)
        root_layout.addLayout(top_groups_layout)
        tables_layout: QHBoxLayout = QHBoxLayout()
        self.player_spell_table = self._create_table(tables_layout, '玩家技能冷却（15）', self.MAIN_TABLE_MAX_ROWS)
        self.player_buff_table = self._create_table(tables_layout, '玩家 Buff（15）', self.MAIN_TABLE_MAX_ROWS)
        self.player_debuff_table = self._create_table(tables_layout, '玩家 Debuff（15）', self.MAIN_TABLE_MAX_ROWS)
        self.target_debuff_table = self._create_table(tables_layout, '目标 Debuff（15）', self.MAIN_TABLE_MAX_ROWS)
        self.focus_debuff_table = self._create_table(tables_layout, '焦点 Debuff（15）', self.MAIN_TABLE_MAX_ROWS)
        root_layout.addLayout(tables_layout, 1)
        self._init_party_groups(root_layout)

    def _create_info_group(self, title: str, field_specs: list[tuple[str, str]], columns_per_row: int) -> QGroupBox:
        group_box: QGroupBox = QGroupBox(title)
        group_layout: QGridLayout = QGridLayout(group_box)
        group_layout.setHorizontalSpacing(8)
        group_layout.setVerticalSpacing(6)
        for index, (field_key, label_text) in enumerate(field_specs):
            row: int = index // columns_per_row
            col: int = index % columns_per_row * 2
            copy_path: str = self.field_copy_paths.get(field_key, field_key)
            label: QLabel = CopyPathLabel(f'{label_text}：', copy_path, self._copy_text)
            edit: QLineEdit = CopyPathLineEdit(copy_path, self._copy_text)
            edit.setReadOnly(True)
            group_layout.addWidget(label, row, col)
            group_layout.addWidget(edit, row, col + 1)
            self.field_edits[field_key] = edit
        return group_box

    def _create_table(self, parent_layout: QHBoxLayout, title_text: str, max_rows: int) -> QTableWidget:
        container: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        title: QLabel = QLabel(title_text)
        table: QTableWidget = self._create_table_widget(max_rows)
        layout.addWidget(title)
        layout.addWidget(table)
        parent_layout.addWidget(container)
        return table

    def _create_table_widget(self, max_rows: int) -> QTableWidget:
        table: QTableWidget = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['title', 'remaining'])
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(22)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setSortingEnabled(False)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header: QHeaderView = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.itemClicked.connect(self._copy_table_title_from_item)
        self._set_fixed_table_height(table, max_rows)
        return table

    def _set_fixed_table_height(self, table: QTableWidget, rows: int) -> None:
        header_height: int = table.horizontalHeader().sizeHint().height()
        row_height: int = table.verticalHeader().defaultSectionSize()
        frame_height: int = table.frameWidth() * 2
        table.setFixedHeight(header_height + row_height * rows + frame_height + 2)

    def _init_party_groups(self, root_layout: QVBoxLayout) -> None:
        party_layout: QHBoxLayout = QHBoxLayout()
        for index in range(1, 5):
            party_key: str = f'party{index}'
            party_box: QGroupBox = QGroupBox(f'{party_key}')
            party_box_layout: QVBoxLayout = QVBoxLayout(party_box)
            info_specs: list[tuple[str, str]] = [(f'{party_key}_exists', '存在'), (f'{party_key}_class', '职业'), (f'{party_key}_role', '职责'), (f'{party_key}_health', '生命值'), (f'{party_key}_in_range', '在范围'), (f'{party_key}_is_alive', '存活'), (f'{party_key}_selected', '被选中'), (f'{party_key}_damage_absorbs', '伤害吸收'), (f'{party_key}_heal_absorbs', '治疗吸收')]
            party_box_layout.addWidget(self._create_info_group('状态', info_specs, columns_per_row=2))
            aura_layout: QHBoxLayout = QHBoxLayout()
            buff_table: QTableWidget = self._create_table(aura_layout, 'Buff（6）', self.PARTY_TABLE_MAX_ROWS)
            debuff_table: QTableWidget = self._create_table(aura_layout, 'Debuff（6）', self.PARTY_TABLE_MAX_ROWS)
            party_box_layout.addLayout(aura_layout)
            self.party_tables[party_key] = {'buff': buff_table, 'debuff': debuff_table}
            party_layout.addWidget(party_box, 1)
        root_layout.addLayout(party_layout)

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        return {}

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return cast(list[Any], value)
        return []

    @staticmethod
    def _safe_get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
        current: Any = data
        for key in path:
            if not isinstance(current, dict):
                return default
            current_dict: dict[str, Any] = cast(dict[str, Any], current)
            current = current_dict.get(key)
            if current is None:
                return default
        return current

    @staticmethod
    def _to_text(value: Any) -> str:
        if value is None:
            return ''
        return str(value)

    @staticmethod
    def _to_bool_text(value: Any) -> str:
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, str):
            lower: str = value.strip().lower()
            if lower in {'true', 'false'}:
                return lower
        return ''

    @staticmethod
    def _to_one_decimal(value: Any) -> str:
        if isinstance(value, (int, float)):
            return f'{float(value):.1f}'
        return ''

    @staticmethod
    def _sort_key_by_remaining(entry: dict[str, Any]) -> float:
        if entry.get('forever') is True:
            return float('inf')
        value: Any = entry.get('remaining')
        if isinstance(value, (int, float)):
            return float(value)
        return float('inf')

    @staticmethod
    def _pick_cast_info(status: dict[str, Any]) -> tuple[str, str]:
        cast_icon: Any = status.get('unit_cast_icon')
        channel_icon: Any = status.get('unit_channel_icon')
        cast_duration: Any = status.get('unit_cast_duration')
        channel_duration: Any = status.get('unit_channel_duration')
        icon: str = str(cast_icon if cast_icon else channel_icon) if cast_icon or channel_icon else ''
        duration_value: Any = cast_duration if cast_duration is not None else channel_duration
        duration: str = f'{float(duration_value):.1f}' if isinstance(duration_value, (int, float)) else ''
        return (icon, duration)

    def _set_field(self, field_key: str, value: str) -> None:
        field: QLineEdit | None = self.field_edits.get(field_key)
        if field is not None:
            field.setText(value)

    def _clear_table(self, table: QTableWidget) -> None:
        table.setRowCount(0)

    def _set_table_rows(self, table: QTableWidget, sequence: list[dict[str, Any]], max_rows: int, predicate: Callable[[dict[str, Any]], bool] | None = None, reverse: bool = False) -> None:
        filtered: list[dict[str, Any]] = []
        for entry in sequence:
            if predicate is not None and (not predicate(entry)):
                continue
            filtered.append(entry)
        filtered.sort(key=self._sort_key_by_remaining, reverse=reverse)
        filtered = filtered[:max_rows]
        table.setRowCount(len(filtered))
        for row, entry in enumerate(filtered):
            title_item: QTableWidgetItem = QTableWidgetItem(self._to_text(entry.get('title')))
            title_alignment: int = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            title_item.setTextAlignment(title_alignment)
            remaining_item: QTableWidgetItem = QTableWidgetItem(self._to_one_decimal(entry.get('remaining')))
            remaining_alignment: int = int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            remaining_item.setTextAlignment(remaining_alignment)
            table.setItem(row, 0, title_item)
            table.setItem(row, 1, remaining_item)

    def _copy_table_title_from_item(self, item: QTableWidgetItem) -> None:
        table: QTableWidget = item.tableWidget()
        title_item: QTableWidgetItem | None = table.item(item.row(), 0)
        if title_item is None:
            return
        title_text: str = title_item.text().strip()
        if title_text:
            self._copy_text(title_text)

    def _init_copy_hint(self) -> None:
        hint_label: QLabel = QLabel('', self)
        hint_label.setObjectName('copy_hint_label')
        hint_label.hide()
        hint_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        hint_label.setStyleSheet(
            'QLabel#copy_hint_label {'
            'color: #f5f5f5;'
            'padding: 6px 12px;'
            'border-radius: 10px;'
            'background: qlineargradient('
            'x1:0, y1:0, x2:1, y2:1,'
            'stop:0 rgba(20, 20, 20, 225),'
            'stop:1 rgba(60, 60, 60, 185)'
            ');'
            '}'
        )
        effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(hint_label)
        effect.setOpacity(1.0)
        hint_label.setGraphicsEffect(effect)
        animation: QPropertyAnimation = QPropertyAnimation(effect, b'opacity', self)
        animation.setDuration(1400)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.finished.connect(hint_label.hide)
        self.copy_hint_label = hint_label
        self.copy_hint_effect = effect
        self.copy_hint_animation = animation

    def _copy_text(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self._show_copy_hint(text)

    def _show_copy_hint(self, text: str) -> None:
        if not text:
            return
        if self.copy_hint_label is None or self.copy_hint_effect is None or self.copy_hint_animation is None:
            return
        self.copy_hint_label.setText(f'已复制: {text}')
        self.copy_hint_label.adjustSize()
        self._position_copy_hint()
        self.copy_hint_effect.setOpacity(1.0)
        self.copy_hint_label.show()
        if self.copy_hint_animation.state() == QPropertyAnimation.State.Running:
            self.copy_hint_animation.stop()
        self.copy_hint_animation.start()

    def _position_copy_hint(self) -> None:
        if self.copy_hint_label is None:
            return
        cursor_pos: QPoint = self.mapFromGlobal(QCursor.pos())
        self.copy_hint_label.move(cursor_pos.x(), cursor_pos.y())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self.copy_hint_label is not None and self.copy_hint_label.isVisible():
            self._position_copy_hint()

    def update_from_pixel_dump(self, pixel_dump: dict[str, Any]) -> None:
        dump: dict[str, Any] = self._as_dict(pixel_dump)
        misc: dict[str, Any] = self._as_dict(dump.get('misc'))
        player_status: dict[str, Any] = self._as_dict(self._safe_get(dump, ['player', 'status'], {}))
        target_status: dict[str, Any] = self._as_dict(self._safe_get(dump, ['target', 'status'], {}))
        focus_status: dict[str, Any] = self._as_dict(self._safe_get(dump, ['focus', 'status'], {}))
        self._set_field('timestamp', self._to_text(dump.get('timestamp')))
        self._set_field('error', self._to_text(dump.get('error')))
        self._set_field('misc_ac', self._to_text(misc.get('ac')) if misc else '')
        self._set_field('misc_on_chat', self._to_bool_text(misc.get('on_chat')) if misc else '')
        self._set_field('misc_is_targeting', self._to_bool_text(misc.get('is_targeting')) if misc else '')
        self._set_field('misc_enemy_count', self._to_one_decimal(misc.get('enemy_count')) if misc else '')
        self._set_field('misc_delay', self._to_bool_text(misc.get('delay')) if misc else '')
        self._set_field('player_class', self._to_text(player_status.get('unit_class')))
        self._set_field('player_role', self._to_text(player_status.get('unit_role')))
        self._set_field('player_health', self._to_one_decimal(player_status.get('unit_health')))
        self._set_field('player_power', self._to_one_decimal(player_status.get('unit_power')))
        self._set_field('player_damage_absorbs', self._to_one_decimal(player_status.get('unit_damage_absorbs')))
        self._set_field('player_heal_absorbs', self._to_one_decimal(player_status.get('unit_heal_absorbs')))
        self._set_field('player_dead', self._to_bool_text(player_status.get('unit_is_dead_or_ghost')))
        self._set_field('player_in_combat', self._to_bool_text(player_status.get('unit_in_combat')))
        self._set_field('player_combat_time', self._to_one_decimal(player_status.get('combat_time')))
        self._set_field('player_in_movement', self._to_bool_text(player_status.get('unit_in_movement')))
        self._set_field('player_in_vehicle', self._to_bool_text(player_status.get('unit_in_vehicle')))
        self._set_field('player_is_empowering', self._to_bool_text(player_status.get('unit_is_empowering')))
        player_cast_icon, player_cast_remaining = self._pick_cast_info(player_status)
        self._set_field('player_cast_icon', player_cast_icon)
        self._set_field('player_cast_remaining', player_cast_remaining)
        target_exists: Any = target_status.get('exists')
        self._set_field('target_exists', self._to_bool_text(target_exists))
        if target_exists is True:
            self._set_field('target_health', self._to_one_decimal(target_status.get('unit_health')))
            self._set_field('target_in_range', self._to_bool_text(target_status.get('unit_in_range')))
            self._set_field('target_in_combat', self._to_bool_text(target_status.get('unit_in_combat')))
            self._set_field('target_can_attack', self._to_bool_text(target_status.get('unit_can_attack')))
            self._set_field('target_is_alive', self._to_bool_text(target_status.get('unit_is_alive')))
            target_cast_icon, target_cast_remaining = self._pick_cast_info(target_status)
            self._set_field('target_cast_icon', target_cast_icon)
            self._set_field('target_cast_remaining', target_cast_remaining)
        else:
            self._set_field('target_health', '')
            self._set_field('target_in_range', '')
            self._set_field('target_in_combat', '')
            self._set_field('target_can_attack', '')
            self._set_field('target_is_alive', '')
            self._set_field('target_cast_icon', '')
            self._set_field('target_cast_remaining', '')
        focus_exists: Any = focus_status.get('exists')
        self._set_field('focus_exists', self._to_bool_text(focus_exists))
        if focus_exists is True:
            self._set_field('focus_health', self._to_one_decimal(focus_status.get('unit_health')))
            self._set_field('focus_in_range', self._to_bool_text(focus_status.get('unit_in_range')))
            self._set_field('focus_in_combat', self._to_bool_text(focus_status.get('unit_in_combat')))
            self._set_field('focus_can_attack', self._to_bool_text(focus_status.get('unit_can_attack')))
            self._set_field('focus_is_alive', self._to_bool_text(focus_status.get('unit_is_alive')))
            focus_cast_icon, focus_cast_remaining = self._pick_cast_info(focus_status)
            self._set_field('focus_cast_icon', focus_cast_icon)
            self._set_field('focus_cast_remaining', focus_cast_remaining)
        else:
            self._set_field('focus_health', '')
            self._set_field('focus_in_range', '')
            self._set_field('focus_in_combat', '')
            self._set_field('focus_can_attack', '')
            self._set_field('focus_is_alive', '')
            self._set_field('focus_cast_icon', '')
            self._set_field('focus_cast_remaining', '')
        player_buff_sequence: list[dict[str, Any]] = self._as_list(self._safe_get(dump, ['player', 'aura', 'buff_sequence'], []))
        self._set_table_rows(self.player_buff_table, player_buff_sequence, max_rows=self.MAIN_TABLE_MAX_ROWS)
        player_spell_sequence: list[dict[str, Any]] = self._as_list(self._safe_get(dump, ['player', 'spell_sequence'], []))
        self._set_table_rows(self.player_spell_table, player_spell_sequence, max_rows=self.MAIN_TABLE_MAX_ROWS, predicate=lambda item: item.get('known') is True, reverse=True)
        player_debuff_sequence: list[dict[str, Any]] = self._as_list(self._safe_get(dump, ['player', 'aura', 'debuff_sequence'], []))
        self._set_table_rows(self.player_debuff_table, player_debuff_sequence, max_rows=self.MAIN_TABLE_MAX_ROWS)
        if target_exists is True:
            target_debuff_sequence: list[dict[str, Any]] = self._as_list(self._safe_get(dump, ['target', 'aura', 'debuff_sequence'], []))
            self._set_table_rows(self.target_debuff_table, target_debuff_sequence, max_rows=self.MAIN_TABLE_MAX_ROWS)
        else:
            self._clear_table(self.target_debuff_table)
        if focus_exists is True:
            focus_debuff_sequence: list[dict[str, Any]] = self._as_list(self._safe_get(dump, ['focus', 'aura', 'debuff_sequence'], []))
            self._set_table_rows(self.focus_debuff_table, focus_debuff_sequence, max_rows=self.MAIN_TABLE_MAX_ROWS)
        else:
            self._clear_table(self.focus_debuff_table)
        party_data: dict[str, Any] = self._as_dict(dump.get('party'))
        for index in range(1, 5):
            party_key: str = f'party{index}'
            party_entry: dict[str, Any] = self._as_dict(party_data.get(party_key))
            party_status: dict[str, Any] = self._as_dict(party_entry.get('status'))
            party_aura: dict[str, Any] = self._as_dict(party_entry.get('aura'))
            party_exists: Any = party_entry.get('exists')
            self._set_field(f'{party_key}_exists', self._to_bool_text(party_exists))
            if party_exists is True:
                self._set_field(f'{party_key}_class', self._to_text(party_status.get('unit_class')))
                self._set_field(f'{party_key}_role', self._to_text(party_status.get('unit_role')))
                self._set_field(f'{party_key}_health', self._to_one_decimal(party_status.get('unit_health')))
                self._set_field(f'{party_key}_in_range', self._to_bool_text(party_status.get('unit_in_range')))
                self._set_field(f'{party_key}_is_alive', self._to_bool_text(party_status.get('unit_is_alive')))
                self._set_field(f'{party_key}_selected', self._to_bool_text(party_status.get('selected')))
                self._set_field(f'{party_key}_damage_absorbs', self._to_one_decimal(party_status.get('unit_damage_absorbs')))
                self._set_field(f'{party_key}_heal_absorbs', self._to_one_decimal(party_status.get('unit_heal_absorbs')))
                self._set_table_rows(self.party_tables[party_key]['buff'], self._as_list(party_aura.get('buff_sequence')), max_rows=self.PARTY_TABLE_MAX_ROWS)
                self._set_table_rows(self.party_tables[party_key]['debuff'], self._as_list(party_aura.get('debuff_sequence')), max_rows=self.PARTY_TABLE_MAX_ROWS)
            else:
                self._set_field(f'{party_key}_class', '')
                self._set_field(f'{party_key}_role', '')
                self._set_field(f'{party_key}_health', '')
                self._set_field(f'{party_key}_in_range', '')
                self._set_field(f'{party_key}_is_alive', '')
                self._set_field(f'{party_key}_selected', '')
                self._set_field(f'{party_key}_damage_absorbs', '')
                self._set_field(f'{party_key}_heal_absorbs', '')
                self._clear_table(self.party_tables[party_key]['buff'])
                self._clear_table(self.party_tables[party_key]['debuff'])
