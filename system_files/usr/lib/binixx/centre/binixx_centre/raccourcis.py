"""Aide-mémoire des raccourcis : fichier des raccourcis de Windows qui marchent ici, noms à afficher, et lecture de ce
que KDE a réellement enregistré dans la session. Aucune dépendance à Qt : testé seul
(tests/image/centre/test_raccourcis.py) ; l'outil en ligne de commande est /usr/libexec/binixx/binixx-raccourcis.

Les raccourcis s'écrivent comme dans KDE (« Meta+Shift+S » : Meta est la touche Windows). KDE les range dans son
service de raccourcis globaux (org.kde.kglobalaccel) ; on l'interroge par D-Bus avec busctl, sans shell, et on compare
les codes de touches de Qt (modificateurs + touche) avec ceux du fichier.
"""

import glob
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
    """Les actions d'un composant : des listes qui commencent par six textes (nom de l'action, nom affiché, composant,
    nom affiché du composant, contexte, nom affiché du contexte), puis les touches actuelles et celles par défaut."""
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
    return [(s[2], s[0], _entiers(s[6])) for s in _structures(donnees)]


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


def conflits(presents):
    """[(raccourci, [(composant, action)])] : les touches annoncées que KDE donne à plusieurs actions. Une seule peut
    la recevoir : l'autre est ignorée, et on ne sait pas laquelle, donc le raccourci annoncé peut ne pas marcher."""
    return [(raccourci, trouve) for raccourci, trouve in presents if len(set(trouve)) > 1]


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


# --- une touche, un seul propriétaire ------------------------------------------------------------------------------------
# Les lanceurs de KDE (Spectacle, Configuration du système…) déclarent leurs touches dans leur fichier .desktop
# (X-KDE-Shortcuts, pour l'entrée principale ou pour une action) : c'est ce que le service de raccourcis de KDE lit.
# Si l'un d'eux prend une touche que BinixX OS annonce, KDE ne la donne qu'à l'un des deux, au hasard de l'ordre de
# démarrage. Au build, on retire donc la touche dans le .desktop de l'autre (le test VM vérifie qu'il ne reste aucun
# conflit). Un « [services] » dans kglobalshortcutsrc n'y suffit pas : KDE le laisse de côté pour ces lanceurs.
APPLICATIONS = "/usr/share/applications"
JOURNAL_RETRAITS = "/usr/share/binixx/raccourcis/touches-retirees.txt"


def _code_ou_rien(touches):
    try:
        return code_qt(touches)
    except ValueError:
        return None


def _action_de_section(ligne):
    """« _launch » pour [Desktop Entry], le nom de l'action pour [Desktop Action X], None pour le reste."""
    nom = ligne.strip().strip("[]")
    if nom == "Desktop Entry":
        return "_launch"
    return nom[len("Desktop Action "):] if nom.startswith("Desktop Action ") else None


def touches_du_lanceur(chemin):
    """{action : [touches]} des X-KDE-Shortcuts d'un .desktop : « _launch » pour l'entrée principale, le nom de l'action
    pour une [Desktop Action X]."""
    actions, action = {}, None
    try:
        with open(chemin, encoding="utf-8", errors="replace") as fichier:
            for ligne in fichier:
                if ligne.lstrip().startswith("["):
                    action = _action_de_section(ligne)
                elif action and ligne.startswith("X-KDE-Shortcuts="):
                    actions[action] = [t for t in re.split(r"[,\t;]", ligne.rstrip("\n").split("=", 1)[1]) if t]
    except OSError:
        pass
    return actions


def surcharges(raccourcis, dossier=None, chemin_xdg=None):
    """{lanceur : {action : [touches à garder]}} : ce qu'il reste à retirer aux lanceurs qui ne sont pas à BinixX OS pour que
    chaque touche de source « binixx » n'ait qu'un propriétaire. Vide quand il n'y a plus de conflit."""
    dossier = dossier or os.environ.get("BINIXX_LANCEURS", APPLICATIONS)
    prises = {code_qt(r.touches) for r in raccourcis if r.source == "binixx"}
    fournis = touches_du_fichier_xdg(chemin_xdg)       # un lanceur auquel l'image donne elle-même une touche la garde
    resultat = {}
    for chemin in sorted(glob.glob(os.path.join(dossier, "*.desktop"))):
        lanceur = os.path.basename(chemin)
        if lanceur.startswith("binixx-"):
            continue
        for action, touches in touches_du_lanceur(chemin).items():
            gardees = [t for t in touches
                       if _code_ou_rien(t) not in prises or (action == "_launch" and fournis.get(lanceur) == t)]
            if len(gardees) != len(touches):
                resultat.setdefault(lanceur, {})[action] = gardees
    return resultat


