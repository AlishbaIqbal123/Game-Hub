from __future__ import annotations
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QGridLayout, QProgressBar
)
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY
from hub.ui.components import StatChip, GlassCard, animate_reveal

class AchievementsScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, registry, storage, parent=None) -> None:
        super().__init__(parent)
        self.registry = registry
        self.storage = storage
        self._animated_widgets = []

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 40, 40, 40)
        main.setSpacing(32)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame(); header.setObjectName("GlassCard"); header.setFixedHeight(120)
        hl = QHBoxLayout(header); hl.setContentsMargins(32, 0, 32, 0)
        
        ht = QVBoxLayout(); ht.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag = QLabel("PLAYER MILESTONES"); tag.setObjectName("TagLabel")
        title = QLabel("Achievements"); title.setObjectName("TitleLabel")
        ht.addWidget(tag); ht.addWidget(title)
        hl.addLayout(ht); hl.addStretch(1)

        # Real Achievement Logic
        moves_count = self.storage.get_stat("moves")
        games_count = self.storage.get_stat("games_played")
        wins_count  = self.storage.get_stat("wins")
        
        achievements = [
            ("Arcade Rookie", f"Launch 10 different games. ({games_count}/10)", "🎮", min(100, int(games_count/10*100))),
            ("Move Maestro", f"Perform 500 tactical moves. ({moves_count}/500)", "🖱️", min(100, int(moves_count/500*100))),
            ("Grand Champion", f"Claim victory in 5 full matches. ({wins_count}/5)", "🏆", min(100, int(wins_count/5*100))),
            ("Steady Hand", "Win your first Klondike match.", "👑", 100 if self.storage.high_score("solitaire") > 0 else 0),
            ("Spider Slayer", "Clear your first Spider sequence.", "🕷️", 100 if self.storage.high_score("spider_solitaire") > 0 else 0),
            ("Tower Zenith", "Reach 10 blocks in Tower Stacking.", "🏙️", min(100, int(self.storage.high_score("tower_stacking")/10*100))),
        ]

        unlocked = sum(1 for _, _, _, p in achievements if p == 100)
        self._unlocked_chip = StatChip(f"💎 {unlocked}/{len(achievements)} Unlocked", PALETTE["secondary"])
        hl.addWidget(self._unlocked_chip)
        main.addWidget(header)
        self._animated_widgets.append(header)

        # ── Content ───────────────────────────────────────────────────────────
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        grid_w = QWidget(); grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 10, 0); grid.setSpacing(24)
        for i in range(3): grid.setColumnStretch(i, 1)

        for i, (name, desc, ico, prog) in enumerate(achievements):
            card = GlassCard(); card.setFixedHeight(220)
            cl = QVBoxLayout(card); cl.setContentsMargins(24, 24, 24, 24); cl.setSpacing(12)
            
            top = QHBoxLayout()
            icon_lbl = QLabel(ico); icon_lbl.setStyleSheet("font-size: 32px;")
            top.addWidget(icon_lbl); top.addStretch(1)
            if prog == 100:
                top.addWidget(StatChip("UNLOCKED", PALETTE["tertiary"]))
            cl.addLayout(top)

            aname = QLabel(name); aname.setStyleSheet(f"font-weight: 800; font-size: 18px; color: {PALETTE['primary'] if prog > 0 else PALETTE['muted']};")
            cl.addWidget(aname)
            
            adesc = QLabel(desc); adesc.setObjectName("MutedLabel"); adesc.setWordWrap(True)
            cl.addWidget(adesc)
            
            cl.addStretch(1)
            pb = QProgressBar(); pb.setFixedHeight(6); pb.setValue(prog)
            pb.setTextVisible(False)
            pb.setStyleSheet(f"QProgressBar {{ background: {PALETTE['surface_low']}; border-radius: 3px; border: none; }} "
                             f"QProgressBar::chunk {{ background: {PALETTE['secondary'] if prog < 100 else PALETTE['tertiary']}; border-radius: 3px; }}")
            cl.addWidget(pb)
            
            grid.addWidget(card, i // 3, i % 3)
            self._animated_widgets.append(card)

        scroll.setWidget(grid_w)
        main.addWidget(scroll, 1)

    def showEvent(self, event):
        super().showEvent(event)
        for i, w in enumerate(self._animated_widgets):
            animate_reveal(w, delay_ms=i*40)
