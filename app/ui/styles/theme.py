"""
EdgeScholar — Creative Editorial & Studio Theme.

An anti-AI, humanistic, tactile design system inspired by physical notebooks,
editorial typography (Charter/Georgia), and calm craftsmanship (Things 3 / Bear / iA Writer).
No noisy cyberpunk neon; instead: warm matte charcoal, linen hairline borders,
subtle honey amber accents, and distraction-free breathing room.
"""
from __future__ import annotations

# ── Color Palette: Warm Studio Canvas ──
BG_CANVAS = "#111216"         # Warm deep charcoal
BG_SURFACE = "#181920"        # Calm tactile paper surface
BG_ELEVATED = "#21222b"       # Elevated warm card
BG_HOVER = "#2a2b37"          # Subtle hover state
BG_CARD = "#1c1d25"

# Warm organic accents
ACCENT_HONEY = "#e59837"      # Warm honey amber
ACCENT_HONEY_HOVER = "#f5a847"
ACCENT_HONEY_PRESSED = "#c97f26"

SNAPDRAGON_RED = "#d9383a"    # Refined terracotta crimson
SNAPDRAGON_RED_HOVER = "#e5484a"
SNAPDRAGON_RED_PRESSED = "#b5282a"

QUALCOMM_CYAN = "#38bdf8"     # Soft sky cyan
ACCENT_SAGE = "#34d399"       # Muted sage green

# Semantic status colors
STATUS_GREEN = "#10b981"      # Calm emerald
STATUS_AMBER = "#f59e0b"      # Muted amber
STATUS_RED = "#ef4444"        # Soft coral red

# Borders
BORDER_SUBTLE = "#272935"     # Fine bookbinding divider
BORDER_ACTIVE = "#3d4052"     # Focused border
BORDER_WARM = "#383a49"

# Typography
TEXT_PRIMARY = "#f4f4f6"      # Soft book-paper white (not harsh #fff)
TEXT_SECONDARY = "#a1a1aa"    # Warm linen silver
TEXT_MUTED = "#71717a"        # Soft pencil graphite
TEXT_HEADING = "#fafafa"

# Font hierarchy
FONT_SERIF = "'Charter', 'Georgia', 'Iowan Old Style', 'Times New Roman', serif"
FONT_SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif"
FONT_MONO = "'SF Mono', 'JetBrains Mono', Consolas, monospace"

# ── Backward Compatibility Aliases ──
BG_DARK = BG_CANVAS
ACCENT = ACCENT_HONEY
ACCENT_HOVER = ACCENT_HONEY_HOVER
ACCENT_PRESSED = ACCENT_HONEY_PRESSED
BORDER = BORDER_SUBTLE
SUCCESS = STATUS_GREEN
WARNING = STATUS_AMBER
ERROR = STATUS_RED
CITATION_BG = "#1e1f29"


