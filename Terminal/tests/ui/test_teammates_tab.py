import os
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terminal.ui.tabs.teammates_tab import TeammatesTab


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_teammates_tab_shows_is_player_casting_target(qapp: QApplication) -> None:
    tab = TeammatesTab()

    tab.refresh_from_decode_snapshot(
        {
            "decoded_data": {
                "party": {
                    "party1": {
                        "exists": True,
                        "status": {
                            "isPlayerCastingTarget": False,
                        },
                        "buff": [],
                        "debuff": [],
                    }
                }
            },
            "decode_result_is_stale": False,
        }
    )

    party1_section = tab.sections["party1"]
    assert party1_section["field_labels"]["isPlayerCastingTarget"].text() == "是玩家当前施法目标"
    assert party1_section["value_inputs"]["isPlayerCastingTarget"].text() == "False"
