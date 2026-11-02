#!/usr/bin/env python3
"""Icônes de BinixX OS : celles de Breeze, avec des dossiers arrondis et pastel, d'une couleur par contenu (docs/identite-visuelle.md).

Dans Breeze, un dossier est dessiné en quatre tracés anguleux (le corps à la couleur d'accent, l'onglet, un reflet, une ombre), puis
le pictogramme de son contenu (Documents, Images, Musique, Git…). Ce script garde le pictogramme et remplace le reste par le dossier
BinixX : un onglet arrière, une face avant aux coins arrondis, un fin reflet, comme les dossiers des téléphones (One UI). La couleur
dépend du contenu : Documents bleu clair, Images vert, Musique rose, Vidéos violet, Téléchargements orange, Bureau ardoise, Public
turquoise, les autres jaune clair ; les dossiers de couleur de Breeze (folder-blue, folder-green…) prennent le pastel du même nom et
servent au choix libre (clic droit sur un dossier, binixx-couleur-dossier). Le pictogramme prend une nuance foncée de la couleur.
Aux petites tailles (16, 22 et 24 pixels), le dossier est dessiné sans pictogramme, illisible à cette taille.

Deux thèmes sont écrits dans /usr/share/icons, qui héritent de Breeze :
    binixx-os        Breeze + dossiers pastel (Aube)
    binixx-os-dark   Breeze sombre + les mêmes dossiers en tons plus profonds (Nuit), pour ne pas éblouir
Les liens de Breeze vers un dossier (inode-directory, dossiers de l'application, etc.) sont refaits pour viser le dossier BinixX.

Généré depuis le paquet breeze-icon-theme de l'image, donc à chaque construction : les mises à jour de Breeze sont suivies. La
construction échoue si les dossiers de Breeze n'ont plus la forme attendue. Les icônes de Breeze sont sous licence LGPL-3.0 ou plus
récente (et CC-BY-SA-4.0 pour certaines) : le texte de la licence est copié dans le thème, avec une note disant ce qui a été modifié.

    python3 build_files/icones-binixx.py [dossier des thèmes] [dossier de Breeze]
"""
import colorsys
import configparser
import os
import re
import shutil
import sys

NOM = "binixx-os"
NOM_SOMBRE = "binixx-os-dark"

# Pastels (Aube) et tons profonds (Nuit), validés sur maquette ; une couleur par contenu
COULEURS = {
    "jaune": ("#FFE58A", "#C9A43A"),
    "bleu": ("#A9CBFF", "#4C78C9"),
    "vert": ("#AEE8BC", "#3F9A5B"),
    "rose": ("#FFBBD4", "#C45A86"),
    "violet": ("#CDBBFF", "#7A5CD6"),
    "orange": ("#FFCFA3", "#C97A3A"),
    "ardoise": ("#C9D0DE", "#66708A"),
    "turquoise": ("#A3E6DF", "#3A9C93"),
    "rouge": ("#FFB4AB", "#C4574D"),
    "brun": ("#E3C3A0", "#9A6B45"),
    "noir": ("#7A8090", "#3A3F4C"),
    "blanc": ("#F4F6FA", "#B9C0CF"),
}
# Nom de l'icône (sans « folder- ») → couleur ; les autres dossiers sont jaunes
PAR_CONTENU = {
    "documents": "bleu", "text": "bleu", "txt": "bleu", "notes": "bleu", "book": "bleu", "library": "bleu", "presentation": "bleu",
    "table": "bleu", "sign": "bleu", "print": "bleu",
    "pictures": "vert", "picture": "vert", "image": "vert", "images": "vert", "image-people": "vert", "drawing": "vert",
    "paint": "vert", "design": "vert",
    "music": "rose", "sound": "rose", "podcast": "rose",
    "videos": "violet", "video": "violet",
    "download": "orange", "downloads": "orange",
    "desktop": "ardoise",
    "public": "turquoise", "publicshare": "turquoise", "network": "turquoise", "remote": "turquoise", "cloud": "turquoise",
    "gdrive": "turquoise", "onedrive": "turquoise", "dropbox": "turquoise", "owncloud": "turquoise",
    # dossiers de couleur de Breeze : le choix libre (binixx-couleur-dossier)
    "yellow": "jaune", "blue": "bleu", "green": "vert", "magenta": "rose", "violet": "violet", "orange": "orange", "grey": "ardoise",
    "cyan": "turquoise", "red": "rouge", "brown": "brun", "black": "noir", "white": "blanc",
}
PETITES = 24  # au-dessus : avec pictogramme
CHEMIN = re.compile(r"<path\b.*?/>", re.S)
NOMBRE = re.compile(r"-?\d+(?:\.\d+)?")
VUE = re.compile(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"')


def couleur_de(nom):
    """Couleur d'un dossier de Breeze d'après son nom (folder-documents.svg → bleu)."""
    cle = nom[:-4]
    for prefixe in ("folder-", "folder_"):
        if cle.startswith(prefixe):
            cle = cle[len(prefixe):]
    return PAR_CONTENU.get(cle, "jaune")


def _hls(h):
    return colorsys.rgb_to_hls(*(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)))


