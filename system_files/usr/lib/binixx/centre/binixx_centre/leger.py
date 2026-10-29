"""Profil léger : le bureau sans effets, pour un PC de 4 Go ou plus ancien.

Coupe ce qui coûte de la mémoire et du processeur de dessin sans changer à quoi sert le bureau : le flou et la transparence de KWin
(les thèmes d'Aube et de Nuit retombent alors sur leurs fonds pleins, voir docs/theme-windows-11.md), le contraste, et les animations
(ouverture et fermeture des fenêtres, menus qui glissent, réduction des fenêtres). Les couleurs, les icônes et la disposition restent.

Rien n'est perdu : la première fois, les réglages d'origine (ou leur absence) sont gardés dans ~/.config/binixx/profil-leger.json ;
« désactiver » les remet, sauf ceux que l'utilisateur a changés depuis. Aucune dépendance à Qt : testé seul
(tests/image/centre/test_leger.py) ; outil en ligne de commande : /usr/libexec/binixx/binixx-leger.
"""

import json
import os

from . import launch, virtualisation

MARQUEUR = "~/.config/binixx/profil-leger.json"
# (fichier, groupe, clé, valeur du profil léger). Les effets de KWin sont dans [Plugins] sous « <identifiant>Enabled ».
REGLAGES = (
    ("kdeglobals", "KDE", "AnimationDurationFactor", "0"),
    ("kwinrc", "Plugins", "blurEnabled", "false"),
    ("kwinrc", "Plugins", "contrastEnabled", "false"),
    ("kwinrc", "Plugins", "slidingpopupsEnabled", "false"),
    ("kwinrc", "Plugins", "kwin4_effect_fadeEnabled", "false"),
    ("kwinrc", "Plugins", "kwin4_effect_squashEnabled", "false"),
)
# Au plus 4,5 Go vus par le système : le « 4 Go » de la boîte donne 3,8 Go, le « 6 Go » plus de 5,5 Go
SEUIL_CONSEIL_GO = 4.5


def _cle(reglage):
    return "/".join(reglage[:3])


def lire_reglage(fichier, groupe, cle, run=None):
    """La valeur écrite par l'utilisateur ou le système (kreadconfig6), None s'il n'y en a pas."""
    run = run or launch.run
    code, sortie = run(["kreadconfig6", "--file", fichier, "--group", groupe, "--key", cle], timeout=15)
    valeur = sortie.strip() if code == 0 else ""
    return valeur or None


def ecrire_reglage(fichier, groupe, cle, valeur, run=None):
    """Écrit (ou efface, si `valeur` est None) un réglage et prévient les applications ; True si ça a marché."""
    run = run or launch.run
    base = ["kwriteconfig6", "--file", fichier, "--group", groupe, "--key", cle]
    fin = ["--delete"] if valeur is None else [valeur]
    code, _ = run(base + ["--notify"] + fin, timeout=15)
    if code != 0:  # une version de kwriteconfig6 sans --notify : on écrit quand même
        code, _ = run(base + fin, timeout=15)
    return code == 0


def recharger_kwin(run=None):
    """Demande à KWin de relire ses réglages (les effets s'arrêtent tout de suite) ; False sans session graphique."""
    run = run or launch.run
    code, _ = run(["busctl", "--user", "call", "org.kde.KWin", "/KWin", "org.kde.KWin", "reconfigure"], timeout=15)
    return code == 0


def lire_marqueur(chemin=None):
    """{"originales": {clé: valeur ou None}, "ecrites": {clé: valeur}} ; None s'il n'y a rien (ou si le fichier est illisible)."""
    try:
        with open(os.path.expanduser(chemin or MARQUEUR), encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, ValueError):
        return None
    if not isinstance(donnees, dict) or not isinstance(donnees.get("originales"), dict):
        return None
    return {"originales": donnees["originales"], "ecrites": donnees.get("ecrites") or {}}


