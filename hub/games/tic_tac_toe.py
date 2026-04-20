from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton


class TicTacToeScreen(BaseGameScreen):
    WIN_LINES = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )

    def __init__(self, storage, sounds, parent=None) -> None:
        super().__init__(
            "tic_tac_toe",
            "Tic Tac Toe",
            "Play against a simple AI or a local friend inside a polished neon board.",
            "#28f2ff",
            storage,
            sounds,
            parent,
        )
        self.board = [""] * 9
        self.current = "X"
        self.running_score = 0
        self.mode = "AI"

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Mode"))
        self.mode_box = QComboBox()
        self.mode_box.addItems(["AI", "Two Players"])
        self.mode_box.currentTextChanged.connect(self.change_mode)
        controls.addWidget(self.mode_box)
        reset = NeonButton("New Round")
        reset.clicked.connect(self.reset_game)
        controls.addWidget(reset)
        controls.addStretch(1)
        self.content_layout.addLayout(controls)

        self.status_label = QLabel("Player X to move")
        self.status_label.setObjectName("MutedLabel")
        self.content_layout.addWidget(self.status_label)

        board_shell = QWidget()
        board = QGridLayout(board_shell)
        board.setSpacing(10)
        self.buttons = []
        for index in range(9):
            button = QPushButton("")
            button.setFixedSize(120, 120)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(
                "QPushButton { background: rgba(255,255,255,0.08); font-size: 32px; font-weight: 700; border-radius: 22px; }"
                "QPushButton:hover { background: rgba(255,255,255,0.14); }"
            )
            button.clicked.connect(lambda _=False, i=index: self.play_move(i))
            board.addWidget(button, index // 3, index % 3)
            self.buttons.append(button)
        self.content_layout.addWidget(board_shell, alignment=Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch(1)

        self.show_tutorial([
            {"emoji": "✕", "title": "Welcome to Tic Tac Toe!",
             "body": "Two players take turns placing their mark on a 3×3 grid. You are X, the computer is O."},
            {"emoji": "🎯", "title": "How to Win",
             "body": "Get three of your marks in a row — across, down, or diagonally — before your opponent does!"},
            {"emoji": "🤖", "title": "Playing vs AI",
             "body": "In AI mode the computer plays as O and tries to block you. Switch to Two Players to play with a friend on the same screen."},
            {"emoji": "🏆", "title": "Scoring",
             "body": "Win a round as X to earn 10 points. Win as O to earn 6 points. Your total score is saved automatically!"},
        ])

    def change_mode(self, mode: str) -> None:
        self.mode = mode
        self.reset_game()

    def reset_game(self) -> None:
        self.board = [""] * 9
        self.current = "X"
        self.status_label.setText("Player X to move")
        for button in self.buttons:
            button.setText("")
            button.setEnabled(True)

    def play_move(self, index: int) -> None:
        if self.board[index]:
            return
        self.board[index] = self.current
        self.buttons[index].setText(self.current)
        self.sounds.play("move")

        winner = self.check_winner(self.board)
        if winner:
            self.end_round(f"{winner} wins!", 10 if winner == "X" else 6)
            return
        if "" not in self.board:
            self._check_draw()
            return

        self.current = "O" if self.current == "X" else "X"
        self.status_label.setText(f"Player {self.current} to move")
        if self.mode == "AI" and self.current == "O":
            ai_index = self.best_move()
            if ai_index is not None:
                self.play_move(ai_index)

    def end_round(self, message: str, points: int) -> None:
        self.status_label.setText(message)
        self.running_score += points
        self.set_score(self.running_score)
        self.sounds.play("success")
        for button in self.buttons:
            button.setEnabled(False)
        emoji = "🎉" if "X wins" in message else ("😅" if "O wins" in message else "🤝")
        self.show_game_over(emoji, message, self.running_score,
                            message="Press Play Again for a new round!")

    def _check_draw(self) -> bool:
        if "" not in self.board and not self.check_winner(self.board):
            self.status_label.setText("It's a draw!")
            self.sounds.play("click")
            for button in self.buttons:
                button.setEnabled(False)
            self.show_game_over("🤝", "It's a Draw!", self.running_score,
                                message="So close! Try again for the win.")
            return True
        return False

    def check_winner(self, board: list[str]) -> str | None:
        for a, b, c in self.WIN_LINES:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]
        return None

    def best_move(self) -> int | None:
        for symbol in ("O", "X"):
            for index in range(9):
                if self.board[index]:
                    continue
                self.board[index] = symbol
                if self.check_winner(self.board) == symbol:
                    self.board[index] = ""
                    return index
                self.board[index] = ""
        if not self.board[4]:
            return 4
        for choice in (0, 2, 6, 8, 1, 3, 5, 7):
            if not self.board[choice]:
                return choice
        return None
