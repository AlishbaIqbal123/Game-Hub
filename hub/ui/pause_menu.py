from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

from hub.core.theme import PALETTE
from hub.ui.components import NeonButton


class PauseMenu(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumWidth(340)
        self.setStyleSheet(
            f"QDialog {{"
            f"  background: {PALETTE['surface']};"
            f"  border: 2px solid {PALETTE['primary']}44;"
            f"  border-radius: 28px;"
            f"}}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(14)

        title = QLabel("⏸  Game Paused")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Take a break — your game is waiting for you!")
        sub.setObjectName("MutedLabel")
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(6)

        self.resume_button   = NeonButton("▶  Resume Game", primary=True)
        self.restart_button  = NeonButton("🔄  Restart")
        self.settings_button = NeonButton("⚙️  Settings")
        self.home_button     = NeonButton("🏠  Go Home", danger=True)

        for btn in (self.resume_button, self.restart_button,
                    self.settings_button, self.home_button):
            btn.setFixedHeight(46)
            lay.addWidget(btn)
