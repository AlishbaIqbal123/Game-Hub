from __future__ import annotations
import random, time
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient, QBrush, QRadialGradient
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QFrame
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton, StatChip
from hub.games.cards import Card, draw_card, VALUES, CARD_W, CARD_H
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY

COLS = 10; SUIT = "♠"
V_OFF_HIDDEN, V_OFF_SHOWN = 20, 32

class SpiderBoard(QWidget):
    def __init__(self, screen: "SpiderScreen", parent=None):
        super().__init__(parent)
        self.screen = screen; self.setMinimumSize(900, 650)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._src_col, self._src_idx = -1, -1
        self._hover_col = -1; self._m_pos = QPointF(0,0)
        self.setMouseTracking(True)
        
        # Animations
        self._deal_timer = QTimer(self); self._deal_timer.timeout.connect(self._step_animations)
        self._anim_cards = [] # List of {pos, target, card, delay}
        self._deal_timer.start(16)

    def _step_animations(self):
        if not self._anim_cards: return
        t1 = time.time()
        for i in range(len(self._anim_cards)-1, -1, -1):
            a = self._anim_cards[i]
            if a['start_time'] > t1: continue
            
            # Interpolate
            elapsed = t1 - a['start_time']
            p = min(1.0, elapsed / 0.4) # 400ms duration
            ease = 1 - (1 - p)**3 # Ease out cubic
            
            a['current'] = QPointF(
                a['origin'].x() + (a['target'].x() - a['origin'].x()) * ease,
                a['origin'].y() + (a['target'].y() - a['origin'].y()) * ease
            )
            
            if p >= 1.0:
                self.screen.tableau[a['col']].append(a['card'])
                a['card'].face_up = True
                self._anim_cards.pop(i)
                self.screen.sounds.play("click")
        self.update()

    def _col_x(self, col: int) -> float:
        gap = 16; total = COLS * CARD_W + (COLS - 1) * gap
        ox = max(30.0, (self.width() - total) / 2)
        return ox + col * (CARD_W + gap)

    def _card_y(self, col: int, idx: int) -> float:
        cards = self.screen.tableau[col]
        n = len(cards)
        if n == 0: return 60.0
        
        # Adaptive stacking: if total height exceeds available room, compress
        base_y = 60.0
        avail = max(300, self.height() - base_y - CARD_H - 40)
        
        # Calculate theoretical height with standard offsets
        v_sh = V_OFF_SHOWN; v_hi = V_OFF_HIDDEN
        theo = sum(v_hi if not c.face_up else v_sh for c in cards[:-1])
        
        # Compression ratio
        ratio = min(1.0, avail / max(1, theo))
        
        y = base_y
        for i in range(idx):
            off = v_hi if not cards[i].face_up else v_sh
            y += off * ratio
        return y

    def _hit(self, mx: float, my: float) -> tuple[int, int]:
        # Loop columns
        for col in range(COLS-1, -1, -1):
            cards = self.screen.tableau[col]
            if not cards:
                # Check empty slot hit
                if QRectF(self._col_x(col), 60, CARD_W, CARD_H).contains(mx, my): return col, -1
                continue
                
            # Check cards from top to bottom (visually bottom to top)
            for idx in range(len(cards)-1, -1, -1):
                x, y = self._col_x(col), self._card_y(col, idx)
                if QRectF(x, y, CARD_W, CARD_H).contains(mx, my): return col, idx
        return -1, -1

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        mx, my = e.position().x(), e.position().y()
        
        # Check Deck Hit (Bottom Right)
        stock_x, stock_y = self.width() - 110, self.height() - 140
        if QRectF(stock_x - 40, stock_y - 20, CARD_W + 40, CARD_H + 20).contains(mx, my):
            self.screen.deal_stock()
            return

        col, idx = self._hit(mx, my)
        if col < 0: return
        if not self.screen.tableau[col][idx].face_up: return
        sub = self.screen.tableau[col][idx:]
        if self._is_seq(sub): self._src_col, self._src_idx = col, idx

    def _is_seq(self, cards: list[Card]) -> bool:
        for i in range(len(cards)-1):
            if cards[i].rank != cards[i+1].rank + 1: return False
        return True

    def mouseReleaseEvent(self, e):
        if self._src_col < 0: return
        mx = e.position().x()
        target = -1
        for col in range(COLS):
            if abs(mx - (self._col_x(col) + CARD_W/2)) < CARD_W/2 + 10:
                target = col; break
        if 0 <= target != self._src_col: self.screen.move_cards(self._src_col, self._src_idx, target)
        self._src_col = -1; self.update()

    def mouseMoveEvent(self, e):
        self._m_pos = e.position()
        mx = self._m_pos.x()
        old_h = self._hover_col; self._hover_col = -1
        for col in range(COLS):
            if abs(mx - (self._col_x(col) + CARD_W/2)) < CARD_W/2 + 10:
                self._hover_col = col; break
        if old_h != self._hover_col: self.update()
        if self._src_col >= 0: self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background: Rich felt with subtle radial vignette
        grad = QRadialGradient(QPointF(self.rect().center()), self.width()*0.8)
        grad.setColorAt(0, QColor("#12533E")); grad.setColorAt(1, QColor("#08241D"))
        p.fillRect(self.rect(), grad)
        
        # Felt Grain Pattern
        p.setPen(QPen(QColor(255,255,255,3), 1))
        for i in range(0, self.width(), 6): p.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 6): p.drawLine(0, i, self.width(), i)

        # Draw Foundations (Completed Sequences) at Bottom Left
        found_x, found_y = 30, self.height() - 140
        for i in range(8):
            fx = found_x + i * 18
            if i < self.screen.completed:
                # Show representing King for completed sequence
                draw_card(p, Card(SUIT, "K"), fx, found_y)
            else:
                # Ghostly slot for remaining sequences
                p.setOpacity(0.2)
                draw_card(p, None, fx, found_y)
                p.setOpacity(1.0)

        # Draw Stock Indicator (Bottom Right)
        stock_x, stock_y = self.width() - 110, self.height() - 140
        for i in range(len(self.screen.stock_piles)):
            draw_card(p, Card(SUIT, "K", face_up=False), stock_x - i*3, stock_y - i*3)

        # Empty slots (Ghost targets)
        p.setOpacity(0.4)
        for col in range(COLS): draw_card(p, None, self._col_x(col), 60)
        p.setOpacity(1.0)

        # Tableau
        for col in range(COLS):
            cards = self.screen.tableau[col]
            x = self._col_x(col)
            # Highlight target column
            if self._hover_col == col and self._src_col >= 0:
                p.setBrush(QColor(255, 255, 255, 15))
                p.drawRoundedRect(QRectF(x-4, 56, CARD_W+8, self.height()-100), 12, 12)

            for idx, c in enumerate(cards):
                if col == self._src_col and idx >= self._src_idx: continue
                draw_card(p, c, x, self._card_y(col, idx))

        # Flying cards
        for a in self._anim_cards:
            if time.time() > a['start_time']:
                draw_card(p, a['card'], a['current'].x(), a['current'].y())

        # Dragging Ghost
        if self._src_col >= 0:
            dragging = self.screen.tableau[self._src_col][self._src_idx:]
            p.setOpacity(0.9)
            gx, gy = self._m_pos.x() - CARD_W/2, self._m_pos.y() - 30
            for i, c in enumerate(dragging):
                draw_card(p, c, gx, gy + i*V_OFF_SHOWN, selected=True)
            p.setOpacity(1.0)


class SpiderScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("spider_solitaire", "Spider Solitaire", "Premium 1-Suit Edition — Strategic and Fluid", "#22d98a", storage, sounds, parent)
        self.tableau: list[list[Card]] = [[] for _ in range(COLS)]
        self.stock_piles: list[list[Card]] = []
        self.completed, self._moves = 0, 0

        # Compact sub-header
        sub_hdr = QHBoxLayout(); sub_hdr.setContentsMargins(10, 0, 10, 0)
        self._score_lbl = QLabel("SCORE: 0"); self._score_lbl.setStyleSheet(f"font-family:'{FONT_TITLE}'; font-size:18px; font-weight:800; color:{PALETTE['primary']};")
        self._meta_lbl = QLabel("MOVES: 0"); self._meta_lbl.setObjectName("MutedLabel")
        sub_hdr.addWidget(self._score_lbl); sub_hdr.addSpacing(20); sub_hdr.addWidget(self._meta_lbl); sub_hdr.addStretch(1)
        
        deal_btn = NeonButton("DEAL NEW ROW", primary=True); deal_btn.setFixedSize(160, 40)
        deal_btn.clicked.connect(self.deal_stock)
        sub_hdr.addWidget(deal_btn)
        
        self.undo_btn = NeonButton("UNDO", accent=PALETTE['secondary']); self.undo_btn.setFixedSize(80, 40)
        self.undo_btn.clicked.connect(self.undo)
        sub_hdr.addWidget(self.undo_btn)

        reset_btn = NeonButton("RESTART"); reset_btn.setFixedSize(100, 40)
        reset_btn.clicked.connect(self.reset_game)
        sub_hdr.addWidget(reset_btn)
        self.content_layout.addLayout(sub_hdr)

        self._history = []
        self.board = SpiderBoard(self)
        self.content_layout.addWidget(self.board, 1)
        self.reset_game()
        self.show_tutorial([
            {"emoji": "🃏", "title": "Fluid Motion", "body": "Experience smooth card fanning and flying animations while you play."},
            {"emoji": "📦", "title": "Deal row", "body": "Need more options? Deal a new card to every column from the stock."},
            {"emoji": "🕷️", "title": "The Web", "body": "Clear all 8 sequences to claim your place on the leaderboard."}
        ])

    def reset_game(self):
        d = [Card(SUIT, v) for _ in range(8) for v in VALUES]; random.shuffle(d)
        self.tableau = [[] for _ in range(COLS)]
        self.completed, self._moves = 0, 0
        self.board._anim_cards = []
        # Deal initial
        for col in range(COLS):
            n = 6 if col < 4 else 5
            for _ in range(n):
                c = d.pop(); c.face_up = False; self.tableau[col].append(c)
            self.tableau[col][-1].face_up = True
        self.stock_piles = [d[i*10:(i+1)*10] for i in range(5)]
        self._history = []
        self.set_score(0); self._refresh()

    def _save_state(self):
        import copy
        state = {
            "tableau": copy.deepcopy(self.tableau),
            "stock": copy.deepcopy(self.stock_piles),
            "completed": self.completed,
            "moves": self._moves
        }
        self._history.append(state)
        if len(self._history) > 50: self._history.pop(0)

    def undo(self):
        if not self._history or self.board._anim_cards: return
        state = self._history.pop()
        self.tableau = state["tableau"]
        self.stock_piles = state["stock"]
        self.completed = state["completed"]
        self._moves    = state["moves"]
        self.sounds.play("click")
        self._refresh()

    def keyPressEvent(self, e):
        from PyQt6.QtCore import Qt
        if e.key() == Qt.Key.Key_Z and e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo()
        else:
            super().keyPressEvent(e)

    def _refresh(self):
        s = max(0, self.completed * 500 - self._moves * 2)
        self._score_lbl.setText(f"SCORE: {s}")
        self._meta_lbl.setText(f"MOVES: {self._moves}  |  COMPLETE: {self.completed}/8")
        self.board.update()

    def move_cards(self, src_col, src_idx, dst_col):
        self._save_state()
        src, dst = self.tableau[src_col], self.tableau[dst_col]
        moving = src[src_idx:]
        if dst and (not dst[-1].face_up or dst[-1].rank != moving[0].rank + 1): return
        
        self.tableau[dst_col].extend(moving); del self.tableau[src_col][src_idx:]
        if self.tableau[src_col]: self.tableau[src_col][-1].face_up = True
        self._moves += 1; self.sounds.play("move")
        self._check_complete(dst_col); self._refresh()

    def _check_complete(self, col):
        cards = self.tableau[col]
        if len(cards) < 13: return
        tail = cards[-13:]
        if tail[0].rank != 12 or not self.board._is_seq(tail): return # rank 12 is King
        
        # Animate flight to bottom left foundation
        origin = QPointF(self.board._col_x(col), self.board._card_y(col, len(cards)-13))
        target = QPointF(30 + self.completed * 18, self.board.height() - 140)
        self.board._anim_cards.append({
            'origin': origin, 'current': origin, 'target': target,
            'card': tail[0], 'col': -1, 'start_time': time.time()
        })

        del self.tableau[col][-13:]
        if self.tableau[col]: self.tableau[col][-1].face_up = True
        self.completed += 1; self.sounds.play("success")
        if self.completed == 8: self.show_game_over("🏆", "SPIDER MASTER", 5000, 0, "All 8 sequences completed!")
        self._refresh()

    def deal_stock(self):
        # Force clear if something is stuck
        if self.board._anim_cards and len(self.board._anim_cards) > 20: 
            self.board._anim_cards = []
            
        if not self.stock_piles or self.board._anim_cards: return
        self._save_state()
        pile = self.stock_piles.pop(0)
        origin = QPointF(self.board.width() - 110, self.board.height() - 140)
        t_base = time.time()
        for col, c in enumerate(pile):
            target = QPointF(self.board._col_x(col), self.board._card_y(col, len(self.tableau[col])))
            self.board._anim_cards.append({
                'origin': origin, 'current': origin, 'target': target,
                'card': c, 'col': col, 'start_time': t_base + col*0.06
            })
        self._moves += 1; self.sounds.play("click"); self._refresh()
