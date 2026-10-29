#!/usr/bin/env python3
"""Génère l'identité visuelle de BinixX OS : logos, icône, fond d'écran, écran de démarrage, installeur.

Tous les fichiers sont produits à partir de ce script, pour pouvoir retoucher le logo
(couleurs, proportions) et tout régénérer d'un coup :

    pip install fonttools uharfbuzz pillow numpy scipy
    python3 branding/generer.py [--chromium /chemin/vers/chrome] [--installeur-seulement]

Chromium (ou Chrome) sert à rendre les images matricielles de l'écran de démarrage et de l'installeur.
Le fond d'écran, lui, est calculé par branding/fond_ecran.py (numpy, scipy, Pillow).

Police : Outfit (SIL Open Font License, voir branding/police/OFL.txt). Le texte est
converti en tracés : les fichiers produits ne dépendent d'aucune police installée.
"""
import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

BRANDING = Path(__file__).resolve().parent
REPO = BRANDING.parent
SYSTEM = REPO / "system_files"
FONT = BRANDING / "police" / "Outfit.ttf"

# ------------------------------------------------------------------ couleurs
INK = "#0B0F1A"          # encre : texte et fonds sombres
WHITE = "#FFFFFF"
# « BinixX OS » a deux « i » (positions 1 et 3 du texte) : ceux dont le point devient une gemme
POINTS_EN_GEMME = (1, 3)
# dégradé de la gemme : ciel lumineux -> bleu BinixX OS -> indigo profond
GEM_LIGHT = [("0", "#5FB2FF"), ("0.45", "#2F5BFF"), ("1", "#1A26C9")]
GEM_DARK = [("0", "#8CCBFF"), ("0.45", "#5A7DFF"), ("1", "#3A3FE0")]

_ids = [0]


def uid(prefix):
    _ids[0] += 1
    return f"{prefix}{_ids[0]}"


def stops_xml(stops):
    return "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)


# ------------------------------------------------------------------ symbole
def gem(cx, cy, size, stops=GEM_LIGHT, small=False, mono=None, highlight=True):
    """La gemme : losange aux angles doux, fendu de deux entailles diagonales
    (une seule en petite taille), héritées des lames de l'avatar Nic69Han."""
    side = size / math.sqrt(2) * 0.98
    radius = side * 0.2
    if small:
        weights, gap = [1.15, 0.85], side * 0.09
    else:
        weights, gap = [1.25, 1.0, 0.8], side * 0.05
    unit = (side - gap * (len(weights) - 1)) / sum(weights)
    clip = uid("c")
    defs = [f'<clipPath id="{clip}"><rect x="{-side / 2:.2f}" y="{-side / 2:.2f}" width="{side:.2f}" '
            f'height="{side:.2f}" rx="{radius:.2f}"/></clipPath>']
    if mono:
        fill = mono
    else:
        gid = uid("g")
        defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{-side / 2:.1f}" '
                    f'y1="{-side / 2:.1f}" x2="{side / 2:.1f}" y2="{side / 2:.1f}">{stops_xml(stops)}</linearGradient>')
        fill = f"url(#{gid})"
    body, y = [], -side / 2
    for w in weights:
        h = unit * w
        body.append(f'<rect x="{-side / 2 - 1:.2f}" y="{y:.2f}" width="{side + 2:.2f}" height="{h:.2f}" fill="{fill}"/>')
        y += h + gap
    if highlight and not mono:
        hid = uid("h")  # lumière venant du haut de l'écran
        defs.append(f'<linearGradient id="{hid}" x1="1" y1="0" x2="0.35" y2="0.65">'
                    f'<stop offset="0" stop-color="#fff" stop-opacity="0.26"/>'
                    f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
        body.append(f'<rect x="{-side / 2:.2f}" y="{-side / 2:.2f}" width="{side:.2f}" height="{side:.2f}" fill="url(#{hid})"/>')
    return (f'<defs>{"".join(defs)}</defs><g transform="translate({cx:.2f} {cy:.2f}) rotate(-45)">'
            f'<g clip-path="url(#{clip})">{"".join(body)}</g></g>')


def dot_gem(cx, cy, d, stops):
    """Point du « i » : une mini-gemme."""
    gid, r = uid("g"), d / 2
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">{stops_xml(stops)}</linearGradient></defs>'
            f'<path d="M{cx:.2f} {cy - r:.2f} Q{cx + r * 0.08:.2f} {cy - r * 0.92:.2f} {cx + r * 0.92:.2f} {cy - r * 0.08:.2f} '
            f'L{cx + r:.2f} {cy:.2f} L{cx:.2f} {cy + r:.2f} L{cx - r:.2f} {cy:.2f} Z" fill="url(#{gid})"/>')


