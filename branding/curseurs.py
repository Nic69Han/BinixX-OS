#!/usr/bin/env python3
"""Pointeur de souris BinixX OS : blanc, plat et fin, contour au bleu BinixX pastel, ombre douce (docs/identite-visuelle.md).

Dessine chaque forme en SVG (grille de 32 × 32), la rend à plusieurs tailles et écrit les fichiers Xcursor du thème
« binixx-curseurs » dans system_files/usr/share/icons/binixx-curseurs (index.theme, cursors/ : un fichier par forme et des liens
pour les autres noms qu'utilisent les applications). Les noms absents viennent de Breeze (Inherits=breeze_cursors).

    pip install pyside6-essentials numpy
    python3 branding/curseurs.py

Format Xcursor (libXcursor, « Xcursor file format ») : en-tête, table des images, puis chaque image en ARGB prémultiplié.
"""
import math
import os
import shutil
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
THEME = REPO / "system_files/usr/share/icons/binixx-curseurs"
CONTOUR = "#ADCFFB"  # le bleu BinixX pastel
FORT = "#0C6EEE"  # sa nuance forte : l'arc de l'attente
TAILLES = (24, 32, 48, 64, 96)
IMAGES_ATTENTE = 8
DELAI_MS = 70


def forme(corps, epaisseur=2.2):
    """Contour (la forme épaissie, au pastel) puis la forme en blanc par-dessus : un contour net et fin, sans traits intérieurs."""
    return (f'<g fill="{CONTOUR}" stroke="{CONTOUR}" stroke-width="{epaisseur}" stroke-linejoin="round" stroke-linecap="round">{corps}</g>'
            f'<g fill="#ffffff">{corps}</g>')


def trait(chemin, large=1.3):
    """Un tracé blanc fin cerné de pastel (texte, viseur)."""
    return (f'<path d="{chemin}" fill="none" stroke="{CONTOUR}" stroke-width="{large + 2.1}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{chemin}" fill="none" stroke="#ffffff" stroke-width="{large}" stroke-linecap="round" stroke-linejoin="round"/>')


FLECHE = '<path d="M7 3.6v19.6l4.7-4.4 3.3 7.4 2.5-1.1-3.3-7.3h6.6z"/>'
MAIN = ('<rect x="11.4" y="3" width="3.4" height="15" rx="1.7"/><rect x="14.8" y="10.2" width="3.2" height="8" rx="1.6"/>'
        '<rect x="18" y="11.2" width="3.1" height="7.5" rx="1.55"/><rect x="21.1" y="12.6" width="2.9" height="6.6" rx="1.45"/>'
        '<rect x="10.8" y="14.8" width="13.2" height="12.6" rx="5.2"/>'
        '<rect x="6.8" y="15.2" width="3.2" height="8.6" rx="1.6" transform="rotate(-38 8.4 22.6)"/>')
MAIN_OUVERTE = ('<rect x="10.6" y="6" width="3.2" height="12" rx="1.6"/><rect x="13.8" y="4" width="3.2" height="14" rx="1.6"/>'
                '<rect x="17" y="5" width="3.1" height="13" rx="1.55"/><rect x="20.1" y="7.5" width="2.9" height="11" rx="1.45"/>'
                '<rect x="10.4" y="14.8" width="12.8" height="12.6" rx="5.2"/>'
                '<rect x="6.6" y="13.6" width="3.2" height="8.6" rx="1.6" transform="rotate(-38 8.2 21)"/>')
MAIN_FERMEE = ('<rect x="10.6" y="11" width="3.2" height="7" rx="1.6"/><rect x="13.8" y="10.2" width="3.2" height="7.8" rx="1.6"/>'
               '<rect x="17" y="10.6" width="3.1" height="7.4" rx="1.55"/><rect x="20.1" y="11.6" width="2.9" height="6.6" rx="1.45"/>'
               '<rect x="10.4" y="14.8" width="12.8" height="12.6" rx="5.2"/>'
               '<rect x="7.4" y="15.6" width="3.2" height="7.2" rx="1.6" transform="rotate(-38 9 21)"/>')
