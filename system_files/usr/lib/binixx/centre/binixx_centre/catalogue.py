"""Catalogue « Mon logiciel Windows » : lecture du fichier, recherche, déduction d'un nom de programme.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_catalogue.py).
"""

import csv
import glob
import os
import re
import unicodedata
from dataclasses import dataclass

CATALOGUE = "/usr/share/binixx/catalogue-windows/catalogue.tsv"
LISTES_FLATPAK = ("/usr/share/binixx/flatpaks/system-flatpaks.list", "/usr/share/binixx/flatpaks/system-flatpaks.d/*.list")
TYPES = ("inclus", "flatpak", "web", "info", "windows")

# Mots sans intérêt dans le nom d'un fichier d'installation (setup_sage_x64.exe → « sage »)
BRUIT = {"setup", "install", "installer", "installation", "win", "windows", "winx", "full", "offline", "online",
         "latest", "update", "version", "release", "stable", "free", "fra", "french", "msi", "exe", "x64", "x86",
         "amd", "setups", "web", "stub", "bundle", "set"}


# Un pictogramme (voir icones.py) par catégorie du catalogue, pour les pages qui les montrent
ICONES_CATEGORIES = {
    "Accès à distance": "monitor", "Bureautique": "file-text", "Communication": "mail",
    "Compatibilité Windows": "layers", "Comptabilité et gestion": "briefcase", "Documents PDF": "file",
    "Développement": "code", "Fichiers et cloud": "cloud", "Images et design": "image", "Jeux": "gamepad",
    "Navigateur": "globe", "Sécurité": "shield", "Technique": "settings", "Utilitaires": "sliders",
    "Vidéo et audio": "play-circle",
}


def icone_de(categorie):
    """Le pictogramme d'une catégorie du catalogue (un colis pour une catégorie inconnue)."""
    return ICONES_CATEGORIES.get(categorie, "package")


BADGES = {
    "inclus": "Déjà installé",
    "web": "En ligne",
    "info": "Bon à savoir",
    "windows": "Pas d'équivalent direct",
}


@dataclass(frozen=True)
class Entree:
    windows: str
    alias: tuple
    categorie: str
    type: str
    cible: str
    remplacant: str
    remarque: str


def normaliser(texte):
    """Minuscules, sans accents, sans ponctuation : « Éditeur-PDF » → « editeur pdf »."""
    sans_accent = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", sans_accent.lower()).strip()


def charger(chemin=None):
    """Lit le catalogue ; ValueError (avec le numéro de ligne) si une ligne est mal formée.

    BINIXX_CATALOGUE désigne un autre fichier (tests, essais)."""
    chemin = chemin or os.environ.get("BINIXX_CATALOGUE", CATALOGUE)
    entrees = []
    with open(chemin, encoding="utf-8", newline="") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            ligne = ligne.rstrip("\n")
            if not ligne or ligne.startswith("#"):
                continue
            champs = ligne.split("\t")
            if len(champs) != 7:
                raise ValueError(f"{chemin}:{numero} : {len(champs)} colonnes au lieu de 7")
            windows, alias, categorie, type_, cible, remplacant, remarque = champs
            if type_ not in TYPES:
                raise ValueError(f"{chemin}:{numero} : type « {type_} » inconnu")
            if type_ in ("inclus", "flatpak", "web") and not cible:
                raise ValueError(f"{chemin}:{numero} : cible manquante pour « {windows} »")
            if type_ == "web" and not cible.startswith("https://"):
                raise ValueError(f"{chemin}:{numero} : adresse web non https")
            entrees.append(Entree(windows, tuple(a for a in alias.split(";") if a), categorie, type_, cible,
                                  remplacant, remarque))
    return entrees


