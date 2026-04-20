from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from hub.ui.components import NeonButton, StatChip, TutorialOverlay, GameOverOverlay
from hub.ui.pause_menu import PauseMenu
from hub.ui.transitions import animate_reveal


class BaseGameScreen(QWidget):
    go_home     = pyqtSignal()
    open_settings = pyqtSignal()
    score_changed = pyqtSignal(str, int)

    def __init__(self, game_key, title, subtitle, accent, storage, sounds, parent=None) -> None:
        super().__init__(parent)
        self.game_key = game_key
        self.accent   = accent
        self.storage  = storage
        self.sounds   = sounds
        self.storage.increment_stat("games_played")
        self._animated_widgets: list[QWidget] = []

        # Pause dialog
        self.pause_dialog = PauseMenu(self)
        self.pause_dialog.resume_button.clicked.connect(self.pause_dialog.accept)
        self.pause_dialog.restart_button.clicked.connect(self._restart_from_pause)
        self.pause_dialog.settings_button.clicked.connect(self._open_settings_from_pause)
        self.pause_dialog.home_button.clicked.connect(self._go_home_from_pause)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # ── Main area (no sidebar — it's in MainWindow) ───────────────────────
        main_area = QVBoxLayout()
        main_area.setSpacing(10)
        root.addLayout(main_area, 1)

        # Header bar
        header = QFrame()
        header.setObjectName("GlassCard")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 8, 12, 8)
        hl.setSpacing(12)

        # Coloured left accent stripe
        stripe = QFrame()
        stripe.setFixedWidth(5)
        stripe.setStyleSheet(
            f"background:{accent}; border-radius:3px;")
        hl.addWidget(stripe)

        tb = QVBoxLayout(); tb.setSpacing(2)
        t_lbl = QLabel(title.upper())
        t_lbl.setObjectName("TitleLabel")
        t_lbl.setStyleSheet(f"font-size:20px; font-weight:800; color:{accent};")
        s_lbl = QLabel(subtitle)
        s_lbl.setObjectName("MutedLabel"); s_lbl.setWordWrap(True)
        tb.addWidget(t_lbl); tb.addWidget(s_lbl)
        hl.addLayout(tb, 1)

        # Game controls
        ctrl = QHBoxLayout(); ctrl.setSpacing(8)
        self.pause_button    = NeonButton("⏸  Pause")
        self.settings_button = NeonButton("⚙️")
        self.home_button     = NeonButton("🏠  Home")
        self.pause_button.setFixedHeight(36)
        self.settings_button.setFixedSize(36, 36)
        self.home_button.setFixedHeight(36)
        self.pause_button.clicked.connect(self.open_pause_menu)
        self.settings_button.clicked.connect(self.open_settings.emit)
        self.home_button.clicked.connect(self.go_home.emit)
        ctrl.addWidget(self.pause_button)
        ctrl.addWidget(self.settings_button)
        ctrl.addWidget(self.home_button)
        hl.addLayout(ctrl)

        # Score chips
        chips_col = QVBoxLayout(); chips_col.setSpacing(4)
        self.score_chip = QLabel("⭐ 0")
        self.score_chip.setStyleSheet(
            f"background:{accent}22; border:1px solid {accent}55;"
            f" border-radius:12px; padding:5px 12px;"
            f" color:{accent}; font-size:13px; font-weight:700;")
        best = self.storage.high_score(game_key)
        self.high_score_chip = QLabel("Best  —" if best == 0 else f"🏆 {best}")
        self.high_score_chip.setStyleSheet(
            f"background:{accent}11; border:1px solid {accent}33;"
            f" border-radius:12px; padding:5px 12px;"
            f" color:{accent}; font-size:12px; font-weight:600;")
        chips_col.addWidget(self.score_chip)
        chips_col.addWidget(self.high_score_chip)
        hl.addLayout(chips_col)
        main_area.addWidget(header)

        # Content frame with Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.content = QFrame()
        self.content.setObjectName("PanelCard")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(14)
        
        self.scroll.setWidget(self.content)
        main_area.addWidget(self.scroll, 1)

        self._animated_widgets.extend([header, self.content])

        # Tutorial overlay (shown on first play)
        self._tutorial: TutorialOverlay | None = None
        # Game-over overlay
        self._game_over_overlay = GameOverOverlay(
            on_restart=self._do_restart,
            on_home=self.go_home.emit,
            parent=self,
        )
        self._game_over_overlay.hide()

    def _do_restart(self) -> None:
        self.reset_game()

    def show_tutorial(self, steps: list[dict]) -> None:
        """Show the tutorial overlay. Call from subclass __init__ after building UI."""
        if self.storage.has_seen_tutorial(self.game_key):
            return
        self._tutorial = TutorialOverlay(
            steps=steps,
            on_done=lambda: self.storage.mark_tutorial_seen(self.game_key),
            parent=self,
        )
        self._tutorial.setGeometry(self.rect())
        self._tutorial.show()
        self._tutorial.raise_()

    def show_game_over(self, emoji: str, title: str, score: int, message: str = "") -> None:
        """Show the game-over overlay with score summary."""
        best = self.storage.high_score(self.game_key)
        self._game_over_overlay.show_result(emoji, title, score, best, message)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._tutorial and self._tutorial.isVisible():
            self._tutorial.setGeometry(self.rect())
        if self._game_over_overlay.isVisible():
            self._game_over_overlay.setGeometry(self.rect())

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        best = self.storage.high_score(self.game_key)
        self.high_score_chip.setText("Best  —" if best == 0 else f"🏆 {best}")
        for i, w in enumerate(self._animated_widgets):
            animate_reveal(w, delay_ms=i * 55)

    def set_score(self, score: int) -> None:
        self.score_chip.setText(f"⭐ {score}")
        if self.storage.update_high_score(self.game_key, score):
            self.high_score_chip.setText(f"🏆 {score}")
        else:
            best = self.storage.high_score(self.game_key)
            self.high_score_chip.setText("Best  —" if best == 0 else f"🏆 {best}")
        self.score_changed.emit(self.game_key, score)

    def open_pause_menu(self) -> None:
        self.sounds.play("click")
        self.pause_dialog.adjustSize()
        self.pause_dialog.show()
        self.pause_dialog.raise_()
        self.pause_dialog.activateWindow()

    def _restart_from_pause(self) -> None:
        self.pause_dialog.accept(); self.reset_game()

    def _open_settings_from_pause(self) -> None:
        self.pause_dialog.accept(); self.open_settings.emit()

    def _go_home_from_pause(self) -> None:
        self.pause_dialog.accept(); self.go_home.emit()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_P):
            self.open_pause_menu()
        else:
            super().keyPressEvent(event)

    def reset_game(self) -> None:
        raise NotImplementedError