def ecrire_marqueur(originales, ecrites, chemin=None):
    chemin = os.path.expanduser(chemin or MARQUEUR)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump({"originales": originales, "ecrites": ecrites}, fichier)


def actif(run=None, chemin=None):
    """True si le profil est en place : le marqueur existe et tous les réglages ont la valeur du profil."""
    run = run or launch.run
    if lire_marqueur(chemin) is None:
        return False
    return all(lire_reglage(f, g, c, run) == valeur for f, g, c, valeur in REGLAGES)


def conseille(meminfo=None):
    """True si ce PC a 4 Go de mémoire vive ou moins : le profil léger lui rendra service."""
    if meminfo is None:
        try:
            with open("/proc/meminfo", encoding="utf-8") as fichier:
                meminfo = fichier.read()
        except OSError:
            return False
    go = virtualisation.memoire_go(meminfo)
    return 0 < go <= SEUIL_CONSEIL_GO


def activer(run=None, chemin=None):
    """Pose le profil léger ; (réussi, message en français). Les réglages d'origine sont gardés à la première fois."""
    run = run or launch.run
    marqueur = lire_marqueur(chemin)
    actuelles = {_cle(r): lire_reglage(*r[:3], run) for r in REGLAGES}
    if marqueur is None:
        originales = dict(actuelles)
    else:
        originales = dict(marqueur["originales"])
        for r in REGLAGES:  # un réglage changé à la main depuis devient la nouvelle référence
            cle = _cle(r)
            if actuelles[cle] != marqueur["ecrites"].get(cle, originales.get(cle)):
                originales[cle] = actuelles[cle]
    for fichier, groupe, cle, valeur in REGLAGES:
        if not ecrire_reglage(fichier, groupe, cle, valeur, run):
            return False, "Le profil léger n'a pas pu être posé : le bureau ne répond pas. Essayez depuis une session ouverte."
    ecrire_marqueur(originales, {_cle(r): r[3] for r in REGLAGES}, chemin)
    if recharger_kwin(run):
        return True, "Profil léger en place : sans flou ni animations. Les fenêtres déjà ouvertes en profitent à leur prochaine ouverture."
    return True, "Profil léger posé : il sera en place à la prochaine ouverture de session."


def desactiver(run=None, chemin=None):
    """Remet les réglages d'origine (sauf ceux que l'utilisateur a changés depuis) ; (réussi, message)."""
    run = run or launch.run
    marqueur = lire_marqueur(chemin)
    if marqueur is None:
        return True, "Le profil léger n'était pas activé."
    for fichier, groupe, cle, valeur in REGLAGES:
        identifiant = _cle((fichier, groupe, cle))
        if lire_reglage(fichier, groupe, cle, run) != marqueur["ecrites"].get(identifiant, valeur):
            continue          # changé à la main depuis : on le laisse
        if not ecrire_reglage(fichier, groupe, cle, marqueur["originales"].get(identifiant), run):
            return False, "Le profil léger n'a pas pu être retiré : le bureau ne répond pas."
    try:
        os.remove(os.path.expanduser(chemin or MARQUEUR))
    except OSError:
        pass
    recharger_kwin(run)
    return True, "Le bureau a retrouvé ses effets."


def main(argv=None, run=None, sortie=print, chemin=None, meminfo=None):
    """binixx-leger etat | conseil | activer | desactiver ; code de sortie 1 en cas d'échec."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-leger", description="Profil léger : le bureau sans flou ni animations.")
    parser.add_argument("action", choices=("etat", "conseil", "activer", "desactiver"))
    args = parser.parse_args(argv)
    if args.action == "etat":
        sortie(f"leger={'oui' if actif(run, chemin) else 'non'}")
        sortie(f"conseille={'oui' if conseille(meminfo) else 'non'}")
        return 0
    if args.action == "conseil":
        sortie("oui" if conseille(meminfo) else "non")
        return 0
    reussi, message = (activer if args.action == "activer" else desactiver)(run, chemin)
    sortie(message)
    return 0 if reussi else 1
