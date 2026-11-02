"""Icônes d'applications BinixX OS : chaque application sur une même plaque « squircle », comme sur un téléphone (docs/identite-visuelle.md).

Règles choisies sur maquette :
  - la forme est un squircle (superellipse, la forme des icônes de téléphone), la même pour toutes les applications ;
  - un logo qui a son propre fond (carré ou rond plein : Signal, Zoom, Spotify…) est posé sur une plaque de ce fond, façon One UI ;
  - un logo sans fond (Firefox, VLC, GIMP…) est posé sur une plaque en verre teinté de sa couleur principale ;
  - en Nuit, les plaques sont un peu plus profondes, pour ne pas éblouir.
Le logo est celui que l'application installe (Breeze pour les applications de KDE, hicolor sinon) : on ne le redessine pas, on le pose
sur la plaque. L'icône produite est un SVG : la plaque en vecteurs, le logo en image (PNG intégré) rendue par QtSvg.

Deux usages :
  - à la construction de l'image (build_files/icones-binixx.py appelle fabriquer_systeme) : toutes les applications fournies ;
  - dans la session (binixx-plaques, service utilisateur) : les applications installées ensuite (Flatpak), écrites dans
    ~/.local/share/icons/binixx-os[-dark]/apps/scalable.

    python3 -m binixx_centre.plaques [--systeme] [dossier des thèmes]
"""

import base64
import colorsys
import configparser
import glob
import math
import os
import re
import sys

NOM, NOM_SOMBRE = "binixx-os", "binixx-os-dark"
REPERTOIRE = "apps/scalable"
TAILLE_ANALYSE = 96
TAILLE_LOGO = 192  # pixels du logo intégré (affiché net jusqu'à 192 et au-delà sans défaut visible)
MARQUE = "binixx-plaque"
DOSSIERS_APPLICATIONS = ("/usr/share/applications", "/var/lib/flatpak/exports/share/applications",
                         "~/.local/share/flatpak/exports/share/applications")
DOSSIERS_ICONES = ("~/.local/share/icons", "~/.local/share/flatpak/exports/share/icons", "/var/lib/flatpak/exports/share/icons",
                   "/usr/share/icons")
THEMES_SOURCE = ("breeze", "hicolor")


def _squircle():
    """Le squircle (superellipse n = 5) dans un carré de 100 : la forme commune à toutes les applications."""
    points = []
    for i in range(96):
        a = 2 * math.pi * i / 96
        c, s = math.cos(a), math.sin(a)
        x = 50 + 49 * math.copysign(abs(c) ** 0.4, c)
        y = 50 + 49 * math.copysign(abs(s) ** 0.4, s)
        points.append(f"{x:.2f},{y:.2f}")
    return "M" + " L".join(points) + " Z"


SQUIRCLE = _squircle()


# ------------------------------------------------------------------ trouver le logo d'une application
def applications(dossiers=DOSSIERS_APPLICATIONS):
    """{nom de l'icône : nom de l'application} des applications visibles (Icon= qui n'est pas un chemin)."""
    trouvees = {}
    for dossier in dossiers:
        for chemin in sorted(glob.glob(os.path.join(os.path.expanduser(dossier), "*.desktop"))):
            lecteur = configparser.ConfigParser(interpolation=None, strict=False)
            lecteur.optionxform = str
            try:
                lecteur.read(chemin, encoding="utf-8")
                entree = lecteur["Desktop Entry"]
            except (configparser.Error, KeyError, UnicodeDecodeError):
                continue
            icone = entree.get("Icon", "").strip()
            if not icone or "/" in icone or entree.get("NoDisplay", "").lower() == "true" or entree.get("Hidden", "").lower() == "true":
                continue
            trouvees.setdefault(icone, entree.get("Name", icone))
    return trouvees


def _taille_du_dossier(chemin):
    """Taille d'un répertoire d'icônes (apps/48, 48x48/apps, scalable/apps…) ; 1000 pour un dessin vectoriel."""
    if "scalable" in chemin:
        return 1000
    nombres = [int(n) for n in re.findall(r"(\d+)(?:x\d+)?(?:@\d+x)?", chemin)]
    return max(nombres) if nombres else 0