def _hexa(hls):
    return "#%02X%02X%02X" % tuple(round(max(0, min(1, c)) * 255) for c in colorsys.hls_to_rgb(*hls))


def nuances(couleur, sombre):
    """(face avant, onglet arrière, pictogramme) pour une couleur du dossier."""
    face = COULEURS[couleur][1 if sombre else 0]
    h, l, s = _hls(face)
    onglet = _hexa((h, l * (0.86 if not sombre else 0.80), s))
    picto = _hexa((h, 0.92, min(1, s * 0.6))) if sombre else _hexa((h, min(0.32, l * 0.42), min(1, s * 0.75)))
    return face, onglet, picto


def dossier_svg(taille, face, onglet, picto="", sombre=False):
    """Le dossier BinixX dessiné dans une grille de 64, mis à l'échelle de la taille de l'icône, avec un pictogramme éventuel."""
    k = taille / 64
    reflet = 0.18 if sombre else 0.55
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {taille:g} {taille:g}">\n'
            "<!-- BinixX OS : dossier pastel (build_files/icones-binixx.py), pictogramme de Breeze (LGPL-3.0-or-later) -->\n"
            f'<g transform="scale({k:g})">'
            f'<path d="M5 13.5a5 5 0 0 1 5-5h13.6a4 4 0 0 1 2.8 1.2l3.4 3.3H54a5 5 0 0 1 5 5V53a5 5 0 0 1-5 5H10a5 5 0 0 1-5-5z" fill="{onglet}"/>'
            f'<rect x="5" y="19" width="54" height="39" rx="6.5" fill="{face}"/>'
            f'<path d="M11.5 19.75h41a5.75 5.75 0 0 1 5.75 5.75" fill="none" stroke="#fff" stroke-opacity="{reflet}" stroke-width="1.2" stroke-linecap="round"/>'
            f"</g>{picto}\n</svg>\n")


def etendue(chemin_svg):
    """Étendue des coordonnées d'un tracé en commandes absolues (plus grande moins plus petite) ; None s'il est en commandes relatives
    (sa forme ne se lit pas simplement)."""
    d = re.search(r'\bd="([^"]*)"', chemin_svg)
    if not d or re.search(r"[a-df-y]", d.group(1)):
        return None
    nombres = [float(n) for n in NOMBRE.findall(d.group(1))]
    return max(nombres) - min(nombres) if nombres else None


