"""Couleurs et styles de NicOS (voir branding/generer.py et docs/identite-visuelle.md)."""

INK = "#0B0F1A"
NAVY = "#10163A"
BLUE = "#2F5BFF"
SKY = "#5FB2FF"

STYLE = f"""
QWidget#sidebar {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {NAVY}, stop:1 {INK}); }}
QLabel#sidebarTitle {{ color: white; font-size: 18pt; font-weight: 600; }}
QLabel#sidebarSubtitle {{ color: #AEB8E6; font-size: 9pt; }}
QPushButton#nav {{
    color: #DDE4FF; background: transparent; border: none; border-radius: 8px;
    text-align: left; padding: 10px 14px; font-size: 11pt;
}}
QPushButton#nav:hover {{ background: rgba(255,255,255,0.08); }}
QPushButton#nav:checked {{ background: {BLUE}; color: white; }}
QLabel#pageTitle {{ font-size: 22pt; font-weight: 600; }}
QLabel#pageLead {{ font-size: 11pt; }}
QLabel#sectionTitle {{ font-size: 13pt; font-weight: 600; }}
QFrame#card {{ border: 1px solid palette(mid); border-radius: 12px; background: palette(base); }}
QFrame#card:hover {{ border-color: {BLUE}; }}
QLabel#cardTitle {{ font-size: 11.5pt; font-weight: 600; }}
QPushButton#primary {{
    background: {BLUE}; color: white; border: none; border-radius: 8px; padding: 8px 16px; font-weight: 600;
}}
QPushButton#primary:hover {{ background: #4A71FF; }}
"""
