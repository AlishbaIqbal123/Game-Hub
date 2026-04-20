"""
Arcade Hub — Editorial Play Design System
Inspired by the 'Elevated Playground' philosophy:
- Pinterest-meets-Apple aesthetic.
- Heavy organic curves (rounded-xl/ROUND_FULL).
- Tonal depth over structural rigidity (no 1px borders for sectioning).
- Lush gradients and glassmorphism.
"""
from __future__ import annotations
from PyQt6.QtGui import QColor

# ── Editorial Play Palette (Dark Mode) ─────────────────────────────────────────
DARK = {
    # Surfaces & Backgrounds
    "bg":           "#060e20",   # ink navy
    "surface":      "#060e20",
    "surface_low":  "#081329",   # sectioning
    "surface_mid":  "#0c1934",   # container
    "surface_high": "#101e3e",   # interactive cards
    "surface_highest":"#142449", # elevated/hover
    "surface_bright":"#172b54",  # floating/pop-overs
    
    # Text & Content
    "text":         "#dee5ff",   # primary text
    "on_surface":   "#dee5ff",
    "text_sec":     "#9baad6",   # muted / secondary
    "muted":        "#38476d",   # disabled / outline variant
    
    # Brand Accents — Glowing Pastels
    "primary":      "#c4ffcd",   # primary pastel green
    "primary_con":  "#6dfe9c",   # primary container hint
    "primary_dim":  "#5def8f",
    
    "secondary":      "#bdc2ff", # lavender/blue
    "secondary_con":  "#010c83",
    
    "tertiary":       "#ffcb97", # peach/gold
    "tertiary_con":   "#fcb973",
    
    "error":          "#fd6f85",
    "error_con":      "#8a1632",
    "success":        "#22d98a",
    "warning":        "#ffd60a",

    # Structural
    "border":       "rgba(101, 117, 158, 0.15)", # Ghost border fallback
    "outline":      "#65759e",
    "shadow":       "rgba(0, 0, 0, 0.50)",
    "overlay":      "rgba(6, 14, 32, 0.85)",
}

# ── Editorial Play Palette (Light Mode) ────────────────────────────────────────
LIGHT = {
    "bg":           "#faf8ff",
    "surface":      "#faf8ff",
    "surface_low":  "#f0f1f8",
    "surface_mid":  "#e8eaf4",
    "surface_high": "#e1e4f0",
    "surface_highest":"#d9ddec",
    "surface_bright":"#ffffff",

    "text":         "#060e20",
    "on_surface":   "#060e20",
    "text_sec":     "#3c4a6e",
    "muted":        "#717e9e",

    "primary":      "#005a2e",
    "primary_con":  "#a7ffb4",
    "primary_dim":  "#003d1f",

    "secondary":      "#1a227e",
    "secondary_con":  "#d1d1ff",
    
    "tertiary":       "#512e00",
    "tertiary_con":   "#ffcb97",

    "error":          "#8a1632",
    "error_con":      "#fd6f85",
    "success":        "#006e36",
    "warning":        "#a25600",

    "border":       "rgba(6, 14, 32, 0.12)",
    "outline":      "#3c4a6e",
    "shadow":       "rgba(0, 0, 0, 0.15)",
    "overlay":      "rgba(250, 248, 255, 0.85)",
}

# Active palette
PALETTE = dict(DARK)
_dark_mode = True

# Premium Typography
FONT_BODY  = '"Plus Jakarta Sans", "Inter", "Segoe UI", sans-serif'
FONT_TITLE = '"Plus Jakarta Sans", "Inter", "Segoe UI Semibold", sans-serif'
FONT_MONO  = '"Consolas", "Courier New", monospace'


def is_dark() -> bool:
    return _dark_mode


def set_dark_mode(dark: bool) -> None:
    global _dark_mode, PALETTE
    _dark_mode = dark
    PALETTE.clear()
    PALETTE.update(DARK if dark else LIGHT)


def qcolor(name: str) -> QColor:
    if name not in PALETTE:
        # Compatibility aliases if components use old names
        alias = {
            "bg_alt": "surface_low",
            "surface_alt": "surface_mid",
            "text_sec": "text_sec",
            "card_bg": "surface_high",
            "sidebar_bg": "bg",
            "primary_light": "primary_con",
        }.get(name)
        if alias: return QColor(PALETTE[alias])
    return QColor(PALETTE.get(name, "#888888"))


