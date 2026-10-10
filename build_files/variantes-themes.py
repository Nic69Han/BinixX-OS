#!/usr/bin/env python3
"""Variantes des thèmes de BinixX OS, fabriquées à la construction de l'image : « verre adaptatif » pour Aube et Nuit, opaque pour le
contraste élevé.

Les thèmes de Win11OS KDE rendent les fenêtres des applications (Kvantum) et les fenêtres de Plasma (barre des tâches, menu de démarrage,
bulles) translucides, en comptant sur l'effet « flou » de KWin pour que ce soit lisible, comme l'acrylique de Windows 11 ou le « Liquid
Glass » d'Apple. Sans flou (PC sans accélération graphique, machine virtuelle, bureau à distance), on voit à travers : les fenêtres du
dessous se lisent par-dessus le menu de démarrage et le texte devient illisible (constaté dans le test VM).

Plasma choisit lui-même le fond de ses fenêtres (libplasma : ThemePrivate::updateKSvgSelectors, DialogPrivate::updateTheme ; Panel.qml) :
  - dans « translucent/ » quand l'effet de flou de KWin est actif ;
  - dans les dossiers « dialogs/ » et « widgets/ » eux-mêmes quand il ne l'est pas ;
  - dans « solid/ » quand un élément demande un fond plein (la barre des tâches quand une fenêtre agrandie la touche, certaines
    info-bulles).
Les variantes s'appuient sur ce choix :
  - BinixX-Win11-light et BinixX-Win11-dark (thème Plasma d'Aube et de Nuit) : **verre adaptatif**. Avec le flou, le verre dépoli
    d'origine de Win11OS KDE (« translucent ») ; sans flou, les fonds pleins de « solid » à la place de ceux, translucides, de
    « dialogs/ » et « widgets/ ». Chaque PC a donc le plus beau rendu qu'il sait afficher lisiblement.
  - BinixX-Win11-light et BinixX-Win11-dark (thème Kvantum, fenêtres des applications) : **opaques**. Kvantum ne sait pas si le flou est
    là : ses réglages de transparence et de flou sont coupés, le dessin (fichier .svg) est le même. Comme le « Mica » de Windows 11, les
    fenêtres des applications restent pleines ; le verre est pour la barre des tâches, le menu et les bulles.
  - BinixX-contraste (thème Plasma du contraste élevé), à partir de Breeze (« default ») : **opaque dans tous les cas**, flou ou pas. Le
    contraste élevé sert à lire : rien ne doit transparaître derrière le texte.
Les thèmes d'origine restent installés, inchangés : on peut les choisir à la main (Kvantum Manager, Configuration du système → Style de
Plasma). Chaque variante est faite de liens vers son thème d'origine, plus ses propres métadonnées ; la section « Wallpaper » (qui nomme
des fonds d'écran que BinixX OS ne livre pas) en est retirée. La construction échoue si un réglage ou un fond attendu a disparu d'un
thème d'origine : mieux vaut cela que des fenêtres redevenues transparentes sans que personne le sache.

    python3 build_files/variantes-themes.py [/usr/share]
"""
import json
import os
import re
import shutil
import sys

VARIANTES = ("light", "dark")
CONTRASTE = ("default", "BinixX-contraste")
# Fonds que « solid » doit fournir : le menu de démarrage et les bulles (dialogs/background), les fenêtres de Plasma et la barre des tâches
FONDS_OPAQUES = {"dialogs": ("background",), "widgets": ("background", "panel-background")}
# Réglages Kvantum qui rendent quelque chose translucide ou flou : tous passent à « false »
KVANTUM_COUPES = ("translucent_windows", "blurring", "popup_blurring", "transparent_dolphin_view", "transparent_pcmanfm_sidepane",
                  "transparent_pcmanfm_view", "transparent_menutitle", "blur_translucent")