def pictogramme(texte, taille):
    """Les tracés du pictogramme d'un dossier de Breeze (après les quatre tracés du dossier) ; None si la forme a changé."""
    chemins = CHEMIN.findall(texte)
    if len(chemins) < 4:
        return None
    premier = etendue(chemins[0])
    # le premier tracé est le corps du dossier : presque toute la largeur, à la couleur d'accent (ou fixe pour folder-blue…)
    if premier is None or premier < 0.75 * taille or ('class="ColorScheme-Accent"' not in chemins[0] and "fill:#" not in chemins[0]):
        return None
    reste = texte[texte.index(chemins[3]) + len(chemins[3]):]
    reste = reste[:reste.rindex("</svg>")]
    return reste.strip()


def colorier_pictogramme(picto, couleur):
    """Le pictogramme dans une seule couleur fixe (plus de couleurs du bureau : il doit rester lisible sur le dossier)."""
    picto = re.sub(r'\s*class="ColorScheme-[A-Za-z]+"', "", picto)
    picto = picto.replace("fill:currentColor", f"fill:{couleur}").replace('fill="currentColor"', f'fill="{couleur}"')
    picto = re.sub(r"fill-opacity:0?\.\d+", "fill-opacity:0.9", picto)
    return picto


def lire_index(chemin):
    lecteur = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",))
    lecteur.optionxform = str
    with open(chemin, encoding="utf-8") as fichier:
        lecteur.read_file(fichier)
    return lecteur


def ecrire_index(chemin, breeze, nom, commentaire, parents, repertoires):
    """index.theme : les rubriques (taille, contexte) de Breeze pour les seuls répertoires où l'on a écrit quelque chose."""
    entete = breeze["Icon Theme"]
    liste = [d for d in entete["Directories"].split(",") if d in repertoires]
    mises_a_l_echelle = [d for d in entete.get("ScaledDirectories", "").split(",") if d in repertoires]
    lignes = ["[Icon Theme]", f"Name={nom}", f"Comment={commentaire}", f"Inherits={parents}", "FollowsColorScheme=true",
              "Directories=" + ",".join(liste)]
    if mises_a_l_echelle:
        lignes.append("ScaledDirectories=" + ",".join(mises_a_l_echelle))
    for rubrique in liste + mises_a_l_echelle:
        if breeze.has_section(rubrique):
            lignes += ["", f"[{rubrique}]"] + [f"{cle}={valeur}" for cle, valeur in breeze.items(rubrique)]
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write("\n".join(lignes) + "\n")


def dossier_binixx(texte, nom, sombre):
    """Le dossier BinixX qui remplace ce SVG de Breeze ; None si ce n'est pas un dossier de Breeze reconnu."""
    vue = VUE.search(texte)
    if not vue:
        return None
    taille = float(vue.group(1))
    face, onglet, couleur_picto = nuances(couleur_de(nom), sombre)
    if taille <= PETITES:
        # petit dossier de Breeze : un seul tracé au trait ; on dessine le dossier plein, sans pictogramme
        if texte.count("<path") < 1:
            return None
        return dossier_svg(taille, face, onglet, sombre=sombre)
    picto = pictogramme(texte, taille)
    if picto is None:
        return None
    return dossier_svg(taille, face, onglet, colorier_pictogramme(picto, couleur_picto), sombre)