def retirer_des_lanceurs(retirees, dossier=None):
    """Réécrit les .desktop : pour chaque (lanceur, action), X-KDE-Shortcuts ne garde que les touches données (la ligne
    disparaît s'il n'en reste aucune). Les autres lignes ne changent pas."""
    dossier = dossier or os.environ.get("BINIXX_LANCEURS", APPLICATIONS)
    for lanceur, actions in retirees.items():
        chemin = os.path.join(dossier, lanceur)
        with open(chemin, encoding="utf-8") as fichier:
            lignes = fichier.read().split("\n")
        sortie, action = [], None
        for ligne in lignes:
            if ligne.lstrip().startswith("["):
                action = _action_de_section(ligne)
            elif action in actions and ligne.startswith("X-KDE-Shortcuts="):
                if actions[action]:
                    sortie.append("X-KDE-Shortcuts=" + ",".join(actions[action]))
                continue
            sortie.append(ligne)
        with open(chemin, "w", encoding="utf-8") as fichier:
            fichier.write("\n".join(sortie))


def decrire_retraits(avant, apres):
    """Les lignes du journal : « lanceur / action : touches d'origine -> touches gardées »."""
    return [f"{lanceur} / {action} : {', '.join(avant[lanceur][action])} -> {', '.join(touches) or 'aucune'}"
            for lanceur, actions in sorted(apres.items()) for action, touches in sorted(actions.items())]


def main(argv=None, run=launch.run, sortie=print):
    """binixx-raccourcis liste | verifier | registre | surcharger ; code de sortie 1 si un raccourci annoncé manque ou est disputé."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-raccourcis",
                                     description="Les raccourcis de Windows qui marchent sur BinixX OS.")
    parser.add_argument("action", choices=("liste", "verifier", "registre", "surcharger"),
                        help="liste : les raccourcis annoncés ; verifier : sont-ils enregistrés par KDE dans la "
                             "session, et par une seule action ? ; registre : tout ce que KDE a enregistré ; "
                             "surcharger : (build) retire nos touches aux lanceurs qui les prennent aussi")
    parser.add_argument("--verifier", action="store_true",
                        help="avec surcharger : n'écrit rien, échoue s'il reste un conflit")
    args = parser.parse_args(argv)
    raccourcis = charger()
    if args.action == "surcharger":
        retirees = surcharges(raccourcis)
        if args.verifier:
            for lanceur, actions in sorted(retirees.items()):
                for action in sorted(actions):
                    sortie(f"CONFLIT  {lanceur} / {action} garde une touche de BinixX OS")
            sortie(f"{sum(len(a) for a in retirees.values())} conflits de touches entre lanceurs")
            return 1 if retirees else 0
        dossier = os.environ.get("BINIXX_LANCEURS", APPLICATIONS)
        avant = {lanceur: touches_du_lanceur(os.path.join(dossier, lanceur)) for lanceur in retirees}
        retirer_des_lanceurs(retirees)
        lignes = decrire_retraits(avant, retirees)
        for ligne in lignes:
            sortie(f"touche retirée : {ligne}")
        journal = os.environ.get("BINIXX_JOURNAL_RETRAITS", JOURNAL_RETRAITS)
        try:
            os.makedirs(os.path.dirname(journal), exist_ok=True)
            with open(journal, "w", encoding="utf-8") as fichier:
                fichier.write("# Touches retirées aux lanceurs de KDE au build (binixx-raccourcis surcharger) : elles appartiennent à BinixX OS\n"
                              + "".join(ligne + "\n" for ligne in lignes))
        except OSError as erreur:
            sortie(f"journal non écrit : {erreur}")
        sortie(f"{len(lignes)} touches retirées à d'autres lanceurs")
        return 0
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
    disputes = {r.touches for r, _ in conflits(presents)}
    for raccourci, trouve in presents:
        qui = ", ".join(f"{composant} / {action}" for composant, action in trouve)
        if raccourci.touches in disputes:
            sortie(f"CONFLIT  {raccourci.touches:<16} {raccourci.action} : prise par plusieurs actions : {qui}")
        else:
            sortie(f"ok       {raccourci.touches:<16} {raccourci.action} : {qui}")
    for raccourci in absents:
        sortie(f"MANQUE   {raccourci.touches:<16} {raccourci.action} : KDE n'a rien enregistré pour cette touche")
    sortie(f"{len(presents) - len(disputes)} raccourcis enregistrés sur {len(raccourcis)}"
           + (f", {len(disputes)} en conflit" if disputes else ""))
    return 1 if absents or disputes else 0
