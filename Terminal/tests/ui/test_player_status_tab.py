import os
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from terminal.ui.tabs.player_status_tab import PlayerStatusTab


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_player_status_tab_shows_is_player_casting_target(qapp: QApplication) -> None:
    tab = PlayerStatusTab()

    tab.refresh_from_decode_snapshot(
        {
            "decoded_data": {
                "player": {
                    "status": {
                        "isPlayerCastingTarget": True,
                    }
                }
            },
            "decode_result_is_stale": False,
        }
    )

    assert tab.field_labels["isPlayerCastingTarget"].text() == "是玩家当前施法目标"
    assert tab.value_inputs["isPlayerCastingTarget"].text() == "True"
