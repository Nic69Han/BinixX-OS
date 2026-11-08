"""Aiguillage des programmes Windows (.exe, .msi) : avec quoi les ouvrir sous BinixX OS ?

Trois chemins, du plus léger au plus lourd :
  - un équivalent BinixX OS (catalogue « Mon logiciel Windows ») : le mieux quand il existe ;
  - Wine, par Bottles (Flatpak) : le programme tourne directement, sans Windows, dans une « bouteille » BinixX à part ;
    marche avec beaucoup de logiciels, pas tous ;
  - Windows lui-même, en arrière-plan (WinBoat) : le plus compatible, mais lourd (machine virtuelle, licence Windows).

Le choix fait pour un programme peut être retenu (~/.config/binixx/moteurs-windows.json) : les fois suivantes, il s'ouvre
directement. Aucune dépendance à Qt : testé seul (tests/image/centre/test_moteurs.py) ; la fenêtre est
aiguillage_fenetre.py.

    binixx-ouvrir-windows FICHIER             la fenêtre de choix, ou le choix retenu
    binixx-ouvrir-windows --choisir FICHIER   la fenêtre de choix, même si un choix est retenu
    binixx-ouvrir-windows --moteur wine FICHIER   ouvre avec Wine (menu du clic droit)
    binixx-ouvrir-windows --json FICHIER      le conseil, sans fenêtre (support, tests)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass

from . import catalogue

BOTTLES = "com.usebottles.bottles"
BOUTEILLE = "BinixX"  # la bouteille où s'installent les programmes Windows ouverts depuis BinixX OS
WINDOWS_REQUIS = "/usr/share/binixx/catalogue-windows/windows-requis.tsv"
MOTEURS = ("equivalent", "wine", "windows")
EXTENSIONS = (".exe", ".msi")
DOSSIERS_LANCEURS = ("/usr/share/applications", "/usr/local/share/applications", "~/.local/share/applications",
                     "/var/lib/flatpak/exports/share/applications", "~/.local/share/flatpak/exports/share/applications")


@dataclass(frozen=True)
class Conseil:
    moteur: str             # « equivalent », « wine » ou « windows »
    raison: str             # une phrase pour l'utilisateur
    equivalent: object      # l'entrée du catalogue qui remplace le programme (ou None)
    retenu: bool = False    # le choix vient de l'utilisateur (« Retenir ce choix »)


# --- Programmes qui ne marchent pas avec Wine ------------------------------------------------------------------------------

def charger_windows_requis(chemin=None):
    """[(mots normalisés, raison)] : les programmes connus pour ne pas marcher avec Wine. ValueError si une ligne est mal
    formée. BINIXX_WINDOWS_REQUIS désigne un autre fichier (tests)."""
    chemin = chemin or os.environ.get("BINIXX_WINDOWS_REQUIS", WINDOWS_REQUIS)
    regles = []
    with open(chemin, encoding="utf-8") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            ligne = ligne.rstrip("\n")
            if not ligne or ligne.startswith("#"):
                continue
            champs = ligne.split("\t")
            if len(champs) != 2 or not champs[0] or not champs[1]:
                raise ValueError(f"{chemin}:{numero} : 2 colonnes attendues (mots, raison)")
            mots = tuple(m for m in (catalogue.normaliser(m).replace(" ", "") for m in champs[0].split(";")) if m)
            if not mots:
                raise ValueError(f"{chemin}:{numero} : aucun mot")
            regles.append((mots, champs[1]))
    return regles


def windows_requis(regles, chemin):
    """La raison pour laquelle ce programme demande Windows, ou None. Les mots sont cherchés dans le nom du fichier,
    sans séparateurs : « Photoshop_Set-Up.exe » → « photoshopsetup » contient « photoshop »."""
    nom = catalogue.normaliser(os.path.splitext(os.path.basename(chemin))[0]).replace(" ", "")
    for mots, raison in regles:
        if any(mot in nom for mot in mots):
            return raison
    return None


# --- Choix retenus ---------------------------------------------------------------------------------------------------------

def fichier_memoire():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "binixx", "moteurs-windows.json")


def lire_memoire(chemin=None):
    """{chemin absolu du programme : moteur} ; vide si le fichier manque ou est abîmé."""
    try:
        with open(chemin or fichier_memoire(), encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, ValueError):
        return {}
    if not isinstance(donnees, dict):
        return {}
    return {k: v for k, v in donnees.items() if isinstance(k, str) and v in MOTEURS}


def retenir(programme, moteur, chemin=None):
    """Retient le moteur d'un programme (None : oublie). Écriture atomique."""
    chemin = chemin or fichier_memoire()
    memoire = lire_memoire(chemin)
    programme = os.path.abspath(programme)
    if moteur is None:
        memoire.pop(programme, None)
    elif moteur in MOTEURS:
        memoire[programme] = moteur
    else:
        raise ValueError(f"moteur inconnu : {moteur}")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    provisoire = chemin + ".tmp"
    with open(provisoire, "w", encoding="utf-8") as fichier:
        json.dump(memoire, fichier, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(provisoire, chemin)


# --- Le conseil ------------------------------------------------------------------------------------------------------------

def conseiller(programme, entrees, regles, memoire=None):
    """Le chemin conseillé pour ouvrir `programme` : le choix retenu, sinon un équivalent du catalogue, sinon Windows
    pour les programmes connus pour ne pas marcher avec Wine, sinon Wine."""
    _, resultats = catalogue.chercher_fichier(entrees, programme)
    premier = resultats[0] if resultats else None
    equivalent = premier if premier is not None and premier.type in ("inclus", "flatpak", "web") else None
    retenu = (memoire or {}).get(os.path.abspath(programme))
    if retenu and (retenu != "equivalent" or equivalent is not None):
        return Conseil(retenu, "Votre choix pour ce programme.", equivalent, retenu=True)
    if equivalent is not None:
        return Conseil("equivalent", f"{equivalent.remplacant} remplace {equivalent.windows} sous BinixX OS.", equivalent)
    raison = windows_requis(regles, programme)
    if raison:
        return Conseil("windows", raison, None)
    if premier is not None and premier.type == "windows":  # pas d'équivalent direct au catalogue (Sage, Access…)
        return Conseil("windows", premier.remarque, None)
    return Conseil("wine", "Beaucoup de programmes Windows s'ouvrent directement avec Wine, sans Windows.", None)


# --- Wine (Bottles) --------------------------------------------------------------------------------------------------------

def dossier_partage(programme, maison=None):
    """Ce que Bottles (Flatpak, sans accès aux fichiers) peut lire pour ouvrir le programme, en lecture seule : le dossier
    du programme (un installateur a souvent ses fichiers à côté de lui), mais seulement le fichier quand ce dossier est le
    dossier personnel ou la racine d'un disque, pour ne pas tout montrer."""
    programme = os.path.abspath(programme)
    dossier = os.path.dirname(programme)
    maison = os.path.abspath(maison or os.path.expanduser("~"))
    if dossier in (maison, os.path.dirname(maison), "/") or dossier.count("/") < 2:
        return programme
    return dossier


def bottles_cli(arguments, partage=None, flatpak="flatpak"):
    """Commande bottles-cli dans le Flatpak de Bottles ; `partage` : un chemin à lui montrer, en lecture seule."""
    argv = [flatpak, "run", "--command=bottles-cli"]
    if partage:
        argv.append(f"--filesystem={partage}:ro")
    return argv + [BOTTLES] + list(arguments)


def commande_installee(flatpak="flatpak"):
    """Code de sortie 0 si Bottles est installé."""
    return [flatpak, "info", BOTTLES]


def commande_lister(flatpak="flatpak"):
    return bottles_cli(["list", "bottles"], flatpak=flatpak)


def commande_creer(flatpak="flatpak"):
    return bottles_cli(["new", "--bottle-name", BOUTEILLE, "--environment", "application"], flatpak=flatpak)


def commande_lancer(programme, flatpak="flatpak"):
    """Ouvre le programme dans la bouteille BinixX ; jamais de shell, le chemin est un seul argument."""
    programme = os.path.abspath(programme)
    return bottles_cli(["run", "-b", BOUTEILLE, "-e", programme], partage=dossier_partage(programme), flatpak=flatpak)


def bouteille_existe(sortie):
    """La sortie de « bottles-cli list bottles » (« Found 2 bottles: » puis « - Nom ») contient-elle la bouteille BinixX ?"""
    return any(ligne.strip() == f"- {BOUTEILLE}" for ligne in sortie.splitlines())


# --- Windows (WinBoat) -----------------------------------------------------------------------------------------------------

def trouver_winboat(dossiers=DOSSIERS_LANCEURS):
    """Le lanceur de WinBoat (.desktop, installé par son RPM, son AppImage intégrée ou un Flatpak), ou None."""
    for dossier in dossiers:
        dossier = os.path.expanduser(dossier)
        try:
            noms = sorted(os.listdir(dossier))
        except OSError:
            continue
        for nom in noms:
            if nom.endswith(".desktop") and re.search(r"winboat", nom, re.IGNORECASE):
                return os.path.join(dossier, nom)
    return None


def windows_possible(verifications):
    """Le PC peut-il faire tourner Windows (aucune vérification de virtualisation.verifier en échec) ?"""
    return all(v.etat != "ko" for v in verifications)


# --- Ligne de commande -----------------------------------------------------------------------------------------------------

def _charger():
    """(entrées du catalogue, règles « Windows requis ») ; listes vides si un fichier manque."""
    try:
        entrees = catalogue.charger()
    except (OSError, ValueError):
        entrees = []
    try:
        regles = charger_windows_requis()
    except (OSError, ValueError):
        regles = []
    return entrees, regles


def parse(argv):
    parser = argparse.ArgumentParser(prog="binixx-ouvrir-windows",
                                     description="Ouvrir un programme Windows (.exe, .msi) sous BinixX OS")
    parser.add_argument("fichier", help="le programme Windows")
    groupe = parser.add_mutually_exclusive_group()
    groupe.add_argument("--choisir", action="store_true", help="montrer les choix, même si un choix est retenu")
    groupe.add_argument("--moteur", choices=MOTEURS, help="ouvrir directement avec ce moteur")
    groupe.add_argument("--json", action="store_true", help="afficher le conseil sans fenêtre")
    groupe.add_argument("--oublier", action="store_true", help="oublier le choix retenu pour ce programme")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)
    programme = os.path.abspath(args.fichier)
    if args.oublier:
        retenir(programme, None)
        return 0
    entrees, regles = _charger()
    if args.json:
        conseil = conseiller(programme, entrees, regles, lire_memoire())
        print(json.dumps({"moteur": conseil.moteur, "raison": conseil.raison, "retenu": conseil.retenu,
                          "equivalent": conseil.equivalent.remplacant if conseil.equivalent else None,
                          "wine": commande_lancer(programme)}, ensure_ascii=False))
        return 0
    if not os.path.isfile(programme):
        print(f"{programme} : fichier introuvable", file=sys.stderr)
        return 2
    from . import aiguillage_fenetre  # Qt seulement pour la fenêtre
    if args.moteur:
        return aiguillage_fenetre.main(programme, entrees, regles, moteur=args.moteur)
    memoire = {} if args.choisir else lire_memoire()
    conseil = conseiller(programme, entrees, regles, memoire)
    return aiguillage_fenetre.main(programme, entrees, regles, moteur=conseil.moteur if conseil.retenu else None)
