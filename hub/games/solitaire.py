from __future__ import annotations
import random, time
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget, QFrame
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton
from hub.games.cards import Card, draw_card, SUITS, VALUES, CARD_W, CARD_H
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY

class SolitaireBoard(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen; self.setMinimumSize(950, 700)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._src_type = ""; self._src_col = -1; self._src_idx = -1
        self._hover_area = ""; self._hover_col = -1; self._m_pos = QPointF(0,0)
        self.setMouseTracking(True)

    def _foundation_rect(self, i: int) -> QRectF:
        return QRectF(300 + i*(CARD_W+20), 40, CARD_W, CARD_H)

    def _tableau_x(self, col: int) -> float:
        gap = 24; total = 7 * CARD_W + 6 * gap
        ox = (self.width() - total) / 2
        return ox + col * (CARD_W + gap)

    def _tableau_y(self, col, idx) -> float:
        cards = self.screen.tableau[col]
        if not cards: return 200.0
        
        base_y = 200.0
        avail = max(200, self.height() - base_y - CARD_H - 40)
        
        # Klondike offsets: 18 hidden, 34 shown
        v_sh, v_hi = 34, 18
        theo = sum(v_hi if not c.face_up else v_sh for c in cards[:-1])
        
        ratio = min(1.0, avail / max(1, theo))
        
        y = base_y
        for i in range(idx):
            off = v_hi if not cards[i].face_up else v_sh
            y += off * ratio
        return y

    def _hit(self, pos: QPointF) -> tuple[str, int, int]:
        # Foundation
        for i in range(4):
            if self._foundation_rect(i).contains(pos): return "foundation", i, -1
        # Tableau
        for col in range(6, -1, -1):
            cards = self.screen.tableau[col]
            for idx in range(len(cards)-1, -1, -1):
                x, y = self._tableau_x(col), self._tableau_y(col, idx)
                if QRectF(x, y, CARD_W, CARD_H).contains(pos): return "tableau", col, idx
            # Empty column slot hit
            if QRectF(self._tableau_x(col), 200, CARD_W, CARD_H).contains(pos): return "tableau", col, -1
        # Stock/Waste
        if QRectF(40, 40, CARD_W, CARD_H).contains(pos): return "stock", -1, -1
        if QRectF(40 + CARD_W + 24, 40, CARD_W, CARD_H).contains(pos): return "waste", -1, -1
        return "", -1, -1

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        area, col, idx = self._hit(e.position())
        if area == "stock": self.screen.draw_stock(); return
        if area == "waste" and self.screen.waste:
            self._src_type, self._src_col, self._src_idx = "waste", -1, -1
        elif area == "tableau" and col >= 0 and idx >= 0:
            if self.screen.tableau[col][idx].face_up:
                self._src_type, self._src_col, self._src_idx = "tableau", col, idx
        elif area == "foundation" and col >= 0 and self.screen.foundations[col]:
             self._src_type, self._src_col, self._src_idx = "foundation", col, -1

    def mouseReleaseEvent(self, e):
        if not self._src_type: return
        area, col, _ = self._hit(e.position())
        if area: self.screen.try_move(self._src_type, self._src_col, self._src_idx, area, col)
        self._src_type = ""; self.update()

    def mouseMoveEvent(self, e):
        self._m_pos = e.position()
        old_a, old_c = self._hover_area, self._hover_col
        self._hover_area, self._hover_col, _ = self._hit(self._m_pos)
        if old_a != self._hover_area or old_c != self._hover_col or self._src_type: self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QRadialGradient(QPointF(self.rect().center()), self.width()*0.7)
        grad.setColorAt(0, QColor("#12533E")); grad.setColorAt(1, QColor("#08241D"))
        p.fillRect(self.rect(), grad)

        # Stock/Waste slots
        draw_card(p, Card("♠", "A", False) if self.screen.stock else None, 40, 40)
        if self.screen.waste: draw_card(p, self.screen.waste[-1], 40 + CARD_W + 24, 40)
        else: draw_card(p, None, 40 + CARD_W + 24, 40)

        # Foundations
        for i in range(4):
            r = self._foundation_rect(i)
            draw_card(p, self.screen.foundations[i][-1] if self.screen.foundations[i] else None, r.x(), r.y())

        # Tableau
        for col in range(7):
            x = self._tableau_x(col)
            draw_card(p, None, x, 200)
            for idx, c in enumerate(self.screen.tableau[col]):
                if self._src_type == "tableau" and self._src_col == col and idx >= self._src_idx: continue
                draw_card(p, c, x, self._tableau_y(col, idx))

        # Dragging
        if self._src_type:
            p.setOpacity(0.9)
            gx, gy = self._m_pos.x() - CARD_W/2, self._m_pos.y() - 30
            if self._src_type == "waste": draw_card(p, self.screen.waste[-1], gx, gy, selected=True)
            elif self._src_type == "foundation": draw_card(p, self.screen.foundations[self._src_col][-1], gx, gy, selected=True)
            elif self._src_type == "tableau":
                sub = self.screen.tableau[self._src_col][self._src_idx:]
                for i, c in enumerate(sub): draw_card(p, c, gx, gy + i*34, selected=True)
            p.setOpacity(1.0)

class SolitaireScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("solitaire", "Klondike Solitaire", "The classic masterpiece of patience and strategy.", "#ffd60a", storage, sounds, parent)
        self.stock, self.waste = [], []
        self.foundations = [[] for _ in range(4)]
        self.tableau = [[] for _ in range(7)]
        self._moves = 0

        # Compact sub-header
        sub_hdr = QHBoxLayout(); sub_hdr.setContentsMargins(10, 0, 10, 0)
        self._stats = QLabel("SCORE: 0  |  MOVES: 0"); self._stats.setStyleSheet(f"font-family:'{FONT_TITLE}'; font-size:18px; font-weight:800; color:{PALETTE['primary']};")
        sub_hdr.addWidget(self._stats); sub_hdr.addStretch(1)
        self.undo_btn = NeonButton("UNDO", accent=PALETTE['secondary']); self.undo_btn.setFixedSize(80, 40)
        self.undo_btn.clicked.connect(self.undo)
        sub_hdr.addWidget(self.undo_btn)
        
        reset = NeonButton("RESTART"); reset.setFixedSize(100, 40); reset.clicked.connect(self.reset_game)
        sub_hdr.addWidget(reset)
        self.content_layout.addLayout(sub_hdr)

        self.board = SolitaireBoard(self); self.content_layout.addWidget(self.board, 1)
        self.reset_game()
        self.show_tutorial([
            {"emoji": "👑", "title": "Solitaire Legend", "body": "Stack cards in alternating colors and descending order (e.g., Red 9 on Black 10)."},
            {"emoji": "🃏", "title": "Building Foundations", "body": "Move Aces to the top foundation slots, then stack by suit from Ace to King to win!"},
            {"emoji": "📦", "title": "Stock & Waste", "body": "Draw cards from the stock pile to find new moves. When empty, click to recycle the waste pile."}
        ])

    def reset_game(self):
        d = [Card(s, v) for s in SUITS for v in VALUES]; random.shuffle(d)
        self.tableau = [[] for _ in range(7)]
        for i in range(7):
            for j in range(i+1):
                c = d.pop(); c.face_up = (j == i); self.tableau[i].append(c)
        self.foundations = [[] for _ in range(4)]; self.stock = d; self.waste = []
        self._history = []
        self._moves = 0; self._refresh()

    def _save_state(self):
        import copy
        state = {
            "stock": copy.deepcopy(self.stock),
            "waste": copy.deepcopy(self.waste),
            "foundations": copy.deepcopy(self.foundations),
            "tableau": copy.deepcopy(self.tableau),
            "moves": self._moves
        }
        self._history.append(state)
        if len(self._history) > 50: self._history.pop(0)

    def undo(self):
        if not self._history: return
        state = self._history.pop()
        self.stock = state["stock"]
        self.waste = state["waste"]
        self.foundations = state["foundations"]
        self.tableau = state["tableau"]
        self._moves = state["moves"]
        self.sounds.play("click")
        self._refresh()

    def keyPressEvent(self, e):
        from PyQt6.QtCore import Qt
        if e.key() == Qt.Key.Key_Z and e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo()
        else:
            super().keyPressEvent(e)

    def _refresh(self):
        self._stats.setText(f"SCORE: {self._calc_score()}  |  MOVES: {self._moves}")
        self.board.update()

    def _calc_score(self) -> int:
        return sum(len(f) for f in self.foundations) * 100 - self._moves

    def draw_stock(self):
        self._save_state()
        if not self.stock: self.stock = self.waste[::-1]; self.waste = []
        else: self.waste.append(self.stock.pop()); self.waste[-1].face_up = True
        self._moves += 1; self.sounds.play("click"); self._refresh()

    def try_move(self, s_type, s_col, s_idx, d_type, d_col):
        src = []
        if s_type == "waste": src = [self.waste[-1]]
        elif s_type == "foundation": src = [self.foundations[s_col][-1]]
        elif s_type == "tableau": src = self.tableau[s_col][s_idx:]

        valid = False
        if d_type == "foundation":
            if len(src) == 1:
                f = self.foundations[d_col]
                if not f: valid = (src[0].value == "A")
                else: valid = (src[0].suit == f[-1].suit and src[0].rank == f[-1].rank + 1)
        elif d_type == "tableau":
            t = self.tableau[d_col]
            if not t: valid = (src[0].value == "K")
            else: valid = (src[0].is_red != t[-1].is_red and src[0].rank == t[-1].rank - 1)

        if valid:
            self._save_state()
            if s_type == "waste": self.waste.pop()
            elif s_type == "foundation": self.foundations[s_col].pop()
            elif s_type == "tableau":
                del self.tableau[s_col][s_idx:]
                if self.tableau[s_col]: self.tableau[s_col][-1].face_up = True
            
            if d_type == "foundation": self.foundations[d_col].extend(src)
            else: self.tableau[d_col].extend(src)
            self._moves += 1; self.sounds.play("move"); self._refresh()
            if sum(len(f) for f in self.foundations) == 52: self.show_game_over("🏆", "PATIENCE REWARDED", self._calc_score(), 0, "Victory!")
