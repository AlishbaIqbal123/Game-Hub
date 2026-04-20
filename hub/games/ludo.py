from __future__ import annotations

import random
from dataclasses import dataclass, field

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

# ─────────────────────────────────────────────────────────────────────────────
#  Board constants
# ─────────────────────────────────────────────────────────────────────────────

TRACK_COORDS = [
    (6,1),(6,2),(6,3),(6,4),(6,5),(5,6),(4,6),(3,6),(2,6),(1,6),(0,6),
    (0,7),(0,8),(1,8),(2,8),(3,8),(4,8),(5,8),(6,9),(6,10),(6,11),(6,12),
    (6,13),(6,14),(7,14),(8,14),(8,13),(8,12),(8,11),(8,10),(8,9),(9,8),
    (10,8),(11,8),(12,8),(13,8),(14,8),(14,7),(14,6),(13,6),(12,6),(11,6),
    (10,6),(9,6),(8,5),(8,4),(8,3),(8,2),(8,1),(8,0),(7,0),(6,0),
]
SAFE_INDICES      = {0, 8, 13, 21, 26, 34, 39, 47}
TOKENS_PER_PLAYER = 4
FINISH_PROGRESS   = 57
PLAYER_SELECTIONS = {2: [0, 2], 3: [0, 1, 2], 4: [0, 1, 2, 3]}

# Pinterest-friendly vivid colours
PLAYER_TEMPLATES = [
    # Red  — top-left zone  (cols 0-5, rows 0-5), inner base (1,1) 4×4
    {"name": "Red",    "short": "R", "emoji": "🔴",
     "color": "#FF4757", "light": "#FFE0E3", "dark": "#C0392B",
     "start_index": 0,
     "home_lane":  [(7,1),(7,2),(7,3),(7,4),(7,5),(7,6)],
     "base_slots": [(2,2),(3,2),(2,3),(3,3)]},

    # Green — top-right zone (cols 9-14, rows 0-5), inner base (10,1) 4×4
    {"name": "Green",  "short": "G", "emoji": "🟢",
     "color": "#2ED573", "light": "#D4F7E7", "dark": "#1A9E52",
     "start_index": 13,
     "home_lane":  [(1,7),(2,7),(3,7),(4,7),(5,7),(6,7)],
     "base_slots": [(11,2),(12,2),(11,3),(12,3)]},

    # Yellow — bottom-right zone (cols 9-14, rows 9-14), inner base (10,10) 4×4
    {"name": "Yellow", "short": "Y", "emoji": "🟡",
     "color": "#FFD32A", "light": "#FFF8D6", "dark": "#C9A800",
     "start_index": 26,
     "home_lane":  [(7,13),(7,12),(7,11),(7,10),(7,9),(7,8)],
     "base_slots": [(11,11),(12,11),(11,12),(12,12)]},

    # Blue  — bottom-left zone (cols 0-5, rows 9-14), inner base (1,10) 4×4
    {"name": "Blue",   "short": "B", "emoji": "🔵",
     "color": "#1E90FF", "light": "#D6EEFF", "dark": "#0A6ECC",
     "start_index": 39,
     "home_lane":  [(13,7),(12,7),(11,7),(10,7),(9,7),(8,7)],
     "base_slots": [(2,11),(3,11),(2,12),(3,12)]},
]

QUADRANTS   = {"Red":(0,0,6,6),"Green":(9,0,6,6),"Yellow":(9,9,6,6),"Blue":(0,9,6,6)}
INNER_BASES = {"Red":(1,1,4,4),"Green":(10,1,4,4),"Yellow":(10,10,4,4),"Blue":(1,10,4,4)}

# ─────────────────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PlayerState:
    name: str; short: str; color: str; light: str; dark: str; emoji: str
    start_index: int
    home_lane:  list[tuple[int,int]]
    base_slots: list[tuple[int,int]]
    tokens:   list[int] = field(default_factory=lambda: [-1]*TOKENS_PER_PLAYER)
    captures: int = 0
    finished: int = 0


def _rgb(h: str) -> str:
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

# ─────────────────────────────────────────────────────────────────────────────
#  Dice widget  — big, colourful, kid-friendly
# ─────────────────────────────────────────────────────────────────────────────

