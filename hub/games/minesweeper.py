from __future__ import annotations
import random
from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

ROWS, COLS, MINES = 9, 9, 10
NUM_COLORS = ["","#4488ff","#22d98a","#ff4da6","#a855f7",
              "#ff8c00","#00d4ff","#ff5555","#888888"]


class MineGrid(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(360, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _cs(self): return min(self.width()/COLS, self.height()/ROWS)
    def _origin(self):
        cs = self._cs()
        return (self.width()-cs*COLS)/2, (self.height()-cs*ROWS)/2

    def mousePressEvent(self, e):
        cs = self._cs(); ox, oy = self._origin()
        col = int((e.position().x()-ox)/cs)
        row = int((e.position().y()-oy)/cs)
        if not (0<=row<ROWS and 0<=col<COLS): return
        if e.button() == Qt.MouseButton.LeftButton:
            self.screen.reveal(row, col)
        elif e.button() == Qt.MouseButton.RightButton:
            self.screen.flag(row, col)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cs = self._cs(); ox, oy = self._origin()
        pad = 2

        for row in range(ROWS):
            for col in range(COLS):
                x = ox+col*cs+pad; y = oy+row*cs+pad
                w = cs-pad*2;      h = cs-pad*2
                r = QRectF(x, y, w, h)
                state = self.screen.state[row][col]  # 'H','R','F','X'
                val   = self.screen.grid[row][col]   # -1=mine, 0-8=count

                if state == 'H':
                    p.setBrush(QColor(30, 50, 100))
                    p.setPen(QPen(QColor(50, 80, 150), 1))
                elif state == 'F':
                    p.setBrush(QColor(255, 140, 0, 60))
                    p.setPen(QPen(QColor(255, 140, 0), 1.5))
                elif state == 'X':
                    p.setBrush(QColor(255, 50, 50, 80))
                    p.setPen(QPen(QColor(255, 50, 50), 1.5))
                else:  # Revealed
                    p.setBrush(QColor(10, 20, 50))
                    p.setPen(QPen(QColor(30, 50, 100), 1))
                p.drawRoundedRect(r, 6, 6)

                fs = max(8, int(cs*0.38))
                p.setFont(QFont("Segoe UI", fs, QFont.Weight.Bold))
                if state == 'F':
                    p.setPen(QColor(255, 140, 0))
                    p.drawText(r, Qt.AlignmentFlag.AlignCenter, "🚩")
                elif state == 'X':
                    p.setPen(QColor(255, 80, 80))
                    p.drawText(r, Qt.AlignmentFlag.AlignCenter, "💣")
                elif state == 'R' and val > 0:
                    p.setPen(QColor(NUM_COLORS[val]))
                    p.drawText(r, Qt.AlignmentFlag.AlignCenter, str(val))
                elif state == 'R' and val == -1:
                    p.setPen(QColor(255, 80, 80))
                    p.drawText(r, Qt.AlignmentFlag.AlignCenter, "💣")


class MinesweeperScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("minesweeper", "Minesweeper",
                         "Reveal all safe squares without hitting a mine!",
                         "#22d98a", storage, sounds, parent)
        self.grid:  list[list[int]] = []
        self.state: list[list[str]] = []  # H=hidden R=revealed F=flagged X=exploded
        self._first = True; self._revealed = 0

        top = QHBoxLayout(); top.setSpacing(12)
        self._info = QLabel(f"💣 {MINES} mines  |  Right-click to flag")
        self._info.setStyleSheet("font-size:14px; color:#8899cc;")
        top.addWidget(self._info, 1)
        self._flags_lbl = QLabel("🚩 0")
        self._flags_lbl.setStyleSheet("font-size:14px; font-weight:700;")
        top.addWidget(self._flags_lbl)
        new_btn = NeonButton("🔄 New Game", primary=True)
        new_btn.setFixedHeight(40); new_btn.clicked.connect(self.reset_game)
        top.addWidget(new_btn)
        self.content_layout.addLayout(top)

        self.mine_grid = MineGrid(self)
        self.content_layout.addWidget(self.mine_grid, 1)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "💣", "title": "Welcome to Minesweeper!",
             "body": f"There are {MINES} hidden mines in a {ROWS}×{COLS} grid. Reveal all safe squares to win!"},
            {"emoji": "👆", "title": "Left Click to Reveal",
             "body": "Click a square to reveal it. Numbers show how many mines are in the 8 surrounding squares."},
            {"emoji": "🚩", "title": "Right Click to Flag",
             "body": "Right-click a square you think has a mine to place a flag. This helps you keep track!"},
            {"emoji": "🏆", "title": "Win!",
             "body": "Reveal every safe square without clicking a mine. Use the numbers to deduce where mines are hiding!"},
        ])

    def reset_game(self):
        self.grid  = [[0]*COLS for _ in range(ROWS)]
        self.state = [['H']*COLS for _ in range(ROWS)]
        self._first = True; self._revealed = 0
        self.set_score(0); self._refresh()

    def _place_mines(self, safe_r, safe_c):
        safe = {(safe_r+dr, safe_c+dc) for dr in range(-1,2) for dc in range(-1,2)}
        cells = [(r,c) for r in range(ROWS) for c in range(COLS) if (r,c) not in safe]
        for r,c in random.sample(cells, MINES):
            self.grid[r][c] = -1
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == -1: continue
                self.grid[r][c] = sum(
                    1 for dr in range(-1,2) for dc in range(-1,2)
                    if 0<=r+dr<ROWS and 0<=c+dc<COLS and self.grid[r+dr][c+dc]==-1)

    def _refresh(self):
        flags = sum(1 for r in range(ROWS) for c in range(COLS) if self.state[r][c]=='F')
        self._flags_lbl.setText(f"🚩 {flags}")
        self.mine_grid.update()

    def reveal(self, row, col):
        if self.state[row][col] != 'H': return
        if self._first:
            self._place_mines(row, col); self._first = False
        if self.grid[row][col] == -1:
            self.state[row][col] = 'X'
            self.sounds.play("lose")
            for r in range(ROWS):
                for c in range(COLS):
                    if self.grid[r][c]==-1 and self.state[r][c]=='H':
                        self.state[r][c]='R'
            self._refresh()
            self.show_game_over("💥", "Boom! You hit a mine!", 0, message="Try again — use the numbers!")
            return
        self._flood(row, col)
        self.sounds.play("move")
        safe = ROWS*COLS - MINES
        if self._revealed >= safe:
            score = 500
            self.set_score(score)
            self.show_game_over("🏆", "You cleared the board!", score, message="All mines avoided!")
        else:
            self.set_score(self._revealed * 2)
        self._refresh()

    def _flood(self, row, col):
        if not (0<=row<ROWS and 0<=col<COLS): return
        if self.state[row][col] != 'H': return
        self.state[row][col] = 'R'; self._revealed += 1
        if self.grid[row][col] == 0:
            for dr in range(-1,2):
                for dc in range(-1,2):
                    self._flood(row+dr, col+dc)

    def flag(self, row, col):
        if self.state[row][col] == 'H':
            self.state[row][col] = 'F'; self.sounds.play("click")
        elif self.state[row][col] == 'F':
            self.state[row][col] = 'H'
        self._refresh()
