"""Fonds « verre fumé » de BinixX OS pour le thème Plasma : barre des tâches, menus et fenêtres de Plasma, bulles d'aide.

Plasma dessine ces fonds à partir d'une image SVG découpée en neuf morceaux (KSvg::FrameSvg) : quatre coins, quatre bords et le
centre, repérés par leur « id » (topleft, top, …, center). Les rectangles « hint-*-margin » donnent la marge intérieure (l'écart
entre le bord et le contenu), « shadow-* » l'ombre portée que KWin dessine autour, « shadow-hint-*-margin » sa largeur.

Ce module fabrique ces images, en deux matières, dans la même forme :
  - verre : un fond fumé translucide, lisible parce que KWin floute ce qu'il y a derrière (dossier « translucent/ » du thème, que
    Plasma ne lit que si le flou est actif) ;
  - opaque : le même dessin, plein (dossiers « dialogs/ » et « widgets/ », lus sans flou : machine virtuelle, vieux PC, profil léger).
Un liseré d'un pixel souligne le bord, comme sur les maquettes ; la barre des tâches est une pilule (coins de la moitié de sa hauteur).

    from verre_plasma import FONDS, svg
    svg(FONDS["widgets/panel-background"], MATIERES["dark"]["verre"])
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Forme:
    rayon: int  # rayon des coins, en pixels
    marges: tuple  # marge intérieure : haut, droite, bas, gauche
    ombre: int  # largeur de l'ombre portée
    force_ombre: float  # opacité de l'ombre au ras du bord


@dataclass(frozen=True)
class Matiere:
    fond: str  # couleur du fond (#rrggbb)
    opacite: float  # opacité du fond : moins de 1 pour le verre
    liseret: str  # couleur du liseré du bord
    opacite_liseret: float


# Fonds remplacés, chemin dans le thème sans extension : la barre des tâches (pilule), les menus et fenêtres de Plasma (menu de
# démarrage, calendrier, zone de notification, notifications), les bulles d'aide
FONDS = {
    "widgets/panel-background": Forme(rayon=20, marges=(4, 10, 4, 10), ombre=12, force_ombre=0.28),
    "dialogs/background": Forme(rayon=16, marges=(10, 10, 10, 10), ombre=24, force_ombre=0.34),
    "widgets/tooltip": Forme(rayon=10, marges=(6, 8, 6, 8), ombre=12, force_ombre=0.24),
}

# Couleurs des maquettes « verre fumé » (Nuit) et « verre dépoli » (Aube) ; en opaque, le même ton, plein
MATIERES = {
    "dark": {
        "verre": Matiere(fond="#181822", opacite=0.52, liseret="#ffffff", opacite_liseret=0.10),
        "opaque": Matiere(fond="#1d1f2a", opacite=1.0, liseret="#ffffff", opacite_liseret=0.08),
    },
    "light": {
        "verre": Matiere(fond="#ffffff", opacite=0.66, liseret="#000000", opacite_liseret=0.08),
        "opaque": Matiere(fond="#f5f6fa", opacite=1.0, liseret="#000000", opacite_liseret=0.10),
    },
}

CENTRE = 8  # taille du morceau central et des bords (Plasma les étire)
ECART = 40  # espace entre le cadre et l'ombre dans l'image


def _n(valeur):
    """Nombre sans zéros inutiles (1.0 → 1, 0.50 → 0.5)."""
    return f"{valeur:.4f}".rstrip("0").rstrip(".")


def _rect(ident, x, y, l, h, couleur="#000000", opacite=0.0, extra=""):
    ident = f' id="{ident}"' if ident else ""
    return (f'<rect{ident} x="{_n(x)}" y="{_n(y)}" width="{_n(l)}" height="{_n(h)}" fill="{couleur}" '
            f'fill-opacity="{_n(opacite)}"{extra}/>')


def _coin(ident, x, y, r, sx, sy, m):
    """Coin arrondi de r × r en (x, y) ; (sx, sy) : sens vers l'intérieur du cadre (1 ou -1 sur chaque axe)."""
    # centre du quart de disque : le coin intérieur du morceau
    cx, cy = (x + r if sx > 0 else x), (y + r if sy > 0 else y)
    ax, ay = cx - sx * r, cy  # extrémité de l'arc sur le bord vertical
    bx, by = cx, cy - sy * r  # extrémité sur le bord horizontal
    balayage = 1 if sx * sy > 0 else 0
    fond = (f'<path d="M {_n(cx)} {_n(cy)} L {_n(ax)} {_n(ay)} A {r} {r} 0 0 {balayage} {_n(bx)} {_n(by)} Z" '
            f'fill="{m.fond}" fill-opacity="{_n(m.opacite)}"/>')
    # Liseré : un quart d'anneau d'un pixel, rempli (pas un trait : QtSvg compte la demi-épaisseur d'un trait dans la boîte de
    # l'élément, le coin mesurait alors r + 0,5 px et Plasma laissait un raccord visible entre le coin et les bords)
    ri = r - 1
    liseret = (f'<path d="M {_n(ax)} {_n(ay)} A {r} {r} 0 0 {balayage} {_n(bx)} {_n(by)} '
               f'L {_n(cx)} {_n(cy - sy * ri)} A {ri} {ri} 0 0 {1 - balayage} {_n(cx - sx * ri)} {_n(cy)} Z" '
               f'fill="{m.liseret}" fill-opacity="{_n(m.opacite_liseret)}"/>')
    # rectangle invisible : la boîte du morceau fait exactement r × r
    return f'<g id="{ident}">{_rect("", x, y, r, r)}{fond}{liseret}</g>'


