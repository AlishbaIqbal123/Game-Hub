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
        t_lbl.setObjectName("HeroTitle")
        # Ensure high contrast in light mode by using the accent color only if it's dark enough, or keep it.
        t_lbl.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {color};")
        
        s_lbl = QLabel(subtitle)
        s_lbl.setObjectName("HeroSubtitle")
        # Fixed: subtitle color now adapts via theme.py object name
        lay.addWidget(t_lbl)
        lay.addWidget(s_lbl)
        lay.addSpacing(20)
        
        self.play_btn = NeonButton("PLAY NOW", primary=True); self.play_btn.setFixedSize(140, 46)
        # Force high visibility in light mode
        self.play_btn.setObjectName("PrimaryButton")
        self.play_btn.clicked.connect(lambda: self.clicked.emit(self.key))
        lay.addWidget(self.play_btn)

    def mousePressEvent(self, e):
        # Allow clicking the entire card to launch the game
        self.clicked.emit(self.key)

    def paintEvent(self, e):
        super().paintEvent(e)
        from hub.core.theme import is_dark
        # Background: Add subtle editorial gradient
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(0.15 if is_dark() else 0.05)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        # Use white in dark mode, black in light mode for subtle tonal depth
        color = Qt.GlobalColor.white if is_dark() else Qt.GlobalColor.black
        grad.setColorAt(0, color); grad.setColorAt(1, Qt.GlobalColor.transparent)
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
        title.setObjectName("TitleLabel")
        # Removed in-line style for theme reactivity
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
