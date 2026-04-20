from __future__ import annotations
import random, time
from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

ROUNDS = 5


class ReactionCanvas(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.screen.on_click()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        state = self.screen.state  # 'wait' 'ready' 'go' 'result' 'done'

        if state == 'wait':
            p.fillRect(self.rect(), QColor(20, 30, 60))
            p.setPen(QColor(100, 130, 200))
            p.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Click anywhere\nto start!")
        elif state == 'ready':
            p.fillRect(self.rect(), QColor(180, 30, 30))
            p.setPen(QColor(255, 200, 200))
            p.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "⏳  Wait for green...")
        elif state == 'go':
            p.fillRect(self.rect(), QColor(20, 180, 80))
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "CLICK NOW! ⚡")
        elif state == 'result':
            p.fillRect(self.rect(), QColor(20, 30, 60))
            p.setPen(QColor(0, 212, 255))
            p.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
            ms = self.screen.last_ms
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       f"⚡ {ms} ms\n\nClick for next round")
        elif state == 'early':
            p.fillRect(self.rect(), QColor(180, 100, 0))
            p.setPen(QColor(255, 220, 100))
            p.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Too early! 😅\nClick to try again")


class ReactionTimeScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("reaction_time", "Reaction Time",
                         "Click as fast as you can when the screen turns green!",
                         "#ffd60a", storage, sounds, parent)
        self.state = 'wait'
        self.results: list[int] = []
        self.last_ms = 0
        self._start_time = 0.0
        self._wait_timer = QTimer(self); self._wait_timer.setSingleShot(True)
        self._wait_timer.timeout.connect(self._go)

        top = QHBoxLayout(); top.setSpacing(12)
        self._round_lbl = QLabel(f"Round 0 / {ROUNDS}")
        self._round_lbl.setStyleSheet("font-size:16px; font-weight:700;")
        top.addWidget(self._round_lbl, 1)
        self._avg_lbl = QLabel("Avg: —")
        self._avg_lbl.setStyleSheet("color:#8899cc; font-size:14px;")
        top.addWidget(self._avg_lbl)
        new_btn = NeonButton("🔄 Reset", primary=True)
        new_btn.setFixedHeight(40); new_btn.clicked.connect(self.reset_game)
        top.addWidget(new_btn)
        self.content_layout.addLayout(top)

        self.canvas = ReactionCanvas(self)
        self.content_layout.addWidget(self.canvas, 1)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "⚡", "title": "Welcome to Reaction Time!",
             "body": "This game tests how fast your reflexes are. Get ready to click as fast as possible!"},
            {"emoji": "🔴", "title": "Wait for Green",
             "body": "The screen will turn RED — wait. When it turns GREEN, click as fast as you can!"},
            {"emoji": "⏱️", "title": "Your Time",
             "body": "Your reaction time is measured in milliseconds. Under 200ms is excellent! Under 300ms is good."},
            {"emoji": "🏆", "title": "5 Rounds",
             "body": f"You'll do {ROUNDS} rounds. Your average reaction time is your final score. Lower is better!"},
        ])

    def reset_game(self):
        self._wait_timer.stop()
        self.state = 'wait'; self.results = []; self.last_ms = 0
        self.set_score(0)
        self._round_lbl.setText(f"Round 0 / {ROUNDS}")
        self._avg_lbl.setText("Avg: —")
        self.canvas.update()

    def on_click(self):
        if self.state == 'wait':
            self._begin_round()
        elif self.state == 'ready':
            self.state = 'early'; self._wait_timer.stop()
            self.sounds.play("lose"); self.canvas.update()
        elif self.state == 'go':
            ms = int((time.perf_counter() - self._start_time) * 1000)
            self.last_ms = ms; self.results.append(ms)
            self.state = 'result'; self.sounds.play("success")
            avg = sum(self.results) // len(self.results)
            self._avg_lbl.setText(f"Avg: {avg} ms")
            self._round_lbl.setText(f"Round {len(self.results)} / {ROUNDS}")
            score = max(0, 1000 - avg)
            self.set_score(score)
            if len(self.results) >= ROUNDS:
                self.state = 'done'
                self.show_game_over("⚡", f"Average: {avg} ms", score,
                                    message=self._rating(avg))
            self.canvas.update()
        elif self.state in ('result', 'early'):
            self._begin_round()

    def _begin_round(self):
        self.state = 'ready'
        delay = random.randint(1500, 4000)
        self._wait_timer.start(delay)
        self.canvas.update()

    def _go(self):
        self.state = 'go'
        self._start_time = time.perf_counter()
        self.canvas.update()

    @staticmethod
    def _rating(avg: int) -> str:
        if avg < 180: return "🚀 Superhuman reflexes!"
        if avg < 220: return "⚡ Excellent reaction time!"
        if avg < 280: return "👍 Good reflexes!"
        if avg < 350: return "😊 Average — keep practising!"
        return "🐢 Keep practising to improve!"