DOUBLE_FLECHE = '<path d="M4.5 16l4.6-4.6v3.1h13.8v-3.1l4.6 4.6-4.6 4.6v-3.1H9.1v3.1z"/>'
DEPLACER = ('<path d="M16 3.5l3.6 3.6h-2.4v7.7h7.7v-2.4l3.6 3.6-3.6 3.6v-2.4h-7.7v7.7h2.4L16 28.5l-3.6-3.6h2.4v-7.7H7.1v2.4'
            'L3.5 16l3.6-3.6v2.4h7.7V7.1h-2.4z"/>')
I_TEXTE = "M12.5 5.5h1.8a1.7 1.7 0 0 1 1.7 1.7 1.7 1.7 0 0 1 1.7-1.7h1.8 M16 7.2v17.6 M12.5 26.5h1.8a1.7 1.7 0 0 0 1.7-1.7 1.7 1.7 0 0 0 1.7 1.7h1.8"


def tourne(svg, angle):
    return f'<g transform="rotate({angle} 16 16)">{svg}</g>'


def anneau(cx, cy, r, angle, epais=2.6):
    """Anneau blanc cerné de pastel, avec un arc à la nuance forte qui tourne (attente)."""
    a0, a1 = math.radians(angle - 90), math.radians(angle)
    x0, y0, x1, y1 = cx + r * math.cos(a0), cy + r * math.sin(a0), cx + r * math.cos(a1), cy + r * math.sin(a1)
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{CONTOUR}" stroke-width="{epais + 2}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#ffffff" stroke-width="{epais}"/>'
            f'<path d="M{x0:.2f} {y0:.2f}A{r} {r} 0 0 1 {x1:.2f} {y1:.2f}" fill="none" stroke="{FORT}" stroke-width="{epais}" stroke-linecap="round"/>')


def pastille(cx, cy, dessin):
    """Petit badge rond au bas de la flèche (copier, lien, aide, menu)."""
    return (f'<circle cx="{cx}" cy="{cy}" r="5.6" fill="{CONTOUR}"/><circle cx="{cx}" cy="{cy}" r="4.5" fill="#ffffff"/>'
            f'<path d="{dessin}" fill="none" stroke="{FORT}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')


# nom principal : (dessin, point actif x, y), ou (fonction(angle), x, y) pour une forme animée
FORMES = {
    "default": (forme(FLECHE), 7, 3.6),
    "pointer": (forme(MAIN), 13.1, 3),
    "text": (trait(I_TEXTE), 16, 16),
    "vertical-text": (tourne(trait(I_TEXTE), 90), 16, 16),
    "wait": (lambda a: anneau(16, 16, 8.5, a), 16, 16),
    "progress": (lambda a: forme(FLECHE) + anneau(22.5, 23, 4.6, a, 2), 7, 3.6),
    "not-allowed": (trait("M16 7a9 9 0 1 0 0.01 0z M9.8 22.2l12.4-12.4", 2.4), 16, 16),
    "move": (forme(DEPLACER), 16, 16),
    "grab": (forme(MAIN_OUVERTE), 16, 12),
    "grabbing": (forme(MAIN_FERMEE), 16, 14),
    "ew-resize": (forme(DOUBLE_FLECHE), 16, 16),
    "ns-resize": (tourne(forme(DOUBLE_FLECHE), 90), 16, 16),
    "nwse-resize": (tourne(forme(DOUBLE_FLECHE), 45), 16, 16),
    "nesw-resize": (tourne(forme(DOUBLE_FLECHE), -45), 16, 16),
    "crosshair": (trait("M16 4v8 M16 20v8 M4 16h8 M20 16h8", 1.3), 16, 16),
    "cell": (forme('<path d="M13.5 5h5v8.5H27v5h-8.5V27h-5v-8.5H5v-5h8.5z"/>', 1.8), 16, 16),
    "help": (forme(FLECHE) + pastille(22.5, 23, "M20.9 21.6a1.7 1.7 0 1 1 2.3 1.6c-.5.2-.7.6-.7 1.1 M22.5 25.9h.01"), 7, 3.6),
    "copy": (forme(FLECHE) + pastille(22.5, 23, "M22.5 20.6v4.8 M20.1 23h4.8"), 7, 3.6),
    "alias": (forme(FLECHE) + pastille(22.5, 23, "M20.6 25l3.8-3.8 M21.6 21.2h2.8v2.8"), 7, 3.6),
    "context-menu": (forme(FLECHE) + pastille(22.5, 23, "M20.4 21.4h4.2 M20.4 23h4.2 M20.4 24.6h4.2"), 7, 3.6),
    "zoom-in": (trait("M13.5 5.5a8 8 0 1 0 .01 0z M19.2 19.2l7 7 M13.5 10v7 M10 13.5h7", 1.4), 13.5, 13.5),
    "zoom-out": (trait("M13.5 5.5a8 8 0 1 0 .01 0z M19.2 19.2l7 7 M10 13.5h7", 1.4), 13.5, 13.5),
}

