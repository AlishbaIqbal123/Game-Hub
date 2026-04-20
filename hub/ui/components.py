from __future__ import annotations

import math
import random

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF,
    QSequentialAnimationGroup, Qt, QTimer, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from hub.core.theme import PALETTE, is_dark, FONT_BODY, FONT_TITLE


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def add_glow(widget: QWidget, color: str, blur: int = 40, alpha: int = 80) -> None:
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(blur)
    fx.setOffset(0, 0)
    c = QColor(color); c.setAlpha(alpha)
    fx.setColor(c)
    widget.setGraphicsEffect(fx)


def pulse_glow(widget: QWidget, color: str, lo: int = 30, hi: int = 110,
               duration: int = 1800) -> None:
    """Animate a glow effect between two alpha values continuously."""
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(45)
    fx.setOffset(0, 0)
    c = QColor(color); c.setAlpha(lo)
    fx.setColor(c)
    widget.setGraphicsEffect(fx)

    anim_in = QPropertyAnimation(fx, b"blurRadius", widget)
    anim_in.setDuration(duration // 2)
    anim_in.setStartValue(28)
    anim_in.setEndValue(60)
    anim_in.setEasingCurve(QEasingCurve.Type.InOutSine)

    anim_out = QPropertyAnimation(fx, b"blurRadius", widget)
    anim_out.setDuration(duration // 2)
    anim_out.setStartValue(60)
    anim_out.setEndValue(28)
    anim_out.setEasingCurve(QEasingCurve.Type.InOutSine)

    seq = QSequentialAnimationGroup(widget)
    seq.addAnimation(anim_in)
    seq.addAnimation(anim_out)
    seq.setLoopCount(-1)
    seq.start()
    widget._pulse_anim = seq  # keep reference


def animate_reveal(widget: QWidget, delay_ms: int = 0) -> None:
    """Standard soft slide-up with opacity reveal."""
    widget.setGraphicsEffect(None) # Clear existing
    op = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(op)
    
    pos = widget.pos()
    widget.move(pos.x(), pos.y() + 20)
    
    a1 = QPropertyAnimation(op, b"opacity")
    a1.setDuration(500); a1.setStartValue(0); a1.setEndValue(1)
    a1.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    a2 = QPropertyAnimation(widget, b"pos")
    a2.setDuration(500); a2.setStartValue(widget.pos()); a2.setEndValue(pos)
    a2.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    if delay_ms > 0:
        QTimer.singleShot(delay_ms, lambda: (a1.start(), a2.start()))
        widget._reveal_anims = [a1, a2] # Keep ref
    else:
        a1.start(); a2.start()


# ─────────────────────────────────────────────────────────────────────────────
#  Particle background widget
# ─────────────────────────────────────────────────────────────────────────────

class ParticleField(QWidget):
    """Floating dot particles — drop behind any screen for depth."""

    def __init__(self, count: int = 60, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._particles: list[dict] = []
        self._count = count
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(32)

    def _spawn(self) -> dict:
        w, h = max(self.width(), 1), max(self.height(), 1)
        return {
            "x": random.uniform(0, w),
            "y": random.uniform(0, h),
            "vx": random.uniform(-0.15, 0.15),
            "vy": random.uniform(-0.4, -0.1),
            "r": random.uniform(1.0, 4.0),
            "alpha": random.uniform(0.1, 0.45),
            "color": random.choice([
                PALETTE["primary"],
                PALETTE["secondary"],
                PALETTE["tertiary"],
            ]),
        }

    def _step(self) -> None:
        w, h = max(self.width(), 1), max(self.height(), 1)
        while len(self._particles) < self._count:
            self._particles.append(self._spawn())
        for pt in self._particles:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            if pt["y"] < -10 or pt["x"] < -10 or pt["x"] > w + 10:
                pt.update(self._spawn())
                pt["y"] = h + 10
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for pt in self._particles:
            c = QColor(pt["color"])
            c.setAlphaF(pt["alpha"])
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(pt["x"], pt["y"]), pt["r"], pt["r"])


# ─────────────────────────────────────────────────────────────────────────────
#  Animated 3-D glass card
# ─────────────────────────────────────────────────────────────────────────────

class GlassCard(QFrame):
    """Card with a painted gradient, top-edge highlight, and hover glow."""
    clicked = pyqtSignal()

    def __init__(self, accent: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._accent = QColor(accent or PALETTE["primary"])
        self._hover  = False
        self.setObjectName("GlassCard")
        self.setMinimumHeight(180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, e) -> None:  # noqa: N802
        self._hover = True; self.update()

    def leaveEvent(self, e) -> None:  # noqa: N802
        self._hover = False; self.update()

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self.clicked.emit(); super().mousePressEvent(e)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        path = QPainterPath(); path.addRoundedRect(r, 32, 32)

        # Body gradient — adapts to light/dark tonal layers
        dark = is_dark()
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        if dark:
            g.setColorAt(0.0, QColor(PALETTE["surface_mid"]))
            g.setColorAt(1.0, QColor(PALETTE["surface_low"]))
        else:
            g.setColorAt(0.0, QColor(PALETTE["surface_bright"]))
            g.setColorAt(1.0, QColor(PALETTE["surface_mid"]))
        p.fillPath(path, g)

        # Ambient glow background
        # (Very subtle bloom effect behind the card)
        
        # Accent top-edge blur shimmer
        shimmer = QLinearGradient(r.topLeft(), r.topRight())
        ac = QColor(self._accent)
        ac.setAlpha(120 if self._hover else 40)
        shimmer.setColorAt(0.0, QColor(0,0,0,0))
        shimmer.setColorAt(0.5, ac)
        shimmer.setColorAt(1.0, QColor(0,0,0,0))
        p.fillRect(QRectF(r.x()+32, r.y(), r.width()-64, 4), shimmer)

        # Border
        alpha = 60 if self._hover else 25
        p.setPen(QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), alpha), 1.5))
        p.drawPath(path)


