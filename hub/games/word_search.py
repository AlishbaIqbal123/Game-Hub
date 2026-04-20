from __future__ import annotations

import random
import string
from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from hub.ui.base_game_screen import BaseGameScreen
from hub.ui.components import NeonButton

# ── Word bank — 6 random words chosen each game ───────────────────────────────
_ALL_WORDS = [
    ("SNAKE",  "🐍", "#2ECC71"), ("LUDO",    "🎲", "#E91E8C"),
    ("PUZZLE", "🧩", "#9B59B6"), ("TOWER",   "🏗",  "#F1C40F"),
    ("GAME",   "🎮", "#00BCD4"), ("SCORE",   "⭐", "#FF5722"),
    ("KING",   "👑", "#FFD700"), ("QUEEN",   "♛",  "#FF69B4"),
    ("MAGIC",  "✨", "#8A2BE2"), ("BRAVE",   "🦁", "#FF8C00"),
    ("CLOUD",  "☁",  "#87CEEB"), ("FLAME",   "🔥", "#FF4500"),
    ("STORM",  "⛈",  "#4169E1"), ("OCEAN",   "🌊", "#1E90FF"),
    ("TIGER",  "🐯", "#FF6347"), ("EAGLE",   "🦅", "#8B4513"),
    ("SWORD",  "⚔",  "#C0C0C0"), ("ARROW",   "🏹", "#228B22"),
    ("NINJA",  "🥷", "#2F4F4F"), ("ROBOT",   "🤖", "#00CED1"),
    ("PIZZA",  "🍕", "#FF6B35"), ("MUSIC",   "🎵", "#DA70D6"),
    ("SPACE",  "🚀", "#191970"), ("DREAM",   "💭", "#9370DB"),
    ("LIGHT",  "💡", "#FFD700"), ("POWER",   "⚡", "#FFD700"),
    ("HEART",  "❤",  "#FF1493"), ("STAR",    "⭐", "#FFD700"),
    ("MOON",   "🌙", "#C0C0C0"), ("SOLAR",   "☀",  "#FFA500"),
]

def _pick_words():
    """Pick 6 random words from the bank each game."""
    chosen = random.sample(_ALL_WORDS, 6)
    return [{"word": w, "emoji": e, "color": c} for w, e, c in chosen]

GRID_SIZE = 10
DIRS = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]


def _build_grid(word_defs):
    word_set = {d["word"] for d in word_defs}
    grid = [[""] * GRID_SIZE for _ in range(GRID_SIZE)]
    placements = {}
    for word in [d["word"] for d in word_defs]:
        placed = False
        for _ in range(500):
            dr, dc = random.choice(DIRS)
            r0 = random.randint(0, GRID_SIZE - 1)
            c0 = random.randint(0, GRID_SIZE - 1)
            cells = [(r0+i*dr, c0+i*dc) for i in range(len(word))]
            if any(r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE for r,c in cells):
                continue
            if any(grid[r][c] not in ("", word[i]) for i,(r,c) in enumerate(cells)):
                continue
            for i,(r,c) in enumerate(cells):
                grid[r][c] = word[i]
            placements[word] = cells
            placed = True
            break
        if not placed:
            for row in range(GRID_SIZE):
                col = random.randint(0, max(0, GRID_SIZE - len(word)))
                cells = [(row, col+i) for i in range(len(word))]
                if all(grid[r][c] in ("", word[i]) for i,(r,c) in enumerate(cells)):
                    for i,(r,c) in enumerate(cells):
                        grid[r][c] = word[i]
                    placements[word] = cells
                    break
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if not grid[r][c]:
                grid[r][c] = random.choice(string.ascii_uppercase)
    return grid, placements