# Autres noms (CSS, X11, Qt, GTK) qui désignent la même forme : des liens dans cursors/
ALIAS = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left_arrow"],
    "pointer": ["hand1", "hand2", "pointing_hand", "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822"],
    "text": ["xterm", "ibeam"],
    "wait": ["watch", "0426c94ea35c87780ff01dc239897213"],
    "progress": ["left_ptr_watch", "half-busy", "3ecb610c1bf2410f44200f48c40d3599", "00000000000000020006000e7e9ffc3f",
                 "08e8e1c95fe2fc01f976f1e063a24ccd"],
    "not-allowed": ["crossed_circle", "forbidden", "circle", "no-drop", "dnd-no-drop", "03b6e0fcb3499374a867c041f52298f0"],
    "move": ["fleur", "all-scroll", "size_all", "dnd-move", "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"],
    "grab": ["openhand", "5aca4d189052212118709018842178c0"],
    "grabbing": ["closedhand", "dnd-none", "208530c400c041818281048008011002"],
    "ew-resize": ["col-resize", "size_hor", "h_double_arrow", "sb_h_double_arrow", "e-resize", "w-resize", "left_side", "right_side",
                  "split_h", "14fef782d02440884392942c11205230", "028006030e0e7ebffc7f7070c0600140", "043a9f68147c53184671403ffa811cc5"],
    "ns-resize": ["row-resize", "size_ver", "v_double_arrow", "sb_v_double_arrow", "n-resize", "s-resize", "top_side", "bottom_side",
                  "split_v", "2870a09082c103050810ffdffffe0204", "00008160000006810000408080010102", "c07385c7190e701020ff7ffffd08103c"],
    "nwse-resize": ["size_fdiag", "bd_double_arrow", "nw-resize", "se-resize", "top_left_corner", "bottom_right_corner",
                    "c7088f0f3e6c8088236ef8e1e3e70000"],
    "nesw-resize": ["size_bdiag", "fd_double_arrow", "ne-resize", "sw-resize", "top_right_corner", "bottom_left_corner",
                    ],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross"],
    "cell": ["plus"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "5c6cd98b3f3ebcb1f9c7f1c204630408", "d9ce0ab605698f320427677b458ad60b"],
    "copy": ["dnd-copy", "1081e37283d90000800003c07f3ef6bf", "6407b0e94181790501fd1e167b474872", "b66166c04f8c3109214a4fbd64a50fc8"],
    "alias": ["link", "dnd-link", "3085a0e285430894940527032f8b26df", "640fb0e74195791501fd1ed57b41487f", "a2a266d0498c3104214a47bd64ab0fc8"],
    "context-menu": [],
    "zoom-in": [],
    "zoom-out": [],
}


def svg(dessin):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{dessin}</svg>'


