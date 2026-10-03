"""Couleurs et styles de BinixX OS (voir branding/generer.py et docs/identite-visuelle.md)."""

INK = "#0B0F1A"
NAVY = "#10163A"
BLUE = "#2F5BFF"
SKY = "#5FB2FF"

# Un couple (foncé, clair) par couleur : l'en-tête, les liserés et les pastilles de chaque page, et les catégories de
# Paramètres. Les noms servent de clés (page.COULEURS = ACCENTS["orange"]).
ACCENTS = {
    "bleu": (BLUE, SKY),
    "indigo": ("#4F46E5", "#818CF8"),
    "violet": ("#7C3AED", "#A78BFA"),
    "rose": ("#DB2777", "#F472B6"),
    "rouge": ("#DC2626", "#F87171"),
    "orange": ("#EA580C", "#FB923C"),
    "ambre": ("#D97706", "#FBBF24"),
    "vert": ("#059669", "#34D399"),
    "sarcelle": ("#0F766E", "#2DD4BF"),
    "cyan": ("#0891B2", "#22D3EE"),
    "fuchsia": ("#A21CAF", "#E879F9"),
    "bleu-fonce": ("#1D4ED8", "#60A5FA"),
    "lime": ("#4D7C0F", "#A3E635"),
    "ardoise": ("#475569", "#94A3B8"),
}

STYLE = f"""
QWidget#sidebar {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {NAVY}, stop:1 {INK}); }}
QLabel#sidebarTitle {{ color: white; font-size: 18pt; font-weight: 600; }}
QLabel#sidebarSubtitle {{ color: #AEB8E6; font-size: 9pt; }}
QPushButton#nav {{
    color: #DDE4FF; background: transparent; border: none; border-radius: 12px;
    text-align: left; padding: 5px 8px; font-size: 10pt;
}}
QPushButton#nav:hover {{ background: rgba(255,255,255,0.08); }}
QPushButton#nav:checked {{
    color: white; font-weight: 600;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE}, stop:1 #3F6BFF);
}}
QLabel#pageTitle {{ font-size: 22pt; font-weight: 600; }}
QLabel#pageLead {{ font-size: 11pt; }}
QLabel#sectionTitle {{ font-size: 13pt; font-weight: 700; padding-left: 14px; }}
QFrame#card {{ border: 1px solid rgba(128,128,128,0.30); border-radius: 16px; background: palette(base); }}
QFrame#card:hover {{ border-color: {BLUE}; background: rgba(47,91,255,0.04); }}
QLabel#cardTitle {{ font-size: 11.5pt; font-weight: 600; background: transparent; border: none; }}
QPushButton#primary {{
    background: {BLUE}; color: white; border: none; border-radius: 14px; padding: 7px 18px; font-weight: 600;
}}
QPushButton#secondaire {{
    background: palette(base); color: palette(text); border: 1px solid rgba(128,128,128,0.50); border-radius: 14px;
    padding: 6px 16px; font-weight: 600;
}}
QPushButton#secondaire:hover {{ border-color: {BLUE}; color: {BLUE}; }}
QPushButton#secondaire:disabled {{ color: rgba(128,128,128,0.8); border-color: rgba(128,128,128,0.25); }}
QPushButton#primary:hover {{ background: #4A71FF; }}
QPushButton#primary:pressed {{ background: #2447D6; }}
QPushButton#primary:disabled {{ background: rgba(128,128,128,0.35); color: rgba(255,255,255,0.75); }}
QPushButton#primary:focus {{ border: 2px solid {SKY}; }}
QFrame#barre {{ background: palette(base); border-top: 1px solid rgba(128,128,128,0.30); }}
QLabel#installee {{ color: #047857; font-weight: 600; }}
QProgressBar {{ border: none; border-radius: 4px; background: rgba(128,128,128,0.25); }}
QProgressBar::chunk {{ border-radius: 4px; background: {BLUE}; }}
QLabel#bandeau {{
    background: rgba(47,91,255,0.10); border: 1px solid rgba(47,91,255,0.40); border-radius: 14px; padding: 12px 16px;
}}
QLabel#heroTitre {{ color: white; font-size: 23pt; font-weight: 700; background: transparent; }}
QLabel#heroTexte {{ color: rgba(255,255,255,0.86); font-size: 10.5pt; background: transparent; }}
QLineEdit#recherche {{
    background: white; color: {INK}; border: 2px solid transparent; border-radius: 23px;
    padding: 9px 14px; font-size: 11.5pt; selection-background-color: {BLUE};
}}
QLineEdit#recherche:focus {{ border-color: {SKY}; }}
QListWidget#categories {{ background: transparent; border: none; outline: 0; font-size: 10.5pt; }}
QListWidget#categories::item {{ padding: 4px 8px; margin: 1px 0; border-radius: 14px; }}
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
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: rgba(128,128,128,0.45); border-radius: 4px; min-height: 36px; }}
QScrollBar::handle:horizontal {{ background: rgba(128,128,128,0.45); border-radius: 4px; min-width: 36px; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ background: rgba(128,128,128,0.75); }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""

