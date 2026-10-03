"""Ambiances : l'allure du bureau en un clic (Aube, Nuit, Contraste élevé) et un interrupteur « Grand texte ».

Aucune dépendance à Qt : testé seul (tests/image/centre/test_ambiances.py) ; l'outil en ligne de commande est
/usr/libexec/binixx/binixx-ambiance.

Deux choses indépendantes, pour qu'on puisse avoir une ambiance sombre ET un grand texte :
  - l'allure : Aube (thème BinixX OS clair), Nuit (thème BinixX OS sombre) ou Contraste élevé (noir, blanc et jaune) ;
  - « Grand texte » : le texte à 130 % (voir taille_texte.py) et un pointeur de souris plus gros.

L'allure se pose avec les outils de Plasma (plasma-apply-lookandfeel, plasma-apply-colorscheme), qui changent tout de suite
les couleurs, les icônes, le style des fenêtres et les applications ouvertes ; le fond d'écran, lui, a deux versions (claire et
sombre) que Plasma choisit tout seul selon les couleurs. On relit toujours kdeglobals pour vérifier que ça a marché : on
n'annonce rien sur la foi du code de sortie d'un outil. L'ambiance en cours se reconnaît à son schéma de couleurs.
"""

import json
import os
from collections import namedtuple

from . import launch, taille_texte

DOSSIER_REGLAGES = "~/.config/binixx"
MARQUEUR = os.path.join(DOSSIER_REGLAGES, "grand-texte.json")
POINTEUR_GRAND = 36
POINTEUR_NORMAL = 24          # la taille de KDE quand rien n'est écrit
TEXTE_GRAND = 130
THEME_CURSEUR = "breeze_cursors"

# cle, titre, texte, thème global de Plasma, schéma de couleurs, aperçu (fond, texte, accent, barre de titre)
Ambiance = namedtuple("Ambiance", "cle titre texte theme couleurs apercu")
AMBIANCES = (
    Ambiance("aube", "Aube", "Le thème clair de BinixX OS : fond clair, bleu BinixX OS, icônes sombres. Le plus proche de "
                             "Windows en mode clair.",
             "org.binixx.desktop", "BinixXClair", ("#F4F6FB", "#1B2230", "#2F5BFF", "#FFFFFF")),
    Ambiance("nuit", "Nuit", "Le thème sombre de BinixX OS : fond sombre, bleu clair, icônes clairs. Repose les yeux le soir et "
                             "dans une pièce peu éclairée.",
             "org.binixx.dark.desktop", "BinixXSombre", ("#1E232E", "#EEF1F8", "#5A7DFF", "#2A3040")),
    Ambiance("contraste", "Contraste élevé", "Texte blanc sur fond noir, sélection en jaune : chaque élément se détache "
                                              "nettement, pour mieux lire quand la vue est fatiguée ou l'écran très "
                                              "lumineux.",
             "org.binixx.dark.desktop", "BinixXContraste", ("#000000", "#FFFFFF", "#FFDD00", "#FFDD00")),
)
CLES = tuple(a.cle for a in AMBIANCES)


def trouver(cle):
    """L'ambiance de ce nom, ou None."""
    return next((a for a in AMBIANCES if a.cle == cle), None)


def lire(fichier, groupe, cle, run=None):
    """La valeur d'une clé de KDE d'après kreadconfig6 (celle qui s'applique vraiment, réglages du système compris) ; "" si rien."""
    run = run or launch.run
    code, sortie = run(["kreadconfig6", "--file", fichier, "--group", groupe, "--key", cle], timeout=15)
    return sortie.strip() if code == 0 else ""


def couleurs_actuelles(run=None):
    """Le schéma de couleurs en place. Tant qu'on n'a rien choisi, il n'est pas dans kdeglobals : Plasma le range dans
    ~/.config/kdedefaults/kdeglobals, d'après le thème global (c'est lui qui dit « Aube » sur une installation neuve)."""
    schema = lire("kdeglobals", "General", "ColorScheme", run)
    if schema:
        return schema
    base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    return lire(os.path.expanduser(os.path.join(base, "kdedefaults", "kdeglobals")), "General", "ColorScheme", run)


