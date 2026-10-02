"""Installer des applications (page « Applications ») : liste tirée du catalogue, licences, commande Flatpak.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_applications.py). Aucun texte venant de
l'utilisateur ne finit dans une commande : les identifiants viennent du catalogue de l'image et sont revérifiés.
"""

import os
import re
from dataclasses import dataclass

from . import catalogue

LICENCES = "/usr/share/nicos/catalogue-windows/licences.tsv"
# Ces catégories ont leur propre page, avec leurs explications : Jeux, Windows complet
CATEGORIES_A_PART = ("Jeux", "Compatibilité Windows")
ID_FLATPAK = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+){2,}$")
SIMPLE = re.compile(r"^[A-Za-z0-9.+\-]+$")


@dataclass(frozen=True)
class Application:
    identifiant: str
    nom: str
    remplace: tuple
    categorie: str
    remarque: str


def proposees(entrees, fournies, a_part=CATEGORIES_A_PART):
    """Applications Flatpak à proposer : une par identifiant, dans l'ordre du catalogue, avec les logiciels Windows
    qu'elles remplacent. Ni celles installées au premier démarrage, ni celles des catégories qui ont leur page."""
    exclues = {e.cible for e in entrees if e.categorie in a_part} | set(fournies)
    trouvees = {}
    for entree in entrees:
        if entree.type != "flatpak" or entree.cible in exclues:
            continue
        if entree.cible in trouvees:
            ancienne = trouvees[entree.cible]
            trouvees[entree.cible] = Application(ancienne.identifiant, ancienne.nom, ancienne.remplace + (entree.windows,),
                                                 ancienne.categorie, ancienne.remarque)
        else:
            trouvees[entree.cible] = Application(entree.cible, entree.remplacant, (entree.windows,), entree.categorie,
                                                 entree.remarque)
    return list(trouvees.values())


def remplace_vraiment(application):
    """Logiciels Windows que l'application remplace, sans ceux qui portent son propre nom (VLC remplace « VLC » : rien à dire)."""
    nom = catalogue.normaliser(application.nom)
    return tuple(w for w in application.remplace if catalogue.normaliser(w) != nom)


def par_categorie(applications):
    """[(catégorie, [applications])] dans l'ordre alphabétique des catégories."""
    groupes = {}
    for application in applications:
        groupes.setdefault(application.categorie, []).append(application)
    return sorted(groupes.items(), key=lambda groupe: groupe[0].lower())


def lire_licences(chemin=None):
    """{identifiant: licence} depuis licences.tsv (identifiant, tabulation, licence SPDX ou « LicenseRef-… »)."""
    chemin = chemin or os.environ.get("NICOS_LICENCES", LICENCES)
    licences = {}
    try:
        with open(chemin, encoding="utf-8") as fichier:
            for ligne in fichier:
                ligne = ligne.rstrip("\n")
                if not ligne or ligne.startswith("#"):
                    continue
                identifiant, _, licence = ligne.partition("\t")
                if identifiant and licence:
                    licences[identifiant] = licence
    except OSError:
        pass
    return licences


def est_proprietaire(licence):
    return licence.startswith("LicenseRef-proprietary")


def libelle_licence(licence):
    """« Libre · GPL-3.0 », « Libre » (licences multiples), « Propriétaire » ou « Licence non vérifiée »."""
    if not licence:
        return "Licence non vérifiée"
    if est_proprietaire(licence):
        return "Propriétaire"
    return f"Libre · {licence}" if SIMPLE.match(licence) else "Libre"


def valider(identifiant):
    if not ID_FLATPAK.match(identifiant):
        raise ValueError(f"identifiant Flatpak invalide : {identifiant!r}")
    return identifiant


def commande(identifiants, flatpak="flatpak"):
    """La commande d'installation pour tout le système (un seul mot de passe d'administrateur pour l'ensemble)."""
    identifiants = [valider(i) for i in identifiants]
    if not identifiants:
        raise ValueError("aucune application choisie")
    return [flatpak, "install", "--system", "--noninteractive", "--assumeyes", "flathub", *identifiants]


def derniere_ligne(texte, longueur=110):
    """Dernier message lisible de flatpak (qui réécrit sa ligne de progression avec des retours chariot)."""
    for morceau in reversed(re.split(r"[\r\n]+", texte)):
        sans_barres = re.sub("[▀-▟─-╿]+", "", morceau)  # barres de progression
        propre = re.sub(r"\s+", " ", sans_barres).strip()
        if propre:
            return propre if len(propre) <= longueur else propre[:longueur - 1] + "…"
    return ""


def explication_echec(sortie):
    """Phrase simple pour la cause la plus fréquente d'un échec, d'après la sortie de flatpak."""
    texte = sortie.lower()
    if any(m in texte for m in ("not allowed", "authentication", "permission denied", "polkit", "dismissed")):
        return "Il faut être administrateur (ou saisir le mot de passe d'un administrateur) pour installer des applications."
    if any(m in texte for m in ("could not resolve", "unable to connect", "network", "timed out", "no route")):
        return "La connexion à Flathub a échoué : vérifiez le réseau, puis recommencez."
    if "no remote" in texte or "remote \"flathub\" not found" in texte or "not found" in texte:
        return "Une application n'a pas été trouvée sur Flathub : recommencez plus tard ou choisissez-en une autre."
    if "no space" in texte:
        return "Il n'y a pas assez de place sur le disque."
    return ""
