from __future__ import annotations
import random, time
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QFrame
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton, StatChip
from hub.games.cards import draw_card, Card
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY

EMOJIS = ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🐔"]
GRID = 4

class MemoryBoard(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen; self.setMinimumSize(450, 450)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cs = min(self.width(), self.height()) / GRID; pad = cs * 0.12
        ox, oy = (self.width()-cs*GRID)/2, (self.height()-cs*GRID)/2
        
        for i, (emoji, face_up, matched) in enumerate(self.screen.cards):
            row, col = divmod(i, GRID)
            x, y = ox + col*cs + pad, oy + row*cs + pad
            card_w, card_h = cs - pad*2, cs - pad*2
            
            # Use draw_card as base
            p.setOpacity(0.5 if matched else 1.0)
            mock_card = Card("♠", "A", face_up=face_up or matched)
            draw_card(p, mock_card, x, y, card_w, card_h, highlight=PALETTE["success"] if matched else "")
            
            if face_up or matched:
                p.setFont(QFont("Segoe UI", int(card_h * 0.5)))
                p.drawText(QRectF(x, y, card_w, card_h), Qt.AlignmentFlag.AlignCenter, emoji)
            p.setOpacity(1.0)

    def mousePressEvent(self, e):
        cs = min(self.width(), self.height()) / GRID
        ox, oy = (self.width()-cs*GRID)/2, (self.height()-cs*GRID)/2
        col, row = int((e.position().x()-ox)/cs), int((e.position().y()-oy)/cs)
        if 0 <= row < GRID and 0 <= col < GRID: self.screen.flip(row*GRID+col)

class MemoryMatchScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("memory_match", "Memory Match", "A premium cognitive challenge of recall and precision.", "#a855f7", storage, sounds, parent)
        self.cards = []; self._flipped = []; self._locked = False
        self._pairs, self._moves = 0, 0

        header = QFrame(); header.setObjectName("GlassCard"); header.setFixedHeight(90)
        hl = QHBoxLayout(header); hl.setContentsMargins(24, 0, 24, 0)
        self._status = QLabel("FIND ALL 8 PAIRS"); self._status.setStyleSheet(f"font-family:'{FONT_TITLE}'; font-weight:900; font-size:18px; color:{PALETTE['primary']};")
        hl.addWidget(self._status); hl.addStretch(1)
        self._moves_lbl = QLabel("MOVES: 0"); self._moves_lbl.setObjectName("MutedLabel")
        hl.addWidget(self._moves_lbl); hl.addSpacing(20)
        new_btn = NeonButton("RESET"); new_btn.setFixedSize(110, 44); new_btn.clicked.connect(self.reset_game)
        hl.addWidget(new_btn)
        self.content_layout.addWidget(header)

        self.board = MemoryBoard(self); self.content_layout.addWidget(self.board, 1)
        self.reset_game()

    def reset_game(self):
        pool = random.sample(EMOJIS, 8); deck = pool * 2; random.shuffle(deck)
        self.cards = [(e, False, False) for e in deck]
        self._flipped, self._locked = [], False
        self._pairs, self._moves = 0, 0; self._refresh()

    def _refresh(self):
        self._moves_lbl.setText(f"MOVES: {self._moves}")
        rem = 8 - self._pairs
        self._status.setText(f"PAIRS REMAINING: {rem}" if rem > 0 else "CONGRATULATIONS!")
        self.board.update()

    def flip(self, idx):
        if self._locked: return
        e, fu, matched = self.cards[idx]
        if fu or matched or idx in self._flipped: return
        self.cards[idx] = (e, True, False); self._flipped.append(idx)
        self.sounds.play("click"); self.board.update()
        if len(self._flipped) == 2:
            self._moves += 1; self._locked = True
            QTimer.singleShot(600, self._check_pair)

    def _check_pair(self):
        a, b = self._flipped; ea, eb = self.cards[a][0], self.cards[b][0]
        if ea == eb:
            self.cards[a] = (ea, True, True); self.cards[b] = (eb, True, True)
            self._pairs += 1; self.sounds.play("success")
            if self._pairs == 8: self.show_game_over("🎉", "MATCH MASTER", self._pairs*50, 0, f"Victory in {self._moves} moves!")
        else:
            self.cards[a] = (ea, False, False); self.cards[b] = (eb, False, False)
        self._flipped, self._locked = [], False; self._refresh()