def ambiance_actuelle(run=None):
    """L'ambiance en cours (reconnue à son schéma de couleurs), ou None si le schéma n'est pas l'un des nôtres."""
    couleurs = couleurs_actuelles(run)
    return next((a for a in AMBIANCES if a.couleurs == couleurs), None)


def _sans_ecran():
    """Les outils plasma-apply-* démarrent une application Qt : sans écran (ssh, test, tâche programmée) elle s'arrête avant
    d'avoir rien fait. On leur donne alors la plateforme « offscreen » : ils écrivent les réglages et préviennent les
    applications par D-Bus, sans rien afficher."""
    return None if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY") else {"QT_QPA_PLATFORM": "offscreen"}


def _essayer(commandes, run, verifie=None):
    """Lance les commandes l'une après l'autre ; s'arrête à la première qui réussit ET dont le résultat se vérifie
    (`verifie()` renvoie True) : un outil qui répond « réussi » sans rien changer ne suffit pas. True si c'est le cas."""
    env = _sans_ecran()
    for argv in commandes:
        if env and argv[0].startswith(("plasma-apply-", "lookandfeeltool")):
            code, _ = run(argv, timeout=60, env=env)
        else:
            code, _ = run(argv, timeout=60)
        if code == 0 and (verifie is None or verifie()):
            return True
    return False


def appliquer(cle, run=None):
    """Pose l'ambiance `cle` ; (réussi, message en français)."""
    run = run or launch.run
    ambiance = trouver(cle)
    if ambiance is None:
        return False, "Cette ambiance n'existe pas : " + ", ".join(CLES) + "."
    if ambiance.cle == "contraste":
        # Une couleur d'accentuation choisie à la main écraserait le jaune : on l'enlève (elle n'existe pas la plupart du temps)
        run(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "AccentColor", "--delete"], timeout=15)
    _essayer([["plasma-apply-lookandfeel", "--apply", ambiance.theme], ["lookandfeeltool", "--apply", ambiance.theme]], run)
    # Le thème global pose déjà ses couleurs ; pour le contraste élevé, on les remplace par les nôtres. Dans tous les cas on
    # force le schéma voulu : c'est lui qui dit quelle ambiance est en cours. Pas de secours par écriture directe du nom :
    # sans les couleurs que l'outil copie dans kdeglobals, le nom seul ne changerait rien à l'écran.
    _essayer([["plasma-apply-colorscheme", ambiance.couleurs]], run, lambda: couleurs_actuelles(run) == ambiance.couleurs)
    if couleurs_actuelles(run) != ambiance.couleurs:
        return False, ("L'ambiance « %s » n'a pas pu être appliquée : le bureau ne répond pas. Essayez depuis une session "
                       "ouverte." % ambiance.titre)
    return True, f"L'ambiance « {ambiance.titre} » est en place."


def pointeur_actuel(run=None):
    """La taille du pointeur ('' si rien n'est écrit : KDE prend alors 24)."""
    return lire("kcminputrc", "Mouse", "cursorSize", run)


def poser_pointeur(taille, run=None):
    """Règle la taille du pointeur, tout de suite si Plasma sait le faire, sinon à la prochaine ouverture de session.
    On relit la valeur : l'outil de Plasma peut répondre « réussi » sans l'avoir écrite, l'écriture directe prend alors le relais."""
    run = run or launch.run
    theme = lire("kcminputrc", "Mouse", "cursorTheme", run) or THEME_CURSEUR
    juste = lambda: (pointeur_actuel(run) or str(POINTEUR_NORMAL)) == str(taille)  # noqa: E731
    return _essayer([["plasma-apply-cursortheme", "--size", str(taille), theme],
                     ["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", str(taille)]],
                    run, juste)


def lire_marqueur(chemin=None):
    """{"curseur": taille d'origine du pointeur ou None} ; None s'il n'y a rien (ou si le fichier est illisible)."""
    try:
        with open(os.path.expanduser(chemin or MARQUEUR), encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, ValueError):
        return None
    if not isinstance(donnees, dict) or "curseur" not in donnees:
        return None
    curseur = donnees["curseur"]
    return {"curseur": curseur if isinstance(curseur, str) and curseur.isdigit() else None}