# ------------------------------------------------------------------ logotype
class Wordmark:
    """« BinixX OS » en Outfit SemiBold, converti en tracés, point du i en gemme."""

    def __init__(self, weight=600):
        self.font = instantiateVariableFont(TTFont(FONT), {"wght": weight})
        self.glyphs = self.font.getGlyphSet()
        self.cap = self.font["OS/2"].sCapHeight
        self.hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(str(FONT))))
        self.hbfont.set_variations({"wght": weight})
        self.dot = self._dot_box()

    def _dot_box(self):
        """Boîte du point d'origine du « i » (son contour le plus haut)."""
        rec = DecomposingRecordingPen(self.glyphs)
        self.glyphs["i"].draw(rec)
        contours, current = [], []
        for op, args in rec.value:
            current.append((op, args))
            if op in ("closePath", "endPath"):
                contours.append(current)
                current = []
        boxes = []
        for contour in contours:
            bp = BoundsPen(self.glyphs)
            for op, args in contour:
                getattr(bp, op)(*args)
            boxes.append(bp.bounds)
        return max(boxes, key=lambda b: b[1])

    def render(self, x, baseline, cap_px, color, stops):
        """Renvoie (svg, largeur)."""
        text = "BinixX OS"
        buf = hb.Buffer()
        buf.add_str("".join("ı" if k in POINTS_EN_GEMME else c for k, c in enumerate(text)))  # i sans point
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {"kern": True, "liga": False})
        scale = cap_px / self.cap
        out, pen_x = [], 0
        for k, (ch, info, pos) in enumerate(zip(text, buf.glyph_infos, buf.glyph_positions)):
            pen = SVGPathPen(self.glyphs)
            self.glyphs[self.font.getGlyphName(info.codepoint)].draw(
                TransformPen(pen, (scale, 0, 0, -scale, x + pen_x * scale, baseline)))
            out.append(f'<path d="{pen.getCommands()}" fill="{color}"/>')
            if k in POINTS_EN_GEMME:
                x0, y0, x1, y1 = self.dot
                out.append(dot_gem(x + (pen_x + (x0 + x1) / 2) * scale, baseline - (y0 + y1) / 2 * scale,
                                   (x1 - x0) * 1.45 * scale, stops))
            pen_x += pos.x_advance
        return "".join(out), pen_x * scale


def lockup_horizontal(wm, x, cy, sym, stops, text_color):
    cap = sym * 0.42
    tx = x + sym * 1.2
    text, w = wm.render(tx, cy + cap / 2, cap, text_color, stops)
    return gem(x + sym / 2, cy, sym, stops) + text, tx + w - x


def lockup_vertical(wm, cx, top, sym, stops, text_color):
    cap = sym * 0.235
    _, w = wm.render(0, 0, cap, text_color, stops)
    text, _ = wm.render(cx - w / 2, top + sym * 1.2 + cap, cap, text_color, stops)
    return gem(cx, top + sym / 2, sym, stops) + text, top + sym * 1.2 + cap


def svg_doc(w, h, body, background=None):
    bg = f'<rect width="100%" height="100%" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" '
            f'viewBox="0 0 {w:g} {h:g}">{bg}{body}</svg>\n')


# ------------------------------------------------------------------ rendu matriciel
class Renderer:
    def __init__(self, chromium):
        self.chromium = chromium
        self.tmp = Path(tempfile.mkdtemp(prefix="binixx-branding-"))

    def png(self, html_body, w, h, dest, transparent=False):
        page = self.tmp / "page.html"
        page.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;'
                        f'padding:0;{"background:transparent" if transparent else ""}}}</style></head>'
                        f'<body>{html_body}</body></html>')
        args = [self.chromium, "--headless", "--no-sandbox", "--hide-scrollbars",
                f"--window-size={w},{h}", "--force-device-scale-factor=1", f"--screenshot={dest}"]
        if transparent:
            args.append("--default-background-color=00000000")
        subprocess.run(args + [page.as_uri()], check=True, capture_output=True)