# ─────────────────────────────────────────────────────────────────────────────
#  Premium Components
# ─────────────────────────────────────────────────────────────────────────────

class NeonButton(QPushButton):
    def __init__(self, text: str, primary: bool = False, danger: bool = False, accent: str = None, parent=None) -> None:
        super().__init__(text, parent)
        if primary: self.setObjectName("PrimaryButton")
        elif danger: self.setObjectName("DangerButton")
        else: self.setObjectName("GhostButton")
        
        if accent:
            self.setStyleSheet(f"""
                QPushButton { {
                    border: 1px solid {accent}55;
                    color: {accent};
                } }
                QPushButton:hover { {
                    background: {accent}22;
                    border: 1px solid {accent};
                } }
            """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SidebarButton(QPushButton):
    def __init__(self, text: str, active: bool = False, parent=None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setChecked(active)
        self.setObjectName("SidebarButton")


class StatChip(QLabel):
    def __init__(self, text: str, accent: str, parent=None) -> None:
        super().__init__(text, parent)
        self._accent = accent
        self.setStyleSheet(
            f"background: {accent}14; border-radius: 20px; padding: 10px 18px;"
            f"color: {accent}; font-weight: 800; font-size: 13px;"
        )


class StatCard(QFrame):
    """Mini card showing a metric."""
    def __init__(self, label: str, value: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelCard")
        self.setMinimumWidth(160)
        l = QVBoxLayout(self); l.setContentsMargins(20,20,20,20); l.setSpacing(4)
        
        lbl = QLabel(label); lbl.setObjectName("TagLabel")
        lbl.setStyleSheet(f"color: {accent};")
        l.addWidget(lbl)
        
        val = QLabel(value)
        val.setStyleSheet("font-size: 24px; font-weight: 800;")
        l.addWidget(val)


class SectionPanel(QFrame):
    def __init__(self, title: str, subtitle: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PanelCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        header = QLabel(title); header.setObjectName("SectionLabel")
        layout.addWidget(header)

        if subtitle:
            copy = QLabel(subtitle); copy.setObjectName("MutedLabel")
            copy.setWordWrap(True); layout.addWidget(copy)

        self.body = QVBoxLayout(); self.body.setSpacing(12); layout.addLayout(self.body)


class GameCanvas(QFrame):
    """Reusable surface wrapper for painter-driven games."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PanelCard")
        self.setMinimumSize(520, 360)


# ─────────────────────────────────────────────────────────────────────────────
#  Tutorial & Overlays
# ─────────────────────────────────────────────────────────────────────────────

class TutorialOverlay(QWidget):
    """Full-screen overlay with step-by-step how-to-play cards."""

    def __init__(self, steps: list[dict], on_done, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {PALETTE['overlay']};")
        self._steps   = steps
        self._current = 0
        self._on_done = on_done

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QFrame(); self._card.setObjectName("Card")
        self._card.setFixedWidth(520)
        outer.addWidget(self._card, 0, Qt.AlignmentFlag.AlignCenter)

        cl = QVBoxLayout(self._card); cl.setContentsMargins(10, 10, 10, 10); cl.setSpacing(0)

        # 1. Header (Dots + Close)
        header_w = QWidget(); header_lay = QHBoxLayout(header_w); header_lay.setContentsMargins(24, 16, 24, 0)
        self._dots_row = QHBoxLayout(); self._dots_row.setSpacing(8)
        self._dots: list[QLabel] = []
        for _ in steps:
            dot = QLabel("●")
            dot.setStyleSheet("color: rgba(255,255,255,0.1); font-size: 10px;")
            self._dots.append(dot); self._dots_row.addWidget(dot)
        header_lay.addLayout(self._dots_row, 1)
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet("background: rgba(255,255,255,0.1); border-radius: 15px; color: white; font-weight: bold; border: none;")
        self._close_btn.clicked.connect(self._exit_tutorial)
        header_lay.addWidget(self._close_btn)
        cl.addWidget(header_w)

        # 2. Scrollable Body
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget(); scroll_content.setStyleSheet("background: transparent;")
        sl = QVBoxLayout(scroll_content); sl.setContentsMargins(32, 10, 32, 10); sl.setSpacing(16)
        
        self._emoji_lbl = QLabel()
        self._emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emoji_lbl.setStyleSheet("font-size: 64px;"); sl.addWidget(self._emoji_lbl)

        self._title_lbl = QLabel()
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setObjectName("TitleLabel")
        self._title_lbl.setStyleSheet("font-size: 24px; font-weight: 800;"); sl.addWidget(self._title_lbl)

        self._body_lbl = QLabel()
        self._body_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body_lbl.setWordWrap(True); self._body_lbl.setObjectName("MutedLabel")
        self._body_lbl.setStyleSheet("font-size: 15px; line-height: 1.6; color: #9baad6;")
        sl.addWidget(self._body_lbl)
        
        scroll.setWidget(scroll_content)
        scroll.setFixedHeight(300) # Give it a fixed visible height to ensure it fits
        cl.addWidget(scroll)

        # 3. Footer (Action Button)
        footer_w = QWidget(); fl = QVBoxLayout(footer_w); fl.setContentsMargins(32, 10, 32, 24)
        self._next_btn = NeonButton("Next Step →", primary=True); self._next_btn.setFixedHeight(54)
        # Ensure the button is extremely visible with an explicit override
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE['primary']};
                color: #060e20;
                border-radius: 18px;
                font-size: 15px;
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['primary_con']};
            }}
        """)
        self._next_btn.clicked.connect(self._advance)
        fl.addWidget(self._next_btn); cl.addWidget(footer_w)

        self._show_step(0)

    def _show_step(self, idx: int) -> None:
        step = self._steps[idx]
        self._emoji_lbl.setText(step["emoji"])
        self._title_lbl.setText(step["title"])
        self._body_lbl.setText(step["body"])
        for i, dot in enumerate(self._dots):
            dot.setStyleSheet(f"color: {PALETTE['primary'] if i == idx else 'rgba(255,255,255,0.1)'};")
        is_last = idx == len(self._steps) - 1
        self._next_btn.setText("LET'S PLAY" if is_last else "Next Step →")

    def _exit_tutorial(self) -> None:
        self.hide(); self._on_done()

    def _advance(self) -> None:
        if self._current < len(self._steps) - 1:
            self._current += 1; self._show_step(self._current)
        else: self._exit_tutorial()

    def resizeEvent(self, event) -> None:  # noqa: N802
        if self.parent(): self.setGeometry(self.parent().rect())


class GameOverOverlay(QWidget):
    def __init__(self, on_restart, on_home, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"background: {PALETTE['overlay']};")

        outer = QVBoxLayout(self); outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(); card.setObjectName("Card"); card.setFixedWidth(440)
        outer.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

        cl = QVBoxLayout(card); cl.setContentsMargins(48, 48, 48, 48); cl.setSpacing(20)

        self._emoji_lbl = QLabel("🏆")
        self._emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emoji_lbl.setStyleSheet("font-size: 64px;"); cl.addWidget(self._emoji_lbl)

        self._title_lbl = QLabel("Well Played!"); self._title_lbl.setObjectName("TitleLabel")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self._title_lbl)

        self._score_lbl = QLabel("0"); self._score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_lbl.setStyleSheet(f"color: {PALETTE['primary']}; font-size: 48px; font-weight: 800;")
        cl.addWidget(self._score_lbl)

        self._msg_lbl = QLabel(""); self._msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg_lbl.setObjectName("MutedLabel"); cl.addWidget(self._msg_lbl)

        cl.addSpacing(16)
        btn_row = QVBoxLayout(); btn_row.setSpacing(12)
        
        r_btn = NeonButton("REPLAY EXPERIENCE", primary=True); r_btn.setFixedHeight(56)
        r_btn.clicked.connect(lambda: (self.hide(), on_restart()))
        btn_row.addWidget(r_btn)
        
        h_btn = NeonButton("BACK TO HUB"); h_btn.setFixedHeight(56)
        h_btn.clicked.connect(lambda: (self.hide(), on_home()))
        btn_row.addWidget(h_btn)
        cl.addLayout(btn_row)

    def show_result(self, emoji: str, title: str, score: int, best: int, message: str = "") -> None:
        self._emoji_lbl.setText(emoji)
        self._title_lbl.setText(title)
        self._score_lbl.setText(str(score))
        self._msg_lbl.setText(message)
        self.show(); self.raise_()
        if self.parent(): self.setGeometry(self.parent().rect())

    def resizeEvent(self, event) -> None:  # noqa: N802
        if self.parent(): self.setGeometry(self.parent().rect())
