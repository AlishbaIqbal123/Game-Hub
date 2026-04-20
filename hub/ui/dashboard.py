from __future__ import annotations
import math
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)
from hub.ui.components import NeonButton, SectionPanel, StatChip
from hub.ui.transitions import animate_reveal
from hub.core.theme import PALETTE


# ── Animated preview painters (frame = tick counter) ─────────────────────────

def _p_tic(p, r, f):
    from hub.core.theme import PALETTE, is_dark
    # Grid background
    bg = QColor(PALETTE["surface_mid"])
    p.fillRect(r, bg)
    
    # Grid lines (lavender)
    p.setPen(QPen(QColor(PALETTE["secondary"]), 2)); p.setBrush(Qt.BrushStyle.NoBrush)
    w,h = r.width(),r.height(); x,y = r.x(),r.y()
    for i in (1,2):
        p.drawLine(QPointF(x+w*i/3,y+8),QPointF(x+w*i/3,y+h-8))
        p.drawLine(QPointF(x+8,y+h*i/3),QPointF(x+w-8,y+h*i/3))
    
    # X and O marks — vibrant glow
    marks=[("X",0,0),("O",1,0),("X",2,0),("O",0,1),("X",1,1),("X",0,2),("O",2,2)]
    p.setFont(QFont("Plus Jakarta Sans",max(8,int(w*0.13)),QFont.Weight.Bold))
    for m,c,row in marks:
        col = QColor(PALETTE["error"] if m=="X" else PALETTE["primary"])
        p.setPen(col)
        # Pulse alpha
        ca = QColor(col); ca.setAlpha(180 + int(30 * math.sin(f*0.1)))
        p.setPen(ca)
        p.drawText(QRectF(x+(c+0.1)*w/3,y+(row+0.1)*h/3,w*0.8/3,h*0.8/3),
                   Qt.AlignmentFlag.AlignCenter,m)

def _p_c4(p, r, f):
    from hub.core.theme import PALETTE
    # Board background - deep ink
    p.setBrush(QColor(PALETTE["surface_highest"])); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(r,12,12)
    
    cols,rows=7,5; cw=r.width()/cols; ch=r.height()/rows
    board={(0,4):PALETTE["error"],(1,4):PALETTE["tertiary"],(2,4):PALETTE["error"],(3,4):PALETTE["tertiary"],
           (4,4):PALETTE["error"],(1,3):PALETTE["tertiary"],(2,3):PALETTE["error"],(2,2):PALETTE["tertiary"]}
    
    for row in range(rows):
        for col in range(cols):
            cx=r.x()+(col+0.5)*cw; cy=r.y()+(row+0.5)*ch
            key=(col,row)
            if key in board:
                c=QColor(board[key])
            else:
                c=QColor(PALETTE["surface_mid"])
            p.setBrush(c); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx,cy),cw*0.35,ch*0.35)

def _p_snake(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    
    g=9; cw=r.width()/g; ch=r.height()/g
    # Snake body segments
    segs=[(4,4),(3,4),(2,4),(2,3),(2,2),(3,2)]
    for i,(gc,gr) in enumerate(segs):
        col=QColor(PALETTE["primary"]) if i==0 else QColor(PALETTE["secondary"])
        p.setBrush(col); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(r.x()+gc*cw+2,r.y()+gr*ch+2,cw-4,ch-4),6,6)
    # Food (glowing peach)
    p.setBrush(QColor(PALETTE["tertiary"]))
    glow = QColor(PALETTE["tertiary"]); glow.setAlpha(100)
    p.setPen(QPen(glow, 4))
    p.drawEllipse(QPointF(r.x()+6*cw+cw/2,r.y()+6*ch+ch/2),cw*0.3,ch*0.3)

