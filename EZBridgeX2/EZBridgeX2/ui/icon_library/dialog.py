from typing import Any, Callable
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QSlider, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from ...core.database import IconTitleRecord, IconTitleRepository, calculate_footnote_title
from .constants import ICON_CATEGORIES
from .delegates import HashDisplayDelegate, SimilarityDisplayDelegate
from .helpers import create_icon_from_data


class IconLibraryDialog(QDialog):

    def __init__(self, title_manager: IconTitleRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_manager: IconTitleRepository = title_manager
        self.setWindowTitle('图标库管理')
        self.resize(1200, 800)
        self._last_unmatched_count: int = 0
        self._last_unmatched_hashes: set[str] = set()
        self.init_ui()
        self.refresh_timer: QTimer = QTimer(self)
        self.refresh_timer.timeout.connect(self._smart_refresh_unmatched)
        self.refresh_timer.start(1000)
        self.refresh_database_tab()
        self.refresh_unmatched_tab()
        self.refresh_cosine_tab()

    def init_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout()
        self.tab_widget: QTabWidget = QTabWidget()
        self.icon_categories: list[dict[str, Any]] = list(ICON_CATEGORIES)
        self.db_tables: list[QTableWidget] = []
        for category in self.icon_categories:
            tab_widget, table = self._create_database_tab(category)
            self.tab_widget.addTab(tab_widget, category['name'])
            self.db_tables.append(table)
        self.tab_unmatched: QWidget = self._create_unmatched_tab()
        self.tab_widget.addTab(self.tab_unmatched, '未匹配图标')
        self.tab_cosine: QWidget = self._create_cosine_tab()
        self.tab_widget.addTab(self.tab_cosine, '相似度匹配记录')
        self.tab_settings: QWidget = self._create_settings_tab()
        self.tab_widget.addTab(self.tab_settings, '设置')
        layout.addWidget(self.tab_widget)
        self.stats_label: QLabel = QLabel('加载中...')
        self.update_stats()
        layout.addWidget(self.stats_label)
        self.setLayout(layout)

    def _create_icon_from_data(self, full_array: np.ndarray, hash_value: str = '') -> QIcon:
        _ = hash_value
        return create_icon_from_data(full_array)

    def _create_database_tab(self, category: dict[str, Any]) -> tuple[QWidget, QTableWidget]:
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()
        category_footnotes: str = ', '.join(category['footnotes'])
        info_label: QLabel = QLabel(f"分类: {category['name']}\n包含Footnote类型: {category_footnotes}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        db_table: QTableWidget = QTableWidget()
        db_table.setColumnCount(6)
        db_table.setHorizontalHeaderLabels(['图标', '标题', 'Hash', 'Footnote', '类型', '操作'])
        db_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        db_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        db_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        db_table.setColumnWidth(0, 50)
        db_table.setColumnWidth(5, 150)
        db_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        db_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        db_table.setItemDelegateForColumn(2, HashDisplayDelegate(db_table))
        layout.addWidget(db_table)
        refresh_btn: QPushButton = QPushButton('刷新列表')
        refresh_btn.clicked.connect(self.refresh_database_tab)
        if category['name'] == '其他':
            action_layout: QHBoxLayout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(8)
            delete_unknown_btn: QPushButton = QPushButton('删除Unknown分类图标')
            delete_unknown_btn.setStyleSheet('background-color: #f7c9c9;')
            delete_unknown_btn.clicked.connect(self.on_delete_unknown_titles)
            action_layout.addWidget(refresh_btn, 1)
            action_layout.addWidget(delete_unknown_btn, 1)
            layout.addLayout(action_layout)
        else:
            layout.addWidget(refresh_btn)
        widget.setLayout(layout)
        return (widget, db_table)

    def refresh_database_tab(self) -> None:
        all_records: list[IconTitleRecord] = self.title_manager.get_all_titles()
        for i, category in enumerate(self.icon_categories):
            filtered_records: list[IconTitleRecord] = [r for r in all_records if r.footnote_title in category['footnotes']]
            self._populate_db_table(self.db_tables[i], filtered_records)
        self.update_stats()

    def _populate_db_table(self, table: QTableWidget, records: list[IconTitleRecord]) -> None:
        table.setRowCount(len(records))
        for row, record in enumerate(records):
            table.setRowHeight(row, 40)
            full_array: np.ndarray = np.frombuffer(record.full_blob, dtype=np.uint8).reshape(8, 8, 3)
            icon: QIcon = self._create_icon_from_data(full_array)
            icon_item: QTableWidgetItem = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 0, icon_item)
            title_item: QTableWidgetItem = QTableWidgetItem(record.title)
            title_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 1, title_item)
            hash_item: QTableWidgetItem = QTableWidgetItem()
            hash_item.setData(Qt.ItemDataRole.DisplayRole, record.middle_hash)
            hash_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 2, hash_item)
            footnote_item: QTableWidgetItem = QTableWidgetItem(record.footnote_title)
            footnote_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 3, footnote_item)
            type_text: str = '手动添加' if record.match_type == 'manual' else '相似度匹配'
            type_item: QTableWidgetItem = QTableWidgetItem(type_text)
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            table.setItem(row, 4, type_item)
            operation_widget: QWidget = QWidget()
            op_layout: QHBoxLayout = QHBoxLayout()
            op_layout.setContentsMargins(2, 2, 2, 2)
            edit_btn: QPushButton = QPushButton('编辑')
            edit_btn.setProperty('record_id', record.id)
            edit_btn.setProperty('current_title', record.title)
            edit_btn.clicked.connect(self.on_edit_title)
            delete_btn: QPushButton = QPushButton('删除')
            delete_btn.setProperty('record_id', record.id)
            delete_btn.clicked.connect(self.on_delete_title)
            op_layout.addWidget(edit_btn)
            op_layout.addWidget(delete_btn)
            operation_widget.setLayout(op_layout)
            table.setCellWidget(row, 5, operation_widget)

    def _get_category_for_footnote(self, footnote: str) -> dict[str, Any] | None:
        for category in self.icon_categories:
            if footnote in category['footnotes']:
                return category
        return None

    def on_edit_title(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return
        record_id: int = sender.property('record_id')
        current_title: str = sender.property('current_title')
        new_title: str
        ok: bool
        new_title, ok = QInputDialog.getText(self, '编辑标题', '请输入新标题:', text=current_title)
        if ok and new_title and (new_title != current_title):
            if self.title_manager.update_title(record_id, new_title, match_type='manual'):
                QMessageBox.information(self, '成功', '标题已更新，类型已设为手动添加')
                self.refresh_database_tab()
            else:
                QMessageBox.warning(self, '失败', '更新失败')

    def on_delete_title(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return
        record_id: int = sender.property('record_id')
        reply: QMessageBox.StandardButton = QMessageBox.question(self, '确认删除', '确定要删除这条记录吗？', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.title_manager.delete_title(record_id):
                QMessageBox.information(self, '成功', '记录已删除')
                self.refresh_database_tab()
            else:
                QMessageBox.warning(self, '失败', '删除失败')

    def on_delete_unknown_titles(self) -> None:
        all_records: list[IconTitleRecord] = self.title_manager.get_all_titles()
        unknown_ids: list[int] = [record.id for record in all_records if record.footnote_title == 'Unknown']
        if not unknown_ids:
            QMessageBox.information(self, '提示', '没有可删除的Unknown分类记录')
            return
        reply: QMessageBox.StandardButton = QMessageBox.question(self, '确认删除', f'确定要删除 {len(unknown_ids)} 条Unknown分类记录吗？', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        success_count: int = 0
        for record_id in unknown_ids:
            if self.title_manager.delete_title(record_id):
                success_count += 1
        self.refresh_database_tab()
        if success_count == len(unknown_ids):
            QMessageBox.information(self, '成功', f'已删除 {success_count} 条Unknown分类记录')
        else:
            QMessageBox.warning(self, '部分失败', f'尝试删除 {len(unknown_ids)} 条，成功 {success_count} 条，失败 {len(unknown_ids) - success_count} 条')

    def _make_add_unmatched_handler(self, hash_value: str) -> Callable[[bool], None]:
        def _handler(_checked: bool = False, *, value: str = hash_value) -> None:
            self.on_add_unmatched_by_hash(value)

        return _handler

    def _make_show_detail_handler(self, match_info: dict[str, Any]) -> Callable[[bool], None]:
        def _handler(_checked: bool = False, *, payload: dict[str, Any] = match_info) -> None:
            self.show_cosine_detail(payload)

        return _handler

    def _create_unmatched_tab(self) -> QWidget:
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()
        info_label: QLabel = QLabel('以下是在获取标题过程中未能匹配的图标。输入标题后点击"添加"按钮将其加入数据库。\n最接近的标题仅供参考。')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        self.unmatched_table: QTableWidget = QTableWidget()
        self.unmatched_table.setColumnCount(7)
        self.unmatched_table.setHorizontalHeaderLabels(['图标', 'Hash', '最接近的标题', '相似度', 'Footnote', '输入标题', '操作'])
        self.unmatched_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.unmatched_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.unmatched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.unmatched_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.unmatched_table.setColumnWidth(0, 50)
        self.unmatched_table.setColumnWidth(1, 120)
        self.unmatched_table.setColumnWidth(6, 100)
        self.unmatched_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.unmatched_table.setItemDelegateForColumn(1, HashDisplayDelegate(self.unmatched_table))
        self.unmatched_table.setItemDelegateForColumn(3, SimilarityDisplayDelegate(self.unmatched_table))
        layout.addWidget(self.unmatched_table)
        clear_btn: QPushButton = QPushButton('清空缓存')
        clear_btn.clicked.connect(self.on_clear_unmatched)
        layout.addWidget(clear_btn)
        widget.setLayout(layout)
        return widget

    def refresh_unmatched_tab(self) -> None:
        nodes: list[dict[str, Any]] = self.title_manager.get_unmatched_nodes()
        current_inputs: dict[str, str] = {}
        for row in range(self.unmatched_table.rowCount()):
            existing_hash_item = self.unmatched_table.item(row, 1)
            if existing_hash_item:
                hash_value: str | None = existing_hash_item.data(Qt.ItemDataRole.UserRole + 1)
                if hash_value:
                    input_widget: QWidget | None = self.unmatched_table.cellWidget(row, 5)
                    if input_widget and isinstance(input_widget, QLineEdit):
                        current_inputs[hash_value] = input_widget.text()
        self.unmatched_table.setRowCount(len(nodes))
        for row, node_info in enumerate(nodes):
            node_array: np.ndarray = node_info['full_array']
            node_hash: str = node_info['hash']
            self.unmatched_table.setRowHeight(row, 40)
            icon: QIcon = self._create_icon_from_data(node_array)
            icon_item: QTableWidgetItem = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 0, icon_item)
            hash_item: QTableWidgetItem = QTableWidgetItem()
            hash_item.setData(Qt.ItemDataRole.DisplayRole, node_hash)
            hash_item.setData(Qt.ItemDataRole.UserRole + 1, node_hash)
            hash_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 1, hash_item)
            closest: str = node_info.get('closest_title', '')
            closest_item: QTableWidgetItem = QTableWidgetItem(closest if closest else '无')
            closest_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 2, closest_item)
            similarity: float = node_info.get('closest_similarity', 0.0)
            sim_item: QTableWidgetItem = QTableWidgetItem()
            sim_item.setData(Qt.ItemDataRole.DisplayRole, similarity)
            sim_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 3, sim_item)
            footnote_title: str = calculate_footnote_title(node_array)
            footnote_item: QTableWidgetItem = QTableWidgetItem(footnote_title)
            footnote_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.unmatched_table.setItem(row, 4, footnote_item)
            title_input: QLineEdit = QLineEdit()
            if node_hash in current_inputs:
                title_input.setText(current_inputs[node_hash])
            self.unmatched_table.setCellWidget(row, 5, title_input)
            add_btn: QPushButton = QPushButton('添加')
            add_btn.clicked.connect(self._make_add_unmatched_handler(node_hash))
            self.unmatched_table.setCellWidget(row, 6, add_btn)

    def on_add_unmatched_by_hash(self, hash_value: str) -> None:
        nodes: list[dict[str, Any]] = self.title_manager.get_unmatched_nodes()
        target_node_info: dict[str, Any] | None = None
        target_row: int = -1
        for row, node_info in enumerate(nodes):
            if node_info['hash'] == hash_value:
                target_node_info = node_info
                target_row = row
                break
        if not target_node_info:
            QMessageBox.warning(self, '错误', '找不到对应的节点')
            return
        title_input: QWidget | None = self.unmatched_table.cellWidget(target_row, 5)
        if not title_input or not isinstance(title_input, QLineEdit):
            return
        title: str = title_input.text().strip()
        if not title:
            QMessageBox.warning(self, '错误', '请输入标题')
            return
        self.title_manager.add_title(full_array=target_node_info['full_array'], middle_hash=hash_value, middle_array=target_node_info['middle_array'], title=title, match_type='manual')
        QMessageBox.information(self, '成功', f'已添加: {title}')
        self.refresh_unmatched_tab()
        self.refresh_database_tab()

    def on_clear_unmatched(self) -> None:
        self.title_manager.clear_unmatched_cache()
        self.refresh_unmatched_tab()

    def _smart_refresh_unmatched(self) -> None:
        nodes: list[dict[str, Any]] = self.title_manager.get_unmatched_nodes()
        current_hashes: set[str] = {node_info['hash'] for node_info in nodes}
        current_count: int = len(nodes)
        has_changed: bool = current_count != self._last_unmatched_count or current_hashes != self._last_unmatched_hashes
        if has_changed:
            self._last_unmatched_count = current_count
            self._last_unmatched_hashes = current_hashes
            has_focus: bool = False
            focused_hash: str | None = None
            focused_text: str = ''
            for row in range(self.unmatched_table.rowCount()):
                input_widget: QWidget | None = self.unmatched_table.cellWidget(row, 5)
                if input_widget and isinstance(input_widget, QLineEdit):
                    if input_widget.hasFocus():
                        has_focus = True
                        hash_item: QTableWidgetItem | None = self.unmatched_table.item(row, 1)
                        if hash_item:
                            focused_hash = hash_item.data(Qt.ItemDataRole.UserRole + 1)
                            focused_text = input_widget.text()
                        break
            self.refresh_unmatched_tab()
            if has_focus and focused_hash:
                for row in range(self.unmatched_table.rowCount()):
                    hash_item: QTableWidgetItem | None = self.unmatched_table.item(row, 1)
                    if hash_item:
                        row_hash: str | None = hash_item.data(Qt.ItemDataRole.UserRole + 1)
                        if row_hash == focused_hash:
                            new_input: QWidget | None = self.unmatched_table.cellWidget(row, 5)
                            if new_input and isinstance(new_input, QLineEdit):
                                new_input.setText(focused_text)
                                new_input.setFocus()
                            break

    def _create_cosine_tab(self) -> QWidget:
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()
        info_label: QLabel = QLabel("以下是通过余弦相似度算法在本会话中自动匹配的图标。\n这些图标已自动添加到数据库（类型为'相似度匹配'）。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        self.cosine_table: QTableWidget = QTableWidget()
        self.cosine_table.setColumnCount(5)
        self.cosine_table.setHorizontalHeaderLabels(['图标', '匹配到的标题', '相似度', '时间', '操作'])
        self.cosine_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cosine_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.cosine_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.cosine_table.setColumnWidth(0, 50)
        self.cosine_table.setColumnWidth(4, 100)
        self.cosine_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cosine_table.setItemDelegateForColumn(2, SimilarityDisplayDelegate(self.cosine_table))
        layout.addWidget(self.cosine_table)
        clear_btn: QPushButton = QPushButton('清空会话记录')
        clear_btn.clicked.connect(self.on_clear_cosine)
        layout.addWidget(clear_btn)
        widget.setLayout(layout)
        return widget

    def refresh_cosine_tab(self) -> None:
        matches: list[dict[str, Any]] = self.title_manager.get_cosine_matches()
        self.cosine_table.setRowCount(len(matches))
        for row, match_info in enumerate(matches):
            node_array: np.ndarray = match_info['full_array']
            self.cosine_table.setRowHeight(row, 40)
            icon: QIcon = self._create_icon_from_data(node_array)
            icon_item: QTableWidgetItem = QTableWidgetItem()
            icon_item.setIcon(icon)
            icon_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 0, icon_item)
            title_item: QTableWidgetItem = QTableWidgetItem(match_info['title'])
            title_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 1, title_item)
            similarity: float = match_info.get('similarity', 0.0)
            sim_item: QTableWidgetItem = QTableWidgetItem()
            sim_item.setData(Qt.ItemDataRole.DisplayRole, float(similarity))
            sim_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 2, sim_item)
            time_item: QTableWidgetItem = QTableWidgetItem(match_info.get('timestamp', ''))
            time_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.cosine_table.setItem(row, 3, time_item)
            detail_btn: QPushButton = QPushButton('查看')
            detail_btn.clicked.connect(self._make_show_detail_handler(match_info))
            self.cosine_table.setCellWidget(row, 4, detail_btn)

    def show_cosine_detail(self, match_info: dict[str, Any]) -> None:
        msg: str = f"Hash: {match_info['hash']}\n匹配标题: {match_info['title']}\n相似度: {match_info['similarity']:.4f} ({match_info['similarity'] * 100:.2f}%)\n时间: {match_info.get('timestamp', 'N/A')}"
        QMessageBox.information(self, '匹配详情', msg)

    def on_clear_cosine(self) -> None:
        self.title_manager.clear_cosine_matches_cache()
        self.refresh_cosine_tab()

    def _create_settings_tab(self) -> QWidget:
        widget: QWidget = QWidget()
        layout: QVBoxLayout = QVBoxLayout()
        threshold_group: QGroupBox = QGroupBox('余弦相似度阈值')
        threshold_layout: QVBoxLayout = QVBoxLayout()
        slider_layout: QHBoxLayout = QHBoxLayout()
        self.threshold_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(980, 999)
        self.threshold_slider.setValue(int(round(self.title_manager.similarity_threshold * 1000)))
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        slider_layout.addWidget(self.threshold_slider)
        self.threshold_label: QLabel = QLabel(f'{self.title_manager.similarity_threshold:.3f}')
        self.threshold_label.setFixedWidth(60)
        slider_layout.addWidget(self.threshold_label)
        threshold_layout.addLayout(slider_layout)
        info_text: QLabel = QLabel('阈值说明:\n- 0.995 (推荐): 非常严格的匹配，只匹配高度相似的图标\n- 0.980: 更宽松的匹配，可能匹配到相似但不完全相同的图标\n- 低于0.980: 容易误匹配，不推荐')
        info_text.setWordWrap(True)
        threshold_layout.addWidget(info_text)
        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)
        db_group: QGroupBox = QGroupBox('数据库信息')
        db_layout: QVBoxLayout = QVBoxLayout()
        self.db_info_label: QLabel = QLabel('加载中...')
        self.update_db_info()
        db_layout.addWidget(self.db_info_label)
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        import_export_group: QGroupBox = QGroupBox('数据导入导出')
        import_export_layout: QHBoxLayout = QHBoxLayout()
        self.export_btn: QPushButton = QPushButton('导出JSON')
        self.export_btn.clicked.connect(self.on_export)
        import_export_layout.addWidget(self.export_btn)
        self.import_btn: QPushButton = QPushButton('导入JSON')
        self.import_btn.clicked.connect(self.on_import)
        import_export_layout.addWidget(self.import_btn)
        import_export_group.setLayout(import_export_layout)
        layout.addWidget(import_export_group)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_export(self) -> None:
        path: str
        _filter: str
        path, _filter = QFileDialog.getSaveFileName(self, '导出图标库', 'node_titles_v2.json', 'JSON文件 (*.json)')
        if path:
            if self.title_manager.export_to_json(path):
                QMessageBox.information(self, '成功', f'已导出到:\n{path}')
            else:
                QMessageBox.warning(self, '失败', '导出失败')

    def on_import(self) -> None:
        path: str
        _filter: str
        path, _filter = QFileDialog.getOpenFileName(self, '导入图标库（v2格式）', '', 'JSON文件 (*.json)')
        if path:
            reply: QMessageBox.StandardButton = QMessageBox.question(self, '导入方式', '选择导入方式:\nYes = 合并现有数据\nNo = 覆盖现有数据\nCancel = 取消', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            merge: bool = reply == QMessageBox.StandardButton.Yes
            if self.title_manager.import_from_json(path, merge=merge):
                QMessageBox.information(self, '成功', '导入完成')
                self.refresh_database_tab()
            else:
                QMessageBox.warning(self, '失败', '导入失败')

    def on_threshold_changed(self, value: int) -> None:
        threshold: float = value / 1000.0
        self.title_manager.update_threshold(threshold)
        self.threshold_label.setText(f'{threshold:.3f}')

    def update_db_info(self) -> None:
        stats: dict[str, int] = self.title_manager.get_stats()
        info: str = f"数据库路径: {self.title_manager.db_path}\n总记录数: {stats['total']}\n手动添加: {stats['manual']}\n相似度匹配: {stats['cosine']}\nHash缓存: {stats['hash_cached']}\n当前未匹配(内存): {stats['unmatched_memory']}\n会话相似度匹配: {stats['cosine_matches_session']}"
        self.db_info_label.setText(info)

    def update_stats(self) -> None:
        stats: dict[str, int] = self.title_manager.get_stats()
        text: str = f"总记录: {stats['total']} | 手动添加: {stats['manual']} | 相似度匹配: {stats['cosine']} | 当前未匹配: {stats['unmatched_memory']}"
        self.stats_label.setText(text)

    def closeEvent(self, event: Any) -> None:
        self.refresh_timer.stop()
        super().closeEvent(event)