def installer_sidebar_html(w, h):
    """Panneau latéral de l'installeur : nuit BinixX OS, halo bleu derrière le logo, gemme discrète.
    Anaconda l'affiche sans le redimensionner, calé en haut à gauche, sur 15 % de la largeur de
    l'écran (153 px en 1024x768) : l'essentiel tient dans les 150 premiers pixels et les 700
    premières lignes ; le bas finit sur la couleur unie du CSS (INK)."""
    size = 300
    background = ("radial-gradient(120px 140px at 95px 70px, rgba(47,91,255,.55), transparent),"
                  "radial-gradient(220px 260px at 70px 600px, rgba(26,38,201,.40), transparent),"
                  f"linear-gradient(180deg,#10163A,{INK} 70%)")
    glow = svg_doc(size, size, gem(size / 2, size / 2, size * 0.8, GEM_DARK, highlight=False))
    shape = svg_doc(size, size, gem(size / 2, size / 2, size * 0.8, GEM_DARK))
    left, top = 100 - size / 2, 600 - size / 2
    return (f'<div style="position:relative;width:{w}px;height:{h}px;overflow:hidden;background:{background}">'
            f'<div style="position:absolute;left:{left}px;top:{top}px;filter:blur(40px);opacity:.55">{glow}</div>'
            f'<div style="position:absolute;left:{left}px;top:{top}px;opacity:.28">{shape}</div>'
            '</div>')


INSTALLER_CSS = f"""/* Installeur (Anaconda) : logo et couleurs BinixX OS à la place de ceux de Fedora.
 * Généré par branding/generer.py ; placé dans images/product.img sur l'ISO par
 * disk_config/personnaliser-iso.sh. Anaconda charge ce fichier après son propre style et celui de
 * Fedora (fedora-logos), avec une priorité plus haute.
 */

/* Panneau latéral : fond, puis logo */
.logo-sidebar {{
    background-image: url('/usr/share/anaconda/pixmaps/binixx/sidebar-bg.png');
    background-color: {INK};
    background-repeat: no-repeat;
}}

.logo {{
    background-image: url('/usr/share/anaconda/pixmaps/binixx/sidebar-logo.png');
    background-position: 50% 24px;
    background-repeat: no-repeat;
    background-color: transparent;
}}

.product-logo {{
    background-image: none;
    background-color: transparent;
}}

/* Barre du haut des écrans de réglage (disque, clavier, langue…) */
AnacondaSpokeWindow #nav-box {{
    background-color: #10163A;
    background-image: linear-gradient(to right, {INK}, #10163A 60%, #1A2A8F);
    color: white;
}}
"""


def installer_assets(wm, renderer):
    """Images et style de l'installeur, dans branding/installeur/ (arborescence de product.img)."""
    root = BRANDING / "installeur"
    pixmaps = root / "usr/share/anaconda/pixmaps/binixx"
    pixmaps.mkdir(parents=True, exist_ok=True)
    # Logo horizontal blanc, 130 px de large, centré dans 150 px (le panneau en fait 153 en 1024x768)
    body, w = lockup_horizontal(wm, 0, 60, 120, GEM_DARK, WHITE)
    scale = 130 / w
    logo_h = math.ceil(120 * scale) + 4
    body = f'<g transform="translate(10 2) scale({scale:.5f})">{body}</g>'
    renderer.png(svg_doc(150, logo_h, body), 150, logo_h, pixmaps / "sidebar-logo.png", transparent=True)
    renderer.png(installer_sidebar_html(420, 1200), 420, 1200, pixmaps / "sidebar-bg.png")
    css = root / "run/install/product/anaconda-gtk.css"
    css.parent.mkdir(parents=True, exist_ok=True)
    css.write_text(INSTALLER_CSS)


