from __future__ import annotations
import random
from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

HOLES = 9
GAME_TIME = 30  # seconds


class MoleGrid(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(360, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _hole_rect(self, idx: int) -> QRectF:
        cols = 3; rows = 3
        cs = min(self.width()/cols, self.height()/rows)
        ox = (self.width()  - cs*cols) / 2
        oy = (self.height() - cs*rows) / 2
        r, c = divmod(idx, cols)
        pad = cs * 0.12
        return QRectF(ox+c*cs+pad, oy+r*cs+pad, cs-pad*2, cs-pad*2)

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        for i in range(HOLES):
            if self._hole_rect(i).contains(e.position()):
                self.screen.whack(i); return

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(20, 80, 30))

        for i in range(HOLES):
            r = self._hole_rect(i)
            # Hole
            p.setBrush(QColor(10, 40, 15))
            p.setPen(QColor(5, 25, 10))
            p.drawEllipse(r)

            state = self.screen.holes[i]  # 0=empty 1=mole 2=whacked
            if state == 1:
                # Mole
                p.setFont(QFont("Segoe UI", max(12, int(r.width()*0.38))))
                p.setPen(QColor(255, 255, 255))
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, "🐹")
            elif state == 2:
                # Whacked
                p.setFont(QFont("Segoe UI", max(12, int(r.width()*0.38))))
                p.setPen(QColor(255, 200, 0))
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, "💥")


class WhackAMoleScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("whack_a_mole", "Whack-a-Mole",
                         "Whack the moles before they disappear!",
                         "#22d98a", storage, sounds, parent)
        self.holes = [0] * HOLES
        self.score = 0; self.time_left = GAME_TIME; self.running = False

        top = QHBoxLayout(); top.setSpacing(12)
        self._time_lbl = QLabel(f"⏱️ {GAME_TIME}s")
        self._time_lbl.setStyleSheet("font-size:18px; font-weight:800; color:#ffd60a;")
        top.addWidget(self._time_lbl)
        top.addStretch(1)
        self.start_btn = NeonButton("▶ Start", primary=True)
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self._start)
        top.addWidget(self.start_btn)
        self.content_layout.addLayout(top)

        self.grid_w = MoleGrid(self)
        self.content_layout.addWidget(self.grid_w, 1)

        self._mole_timer  = QTimer(self); self._mole_timer.timeout.connect(self._pop_mole)
        self._clear_timer = QTimer(self); self._clear_timer.timeout.connect(self._clear_moles)
        self._game_timer  = QTimer(self); self._game_timer.timeout.connect(self._tick_time)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "🐹", "title": "Welcome to Whack-a-Mole!",
             "body": "Moles will pop up from the holes. Click them as fast as you can before they disappear!"},
            {"emoji": "👆", "title": "How to Play",
             "body": "Click on a mole when you see it pop up. Each successful whack earns you 10 points!"},
            {"emoji": "⏱️", "title": "Time Limit",
             "body": f"You have {GAME_TIME} seconds. The moles get faster as time goes on — stay sharp!"},
            {"emoji": "🏆", "title": "High Score",
             "body": "Try to whack as many moles as possible before time runs out. Beat your best score!"},
        ])

    def reset_game(self):
        self.holes = [0]*HOLES; self.score = 0
        self.time_left = GAME_TIME; self.running = False
        self._mole_timer.stop(); self._clear_timer.stop(); self._game_timer.stop()
        self.set_score(0)
        self._time_lbl.setText(f"⏱️ {GAME_TIME}s")
        self.start_btn.setText("▶ Start")
        self.start_btn.setEnabled(True)   # always re-enable on reset
        self.grid_w.update()

    def _start(self):
        # Full reset then start
        self.holes = [0]*HOLES
        self.score = 0
        self.time_left = GAME_TIME
        self.running = True
        self.set_score(0)
        self._time_lbl.setText(f"⏱️ {GAME_TIME}s")
        self._mole_timer.stop(); self._clear_timer.stop(); self._game_timer.stop()
        self._mole_timer.start(800)
        self._clear_timer.start(1200)
        self._game_timer.start(1000)
        self.start_btn.setText("⏳ Running...")
        self.start_btn.setEnabled(False)
        self.grid_w.update()

    def _pop_mole(self):
        if not self.running: return
        empty = [i for i in range(HOLES) if self.holes[i] == 0]
        if empty:
            self.holes[random.choice(empty)] = 1
        self.grid_w.update()
        # Speed up over time
        elapsed = GAME_TIME - self.time_left
        speed = max(400, 800 - elapsed * 12)
        self._mole_timer.setInterval(speed)

    def _clear_moles(self):
        for i in range(HOLES):
            if self.holes[i] == 1: self.holes[i] = 0
            elif self.holes[i] == 2: self.holes[i] = 0
        self.grid_w.update()

    def _tick_time(self):
        self.time_left -= 1
        self._time_lbl.setText(f"⏱️ {self.time_left}s")
        if self.time_left <= 0:
            self.running = False
            self._mole_timer.stop(); self._clear_timer.stop(); self._game_timer.stop()
            self.holes = [0]*HOLES; self.grid_w.update()
            # Re-enable start button so user can play again
            self.start_btn.setText("▶ Play Again")
            self.start_btn.setEnabled(True)
            self.show_game_over("🐹", "Time's Up!", self.score,
                                f"You whacked {self.score//10} moles!")

    def whack(self, idx: int):
        if not self.running or self.holes[idx] != 1: return
        self.holes[idx] = 2
        self.score += 10; self.set_score(self.score)
        self.sounds.play("score")
        self.grid_w.update()
        QTimer.singleShot(200, lambda: self._clear_whack(idx))

    def _clear_whack(self, idx):
        if self.holes[idx] == 2: self.holes[idx] = 0
        self.grid_w.update()

    def hideEvent(self, e):
        self._mole_timer.stop(); self._clear_timer.stop(); self._game_timer.stop()
        super().hideEvent(e)