CREATIVE_STYLESHEET = f"""
/* ── Studio Reset ── */
QWidget {{
    background-color: {BG_CANVAS};
    color: {TEXT_PRIMARY};
    font-family: {FONT_SANS};
    font-size: 13px;
    selection-background-color: {ACCENT_HONEY};
    selection-color: #111216;
}}

/* ── Left Shelf / Sidebar ── */
#sidebar {{
    background-color: {BG_SURFACE};
    border-right: 1px solid {BORDER_SUBTLE};
}}

#sidebar_brand {{
    color: {TEXT_HEADING};
    font-family: {FONT_SERIF};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}

#sidebar_subtitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-style: italic;
}}

/* ── Shelf Items (Clean Notebook Style) ── */
QPushButton#shelf_btn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    color: {TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#shelf_btn:hover {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}
QPushButton#shelf_btn[active="true"] {{
    background-color: {BG_ELEVATED};
    color: {ACCENT_HONEY};
    font-weight: 700;
    border-left: 3px solid {ACCENT_HONEY};
    border-radius: 0px 8px 8px 0px;
}}

QPushButton#nav_btn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    color: {TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav_btn:hover {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}
QPushButton#nav_btn[active="true"] {{
    background-color: {BG_ELEVATED};
    color: {ACCENT_HONEY};
    font-weight: 700;
    border-left: 3px solid {ACCENT_HONEY};
    border-radius: 0px 8px 8px 0px;
}}

/* ── Clean Paper Cards ── */
#card, QFrame#card {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 12px;
    padding: 18px;
}}
#card:hover {{
    border-color: {BORDER_WARM};
}}

#hero_banner {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e1b18, stop:0.5 #181920, stop:1 #131418);
    border: 1px solid #332b22;
    border-radius: 14px;
    padding: 24px;
}}

/* ── Warm Handcrafted Buttons ── */
QPushButton#primary_btn {{
    background-color: {ACCENT_HONEY};
    color: #111216;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 700;
    font-size: 13px;
}}
QPushButton#primary_btn:hover {{
    background-color: {ACCENT_HONEY_HOVER};
}}
QPushButton#primary_btn:pressed {{
    background-color: {ACCENT_HONEY_PRESSED};
}}
QPushButton#primary_btn:disabled {{
    background-color: {BG_ELEVATED};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_SUBTLE};
}}

QPushButton#secondary_btn {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#secondary_btn:hover {{
    background-color: {BG_HOVER};
    border-color: {BORDER_ACTIVE};
    color: {TEXT_HEADING};
}}
QPushButton#secondary_btn:pressed {{
    background-color: #1a1b22;
}}
QPushButton#secondary_btn:disabled {{
    background-color: {BG_CANVAS};
    color: {TEXT_MUTED};
    border-color: {BORDER_SUBTLE};
}}

/* ── Minimal Text Editor & Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 8px;
    padding: 10px 14px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
    line-height: 1.6;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {ACCENT_HONEY};
    background-color: #1b1c23;
}}

/* ── Dropdowns ── */
QComboBox {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 8px;
    padding: 6px 14px;
    color: {TEXT_PRIMARY};
    font-weight: 500;
    min-height: 24px;
}}
QComboBox:hover {{
    border-color: {BORDER_ACTIVE};
}}
QComboBox:focus {{
    border-color: {ACCENT_HONEY};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_ACTIVE};
    border-radius: 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_HONEY};
    selection-color: #111216;
    padding: 4px;
}}

/* ── Study Desk Segmented Modes / Tab Bar ── */
QTabWidget::pane {{
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 10px;
    background-color: {BG_SURFACE};
    top: -1px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    padding: 9px 20px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 13px;
    margin-right: 4px;
}}
QTabBar::tab:selected {{
    color: {ACCENT_HONEY};
    border-bottom: 2px solid {ACCENT_HONEY};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRIMARY};
}}

/* ── Minimal Tables ── */
QTableWidget {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 10px;
    gridline-color: {BORDER_SUBTLE};
    color: {TEXT_PRIMARY};
}}
QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {BORDER_SUBTLE};
}}
QTableWidget::item:selected {{
    background-color: rgba(229, 152, 55, 0.15);
    color: #ffffff;
}}
QHeaderView::section {{
    background-color: {BG_ELEVATED};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {BORDER_SUBTLE};
    padding: 9px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}}

/* ── Soft Progress Bar ── */
QProgressBar {{
    background-color: {BG_ELEVATED};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {ACCENT_HONEY};
    border-radius: 3px;
}}

/* ── Minimal Scrollbars ── */
QScrollBar:vertical {{
    background: {BG_CANVAS};
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_ACTIVE};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {BG_CANVAS};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_ACTIVE};
    border-radius: 3px;
}}

/* ── Warm Tactile Badges ── */
#badge_snapdragon {{
    background-color: rgba(229, 152, 55, 0.12);
    border: 1px solid rgba(229, 152, 55, 0.35);
    border-radius: 6px;
    color: {ACCENT_HONEY};
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
}}

#badge_npu {{
    background-color: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 6px;
    color: {QUALCOMM_CYAN};
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
}}

#badge_verified {{
    background-color: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 6px;
    color: {STATUS_GREEN};
    font-weight: 700;
    font-size: 11px;
    padding: 3px 8px;
}}

/* ── Humanistic Editorial Typography ── */
#heading_label {{
    color: {TEXT_HEADING};
    font-family: {FONT_SERIF};
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.4px;
}}
#subheading_label {{
    color: {TEXT_PRIMARY};
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.2px;
}}
#caption_label {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QSplitter::handle {{
    background-color: {BORDER_SUBTLE};
}}
"""


def get_stylesheet() -> str:
    return CREATIVE_STYLESHEET
