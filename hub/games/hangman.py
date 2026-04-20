from __future__ import annotations
import random
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton
from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY


WORDS = [
    ("PYTHON","🐍"),  ("ARCADE","🕹️"), ("PUZZLE","🧩"),  ("DRAGON","🐉"),
    ("CASTLE","🏰"),  ("ROCKET","🚀"),  ("WIZARD","🧙"),  ("JUNGLE","🌴"),
    ("PIRATE","🏴"),  ("GALAXY","🌌"),  ("TROPHY","🏆"),  ("BRIDGE","🌉"),
    ("COOKIE","🍪"),  ("PLANET","🪐"),  ("KNIGHT","♞"),   ("FLOWER","🌸"),
    ("MONKEY","🐒"),  ("BUTTER","🧈"),  ("CANDLE","🕯️"),  ("DESERT","🏜️"),
    ("FOREST","🌲"),  ("GUITAR","🎸"),  ("HAMMER","🔨"),  ("ISLAND","🏝️"),
    ("JUNGLE","🌴"),  ("KITTEN","🐱"),  ("LEMON","🍋"),   ("MIRROR","🪞"),
    ("NEEDLE","🪡"),  ("ORANGE","🍊"),  ("PARROT","🦜"),  ("QUARTZ","💎"),
]
MAX_WRONG = 6

# ── Keyboard button style helpers ─────────────────────────────────────────────
def _btn_default() -> str:
    p = PALETTE
    return (
        f"QPushButton {{"
        f"  background: {p['surface_mid']};"
        f"  border: 1.5px solid {p['border']};"
        f"  border-radius: 12px;"
        f"  color: {p['text']};"
        f"  font-family: '{FONT_BODY}';"
        f"  font-size: 14px;"
        f"  font-weight: 700;"
        f"  padding: 0px;"
        f"}}"
        f"QPushButton:hover {{"
        f"  background: {p['primary']}1a;"
        f"  border-color: {p['primary']};"
        f"  color: {p['primary']};"
        f"}}"
        f"QPushButton:disabled {{"
        f"  background: {p['surface_low']};"
        f"  border-color: {p['border']};"
        f"  color: {p['muted']};"
        f"}}"
    )

def _btn_correct() -> str:
    p = PALETTE
    return (
        f"QPushButton {{"
        f"  background: {p['success']};"
        f"  border: none;"
        f"  border-radius: 12px;"
        f"  color: #ffffff;"
        f"  font-family: '{FONT_BODY}';"
        f"  font-size: 14px;"
        f"  font-weight: 700;"
        f"  padding: 0px;"
        f"}}"
    )

def _btn_wrong() -> str:
    p = PALETTE
    return (
        f"QPushButton {{"
        f"  background: {p['error_con']};"
        f"  border: 1.5px solid {p['error']};"
        f"  border-radius: 12px;"
        f"  color: {p['error']};"
        f"  font-family: '{FONT_BODY}';"
        f"  font-size: 14px;"
        f"  font-weight: 700;"
        f"  padding: 0px;"
        f"}}"
    )


# ── Gallows painter ───────────────────────────────────────────────────────────

