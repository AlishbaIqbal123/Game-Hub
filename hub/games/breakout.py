from __future__ import annotations
import random
from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_COLORS = ["#FF4757","#FF6B35","#FFD32A","#2ED573","#00d4ff","#a855f7"]
PAD_W, PAD_H = 100, 14
BALL_R = 8


class BreakoutCanvas(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        self.screen.pad_x = max(0, min(self.width()-PAD_W,
                                       e.position().x() - PAD_W/2))
        self.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Left:
            self.screen.pad_x = max(0, self.screen.pad_x - 20)
        elif e.key() == Qt.Key.Key_Right:
            self.screen.pad_x = min(self.width()-PAD_W, self.screen.pad_x + 20)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(8, 12, 28))

        # Bricks
        bw = (w - 20) / BRICK_COLS
        bh = 22
        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                if self.screen.bricks[r][c]:
                    x = 10 + c*bw; y = 40 + r*(bh+4)
                    col = QColor(BRICK_COLORS[r % len(BRICK_COLORS)])
                    p.setBrush(col); p.setPen(QPen(col.darker(130), 1))
                    p.drawRoundedRect(QRectF(x+1, y+1, bw-2, bh-2), 5, 5)

        # Paddle
        py = h - 40
        p.setBrush(QColor("#00d4ff"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(self.screen.pad_x, py, PAD_W, PAD_H), 7, 7)

        # Ball
        bx, by = self.screen.ball_x, self.screen.ball_y
        p.setBrush(QColor("#ffd60a"))
        p.drawEllipse(QRectF(bx-BALL_R, by-BALL_R, BALL_R*2, BALL_R*2))

        # Lives
        p.setFont(p.font())
        p.setPen(QColor("#f4f6ff"))
        from PyQt6.QtGui import QFont
        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p.drawText(QRectF(10, 8, 200, 24), Qt.AlignmentFlag.AlignLeft,
                   "❤️ " * self.screen.lives)

        if not self.screen.running and not self.screen.game_over:
            p.setPen(QColor(255, 255, 255, 180))
            p.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Move mouse to aim\nClick Start to launch!")


class BreakoutScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("breakout", "Breakout",
                         "Bounce the ball to smash all the bricks!",
                         "#00d4ff", storage, sounds, parent)
        self.pad_x = 200.0; self.ball_x = 250.0; self.ball_y = 300.0
        self.vx = 4.0; self.vy = -4.0
        self.bricks: list[list[bool]] = []
        self.lives = 3; self.score = 0; self.running = False; self.game_over = False

        top = QHBoxLayout(); top.setSpacing(12)
        self._info = QLabel("Move mouse to control paddle")
        self._info.setStyleSheet("color:#8899cc; font-size:13px;")
        top.addWidget(self._info, 1)
        self.start_btn = NeonButton("▶ Start", primary=True)
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self._start_or_restart)
        top.addWidget(self.start_btn)
        self.content_layout.addLayout(top)

        self.canvas = BreakoutCanvas(self)
        self.content_layout.addWidget(self.canvas, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "🏓", "title": "Welcome to Breakout!",
             "body": "A ball bounces around the screen. Use your paddle to keep it in play and smash all the bricks!"},
            {"emoji": "🖱️", "title": "Controls",
             "body": "Move your mouse left and right to move the paddle. You can also use the Left/Right arrow keys!"},
            {"emoji": "🧱", "title": "Break the Bricks",
             "body": "The ball bounces off bricks and destroys them. Each brick gives you points. Clear all bricks to win!"},
            {"emoji": "❤️", "title": "Lives",
             "body": "You have 3 lives. If the ball falls below your paddle, you lose a life. Lose all 3 and it's game over!"},
        ])

    def reset_game(self):
        self.bricks = [[True]*BRICK_COLS for _ in range(BRICK_ROWS)]
        self.lives = 3; self.score = 0; self.running = False; self.game_over = False
        self.timer.stop()
        self.start_btn.setText("▶ Start")
        self.start_btn.setEnabled(True)   # always re-enable
        self.set_score(0); self._reset_ball(); self.canvas.update()

    def _reset_ball(self):
        w = self.canvas.width() or 500
        h = self.canvas.height() or 400
        self.pad_x = w/2 - PAD_W/2
        self.ball_x = w/2; self.ball_y = h - 80
        self.vx = random.choice([-4.0, 4.0]); self.vy = -4.5

    def _start_or_restart(self):
        if self.game_over:
            self.reset_game(); return
        self.running = True
        self.timer.start(16)
        self.start_btn.setText("▶ Running")
        self.canvas.setFocus()

    def hideEvent(self, e):
        self.timer.stop(); super().hideEvent(e)

    def _tick(self):
        if not self.running: return
        w = self.canvas.width(); h = self.canvas.height()
        self.ball_x += self.vx; self.ball_y += self.vy

        # Wall bounces
        if self.ball_x - BALL_R <= 0 or self.ball_x + BALL_R >= w: self.vx *= -1
        if self.ball_y - BALL_R <= 0: self.vy *= -1

        # Paddle
        py = h - 40
        if (py - BALL_R <= self.ball_y <= py + PAD_H and
                self.pad_x <= self.ball_x <= self.pad_x + PAD_W):
            self.vy = -abs(self.vy)
            offset = (self.ball_x - (self.pad_x + PAD_W/2)) / (PAD_W/2)
            self.vx = offset * 6
            self.sounds.play("move")

        # Brick collision
        bw = (w - 20) / BRICK_COLS; bh = 22
        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                if not self.bricks[r][c]: continue
                bx = 10 + c*bw; by = 40 + r*(bh+4)
                if (bx <= self.ball_x <= bx+bw and by <= self.ball_y <= by+bh):
                    self.bricks[r][c] = False
                    self.vy *= -1
                    self.score += 10
                    self.set_score(self.score)
                    self.sounds.play("score")

        # Ball lost
        if self.ball_y > h + 20:
            self.lives -= 1; self.sounds.play("lose")
            if self.lives <= 0:
                self.running = False; self.game_over = True; self.timer.stop()
                self.show_game_over("💔", "Game Over!", self.score, message="All lives lost!")
            else:
                self._reset_ball(); self.running = False; self.timer.stop()
                self.start_btn.setText("▶ Launch")

        # Win
        if all(not self.bricks[r][c] for r in range(BRICK_ROWS) for c in range(BRICK_COLS)):
            self.running = False; self.timer.stop()
            self.show_game_over("🏆", "All Bricks Cleared!", self.score, message="Amazing!")

        self.canvas.update()
