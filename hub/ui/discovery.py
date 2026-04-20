"""
Arcade Discovery Screen — Editorial & Magazine Layout
Distinct from the high-density Dashboard.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QSizePolicy
)

from hub.ui.components import NeonButton, GlassCard, ParticleField
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY

class HeroCard(GlassCard):
    """Large editorial banner for discovery."""
    clicked = pyqtSignal(str)

    def __init__(self, key: str, title: str, subtitle: str, color: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.addStretch(1)
        
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet(f"font-family:'{FONT_TITLE}'; font-size:32px; font-weight:900; color:{color};")
        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(f"font-family:'{FONT_BODY}'; font-size:16px; color:#ffffffBB;")
        lay.addWidget(t_lbl)
        lay.addWidget(s_lbl)
        lay.addSpacing(20)
        
        play = NeonButton("PLAY NOW", primary=True); play.setFixedSize(140, 46)
        play.clicked.connect(lambda: self.clicked.emit(self.key))
        lay.addWidget(play)

    def paintEvent(self, e):
        super().paintEvent(e)
        # Background: Add subtle editorial gradient
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(0.1)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, Qt.GlobalColor.white); grad.setColorAt(1, Qt.GlobalColor.transparent)
        p.setBrush(grad); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 32, 32)

class DiscoveryScreen(QWidget):
    open_game = pyqtSignal(str)

    def __init__(self, registry, storage, parent=None):
        super().__init__(parent)
        self.registry = registry
        
        root = QVBoxLayout(self); root.setContentsMargins(40, 40, 40, 40); root.setSpacing(32)
        
        hdr = QVBoxLayout(); hdr.setSpacing(4)
        title = QLabel("ARCADE DISCOVERY")
        title.setStyleSheet(f"font-family:'{FONT_TITLE}'; font-size:42px; font-weight:900; color:{PALETTE['primary']};")
        sub = QLabel("Explore curated experiences and epic challenges.")
        sub.setObjectName("MutedLabel")
        hdr.addWidget(title); hdr.addWidget(sub)
        root.addLayout(hdr)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget(); container.setStyleSheet("background: transparent;")
        self.cl = QVBoxLayout(container); self.cl.setSpacing(24); self.cl.setContentsMargins(0, 0, 0, 0)
        
        # Add Hero Spotlights
        spotlights = [
            ("spider_solitaire", "Fluid Spider", "Master the web in our premium 1-suit edition.", "#22d98a"),
            ("solitaire", "Klondike Classic", "The ultimate test of patience and strategy.", "#ffd60a"),
            ("tower_stacking", "Tower Zenith", "How high can you build your legacy?", "#ff4d6d"),
        ]
        
        for key, t, s, c in spotlights:
            hero = HeroCard(key, t, s, c)
            hero.clicked.connect(self.open_game.emit)
            self.cl.addWidget(hero)
            
        self.cl.addStretch(1)
        scroll.setWidget(container)
        root.addWidget(scroll)
