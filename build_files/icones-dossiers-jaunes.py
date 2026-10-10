#!/usr/bin/env python3
"""Icônes de BinixX OS : celles de Breeze, avec des dossiers jaunes (comme ceux de Windows) au lieu de dossiers à la couleur d'accent.

Dans Breeze, un dossier prend la couleur d'accentuation du bureau (le bleu de BinixX OS) : le corps du dossier est un tracé
« fill:currentColor » de classe « ColorScheme-Accent ». Ce script copie chaque dossier de ce genre dans un thème d'icônes à part
en remplaçant seulement cette couleur par le jaune de Breeze (#f2cb40, celui de son « dossier jaune »). Les ombres, le dessin et
les pictogrammes (Documents, Images, Musique…) ne changent pas ; les icônes qui ne sont pas des dossiers viennent de Breeze.
Aux petites tailles (16, 22 et 24 pixels), Breeze dessine ses dossiers d'un seul trait de la couleur du texte : « folder » et
« folder-open » passent en jaune (#fdbc4b, comme le dossier jaune de Breeze à ces tailles), les autres pictogrammes restent au trait.

Deux thèmes sont écrits dans /usr/share/icons, qui héritent de Breeze :
    binixx-os        Breeze + dossiers jaunes (Aube)
    binixx-os-dark   Breeze sombre + les mêmes dossiers jaunes (Nuit) : ses dossiers sont ceux de binixx-os (liens)
Les liens de Breeze vers un dossier (inode-directory, dossiers de l'application, etc.) sont refaits pour viser le dossier jaune.

Généré depuis le paquet breeze-icon-theme de l'image, donc à chaque construction : les mises à jour de Breeze sont suivies.
Les icônes de Breeze sont sous licence LGPL-3.0 ou plus récente (et CC-BY-SA-4.0 pour certaines) : le texte de la licence est copié
dans le thème, avec une note disant ce qui a été modifié.

    python3 build_files/icones-dossiers-jaunes.py [dossier des thèmes] [dossier de Breeze]
"""
import configparser
import os
import re
import shutil
import sys

JAUNE = "#f2cb40"
JAUNE_PETIT = "#fdbc4b"   # celui du « dossier jaune » de Breeze en 16, 22 et 24 pixels (dessin d'un seul tracé, sans ombres)
NOM = "binixx-os"
NOM_SOMBRE = "binixx-os-dark"
# Le corps d'un dossier de Breeze : un tracé rempli de la couleur d'accent
CORPS = re.compile(r'(<path\b[^>]*?style="[^"]*?)fill:currentColor([^"]*"[^>]*?class="ColorScheme-Accent"[^>]*>)', re.S)
CORPS_INVERSE = re.compile(r'(<path\b[^>]*?class="ColorScheme-Accent"[^>]*?style="[^"]*?)fill:currentColor([^"]*"[^>]*>)', re.S)


def figer_les_couleurs(texte):
    """Le SVG ne reçoit plus les couleurs du bureau (l'identifiant de sa feuille de style est ce que l'application cherche) : les
    pictogrammes gardent la couleur sombre de Breeze. Sinon, sous le thème sombre, ils prendraient le blanc du texte et
    disparaîtraient sur le jaune du dossier."""
    return texte.replace('id="current-color-scheme"', 'id="couleurs-fixes-binixx"')


def jaunir(texte):
    """Le texte du SVG avec le corps du dossier en jaune ; None si ce n'est pas un dossier à la couleur d'accent."""
    nouveau, n1 = CORPS.subn(lambda m: m.group(1) + "fill:" + JAUNE + m.group(2), texte)
    nouveau, n2 = CORPS_INVERSE.subn(lambda m: m.group(1) + "fill:" + JAUNE + m.group(2), nouveau)
    return figer_les_couleurs(nouveau) if n1 + n2 == 1 else None


# Petits dossiers (16, 22 et 24 pixels) : un seul tracé, de la couleur du texte ; seuls « folder » et « folder-open » passent en jaune,
# comme le fait Breeze pour son dossier jaune (les autres sont des pictogrammes au trait, qui restent de la couleur du texte)
PETIT_CORPS = re.compile(r'(<path\b[^>]*?style="[^"]*?)fill:currentColor([^"]*"[^>]*?class="ColorScheme-Text"[^>]*>)', re.S)
PETIT_CORPS_INVERSE = re.compile(r'(<path\b[^>]*?class="ColorScheme-Text"[^>]*?style="[^"]*?)fill:currentColor([^"]*"[^>]*>)', re.S)
TAILLE = re.compile(r'viewBox="0 0 (\d+) \d+"')


