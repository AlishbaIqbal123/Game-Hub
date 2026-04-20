"""
Arcade Hub — Premium Sidebar Navigation
Inspired by Apple Arcade + Epic Games Launcher sidebar patterns.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from hub.core.theme import PALETTE, is_dark, set_dark_mode, FONT_TITLE, FONT_BODY


# ── Nav item data ─────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("home",         "✸", "Home"),
    ("games",        "✦", "Discovery"),
    ("achievements", "❂", "Milestones"),
    ("settings",     "⚙", "System"),
]

BOTTOM_ITEMS = [
    ("help",         "?", "Insights"),
]


class NavButton(QPushButton):
    """Single sidebar navigation item."""
    def __init__(self, key: str, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setText(f"   {icon}   {label}")
        self.setCheckable(True)
        self.setObjectName("SidebarButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class ThemeToggle(QWidget):
    """Modern light/dark mode toggle."""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = is_dark()
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._dark = not self._dark
        set_dark_mode(self._dark)
        self.toggled.emit(self._dark)
        self.update()

    def paintEvent(self, e) -> None:  # noqa: N802
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Track
        track_col = QColor(PALETTE["surface_mid"])
        p.setBrush(track_col); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 4, w, h-8, (h-8)//2, (h-8)//2)

        # Knob
        knob_size = h - 16
        knob_x = w - knob_size - 4 if self._dark else 4
        p.setBrush(QColor(PALETTE["primary"])); p.drawEllipse(knob_x, 8, knob_size, knob_size)
        
        # Label
        p.setPen(QColor(PALETTE["text"]))
        p.setFont(QFont(FONT_BODY, 9, 700))
        txt = "DARK" if self._dark else "LIGHT"
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, txt)


class QuickToggle(QWidget):
    """Modern toggle switch for sound / animations."""
    toggled = pyqtSignal(bool)

    def __init__(self, icon: str, label: str, initial: bool = True, parent=None):
        super().__init__(parent)
        self._on = initial
        self._icon = icon
        self._label = label
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0); lay.setSpacing(12)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setStyleSheet(f"font-size:16px; color:{PALETTE['primary']};")
        lay.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setStyleSheet(f"font-size:13px; font-weight:600; color:{PALETTE['text']};")
        lay.addWidget(self._text_lbl, 1)

        self._state = QLabel("ON" if initial else "OFF")
        self._state.setStyleSheet(f"font-size:10px; font-weight:800; color:{PALETTE['primary'] if initial else PALETTE['muted']};")
        lay.addWidget(self._state)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._on = not self._on
        self.set_state(self._on)
        self.toggled.emit(self._on)

    def set_state(self, on: bool) -> None:
        self._on = on
        self._state.setText("ON" if on else "OFF")
        self._state.setStyleSheet(f"font-size:10px; font-weight:800; color:{PALETTE['primary'] if on else PALETTE['muted']};")


class Sidebar(QFrame):
    navigate      = pyqtSignal(str)
    theme_changed = pyqtSignal(bool)
    sound_toggled = pyqtSignal(bool)
    anim_toggled  = pyqtSignal(bool)

    def __init__(self, registry, storage, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.storage  = storage
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(260)

        root = QVBoxLayout(self); root.setContentsMargins(20, 32, 20, 32); root.setSpacing(6)

        # ── Logo & Brand ──────────────────────────────────────────────────────
        logo_container = QWidget()
        logo_container.setObjectName("PanelCard")
        logo_lay = QHBoxLayout(logo_container); logo_lay.setContentsMargins(16, 16, 16, 16); logo_lay.setSpacing(16)
        
        logo_icon = QLabel("✧")
        logo_icon.setStyleSheet(f"font-size:28px; font-weight:900; color:{PALETTE['primary']};")
        logo_lay.addWidget(logo_icon)
        
        logo_text = QVBoxLayout(); logo_text.setSpacing(0)
        logo_name = QLabel("ARCADE"); logo_name.setStyleSheet("font-size:14px; font-weight:900; letter-spacing:2px;")
        logo_sub = QLabel("Editorial Play"); logo_sub.setStyleSheet(f"font-size:10px; color:{PALETTE['muted']};")
        logo_text.addWidget(logo_name); logo_text.addWidget(logo_sub)
        logo_lay.addLayout(logo_text, 1)
        root.addWidget(logo_container)
        root.addSpacing(32)

        # ── Nav buttons ───────────────────────────────────────────────────────
        self._nav_btns: dict[str, NavButton] = {}
        for key, icon, label in NAV_ITEMS:
            btn = NavButton(key, icon, label)
            btn.clicked.connect(lambda _=False, k=key: self._on_nav(k))
            self._nav_btns[key] = btn
            root.addWidget(btn)

        root.addSpacing(24)

        # ── Quick settings ────────────────────────────────────────────────────
        qs_lbl = QLabel("SYSTEM"); qs_lbl.setObjectName("TagLabel")
        root.addWidget(qs_lbl)

        settings = storage.settings()
        self._sound_toggle = QuickToggle("♬", "Audio", initial=settings.get("sound_enabled", True))
        self._sound_toggle.toggled.connect(self.sound_toggled.emit)
        root.addWidget(self._sound_toggle)

        self._anim_toggle = QuickToggle("✦", "Visuals", initial=settings.get("animations_enabled", True))
        self._anim_toggle.toggled.connect(self.anim_toggled.emit)
        root.addWidget(self._anim_toggle)

        root.addSpacing(16)

        # ── Theme toggle ──────────────────────────────────────────────────────
        self._theme_toggle = ThemeToggle()
        self._theme_toggle.toggled.connect(self.theme_changed.emit)
        root.addWidget(self._theme_toggle)

        root.addStretch(1)

        # ── Bottom items ──────────────────────────────────────────────────────
        for key, icon, label in BOTTOM_ITEMS:
            btn = NavButton(key, icon, label)
            btn.clicked.connect(lambda _=False, k=key: self._on_nav(k))
            root.addWidget(btn)

        self.set_active("home")

    def _on_nav(self, key: str) -> None:
        self.set_active(key)
        self.navigate.emit(key)

    def set_active(self, key: str) -> None:
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)

    def refresh_toggles(self, settings: dict) -> None:
        self._sound_toggle.set_state(settings.get("sound_enabled", True))
        self._anim_toggle.set_state(settings.get("animations_enabled", True))
