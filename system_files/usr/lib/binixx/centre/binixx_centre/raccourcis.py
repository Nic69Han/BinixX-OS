"""Aide-mémoire des raccourcis : fichier des raccourcis de Windows qui marchent ici, noms à afficher, et lecture de ce
que KDE a réellement enregistré dans la session. Aucune dépendance à Qt : testé seul
(tests/image/centre/test_raccourcis.py) ; l'outil en ligne de commande est /usr/libexec/binixx/binixx-raccourcis.

Les raccourcis s'écrivent comme dans KDE (« Meta+Shift+S » : Meta est la touche Windows). KDE les range dans son
service de raccourcis globaux (org.kde.kglobalaccel) ; on l'interroge par D-Bus avec busctl, sans shell, et on compare
les codes de touches de Qt (modificateurs + touche) avec ceux du fichier.
"""

import json
import os
import re
from dataclasses import dataclass

from . import catalogue, launch

RACCOURCIS = "/usr/share/binixx/raccourcis/raccourcis.tsv"
SOURCES = ("kde", "binixx")
XDG_RACCOURCIS = "/etc/xdg/kglobalshortcutsrc"

# Codes de Qt::KeyboardModifier (Qt6) : ils s'ajoutent au code de la touche
MODIFICATEURS = {"Meta": 0x10000000, "Ctrl": 0x04000000, "Alt": 0x08000000, "Shift": 0x02000000}
AFFICHAGE_MODIFICATEURS = {"Meta": "Windows", "Ctrl": "Ctrl", "Alt": "Alt", "Shift": "Maj"}
# Touches nommées : nom KDE -> (code Qt::Key, texte affiché)
TOUCHES = {
    "Esc": (0x01000000, "Échap"), "Tab": (0x01000001, "Tab"), "Return": (0x01000004, "Entrée"),
    "Del": (0x01000007, "Suppr"), "Print": (0x01000009, "Impr. écran"), "Left": (0x01000012, "←"),
    "Up": (0x01000013, "↑"), "Right": (0x01000014, "→"), "Down": (0x01000015, "↓"), "Space": (0x20, "Espace"),
    ".": (0x2E, "."),
}
SERVICE = ["busctl", "--user", "--json=short", "call", "org.kde.kglobalaccel"]
DELAI = 15


@dataclass(frozen=True)
class Raccourci:
    categorie: str
    touches: str
    action: str
    precision: str
    source: str


def _touche(nom):
    """(code Qt, texte affiché) d'une touche écrite à la KDE ; ValueError si on ne la connaît pas."""
    if nom in TOUCHES:
        return TOUCHES[nom]
    if re.fullmatch(r"[A-Z]", nom):
        return ord(nom), nom
    if re.fullmatch(r"[0-9]", nom):
        return ord(nom), nom
    numero = re.fullmatch(r"F([1-9]|1[0-2])", nom)
    if numero:
        return 0x01000030 + int(numero.group(1)) - 1, nom
    raise ValueError(f"touche inconnue : « {nom} »")


def decomposer(touches):
    """(modificateurs, touche) d'une écriture comme « Ctrl+Shift+Esc » ; ValueError si elle est mal formée."""
    morceaux = touches.split("+")
    if len(morceaux) < 2 and touches not in ("Print",) and not re.fullmatch(r"F([1-9]|1[0-2])", touches):
        raise ValueError(f"raccourci sans modificateur : « {touches} »")
    *modificateurs, nom = morceaux
    if len(set(modificateurs)) != len(modificateurs) or any(m not in MODIFICATEURS for m in modificateurs):
        raise ValueError(f"modificateurs invalides : « {touches} »")
    _touche(nom)
    return modificateurs, nom


def code_qt(touches):
    """Le code que KDE donne à ce raccourci (modificateurs + touche) : celui qu'il renvoie par D-Bus."""
    modificateurs, nom = decomposer(touches)
    return sum(MODIFICATEURS[m] for m in modificateurs) + _touche(nom)[0]


def affichage(touches):
    """Les touches à dessiner, dans l'ordre : « Meta+Shift+S » -> [« Windows », « Maj », « S »]."""
    modificateurs, nom = decomposer(touches)
    return [AFFICHAGE_MODIFICATEURS[m] for m in modificateurs] + [_touche(nom)[1]]


