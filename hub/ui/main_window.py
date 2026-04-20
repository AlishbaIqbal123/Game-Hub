from __future__ import annotations
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from hub.core.sound import SoundManager
from hub.core.storage import StorageManager
from hub.core.theme import app_stylesheet, set_dark_mode
from hub.games.registry import build_registry
from hub.ui.dashboard import DashboardScreen
from hub.ui.discovery import DiscoveryScreen
from hub.ui.settings import SettingsScreen
from hub.ui.achievements import AchievementsScreen
from hub.ui.help import HelpScreen
from hub.ui.sidebar import Sidebar
from hub.ui.transitions import FadeStackedWidget


class MainWindow(QMainWindow):
    def __init__(self, resource_root: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("ARCADE HUB — Editorial Play")
        self.resize(1500, 950)
        self.setMinimumSize(1200, 750)
        self.showMaximized()

        if resource_root is None:
            resource_root = Path(__file__).resolve().parents[2]

        data_dir = resource_root / ".hub_data"
        self.storage = StorageManager(data_dir)
        self.sounds  = SoundManager(data_dir / "sounds", self.storage.settings)
        self.registry = build_registry(self.storage, self.sounds)

        self.setStyleSheet(app_stylesheet())

        # ── Root layout: sidebar + content stack ──────────────────────────────
        root_w = QWidget(objectName="RootSurface")
        self.setCentralWidget(root_w)
        root_lay = QHBoxLayout(root_w)
        root_lay.setContentsMargins(0, 0, 0, 0); root_lay.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.registry, self.storage)
        self.sidebar.navigate.connect(self._on_navigate)
        self.sidebar.theme_changed.connect(self._on_theme_changed)
        self.sidebar.sound_toggled.connect(self._on_sound_toggled)
        self.sidebar.anim_toggled.connect(self._on_anim_toggled)
        root_lay.addWidget(self.sidebar)

        # Content stack
        self.stack = FadeStackedWidget()
        root_lay.addWidget(self.stack, 1)

        # ── Screens ───────────────────────────────────────────────────────────
        self.dashboard = DashboardScreen(self.registry, self.storage)
        self.dashboard.open_game.connect(self._launch_game)
        self.dashboard.open_settings.connect(lambda: self._on_navigate("settings"))

        self.settings_screen = SettingsScreen(self.storage)
        self.settings_screen.go_home.connect(lambda: self._on_navigate("home"))
        self.settings_screen.settings_changed.connect(self._on_settings_changed)

        self.discovery_screen = DiscoveryScreen(self.registry, self.storage)
        self.discovery_screen.open_game.connect(self._launch_game)
        
        self.achievements = AchievementsScreen(self.registry, self.storage)
        self.help_screen = HelpScreen()

        self.screens: dict[str, QWidget] = {
            "home":         self.dashboard,
            "games":        self.discovery_screen,
            "settings":     self.settings_screen,
            "achievements": self.achievements,
            "help":         self.help_screen,
        }
        
        # Add core screens to stack
        for key in ["home", "games", "settings", "achievements", "help"]:
            self.stack.addWidget(self.screens[key])

        # Build game screens
        for key, meta in self.registry.items():
            screen = meta["factory"]()
            screen.go_home.connect(lambda: self._on_navigate("home"))
            screen.open_settings.connect(lambda: self._on_navigate("settings"))
            self.screens[key] = screen
            self.stack.addWidget(screen)

        self._on_navigate("home", animate=False)

    def _on_navigate(self, key: str, animate: bool = True) -> None:
        # Map specialized sidebar keys to screen keys
        screen_key = key

        if screen_key not in self.screens:
            return

        # Show/Hide sidebar based on screen type
        main_menus = ["home", "games", "settings", "achievements", "help"]
        is_main = screen_key in main_menus
        self.sidebar.setVisible(is_main)

        self.sidebar.set_active(key)
        widget = self.screens[screen_key]
        idx = self.stack.indexOf(widget)
        anim_on = self.storage.settings().get("animations_enabled", True)
        
        if animate and anim_on:
            self.stack.set_current_index_animated(idx)
        else:
            self.stack.setCurrentIndex(idx)

    def _launch_game(self, key: str) -> None:
        if key in self.screens:
            self.sidebar.hide() # Auto-hide on game launch
            widget = self.screens[key]
            idx = self.stack.indexOf(widget)
            anim_on = self.storage.settings().get("animations_enabled", True)
            if anim_on:
                self.stack.set_current_index_animated(idx)
            else:
                self.stack.setCurrentIndex(idx)

    def _on_theme_changed(self, dark: bool) -> None:
        self.setStyleSheet(app_stylesheet())
        self.sidebar.update()

    def _on_sound_toggled(self, on: bool) -> None:
        self.storage.update_settings({"sound_enabled": on})

    def _on_anim_toggled(self, on: bool) -> None:
        self.storage.update_settings({"animations_enabled": on})

    def _on_settings_changed(self, updates: dict) -> None:
        self.sidebar.refresh_toggles(self.storage.settings())

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showMaximized()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
