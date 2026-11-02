"""Couleur d'un dossier : clic droit sur un dossier dans Dolphin (ou sur le bureau) → « Couleur du dossier » (docs/identite-visuelle.md).

Les dossiers de BinixX OS ont une couleur pastel selon leur contenu (build_files/icones-binixx.py) ; on peut en choisir une autre pour
n'importe quel dossier. Le choix s'écrit comme le fait KDE, dans le fichier caché « .directory » du dossier (groupe [Desktop Entry],
clé Icon=folder-<couleur>), avec kwriteconfig6 : Dolphin et le bureau le relisent tout seuls. « Par défaut » efface la clé.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_couleur_dossier.py) ; l'outil est /usr/libexec/binixx/binixx-couleur-dossier,
appelé par le menu /usr/share/kio/servicemenus/binixx-couleur-dossier.desktop.
"""

import os
import sys

from . import launch

# couleur proposée → icône de dossier du thème BinixX (les noms de Breeze, recolorés en pastel)
COULEURS = {
    "jaune": "folder-yellow", "bleu": "folder-blue", "vert": "folder-green", "rose": "folder-magenta", "violet": "folder-violet",
    "orange": "folder-orange", "ardoise": "folder-grey", "turquoise": "folder-cyan", "rouge": "folder-red", "brun": "folder-brown",
}
DEFAUT = "defaut"


def colorer(dossier, couleur, run=None):
    """Pose (ou retire, pour « defaut ») la couleur d'un dossier ; (réussi, message)."""
    run = run or launch.run
    if couleur != DEFAUT and couleur not in COULEURS:
        return False, f"Couleur inconnue : « {couleur} » (au choix : {', '.join(COULEURS)}, {DEFAUT})."
    if not os.path.isdir(dossier):
        return False, f"« {dossier} » n'est pas un dossier."
    fichier = os.path.join(dossier, ".directory")
    argv = ["kwriteconfig6", "--file", fichier, "--group", "Desktop Entry", "--key", "Icon"]
    if couleur == DEFAUT:
        if not os.path.exists(fichier):
            return True, "Le dossier a déjà sa couleur d'origine."
        argv += ["--delete"]
    else:
        argv += [COULEURS[couleur]]
    code, sortie = run(argv, timeout=15)
    if code != 0:
        return False, f"La couleur n'a pas pu être enregistrée dans {fichier} : {sortie.strip()[:200]}"
    return True, "Couleur d'origine rétablie." if couleur == DEFAUT else f"Dossier en {couleur}."


def main(argv=None, run=None, sortie=print):
    """binixx-couleur-dossier COULEUR DOSSIER… ; code de sortie 1 si l'un des dossiers n'a pas pu être coloré."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        sortie(f"Usage : binixx-couleur-dossier {{{'|'.join(list(COULEURS) + [DEFAUT])}}} DOSSIER…")
        return 2
    couleur, dossiers = argv[0], argv[1:]
    resultat = 0
    for dossier in dossiers:
        reussi, message = colorer(dossier, couleur, run)
        sortie(f"{dossier} : {message}")
        resultat = resultat or (0 if reussi else 1)
    return resultat
