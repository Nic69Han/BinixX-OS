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
QFrame#hero {{
    border-radius: 20px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {NAVY}, stop:0.55 #1E2E9E, stop:1 {BLUE});
}}
QLabel#heroTitre {{ color: white; font-size: 25pt; font-weight: 700; background: transparent; }}
QLabel#heroTexte {{ color: #C9D6FF; font-size: 10.5pt; background: transparent; }}
QLineEdit#recherche {{
    background: white; color: {INK}; border: 2px solid transparent; border-radius: 23px;
    padding: 9px 14px; font-size: 11.5pt; selection-background-color: {BLUE};
}}
QLineEdit#recherche:focus {{ border-color: {SKY}; }}
QListWidget#categories {{ background: transparent; border: none; outline: 0; font-size: 10.5pt; }}
QListWidget#categories::item {{ padding: 6px 8px; margin: 2px 0; border-radius: 14px; }}
QListWidget#categories::item:hover {{ background: rgba(47,91,255,0.10); }}
QListWidget#categories::item:selected {{ background: rgba(47,91,255,0.20); color: palette(text); }}
QFrame#tuile {{
    background: palette(base); border: 1px solid rgba(128,128,128,0.30); border-radius: 18px;
}}
QFrame#tuile:hover {{ border: 1px solid {BLUE}; background: rgba(47,91,255,0.07); }}
QFrame#tuile:focus {{ border: 2px solid {BLUE}; }}
QFrame#tuile[appuye="true"] {{ background: rgba(47,91,255,0.17); }}
QFrame#tuile[info="true"] {{ background: transparent; border: 1px dashed rgba(128,128,128,0.50); }}
QFrame#tuile[info="true"]:hover {{ background: transparent; border: 1px dashed rgba(128,128,128,0.50); }}
QLabel#tuileTitre {{ font-size: 11.5pt; font-weight: 600; background: transparent; }}
QLabel#tuileTexte {{ font-size: 9.5pt; background: transparent; }}
QLabel#tuileCategorie {{ font-size: 8pt; font-weight: 700; background: transparent; }}
QLabel#etiquette {{
    color: white; background: {BLUE}; border-radius: 11px; padding: 3px 11px; font-size: 9pt; font-weight: 600;
}}
QPushButton#lien {{ background: transparent; border: none; color: {BLUE}; font-weight: 600; padding: 6px 4px; }}
QPushButton#lien:hover {{ text-decoration: underline; }}
"""