class DiceWidget(QFrame):
    PIPS = {
        1: [(0,0)],
        2: [(-1,-1),(1,1)],
        3: [(-1,-1),(0,0),(1,1)],
        4: [(-1,-1),(1,-1),(-1,1),(1,1)],
        5: [(-1,-1),(1,-1),(0,0),(-1,1),(1,1)],
        6: [(-1,-1),(1,-1),(-1,0),(1,0),(-1,1),(1,1)],
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.value: int | None = None
        self._rolling = False
        self._frame   = 0
        self._display: int | None = None
        self._timer   = QTimer(self)
        self._timer.timeout.connect(self._tick)
        # No fixed size — let it be square via sizeHint
        self.setMinimumSize(80, 80)
        self.setMaximumSize(110, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_value(self, v: int | None) -> None:
        self._timer.stop(); self._rolling = False
        self.value = v; self._display = v; self.update()

    def animate_to(self, v: int, frames: int = 14) -> None:
        self.value = v; self._rolling = True
        self._frame = frames; self._display = random.randint(1, 6)
        self._timer.start(50); self.update()

    def _tick(self) -> None:
        self._frame -= 1
        if self._frame <= 0:
            self._timer.stop(); self._rolling = False; self._display = self.value
        else:
            self._display = random.randint(1, 6)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Use QRectF directly to avoid QPoint/QPointF mismatch
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)

        # Drop shadow
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 55))
        p.drawRoundedRect(r.adjusted(4, 5, 4, 5), 20, 20)

        # Face — warm white when idle, golden when rolling
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        if self._rolling:
            g.setColorAt(0.0, QColor(255, 248, 180))
            g.setColorAt(1.0, QColor(255, 210, 80))
        else:
            g.setColorAt(0.0, QColor(255, 255, 255))
            g.setColorAt(1.0, QColor(235, 235, 255))
        p.setBrush(g)
        border_col = QColor("#FF6B9D") if self._rolling else QColor(190, 190, 215)
        p.setPen(QPen(border_col, 3 if self._rolling else 2))
        p.drawRoundedRect(r, 20, 20)

        d = self._display
        if d is None:
            p.setPen(QColor(160, 160, 190))
            p.setFont(QFont("Arial", 26, QFont.Weight.Bold))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "?")
            return

        # Scale pip size and spacing to the actual widget size
        cx, cy = r.center().x(), r.center().y()
        half = min(r.width(), r.height()) / 2.0
        step = half * 0.52          # distance from centre to pip position
        pip_r = half * 0.16         # pip radius — scales with widget

        pip_col = QColor("#E8192C") if self._rolling else QColor("#2C2C5E")
        p.setBrush(pip_col)
        p.setPen(Qt.PenStyle.NoPen)
        for dx, dy in self.PIPS[d]:
            p.drawEllipse(QPointF(cx + dx * step, cy + dy * step), pip_r, pip_r)

# ─────────────────────────────────────────────────────────────────────────────
#  Player card  — pastel, emoji-rich
# ─────────────────────────────────────────────────────────────────────────────

class PlayerCard(QFrame):
    def __init__(self, player: PlayerState, parent=None) -> None:
        super().__init__(parent)
        self.player  = player
        self._active = False
        self.setMinimumHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        # Big emoji circle
        self._emoji_lbl = QLabel(player.emoji)
        self._emoji_lbl.setFixedSize(38, 38)
        self._emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emoji_lbl.setStyleSheet(
            f"background:{player.light}; border-radius:19px; font-size:18px;")
        lay.addWidget(self._emoji_lbl)

        info = QVBoxLayout(); info.setSpacing(2)
        self._name_lbl = QLabel(player.name)
        self._name_lbl.setStyleSheet(
            f"color:{player.dark}; font-weight:800; font-size:14px;")
        self._stat_lbl = QLabel()
        self._stat_lbl.setWordWrap(True)
        self._stat_lbl.setStyleSheet("color:#888; font-size:11px;")
        info.addWidget(self._name_lbl)
        info.addWidget(self._stat_lbl)
        lay.addLayout(info, 1)

        self._home_lbl = QLabel()
        self._home_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._home_lbl.setStyleSheet(f"color:{player.dark}; font-size:12px; font-weight:700;")
        lay.addWidget(self._home_lbl)

        self._apply_style()

    def refresh(self, active: bool) -> None:
        self._active = active
        p = self.player
        on_board = sum(1 for t in p.tokens if t >= 0 and t < FINISH_PROGRESS)
        self._stat_lbl.setText(
            f"{'▶ YOUR TURN  ' if active else ''}"
            f"On board: {on_board}  |  Captured: {p.captures}"
        )
        homes = "🏠" * p.finished + "⬜" * (TOKENS_PER_PLAYER - p.finished)
        self._home_lbl.setText(homes)
        self._apply_style()

    def _apply_style(self) -> None:
        if self._active:
            self.setStyleSheet(
                f"QFrame {{ background: {self.player.light};"
                f" border: 2.5px solid {self.player.color};"
                f" border-radius: 16px; }}"
            )
        else:
            self.setStyleSheet(
                "QFrame { background: #F8F8FC;"
                " border: 1.5px solid #E8E8F0;"
                " border-radius: 16px; }"
            )


