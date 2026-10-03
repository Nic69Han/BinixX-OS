"""Recherche unique (Windows + S) : applications, réglages, logiciels Windows, aide et fichiers, en une seule liste.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_recherche.py). La fenêtre est dans recherche_fenetre.py ;
l'outil en ligne de commande est /usr/libexec/binixx/binixx-recherche (`--texte imprimante` affiche les résultats).

Chaque source rend des résultats notés de la même façon (le nom exact d'abord, puis un début de nom, un synonyme…), pour
que « imprimante » mette le réglage des imprimantes en tête et que « word » mette l'équivalent de Word en tête. Les
catégories sont rangées par leur meilleur résultat : on tape Entrée sur la première ligne.
"""

import json
import os
import re
from dataclasses import dataclass

from . import catalogue, launch, parametres

DOSSIERS_LANCEURS = (
    "/usr/share/applications", "/usr/local/share/applications", "~/.local/share/applications",
    "/var/lib/flatpak/exports/share/applications", "~/.local/share/flatpak/exports/share/applications",
)
ORDRE = ("Applications", "Réglages", "Logiciels Windows", "Aide", "Fichiers")
PAR_CATEGORIE = 5
FICHIERS = ["baloosearch6", "-l", "6", "--"]
DELAI_FICHIERS = 10


@dataclass(frozen=True)
class Resultat:
    categorie: str
    titre: str
    precision: str
    icone: str        # un nom d'icône du thème (applications, fichiers) ou « : » + nom de icones.py (réglages…)
    action: tuple     # ("lanceur", chemin) | ("kcm", id) | ("centre", page, recherche) | ("fichier", chemin) | ...
    score: int


def mots_de(requete):
    return catalogue.normaliser(requete).split()


def noter(mots, nom, synonymes=(), autres=""):
    """Note d'une réponse à `mots` (déjà normalisés) : 0 si un mot ne s'y trouve pas, sinon d'autant plus haut que
    la requête ressemble au nom ou à un synonyme."""
    if not mots:
        return 0
    nom_n = catalogue.normaliser(nom)
    synonymes_n = [catalogue.normaliser(s) for s in synonymes]
    texte = " ".join([nom_n, *synonymes_n, catalogue.normaliser(autres)])
    # « wifi » doit trouver « Wi-Fi » : on compare aussi sans les espaces
    if not all(mot in texte or mot in texte.replace(" ", "") for mot in mots):
        return 0
    phrase = " ".join(mots)
    sans_espace = phrase.replace(" ", "")
    note = 10                                            # trouvé seulement dans le texte d'explication
    mots_du_nom = nom_n.split()
    if nom_n == phrase or nom_n.replace(" ", "") == sans_espace:
        note = 100
    elif phrase in synonymes_n or sans_espace in [s.replace(" ", "") for s in synonymes_n]:
        note = 80
    elif nom_n.startswith(phrase) or nom_n.replace(" ", "").startswith(sans_espace):
        note = 70
    elif any(m.startswith(phrase) for m in mots_du_nom):
        note = 55
    elif any(s.startswith(phrase) for s in synonymes_n):
        note = 50
    elif phrase in nom_n:
        note = 40
    elif all(any(m.startswith(mot) for m in mots_du_nom) for mot in mots):
        note = 45                                        # chaque mot commence un mot du nom, dans un autre ordre
    elif any(phrase in s for s in synonymes_n):
        note = 30
    return note + min(len(mots) - 1, 3)                  # un mot de plus qui correspond : un peu mieux


# --- applications ------------------------------------------------------------------------------------------------

def langue():
    """« fr » d'après l'environnement (LANGUAGE, LC_ALL, LC_MESSAGES, LANG) ; « fr » faute de mieux."""
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        valeur = os.environ.get(variable, "")
        if valeur and valeur not in ("C", "POSIX"):
            return re.split(r"[_.@:]", valeur)[0].lower() or "fr"
    return "fr"


def lire_lanceur(chemin, lang="fr"):
    """{nom, generique, commentaire, mots, icone, id, chemin} d'un fichier .desktop à montrer ; None s'il est masqué."""
    champs, dans_le_bloc = {}, False
    try:
        with open(chemin, encoding="utf-8", errors="replace") as fichier:
            for ligne in fichier:
                ligne = ligne.strip()
                if ligne.startswith("["):
                    dans_le_bloc = ligne == "[Desktop Entry]"
                    if not dans_le_bloc and champs:
                        break
                elif dans_le_bloc and "=" in ligne and not ligne.startswith("#"):
                    cle, valeur = ligne.split("=", 1)
                    champs[cle.strip()] = valeur.strip()
    except OSError:
        return None
    if champs.get("Type") != "Application" or champs.get("NoDisplay", "").lower() == "true" \
            or champs.get("Hidden", "").lower() == "true":
        return None
    seulement = [x for x in champs.get("OnlyShowIn", "").split(";") if x]
    sauf = [x for x in champs.get("NotShowIn", "").split(";") if x]
    if (seulement and "KDE" not in seulement) or "KDE" in sauf:
        return None

    def localise(cle):
        for variante in (f"{cle}[{lang}_FR]", f"{cle}[{lang}]", cle):
            if champs.get(variante):
                return champs[variante]
        return ""

    nom = localise("Name")
    if not nom:
        return None
    return {"nom": nom, "generique": localise("GenericName"), "commentaire": localise("Comment"),
            "mots": [m for m in localise("Keywords").split(";") if m], "icone": champs.get("Icon", ""),
            "id": os.path.basename(chemin)[:-len(".desktop")], "chemin": chemin}