def chercher(entrees, requete):
    """Entrées qui répondent à `requete` (tous les mots doivent y figurer), les plus pertinentes d'abord.

    Une requête vide renvoie tout le catalogue, par catégorie.
    """
    mots = normaliser(requete).split()
    if not mots:
        return sorted(entrees, key=lambda e: (normaliser(e.categorie), normaliser(e.windows)))
    resultats = []
    for entree in entrees:
        nom = normaliser(entree.windows)
        alias = [normaliser(a) for a in entree.alias]
        texte = " ".join([nom, *alias, normaliser(entree.remplacant), normaliser(entree.categorie)])
        if not all(mot in texte for mot in mots):
            continue
        score = 0
        for mot in mots:
            if nom.startswith(mot) or any(a.startswith(mot) for a in alias):
                score += 3
            elif mot in nom.split() or mot in alias:
                score += 2
            else:
                score += 1
        resultats.append((-score, nom, entree))
    return [entree for _, _, entree in sorted(resultats, key=lambda r: r[:2])]


def deviner_programme(chemin):
    """Mots à chercher d'après le nom d'un fichier .exe ou .msi : « Setup_Sage100_v2023.exe » → « Sage »."""
    nom = os.path.splitext(os.path.basename(chemin))[0]
    mots = [m for m in re.findall(r"[^\W\d_]+", nom) if len(m) >= 3 and m.lower() not in BRUIT]
    return " ".join(mots[:2])


def chercher_fichier(entrees, chemin):
    """(requête, résultats) pour un fichier .exe ou .msi : le nom du programme, puis des débuts de plus en
    plus courts (« AcroRdrDC » ne répond à rien, « acro » trouve Acrobat Reader)."""
    requete = deviner_programme(chemin)
    mots = requete.split()
    if not mots:
        return "", []
    resultats = chercher(entrees, requete)
    premier = mots[0]
    longueur = len(premier)
    while not resultats and longueur > 4:
        longueur -= 1
        requete = premier[:longueur].lower()
        resultats = chercher(entrees, requete)
    return (requete if resultats else " ".join(mots)), resultats


def fournies(listes=LISTES_FLATPAK):
    """Identifiants Flatpak installés par BinixX OS au premier démarrage (listes de l'image)."""
    fichiers = []
    for motif in listes:
        fichiers.extend(sorted(glob.glob(motif)))
    identifiants = set()
    for fichier in fichiers:
        with open(fichier, encoding="utf-8") as lecture:
            for ligne in lecture:
                ligne = ligne.split("#", 1)[0].strip()
                if ligne:
                    identifiants.add(ligne)
    return identifiants


def etat(entree, installees, fournies):
    """(texte du badge, libellé du bouton ou None, action ou None) ; l'action est (genre, cible), voir launch.executer."""
    if entree.type == "inclus":
        return BADGES["inclus"], "Ouvrir", ("app", entree.cible)
    if entree.type == "web":
        return BADGES["web"], "Ouvrir le site", ("url", entree.cible)
    if entree.type == "flatpak":
        if entree.cible in installees:
            return "Installé", "Ouvrir", ("flatpak", entree.cible)
        if entree.cible in fournies:
            return "Installé au premier démarrage", "Voir dans Discover", ("discover", entree.cible)
        return "À installer depuis Flathub", "Installer", ("discover", entree.cible)
    return BADGES[entree.type], None, None


@dataclass(frozen=True)
class Remplacant:
    """Une application qui remplace plusieurs logiciels Windows (Heroic : Epic Games Store et GOG Galaxy)."""
    nom: str
    entree: Entree  # la première entrée qui la propose : type, cible et remarque
    remplace: tuple


def remplacants(entrees, categorie):
    """Applications de la catégorie, chacune avec les logiciels Windows qu'elle remplace (ordre du catalogue)."""
    trouves = {}
    for entree in entrees:
        if entree.categorie != categorie:
            continue
        cle = (entree.type, entree.cible)
        if cle in trouves:
            trouves[cle] = Remplacant(trouves[cle].nom, trouves[cle].entree, trouves[cle].remplace + (entree.windows,))
        else:
            trouves[cle] = Remplacant(entree.remplacant, entree, (entree.windows,))
    return list(trouves.values())
