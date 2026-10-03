"""Position de la barre des tâches : en bas (comme Windows) ou en haut de l'écran. Aucune dépendance à Qt.

Plasma accepte des scripts de disposition par D-Bus (org.kde.PlasmaShell.evaluateScript) : on s'en sert pour déplacer le
ou les panneaux de la session ouverte, sans toucher à un fichier de configuration. Aucun shell n'est utilisé et la
position vient d'une liste fermée, jamais d'un texte saisi.

La position actuelle se lit dans la disposition courante de Plasma (dumpCurrentLayoutJS) et, à défaut, dans le fichier de
configuration du bureau de l'utilisateur.

Testé seul (tests/image/centre/test_barre.py) ; l'outil en ligne de commande est /usr/libexec/binixx/binixx-barre.
"""

import argparse
import configparser
import os
import re

from . import launch

POSITIONS = ("haut", "bas")
NOMS = {"haut": "en haut", "bas": "en bas"}
EMPLACEMENTS = {"haut": "top", "bas": "bottom"}
APPLETSRC = "~/.config/plasma-org.kde.plasma.desktop-appletsrc"
SERVICE = ["busctl", "--user", "call", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell"]
# « panel.location = "top" » dans le script de la disposition courante (busctl échappe les guillemets)
LIGNE_EMPLACEMENT = re.compile(r"""location\s*=\s*\\?["'](top|bottom|left|right)\\?["']""")
# Plasma::Types::Location dans le fichier de configuration : 3 = haut, 4 = bas
CODES = {"3": "haut", "4": "bas"}


def script_de_deplacement(position):
    """Le script Plasma qui met tous les panneaux à `position` ; ValueError si elle n'est pas dans POSITIONS."""
    if position not in POSITIONS:
        raise ValueError(f"position inconnue : {position} (attendu : {', '.join(POSITIONS)})")
    return ('var p = panels(); for (var i = 0; i < p.length; i++) { p[i].location = "'
            + EMPLACEMENTS[position] + '"; }')


def position_dans_disposition(texte):
    """« haut » ou « bas » d'après le premier panneau du script de disposition ; None si on ne le lit pas."""
    trouve = LIGNE_EMPLACEMENT.search(texte or "")
    if not trouve:
        return None
    return {"top": "haut", "bottom": "bas"}.get(trouve.group(1))


def position_dans_configuration(chemin=None):
    """« haut » ou « bas » d'après le fichier de configuration du bureau ; None s'il manque ou ne dit rien."""
    chemin = os.path.expanduser(chemin or APPLETSRC)
    lecteur = configparser.ConfigParser(interpolation=None, strict=False)
    lecteur.optionxform = str
    try:
        lecteur.read(chemin, encoding="utf-8")
    except (OSError, configparser.Error, UnicodeDecodeError):
        return None
    for section in lecteur.sections():
        if section.startswith("Containments][") and section.count("][") == 1 \
                and lecteur.get(section, "plugin", fallback="") == "org.kde.panel":
            position = CODES.get(lecteur.get(section, "location", fallback=""))
            if position:
                return position
    return None


def position_actuelle(run=launch.run, chemin=None):
    """Où est la barre : « haut », « bas », ou None si on ne le sait pas (bureau fermé, barre sur un côté)."""
    code, sortie = run(SERVICE + ["dumpCurrentLayoutJS"], timeout=5)
    if code == 0:
        position = position_dans_disposition(sortie)
        if position:
            return position
    return position_dans_configuration(chemin)


def deplacer(position, run=launch.run, chemin=None):
    """Déplace la barre : (réussi, message en français). Il faut une session de bureau ouverte."""
    script = script_de_deplacement(position)
    code, sortie = run(SERVICE + ["evaluateScript", "s", script], timeout=15)
    if code != 0:
        return False, "La barre n'a pas pu être déplacée : le bureau ne répond pas. Essayez depuis une session ouverte."
    if "rror" in (sortie or ""):  # Plasma renvoie le texte de l'erreur du script
        return False, "La barre n'a pas pu être déplacée : " + sortie.strip()[:200]
    voulue = position_actuelle(run, chemin)
    if voulue is not None and voulue != position:
        return False, f"La barre est restée {NOMS[voulue]}."
    return True, f"La barre est maintenant {NOMS[position]}."


def main(argv=None):
    """binixx-barre haut | bas | etat : affiche la position ou la change ; code de sortie 1 en cas d'échec."""
    parser = argparse.ArgumentParser(prog="binixx-barre", description="Place la barre des tâches en haut ou en bas.")
    parser.add_argument("action", choices=POSITIONS + ("etat",),
                        help="haut ou bas : déplace la barre ; etat : affiche sa position")
    args = parser.parse_args(argv)
    if args.action == "etat":
        position = position_actuelle()
        print(position or "inconnue")
        return 0 if position else 1
    reussi, message = deplacer(args.action)
    print(message)
    return 0 if reussi else 1