def lanceurs(dossiers=None, lang=None):
    """Les applications installées (un premier lanceur gagne si deux dossiers en ont un du même nom).

    BINIXX_LANCEURS désigne d'autres dossiers, séparés par « : » (tests, essais)."""
    if dossiers is None:
        env = os.environ.get("BINIXX_LANCEURS")
        dossiers = env.split(os.pathsep) if env else DOSSIERS_LANCEURS
    lang = lang or langue()
    vus, trouves = set(), []
    for dossier in dossiers:
        dossier = os.path.expanduser(dossier)
        try:
            noms = sorted(os.listdir(dossier))
        except OSError:
            continue
        for fichier in noms:
            if not fichier.endswith(".desktop") or fichier in vus:
                continue
            vus.add(fichier)
            lanceur = lire_lanceur(os.path.join(dossier, fichier), lang)
            if lanceur:
                trouves.append(lanceur)
    return trouves


def chercher_applications(mots, liste):
    resultats = []
    for lanceur in liste:
        # Les mots-clés d'un lanceur pèsent peu : « Mon logiciel Windows » cite Word, Excel et Sage pour être trouvé
        # par ceux qui les cherchent, mais en tapant « word » on veut d'abord Word ou son équivalent
        note = noter(mots, lanceur["nom"], [lanceur["generique"]],
                     " ".join([*lanceur["mots"], lanceur["id"], lanceur["commentaire"]]))
        if note:
            resultats.append(Resultat("Applications", lanceur["nom"], lanceur["generique"] or lanceur["commentaire"],
                                      lanceur["icone"], ("lanceur", lanceur["chemin"]), note))
    return resultats


# --- réglages, logiciels Windows, aide, fichiers -----------------------------------------------------------------

ACTIONS_REGLAGES = {"kcm": "kcm", "page": "centre", "app": "app", "flatpak": "flatpak", "discover": "discover",
                    "info": "info"}


def action_du_reglage(reglage):
    genre = ACTIONS_REGLAGES[reglage.type]
    if genre == "centre":
        return ("centre", reglage.cible, "")
    return (genre, reglage.cible)


def chercher_reglages(mots, reglages):
    resultats = []
    for reglage in reglages:
        note = noter(mots, reglage.nom, reglage.alias, reglage.explication + " " + reglage.categorie)
        if note:
            resultats.append(Resultat("Réglages", reglage.nom, f"{reglage.categorie} : {reglage.explication}",
                                      ":" + reglage.icone, action_du_reglage(reglage), note))
    return resultats


def chercher_logiciels(mots, entrees, requete, installees=frozenset(), fournies=frozenset()):
    """Les logiciels Windows du catalogue : un inclus s'ouvre tout de suite, les autres ouvrent le catalogue."""
    resultats = []
    for entree in entrees:
        note = noter(mots, entree.windows, entree.alias, entree.remplacant + " " + entree.categorie)
        if not note:
            continue
        _, _, action = catalogue.etat(entree, installees, fournies)
        resultat_action = ("executer", *action) if action and entree.type == "inclus" else ("centre", "catalogue",
                                                                                          requete.strip())
        resultats.append(Resultat("Logiciels Windows", entree.windows,
                                  f"Sous BinixX OS : {entree.remplacant}" if entree.remplacant else entree.remarque,
                                  ":" + catalogue.icone_de(entree.categorie), resultat_action, note))
    return resultats


def chercher_aide(mots, sujets):
    """`sujets` : [(titre, texte)] des cas d'aide du Centre ; chaque réponse ouvre la page d'aide."""
    resultats = []
    for titre, texte in sujets:
        note = noter(mots, titre, (), texte)
        if note:
            resultats.append(Resultat("Aide", titre, texte, ":life-buoy", ("centre", "aide", ""), note))
    return resultats


def lire_fichiers(sortie):
    """Les fichiers de la réponse de baloosearch6 : un chemin absolu par ligne, rien d'autre."""
    resultats = []
    for ligne in sortie.splitlines():
        ligne = ligne.strip()
        if not ligne.startswith("/") or "\x00" in ligne:
            continue
        resultats.append(Resultat("Fichiers", os.path.basename(ligne) or ligne, os.path.dirname(ligne), "text-x-generic",
                                  ("fichier", ligne), 20 - len(resultats)))
    return resultats


