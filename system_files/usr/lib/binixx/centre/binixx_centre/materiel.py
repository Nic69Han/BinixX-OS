"""Matériel utile aux jeux : cartes graphiques. Aucune dépendance à Qt : testé seul (tests/image/centre/test_jeux.py)."""

import shlex
import subprocess

CLASSES_GRAPHIQUES = ("VGA compatible controller", "3D controller", "Display controller")


def analyser_switcheroo(sortie):
    """Cartes décrites par « switcherooctl list » : liste de {nom, defaut, dedie}."""
    cartes = []
    for ligne in sortie.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("Device:"):
            cartes.append({"nom": "", "defaut": False, "dedie": False})
        elif cartes and ":" in ligne:
            cle, valeur = (partie.strip() for partie in ligne.split(":", 1))
            if cle == "Name":
                cartes[-1]["nom"] = valeur
            elif cle == "Default":
                cartes[-1]["defaut"] = valeur.lower() == "yes"
            elif cle == "Discrete":
                cartes[-1]["dedie"] = valeur.lower() == "yes"
    return [carte for carte in cartes if carte["nom"]]


def analyser_lspci(sortie):
    """Cartes décrites par « lspci -mm » : liste de {nom, defaut, dedie} (défaut et dédié inconnus : False)."""
    cartes = []
    for ligne in sortie.splitlines():
        try:
            champs = shlex.split(ligne)
        except ValueError:
            continue
        if len(champs) >= 4 and champs[1] in CLASSES_GRAPHIQUES:
            cartes.append({"nom": f"{champs[2]} {champs[3]}", "defaut": False, "dedie": False})
    return cartes


def _lancer(argv):
    try:
        fini = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return fini.stdout if fini.returncode == 0 else ""


def cartes_graphiques():
    """(cartes, via_switcheroo) : switcheroo-control sait aussi lancer un programme avec une carte donnée."""
    cartes = analyser_switcheroo(_lancer(["switcherooctl", "list"]))
    if cartes:
        return cartes, True
    return analyser_lspci(_lancer(["lspci", "-mm"])), False