def trouver_logo(nom, dossiers=DOSSIERS_ICONES, themes=THEMES_SOURCE):
    """Chemin du meilleur dessin de l'icône `nom` (vectoriel d'abord, sinon la plus grande image) ; None s'il n'y en a pas."""
    candidats = []
    for base in dossiers:
        base = os.path.expanduser(base)
        for theme in themes:
            for extension in ("svg", "svgz", "png"):
                for chemin in glob.glob(os.path.join(base, theme, "**", f"{nom}.{extension}"), recursive=True):
                    if "symbolic" in chemin or "/actions/" in chemin or "/status/" in chemin:
                        continue
                    candidats.append((_taille_du_dossier(os.path.relpath(chemin, base)), extension != "png", chemin))
    pixmap = f"/usr/share/pixmaps/{nom}.png"
    if os.path.exists(pixmap):
        candidats.append((48, False, pixmap))
    if not candidats:
        return None
    candidats.sort(key=lambda c: (c[1], c[0]), reverse=True)
    return candidats[0][2]


# ------------------------------------------------------------------ analyse et composition (Qt)
def _qt():
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    if QGuiApplication.instance() is None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _qt.application = QGuiApplication(sys.argv[:1])
    return QBuffer, QByteArray, QIODevice, QRectF, Qt, QImage, QPainter, QSvgRenderer