def commande_fichiers(requete):
    """La commande qui cherche les fichiers (None si la requête est vide) ; le texte vient après « -- »."""
    mots = mots_de(requete)
    return FICHIERS + [" ".join(mots)] if mots else None


# --- l'ensemble --------------------------------------------------------------------------------------------------

class Index:
    """Tout ce qu'on peut chercher, lu une fois à l'ouverture de la fenêtre."""

    def __init__(self, applications=None, reglages=None, logiciels=None, aide=(), installees=frozenset(),
                 fournies=frozenset()):
        self.applications = lanceurs() if applications is None else applications
        self.reglages = self._charger(parametres.charger) if reglages is None else reglages
        self.logiciels = self._charger(catalogue.charger) if logiciels is None else logiciels
        self.aide = list(aide)
        self.installees = installees
        self.fournies = fournies

    @staticmethod
    def _charger(lecture):
        try:
            return lecture()
        except (OSError, ValueError):
            return []   # un fichier illisible n'empêche pas de chercher dans le reste

    def chercher(self, requete, maximum=PAR_CATEGORIE):
        """Résultats groupés : [(catégorie, [Resultat…])], la catégorie du meilleur résultat d'abord."""
        mots = mots_de(requete)
        if not mots:
            return []
        trouves = {
            "Applications": chercher_applications(mots, self.applications),
            "Réglages": chercher_reglages(mots, self.reglages),
            "Logiciels Windows": chercher_logiciels(mots, self.logiciels, requete, self.installees, self.fournies),
            "Aide": chercher_aide(mots, self.aide),
        }
        if trouves["Logiciels Windows"]:
            # le réglage « Mon logiciel Windows » (qui cite Word, Excel…) ferait doublon avec les logiciels trouvés
            trouves["Réglages"] = [r for r in trouves["Réglages"] if r.action != ("centre", "catalogue", "")]
        groupes = []
        for categorie in ORDRE:
            liste = sorted(trouves.get(categorie, []), key=lambda r: (-r.score, r.titre.lower()))[:maximum]
            if liste:
                groupes.append((categorie, liste))
        return sorted(groupes, key=lambda g: (-g[1][0].score, ORDRE.index(g[0])))


def a_plat(groupes):
    """Les résultats d'une recherche dans l'ordre où on les voit."""
    return [resultat for _, liste in groupes for resultat in liste]


def ajouter_fichiers(groupes, fichiers):
    """Ajoute la catégorie « Fichiers » (réponse tardive de baloosearch6) à la fin d'une recherche."""
    return list(groupes) + ([("Fichiers", fichiers[:PAR_CATEGORIE])] if fichiers else [])


def ouvrir(resultat, centre=launch):
    """Ouvre un résultat ; True s'il a pu l'être. Aucun shell : chaque genre a sa fonction de launch."""
    action = resultat.action
    genre = action[0]
    if genre == "lanceur":
        return centre.open_desktop_file(action[1])
    if genre == "kcm":
        return centre.open_settings(action[1])
    if genre == "centre":
        return centre.open_centre(action[1], action[2] if len(action) > 2 else "")
    if genre == "app":
        return centre.open_app(action[1])
    if genre == "flatpak":
        return centre.run_flatpak(action[1])
    if genre == "discover":
        return centre.open_discover_mode(action[1])
    if genre == "executer":
        return centre.executer((action[1], action[2]))
    if genre == "fichier":
        return centre.open_file(action[1])
    return False


def en_json(groupes):
    return json.dumps([{"categorie": c, "resultats": [{"titre": r.titre, "precision": r.precision, "action": list(r.action),
                                                        "score": r.score} for r in liste]} for c, liste in groupes],
                      ensure_ascii=False, indent=2)


def texte(groupes):
    lignes = []
    for categorie, liste in groupes:
        lignes.append(f"{categorie}")
        for r in liste:
            lignes.append(f"  {r.titre}" + (f" : {r.precision}" if r.precision else "") + f"   -> {' '.join(map(str, r.action))}")
    return "\n".join(lignes) if lignes else "Aucun résultat."


def main(argv=None, sortie=print):
    """binixx-recherche --texte MOT [--json] : affiche ce que la fenêtre de recherche montrerait (sans fenêtre)."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-recherche", description="Recherche unique de BinixX OS.")
    parser.add_argument("--texte", required=True, help="ce qu'on cherche")
    parser.add_argument("--json", action="store_true", help="réponse lisible par un programme")
    args = parser.parse_args(argv)
    groupes = Index().chercher(args.texte)
    sortie(en_json(groupes) if args.json else texte(groupes))
    return 0 if groupes else 1
