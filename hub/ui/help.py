from __future__ import annotations
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QPushButton
)
from hub.core.theme import PALETTE, FONT_TITLE, FONT_BODY
from hub.ui.components import StatChip, NeonButton, animate_reveal

class HelpScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._animated_widgets = []

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 40, 40, 40)
        main.setSpacing(32)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame(); header.setObjectName("GlassCard"); header.setFixedHeight(120)
        hl = QHBoxLayout(header); hl.setContentsMargins(32, 0, 32, 0)
        
        ht = QVBoxLayout(); ht.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag = QLabel("SUPPORT CENTER"); tag.setObjectName("TagLabel")
        title = QLabel("Knowledge Base"); title.setObjectName("TitleLabel")
        ht.addWidget(tag); ht.addWidget(title)
        hl.addLayout(ht); hl.addStretch(1)

        hl.addWidget(StatChip("❓ v2.4.0", PALETTE["primary"]))
        main.addWidget(header)
        self._animated_widgets.append(header)

        # ── Content ───────────────────────────────────────────────────────────
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_w = QWidget(); content_lay = QVBoxLayout(content_w)
        content_lay.setContentsMargins(0, 0, 10, 0); content_lay.setSpacing(24)

        # FAQs
        faq_frame = QFrame(); faq_frame.setObjectName("Card")
        fl = QVBoxLayout(faq_frame); fl.setContentsMargins(40, 40, 40, 40); fl.setSpacing(24)
        
        sec_title = QLabel("Frequently Asked Questions"); sec_title.setObjectName("SectionLabel")
        fl.addWidget(sec_title); fl.addSpacing(16)

        faqs = [
            ("How do I save my progress?", "All your high scores and settings are saved automatically to your local profile after every match."),
            ("Can I play offline?", "Yes! Arcade Hub is designed to work fully offline. No internet connection is required for any of the games."),
            ("How are scores calculated?", "Each game has its own scoring system. Generally, surviving longer and playing with higher precision gives more points."),
            ("Is there a dark mode?", "Arcade Hub defaults to a dark midnight theme for the best visual comfort, but you can toggle contrast in settings."),
        ]

        for q, a in faqs:
            ql = QLabel(f"Q: {q}")
            ql.setStyleSheet(f"font-weight: 800; font-size: 18px; color: {PALETTE['primary']};")
            fl.addWidget(ql)
            
            al = QLabel(a)
            al.setObjectName("MutedLabel"); al.setWordWrap(True)
            fl.addWidget(al)
            fl.addSpacing(8)

        content_lay.addWidget(faq_frame)
        self._animated_widgets.append(faq_frame)

        # Contact
        contact = QFrame(); contact.setObjectName("PanelCard")
        cl = QHBoxLayout(contact); cl.setContentsMargins(32, 32, 32, 32); cl.setSpacing(24)
        
        c_info = QVBoxLayout(); c_info.setSpacing(4)
        c_info.addWidget(QLabel("Need more help?"))
        c_sub = QLabel("Our support team is available 24/7 to assist with your technical inquiries."); c_sub.setObjectName("MutedLabel")
        c_info.addWidget(c_sub)
        cl.addLayout(c_info, 1)
        
        btn = NeonButton("CONTACT SUPPORT", primary=True); btn.setFixedSize(200, 50)
        cl.addWidget(btn)
        content_lay.addWidget(contact)
        self._animated_widgets.append(contact)

        scroll.setWidget(content_w)
        main.addWidget(scroll, 1)

    def showEvent(self, event):
        super().showEvent(event)
        for i, w in enumerate(self._animated_widgets):
            animate_reveal(w, delay_ms=i*100)