def rendre(chemin, taille):
    """Le logo rendu en image carrée `taille` × `taille` (QImage ARGB32), centré et sans déformation ; None s'il est illisible."""
    QBuffer, QByteArray, QIODevice, QRectF, Qt, QImage, QPainter, QSvgRenderer = _qt()
    image = QImage(taille, taille, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    peintre = QPainter(image)
    peintre.setRenderHint(QPainter.Antialiasing)
    peintre.setRenderHint(QPainter.SmoothPixmapTransform)
    if chemin.endswith((".svg", ".svgz")):
        rendu = QSvgRenderer(chemin)
        if not rendu.isValid():
            peintre.end()
            return None
        rendu.render(peintre, QRectF(0, 0, taille, taille))
    else:
        source = QImage(chemin)
        if source.isNull():
            peintre.end()
            return None
        source = source.scaled(taille, taille, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        peintre.drawImage((taille - source.width()) // 2, (taille - source.height()) // 2, source)
    peintre.end()
    return image.convertToFormat(QImage.Format_ARGB32)


def analyser(image):
    """{"fond": bool, "couleur_fond": "#rrggbb" ou None, "dominante": "#rrggbb"} : le logo a-t-il son propre fond (carré ou rond
    plein), de quelle couleur, et quelle est sa couleur principale."""
    taille = image.width()
    octets = bytes(image.constBits())[: taille * taille * 4]  # BGRA
    xs, ys, opaques = [], [], 0
    teintes = {}
    for y in range(taille):
        ligne = y * taille * 4
        for x in range(taille):
            b, g, r, a = octets[ligne + 4 * x: ligne + 4 * x + 4]
            if a > 200:
                opaques += 1
                xs.append(x)
                ys.append(y)
                h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                if s > 0.25 and 0.2 < l < 0.85:
                    teintes.setdefault(int(h * 24), []).append((r, g, b))
    if not xs:
        return {"fond": False, "couleur_fond": None, "dominante": "#7C8496"}
    largeur, hauteur = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    remplissage = opaques / (largeur * hauteur)
    grand = largeur > 0.7 * taille and hauteur > 0.7 * taille and abs(largeur - hauteur) < 0.12 * taille
    carre = remplissage > 0.80
    rond = 0.74 <= remplissage <= 0.82
    fond = grand and (carre or rond)
    if teintes:
        groupe = max(teintes.values(), key=len)
        dominante = tuple(sum(c[i] for c in groupe) // len(groupe) for i in range(3))
    else:
        dominante = (0x7C, 0x84, 0x96)
    couleur_fond = None
    if fond and carre and not rond:
        # carré plein : le fond se lit juste à l'intérieur du bord gauche, à mi-hauteur
        i = ((min(ys) + hauteur // 2) * taille + min(xs) + int(largeur * 0.08)) * 4
        b, g, r = octets[i], octets[i + 1], octets[i + 2]
        couleur_fond = "#%02x%02x%02x" % (r, g, b)
    elif fond:
        # rond plein : le pourtour du disque, là où le dessin du logo ne passe pas, a la couleur principale
        couleur_fond = "#%02x%02x%02x" % dominante
    return {"fond": fond, "couleur_fond": couleur_fond, "dominante": "#%02x%02x%02x" % dominante}


def _assombrir(couleur, facteur):
    r, g, b = (int(couleur[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(c * facteur) for c in (r, g, b))


def _png_base64(image):
    QBuffer, QByteArray, QIODevice, *_ = _qt()
    donnees = QByteArray()
    tampon = QBuffer(donnees)
    tampon.open(QIODevice.WriteOnly)
    image.save(tampon, "PNG")
    tampon.close()
    return base64.b64encode(bytes(donnees)).decode()


def composer(chemin_logo, sombre=False):
    """L'icône BinixX (texte SVG) d'un logo ; None si le logo est illisible."""
    analyse_image = rendre(chemin_logo, TAILLE_ANALYSE)
    logo = rendre(chemin_logo, TAILLE_LOGO)
    if analyse_image is None or logo is None:
        return None
    a = analyser(analyse_image)
    contour = "#ffffff"
    if a["fond"]:
        fond = a["couleur_fond"] if not sombre else _assombrir(a["couleur_fond"], 0.82)
        plaque = f'<path d="{SQUIRCLE}" fill="{fond}"/>'
        echelle = 0.86
        opacite_contour = 0.18 if sombre else 0.35
    else:
        r, g, b = (int(a["dominante"][i:i + 2], 16) for i in (1, 3, 5))
        teinte = 0.30 if sombre else 0.24
        reflet = 0.20 if sombre else 0.62
        plaque = ('<defs><linearGradient id="reflet" x1="0" y1="0" x2="0.35" y2="1">'
                  f'<stop offset="0" stop-color="#ffffff" stop-opacity="{reflet}"/>'
                  '<stop offset="0.6" stop-color="#ffffff" stop-opacity="0"/></linearGradient></defs>'
                  f'<path d="{SQUIRCLE}" fill="rgb({r},{g},{b})" fill-opacity="{teinte}"/>'
                  f'<path d="{SQUIRCLE}" fill="url(#reflet)"/>')
        echelle = 0.68
        opacite_contour = 0.22 if sombre else 0.75
    cote = 100 * echelle
    debut = (100 - cote) / 2
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 100 100">\n'
            f"<!-- {MARQUE} : icône BinixX OS (binixx_centre/plaques.py) ; le logo est celui de l'application, inchangé -->\n"
            f"{plaque}"
            f'<path d="{SQUIRCLE}" fill="none" stroke="{contour}" stroke-opacity="{opacite_contour}" stroke-width="1"/>'
            f'<image x="{debut:.2f}" y="{debut:.2f}" width="{cote:.2f}" height="{cote:.2f}" '
            f'xlink:href="data:image/png;base64,{_png_base64(logo)}"/>\n</svg>\n')


# ------------------------------------------------------------------ thèmes
def _rubrique_index(theme_dir):
    """Ajoute le répertoire des plaques à index.theme (et crée un index.theme minimal s'il n'y en a pas)."""
    index = os.path.join(theme_dir, "index.theme")
    lecteur = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    lecteur.optionxform = str
    if os.path.exists(index):
        lecteur.read(index, encoding="utf-8")
    if not lecteur.has_section("Icon Theme"):
        lecteur.add_section("Icon Theme")
        lecteur.set("Icon Theme", "Name", "BinixX OS")
        lecteur.set("Icon Theme", "Inherits", "breeze-dark" if theme_dir.rstrip("/").endswith("-dark") else "breeze")
    repertoires = [d for d in lecteur.get("Icon Theme", "Directories", fallback="").split(",") if d]
    if REPERTOIRE not in repertoires:
        repertoires.append(REPERTOIRE)
    lecteur.set("Icon Theme", "Directories", ",".join(repertoires))
    if not lecteur.has_section(REPERTOIRE):
        lecteur.add_section(REPERTOIRE)
    for cle, valeur in (("Size", "48"), ("MinSize", "16"), ("MaxSize", "512"), ("Context", "Applications"), ("Type", "Scalable")):
        lecteur.set(REPERTOIRE, cle, valeur)
    with open(index, "w", encoding="utf-8") as fichier:
        lecteur.write(fichier, space_around_delimiters=False)


def fabriquer(dossier_themes, applis=None, dossiers_icones=DOSSIERS_ICONES, deja=()):
    """Écrit la plaque de chaque application dans binixx-os et binixx-os-dark ; (écrites, sans logo). `deja` : icônes à ne pas refaire."""
    applis = applications() if applis is None else applis
    ecrites, sans_logo = [], []
    for nom in sorted(applis):
        if nom in deja:
            continue
        logo = trouver_logo(nom, dossiers_icones)
        if logo is None:
            sans_logo.append(nom)
            continue
        for theme, sombre in ((NOM, False), (NOM_SOMBRE, True)):
            svg = composer(logo, sombre)
            if svg is None:
                break
            dossier = os.path.join(dossier_themes, theme, REPERTOIRE)
            os.makedirs(dossier, exist_ok=True)
            with open(os.path.join(dossier, f"{nom}.svg"), "w", encoding="utf-8") as fichier:
                fichier.write(svg)
        else:
            ecrites.append(nom)
            continue
        sans_logo.append(nom)
    for theme in (NOM, NOM_SOMBRE):
        if os.path.isdir(os.path.join(dossier_themes, theme)):
            _rubrique_index(os.path.join(dossier_themes, theme))
    return ecrites, sans_logo


def fabriquer_session(dossier_themes="~/.local/share/icons", systeme="/usr/share/icons"):
    """Dans la session : les plaques des applications que l'image n'a pas déjà (installées ensuite, Flatpak)."""
    dossier_themes = os.path.expanduser(dossier_themes)
    deja = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(systeme, NOM, REPERTOIRE))} \
        if os.path.isdir(os.path.join(systeme, NOM, REPERTOIRE)) else set()
    deja |= {os.path.splitext(f)[0] for f in os.listdir(os.path.join(dossier_themes, NOM, REPERTOIRE))} \
        if os.path.isdir(os.path.join(dossier_themes, NOM, REPERTOIRE)) else set()
    for theme in (NOM, NOM_SOMBRE):
        index_systeme = os.path.join(systeme, theme, "index.theme")
        index_session = os.path.join(dossier_themes, theme, "index.theme")
        if os.path.exists(index_systeme) and not os.path.exists(index_session):
            os.makedirs(os.path.dirname(index_session), exist_ok=True)
            with open(index_systeme, encoding="utf-8") as source, open(index_session, "w", encoding="utf-8") as cible:
                cible.write(source.read())
    ecrites, sans_logo = fabriquer(dossier_themes, deja=deja)
    if ecrites:
        for theme in (NOM, NOM_SOMBRE):  # le cache des icônes de KDE se renouvelle quand le dossier du thème change
            os.utime(os.path.join(dossier_themes, theme))
    return ecrites, sans_logo


def main(argv=None, sortie=print):
    """binixx-plaques [--systeme [dossier]] : plaques des applications (session : celles installées après l'image)."""
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--systeme"]:
        dossier = argv[1] if len(argv) > 1 else "/usr/share/icons"
        ecrites, sans_logo = fabriquer(dossier, dossiers_icones=("/usr/share/icons",))
    else:
        ecrites, sans_logo = fabriquer_session()
    sortie(f"Icônes BinixX : {len(ecrites)} applications sur leur plaque"
           + (f" ; sans logo trouvé : {', '.join(sans_logo)}" if sans_logo else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
