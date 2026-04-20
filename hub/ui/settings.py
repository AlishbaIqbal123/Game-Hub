from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget,
)

from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY
from hub.ui.components import NeonButton, StatChip, SectionPanel
from hub.ui.components import animate_reveal


class SettingsScreen(QWidget):
    go_home          = pyqtSignal()
    settings_changed = pyqtSignal(dict)

    def __init__(self, storage, parent=None) -> None:
        super().__init__(parent)
        self.storage = storage
        self._animated_widgets: list[QWidget] = []

        root = QHBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(32)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("PanelCard")
        sidebar.setFixedWidth(280)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(32, 40, 32, 40)
        sl.setSpacing(12)

        brand = QLabel("SYSTEM PREFERENCES")
        brand.setObjectName("TagLabel")
        sl.addWidget(brand)
        
        sl.addSpacing(16)
        sl.addWidget(StatChip("⚡ Performance", PALETTE["primary"]))
        sl.addWidget(StatChip("🎨 High-Fidelity", PALETTE["secondary"]))
        sl.addWidget(StatChip("✓ Sync Active", PALETTE["tertiary"]))
        
        sl.addStretch(1)
        
        note = QLabel("Your preferences are synchronized across all experiences.")
        note.setObjectName("MutedLabel")
        note.setWordWrap(True)
        sl.addWidget(note)
        
        root.addWidget(sidebar)

        # ── Main area ─────────────────────────────────────────────────────────
        main = QVBoxLayout()
        main.setSpacing(24)
        root.addLayout(main, 1)

        # Settings panel
        panel = QFrame()
        panel.setObjectName("Card")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(48, 48, 48, 48)
        pl.setSpacing(32)
        
        header = QVBoxLayout(); header.setSpacing(8)
        h_title = QLabel("System Settings"); h_title.setObjectName("TitleLabel")
        h_sub = QLabel("Configure your environment for the best experience."); h_sub.setObjectName("MutedLabel")
        header.addWidget(h_title); header.addWidget(h_sub)
        pl.addLayout(header)

        # ── Sound row ─────────────────────────────────────────────────────────
        sr = QHBoxLayout()
        s_icon = QLabel("♬")
        s_icon.setStyleSheet(f"font-size:32px; color:{PALETTE['primary']};")
        sr.addWidget(s_icon)
        s_info = QVBoxLayout(); s_info.setSpacing(4)
        s_info.addWidget(self._row_title("Audio Feedback"))
        s_info.addWidget(self._row_sub("Immersive sound effects for interactions"))
        sr.addLayout(s_info, 1)
        self.sound_toggle = QCheckBox("")
        sr.addWidget(self.sound_toggle)
        pl.addLayout(sr)

        # ── Animation row ─────────────────────────────────────────────────────
        ar = QHBoxLayout()
        a_icon = QLabel("✦")
        a_icon.setStyleSheet(f"font-size:32px; color:{PALETTE['secondary']};")
        ar.addWidget(a_icon)
        a_info = QVBoxLayout(); a_info.setSpacing(4)
        a_info.addWidget(self._row_title("Visual Dynamics"))
        a_info.addWidget(self._row_sub("Smooth transitions and fluid UI motion"))
        ar.addLayout(a_info, 1)
        self.anim_toggle = QCheckBox("")
        ar.addWidget(self.anim_toggle)
        pl.addLayout(ar)

        # ── Volume row ────────────────────────────────────────────────────────
        vr = QHBoxLayout()
        v_icon = QLabel("❂")
        v_icon.setStyleSheet(f"font-size:32px; color:{PALETTE['tertiary']};")
        vr.addWidget(v_icon)
        v_info = QVBoxLayout(); v_info.setSpacing(4)
        v_info.addWidget(self._row_title("Master Intensity"))
        v_info.addWidget(self._row_sub("Global volume level for all experiences"))
        vr.addLayout(v_info, 1)
        self.volume_value = QLabel("60%")
        self.volume_value.setStyleSheet(f"color:{PALETTE['primary']}; font-weight:900; font-size:20px;")
        vr.addWidget(self.volume_value)
        pl.addLayout(vr)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedHeight(30)
        self.volume_slider.valueChanged.connect(lambda v: self.volume_value.setText(f"{v}%"))
        pl.addWidget(self.volume_slider)

        pl.addSpacing(16)

        # ── Action buttons ────────────────────────────────────────────────────
        ab = QHBoxLayout(); ab.setSpacing(20)
        save_btn = NeonButton("COMMIT CHANGES", primary=True); save_btn.setFixedHeight(56)
        save_btn.clicked.connect(self.save_settings)
        home_btn = NeonButton("RETURN TO HUB"); home_btn.setFixedHeight(56)
        home_btn.clicked.connect(self.go_home.emit)
        ab.addWidget(save_btn, 1); ab.addWidget(home_btn, 1)
        pl.addLayout(ab)

        main.addWidget(panel); main.addStretch(1)
        self._animated_widgets.extend([sidebar, panel])
        self.load_settings()

    @staticmethod
    def _row_title(text: str) -> QLabel:
        lbl = QLabel(text); lbl.setStyleSheet("font-weight:800; font-size:16px;")
        return lbl

    @staticmethod
    def _row_sub(text: str) -> QLabel:
        lbl = QLabel(text); lbl.setObjectName("MutedLabel")
        return lbl

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.load_settings()
        for i, w in enumerate(self._animated_widgets):
            animate_reveal(w, delay_ms=i * 60)

    def load_settings(self) -> None:
        s = self.storage.settings()
        self.sound_toggle.setChecked(bool(s.get("sound_enabled", True)))
        self.anim_toggle.setChecked(bool(s.get("animations_enabled", True)))
        self.volume_slider.setValue(int(s.get("volume", 60)))

    def save_settings(self) -> None:
        updates = {
            "sound_enabled":     self.sound_toggle.isChecked(),
            "animations_enabled": self.anim_toggle.isChecked(),
            "volume":            self.volume_slider.value(),
        }
        self.storage.update_settings(updates)
        self.settings_changed.emit(updates)