def kvantum_opaque(texte, amont, aval):
    """Le .kvconfig d'origine avec la transparence coupée ; SystemExit si un réglage attendu manque."""
    for cle in KVANTUM_COUPES:
        texte, n = re.subn(rf"^{cle}=.*$", f"{cle}=false", texte, flags=re.M)
        if n != 1:
            raise SystemExit(f"{amont}.kvconfig : « {cle} » trouvé {n} fois (une seule attendue) : le thème d'origine a changé, à revoir")
    texte, n = re.subn(r"^comment=(.*)$", r"comment=\1 (variante opaque de BinixX OS : sans transparence ni flou)", texte, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"{amont}.kvconfig : ligne « comment= » introuvable")
    return texte


def sans_section_wallpaper(texte, fichier):
    """Le fichier de réglages sans sa section [Wallpaper] ; SystemExit si elle n'y est pas (le thème d'origine a changé)."""
    texte, n = re.subn(r"(?:^|\n)\[Wallpaper\]\n(?:[^\[\n][^\n]*\n|\n(?!\[))*", "\n", texte)
    if n != 1 or "Wallpaper" in texte:
        raise SystemExit(f"{fichier} : section [Wallpaper] introuvable ou mal retirée, le thème d'origine a changé, à revoir")
    return texte.lstrip("\n")


def plasma_metadata_desktop(texte, amont, aval):
    """metadata.desktop d'origine (Win11OS KDE) sous le nom de la variante, sans la section Wallpaper."""
    texte = sans_section_wallpaper(texte.replace(amont, aval), f"{amont}/metadata.desktop")
    if aval not in texte:
        raise SystemExit(f"{amont}/metadata.desktop : nom mal remplacé")
    return texte


def plasma_metadata_json(texte, amont, aval, nom, description):
    """metadata.json d'origine (Breeze) sous le nom de la variante, sans les traductions du nom et de la description d'origine."""
    def sans_traductions(valeur):
        if isinstance(valeur, dict):
            return {cle: sans_traductions(v) for cle, v in valeur.items() if "[" not in cle}
        if isinstance(valeur, list):
            return [sans_traductions(v) for v in valeur]
        return valeur
    donnees = sans_traductions(json.loads(texte))
    greffon = donnees.get("KPlugin")
    if not isinstance(greffon, dict) or greffon.get("Id") != amont:
        raise SystemExit(f"{amont}/metadata.json : KPlugin.Id « {amont} » introuvable, le thème d'origine a changé, à revoir")
    greffon.update({"Id": aval, "Name": nom, "Description": description})
    return json.dumps(donnees, indent=4, ensure_ascii=False) + "\n"


def radical(nom):
    """Nom de fichier sans .svg ni .svgz : Plasma cherche « fond.svgz » avant « fond.svg », l'un cache donc l'autre."""
    return re.sub(r"\.svgz?$", "", nom)


def opaques_a_la_place(source, cible, amont, dossier):
    """Dossier « dialogs » ou « widgets » de la variante : les fichiers d'origine, sauf ceux que « solid » remplace par un fond opaque."""
    opaques = sorted(os.listdir(os.path.join(source, "solid", dossier)))
    remplaces = {radical(nom) for nom in opaques}
    for attendu in FONDS_OPAQUES[dossier]:
        if attendu not in remplaces:
            raise SystemExit(f"{amont}/solid/{dossier} : fond « {attendu} » introuvable, le thème d'origine a changé, à revoir")
    os.makedirs(os.path.join(cible, dossier))
    for nom in sorted(os.listdir(os.path.join(source, dossier))):
        if radical(nom) not in remplaces:
            os.symlink(os.path.join("..", "..", amont, dossier, nom), os.path.join(cible, dossier, nom))
    for nom in opaques:
        os.symlink(os.path.join("..", "..", amont, "solid", dossier, nom), os.path.join(cible, dossier, nom))