def to_jpeg(png, jpg, quality=90):
    """Grain léger contre les bandes des dégradés, puis JPEG. Sans Pillow : PNG gardé tel quel."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        shutil.copy(png, jpg.with_suffix(".png"))
        return jpg.with_suffix(".png")
    img = Image.open(png).convert("RGB")
    # bruit centré sur 128, écart type ~1,5 niveau : img + bruit - 128
    noise = Image.effect_noise(img.size, 1.5).convert("L")
    img = ImageChops.add(img, Image.merge("RGB", (noise, noise, noise)), scale=1.0, offset=-128)
    img.save(jpg, "JPEG", quality=quality, optimize=True, progressive=True)
    return jpg


# ------------------------------------------------------------------ fichiers produits
def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chromium", default=shutil.which("chromium") or shutil.which("google-chrome")
                        or "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")
    parser.add_argument("--installeur-seulement", action="store_true",
                        help="ne régénérer que l'installeur (le grain des fonds d'écran est aléatoire)")
    args = parser.parse_args()
    wm = Wordmark()

    if args.installeur_seulement:
        renderer = Renderer(args.chromium)
        installer_assets(wm, renderer)
        shutil.rmtree(renderer.tmp)
        print("Installeur régénéré.")
        return

    # 1. Logos (vectoriels)
    logos = {
        "binixx-symbole": svg_doc(512, 512, gem(256, 256, 500)),
        "binixx-symbole-fond-sombre": svg_doc(512, 512, gem(256, 256, 500, GEM_DARK)),
        "binixx-symbole-mono": svg_doc(512, 512, gem(256, 256, 500, mono=INK)),
        "binixx-symbole-petit": svg_doc(64, 64, gem(32, 32, 62, small=True)),
        "binixx-avatar": svg_doc(512, 512, f'<rect width="512" height="512" rx="112" fill="{INK}"/>'
                                + gem(256, 256, 330, GEM_DARK)),
    }
    body, w = lockup_horizontal(wm, 0, 60, 120, GEM_LIGHT, INK)
    logos["binixx-logo-horizontal"] = svg_doc(math.ceil(w), 120, body)
    body, w = lockup_horizontal(wm, 0, 60, 120, GEM_DARK, WHITE)
    logos["binixx-logo-horizontal-fond-sombre"] = svg_doc(math.ceil(w), 120, body)
    body, h = lockup_vertical(wm, 170, 4, 200, GEM_LIGHT, INK)
    logos["binixx-logo-vertical"] = svg_doc(340, math.ceil(h) + 16, body)
    body, h = lockup_vertical(wm, 170, 4, 200, GEM_DARK, WHITE)
    logos["binixx-logo-vertical-fond-sombre"] = svg_doc(340, math.ceil(h) + 16, body)
    for name, doc in logos.items():
        (BRANDING / "logo" / f"{name}.svg").write_text(doc)

    # 2. Icône système (menu Démarrer, « À propos », os-release LOGO=binixx)
    icons = SYSTEM / "usr/share/icons/hicolor/scalable/apps"
    icons.mkdir(parents=True, exist_ok=True)
    (icons / "binixx.svg").write_text(logos["binixx-symbole"])

    renderer = Renderer(args.chromium)

    # 3. Écran de démarrage (Plymouth) : logo vertical blanc, taille 1x
    plymouth = SYSTEM / "usr/share/plymouth/themes/binixx"
    plymouth.mkdir(parents=True, exist_ok=True)
    body, h = lockup_vertical(wm, 120, 4, 140, GEM_DARK, WHITE)
    mark_h = math.ceil(h) + 8
    renderer.png(svg_doc(240, mark_h, body), 240, mark_h, plymouth / "watermark.png", transparent=True)
    # La roue de chargement (throbber-0001.png à 0030.png) : calculée par roue_demarrage.py, sans Chromium
    import roue_demarrage
    roue_demarrage.ecrire_roue(plymouth)

    # 4. Fond d'écran BinixX OS « Le marcheur de l'aube » (clair et sombre) : calculé par fond_ecran.py, sans Chromium
    import fond_ecran
    fond_ecran.ecrire_fonds(SYSTEM / "usr/share/wallpapers/BinixX/contents")

    # 5. Installeur de l'ISO (Anaconda)
    installer_assets(wm, renderer)

    shutil.rmtree(renderer.tmp)
    print("Identité visuelle régénérée.")


if __name__ == "__main__":
    main()
