from __future__ import annotations
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QGridLayout
)
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY
from hub.ui.components import StatChip, SectionPanel, animate_reveal

class LeaderboardScreen(QWidget):
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
        header = QFrame()
        header.setObjectName("GlassCard")
        header.setFixedHeight(120)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(32, 0, 32, 0)
        
        ht = QVBoxLayout(); ht.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag = QLabel("GLOBAL RANKINGS"); tag.setObjectName("TagLabel")
        title = QLabel("Leaderboard"); title.setObjectName("TitleLabel")
        ht.addWidget(tag); ht.addWidget(title)
        hl.addLayout(ht); hl.addStretch(1)

        hl.addWidget(StatChip("🏆 Top 1%", PALETTE["secondary"]))
        hl.addWidget(StatChip("🔥 Active Now", PALETTE["tertiary"]))
        main.addWidget(header)
        self._animated_widgets.append(header)

        # ── Content ───────────────────────────────────────────────────────────
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_w = QWidget(); content_lay = QVBoxLayout(content_w)
        content_lay.setContentsMargins(0, 0, 0, 0); content_lay.setSpacing(24)

        # High Score List
        list_frame = QFrame(); list_frame.setObjectName("Card")
        ll = QVBoxLayout(list_frame); ll.setContentsMargins(32, 32, 32, 32); ll.setSpacing(16)
        
        st = QLabel("Current Standing"); st.setObjectName("SectionLabel")
        ll.addWidget(st); ll.addSpacing(10)

        # Header Row
        hr = QHBoxLayout()
        hr.addWidget(QLabel("GAME"), 2)
        hr.addWidget(QLabel("RANK"), 1)
        hr.addWidget(QLabel("SCORE"), 1)
        hr.addWidget(QLabel("PERCENTILE"), 1)
        for i in range(hr.count()):
            w = hr.itemAt(i).widget()
            if isinstance(w, QLabel): w.setStyleSheet(f"color: {PALETTE['muted']}; font-weight: 800; font-size: 11px;")
        ll.addLayout(hr)
        ll.addWidget(self._divider())

        # Populate rows
        for key, meta in self.registry.items():
            best = self.storage.high_score(key)
            row = QHBoxLayout(); row.setContentsMargins(0, 8, 0, 8)
            
            # Game info
            gn = QLabel(f"<span style='color:{meta['accent']}'>{meta['title']}</span>")
            gn.setStyleSheet(f"font-family: '{FONT_TITLE}'; font-size: 16px; font-weight: 800;")
            row.addWidget(gn, 2)
            
            # Rank (Mock)
            rank = QLabel("#"+str(hash(key)%50 + 1) if best > 0 else "—")
            rank.setStyleSheet(f"font-weight: 700; color: {PALETTE['text']};")
            row.addWidget(rank, 1)
            
            # Score
            sc = QLabel(str(best) if best > 0 else "0")
            sc.setStyleSheet(f"font-weight: 900; color: {PALETTE['primary']}; font-size: 15px;")
            row.addWidget(sc, 1)

            # Percentile
            perc = StatChip("Top 5%" if best > 100 else "Top 20%", PALETTE["surface_highest"])
            row.addWidget(perc, 1)
            
            ll.addLayout(row)
            ll.addWidget(self._divider())

        content_lay.addWidget(list_frame)
        self._animated_widgets.append(list_frame)
        
        scroll.setWidget(content_w)
        main.addWidget(scroll, 1)

    def _divider(self):
        d = QFrame(); d.setFixedHeight(1)
        d.setStyleSheet(f"background: {PALETTE['border']}; opacity: 0.1;")
        return d

    def showEvent(self, event):
        super().showEvent(event)
        for i, w in enumerate(self._animated_widgets):
            animate_reveal(w, delay_ms=i*80)
