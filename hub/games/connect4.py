from __future__ import annotations
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

ROWS, COLS = 6, 7
EMPTY, P1, P2 = 0, 1, 2
COLORS = {P1: "#FF4757", P2: "#FFD32A"}
NAMES  = {P1: "🔴 Red", P2: "🟡 Yellow"}


class BoardWidget(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(420, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover_col = -1
        self.setMouseTracking(True)

    def _cell(self):
        cs = min(self.width() / COLS, self.height() / ROWS)
        ox = (self.width()  - cs * COLS) / 2
        oy = (self.height() - cs * ROWS) / 2
        return cs, ox, oy

    def mouseMoveEvent(self, e):
        cs, ox, _ = self._cell()
        col = int((e.position().x() - ox) / cs)
        self._hover_col = col if 0 <= col < COLS else -1
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            cs, ox, _ = self._cell()
            col = int((e.position().x() - ox) / cs)
            if 0 <= col < COLS:
                self.screen.drop(col)

    def leaveEvent(self, e):
        self._hover_col = -1; self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cs, ox, oy = self._cell()
        r = cs * 0.40

        # Board background
        p.setBrush(QColor(20, 50, 140))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(ox, oy, cs*COLS, cs*ROWS), 14, 14)

        # Hover column highlight
        if 0 <= self._hover_col < COLS and not self.screen.game_over:
            hc = QColor(255, 255, 255, 25)
            p.setBrush(hc)
            p.drawRect(QRectF(ox + self._hover_col*cs, oy, cs, cs*ROWS))

        # Cells
        for row in range(ROWS):
            for col in range(COLS):
                cx = ox + (col + 0.5) * cs
                cy = oy + (row + 0.5) * cs
                v  = self.screen.board[row][col]
                win_cells = set(self.screen.win_cells)

                if v == EMPTY:
                    p.setBrush(QColor(8, 20, 60))
                else:
                    base = QColor(COLORS[v])
                    if (row, col) in win_cells:
                        base = base.lighter(140)
                    g = QRadialGradient(QPointF(cx - r*0.3, cy - r*0.3), r*1.4)
                    g.setColorAt(0, base.lighter(130))
                    g.setColorAt(1, base)
                    p.setBrush(g)

                p.setPen(QPen(QColor(10, 30, 90), 1))
                p.drawEllipse(QPointF(cx, cy), r, r)

        # Drop indicator arrow
        if 0 <= self._hover_col < COLS and not self.screen.game_over:
            cx = ox + (self._hover_col + 0.5) * cs
            cy = oy - cs * 0.35
            col = QColor(COLORS[self.screen.current])
            p.setBrush(col); p.setPen(Qt.PenStyle.NoPen)
            pts = [QPointF(cx, cy+cs*0.28), QPointF(cx-cs*0.18, cy),
                   QPointF(cx+cs*0.18, cy)]
            from PyQt6.QtGui import QPolygonF
            p.drawPolygon(QPolygonF(pts))


class Connect4Screen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("connect4", "Connect 4",
                         "Drop discs to connect four in a row before your opponent!",
                         "#FF4757", storage, sounds, parent)
        self.board: list[list[int]] = []
        self.current = P1
        self.game_over = False
        self.win_cells: list[tuple] = []

        top = QHBoxLayout(); top.setSpacing(12)
        self._turn_lbl = QLabel()
        self._turn_lbl.setStyleSheet("font-size:16px; font-weight:800;")
        top.addWidget(self._turn_lbl, 1)
        new_btn = NeonButton("🔄 New Game", primary=True)
        new_btn.setFixedHeight(40); new_btn.clicked.connect(self.reset_game)
        top.addWidget(new_btn)
        self.content_layout.addLayout(top)

        self.board_w = BoardWidget(self)
        self.content_layout.addWidget(self.board_w, 1)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "🔴", "title": "Welcome to Connect 4!",
             "body": "Two players take turns dropping coloured discs into a 7-column grid. You are Red, the AI is Yellow."},
            {"emoji": "🎯", "title": "How to Win",
             "body": "Be the first to connect FOUR of your discs in a row — horizontally, vertically, or diagonally!"},
            {"emoji": "👆", "title": "How to Play",
             "body": "Click any column to drop your disc. It falls to the lowest empty row. Plan ahead to block your opponent!"},
            {"emoji": "🤖", "title": "The AI",
             "body": "The AI will try to win and block you. It looks one move ahead — can you outsmart it?"},
        ])

    def reset_game(self):
        self.board = [[EMPTY]*COLS for _ in range(ROWS)]
        self.current = P1; self.game_over = False; self.win_cells = []
        self.set_score(0); self._refresh()

    def _refresh(self):
        self._turn_lbl.setText(f"{NAMES[self.current]}'s Turn")
        self._turn_lbl.setStyleSheet(
            f"font-size:16px; font-weight:800; color:{COLORS[self.current]};")
        self.board_w.update()

    def drop(self, col: int):
        if self.game_over: return
        row = self._lowest(col)
        if row < 0: return
        self.board[row][col] = self.current
        self.sounds.play("move")
        winner = self._check_win(row, col)
        if winner:
            self.win_cells = self._winning_cells(row, col)
            self.game_over = True
            self.sounds.play("success")
            self.set_score(100)
            self._refresh()
            self.show_game_over("🏆", f"{NAMES[winner]} Wins!", 100,
                                message="Great game! Play again?")
            return
        if all(self.board[0][c] != EMPTY for c in range(COLS)):
            self.game_over = True
            self.show_game_over("🤝", "It's a Draw!", 0, message="The board is full!")
            return
        self.current = P2 if self.current == P1 else P1
        self._refresh()
        if self.current == P2:
            QTimer.singleShot(400, self._ai_move)

    def _lowest(self, col):
        for r in range(ROWS-1, -1, -1):
            if self.board[r][col] == EMPTY: return r
        return -1

    def _ai_move(self):
        if self.game_over: return
        # Win if possible
        for c in range(COLS):
            r = self._lowest(c)
            if r >= 0:
                self.board[r][c] = P2
                if self._check_win(r, c): self.board[r][c] = EMPTY; self.drop(c); return
                self.board[r][c] = EMPTY
        # Block player
        for c in range(COLS):
            r = self._lowest(c)
            if r >= 0:
                self.board[r][c] = P1
                if self._check_win(r, c): self.board[r][c] = EMPTY; self.drop(c); return
                self.board[r][c] = EMPTY
        # Prefer centre
        for c in [3,2,4,1,5,0,6]:
            if self._lowest(c) >= 0: self.drop(c); return

    def _check_win(self, row, col) -> int:
        v = self.board[row][col]
        if v == EMPTY: return 0
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            count = 1
            for sign in (1, -1):
                r2, c2 = row+dr*sign, col+dc*sign
                while 0<=r2<ROWS and 0<=c2<COLS and self.board[r2][c2]==v:
                    count += 1; r2+=dr*sign; c2+=dc*sign
            if count >= 4: return v
        return 0

    def _winning_cells(self, row, col):
        v = self.board[row][col]; cells = []
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            line = [(row, col)]
            for sign in (1, -1):
                r2, c2 = row+dr*sign, col+dc*sign
                while 0<=r2<ROWS and 0<=c2<COLS and self.board[r2][c2]==v:
                    line.append((r2,c2)); r2+=dr*sign; c2+=dc*sign
            if len(line) >= 4: cells = line; break
        return cells
