#!/usr/bin/env python3
"""Variantes opaques des thèmes Win11OS KDE : BinixX-Win11-light et BinixX-Win11-dark.

Les thèmes de Win11OS KDE rendent les fenêtres des applications (Kvantum) et les fenêtres de Plasma (barre des tâches, menu de démarrage,
bulles) translucides, en comptant sur l'effet « flou » de KWin pour que ce soit lisible, comme l'acrylique de Windows 11. Sans flou (PC sans
accélération graphique, machine virtuelle, bureau à distance), on voit à travers : les fenêtres du dessous se lisent par-dessus le menu de
démarrage et le texte devient illisible (constaté dans le test VM). BinixX OS vise aussi de vieux PC : il livre donc ces variantes, **opaques
dans tous les cas**, et les pose par défaut. Les thèmes d'origine restent installés, inchangés : on peut les choisir à la main (Kvantum
Manager, Configuration du système → Style de Plasma) pour retrouver la transparence sur un PC qui sait flouter.

Ce que ce script fait, à la construction de l'image, à partir des fichiers de Win11OS KDE copiés sans modification dans /usr/share :
  - Kvantum : une copie du thème dont les réglages de transparence et de flou sont coupés (fenêtres, menus, vue de Dolphin, panneau
    latéral) ; le dessin (fichier .svg) est le même ;
  - Plasma : un thème fait de liens vers celui d'origine. Plasma lit les fonds de la barre des tâches, du menu de démarrage, des bulles et
    des info-bulles dans trois endroits selon l'état de l'écran : « solid » sans composition, « translucent » avec le flou de KWin, et les
    dossiers « dialogs » et « widgets » eux-mêmes (translucides) avec composition mais sans flou : le cas d'une machine virtuelle, d'un
    vieux PC ou d'un bureau à distance, celui que le test VM a montré. Les trois mènent donc ici aux fonds opaques de « solid » : « solid »
    et « translucent » par un lien, « dialogs » et « widgets » par des liens fichier par fichier, ceux d'origine qui ont un équivalent opaque
    étant écartés. Sa section « Wallpaper » (qui nomme des fonds d'écran que BinixX OS ne livre pas) est retirée.
La construction échoue si l'un des réglages attendus a disparu du thème d'origine : mieux vaut cela que des fenêtres redevenues
translucides sans que personne le sache.

    python3 build_files/win11os-opaque.py [/usr/share]
"""
import os
import re
import shutil
import sys

VARIANTES = ("light", "dark")
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


def plasma_metadata(texte, amont, aval):
    """metadata.desktop d'origine sous le nom de la variante, sans la section Wallpaper."""
    texte = texte.replace(amont, aval)
    texte, n = re.subn(r"\n\[Wallpaper\]\n(?:[^\[\n][^\n]*\n|\n(?!\[))*", "\n", texte)
    if n != 1:
        raise SystemExit(f"{amont}/metadata.desktop : section [Wallpaper] introuvable, le thème d'origine a changé, à revoir")
    if aval not in texte or "Wallpaper" in texte:
        raise SystemExit(f"{amont}/metadata.desktop : nom ou section Wallpaper mal remplacés")
    return texte


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


def fabriquer(racine="/usr/share"):
    for variante in VARIANTES:
        amont, aval = f"Win11OS-{variante}", f"BinixX-Win11-{variante}"
        # Kvantum
        source, cible = os.path.join(racine, "Kvantum", amont), os.path.join(racine, "Kvantum", aval)
        shutil.rmtree(cible, ignore_errors=True)
        os.makedirs(cible)
        with open(os.path.join(source, f"{amont}.kvconfig"), encoding="utf-8") as fichier:
            texte = kvantum_opaque(fichier.read(), amont, aval)
        with open(os.path.join(cible, f"{aval}.kvconfig"), "w", encoding="utf-8") as fichier:
            fichier.write(texte)
        shutil.copy2(os.path.join(source, f"{amont}.svg"), os.path.join(cible, f"{aval}.svg"))
        # Plasma
        source, cible = os.path.join(racine, "plasma", "desktoptheme", amont), os.path.join(racine, "plasma", "desktoptheme", aval)
        shutil.rmtree(cible, ignore_errors=True)
        os.makedirs(cible)
        if not os.path.isdir(os.path.join(source, "solid")):
            raise SystemExit(f"{amont} : dossier « solid » introuvable, le thème d'origine a changé, à revoir")
        for entree in sorted(os.listdir(source)):
            if entree == "metadata.desktop":
                with open(os.path.join(source, entree), encoding="utf-8") as fichier:
                    texte = plasma_metadata(fichier.read(), amont, aval)
                with open(os.path.join(cible, entree), "w", encoding="utf-8") as fichier:
                    fichier.write(texte)
            elif os.path.isdir(os.path.join(source, "solid", entree)):
                opaques_a_la_place(source, cible, amont, entree)
            else:
                # « translucent » mène aux fonds opaques ; le reste est celui du thème d'origine
                os.symlink(os.path.join("..", amont, "solid" if entree == "translucent" else entree), os.path.join(cible, entree))


if __name__ == "__main__":
    dossier = sys.argv[1] if len(sys.argv) > 1 else "/usr/share"
    fabriquer(dossier)
    print("BinixX-Win11-light, BinixX-Win11-dark : variantes opaques de Kvantum et du thème Plasma de Win11OS KDE")