def ecrire_marqueur(curseur, chemin=None):
    chemin = os.path.expanduser(chemin or MARQUEUR)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump({"curseur": curseur or None}, fichier)


def grand_texte_actif(chemin_marqueur=None, chemin_texte=None):
    """True si « Grand texte » est en place : le marqueur existe et le texte est à 130 %."""
    return lire_marqueur(chemin_marqueur) is not None and taille_texte.pourcentage_actuel(chemin_texte) == TEXTE_GRAND


def activer_grand_texte(run=None, chemin_marqueur=None, chemin_texte=None):
    """Texte à 130 % et pointeur plus gros ; (réussi, message). Les tailles d'avant sont gardées pour « désactiver »."""
    run = run or launch.run
    if lire_marqueur(chemin_marqueur) is None:  # première fois : on garde la taille d'origine du pointeur
        ecrire_marqueur(pointeur_actuel(run), chemin_marqueur)
    reussi, message = taille_texte.appliquer(TEXTE_GRAND, run, chemin_texte)
    if not reussi:
        return False, message
    if not poser_pointeur(POINTEUR_GRAND, run):
        return False, "Le texte est agrandi, mais le pointeur n'a pas pu l'être : le bureau ne répond pas."
    return True, "« Grand texte » est en place : texte à 130 % et pointeur plus gros."


def desactiver_grand_texte(run=None, chemin_marqueur=None, chemin_texte=None):
    """Remet le texte et le pointeur comme avant ; (réussi, message). Un texte réglé à la main sur une autre taille est laissé."""
    run = run or launch.run
    marqueur = lire_marqueur(chemin_marqueur)
    if marqueur is None:
        return True, "« Grand texte » n'était pas activé."
    if taille_texte.pourcentage_actuel(chemin_texte) == TEXTE_GRAND:
        reussi, message = taille_texte.retablir(run, chemin_texte)
        if not reussi:
            return False, message
    if not poser_pointeur(int(marqueur["curseur"] or POINTEUR_NORMAL), run):
        return False, "Le texte est remis, mais le pointeur n'a pas pu l'être : le bureau ne répond pas."
    try:
        os.remove(os.path.expanduser(chemin_marqueur or MARQUEUR))
    except OSError:
        pass
    return True, "Le texte et le pointeur ont retrouvé leur taille d'origine."


def main(argv=None, run=None, sortie=print, chemin_marqueur=None, chemin_texte=None):
    """binixx-ambiance liste | etat | appliquer AMBIANCE | grand-texte oui|non ; code de sortie 1 en cas d'échec."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-ambiance", description="Ambiances du bureau : Aube, Nuit, Contraste élevé.")
    sous = parser.add_subparsers(dest="action", required=True)
    sous.add_parser("liste", help="les ambiances proposées")
    sous.add_parser("etat", help="l'ambiance en cours et l'état de « Grand texte »")
    poser = sous.add_parser("appliquer", help="poser une ambiance")
    poser.add_argument("ambiance", choices=CLES)
    grand = sous.add_parser("grand-texte", help="activer ou désactiver « Grand texte »")
    grand.add_argument("choix", choices=("oui", "non"))
    args = parser.parse_args(argv)
    if args.action == "liste":
        for ambiance in AMBIANCES:
            sortie(f"{ambiance.cle}\t{ambiance.titre}")
        return 0
    if args.action == "etat":
        courante = ambiance_actuelle(run)
        sortie(f"ambiance={courante.cle if courante else 'aucune'}")
        sortie(f"grand-texte={'oui' if grand_texte_actif(chemin_marqueur, chemin_texte) else 'non'}")
        return 0
    if args.action == "appliquer":
        reussi, message = appliquer(args.ambiance, run)
    elif args.choix == "oui":
        reussi, message = activer_grand_texte(run, chemin_marqueur, chemin_texte)
    else:
        reussi, message = desactiver_grand_texte(run, chemin_marqueur, chemin_texte)
    sortie(message)
    return 0 if reussi else 1
