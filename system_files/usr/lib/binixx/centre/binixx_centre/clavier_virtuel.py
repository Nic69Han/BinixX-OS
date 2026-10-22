"""Clavier virtuel (plasma-keyboard) seulement sur les PC à écran tactile.

KWin lance le clavier virtuel de Plasma avec chaque session (réglage [Wayland] InputMethod de kwinrc) ; il prend environ
140 Mo de mémoire vive même quand il ne s'affiche jamais, ce qui est le cas sans écran tactile (docs/memoire.md). À chaque
ouverture de session (/etc/xdg/autostart/binixx-clavier-virtuel.desktop) :
  - pas d'écran tactile, et l'utilisateur n'a pas choisi lui-même : InputMethod vide dans ~/.config/kwinrc, KWin arrête le
    clavier (--notify) ; un marqueur retient que c'est BinixX OS qui l'a coupé ;
  - écran tactile, et c'est BinixX OS qui l'avait coupé (écran branché depuis, disque changé de PC) : le réglage est effacé,
    le clavier revient ;
  - l'utilisateur a choisi lui-même (Configuration du système → Clavier virtuel) : on n'y touche jamais.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_clavier_virtuel.py). Outil : /usr/libexec/binixx/binixx-clavier-virtuel.
"""

import glob
import os

from . import launch

FICHIER, GROUPE, CLE = "kwinrc", "Wayland", "InputMethod"
MARQUEUR = "~/.config/binixx/clavier-virtuel-coupe"


def _config(chemin):
    return os.path.expanduser(chemin)


def ecran_tactile(run=None, peripheriques=None):
    """Vrai si udev a repéré un écran tactile (ID_INPUT_TOUCHSCREEN=1) parmi les périphériques d'entrée."""
    run = run or launch.run
    for peripherique in (glob.glob("/sys/class/input/event*") if peripheriques is None else peripheriques):
        code, sortie = run(["udevadm", "info", "--query=property", "--path", peripherique], timeout=10)
        if code == 0 and "ID_INPUT_TOUCHSCREEN=1" in sortie.splitlines():
            return True
    return False


def choix_utilisateur(kwinrc=None):
    """La valeur d'InputMethod écrite dans le kwinrc de l'utilisateur (« » si vide), None si la clé n'y est pas."""
    chemin = kwinrc or os.path.join(os.environ.get("XDG_CONFIG_HOME") or _config("~/.config"), FICHIER)
    try:
        with open(chemin, encoding="utf-8") as fichier:
            lignes = fichier.read().splitlines()
    except OSError:
        return None
    groupe = None
    for ligne in lignes:
        ligne = ligne.strip()
        if ligne.startswith("[") and ligne.endswith("]"):
            groupe = ligne[1:-1]
        elif groupe == GROUPE and "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            if cle.split("[")[0].strip() == CLE:
                return valeur.strip()
    return None


def _ecrire(valeur, run):
    """Écrit InputMethod (None : l'efface) et prévient KWin, qui arrête ou relance le clavier tout de suite."""
    base = ["kwriteconfig6", "--file", FICHIER, "--group", GROUPE, "--key", CLE]
    fin = ["--delete"] if valeur is None else [valeur]
    code, _ = run(base + ["--notify"] + fin, timeout=15)
    if code != 0:  # kwriteconfig6 sans --notify : on écrit quand même, KWin le lira à la prochaine session
        code, _ = run(base + fin, timeout=15)
    return code == 0


def ajuster(run=None, tactile=None, kwinrc=None, marqueur=None):
    """Coupe ou rétablit le clavier virtuel selon l'écran ; renvoie ce qui a été fait (texte court)."""
    run = run or launch.run
    marqueur = _config(marqueur or MARQUEUR)
    tactile = ecran_tactile(run) if tactile is None else tactile
    choix = choix_utilisateur(kwinrc)
    coupe_par_binixx = os.path.exists(marqueur)
    if tactile:
        if coupe_par_binixx and choix == "":
            _ecrire(None, run)
            os.remove(marqueur)
            return "écran tactile : clavier virtuel rétabli"
        if coupe_par_binixx:  # l'utilisateur a choisi un clavier depuis : on oublie simplement le marqueur
            os.remove(marqueur)
        return "écran tactile : rien à changer"
    if coupe_par_binixx or choix is not None:
        return "clavier virtuel déjà coupé, ou choisi par l'utilisateur : rien à changer"
    if not _ecrire("", run):
        return "impossible d'écrire le réglage du clavier virtuel"
    os.makedirs(os.path.dirname(marqueur), exist_ok=True)
    open(marqueur, "w", encoding="utf-8").close()
    return "pas d'écran tactile : clavier virtuel coupé"


def main(argv=None, run=None, sortie=print):
    sortie(ajuster(run=run))
    return 0