def jaunir_petit(texte):
    """Le texte du SVG d'un petit dossier (24 pixels au plus, un seul tracé) en jaune ; None sinon."""
    taille = TAILLE.search(texte)
    if not taille or int(taille.group(1)) > 24 or texte.count("<path") != 1:
        return None
    nouveau, n1 = PETIT_CORPS.subn(lambda m: m.group(1) + "fill:" + JAUNE_PETIT + m.group(2), texte)
    nouveau, n2 = PETIT_CORPS_INVERSE.subn(lambda m: m.group(1) + "fill:" + JAUNE_PETIT + m.group(2), nouveau)
    return figer_les_couleurs(nouveau) if n1 + n2 == 1 else None


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


def fabriquer(dossier_themes="/usr/share/icons", breeze_dir=None):
    breeze_dir = breeze_dir or os.path.join(dossier_themes, "breeze")
    sortie = os.path.join(dossier_themes, NOM)
    sombre = os.path.join(dossier_themes, NOM_SOMBRE)
    for dossier in (sortie, sombre):
        shutil.rmtree(dossier, ignore_errors=True)
    modifies = set()   # chemins réels (dans Breeze) des dossiers rendus jaunes
    repertoires = set()
    for racine, _, fichiers in os.walk(os.path.join(breeze_dir, "places")):
        for nom in fichiers:
            chemin = os.path.join(racine, nom)
            if not nom.startswith("folder") or not nom.endswith(".svg") or os.path.islink(chemin):
                continue
            with open(chemin, encoding="utf-8") as fichier:
                texte = fichier.read()
            jaune = jaunir(texte)
            if jaune is None and nom in ("folder.svg", "folder-open.svg"):
                jaune = jaunir_petit(texte)
            if jaune is None:
                continue
            relatif = os.path.relpath(chemin, breeze_dir)
            cible = os.path.join(sortie, relatif)
            os.makedirs(os.path.dirname(cible), exist_ok=True)
            with open(cible, "w", encoding="utf-8") as fichier:
                fichier.write(jaune)
            modifies.add(os.path.realpath(chemin))
            repertoires.add(os.path.dirname(relatif))
    if not modifies:
        raise SystemExit("Aucun dossier à la couleur d'accent trouvé dans Breeze : le dessin de ses dossiers a changé, à revoir")
    # Les liens de Breeze (n'importe où dans le thème) qui aboutissent à l'un de ces dossiers : refaits à l'identique, donc ils visent
    # le dossier jaune (le texte du lien est relatif au thème)
    liens = 0
    for racine, dossiers, fichiers in os.walk(breeze_dir):
        for nom in fichiers + [d for d in dossiers if os.path.islink(os.path.join(racine, d))]:
            chemin = os.path.join(racine, nom)
            if os.path.islink(chemin) and os.path.realpath(chemin) in modifies:
                relatif = os.path.relpath(chemin, breeze_dir)
                cible = os.path.join(sortie, relatif)
                os.makedirs(os.path.dirname(cible), exist_ok=True)
                if not os.path.lexists(cible):
                    os.symlink(os.readlink(chemin), cible)
                    liens += 1
                repertoires.add(os.path.dirname(relatif))
    breeze = lire_index(os.path.join(breeze_dir, "index.theme"))
    ecrire_index(os.path.join(sortie, "index.theme"), breeze, "BinixX OS",
                 "Icônes de Breeze avec des dossiers jaunes", "breeze", repertoires)
    # Thème sombre : mêmes dossiers (liens vers ceux du thème clair), icônes de Breeze sombre pour le reste
    os.makedirs(sombre)
    for entree in sorted(os.listdir(sortie)):
        if entree != "index.theme":
            os.symlink(os.path.join("..", NOM, entree), os.path.join(sombre, entree))
    ecrire_index(os.path.join(sombre, "index.theme"), breeze, "BinixX OS sombre",
                 "Icônes de Breeze sombre avec des dossiers jaunes", "breeze-dark", repertoires)
    # Licence de Breeze et note sur ce qui a été modifié
    for dossier in (sortie,):
        licences = "/usr/share/licenses/breeze-icon-theme"
        if os.path.isdir(licences):
            for fichier in os.listdir(licences):
                shutil.copy2(os.path.join(licences, fichier), os.path.join(dossier, fichier))
        with open(os.path.join(dossier, "LISEZMOI.txt"), "w", encoding="utf-8") as fichier:
            fichier.write(
                "Icônes de BinixX OS : dérivées de Breeze (KDE, paquet breeze-icon-theme), LGPL-3.0 ou plus récente.\n"
                f"Seule modification : dans chaque dossier qui prend la couleur d'accentuation, cette couleur devient le jaune {JAUNE}\n"
                "(celui du « dossier jaune » de Breeze). Fichiers générés à la construction de l'image par\n"
                "build_files/icones-dossiers-jaunes.py ; les autres icônes sont celles de Breeze.\n")
    return len(modifies), liens


if __name__ == "__main__":
    themes = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/icons"
    breeze_source = sys.argv[2] if len(sys.argv) > 2 else None
    dossiers, liens = fabriquer(themes, breeze_source)
    print(f"{NOM}, {NOM_SOMBRE} : {dossiers} dossiers jaunes, {liens} liens refaits (depuis Breeze)")
