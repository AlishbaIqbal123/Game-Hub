from __future__ import annotations

import random

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton


class Puzzle2048Screen(BaseGameScreen):
    # (background, text_color)
    COLORS: dict[int, tuple[str, str]] = {
        0:    ("rgba(255,255,255,0.06)", "#f5f8ff"),
        2:    ("#1f375f",  "#f5f8ff"),
        4:    ("#244f75",  "#f5f8ff"),
        8:    ("#2d8a7d",  "#f5f8ff"),
        16:   ("#4c8dff",  "#06111d"),
        32:   ("#7b63ff",  "#f5f8ff"),
        64:   ("#9d4dff",  "#f5f8ff"),
        128:  ("#c45cff",  "#f5f8ff"),
        256:  ("#ff5cb8",  "#f5f8ff"),
        512:  ("#ffd166",  "#06111d"),
        1024: ("#ff9f43",  "#06111d"),
        2048: ("#48f1a9",  "#06111d"),
    }

    def __init__(self, storage, sounds, parent=None) -> None:
        super().__init__(
            "puzzle_2048",
            "2048 Puzzle",
            "Use arrow keys to combine tiles and reach the 2048 tile!",
            "#ffd166",
            storage,
            sounds,
            parent,
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.score_value = 0
        self._game_ended = False

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)
        hint = QLabel("⬆️⬇️⬅️➡️  Use arrow keys to slide tiles")
        hint.setObjectName("MutedLabel")
        ctrl.addWidget(hint, 1)
        new_btn = NeonButton("🔄  New Game", primary=True)
        new_btn.setFixedHeight(40)
        new_btn.clicked.connect(self.reset_game)
        ctrl.addWidget(new_btn)
        self.content_layout.addLayout(ctrl)

        # Grid
        self.cells: list[list[QLabel]] = []
        shell = QWidget()
        grid = QGridLayout(shell)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        for row in range(4):
            row_cells = []
            for col in range(4):
                lbl = QLabel("")
                lbl.setFixedSize(110, 110)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("border-radius: 18px; font-size: 28px; font-weight: 800;")
                grid.addWidget(lbl, row, col)
                row_cells.append(lbl)
            self.cells.append(row_cells)

        self.content_layout.addWidget(shell, 1, Qt.AlignmentFlag.AlignCenter)

        self.reset_game()

        self.show_tutorial([
            {"emoji": "🔢", "title": "Welcome to 2048!",
             "body": "The board has numbered tiles. Slide them with arrow keys to combine matching numbers!"},
            {"emoji": "⬆️", "title": "How to Play",
             "body": "Press any arrow key — all tiles slide that way. Two tiles with the same number merge into one bigger tile!"},
            {"emoji": "🎯", "title": "Goal",
             "body": "Keep merging tiles to reach the 2048 tile. Every merge adds to your score!"},
            {"emoji": "💡", "title": "Strategy Tip",
             "body": "Try to keep your biggest tile in a corner and build a chain of decreasing numbers next to it. Good luck!"},
        ])

    def reset_game(self) -> None:
        self.grid = [[0] * 4 for _ in range(4)]
        self.score_value = 0
        self._game_ended = False
        self.spawn()
        self.spawn()
        self._refresh()
        self.setFocus()

    def spawn(self) -> None:
        empty = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 4 if random.random() > 0.82 else 2

    def _refresh(self) -> None:
        self.set_score(self.score_value)
        for row in range(4):
            for col in range(4):
                v = self.grid[row][col]
                lbl = self.cells[row][col]
                lbl.setText("" if v == 0 else str(v))
                bg, fg = self.COLORS.get(v, ("#ff9f43", "#06111d"))
                lbl.setStyleSheet(
                    f"background:{bg}; border-radius:18px;"
                    f" font-size:28px; font-weight:800; color:{fg};"
                )

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if self._game_ended:
            super().keyPressEvent(event)
            return
        moves = {
            Qt.Key.Key_Left:  lambda: self._move(False),
            Qt.Key.Key_Right: lambda: self._move(True),
            Qt.Key.Key_Up:    lambda: self._move(False, vertical=True),
            Qt.Key.Key_Down:  lambda: self._move(True,  vertical=True),
        }
        action = moves.get(event.key())
        if action:
            changed = action()
            if changed:
                self.spawn()
                self._refresh()
                self.sounds.play("move")
                self._check_end()
        super().keyPressEvent(event)

    def _check_end(self) -> None:
        # Win
        if any(self.grid[r][c] == 2048 for r in range(4) for c in range(4)):
            self._game_ended = True
            self.sounds.play("success")
            self.show_game_over("🏆", "You reached 2048!", self.score_value,
                                "Amazing! Keep going for an even higher score!")
            return
        # Lose — no moves left
        if not self._has_moves():
            self._game_ended = True
            self.sounds.play("lose")
            self.show_game_over("😢", "No More Moves!", self.score_value,
                                "The board is full. Try again!")

    def _has_moves(self) -> bool:
        for r in range(4):
            for c in range(4):
                if self.grid[r][c] == 0:
                    return True
                if c + 1 < 4 and self.grid[r][c] == self.grid[r][c+1]:
                    return True
                if r + 1 < 4 and self.grid[r][c] == self.grid[r+1][c]:
                    return True
        return False

    def _move(self, reverse: bool, vertical: bool = False) -> bool:
        changed = False
        g = list(map(list, zip(*self.grid))) if vertical else [row[:] for row in self.grid]
        new_grid = []
        for row in g:
            orig = row[:]
            if reverse:
                row = list(reversed(row))
            compact = [v for v in row if v]
            merged: list[int] = []
            skip = False
            for i, v in enumerate(compact):
                if skip:
                    skip = False
                    continue
                if i + 1 < len(compact) and compact[i+1] == v:
                    mv = v * 2
                    merged.append(mv)
                    self.score_value += mv
                    skip = True
                else:
                    merged.append(v)
            merged += [0] * (4 - len(merged))
            if reverse:
                merged.reverse()
            new_grid.append(merged)
            if merged != orig:
                changed = True
        if vertical:
            self.grid = [list(row) for row in zip(*new_grid)]
        else:
            self.grid = new_grid
        return changed
