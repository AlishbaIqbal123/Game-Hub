from __future__ import annotations

import random

import pygame
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QLabel

from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import GameCanvas, NeonButton


class SnakeBoard(GameCanvas):
    def __init__(self, screen, parent=None) -> None:
        super().__init__(parent)
        self.screen = screen
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.contentsRect().adjusted(18, 18, -18, -18)
        size = min(rect.width(), rect.height())
        grid_rect = rect
        cell = size / self.screen.grid_size

        painter.fillRect(grid_rect, QColor(9, 18, 36, 220))
        for row in range(self.screen.grid_size):
            for col in range(self.screen.grid_size):
                if (row + col) % 2 == 0:
                    painter.fillRect(int(grid_rect.left() + col * cell), int(grid_rect.top() + row * cell), int(cell), int(cell), QColor(18, 35, 63, 140))

        food_rect = self.screen.cell_rect(self.screen.food, grid_rect, cell)
        painter.setBrush(QColor("#ff5cb8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(*food_rect)

        for index, segment in enumerate(self.screen.snake):
            color = QColor("#48f1a9" if index else "#28f2ff")
            painter.setBrush(color)
            painter.drawRoundedRect(*self.screen.cell_rect(segment, grid_rect, cell), 8, 8)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        directions = {
            Qt.Key.Key_Up: pygame.Vector2(0, -1),
            Qt.Key.Key_Down: pygame.Vector2(0, 1),
            Qt.Key.Key_Left: pygame.Vector2(-1, 0),
            Qt.Key.Key_Right: pygame.Vector2(1, 0),
        }
        if event.key() in directions:
            self.screen.change_direction(directions[event.key()])
        super().keyPressEvent(event)


class SnakeScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None) -> None:
        super().__init__(
            "snake",
            "Snake",
            "Steer with arrow keys, chase fruit, and keep the run alive.",
            "#48f1a9",
            storage,
            sounds,
            parent,
        )
        self.grid_size = 18
        self.direction = pygame.Vector2(1, 0)
        self.pending_direction = pygame.Vector2(1, 0)
        self.score_value = 0

        controls = QLabel("Controls: Arrow keys move the snake. Press Start to begin.")
        controls.setObjectName("MutedLabel")
        self.content_layout.addWidget(controls)

        self.board = SnakeBoard(self)
        self.content_layout.addWidget(self.board, 1)

        start = NeonButton("Start Run", primary=True)
        start.clicked.connect(self.start_game)
        self.content_layout.addWidget(start, alignment=Qt.AlignmentFlag.AlignLeft)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.reset_game()

        self.show_tutorial([
            {"emoji": "🐍", "title": "Welcome to Snake!",
             "body": "You control a snake that moves around the board. Your goal is to eat as much food as possible!"},
            {"emoji": "⬆️", "title": "Controls",
             "body": "Use the Arrow Keys on your keyboard to change direction — Up, Down, Left, Right. The snake keeps moving on its own!"},
            {"emoji": "🍎", "title": "Eat the Food",
             "body": "The pink dot is food. Steer your snake to eat it and grow longer. Each food gives you 5 points!"},
            {"emoji": "💀", "title": "Don't Crash!",
             "body": "If you hit a wall or your own tail, the game ends. The longer you survive, the higher your score!"},
        ])

    def reset_game(self) -> None:
        center = self.grid_size // 2
        self.snake = [pygame.Vector2(center, center), pygame.Vector2(center - 1, center), pygame.Vector2(center - 2, center)]
        self.direction = pygame.Vector2(1, 0)
        self.pending_direction = pygame.Vector2(1, 0)
        self.food = self.random_food()
        self.score_value = 0
        self.set_score(0)
        self.timer.stop()
        self.board.update()
        self.board.setFocus()
        self.setFocus()

    def hideEvent(self, event) -> None:  # noqa: N802
        """Stop the game loop when navigating away so it doesn't run in the background."""
        self.timer.stop()
        super().hideEvent(event)

    def start_game(self) -> None:
        self.timer.start(120)
        self.board.setFocus()

    def change_direction(self, vector) -> None:
        if len(self.snake) > 1 and vector + self.direction == pygame.Vector2(0, 0):
            return
        self.pending_direction = vector

    def tick(self) -> None:
        self.direction = self.pending_direction
        new_head = self.snake[0] + self.direction

        if (
            new_head.x < 0
            or new_head.y < 0
            or new_head.x >= self.grid_size
            or new_head.y >= self.grid_size
            or any(segment == new_head for segment in self.snake)
        ):
            self.timer.stop()
            self.sounds.play("lose")
            self.show_game_over(
                "💀", "Game Over!",
                self.score_value,
                f"You scored {self.score_value} points! Press Play Again to try to beat it."
            )
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score_value += 5
            self.set_score(self.score_value)
            self.food = self.random_food()
            self.sounds.play("score")
        else:
            self.snake.pop()

        self.board.update()

    def random_food(self):
        while True:
            candidate = pygame.Vector2(random.randrange(self.grid_size), random.randrange(self.grid_size))
            if all(candidate != segment for segment in self.snake):
                return candidate

    def cell_rect(self, vector, grid_rect, cell):
        return (
            int(grid_rect.left() + vector.x * cell) + 2,
            int(grid_rect.top() + vector.y * cell) + 2,
            int(cell) - 4,
            int(cell) - 4,
        )
