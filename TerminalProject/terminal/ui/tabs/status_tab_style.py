from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLineEdit, QPlainTextEdit, QTableWidget, QWidget


STATUS_TAB_STYLESHEET = """
QWidget#statusTab {
}

QLabel#statusSummaryLabel {
    padding: 6px 8px 10px 8px;
    font-size: 13px;
}

QLabel#statusSectionTitleLabel {
    font-weight: 600;
    padding: 4px 0 6px 0;
}

QLabel[statusRole="fieldLabel"] {
    padding-right: 6px;
}

QLabel[statusRole="note"] {
    padding: 2px 0 6px 0;
}

QLineEdit[statusRole="value"],
QPlainTextEdit[statusRole="valueMultiline"] {
    border: 1px solid;
    border-radius: 6px;
    padding: 5px 8px;
}

QTableWidget[statusRole="table"] {
    border: 1px solid;
    border-radius: 8px;
    padding: 2px;
}

QTableWidget[statusRole="table"]::item {
    padding: 4px;
}

QHeaderView::section {
    border: none;
    border-bottom: 1px solid;
    padding: 6px;
    font-weight: 600;
}

QScrollArea {
    border: none;
}
"""


def apply_status_tab_skin(tab: QWidget, summary_label: QLabel) -> None:
    tab.setObjectName("statusTab")
    tab.setStyleSheet(STATUS_TAB_STYLESHEET)
    mark_status_summary_label(summary_label)



def mark_status_summary_label(label: QLabel) -> None:
    label.setObjectName("statusSummaryLabel")



def mark_status_section_title(label: QLabel) -> None:
    label.setObjectName("statusSectionTitleLabel")



def mark_status_field_label(label: QLabel) -> None:
    label.setProperty("statusRole", "fieldLabel")



def mark_status_note_label(label: QLabel) -> None:
    label.setProperty("statusRole", "note")



def mark_status_value_input(line_edit: QLineEdit) -> None:
    line_edit.setProperty("statusRole", "value")



def mark_status_multiline_value_input(text_edit: QPlainTextEdit) -> None:
    text_edit.setProperty("statusRole", "valueMultiline")



def prepare_status_table(table: QTableWidget) -> None:
    table.setProperty("statusRole", "table")
    table.setAlternatingRowColors(True)
    table.setShowGrid(True)
