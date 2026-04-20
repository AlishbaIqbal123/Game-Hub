from __future__ import annotations

import random

import pygame
from PyQt6.QtCore import QRect, QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import GameCanvas, NeonButton


# Colours cycling through the stack
BLOCK_COLORS = ["#00d4ff", "#4488ff", "#a855f7", "#ff4da6", "#22d98a", "#ffd60a", "#ff8c00"]


class TowerCanvas(GameCanvas):
    def __init__(self, screen: "TowerStackingScreen", parent=None) -> None:
        super().__init__(parent)
        self.screen = screen
        self.setMinimumSize(400, 400)

    # ── Coordinate helpers ────────────────────────────────────────────────────
    def _canvas_rect(self):
        """Usable drawing area inside the canvas."""
        return self.contentsRect().adjusted(16, 16, -16, -16)

    def cx(self) -> int:
        """Horizontal centre of the usable area."""
        return self._canvas_rect().center().x()

    def bottom(self) -> int:
        """Y coordinate of the bottom of the usable area."""
        return self._canvas_rect().bottom()

    def usable_width(self) -> int:
        return self._canvas_rect().width()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        area = self._canvas_rect()
        p.fillRect(area, QColor(8, 14, 28, 230))

        # Camera scroll logic: if stack is high, shift down
        offset_y = 0
        if self.screen.stack:
            top_y = self.screen.stack[-1].y
            mid_y = area.height() // 2
            if top_y < mid_y:
                offset_y = mid_y - top_y

        # Draw stacked blocks with offset
        for i, block in enumerate(self.screen.stack):
            color = QColor(BLOCK_COLORS[i % len(BLOCK_COLORS)])
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(block.x, block.y + offset_y, block.width, block.height, 5, 5)

        # Draw moving active block with offset
        active = self.screen.active_block
        if active:
            p.setBrush(QColor("#ffd60a"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(active.x, active.y + offset_y, active.width, active.height, 5, 5)

        # Game over message
        if self.screen.game_over:
            p.setPen(QColor(255, 255, 255, 220))
            p.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            p.drawText(area, Qt.AlignmentFlag.AlignCenter, "Game Over!\nPress Start to play again 🎮")


class TowerStackingScreen(BaseGameScreen):
    BLOCK_HEIGHT = 22
    BASE_WIDTH   = 200   # starting block width (scales with canvas)

    def __init__(self, storage, sounds, parent=None) -> None:
        super().__init__(
            "tower_stacking",
            "Tower Stacking",
            "Stack moving platforms, keep the overlap, and climb for a higher score.",
            "#ff4da6",
            storage,
            sounds,
            parent,
        )
        self.game_over = False

        # ── Instructions ──────────────────────────────────────────────────────
        info = QLabel("⬇️  Watch the yellow block move — press  Stack  when it lines up!")
        info.setObjectName("MutedLabel")
        info.setWordWrap(True)
        self.content_layout.addWidget(info)

        # ── Canvas ────────────────────────────────────────────────────────────
        from PyQt6.QtWidgets import QScrollArea, QFrame
        self.canvas = TowerCanvas(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setWidget(self.canvas)
        self.content_layout.addWidget(scroll, 1)

        # ── Bottom controls ───────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)

        self.start_btn = NeonButton("▶  Start Game", primary=True)
        self.start_btn.setFixedHeight(48)
        self.start_btn.clicked.connect(self._start_or_stack)
        ctrl.addWidget(self.start_btn)

        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("MutedLabel")
        ctrl.addWidget(self._status_lbl, 1)
        self.content_layout.addLayout(ctrl)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self._initialised = False
        self.reset_game()

        self.show_tutorial([
            {"emoji": "🏗️", "title": "Welcome to Tower Stacking!",
             "body": "A yellow block slides back and forth. Your job is to drop it on top of the tower at just the right moment!"},
            {"emoji": "⬇️", "title": "How to Stack",
             "body": "Press the Stack button (or click it) when the yellow block is lined up over the tower below. The overlapping part becomes the new layer!"},
            {"emoji": "📏", "title": "Keep It Aligned",
             "body": "The more overlap you get, the wider the next block stays. Miss badly and the game ends!"},
            {"emoji": "⚡", "title": "It Gets Faster!",
             "body": "Each layer you add makes the block move a little faster. How high can you build your tower?"},
        ])

    # ── Geometry ──────────────────────────────────────────────────────────────
    def _base_y(self) -> int:
        """Y position of the first (bottom) block."""
        return self.canvas.bottom() - self.BLOCK_HEIGHT - 10

    def _initial_block_width(self) -> int:
        return min(self.BASE_WIDTH, max(80, self.canvas.usable_width() // 4))

    def _centred_rect(self, width: int, y: int) -> pygame.Rect:
        """A pygame.Rect centred horizontally in the canvas."""
        x = self.canvas.cx() - width // 2
        return pygame.Rect(x, y, width, self.BLOCK_HEIGHT)

    def _random_start_x(self, width: int) -> int:
        margin = 20
        lo = self.canvas._canvas_rect().left() + margin
        hi = max(lo + 1, self.canvas._canvas_rect().right() - width - margin)
        return random.randint(lo, hi)

    # ── Game control ──────────────────────────────────────────────────────────
    def reset_game(self) -> None:
        self.timer.stop()
        self.game_over = False
        self.score_value = 0
        self.set_score(0)
        self._status_lbl.setText("")
        self.start_btn.setText("▶  Start Game")
        self.start_btn.setEnabled(True)   # always re-enable
        self.stack: list[pygame.Rect] = []
        self.active_block: pygame.Rect | None = None
        self.velocity = 6
        self._initialised = False
        self.canvas.update()

    def _init_blocks(self) -> None:
        """Called on first tick so canvas dimensions are known."""
        w = self._initial_block_width()
        base = self._centred_rect(w, self._base_y())
        self.stack = [base]
        self.active_block = pygame.Rect(
            self._random_start_x(w),
            base.y - self.BLOCK_HEIGHT - 8,
            w,
            self.BLOCK_HEIGHT,
        )
        self._initialised = True

    def _start_or_stack(self) -> None:
        if self.game_over or not self._initialised:
            self.reset_game()
            self.timer.start(20)
            self.start_btn.setText("⬇️  Stack!")
            return
        self.stack_block()

    def hideEvent(self, event) -> None:  # noqa: N802
        self.timer.stop()
        super().hideEvent(event)

    # ── Game loop ─────────────────────────────────────────────────────────────
    def tick(self) -> None:
        if not self._initialised:
            self._init_blocks()

        if not self.active_block or self.game_over:
            return

        area = self.canvas._canvas_rect()
        self.active_block.x += self.velocity
        if self.active_block.right >= area.right() - 4:
            self.velocity = -abs(self.velocity)
        elif self.active_block.left <= area.left() + 4:
            self.velocity = abs(self.velocity)
        self.canvas.update()

    def stack_block(self) -> None:
        if not self.active_block or self.game_over:
            return

        base = self.stack[-1]
        ol   = max(base.left, self.active_block.left)
        orr  = min(base.right, self.active_block.right)
        overlap = orr - ol

        if overlap <= 6:
            # Missed — game over
            self.timer.stop()
            self.game_over = True
            self.sounds.play("lose")
            self._status_lbl.setText("😬 Missed! Press Start to try again.")
            self.start_btn.setText("🔄  Try Again")
            self.active_block = None
            self.canvas.update()
            return

        self.sounds.play("score")
        new_y     = base.y - self.BLOCK_HEIGHT - 4
        new_block = pygame.Rect(ol, new_y, overlap, self.BLOCK_HEIGHT)
        self.stack.append(new_block)

        # Speed up slightly each layer
        self.velocity = int(self.velocity * 1.06) or self.velocity
        if abs(self.velocity) > 22:
            self.velocity = 22 * (1 if self.velocity > 0 else -1)

        # New active block starts from a random side
        start_x = self._random_start_x(overlap)
        self.active_block = pygame.Rect(
            start_x,
            new_y - self.BLOCK_HEIGHT - 4,
            overlap,
            self.BLOCK_HEIGHT,
        )

        self.score_value += 10
        self.set_score(self.score_value)
        self._status_lbl.setText(f"🎯 Layer {len(self.stack)}  —  keep going!")
        self.canvas.update()