def ecriture(code):
    """L'écriture à la KDE d'un code de Qt (« Meta+E »), ou « 0x… » pour une touche que l'on ne connaît pas."""
    reste = code
    morceaux = []
    for nom, valeur in MODIFICATEURS.items():
        if reste & valeur:
            morceaux.append(nom)
            reste &= ~valeur
    for nom, (valeur, _) in TOUCHES.items():
        if valeur == reste:
            return "+".join(morceaux + [nom])
    if 0x41 <= reste <= 0x5A or 0x30 <= reste <= 0x39:
        return "+".join(morceaux + [chr(reste)])
    if 0x01000030 <= reste <= 0x0100003B:
        return "+".join(morceaux + [f"F{reste - 0x01000030 + 1}"])
    return "+".join(morceaux + [f"0x{reste:x}"])


def charger(chemin=None):
    """Lit le fichier ; ValueError (avec le numéro de ligne) si une ligne est mal formée.

    BINIXX_RACCOURCIS désigne un autre fichier (tests, essais)."""
    chemin = chemin or os.environ.get("BINIXX_RACCOURCIS", RACCOURCIS)
    raccourcis, vus = [], {}
    with open(chemin, encoding="utf-8", newline="") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            ligne = ligne.rstrip("\n")
            if not ligne or ligne.startswith("#"):
                continue
            champs = ligne.split("\t")
            if len(champs) != 5:
                raise ValueError(f"{chemin}:{numero} : {len(champs)} colonnes au lieu de 5")
            categorie, touches, action, precision, source = champs
            if not categorie or not action:
                raise ValueError(f"{chemin}:{numero} : catégorie et action sont obligatoires")
            if source not in SOURCES:
                raise ValueError(f"{chemin}:{numero} : source « {source} » inconnue")
            try:
                code = code_qt(touches)
            except ValueError as erreur:
                raise ValueError(f"{chemin}:{numero} : {erreur}") from None
            if code in vus:
                raise ValueError(f"{chemin}:{numero} : « {touches} » déjà donné ligne {vus[code]}")
            vus[code] = numero
            raccourcis.append(Raccourci(categorie, touches, action, precision, source))
    return raccourcis


def categories(raccourcis):
    """Catégories dans l'ordre de première apparition."""
    vues = []
    for raccourci in raccourcis:
        if raccourci.categorie not in vues:
            vues.append(raccourci.categorie)
    return vues


def chercher(raccourcis, requete):
    """Les raccourcis qui répondent à `requete` (tous les mots doivent y figurer) ; requête vide : tous.

    Sans accents ni majuscules : « win e », « fichiers » et « captur » trouvent ce qu'on attend."""
    mots = catalogue.normaliser(requete).split()
    if not mots:
        return list(raccourcis)
    trouves = []
    for raccourci in raccourcis:
        texte = catalogue.normaliser(" ".join([raccourci.action, raccourci.precision, raccourci.categorie,
                                               raccourci.touches, *affichage(raccourci.touches)]))
        if all(mot in texte for mot in mots):
            trouves.append(raccourci)
    return trouves


# --- ce que KDE a enregistré dans la session -------------------------------------------------------------------------

def _entiers(valeur):
    """Tous les entiers d'une valeur JSON imbriquée (les séquences de touches y sont des listes de listes)."""
    if isinstance(valeur, bool):
        return []
    if isinstance(valeur, int):
        return [valeur]
    if isinstance(valeur, (list, tuple)):
        return [i for element in valeur for i in _entiers(element)]
    return []


def _chaines(valeur):
    if isinstance(valeur, str):
        return [valeur]
    if isinstance(valeur, (list, tuple)):
        return [c for element in valeur for c in _chaines(element)]
    return []


def _structures(valeur):
    """Les actions d'un composant : des listes qui commencent par six textes (contexte, action, composant…)."""
    if isinstance(valeur, list) and len(valeur) >= 7 and all(isinstance(x, str) for x in valeur[:6]):
        yield valeur
    elif isinstance(valeur, list):
        for element in valeur:
            yield from _structures(element)


def composants(sortie):
    """Les chemins D-Bus des composants de KDE, d'après la réponse de busctl --json à allComponents."""
    try:
        return [c for c in _chaines(json.loads(sortie).get("data", [])) if c.startswith("/")]
    except (ValueError, AttributeError):
        return []