# ─────────────────────────────────────────────────────────────────────────────
#  Token move button  — big, colourful, obvious
# ─────────────────────────────────────────────────────────────────────────────

class TokenButton(QPushButton):
    def __init__(self, idx: int, color: str, light: str, parent=None) -> None:
        super().__init__(parent)
        self._color   = color
        self._light   = light
        self._idx     = idx
        self._movable = False
        self._live    = False
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply()

    def update_state(self, label: str, movable: bool, enabled: bool,
                     color: str = "", light: str = "") -> None:
        if color:
            self._color = color
            self._light = light
        self._movable = movable
        self._live    = enabled
        self.setText(label)
        # Only disable at Qt level when no roll is pending (enabled=False)
        # When enabled=True but movable=False, keep Qt-enabled so stylesheet shows correctly
        super().setEnabled(enabled)
        self._apply()

    def _apply(self) -> None:
        if self._movable and self._live:
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background: {self._light};"
                f"  border: 2.5px solid {self._color};"
                f"  border-radius: 12px;"
                f"  color: {self._color};"
                f"  font-weight: 800;"
                f"  font-size: 12px;"
                f"  padding: 4px 4px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background: {self._color};"
                f"  color: white;"
                f"}}"
                f"QPushButton:pressed {{"
                f"  background: {self._color};"
                f"  color: white;"
                f"}}"
            )
        else:
            self.setStyleSheet(
                "QPushButton {"
                "  background: #EBEBF5;"
                "  border: 1.5px solid #D5D5E8;"
                "  border-radius: 12px;"
                "  color: #AAAACC;"
                "  font-size: 11px;"
                "  padding: 4px 4px;"
                "}"
            )

# ─────────────────────────────────────────────────────────────────────────────
#  Board painter  — bright, clean, Pinterest-style + clickable tokens
# ─────────────────────────────────────────────────────────────────────────────