def _p_ludo(p, r, f):
    """A highly detailed, realistic Ludo board preview."""
    from hub.core.theme import PALETTE
    w, h = r.width(), r.height(); x, y = r.x(), r.y()
    p.fillRect(r, QColor(PALETTE["surface_mid"]))
    
    # ── Geometry constants
    tile_w = w / 15; tile_h = h / 15
    yard_size = 6 * tile_w
    
    # ── Yards (Corners)
    colors = [
        (PALETTE["error"], 0, 0),       # Top-Left (Red)
        (PALETTE["primary"], 9, 0),     # Top-Right (Green)
        (PALETTE["secondary"], 0, 9),   # Bottom-Left (Blue)
        (PALETTE["tertiary"], 9, 9)     # Bottom-Right (Yellow)
    ]
    for col, gx, gy in colors:
        cx, cy = x + gx*tile_w, y + gy*tile_h
        # Yard base
        p.setBrush(QColor(col)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(QRectF(cx, cy, yard_size, yard_size))
        # Inner white patch
        p.setBrush(QColor(255,255,255,180))
        p.drawRoundedRect(QRectF(cx + tile_w, cy + tile_h, 4*tile_w, 4*tile_h), 8, 8)
        # 4 Token starting circles
        p.setBrush(QColor(col))
        for ox, oy in [(1.5, 1.5), (3.5, 1.5), (1.5, 3.5), (3.5, 3.5)]:
            p.drawEllipse(QPointF(cx + ox*tile_w, cy + oy*tile_h), tile_w*0.6, tile_h*0.6)

    # ── Track (The Cross)
    p.setPen(QPen(QColor(PALETTE["text"]), 0.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    
    # Draw grid for the track parts
    for i in range(15):
        for j in range(15):
            # Only draw in the track regions (not in yards or center)
            in_yard = (i < 6 and j < 6) or (i > 8 and j < 6) or (i < 6 and j > 8) or (i > 8 and j > 8)
            in_center = (i >= 6 and i <= 8 and j >= 6 and j <= 8)
            if not in_yard and not in_center:
                rect = QRectF(x + i*tile_w, y + j*tile_h, tile_w, tile_h)
                # Color some specific squares (Home rows and start squares)
                # Red start
                if i==1 and j==6: p.setBrush(QColor(PALETTE["error"]))
                # Green start
                elif i==8 and j==1: p.setBrush(QColor(PALETTE["primary"]))
                # Blue start
                elif i==6 and j==13: p.setBrush(QColor(PALETTE["secondary"]))
                # Yellow start
                elif i==13 and j==8: p.setBrush(QColor(PALETTE["tertiary"]))
                # Home rows
                elif i>0 and i<6 and j==7: p.setBrush(QColor(PALETTE["error"]))
                elif j>0 and j<6 and i==7: p.setBrush(QColor(PALETTE["primary"]))
                elif i>8 and i<14 and j==7: p.setBrush(QColor(PALETTE["tertiary"]))
                elif j>8 and j<14 and i==7: p.setBrush(QColor(PALETTE["secondary"]))
                else: p.setBrush(Qt.BrushStyle.NoBrush)
                
                p.drawRect(rect)
                
    # ── Center Area
    center_rect = QRectF(x + 6*tile_w, y + 6*tile_h, 3*tile_w, 3*tile_h)
    p.setBrush(QColor(PALETTE["surface_highest"]))
    p.drawRect(center_rect)
    # Triangles in center
    poly = QPainterPath()
    poly.moveTo(x+7.5*tile_w, y+7.5*tile_h)
    poly.lineTo(x+6*tile_w, y+6*tile_h); poly.lineTo(x+6*tile_w, y+9*tile_h)
    p.setBrush(QColor(PALETTE["error"])); p.drawPath(poly)
    
    poly = QPainterPath(); poly.moveTo(x+7.5*tile_w, y+7.5*tile_h)
    poly.lineTo(x+6*tile_w, y+6*tile_h); poly.lineTo(x+9*tile_w, y+6*tile_h)
    p.setBrush(QColor(PALETTE["primary"])); p.drawPath(poly)

    # ── Animated Token
    t = (f % 50) / 50.0
    # Move from Red yard to center row
    p.setBrush(QColor(PALETTE["error"]))
    p.setPen(QPen(Qt.GlobalColor.white, 2))
    tok_x = x + tile_w * (1 + t*10)
    tok_y = y + tile_h * 7.5
    p.drawEllipse(QPointF(tok_x, tok_y), tile_w*0.5, tile_h*0.5)

def _p_memory(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    cols,rows=4,3; cw=r.width()/cols; ch=r.height()/rows
    emojis=["🐶","🐱","🐶","🐰","🐱","🦊","🐰","🦊","?","?","?","?"]
    p.setFont(QFont("Plus Jakarta Sans",max(7,int(cw*0.30))))
    for i,em in enumerate(emojis):
        c,row=divmod(i,cols)
        rx=r.x()+row*cw+4; ry=r.y()+c*ch+4
        show=em!="?"
        p.setBrush(QColor(PALETTE["surface_mid"] if not show else PALETTE["surface_highest"]))
        p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(QRectF(rx,ry,cw-8,ch-8),12,12)
        if show:
            p.setPen(QColor(PALETTE["text"]))
            p.drawText(QRectF(rx,ry,cw-8,ch-8),Qt.AlignmentFlag.AlignCenter,em)
        else:
            p.setPen(QColor(PALETTE["primary"]))
            p.drawText(QRectF(rx,ry,cw-8,ch-8),Qt.AlignmentFlag.AlignCenter,"?")

def _p_hangman(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    w,h=r.width(),r.height(); x,y=r.x(),r.y()
    p.setPen(QPen(QColor(PALETTE["secondary"]), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(x+w*0.2,y+h*0.9),QPointF(x+w*0.8,y+h*0.9))
    p.drawLine(QPointF(x+w*0.35,y+h*0.9),QPointF(x+w*0.35,y+h*0.1))
    p.drawLine(QPointF(x+w*0.35,y+h*0.1),QPointF(x+w*0.6,y+h*0.1))
    p.drawLine(QPointF(x+w*0.6,y+h*0.1),QPointF(x+w*0.6,y+h*0.25))
    # Figure - vibrant peach
    p.setPen(QPen(QColor(PALETTE["tertiary"]), 3))
    p.drawEllipse(QPointF(x+w*0.6,y+h*0.32),w*0.08,h*0.08)
    p.drawLine(QPointF(x+w*0.6,y+h*0.40),QPointF(x+w*0.6,y+h*0.65))

def _p_words(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_mid"]))
    letters=["ARCADE","HUBMOD","ERNLAY","EDITOR","IALFUN"]
    cols,rows=6,5; cw=r.width()/cols; ch=r.height()/rows
    n_lit=min(5,(f//12)%6+1)
    p.setFont(QFont("Plus Jakarta Sans",max(6,int(cw*0.42)),QFont.Weight.Bold))
    for row in range(rows):
        for col in range(min(cols,len(letters[row]))):
            letter=letters[row][col]; cx=r.x()+col*cw; cy=r.y()+row*ch
            if col < n_lit and row == 0:
                p.setBrush(QColor(PALETTE["primary"])); p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(QRectF(cx+2,cy+2,cw-4,ch-4),8,8)
                p.setPen(QColor(PALETTE["bg"]))
            else:
                p.setPen(QColor(PALETTE["text"]))
            p.drawText(QRectF(cx,cy,cw,ch),Qt.AlignmentFlag.AlignCenter,letter)

def _p_mine(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    cols,rows=6,5; cw=r.width()/cols; ch=r.height()/rows
    revealed={(0,0),(1,1),(2,0),(3,2),(4,1)}
    mines={(1,1),(3,2)}
    p.setFont(QFont("Plus Jakarta Sans",max(6,int(cw*0.42)),QFont.Weight.Bold))
    for row in range(rows):
        for col in range(cols):
            rx=r.x()+col*cw+2; ry=r.y()+row*ch+2; pos=(col,row)
            if pos in revealed:
                p.setBrush(QColor(PALETTE["surface_highest"] if pos not in mines else PALETTE["error"]))
                p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(QRectF(rx,ry,cw-4,ch-4),10,10)
                if pos in mines: p.drawText(QRectF(rx,ry,cw-4,ch-4),Qt.AlignmentFlag.AlignCenter,"💣")
                else: 
                    p.setPen(QColor(PALETTE["secondary"]))
                    p.drawText(QRectF(rx,ry,cw-4,ch-4),Qt.AlignmentFlag.AlignCenter,"1")
            else:
                p.setBrush(QColor(PALETTE["surface_mid"]))
                p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(QRectF(rx,ry,cw-4,ch-4),10,10)

def _p_spider(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor("#124d35")) # Deep felt green
    # Subtle felt texture
    p.setPen(QPen(QColor(255,255,255,10), 1))
    for i in range(0, int(r.width()), 15): p.drawLine(QPointF(r.x()+i, r.y()), QPointF(r.x()+i, r.y()+r.height()))
    
    cols = 8; cw = r.width() / cols
    for col in range(cols):
        x = r.x() + col*cw + 4; n = 4 + (col % 3)
        for i in range(n):
            y = r.y() + 10 + i*14
            # Card body
            is_top = (i == n-1)
            p.setBrush(QColor(PALETTE["surface_bright"] if is_top else "#1a2a4e"))
            p.setPen(QPen(QColor(255,255,255,30), 0.5))
            p.drawRoundedRect(QRectF(x, y, cw-8, 45), 6, 6)
            if is_top:
                p.setPen(QColor(PALETTE["secondary"]))
                p.setFont(QFont("Plus Jakarta Sans", 8, QFont.Weight.Bold))
                p.drawText(QRectF(x+2, y+2, cw-12, 15), Qt.AlignmentFlag.AlignLeft, "♠")

def _p_breakout(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    brick_cols=7; bw=r.width()/brick_cols; bh=16
    colors=[PALETTE["error"], PALETTE["tertiary"], PALETTE["primary"], PALETTE["secondary"]]
    for row in range(4):
        for col in range(brick_cols):
            p.setBrush(QColor(colors[row])); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(r.x()+col*bw+2,r.y()+10+row*(bh+4),bw-4,bh),4,4)
    p.setBrush(QColor(PALETTE["secondary"]))
    p.drawRoundedRect(QRectF(r.x()+r.width()*0.3,r.y()+r.height()*0.85,r.width()*0.4,10),5,5)

def _p_whack(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_mid"]))
    cols,rows=3,3; cw=r.width()/cols; ch=r.height()/rows
    active=(f//20)%9
    for row in range(rows):
        for col in range(cols):
            cx=r.x()+(col+0.5)*cw; cy=r.y()+(row+0.5)*ch
            p.setBrush(QColor(PALETTE["surface_low"])); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx,cy),cw*0.35,ch*0.35)
            if idx:=col+row*cols==active:
                p.drawText(QRectF(cx-cw*0.3,cy-ch*0.3,cw*0.6,ch*0.6),Qt.AlignmentFlag.AlignCenter,"🐹")

def _p_reaction(p, r, f):
    from hub.core.theme import PALETTE
    phase=(f//40)%3
    bg_t= [PALETTE["error_con"], PALETTE["primary"], PALETTE["surface_highest"]]
    p.fillRect(r, QColor(bg_t[phase]))
    p.setPen(QColor(PALETTE["bg"] if phase==1 else PALETTE["text"]))
    p.setFont(QFont("Plus Jakarta Sans", 16, QFont.Weight.Bold))
    p.drawText(r, Qt.AlignmentFlag.AlignCenter, ["⏳ Wait", "⚡ CLICK", "✅ 180ms"][phase])

def _p_tower(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    colors=[PALETTE["primary"], PALETTE["secondary"], PALETTE["tertiary"], PALETTE["error"]]
    # Shifting camera animation
    cam_y = math.sin(f*0.05) * 10
    for i in range(6):
        w = r.width()*(0.7 - (i%4)*0.1)
        bh = 18; bx = r.x() + (r.width()-w)/2
        by = r.y() + r.height() - (i+1)*(bh+4) + cam_y
        p.setBrush(QColor(colors[i%len(colors)])); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(bx, by, w, bh), 6, 6)
    # Active moving block
    ax = r.x() + (r.width() - 60)/2 + math.sin(f*0.15) * (r.width()*0.3)
    p.setBrush(QColor(255,255,255,180))
    p.drawRoundedRect(QRectF(ax, r.y()+40+cam_y, 60, 18), 6, 6)

def _p_solitaire(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor("#145a32")) # Classic felt
    # Foundation slots
    p.setPen(QPen(QColor(255,255,255,40), 1.5, Qt.PenStyle.DashLine))
    p.setBrush(Qt.BrushStyle.NoBrush)
    cw, ch = 50, 70
    for i in range(3):
        p.drawRoundedRect(QRectF(r.x() + r.width()*0.5 + i*20, r.y()+20, cw, ch), 8, 8)
    
    # Hero card (Ace)
    ax, ay = r.x() + 30, r.y() + 40
    p.setBrush(QColor(255,255,255)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(ax, ay, cw*1.2, ch*1.2), 10, 10)
    p.setPen(QColor("#000000"))
    p.setFont(QFont("Plus Jakarta Sans", 18, QFont.Weight.Bold))
    p.drawText(QRectF(ax, ay, cw*1.2, ch*1.2), Qt.AlignmentFlag.AlignCenter, "♠")
    p.setFont(QFont("Plus Jakarta Sans", 8, QFont.Weight.Bold))
    p.drawText(QRectF(ax+5, ay+5, 15, 15), Qt.AlignmentFlag.AlignLeft, "A")

def _p_2048(p, r, f):
    from hub.core.theme import PALETTE
    p.fillRect(r, QColor(PALETTE["surface_low"]))
    cw, ch = r.width()/4, r.height()/4
    for i in range(4):
        for j in range(3):
            p.setBrush(QColor(PALETTE["surface_mid"]))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(r.x()+i*cw+2,r.y()+j*ch+2,cw-4,ch-4),8,8)
    p.setBrush(QColor(PALETTE["primary"]))
    p.drawRoundedRect(QRectF(r.x()+cw+2,r.y()+ch+2,cw-4,ch-4),8,8)
    p.setPen(QColor(PALETTE["bg"]))
    p.setFont(QFont("Plus Jakarta Sans", 10, QFont.Weight.Bold))
    p.drawText(QRectF(r.x()+cw+2,r.y()+ch+2,cw-4,ch-4), Qt.AlignmentFlag.AlignCenter, "2048")

_PREVIEWS = {
    "tic_tac_toe":      _p_tic,
    "connect4":         _p_c4,
    "snake":            _p_snake,
    "ludo":             _p_ludo,
    "memory_match":     _p_memory,
    "hangman":          _p_hangman,
    "word_search":      _p_words,
    "minesweeper":      _p_mine,
    "spider_solitaire": _p_spider,
    "klondike":         _p_solitaire,
    "breakout":         _p_breakout,
    "whack_a_mole":     _p_whack,
    "reaction_time":    _p_reaction,
    "tower_stacking":   _p_tower,
    "puzzle_2048":      _p_2048,
}


# ── Animated GamePreview widget ───────────────────────────────────────────────

class GamePreview(QWidget):
    def __init__(self, game_key: str, accent: str, parent=None):
        super().__init__(parent)
        self._key   = game_key
        self._accent = QColor(accent)
        self._frame  = 0
        self.setFixedHeight(180)          # Even taller
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        t = QTimer(self); t.timeout.connect(self._tick); t.start(60)

    def _tick(self):
        self._frame += 1; self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        path = QPainterPath(); path.addRoundedRect(r, 32, 32)
        p.setClipPath(path)
        
        fn = _PREVIEWS.get(self._key)
        if fn: fn(p, r, self._frame)
        
        # Subtle accent glow border
        p.setClipping(False)
        p.setPen(QPen(QColor(self._accent.red(),self._accent.green(),
                             self._accent.blue(), 40), 2))
        p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)


# ── Dashboard screen ──────────────────────────────────────────────────────────

class DashboardScreen(QWidget):
    open_game    = pyqtSignal(str)
    open_settings = pyqtSignal()

    def __init__(self, registry, storage, parent=None):
        super().__init__(parent)
        self.registry = registry; self.storage = storage
        self._animated_widgets: list[QWidget] = []

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 40, 40, 40) # Larger margins
        main.setSpacing(32)
        main.addWidget(self._build_topbar())

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        canvas = QWidget(); content = QVBoxLayout(canvas)
        content.setContentsMargins(0, 0, 10, 0); content.setSpacing(40)
        content.addWidget(self._build_hero())
        content.addWidget(self._build_library())
        content.addStretch(1)
        
        scroll.setWidget(canvas); main.addWidget(scroll, 1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        for i, w in enumerate(self._animated_widgets):
            animate_reveal(w, delay_ms=i * 60)

    def _build_topbar(self):
        panel = QFrame(); panel.setObjectName("GlassCard")
        panel.setFixedHeight(120)
        lay = QHBoxLayout(panel); lay.setContentsMargins(32, 0, 32, 0)

        left = QVBoxLayout(); left.setSpacing(4); left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag = QLabel("WELCOME BACK")
        tag.setObjectName("TagLabel")
        left.addWidget(tag)
        title = QLabel("Dashboard")
        title.setObjectName("TitleLabel")
        left.addWidget(title)
        lay.addLayout(left); lay.addStretch(1)

        # High-End Stats
        total_games = len(self.registry)
        played = sum(1 for k in self.registry if self.storage.high_score(k) > 0)
        for txt, col in [
            (f"🕹️ {total_games} Games", PALETTE["primary"]),
            (f"✨ {played} Explore", PALETTE["secondary"]),
        ]:
            chip = StatChip(txt, col)
            lay.addWidget(chip)

        self._animated_widgets.append(panel)
        return panel

    def _build_hero(self):
        hero = QFrame(); hero.setObjectName("Card")
        hero.setFixedHeight(400)
        lay = QHBoxLayout(hero); lay.setContentsMargins(48, 48, 48, 48); lay.setSpacing(40)

        txt_side = QVBoxLayout(); txt_side.setSpacing(16)
        tag = QLabel("FEATURED TONIGHT")
        tag.setObjectName("TagLabel")
        txt_side.addWidget(tag)

        title = QLabel("Experience the\nElevated Playground.")
        title.setObjectName("TitleLabel"); title.setStyleSheet("font-size: 42px; line-height: 1.1;")
        txt_side.addWidget(title)

        sub = QLabel("A curated collection of modern arcade classics with lush animations and tonal depth.")
        sub.setObjectName("MutedLabel"); sub.setWordWrap(True); sub.setFixedWidth(400)
        txt_side.addWidget(sub)

        btns = QHBoxLayout(); btns.setSpacing(16)
        play = NeonButton("▶  EXPLORE NOW", primary=True); play.setFixedHeight(56); play.setFixedWidth(200)
        play.clicked.connect(lambda: self.open_game.emit("ludo"))
        btns.addWidget(play); btns.addStretch(1)
        txt_side.addLayout(btns)
        lay.addLayout(txt_side, 2)

        # Scores Recessed Panel
        scores_frame = QFrame(); scores_frame.setObjectName("PanelCard")
        scores_frame.setFixedWidth(320)
        sl = QVBoxLayout(scores_frame); sl.setContentsMargins(28,28,28,28); sl.setSpacing(12)
        sh = QLabel("🏆 Best Scores")
        sh.setObjectName("SectionLabel"); sl.addWidget(sh)
        for key, meta in list(self.registry.items())[:5]:
            best = self.storage.high_score(key)
            row = QHBoxLayout()
            nm = QLabel(meta["title"]); nm.setStyleSheet("font-weight: 600;")
            row.addWidget(nm, 1)
            sc = QLabel(str(best) if best > 0 else "—")
            sc.setStyleSheet(f"color: {PALETTE['primary']}; font-weight: 800;")
            row.addWidget(sc); sl.addLayout(row)
        lay.addWidget(scores_frame, 1)
        
        self._animated_widgets.append(hero)
        return hero

    def _build_library(self):
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper); wl.setContentsMargins(0,0,0,0); wl.setSpacing(24)

        hdr = QHBoxLayout(); title = QLabel("All Experiences"); title.setObjectName("SectionLabel")
        hdr.addWidget(title); hdr.addStretch(1); wl.addLayout(hdr)

        grid_w = QWidget()
        grid = QGridLayout(grid_w); grid.setSpacing(24)
        for i in range(3): grid.setColumnStretch(i, 1)

        for idx, meta in enumerate(self.registry.values()):
            card = QFrame(); card.setObjectName("Card")
            card.setMinimumHeight(420)
            cl = QVBoxLayout(card); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)

            preview = GamePreview(meta["key"], meta["accent"])
            cl.addWidget(preview)

            info = QWidget(); il = QVBoxLayout(info); il.setContentsMargins(24,24,24,24); il.setSpacing(8)
            nm = QLabel(meta["title"]); nm.setStyleSheet(f"color: {meta['accent']}; font-weight: 800; font-size: 20px;")
            il.addWidget(nm)
            desc = QLabel(meta["subtitle"]); desc.setObjectName("MutedLabel"); desc.setWordWrap(True)
            il.addWidget(desc)
            
            btn = NeonButton("OPEN", primary=True); btn.setFixedHeight(48)
            btn.clicked.connect(lambda _=False, gk=meta["key"]: self.open_game.emit(gk))
            il.addStretch(1); il.addWidget(btn)
            cl.addWidget(info)

            grid.addWidget(card, idx//3, idx%3)
            self._animated_widgets.append(card)

        wl.addWidget(grid_w)
        return wrapper