class WordGrid(QWidget):
    def __init__(self, screen, parent=None) -> None:
        super().__init__(parent)
        self.screen = screen
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(360, 360)
        self.setMouseTracking(True)
        self._pressing = False
        self._wrong_flash = False   # briefly show red pill on wrong release

    def _cs(self):
        return min(self.width(), self.height()) / GRID_SIZE

    def _origin(self):
        cs = self._cs()
        return (self.width() - cs * GRID_SIZE) / 2, (self.height() - cs * GRID_SIZE) / 2

    def _hit(self, x: float, y: float):
        cs = self._cs()
        ox, oy = self._origin()
        col = int((x - ox) / cs)
        row = int((y - oy) / cs)
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return (row, col)
        return None

    @staticmethod
    def _snap_direction(dr: int, dc: int):
        """
        Snap (dr, dc) to the nearest of the 8 unit directions.
        Uses a 22.5° threshold — anything within 22.5° of a diagonal
        snaps to diagonal rather than axis-aligned.
        """
        if dr == 0 and dc == 0:
            return None

        # Normalise signs
        sr = 1 if dr > 0 else (-1 if dr < 0 else 0)
        sc = 1 if dc > 0 else (-1 if dc < 0 else 0)

        adr, adc = abs(dr), abs(dc)

        # Pure axis
        if adr == 0:
            return (0, sc)
        if adc == 0:
            return (sr, 0)

        # Diagonal threshold: snap to diagonal if ratio is between 0.5 and 2.0
        # (i.e. within ~26° of 45°)
        ratio = adr / adc if adc != 0 else float("inf")
        if 0.5 <= ratio <= 2.0:
            return (sr, sc)          # diagonal

        # Dominant axis
        if adr > adc:
            return (sr, 0)           # vertical
        return (0, sc)               # horizontal

    def _build_line(self, start, direction, end_cell):
        """
        Build a straight line of cells from start in direction.
        The line extends as far as the cursor has moved along that direction.
        """
        dr, dc = direction
        sr, sc = start
        er, ec = end_cell

        # Calculate how many steps to take
        if dr != 0 and dc != 0:
            # Diagonal — use the larger of the two distances
            steps = max(abs(er - sr), abs(ec - sc))
        elif dr != 0:
            steps = abs(er - sr)
        elif dc != 0:
            steps = abs(ec - sc)
        else:
            steps = 0

        cells = []
        for i in range(steps + 1):
            nr = sr + i * dr
            nc = sc + i * dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                cells.append((nr, nc))
            else:
                break   # stop at grid boundary
        return cells if cells else [start]

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        cell = self._hit(event.position().x(), event.position().y())
        if not cell:
            return
        self._pressing = True
        self._wrong_flash = False
        self.screen.selection = [cell]
        self.screen._sel_dir = None
        self.screen.sounds.play("click")
        self.screen._update_status()
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self._pressing or not self.screen.selection:
            return
        cell = self._hit(event.position().x(), event.position().y())
        if not cell:
            return

        start = self.screen.selection[0]
        dr = cell[0] - start[0]
        dc = cell[1] - start[1]

        if dr == 0 and dc == 0:
            # Back to start — single cell
            if self.screen.selection != [start]:
                self.screen.selection = [start]
                self.screen._sel_dir = None
                self.screen._update_status()
                self.update()
            return

        # Snap to nearest valid direction
        direction = self._snap_direction(dr, dc)
        if direction is None:
            return

        # Lock direction on first move away from start
        if self.screen._sel_dir is None:
            self.screen._sel_dir = direction

        # Always use the locked direction (ignore snap changes mid-drag)
        direction = self.screen._sel_dir

        # Build the line from start to the cell projected onto the locked direction
        new_sel = self._build_line(start, direction, cell)

        if new_sel and new_sel != self.screen.selection:
            self.screen.selection = new_sel
            self.screen._update_status()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or not self._pressing:
            return
        self._pressing = False
        w = self.screen._word()
        if w in self.screen.word_set and w not in self.screen.found_placements:
            self.screen._try_submit()
        elif len(self.screen.selection) > 1:
            # Wrong word — flash red briefly then clear
            self._wrong_flash = True
            self.update()
            QTimer.singleShot(500, self._clear_wrong)
        else:
            # Single cell tap — keep it selected so user can see where they are
            pass
        self.update()

    def _clear_wrong(self):
        self._wrong_flash = False
        self.screen.selection = []
        self.screen._sel_dir = None
        self.screen._update_status()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cs = self._cs()
        ox, oy = self._origin()
        rp = cs * 0.42

        # White board
        p.setBrush(QColor(255, 255, 255))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(ox, oy, cs*GRID_SIZE, cs*GRID_SIZE), 14, 14)

        # Found pills — use instance word_defs, not a global
        for word, cells in self.screen.found_placements.items():
            ch = next(
                (d["color"] for d in self.screen.word_defs if d["word"] == word),
                "#22d98a",   # fallback colour
            )
            self._pill(p, cells, QColor(ch), cs, ox, oy, rp)

        # Selection pill — red if wrong flash, cyan if active
        if self.screen.selection:
            if self._wrong_flash:
                sel_c = QColor("#ef4444"); sel_c.setAlpha(180)
            else:
                sel_c = QColor("#0ea5e9"); sel_c.setAlpha(170)
            self._pill(p, self.screen.selection, sel_c, cs, ox, oy, rp)

        # Letters
        sel_set   = set(self.screen.selection)
        found_set: set = set()
        for cells in self.screen.found_placements.values():
            found_set.update(cells)

        p.setFont(QFont("Segoe UI", max(9, int(cs*0.44)), QFont.Weight.Bold))
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell = (row, col)
                cx = ox+(col+0.5)*cs
                cy = oy+(row+0.5)*cs
                in_found = cell in found_set
                in_sel   = cell in sel_set
                if in_found:
                    p.setPen(QColor(255, 255, 255))
                elif in_sel and self._wrong_flash:
                    p.setPen(QColor(255, 255, 255))
                elif in_sel:
                    p.setPen(QColor(255, 255, 255))
                else:
                    p.setPen(QColor(25, 25, 50))
                p.drawText(QRectF(cx-cs/2, cy-cs/2, cs, cs),
                           Qt.AlignmentFlag.AlignCenter,
                           self.screen.grid[row][col])

        # Grid lines
        p.setPen(QPen(QColor(215, 220, 232), 0.6))
        for i in range(GRID_SIZE+1):
            p.drawLine(QPointF(ox+i*cs, oy), QPointF(ox+i*cs, oy+GRID_SIZE*cs))
            p.drawLine(QPointF(ox, oy+i*cs), QPointF(ox+GRID_SIZE*cs, oy+i*cs))

    def _pill(self, p, cells, color, cs, ox, oy, r):
        if not cells:
            return
        centres = [QPointF(ox+(c+0.5)*cs, oy+(row+0.5)*cs) for row,c in cells]
        if len(centres) == 1:
            p.setBrush(color); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(centres[0], r, r)
            return
        pen = QPen(color)
        pen.setWidthF(r*2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(centres[0])
        for pt in centres[1:]:
            path.lineTo(pt)
        p.drawPath(path)


class WordSearchScreen(BaseGameScreen):
    def __init__(self, storage, sounds, parent=None) -> None:
        super().__init__(
            "word_search", "Word Search",
            "Click letters one by one to spell hidden words!",
            "#00BCD4", storage, sounds, parent,
        )
        self.grid: list[list[str]] = []
        self.word_defs: list[dict] = []
        self.word_placements:  dict = {}
        self.found_placements: dict = {}
        self.selection: list = []
        self._sel_dir: Optional[tuple] = None

        top = QHBoxLayout(); top.setSpacing(12)
        self._status = QLabel("👆  Hold and drag across letters to select a word!")
        self._status.setStyleSheet("font-size:15px; font-weight:700; color:#1a1d2e;")
        top.addWidget(self._status, 1)
        clr = NeonButton("✕  Clear"); clr.setFixedHeight(38)
        clr.clicked.connect(self.clear_selection)
        top.addWidget(clr)
        self.content_layout.addLayout(top)

        body = QHBoxLayout(); body.setSpacing(16)
        self.grid_widget = WordGrid(self)
        body.addWidget(self.grid_widget, 1)

        panel = QFrame(); panel.setObjectName("GlassCard"); panel.setFixedWidth(165)
        pl = QVBoxLayout(panel); pl.setContentsMargins(14,16,14,16); pl.setSpacing(8)
        hdr = QLabel("🔍  Find These")
        hdr.setStyleSheet("font-weight:800; font-size:15px; color:#f4f6ff;")
        pl.addWidget(hdr)
        self._word_labels: dict[str, QLabel] = {}
        self._word_label_container = pl  # keep ref to rebuild labels
        pl.addStretch(1)
        self._prog = QLabel("0 / 6 found")
        self._prog.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._prog.setStyleSheet("color:#8899cc; font-size:12px;")
        pl.addWidget(self._prog)
        body.addWidget(panel, 0)
        self.content_layout.addLayout(body, 1)

        self.reset_game()
        self.show_tutorial([
            {"emoji": "🔍", "title": "Welcome to Word Search!",
             "body": "Hidden words are in the grid — across, down, or diagonal. Find them all!"},
            {"emoji": "👆", "title": "Click Letters One by One",
             "body": "Hold the left mouse button on the first letter and drag across the word in a straight line. Release to submit!"},
            {"emoji": "✅", "title": "Auto-Found!",
             "body": "The moment you complete a hidden word it lights up automatically — no submit button needed!"},
            {"emoji": "🏆", "title": "Find All 6 Words!",
             "body": "Each word earns 10 points. Find all 6 to win the puzzle. Good luck!"},
        ])

    def reset_game(self) -> None:
        # Pick fresh random words every game
        self.word_defs = _pick_words()
        self.word_set  = {d["word"] for d in self.word_defs}
        self.grid, self.word_placements = _build_grid(self.word_defs)
        self.found_placements = {}
        self.selection = []
        self._sel_dir = None
        self.set_score(0)
        self._status.setText("👆  Hold and drag to select a word!")
        self._prog.setText(f"0 / {len(self.word_defs)} found")

        # Rebuild word labels for the new word set
        # Remove old labels
        for lbl in self._word_labels.values():
            lbl.setParent(None)
        self._word_labels = {}
        # Insert new labels before the stretch (second-to-last item)
        lay = self._word_label_container
        # Remove stretch, add labels, re-add stretch
        # Find and remove the stretch spacer
        for i in range(lay.count() - 1, -1, -1):
            item = lay.itemAt(i)
            if item and item.spacerItem():
                lay.removeItem(item)
                break
        for d in self.word_defs:
            lbl = QLabel(f"{d['emoji']}  {d['word']}")
            lbl.setStyleSheet("color:#8899cc; font-size:14px; font-weight:700;"
                              " padding:5px 8px; border-radius:10px;")
            self._word_labels[d["word"]] = lbl
            lay.addWidget(lbl)
        lay.addStretch(1)

        self.grid_widget.update()

    def on_cell_click(self, cell) -> None:
        """Single-tap fallback — starts a new selection from this cell."""
        row, col = cell
        # If tapping the same start cell, clear selection
        if self.selection and cell == self.selection[0] and len(self.selection) == 1:
            self.clear_selection()
            return
        # Start fresh
        self.selection = [cell]
        self._sel_dir = None
        self.sounds.play("click")
        self._update_status()
        self.grid_widget.update()

    def _word(self):
        return "".join(self.grid[r][c] for r,c in self.selection)

    def _update_status(self) -> None:
        w = self._word()
        if not w:
            self._status.setText("👆  Hold and drag to select a word!"); return
        rem = [d["word"] for d in self.word_defs if d["word"] not in self.found_placements]
        if w in self.word_set and w not in self.found_placements:
            self._status.setText(f"✅  {w}  — found!")
        elif any(r.startswith(w) for r in rem):
            self._status.setText(f"🔤  {w}  — keep going...")
        else:
            self._status.setText(f"❌  {w}  — not a word here")

    def _try_submit(self) -> None:
        w = self._word()
        if w in self.word_set and w not in self.found_placements:
            self._submit(w)

    def _submit(self, word: str) -> None:
        ch = next(d["color"] for d in self.word_defs if d["word"] == word)
        placed = self.word_placements.get(word, self.selection[:])
        self.found_placements[word] = placed
        self.sounds.play("success")
        self.selection = []; self._sel_dir = None
        self._word_labels[word].setStyleSheet(
            f"color:white; font-size:14px; font-weight:800;"
            f" padding:5px 8px; border-radius:10px;"
            f" background:{ch}; text-decoration:line-through;")
        score = len(self.found_placements) * 10
        self.set_score(score)
        total = len(self.word_defs)
        self._prog.setText(f"{len(self.found_placements)} / {total} found")
        self._status.setText(f"🎉  {word} found!  Keep going!")
        self.grid_widget.update()
        if len(self.found_placements) == total:
            QTimer.singleShot(700, self._all_found)

    def _all_found(self) -> None:
        self.sounds.play("success")
        self.show_game_over("🎉", "You Found Them All!",
                            len(self.found_placements)*10,
                            "Amazing! Every hidden word discovered!")

    def clear_selection(self) -> None:
        self.selection = []; self._sel_dir = None
        self._status.setText("👆  Hold and drag to select a word!")
        self.grid_widget.update()


