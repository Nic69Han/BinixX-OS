"""Taille du texte : un seul réglage, de 100 % à 200 %, qui agrandit le texte du bureau et des applications.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_taille_texte.py) ; l'outil en ligne de commande est
/usr/libexec/binixx/binixx-taille-texte.

KDE range ses polices dans `kdeglobals` (« Noto Sans,10,-1,5,400,… » : famille, taille en points, puis le style). On
multiplie la taille de chacune par le facteur, avec kwriteconfig6 --notify : les applications Qt et le bureau changent
de police tout de suite, et le module GTK de KDE recopie la police dans les applications GTK. On ne touche ni aux
familles, ni aux tailles des icônes, ni à la mise à l'échelle de l'écran.

Rien n'est perdu : la première fois, les polices d'origine (ou leur absence) sont gardées dans
~/.config/binixx/taille-du-texte.json ; « rétablir » les remet, sauf celles que l'utilisateur a changées depuis.
"""

import json
import os
import re

from . import launch

DOSSIER_REGLAGES = "~/.config/binixx"
MARQUEUR = os.path.join(DOSSIER_REGLAGES, "taille-du-texte.json")
FICHIER = "kdeglobals"
MINIMUM, MAXIMUM, PAS = 100, 200, 10
# (groupe, clé) : les polices de KDE dont on agrandit la taille
CLES = (("General", "font"), ("General", "fixed"), ("General", "smallestReadableFont"), ("General", "toolBarFont"),
        ("General", "menuFont"), ("WM", "activeFont"))
# Ce que KDE utilise quand rien n'est écrit : la police de l'interface, la police à chasse fixe, la plus petite lisible
STYLE = "-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
DEFAUTS = {
    ("General", "font"): f"Noto Sans,10,{STYLE}", ("General", "fixed"): f"Monospace,10,{STYLE}",
    ("General", "smallestReadableFont"): f"Noto Sans,8,{STYLE}", ("General", "toolBarFont"): f"Noto Sans,10,{STYLE}",
    ("General", "menuFont"): f"Noto Sans,10,{STYLE}", ("WM", "activeFont"): f"Noto Sans,10,{STYLE}",
}


def facteurs():
    """Les pourcentages que propose le curseur : 100, 110… 200."""
    return list(range(MINIMUM, MAXIMUM + 1, PAS))


def taille_de(police):
    """La taille, en points, d'une police écrite par KDE ; None si on ne la comprend pas."""
    champs = police.split(",")
    try:
        return float(champs[1]) if len(champs) >= 3 else None
    except ValueError:
        return None


def avec_taille(police, taille):
    """La même police, à `taille` points (arrondie au demi-point)."""
    champs = police.split(",")
    demi = round(taille * 2) / 2
    champs[1] = str(int(demi)) if demi == int(demi) else str(demi)
    return ",".join(champs)


def borner(pourcentage):
    """Un pourcentage entier entre 100 et 200 ; ValueError s'il n'est pas un nombre."""
    return max(MINIMUM, min(MAXIMUM, int(round(float(pourcentage)))))


def calculer(pourcentage, originales):
    """{(groupe, clé) : police à écrire, ou None pour effacer la clé} à `pourcentage` %, d'après les polices d'origine
    (None quand l'utilisateur n'en avait pas : on part de celles de KDE)."""
    pourcentage = borner(pourcentage)
    resultat = {}
    for cle in CLES:
        police = originales.get(cle) or DEFAUTS[cle]
        taille = taille_de(police)
        if pourcentage == 100 or taille is None:
            resultat[cle] = originales.get(cle)      # 100 % : exactement comme avant (clé effacée si elle n'existait pas)
        else:
            resultat[cle] = avec_taille(police, taille * pourcentage / 100)
    return resultat


def lire_polices(run=None):
    """{(groupe, clé) : police écrite par l'utilisateur ou None} d'après kreadconfig6."""
    run = run or launch.run
    polices = {}
    for groupe, cle in CLES:
        code, sortie = run(["kreadconfig6", "--file", FICHIER, "--group", groupe, "--key", cle], timeout=15)
        valeur = sortie.strip() if code == 0 else ""
        polices[(groupe, cle)] = valeur or None
    return polices


def ecrire_police(groupe, cle, valeur, run=None):
    """Écrit (ou efface, si `valeur` est None) une police et prévient les applications ; True si ça a marché."""
    run = run or launch.run
    if valeur is None:
        base = ["kwriteconfig6", "--file", FICHIER, "--group", groupe, "--key", cle, "--delete"]
        code, _ = run(base + ["--notify"], timeout=15)
        if code != 0:
            code, _ = run(base, timeout=15)
        return code == 0
    base = ["kwriteconfig6", "--file", FICHIER, "--group", groupe, "--key", cle]
    code, _ = run(base + ["--notify", valeur], timeout=15)
    if code != 0:  # une version de kwriteconfig6 sans --notify : on écrit quand même
        code, _ = run(base + [valeur], timeout=15)
    return code == 0