def actions_du_composant(sortie):
    """[(composant, action, [codes de touches])] d'après la réponse de busctl --json à allShortcutInfos."""
    try:
        donnees = json.loads(sortie).get("data", [])
    except (ValueError, AttributeError):
        return []
    return [(s[4], s[2], _entiers(s[6])) for s in _structures(donnees)]


def enregistres(run=launch.run):
    """{code de touche : [(composant, action)]} de ce que KDE a enregistré ; None si on ne peut pas le lire
    (pas de session de bureau, service absent, réponse inattendue)."""
    code, sortie = run(SERVICE + ["/kglobalaccel", "org.kde.KGlobalAccel", "allComponents"], timeout=DELAI)
    chemins = composants(sortie) if code == 0 else []
    if not chemins:
        return None
    registre = {}
    for chemin in chemins:
        base = SERVICE + [chemin, "org.kde.kglobalaccel.Component", "allShortcutInfos"]
        code, sortie = run(base, timeout=DELAI)
        if code != 0:  # certaines versions de KDE veulent le nom du contexte en argument
            code, sortie = run(base + ["s", ""], timeout=DELAI)
        if code != 0:
            continue
        for composant, action, codes in actions_du_composant(sortie):
            for touche in codes:
                if touche:
                    registre.setdefault(touche, []).append((composant, action))
    return registre or None


def verifier(raccourcis, registre):
    """([(raccourci, [(composant, action)])] présents, [raccourci] absents) ; registre None : tout est absent."""
    presents, absents = [], []
    for raccourci in raccourcis:
        trouve = (registre or {}).get(code_qt(raccourci.touches))
        if trouve:
            presents.append((raccourci, trouve))
        else:
            absents.append(raccourci)
    return presents, absents


def touches_du_fichier_xdg(chemin=None):
    """{lanceur : touches} des « _launch » que l'image fournit (etc/xdg/kglobalshortcutsrc)."""
    chemin = chemin or os.environ.get("BINIXX_XDG_RACCOURCIS", XDG_RACCOURCIS)
    fournis, lanceur = {}, None
    try:
        with open(chemin, encoding="utf-8") as fichier:
            for ligne in fichier:
                ligne = ligne.strip()
                section = re.fullmatch(r"\[services\]\[(.+\.desktop)\]", ligne)
                if section:
                    lanceur = section.group(1)
                elif ligne.startswith("["):
                    lanceur = None
                elif lanceur and ligne.startswith("_launch="):
                    fournis[lanceur] = ligne.split("=", 1)[1].split("\t")[0].split(",")[0]
    except OSError:
        pass
    return fournis


def main(argv=None, run=launch.run, sortie=print):
    """binixx-raccourcis liste | verifier | registre ; code de sortie 1 si un raccourci annoncé manque."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-raccourcis",
                                     description="Les raccourcis de Windows qui marchent sur BinixX OS.")
    parser.add_argument("action", choices=("liste", "verifier", "registre"),
                        help="liste : les raccourcis annoncés ; verifier : sont-ils enregistrés par KDE dans la "
                             "session ? ; registre : tout ce que KDE a enregistré")
    args = parser.parse_args(argv)
    raccourcis = charger()
    if args.action == "liste":
        for raccourci in raccourcis:
            sortie(f"{' + '.join(affichage(raccourci.touches)):<28} {raccourci.action}")
        return 0
    registre = enregistres(run)
    if args.action == "registre":
        if registre is None:
            sortie("impossible de lire les raccourcis enregistrés par KDE (pas de session de bureau ?)")
            return 1
        for code in sorted(registre):
            for composant, action in registre[code]:
                sortie(f"{ecriture(code):<24} {composant} / {action}")
        return 0
    if registre is None:
        sortie("impossible de lire les raccourcis enregistrés par KDE (pas de session de bureau ?)")
        return 1
    presents, absents = verifier(raccourcis, registre)
    for raccourci, trouve in presents:
        qui = ", ".join(f"{composant} / {action}" for composant, action in trouve)
        sortie(f"ok       {raccourci.touches:<16} {raccourci.action} : {qui}")
    for raccourci in absents:
        sortie(f"MANQUE   {raccourci.touches:<16} {raccourci.action} : KDE n'a rien enregistré pour cette touche")
    sortie(f"{len(presents)} raccourcis enregistrés sur {len(raccourcis)}")
    return 1 if absents else 0