class GallowsWidget(QWidget):
    def __init__(self, screen, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(220, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        wrong = self.screen.wrong

        # Gallows
        gpen = QPen(QColor(PALETTE["primary"]), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(gpen)
        p.drawLine(QPointF(w*0.1, h*0.9), QPointF(w*0.9, h*0.9))  # base
        p.drawLine(QPointF(w*0.2, h*0.9), QPointF(w*0.2, h*0.1))  # pole
        p.drawLine(QPointF(w*0.2, h*0.1), QPointF(w*0.7, h*0.1))  # beam
        p.drawLine(QPointF(w*0.7, h*0.1), QPointF(w*0.7, h*0.2))  # rope

        # Figure
        cx, cy = w*0.7, h*0.2; r = h * 0.08
        fpen = QPen(QColor(PALETTE["secondary"]), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(fpen)
        if wrong >= 1: p.drawEllipse(QPointF(cx, cy + r), r, r)
        if wrong >= 2: p.drawLine(QPointF(cx, cy+r*2), QPointF(cx, cy+r*5))
        if wrong >= 3: p.drawLine(QPointF(cx, cy+r*3), QPointF(cx-r*1.5, cy+r*4.5))
        if wrong >= 4: p.drawLine(QPointF(cx, cy+r*3), QPointF(cx+r*1.5, cy+r*4.5))
        if wrong >= 5: p.drawLine(QPointF(cx, cy+r*5), QPointF(cx-r*1.5, cy+r*7))
        if wrong >= 6: p.drawLine(QPointF(cx, cy+r*5), QPointF(cx+r*1.5, cy+r*7))


class HangmanScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None):
        super().__init__("hangman", "Hangman", "Unlock secret words to climb the leaderboard.", "#ff4da6", storage, sounds, parent)
        self.word = ""; self.emoji = ""; self.guessed = set(); self.wrong = 0

        top = QHBoxLayout(); top.setSpacing(20)
        self._word_lbl = QLabel()
        self._word_lbl.setStyleSheet(f"font-size:36px; font-weight:900; letter-spacing:10px; font-family:'{FONT_TITLE}';")
        top.addWidget(self._word_lbl, 1)

        self._wrong_lbl = QLabel()
        self._wrong_lbl.setStyleSheet(f"color:{PALETTE['error']}; font-size:14px; font-weight:800; font-family:'{FONT_BODY}';")
        top.addWidget(self._wrong_lbl)

        new_btn = NeonButton("RETRY", primary=True); new_btn.setFixedHeight(48); new_btn.clicked.connect(self.reset_game)
        top.addWidget(new_btn)
        self.content_layout.addLayout(top)

        body = QHBoxLayout(); body.setSpacing(32)
        self.gallows = GallowsWidget(self); body.addWidget(self.gallows, 1)

        right = QVBoxLayout(); right.setSpacing(16)
        self._hint_lbl = QLabel(); self._hint_lbl.setStyleSheet(f"color:{PALETTE['text_sec']}; font-size:16px; font-weight:700;")
        right.addWidget(self._hint_lbl)

        self._missed_lbl = QLabel(); self._missed_lbl.setStyleSheet(f"color:{PALETTE['error']}; font-size:13px; font-weight:700;")
        right.addWidget(self._missed_lbl)

        kb_frame = QFrame(); kb_frame.setObjectName("PanelCard")
        kl = QVBoxLayout(kb_frame); kl.setContentsMargins(20, 20, 20, 20); kl.setSpacing(12)
        kg = QGridLayout(); kg.setSpacing(8)
        self._key_btns = {}
        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            btn = QPushButton(ch); btn.setFixedSize(50, 50); btn.setStyleSheet(_btn_default())
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, c=ch: self.guess(c))
            self._key_btns[ch] = btn
            kg.addWidget(btn, i//9, i%9)
        kl.addLayout(kg); right.addWidget(kb_frame); body.addLayout(right, 2)
        self.content_layout.addLayout(body, 1)

        self.reset_game()
        self.show_tutorial([
            {"emoji": "🧠", "title": "Secret Words", "body": "Guess the letters of the hidden word before the gallows are complete!"},
            {"emoji": "⌨", "title": "Precision Input", "body": "Select letters from the terminal. Watch your accuracy!"},
            {"emoji": "🏆", "title": "Climb Higher", "body": "Fewer wrong guesses result in significantly higher score multipliers."},
        ])

    def reset_game(self):
        self.word, self.emoji = random.choice(WORDS)
        self.guessed = set(); self.wrong = 0
        for b in self._key_btns.values(): b.setEnabled(True); b.setStyleSheet(_btn_default())
        self.set_score(0); self._refresh()

    def _refresh(self):
        txt = " ".join([c if c in self.guessed else "_" for c in self.word])
        self._word_lbl.setText(txt)
        self._wrong_lbl.setText(f"STRIKES: {self.wrong}/{MAX_WRONG}")
        missed = [c for c in sorted(self.guessed) if c not in self.word]
        self._missed_lbl.setText("MISSED: " + " ".join(missed) if missed else "")
        self._hint_lbl.setText(f"Hint: {self.emoji}  ({len(self.word)} chars)")
        self.gallows.update()

    def guess(self, ch: str):
        if ch in self.guessed: return
        self.guessed.add(ch)
        btn = self._key_btns[ch]; btn.setEnabled(False)
        if ch in self.word:
            self.sounds.play("success"); btn.setStyleSheet(_btn_correct())
            if all(c in self.guessed for c in self.word):
                s = max(10, 100 - self.wrong * 15)
                self.set_score(s); self.show_game_over("🎉", "MISSION SUCCESS", s, 0, f"The word was {self.word}!")
        else:
            self.wrong += 1; self.sounds.play("click"); btn.setStyleSheet(_btn_wrong())
            if self.wrong >= MAX_WRONG: self.show_game_over("💀", "MISSION FAILED", 0, 0, f"The word was {self.word}!")
        self._refresh()
