from __future__ import annotations
import random
from dataclasses import dataclass
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY

SUITS  = ["♠", "♥", "♦", "♣"]
VALUES = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
SUIT_COLORS = {"♠": "#0B1221", "♣": "#0B1221", "♥": "#FF3B30", "♦": "#FF3B30"}
VALUE_ORDER = {v: i for i, v in enumerate(VALUES)}

CARD_W, CARD_H = 80, 112

@dataclass
class Card:
    suit: str; value: str; face_up: bool = False
    @property
    def color(self) -> str: return SUIT_COLORS[self.suit]
    @property
    def rank(self) -> int: return VALUE_ORDER[self.value]
    @property
    def is_red(self) -> bool: return self.suit in ("♥", "♦")

def draw_card(p: QPainter, card: Card | None, x: float, y: float, w: float = CARD_W, h: float = CARD_H, selected: bool = False, highlight: str = "") -> None:
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = QRectF(x, y, w, h); path = QPainterPath(); path.addRoundedRect(r, 12, 12)

    # Layered Shadow
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0, 0, 0, 45)); p.drawRoundedRect(r.adjusted(1, 2, 1, 3), 12, 12)
    p.setBrush(QColor(0, 0, 0, 25)); p.drawRoundedRect(r.adjusted(2, 4, 2, 6), 12, 12)

    if card is None:
        p.setBrush(QColor(PALETTE["surface_low"])); p.setPen(QPen(QColor(PALETTE["border"]), 1.5, Qt.PenStyle.DashLine))
        p.drawPath(path); return

    if not card.face_up:
        from PyQt6.QtGui import QLinearGradient
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, QColor(PALETTE["primary"]))
        grad.setColorAt(1, QColor("#1A2A4E"))
        p.setBrush(grad); p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.drawPath(path)
        # Modern Geometric Pattern
        p.setPen(QPen(QColor(255, 255, 255, 15), 1.2))
        for i in range(0, int(w), 8): p.drawLine(QPointF(x+i, y), QPointF(x+w-i, y+h))
        for i in range(0, int(h), 8): p.drawLine(QPointF(x, y+i), QPointF(x+w, y+h-i))
        return

    # Face-up
    bg = QColor(255, 255, 255) if not highlight else QColor(highlight)
    p.setBrush(bg); p.setPen(QPen(QColor(PALETTE["primary"]) if selected else QColor(PALETTE["border"]), 2 if selected else 1))
    p.drawPath(path)

    col = QColor(card.color); p.setPen(col)
    font_sm = QFont(FONT_BODY, max(8, int(h * 0.15)), QFont.Weight.ExtraBold)
    font_lg = QFont(FONT_TITLE, max(12, int(h * 0.3)), QFont.Weight.Black)

    p.setFont(font_sm)
    p.drawText(QRectF(x+6, y+4, w*0.4, h*0.25), Qt.AlignmentFlag.AlignLeft, card.value)
    p.drawText(QRectF(x+6, y+h*0.14, w*0.4, h*0.22), Qt.AlignmentFlag.AlignLeft, card.suit)

    p.setFont(font_lg); p.drawText(r, Qt.AlignmentFlag.AlignCenter, card.suit)

    p.setFont(font_sm)
    p.drawText(QRectF(x+w*0.5, y+h*0.6, w*0.4, h*0.25), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, card.value)
    p.drawText(QRectF(x+w*0.5, y+h*0.75, w*0.4, h*0.22), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, card.suit)