class LudoBoard(QFrame):
    def __init__(self, screen: "LudoScreen", parent=None) -> None:
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(520, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Cache board geometry so mousePressEvent can use it
        self._bx   = 0.0
        self._by   = 0.0
        self._cell = 1.0

    # ── Geometry helpers ──────────────────────────────────────────────────────
    def _board_geometry(self):
        b  = self.rect().adjusted(10, 10, -10, -10)
        sz = min(b.width(), b.height())
        bx = b.center().x() - sz / 2
        by = b.center().y() - sz / 2
        return float(bx), float(by), float(sz / 15)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Map click → board cell → token index → move_token."""
        bx, by, cell = self._board_geometry()
        mx, my = event.position().x(), event.position().y()

        # Which grid cell was clicked?
        col = int((mx - bx) / cell)
        row = int((my - by) / cell)

        # Find a valid token at that cell belonging to the current player
        screen = self.screen
        valid  = set(screen.valid_token_indexes())
        if not valid:
            super().mousePressEvent(event)
            return

        player = screen.current_player_state()
        token_r = cell * 0.40   # must match _draw_tokens radius

        for ti in valid:
            tc, tr = screen.token_cell(player, ti)
            # Use the same offset logic as _draw_tokens
            entries_at_cell = [
                (p, t)
                for p in screen.players
                for t, prog in enumerate(p.tokens)
                if prog != FINISH_PROGRESS and screen.token_cell(p, t) == (tc, tr)
            ]
            offsets = [(0.0,0.0),(- 0.22,0.0),(0.22,0.0),
                       (-0.22,-0.22),(0.22,-0.22),(-0.22,0.22),(0.22,0.22)]
            SINGLE = [(0.0, 0.0)]
            PAIR   = [(-0.22, 0.0), (0.22, 0.0)]
            TRIPLE = [(-0.22,-0.18),(0.22,-0.18),(0.0, 0.22)]
            QUAD   = [(-0.22,-0.22),(0.22,-0.22),(-0.22,0.22),(0.22,0.22)]
            n = len(entries_at_cell)
            layout = SINGLE if n==1 else PAIR if n==2 else TRIPLE if n==3 else QUAD
            # Find this token's stack index
            si = next((i for i,(p,t) in enumerate(entries_at_cell)
                       if p is player and t == ti), 0)
            dx, dy = layout[min(si, len(layout)-1)]
            px = bx + (tc + 0.5 + dx) * cell
            py = by + (tr + 0.5 + dy) * cell

            dist = ((mx - px)**2 + (my - py)**2) ** 0.5
            if dist <= token_r + 6:   # +6px hit-area padding
                screen.move_token(ti)
                return

        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        b  = self.rect().adjusted(10, 10, -10, -10)
        sz = min(b.width(), b.height())
        bx = b.center().x() - sz / 2
        by = b.center().y() - sz / 2
        cell = sz / 15

        # Board background — soft warm white
        p.setPen(QPen(QColor(210, 210, 230), 2))
        p.setBrush(QColor(252, 252, 255))
        p.drawRoundedRect(QRectF(bx, by, sz, sz), 22, 22)

        self._draw_zones(p, bx, by, cell)
        self._draw_track(p, bx, by, cell)
        self._draw_home_lanes(p, bx, by, cell)
        self._draw_center(p, bx, by, cell)
        self._draw_tokens(p, bx, by, cell)

    # ── Coloured corner zones ─────────────────────────────────────────────────
    def _draw_zones(self, p, bx, by, cell) -> None:
        for t in PLAYER_TEMPLATES:
            x, y, w, h = QUADRANTS[t["name"]]
            outer = QRectF(bx + x*cell, by + y*cell, w*cell, h*cell)
            ix, iy, iw, ih = INNER_BASES[t["name"]]
            inner = QRectF(bx + ix*cell, by + iy*cell, iw*cell, ih*cell)

            # Zone fill
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["color"]))
            p.drawRect(outer)

            # White inner base area
            p.setBrush(QColor(255, 255, 255, 230))
            p.drawRoundedRect(inner, 16, 16)

            # Light tint inside base
            c = QColor(t["color"]); c.setAlpha(40)
            p.setBrush(c)
            p.drawRoundedRect(inner.adjusted(6, 6, -6, -6), 12, 12)

    # ── Track squares ─────────────────────────────────────────────────────────
    def _draw_track(self, p, bx, by, cell) -> None:
        for i, (col, row) in enumerate(TRACK_COORDS):
            rect = QRectF(bx + col*cell, by + row*cell, cell, cell)
            if i in SAFE_INDICES:
                p.setBrush(QColor(220, 240, 255))
                p.setPen(QPen(QColor(150, 190, 230), 1))
            else:
                p.setBrush(QColor(248, 248, 255))
                p.setPen(QPen(QColor(200, 200, 220), 0.8))
            p.drawRect(rect)
            if i in SAFE_INDICES:
                p.setPen(QColor(100, 160, 220))
                p.setFont(QFont("Arial", max(7, int(cell * 0.30)), QFont.Weight.Bold))
                p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "★")

        # Coloured start squares
        for t in PLAYER_TEMPLATES:
            sc, sr = TRACK_COORDS[t["start_index"]]
            rect = QRectF(bx + sc*cell, by + sr*cell, cell, cell)
            c = QColor(t["color"]); c.setAlpha(180)
            p.setPen(QPen(QColor(180, 180, 200), 0.8))
            p.setBrush(c)
            p.drawRect(rect)

    # ── Home lanes ────────────────────────────────────────────────────────────
    def _draw_home_lanes(self, p, bx, by, cell) -> None:
        for t in PLAYER_TEMPLATES:
            for step, (col, row) in enumerate(t["home_lane"]):
                rect = QRectF(bx + col*cell, by + row*cell, cell, cell)
                c = QColor(t["color"]); c.setAlpha(50 + step * 28)
                p.setPen(QPen(QColor(180, 180, 200), 0.8))
                p.setBrush(c)
                p.drawRect(rect)

    # ── Center star ───────────────────────────────────────────────────────────
    def _draw_center(self, p, bx, by, cell) -> None:
        cr = QRectF(bx + 6*cell, by + 6*cell, 3*cell, 3*cell)
        cx, cy = cr.center().x(), cr.center().y()
        tris = [
            (QColor(PLAYER_TEMPLATES[0]["color"]),
             [QPointF(bx+6*cell, by+6*cell), QPointF(cx, cy), QPointF(bx+6*cell, by+9*cell)]),
            (QColor(PLAYER_TEMPLATES[1]["color"]),
             [QPointF(bx+6*cell, by+6*cell), QPointF(bx+9*cell, by+6*cell), QPointF(cx, cy)]),
            (QColor(PLAYER_TEMPLATES[2]["color"]),
             [QPointF(bx+9*cell, by+6*cell), QPointF(bx+9*cell, by+9*cell), QPointF(cx, cy)]),
            (QColor(PLAYER_TEMPLATES[3]["color"]),
             [QPointF(bx+6*cell, by+9*cell), QPointF(bx+9*cell, by+9*cell), QPointF(cx, cy)]),
        ]
        p.setPen(Qt.PenStyle.NoPen)
        for color, pts in tris:
            p.setBrush(color)
            p.drawPolygon(QPolygonF(pts))
        # White star overlay
        p.setBrush(QColor(255, 255, 255, 160))
        p.drawEllipse(cr.adjusted(cell*0.6, cell*0.6, -cell*0.6, -cell*0.6))

    # ── Tokens ────────────────────────────────────────────────────────────────
    def _draw_tokens(self, p, bx, by, cell) -> None:
        # Group tokens sharing the same cell
        cell_map: dict[tuple[int,int], list[tuple[PlayerState,int]]] = {}
        for player in self.screen.players:
            for ti, prog in enumerate(player.tokens):
                if prog == FINISH_PROGRESS:
                    continue
                col, row = self.screen.token_cell(player, ti)
                cell_map.setdefault((col, row), []).append((player, ti))

        valid   = set(self.screen.valid_token_indexes())
        rolling = self.screen.dice_widget._rolling

        SINGLE = [(0.0,  0.0)]
        PAIR   = [(-0.22, 0.0), (0.22, 0.0)]
        TRIPLE = [(-0.22,-0.18),(0.22,-0.18),(0.0, 0.22)]
        QUAD   = [(-0.22,-0.22),(0.22,-0.22),(-0.22,0.22),(0.22,0.22)]

        token_r = cell * 0.40          # larger tokens

        for (col, row), entries in cell_map.items():
            n = len(entries)
            layout = SINGLE if n==1 else PAIR if n==2 else TRIPLE if n==3 else QUAD

            for si, (player, ti) in enumerate(entries):
                dx, dy = layout[min(si, len(layout)-1)]
                px = bx + (col + 0.5 + dx) * cell
                py = by + (row + 0.5 + dy) * cell

                is_cur  = player is self.screen.current_player_state()
                movable = ti in valid and is_cur and not rolling

                # Double glow ring for movable tokens
                if movable:
                    outer = QColor(player.color); outer.setAlpha(45)
                    p.setPen(Qt.PenStyle.NoPen); p.setBrush(outer)
                    p.drawEllipse(QPointF(px, py), token_r + 14, token_r + 14)
                    inner = QColor(player.color); inner.setAlpha(90)
                    p.setBrush(inner)
                    p.drawEllipse(QPointF(px, py), token_r + 7, token_r + 7)

                # Token shadow
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(0, 0, 0, 50))
                p.drawEllipse(QPointF(px + 2, py + 3), token_r, token_r)

                # Token body — 3-D gradient
                tg = QLinearGradient(
                    QPointF(px - token_r, py - token_r),
                    QPointF(px + token_r, py + token_r)
                )
                base_c  = QColor(player.color)
                light_c = base_c.lighter(150)
                tg.setColorAt(0.0, light_c)
                tg.setColorAt(1.0, base_c)
                p.setBrush(tg)
                border_w = 2.5 if movable else 1.5
                p.setPen(QPen(QColor(255, 255, 255, 220), border_w))
                p.drawEllipse(QPointF(px, py), token_r, token_r)

                # Token number
                p.setPen(QColor(255, 255, 255))
                font_sz = max(9, int(token_r * 0.85))
                p.setFont(QFont("Arial", font_sz, QFont.Weight.Bold))
                p.drawText(
                    QRectF(px - token_r, py - token_r, token_r*2, token_r*2),
                    Qt.AlignmentFlag.AlignCenter,
                    str(ti + 1),
                )

# ─────────────────────────────────────────────────────────────────────────────
#  Main Ludo screen
# ─────────────────────────────────────────────────────────────────────────────

class LudoScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None) -> None:
        super().__init__(
            "ludo", "Ludo",
            "Roll the dice, move your tokens, capture enemies, and race all four home!",
            "#FF6B9D", storage, sounds, parent,
        )
        self.players: list[PlayerState] = []
        self.current_player  = 0
        self.pending_roll: int | None = None
        self.game_over       = False
        self.bonus_turn_ready = False
        self.turn_message    = ""

        # Override the dark base-game header with a light pastel style
        self.setStyleSheet(
            "QWidget { font-family: 'Segoe UI', 'Arial Rounded MT Bold', Arial, sans-serif; }"
        )

        # ── Top bar ───────────────────────────────────────────────────────────
        top = QHBoxLayout(); top.setSpacing(10)

        self._turn_dot = QFrame()
        self._turn_dot.setFixedSize(20, 20)
        self._turn_dot.setStyleSheet("border-radius:10px; background:#FF6B9D;")
        top.addWidget(self._turn_dot)

        self.turn_label = QLabel("Whose turn?")
        self.turn_label.setStyleSheet(
            "font-weight:800; font-size:18px; color:#3D3D6B;")
        top.addWidget(self.turn_label)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color:#888; font-size:13px;")
        self.status_label.setWordWrap(True)
        top.addWidget(self.status_label, 1)

        self.player_count_box = QComboBox()
        self.player_count_box.addItems(["2 Players", "3 Players", "4 Players"])
        self.player_count_box.setCurrentText("4 Players")
        self.player_count_box.setStyleSheet(
            "QComboBox { background:#F0F0FF; border:2px solid #C8C8E8;"
            " border-radius:12px; padding:6px 12px; color:#3D3D6B; font-weight:600; }"
            "QComboBox::drop-down { border:none; }"
        )
        top.addWidget(self.player_count_box)

        new_btn = QPushButton("🔄  New Game")
        new_btn.setFixedHeight(40)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(
            "QPushButton { background:#FF6B9D; border:none; border-radius:12px;"
            " color:white; font-weight:800; font-size:13px; padding:0 18px; }"
            "QPushButton:hover { background:#FF4785; }"
        )
        new_btn.clicked.connect(self.reset_game)
        top.addWidget(new_btn)
        self.content_layout.addLayout(top)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QHBoxLayout(); body.setSpacing(14)

        self.board = LudoBoard(self)
        body.addWidget(self.board, 1)

        # ── Right panel — vertical scroll only, no horizontal scroll ────────
        rscroll = QScrollArea()
        rscroll.setWidgetResizable(True)
        rscroll.setFrameShape(QFrame.Shape.NoFrame)
        rscroll.setFixedWidth(290)
        rscroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rscroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        rscroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { width: 5px; background: transparent; }"
            "QScrollBar::handle:vertical { background: #D0D0E8; border-radius: 2px; min-height: 20px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        rw = QWidget()
        rw.setStyleSheet("background: transparent;")
        # Hard-pin inner widget to exactly the viewport width — prevents any horizontal scroll
        rw.setFixedWidth(282)
        rl = QVBoxLayout(rw)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)

        # ── Dice card ─────────────────────────────────────────────────────────
        dice_card = QFrame()
        dice_card.setStyleSheet(
            "QFrame { background: white; border-radius: 20px;"
            " border: 2px solid #F0E6FF; }"
        )
        dcl = QVBoxLayout(dice_card)
        dcl.setContentsMargins(16, 16, 16, 16); dcl.setSpacing(10)

        dice_title = QLabel("🎲  Roll the Dice!")
        dice_title.setStyleSheet(
            "color:#3D3D6B; font-weight:800; font-size:15px; border:none;")
        dcl.addWidget(dice_title)

        # Dice centred, number badge centred below it — pure vertical stack
        self.dice_widget = DiceWidget()
        dcl.addWidget(self.dice_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self.roll_value_label = QLabel("?")
        self.roll_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.roll_value_label.setFixedHeight(44)
        self.roll_value_label.setStyleSheet(
            "background:#F8F0FF; border-radius:22px;"
            " border:3px solid #C8A8FF;"
            " color:#7B4FFF; font-size:24px; font-weight:900;"
        )
        dcl.addWidget(self.roll_value_label)

        self._bonus_lbl = QLabel("")
        self._bonus_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bonus_lbl.setWordWrap(True)
        self._bonus_lbl.setStyleSheet(
            "color:#FF6B9D; font-size:12px; font-weight:700; border:none;")
        dcl.addWidget(self._bonus_lbl)

        self.roll_button = QPushButton("🎲  ROLL!")
        self.roll_button.setFixedHeight(50)
        self.roll_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roll_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #A78BFA, stop:1 #7C3AED);"
            " border:none; border-radius:14px; color:white;"
            " font-weight:900; font-size:16px; letter-spacing:1px; }"
            "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #C4B5FD, stop:1 #A78BFA); }"
            "QPushButton:disabled { background:#E8E8F4; color:#BBBBCC; }"
        )
        self.roll_button.clicked.connect(self.roll_die)
        dcl.addWidget(self.roll_button)
        rl.addWidget(dice_card)

        # ── Players card ──────────────────────────────────────────────────────
        pl_card = QFrame()
        pl_card.setStyleSheet(
            "QFrame { background: white; border-radius: 20px;"
            " border: 2px solid #E4F0FF; }"
        )
        pcl = QVBoxLayout(pl_card)
        pcl.setContentsMargins(16, 16, 16, 16); pcl.setSpacing(8)

        pl_title = QLabel("👥  Players")
        pl_title.setStyleSheet(
            "color:#3D3D6B; font-weight:800; font-size:15px; border:none;")
        pcl.addWidget(pl_title)

        self.player_cards: list[PlayerCard] = []
        for i in range(4):
            tmpl = PLAYER_TEMPLATES[i]
            ps = PlayerState(
                name=tmpl["name"], short=tmpl["short"],
                color=tmpl["color"], light=tmpl["light"], dark=tmpl["dark"],
                emoji=tmpl["emoji"],
                start_index=tmpl["start_index"],
                home_lane=list(tmpl["home_lane"]),
                base_slots=list(tmpl["base_slots"]),
            )
            card = PlayerCard(ps); card.hide()
            self.player_cards.append(card)
            pcl.addWidget(card)
        rl.addWidget(pl_card)
        rl.addStretch(1)

        rscroll.setWidget(rw)
        body.addWidget(rscroll, 0)
        self.content_layout.addLayout(body, 1)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "🎲", "title": "Welcome to Ludo!",
             "body": "Each player has 4 tokens. Race all your tokens from the base to the home centre before your opponents do!"},
            {"emoji": "🎯", "title": "Roll to Move",
             "body": "Press ROLL DICE to roll. You need a 6 to bring a token out of base. Then move that many steps around the board!"},
            {"emoji": "💥", "title": "Captures & Safe Squares",
             "body": "Land on an enemy token to send it back to base! Stars (★) are safe squares — no captures allowed there."},
            {"emoji": "🏠", "title": "Race Home",
             "body": "Guide all 4 tokens along the coloured home lane to the centre. First player to get all 4 home wins! Rolling a 6 gives you a bonus turn."},
        ])

    # ─────────────────────────────────────────────────────────────────────────
    #  Game logic
    # ─────────────────────────────────────────────────────────────────────────

    def reset_game(self) -> None:
        count = int(self.player_count_box.currentText()[0])
        self.players = []
        for ti in PLAYER_SELECTIONS[count]:
            t = PLAYER_TEMPLATES[ti]
            self.players.append(PlayerState(
                name=t["name"], short=t["short"],
                color=t["color"], light=t["light"], dark=t["dark"],
                emoji=t["emoji"],
                start_index=t["start_index"],
                home_lane=list(t["home_lane"]),
                base_slots=list(t["base_slots"]),
            ))
        self.current_player   = 0
        self.pending_roll     = None
        self.game_over        = False
        self.bonus_turn_ready = False
        self.turn_message     = "Roll a 6 to bring a token onto the board!"
        self.set_score(0)
        self.dice_widget.set_value(None)
        self.roll_value_label.setText("?")

        for i, card in enumerate(self.player_cards):
            if i < len(self.players):
                card.player = self.players[i]; card.show()
            else:
                card.hide()
        self._refresh_ui()

    def current_player_state(self) -> PlayerState:
        return self.players[self.current_player]

    def token_absolute_position(self, player: PlayerState, progress: int) -> int | None:
        if 0 <= progress < 52:
            return (player.start_index + progress) % 52
        return None

    def token_cell(self, player: PlayerState, ti: int) -> tuple[int, int]:
        prog = player.tokens[ti]
        if prog == -1:              return player.base_slots[ti]
        if prog == FINISH_PROGRESS: return 7, 7
        if prog < 52:               return TRACK_COORDS[self.token_absolute_position(player, prog)]
        return player.home_lane[prog - 52]

    def valid_token_indexes(self) -> list[int]:
        if self.pending_roll is None or self.game_over:
            return []
        player = self.current_player_state()
        return [ti for ti, prog in enumerate(player.tokens)
                if self._can_move(player, prog, self.pending_roll)]

    def roll_die(self) -> None:
        if self.pending_roll is not None or self.game_over or self.dice_widget._rolling:
            return
        self.bonus_turn_ready = False
        rolled = random.randint(1, 6)
        self.pending_roll = rolled
        self.roll_button.setEnabled(False)
        self.dice_widget.animate_to(rolled, frames=14)
        QTimer.singleShot(760, self._on_roll_done)

    def _on_roll_done(self) -> None:
        roll = self.pending_roll
        self.roll_value_label.setText(str(roll))
        self.sounds.play("click")
        if self.valid_token_indexes():
            self.turn_message = (
                f"{self.current_player_state().emoji} "
                f"{self.current_player_state().name} rolled {roll}! Pick a token to move."
            )
            self._refresh_ui()
        else:
            self.turn_message = (
                f"{self.current_player_state().emoji} "
                f"{self.current_player_state().name} rolled {roll} — no move available!"
            )
            self._refresh_ui()
            QTimer.singleShot(1500, self._auto_advance)

    def _auto_advance(self) -> None:
        self.pending_roll = None
        self._advance_turn(extra_turn=False)
        self._refresh_ui()

    def move_token(self, ti: int) -> None:
        # Guard: only act if this token is actually valid to move
        if ti not in self.valid_token_indexes():
            return
        if self.pending_roll is None or self.game_over or self.dice_widget._rolling:
            return
        player   = self.current_player_state()
        prog     = player.tokens[ti]
        roll     = self.pending_roll
        new_prog = 0 if prog == -1 else prog + roll
        player.tokens[ti] = new_prog
        capture_happened = finish_happened = False

        if new_prog == FINISH_PROGRESS:
            player.finished += 1; finish_happened = True
            self.sounds.play("success")
            self.turn_message = f"🏠 {player.name}: Token {ti+1} is home! Great job!"
        else:
            captured = self._resolve_capture(player, ti)
            capture_happened = captured is not None
            if capture_happened:
                player.captures += 1; self.sounds.play("score")
                self.turn_message = (
                    f"💥 {player.name} captured {captured.name}'s token! Back to base!")
            else:
                self.sounds.play("move")
                self.turn_message = (
                    f"{player.emoji} {player.name}: Token {ti+1} moved "
                    f"{roll} step{'s' if roll != 1 else ''}!")

        self.pending_roll = None
        self._update_score()
        if player.finished == TOKENS_PER_PLAYER:
            self.game_over = True
            self.turn_message = f"🏆 {player.name} wins! Congratulations!"
            self.sounds.play("success")
        else:
            self._advance_turn(
                extra_turn=(roll == 6 or capture_happened or finish_happened))
        self._refresh_ui()

    def _can_move(self, player: PlayerState, prog: int, roll: int) -> bool:
        if prog == FINISH_PROGRESS: return False
        if prog == -1:
            return roll == 6 and not self._blocked(player, player.start_index)
        target = prog + roll
        if target > FINISH_PROGRESS: return False
        if target < 52:
            return not self._blocked(
                player, self.token_absolute_position(player, target))
        return True

    def _blocked(self, cur: PlayerState, abs_idx: int) -> bool:
        return sum(
            1 for p in self.players if p is not cur
            for prog in p.tokens
            if self.token_absolute_position(p, prog) == abs_idx
        ) > 1

    def _resolve_capture(self, cur: PlayerState, ti: int) -> PlayerState | None:
        prog    = cur.tokens[ti]
        abs_idx = self.token_absolute_position(cur, prog)
        if abs_idx is None or abs_idx in SAFE_INDICES: return None
        opponents = [
            (p, ei) for p in self.players if p is not cur
            for ei, ep in enumerate(p.tokens)
            if self.token_absolute_position(p, ep) == abs_idx
        ]
        if len(opponents) != 1: return None
        opp, ei = opponents[0]; opp.tokens[ei] = -1
        return opp

    def _advance_turn(self, *, extra_turn: bool) -> None:
        if self.game_over: return
        if extra_turn:
            self.bonus_turn_ready = True
            self.turn_message += (
                f"  🎯 {self.current_player_state().name} gets another turn!")
        else:
            self.bonus_turn_ready = False
            self.current_player = (self.current_player + 1) % len(self.players)
        self.dice_widget.set_value(None)
        self.roll_value_label.setText("?")

    def _update_score(self) -> None:
        self.set_score(max(
            (p.finished * 100 + p.captures * 15 for p in self.players), default=0))

    # ─────────────────────────────────────────────────────────────────────────
    #  UI refresh
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_ui(self) -> None:
        player = self.current_player_state()

        # Top bar
        self._turn_dot.setStyleSheet(
            f"border-radius:10px; background:{player.color};")
        self.turn_label.setText(
            f"{player.emoji}  {player.name}'s Turn")
        self.turn_label.setStyleSheet(
            f"font-weight:800; font-size:18px; color:{player.dark};")
        self.status_label.setText(self.turn_message)

        # Roll button
        can_roll = (self.pending_roll is None and not self.game_over
                    and not self.dice_widget._rolling)
        self.roll_button.setEnabled(can_roll)

        # Token buttons — always visually enabled when it's your turn,
        # but only movable tokens respond to clicks
        valid = set(self.valid_token_indexes())
        live  = self.pending_roll is not None and not self.dice_widget._rolling

        # Hint label in the dice card
        if self.game_over:
            self._bonus_lbl.setText("🏆 Game over!")
        elif self.bonus_turn_ready:
            self._bonus_lbl.setText("🎯 Bonus turn — roll again!")
        elif live and valid:
            self._bonus_lbl.setText("✨ Tap a glowing token on the board!")
        elif live and not valid:
            self._bonus_lbl.setText("😅 No moves — turn passes automatically")
        else:
            self._bonus_lbl.setText("")

        # Player cards
        for i, card in enumerate(self.player_cards):
            if i < len(self.players):
                card.refresh(active=(i == self.current_player and not self.game_over))

        self.board.update()
