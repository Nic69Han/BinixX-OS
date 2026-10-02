"""Page « Paramètres » : lecture du fichier des réglages, recherche, modules KDE réellement présents.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_parametres.py).
"""

import os
import re
from dataclasses import dataclass

from . import catalogue

PARAMETRES = "/usr/share/nicos/parametres/parametres.tsv"
TYPES = ("kcm", "page", "app", "flatpak", "discover", "info")
MODES_DISCOVER = ("installed", "update", "browse")
KCM = re.compile(r"^kcm_[A-Za-z0-9_-]+$")
CLE_PAGE = re.compile(r"^[a-z][a-z0-9_]*$")
LANCEUR = re.compile(r"^[A-Za-z0-9._-]+$")
FLATPAK = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+){2,}$")


@dataclass(frozen=True)
class Reglage:
    categorie: str
    nom: str
    alias: tuple
    explication: str
    type: str
    cible: str


def charger(chemin=None):
    """Lit le fichier ; ValueError (avec le numéro de ligne) si une ligne est mal formée.

    NICOS_PARAMETRES désigne un autre fichier (tests, essais)."""
    chemin = chemin or os.environ.get("NICOS_PARAMETRES", PARAMETRES)
    reglages = []
    with open(chemin, encoding="utf-8", newline="") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            ligne = ligne.rstrip("\n")
            if not ligne or ligne.startswith("#"):
                continue
            champs = ligne.split("\t")
            if len(champs) == 5 and champs[4] == "info":  # la cible vide peut ne pas avoir sa tabulation
                champs.append("")
            if len(champs) != 6:
                raise ValueError(f"{chemin}:{numero} : {len(champs)} colonnes au lieu de 6")
            categorie, nom, alias, explication, type_, cible = champs
            controle = {"kcm": KCM, "page": CLE_PAGE, "app": LANCEUR, "flatpak": FLATPAK}.get(type_)
            if type_ not in TYPES:
                raise ValueError(f"{chemin}:{numero} : type « {type_} » inconnu")
            if controle is not None and not controle.match(cible):
                raise ValueError(f"{chemin}:{numero} : cible « {cible} » invalide pour le type {type_}")
            if type_ == "discover" and cible not in MODES_DISCOVER:
                raise ValueError(f"{chemin}:{numero} : mode Discover « {cible} » inconnu")
            if type_ == "info" and cible:
                raise ValueError(f"{chemin}:{numero} : une ligne « info » n'a pas de cible")
            if not categorie or not nom or not explication:
                raise ValueError(f"{chemin}:{numero} : catégorie, réglage et explication sont obligatoires")
            reglages.append(Reglage(categorie, nom, tuple(a for a in alias.split(";") if a), explication, type_, cible))
    return reglages


def categories(reglages):
    """Catégories dans l'ordre de première apparition."""
    vues = []
    for reglage in reglages:
        if reglage.categorie not in vues:
            vues.append(reglage.categorie)
    return vues


def de_la_categorie(reglages, categorie):
    return [r for r in reglages if r.categorie == categorie]


def chercher(reglages, requete):
    """Réglages qui répondent à `requete` (tous les mots doivent y figurer), les plus pertinents d'abord.

    Sans accents ni majuscules : « Wi-Fi », « wifi » et « WIFI » trouvent la même chose. Requête vide : rien."""
    mots = catalogue.normaliser(requete).split()
    if not mots:
        return []
    resultats = []
    for numero, reglage in enumerate(reglages):
        nom = catalogue.normaliser(reglage.nom)
        alias = [catalogue.normaliser(a) for a in reglage.alias]
        texte = " ".join([nom, *alias, catalogue.normaliser(reglage.categorie), catalogue.normaliser(reglage.explication)])
        if not all(mot in texte for mot in mots):
            continue
        score = 0
        phrase = " ".join(mots)
        if phrase == nom or phrase in alias:  # la requête entière est le nom du réglage ou l'un de ses synonymes
            score += 10
        elif nom.startswith(phrase) or any(a.startswith(phrase) for a in alias):
            score += 4
        for mot in mots:
            if nom.startswith(mot) or any(a.startswith(mot) for a in alias):
                score += 3
            elif mot in nom.split() or any(mot in a.split() for a in alias):
                score += 2
            else:
                score += 1
        resultats.append((-score, numero, reglage))
    return [reglage for _, _, reglage in sorted(resultats, key=lambda r: r[:2])]


def modules_disponibles(sortie):
    """Identifiants des modules listés par `kcmshell6 --list` (« kcm_kscreen - Écrans et moniteurs »).

    None si la sortie ne contient aucun module : on ne masque alors rien plutôt que de tout cacher."""
    modules = set()
    for ligne in sortie.splitlines():
        mots = ligne.strip().split()
        if mots and KCM.match(mots[0]):
            modules.add(mots[0])
    return modules or None


def visibles(reglages, disponibles):
    """Les réglages dont le module KDE est présent (tous, si la liste des modules est inconnue)."""
    if disponibles is None:
        return list(reglages)
    return [r for r in reglages if r.type != "kcm" or r.cible in disponibles]