def rendre(dessin, taille):
    """Image ARGB (tableau taille × taille × 4, non prémultiplié) de la forme, avec une ombre douce dessous."""
    from PySide6.QtCore import QByteArray, QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    def image(texte):
        img = QImage(taille, taille, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        QSvgRenderer(QByteArray(texte.encode())).render(p, QRectF(0, 0, taille, taille))
        p.end()
        tableau = np.frombuffer(img.constBits(), np.uint8).reshape(taille, taille, 4).astype(np.float32) / 255  # BGRA
        return tableau
    forme_img = image(svg(dessin))
    # ombre : l'alpha de la forme, décalé d'un pas vers le bas, adouci (flou gaussien séparable), à 35 %
    pas = taille / 32
    alpha = forme_img[:, :, 3]
    decale = np.zeros_like(alpha)
    d = max(1, round(pas))
    decale[d:, :] = alpha[:-d, :]
    sigma = 0.9 * pas
    r = max(1, int(3 * sigma))
    x = np.arange(-r, r + 1)
    noyau = np.exp(-(x ** 2) / (2 * sigma ** 2))
    noyau /= noyau.sum()
    flou = np.apply_along_axis(lambda v: np.convolve(v, noyau, mode="same"), 0, decale)
    flou = np.apply_along_axis(lambda v: np.convolve(v, noyau, mode="same"), 1, flou)
    ombre = 0.35 * flou
    # composition « par-dessus » : forme sur l'ombre (ombre gris-bleu très foncé)
    a_f = alpha
    a = a_f + ombre * (1 - a_f)
    couleur_ombre = np.array([0x20, 0x10, 0x0B], np.float32) / 255  # BGR de #0B1020
    rgb = forme_img[:, :, :3] * a_f[..., None] + couleur_ombre * (ombre * (1 - a_f))[..., None]
    with np.errstate(invalid="ignore", divide="ignore"):
        rgb = np.where(a[..., None] > 0, rgb / a[..., None], 0)
    return np.dstack([rgb, a])  # BGRA, non prémultiplié


def xcursor(images):
    """Fichier Xcursor : images = [(taille nominale, BGRA non prémultiplié, x actif, y actif, délai ms)]."""
    entete = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(images))
    position = 16 + 12 * len(images)
    toc, corps = b"", b""
    for nominal, img, xh, yh, delai in images:
        h, w = img.shape[:2]
        toc += struct.pack("<III", 0xFFFD0002, nominal, position)
        premult = img.copy()
        premult[:, :, :3] *= premult[:, :, 3:4]
        octets = np.clip(np.rint(premult * 255), 0, 255).astype(np.uint8)  # BGRA = ARGB en petit-boutiste
        morceau = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, nominal, 1, w, h, xh, yh, delai) + octets.tobytes()
        corps += morceau
        position += len(morceau)
    return entete + toc + corps


def fabriquer(dossier=THEME):
    from PySide6.QtGui import QGuiApplication
    QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    curseurs = dossier / "cursors"
    shutil.rmtree(dossier, ignore_errors=True)
    curseurs.mkdir(parents=True)
    (dossier / "index.theme").write_text(
        "[Icon Theme]\nName=BinixX\nComment=Pointeur BinixX OS : blanc, plat et fin, contour bleu BinixX pastel\n"
        "Inherits=breeze_cursors\n", encoding="utf-8")
    (dossier / "cursor.theme").write_text("[Icon Theme]\nInherits=binixx-curseurs\n", encoding="utf-8")
    for nom, (dessin, xh, yh) in FORMES.items():
        images = []
        for taille in TAILLES:
            echelle = taille / 32
            xa, ya = min(taille - 1, round(xh * echelle)), min(taille - 1, round(yh * echelle))
            if callable(dessin):
                for i in range(IMAGES_ATTENTE):
                    images.append((taille, rendre(dessin(360 * i / IMAGES_ATTENTE), taille), xa, ya, DELAI_MS))
            else:
                images.append((taille, rendre(dessin, taille), xa, ya, 0))
        (curseurs / nom).write_bytes(xcursor(images))
        for autre in ALIAS.get(nom, []):
            os.symlink(nom, curseurs / autre)
    return sorted(p.name for p in curseurs.iterdir())


if __name__ == "__main__":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    noms = fabriquer()
    print(f"binixx-curseurs : {len(FORMES)} formes, {len(noms)} noms")