def app_stylesheet() -> str:
    p = PALETTE
    dark = _dark_mode

    return f"""
    * {{ 
        outline: none; 
        border: none;
    }}

    QWidget {{
        color: {p["text"]};
        font-family: {FONT_BODY};
        font-size: 14px;
        selection-background-color: {p["primary"]}44;
        selection-color: {p["primary"]};
    }}

    QMainWindow, QWidget#RootSurface {{
        background: {p["bg"]};
    }}

    /* ── Scrollable areas ── */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{
        width: 12px; background: transparent; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p["surface_highest"]};
        border-radius: 6px; min-height: 40px; margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p["primary"]}88;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ height: 0px; }}

    /* ── Typography ── */
    QLabel#TitleLabel {{
        font-family: {FONT_TITLE};
        font-size: 32px;
        font-weight: 800;
        color: {p["primary"]};
        letter-spacing: -0.02em;
    }}
    QLabel#SectionLabel {{
        font-family: {FONT_TITLE};
        font-size: 18px;
        font-weight: 700;
        color: {p["text"]};
    }}
    QLabel#MutedLabel {{
        color: {p["text_sec"]};
        font-size: 14px;
        line-height: 1.6;
    }}
    QLabel#TagLabel {{
        color: {p["secondary"]};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}
    QLabel#HeroTitle {{
        font-family: {FONT_TITLE};
        font-size: 42px;
        font-weight: 900;
        color: {p["primary"]};
    }}
    QLabel#HeroSubtitle {{
        font-family: {FONT_BODY};
        font-size: 16px;
        color: {p["text_sec"]};
    }}

    /* ── Cards — No 1px borders, use tonal layering ── */
    QFrame#Card {{
        background: {p["surface_high"]};
        border-radius: 32px;
    }}
    QFrame#GlassCard {{
        background: {p["surface_mid"]};
        border-radius: 32px;
    }}
    QFrame#PanelCard {{
        background: {p["surface_low"]};
        border-radius: 24px;
    }}
    QFrame#SidebarFrame {{
        background: {p["surface_low"]};
        border-radius: 0px;
    }}

    /* ── Buttons — Premium Modern ── */
    QPushButton {{
        border-radius: 20px;
        padding: 10px 20px;
        background: {p["surface_highest"]};
        font-weight: 700;
        font-size: 14px;
        color: {p["text"]};
    }}
    QPushButton:hover {{
        background: {p["primary"]}33;
        color: {p["primary"]};
    }}
    
    /* ── Primary CTA — Gradient effect simulation via specific color ── */
    QPushButton#PrimaryButton {{
        background: {p["primary"]};
        color: {p["bg"]};
        border-radius: 20px;
        padding: 12px 24px;
        font-weight: 900;
    }}
    QPushButton#PrimaryButton:hover {{
        background: {p["primary_con"]};
    }}

    QPushButton#DangerButton {{
        background: {p["error_con"]};
        color: {p["error"]};
    }}
    QPushButton#DangerButton:hover {{
        background: {p["error"]};
        color: #ffffff;
    }}

    QPushButton#GhostButton {{
        background: transparent;
        color: {p["text"]};
    }}
    QPushButton#GhostButton:hover {{
        background: {p["surface_highest"]};
        color: {p["primary"]};
    }}

    /* ── Sidebar nav buttons ── */
    QPushButton#SidebarButton {{
        text-align: left;
        border-radius: 16px;
        padding: 14px 20px;
        background: transparent;
        color: {p["text"]};
        font-weight: 700;
    }}
    QPushButton#SidebarButton:hover {{
        background: {p["surface_mid"]};
        color: {p["text"]};
    }}
    QPushButton#SidebarButton:checked {{
        background: {p["primary"]};
        color: {p["bg"]};
        font-weight: 800;
    }}

    /* ── Inputs ── */
    QLineEdit, QComboBox {{
        border-radius: 16px;
        padding: 12px 16px;
        background: {p["surface_mid"]};
        color: {p["text"]};
    }}
    QLineEdit:focus, QComboBox:focus {{
        background: {p["surface_high"]};
    }}
    
    QListWidget {{
        background: {p["surface_mid"]};
        border-radius: 20px;
        padding: 8px;
    }}
    QListWidget::item {{
        padding: 12px;
        border-radius: 12px;
    }}
    QListWidget::item:selected {{
        background: {p["primary"]}33;
        color: {p["primary"]};
    }}
    """