def _bord(ident, x, y, l, h, cote, m):
    """Bord droit de l × h ; cote : où est le liseré (haut, bas, gauche, droite)."""
    lx, ly, ll, lh = {
        "haut": (x, y, l, 1), "bas": (x, y + h - 1, l, 1), "gauche": (x, y, 1, h), "droite": (x + l - 1, y, 1, h),
    }[cote]
    return (f'<g id="{ident}">{_rect("", x, y, l, h, m.fond, m.opacite)}'
            f'{_rect("", lx, ly, ll, lh, m.liseret, m.opacite_liseret)}</g>')


def _cadre(f, m, x0=0, y0=0):
    r, c = f.rayon, CENTRE
    x1, x2, y1, y2 = x0 + r, x0 + r + c, y0 + r, y0 + r + c
    morceaux = [
        _coin("topleft", x0, y0, r, 1, 1, m),
        _bord("top", x1, y0, c, r, "haut", m),
        _coin("topright", x2, y0, r, -1, 1, m),
        _bord("left", x0, y1, r, c, "gauche", m),
        _rect("center", x1, y1, c, c, m.fond, m.opacite),
        _bord("right", x2, y1, r, c, "droite", m),
        _coin("bottomleft", x0, y2, r, 1, -1, m),
        _bord("bottom", x1, y2, c, r, "bas", m),
        _coin("bottomright", x2, y2, r, -1, -1, m),
    ]
    haut, droite, bas, gauche = f.marges
    xm = x0 + 2 * r + c + ECART
    morceaux += [
        _rect("hint-top-margin", xm, y0, 4, haut),
        _rect("hint-right-margin", xm + 10, y0, droite, 4),
        _rect("hint-bottom-margin", xm + 30, y0, 4, bas),
        _rect("hint-left-margin", xm + 40, y0, gauche, 4),
        _rect("hint-stretch-borders", xm + 60, y0, 4, 4),
    ]
    return morceaux