def plasma_variante(racine, amont, aval, verre, metadonnees):
    """Thème Plasma « aval » fait de liens vers « amont ». Sans flou : les fonds de « solid ». Avec le flou : le verre d'origine
    (« translucent ») si verre est vrai, « solid » sinon. metadonnees(nom de fichier, texte) donne les métadonnées de la variante."""
    source, cible = os.path.join(racine, "plasma", "desktoptheme", amont), os.path.join(racine, "plasma", "desktoptheme", aval)
    shutil.rmtree(cible, ignore_errors=True)
    os.makedirs(cible)
    for attendu in ("solid", "translucent"):
        if not os.path.isdir(os.path.join(source, attendu)):
            raise SystemExit(f"{amont} : dossier « {attendu} » introuvable, le thème d'origine a changé, à revoir")
    for entree in sorted(os.listdir(source)):
        chemin = os.path.join(source, entree)
        if entree in ("metadata.desktop", "metadata.json", "plasmarc"):
            with open(chemin, encoding="utf-8") as fichier:
                texte = metadonnees(entree, fichier.read())
            with open(os.path.join(cible, entree), "w", encoding="utf-8") as fichier:
                fichier.write(texte)
        elif os.path.isdir(os.path.join(source, "solid", entree)) and entree in FONDS_OPAQUES:
            opaques_a_la_place(source, cible, amont, entree)
        elif entree == "translucent" and not verre:
            os.symlink(os.path.join("..", amont, "solid"), os.path.join(cible, entree))
        else:
            os.symlink(os.path.join("..", amont, entree), os.path.join(cible, entree))
    for dossier in FONDS_OPAQUES:
        if not os.path.isdir(os.path.join(cible, dossier)) or os.path.islink(os.path.join(cible, dossier)):
            raise SystemExit(f"{amont} : dossier « {dossier} » (ou son équivalent dans « solid ») introuvable, le thème d'origine a changé")


def fabriquer(racine="/usr/share"):
    for variante in VARIANTES:
        amont, aval = f"Win11OS-{variante}", f"BinixX-Win11-{variante}"
        # Kvantum : opaque
        source, cible = os.path.join(racine, "Kvantum", amont), os.path.join(racine, "Kvantum", aval)
        shutil.rmtree(cible, ignore_errors=True)
        os.makedirs(cible)
        with open(os.path.join(source, f"{amont}.kvconfig"), encoding="utf-8") as fichier:
            texte = kvantum_opaque(fichier.read(), amont, aval)
        with open(os.path.join(cible, f"{aval}.kvconfig"), "w", encoding="utf-8") as fichier:
            fichier.write(texte)
        shutil.copy2(os.path.join(source, f"{amont}.svg"), os.path.join(cible, f"{aval}.svg"))

        # Plasma : verre adaptatif
        def metadonnees_win11(nom, texte, amont=amont, aval=aval):
            if nom == "metadata.desktop":
                return plasma_metadata_desktop(texte, amont, aval)
            raise SystemExit(f"{amont}/{nom} : fichier inattendu dans le thème d'origine, à revoir")
        plasma_variante(racine, amont, aval, True, metadonnees_win11)

    # Contraste élevé : Breeze, opaque dans tous les cas
    amont, aval = CONTRASTE

    def metadonnees_contraste(nom, texte):
        if nom == "metadata.json":
            return plasma_metadata_json(texte, amont, aval, "BinixX OS contraste élevé",
                                        "Breeze (KDE) toujours opaque, même avec le flou : variante de BinixX OS pour le contraste élevé")
        if nom == "plasmarc":
            return sans_section_wallpaper(texte, f"{amont}/plasmarc")
        raise SystemExit(f"{amont}/{nom} : fichier inattendu dans le thème d'origine, à revoir")
    plasma_variante(racine, amont, aval, False, metadonnees_contraste)


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else "/usr/share"
    fabriquer(dossier)
    print("BinixX-Win11-light, BinixX-Win11-dark : Kvantum opaque, Plasma en verre adaptatif (verre avec le flou, opaque sans) ; "
          "BinixX-contraste : Breeze toujours opaque")