def lire_marqueur(chemin=None):
    """{"pourcentage": n, "originales": {…}, "ecrites": {…}} ou None s'il n'y a rien (ou si le fichier est illisible)."""
    chemin = os.path.expanduser(chemin or MARQUEUR)
    try:
        with open(chemin, encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, ValueError):
        return None
    if not isinstance(donnees, dict) or not isinstance(donnees.get("originales"), dict):
        return None
    try:
        return {"pourcentage": borner(donnees.get("pourcentage", 100)),
                "originales": {tuple(cle.split("/", 1)): valeur for cle, valeur in donnees["originales"].items()
                               if "/" in cle},
                "ecrites": {tuple(cle.split("/", 1)): valeur for cle, valeur in (donnees.get("ecrites") or {}).items()
                            if "/" in cle}}
    except (ValueError, AttributeError):
        return None


def ecrire_marqueur(pourcentage, originales, ecrites, chemin=None):
    chemin = os.path.expanduser(chemin or MARQUEUR)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    plat = lambda d: {f"{g}/{c}": v for (g, c), v in d.items()}  # noqa: E731
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump({"pourcentage": pourcentage, "originales": plat(originales), "ecrites": plat(ecrites)}, fichier,
                  ensure_ascii=False, indent=2)


def pourcentage_actuel(chemin=None):
    """Le pourcentage appliqué par ce réglage (100 si on n'y a jamais touché)."""
    marqueur = lire_marqueur(chemin)
    return marqueur["pourcentage"] if marqueur else 100


def appliquer(pourcentage, run=None, chemin=None):
    """Applique `pourcentage` % ; (réussi, message en français). Les polices d'origine sont gardées à la première fois."""
    run = run or launch.run
    try:
        pourcentage = borner(pourcentage)
    except (TypeError, ValueError):
        return False, "La taille doit être un pourcentage entre 100 et 200."
    marqueur = lire_marqueur(chemin)
    actuelles = lire_polices(run)
    if marqueur is None:
        originales = dict(actuelles)
    else:
        originales = dict(marqueur["originales"])
        for cle in CLES:  # une police changée à la main depuis devient la nouvelle référence
            if actuelles[cle] != marqueur["ecrites"].get(cle, originales.get(cle)):
                originales[cle] = actuelles[cle]
    voulues = calculer(pourcentage, originales)
    ecrites = {}
    for (groupe, cle), valeur in voulues.items():
        if not ecrire_police(groupe, cle, valeur, run):
            return False, "Le texte n'a pas pu être agrandi : le bureau ne répond pas. Essayez depuis une session ouverte."
        ecrites[(groupe, cle)] = valeur
    ecrire_marqueur(pourcentage, originales, ecrites, chemin)
    return True, f"Le texte est à {pourcentage} %." if pourcentage != 100 else "Le texte a retrouvé sa taille d'origine."


def retablir(run=None, chemin=None):
    """Remet les polices d'origine (sauf celles que l'utilisateur a changées depuis) ; (réussi, message)."""
    run = run or launch.run
    marqueur = lire_marqueur(chemin)
    if marqueur is None or marqueur["pourcentage"] == 100:
        return True, "Le texte a déjà sa taille d'origine."
    actuelles = lire_polices(run)
    for cle in CLES:
        if actuelles[cle] != marqueur["ecrites"].get(cle):
            continue          # changée à la main depuis : on la laisse
        if not ecrire_police(cle[0], cle[1], marqueur["originales"].get(cle), run):
            return False, "Le texte n'a pas pu être remis à sa taille : le bureau ne répond pas."
    try:
        os.remove(os.path.expanduser(chemin or MARQUEUR))
    except OSError:
        pass
    return True, "Le texte a retrouvé sa taille d'origine."


def apercu(pourcentage):
    """La taille, en points, que prend un texte de 10 points à `pourcentage` % (pour l'aperçu de la page)."""
    return round(10 * borner(pourcentage) / 100 * 2) / 2


def main(argv=None, run=None, sortie=print, chemin=None):
    """binixx-taille-texte etat | appliquer POURCENTAGE | retablir ; code de sortie 1 en cas d'échec."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-taille-texte", description="Taille du texte : de 100 % à 200 %.")
    parser.add_argument("action", choices=("etat", "appliquer", "retablir"))
    parser.add_argument("pourcentage", nargs="?", help="pour appliquer : un nombre de 100 à 200")
    args = parser.parse_args(argv)
    if args.action == "etat":
        sortie(f"{pourcentage_actuel(chemin)}")
        return 0
    if args.action == "retablir":
        reussi, message = retablir(run, chemin)
    else:
        if args.pourcentage is None or not re.fullmatch(r"[0-9]{2,3}([.,][0-9]+)?", args.pourcentage):
            sortie("La taille doit être un pourcentage entre 100 et 200.")
            return 1
        reussi, message = appliquer(args.pourcentage.replace(",", "."), run, chemin)
    sortie(message)
    return 0 if reussi else 1