def _degrades(f):
    """Dégradés de l'ombre : du noir (au ras du bord) au transparent."""
    a = f.force_ombre
    arrets = (f'<stop offset="0" stop-color="#000000" stop-opacity="{_n(a)}"/>'
              f'<stop offset="0.45" stop-color="#000000" stop-opacity="{_n(a * 0.4)}"/>'
              f'<stop offset="1" stop-color="#000000" stop-opacity="0"/>')
    lineaires = {"haut": (0, 1, 0, 0), "bas": (0, 0, 0, 1), "gauche": (1, 0, 0, 0), "droite": (0, 0, 1, 0)}
    defs = [f'<linearGradient id="ombre-{cote}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{arrets}</linearGradient>'
            for cote, (x1, y1, x2, y2) in lineaires.items()]
    # coins : l'ombre part de l'arrondi (à r du centre) et s'éteint à r + ombre
    debut = f.rayon / (f.rayon + f.ombre)
    arrets_coin = (f'<stop offset="0" stop-color="#000000" stop-opacity="{_n(a)}"/>'
                   f'<stop offset="{_n(debut)}" stop-color="#000000" stop-opacity="{_n(a)}"/>'
                   f'<stop offset="{_n(debut + (1 - debut) * 0.45)}" stop-color="#000000" stop-opacity="{_n(a * 0.4)}"/>'
                   f'<stop offset="1" stop-color="#000000" stop-opacity="0"/>')
    return defs, arrets_coin


def _ombre(f, x0, y0):
    s, r, c = f.ombre, f.rayon, CENTRE
    k = s + r  # taille d'un coin de l'ombre : l'ombre et l'arrondi du cadre
    defs, arrets_coin = _degrades(f)
    morceaux = []
    coins = {"topleft": (x0, y0, x0 + k, y0 + k), "topright": (x0 + k + c, y0, x0 + k + c, y0 + k),
             "bottomleft": (x0, y0 + k + c, x0 + k, y0 + k + c), "bottomright": (x0 + k + c, y0 + k + c, x0 + k + c, y0 + k + c)}
    for nom, (x, y, cx, cy) in coins.items():
        defs.append(f'<radialGradient id="ombre-{nom}" gradientUnits="userSpaceOnUse" cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(k)}">'
                    f'{arrets_coin}</radialGradient>')
        morceaux.append(f'<rect id="shadow-{nom}" x="{_n(x)}" y="{_n(y)}" width="{k}" height="{k}" fill="url(#ombre-{nom})"/>')
    bords = {"top": (x0 + k, y0, c, s, "haut"), "bottom": (x0 + k, y0 + 2 * k + c - s, c, s, "bas"),
             "left": (x0, y0 + k, s, c, "gauche"), "right": (x0 + 2 * k + c - s, y0 + k, s, c, "droite")}
    for nom, (x, y, l, h, cote) in bords.items():
        morceaux.append(f'<rect id="shadow-{nom}" x="{_n(x)}" y="{_n(y)}" width="{l}" height="{h}" fill="url(#ombre-{cote})"/>')
    morceaux.append(_rect("shadow-center", x0 + k, y0 + k, c, c))
    xm = x0 + 2 * k + c + ECART
    morceaux += [
        _rect("shadow-hint-top-margin", xm, y0, 4, s),
        _rect("shadow-hint-right-margin", xm + 10, y0, s, 4),
        _rect("shadow-hint-bottom-margin", xm + 50, y0, 4, s),
        _rect("shadow-hint-left-margin", xm + 60, y0, s, 4),
    ]
    return defs, morceaux


def svg(forme, matiere):
    """Image SVG complète d'un fond de Plasma (cadre en neuf morceaux, marges, ombre portée)."""
    cadre = _cadre(forme, matiere)
    y_ombre = 2 * forme.rayon + CENTRE + ECART
    defs, ombre = _ombre(forme, 0, y_ombre)
    largeur = max(2 * forme.rayon + CENTRE, 2 * (forme.ombre + forme.rayon) + CENTRE) + ECART + 120
    hauteur = y_ombre + 2 * (forme.ombre + forme.rayon) + CENTRE
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{largeur}" height="{hauteur}" '
            f'viewBox="0 0 {largeur} {hauteur}">\n'
            '<!-- BinixX OS : fond « verre fumé » fabriqué par build_files/verre_plasma.py (Apache-2.0) -->\n'
            f'<defs>{"".join(defs)}</defs>\n' + "\n".join(cadre + ombre) + "\n</svg>\n")