def fabriquer(dossier_themes="/usr/share/icons", breeze_dir=None, minimum=30):
    """Écrit binixx-os et binixx-os-dark ; (dossiers redessinés, liens refaits). minimum : nombre de dossiers de Breeze attendus au moins."""
    breeze_dir = breeze_dir or os.path.join(dossier_themes, "breeze")
    themes = {NOM: False, NOM_SOMBRE: True}
    for nom in themes:
        shutil.rmtree(os.path.join(dossier_themes, nom), ignore_errors=True)
    modifies = set()   # chemins réels (dans Breeze) des dossiers redessinés
    repertoires = set()
    for racine, _, fichiers in os.walk(os.path.join(breeze_dir, "places")):
        for nom in fichiers:
            chemin = os.path.join(racine, nom)
            if not nom.startswith("folder") or not nom.endswith(".svg") or os.path.islink(chemin):
                continue
            with open(chemin, encoding="utf-8") as fichier:
                texte = fichier.read()
            relatif = os.path.relpath(chemin, breeze_dir)
            ecrit = False
            for theme, sombre in themes.items():
                nouveau = dossier_binixx(texte, nom, sombre)
                if nouveau is None:
                    continue
                cible = os.path.join(dossier_themes, theme, relatif)
                os.makedirs(os.path.dirname(cible), exist_ok=True)
                with open(cible, "w", encoding="utf-8") as fichier:
                    fichier.write(nouveau)
                ecrit = True
            if ecrit:
                modifies.add(os.path.realpath(chemin))
                repertoires.add(os.path.dirname(relatif))
    attendus = [os.path.join(breeze_dir, "places", t, f"folder{s}.svg") for t in ("64",) for s in ("", "-documents", "-pictures")]
    if len(modifies) < minimum or not all(os.path.realpath(a) in modifies for a in attendus):
        raise SystemExit(f"{len(modifies)} dossiers de Breeze reconnus seulement : le dessin de ses dossiers a changé, à revoir")
    # Les liens de Breeze (n'importe où dans le thème) qui aboutissent à l'un de ces dossiers : refaits à l'identique dans chaque
    # thème, donc ils visent le dossier BinixX (le texte du lien est relatif au thème)
    liens = 0
    for racine, dossiers, fichiers in os.walk(breeze_dir):
        for nom in fichiers + [d for d in dossiers if os.path.islink(os.path.join(racine, d))]:
            chemin = os.path.join(racine, nom)
            if os.path.islink(chemin) and os.path.realpath(chemin) in modifies:
                relatif = os.path.relpath(chemin, breeze_dir)
                for theme in themes:
                    cible = os.path.join(dossier_themes, theme, relatif)
                    os.makedirs(os.path.dirname(cible), exist_ok=True)
                    if not os.path.lexists(cible):
                        os.symlink(os.readlink(chemin), cible)
                liens += 1
                repertoires.add(os.path.dirname(relatif))
    breeze = lire_index(os.path.join(breeze_dir, "index.theme"))
    ecrire_index(os.path.join(dossier_themes, NOM, "index.theme"), breeze, "BinixX OS",
                 "Icônes de Breeze avec les dossiers pastel de BinixX OS", "breeze", repertoires)
    ecrire_index(os.path.join(dossier_themes, NOM_SOMBRE, "index.theme"), breeze, "BinixX OS sombre",
                 "Icônes de Breeze sombre avec les dossiers de BinixX OS en tons profonds", "breeze-dark", repertoires)
    # Licence de Breeze et note sur ce qui a été modifié
    for theme in themes:
        dossier = os.path.join(dossier_themes, theme)
        licences = "/usr/share/licenses/breeze-icon-theme"
        if os.path.isdir(licences):
            for fichier in os.listdir(licences):
                shutil.copy2(os.path.join(licences, fichier), os.path.join(dossier, fichier))
        with open(os.path.join(dossier, "LISEZMOI.txt"), "w", encoding="utf-8") as fichier:
            fichier.write(
                "Icônes de BinixX OS : dérivées de Breeze (KDE, paquet breeze-icon-theme), LGPL-3.0 ou plus récente.\n"
                "Seule modification : chaque dossier est redessiné (forme arrondie, couleur pastel selon son contenu) en gardant le\n"
                "pictogramme de Breeze, recoloré. Fichiers générés à la construction de l'image par build_files/icones-binixx.py ;\n"
                "les autres icônes sont celles de Breeze.\n")
    return len(modifies), liens


if __name__ == "__main__":
    dossier_themes = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/icons"
    breeze_source = sys.argv[2] if len(sys.argv) > 2 else None
    dossiers, liens = fabriquer(dossier_themes, breeze_source)
    print(f"{NOM}, {NOM_SOMBRE} : {dossiers} dossiers pastel, {liens} liens refaits (depuis Breeze)")
