#!/usr/bin/python3
"""Avis de sécurité Fedora en attente pour les paquets d'une image BinixX OS, avec seuil bloquant.

Pourquoi pas Trivy ou Grype : ils ne couvrent pas Fedora (pas de base d'avis pour cette distribution). La source
fiable est celle de Fedora elle-même : `dnf updateinfo` liste, pour les paquets installés, les avis de sécurité
(FEDORA-2026-…) dont le correctif est déjà publié. Un avis en attente = une faille connue **et corrigeable**.

Usage (voir `just scan-securite`) :
  podman run --rm IMAGE dnf5 --refresh updateinfo list --security | avis-securite.py [--seuil Critical] \
      [--acceptes securite/avis-acceptes.txt]

Sortie : le tableau des avis (gravité, paquet) ; code 0 si aucun avis n'atteint le seuil, 1 sinon, 2 si l'entrée
n'est pas lisible (un contrôle qui ne comprend pas sa source ne doit jamais répondre « tout va bien »).

Test-témoin (`--temoin`) : lit la liste COMPLÈTE des avis connus (`dnf updateinfo list --security --all`) et exige
qu'au moins un avis soit compris. Sans lui, « aucun avis en attente » pourrait aussi vouloir dire « format de dnf
non reconnu » : le témoin prouve que l'analyseur lit la vraie sortie de la version de dnf de l'image.
Gravités : Critical > Important > Moderate > Low ; « sans gravité » (None, Unspecified) est listée mais ne bloque pas.
"""

import argparse
import re
import sys

GRAVITES = ["Low", "Moderate", "Important", "Critical"]  # croissante
RE_AVIS = re.compile(r"^FEDORA(?:-[A-Z]+)?-\d{4}-[0-9a-f]{6,}$", re.IGNORECASE)
RE_GRAVITE = re.compile(r"^(critical|important|moderate|low|none|unspecified)(?:/sec\.?)?$", re.IGNORECASE)
RE_PAQUET = re.compile(r"^[A-Za-z0-9_+.\-]+-[0-9][^\s]*\.(?:fc\d+|noarch|x86_64|aarch64|i686)[^\s]*$")


def normaliser(gravite):
    """« important/Sec. » -> « Important » ; « none » et « unspecified » -> None (sans gravité)."""
    nom = gravite.split("/")[0].capitalize()
    return nom if nom in GRAVITES else None


def lire(lignes):
    """Avis lus dans la sortie de `dnf updateinfo list` : liste de (avis, gravité ou None, paquet).

    Le format change d'une version de dnf à l'autre (colonnes, casse) : on reconnaît chaque champ par sa forme plutôt
    que par sa position. Lève ValueError si des lignes d'avis existent mais qu'aucune n'a pu être comprise."""
    avis, reconnues, vues = [], 0, 0
    for ligne in lignes:
        champs = ligne.split()
        identifiants = [c for c in champs if RE_AVIS.match(c)]
        if not identifiants:
            continue
        vues += 1
        gravites = [c for c in champs if RE_GRAVITE.match(c)]
        paquets = [c for c in champs if RE_PAQUET.match(c)]
        if not paquets:
            continue
        reconnues += 1
        avis.append((identifiants[0], normaliser(gravites[0]) if gravites else None, paquets[0]))
    if vues and not reconnues:
        raise ValueError(f"{vues} ligne(s) d'avis sans nom de paquet reconnaissable : format de dnf inattendu")
    return sorted(set(avis), key=lambda a: (-(GRAVITES.index(a[1]) if a[1] else -1), a[0], a[2]))


def lire_acceptes(texte):
    """Identifiants d'avis acceptés (un par ligne ; « # » commence un commentaire, la raison est obligatoire)."""
    acceptes = set()
    for numero, ligne in enumerate(texte.splitlines(), 1):
        contenu, _, raison = ligne.partition("#")
        contenu = contenu.strip()
        if not contenu:
            continue
        if not RE_AVIS.match(contenu):
            raise ValueError(f"ligne {numero} : « {contenu} » n'est pas un identifiant d'avis Fedora")
        if not raison.strip():
            raise ValueError(f"ligne {numero} : la raison de l'acceptation de {contenu} est obligatoire (après « # »)")
        acceptes.add(contenu.upper())
    return acceptes


def bloquants(avis, seuil, acceptes=()):
    """Avis d'une gravité au moins égale au seuil et non acceptés."""
    minimum = GRAVITES.index(seuil)
    acceptes = {a.upper() for a in acceptes}
    return [a for a in avis if a[1] is not None and GRAVITES.index(a[1]) >= minimum and a[0].upper() not in acceptes]


def rapport(avis, seuil, acceptes=()):
    lignes = []
    if not avis:
        return "Aucun avis de sécurité en attente pour les paquets de l'image."
    compte = {g: sum(1 for a in avis if a[1] == g) for g in reversed(GRAVITES)}
    compte["sans gravité"] = sum(1 for a in avis if a[1] is None)
    lignes.append(f"{len(avis)} avis de sécurité en attente : " + ", ".join(f"{n} {g}" for g, n in compte.items() if n))
    bloques = {a[0] for a in bloquants(avis, seuil, acceptes)}
    acceptes = {a.upper() for a in acceptes}
    for identifiant, gravite, paquet in avis:
        marque = "BLOQUANT" if identifiant in bloques else ("accepté" if identifiant.upper() in acceptes else "")
        lignes.append(f"  {identifiant:<22} {gravite or 'sans gravité':<13} {paquet}  {marque}".rstrip())
    return "\n".join(lignes)


def main(argv):
    analyseur = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    analyseur.add_argument("--seuil", default="Critical", choices=GRAVITES, help="gravité minimale qui bloque")
    analyseur.add_argument("--acceptes", help="fichier des avis acceptés, avec la raison")
    analyseur.add_argument("--temoin", action="store_true", help="vérifie que le format de dnf est compris (au moins un avis lu)")
    args = analyseur.parse_args(argv)
    if args.temoin:
        try:
            avis = lire(sys.stdin)
        except ValueError as erreur:
            print(f"Test-témoin : sortie de dnf illisible : {erreur}", file=sys.stderr)
            return 2
        if not avis:
            print("Test-témoin : aucun avis lu dans la liste complète ; le format de dnf n'est pas reconnu.", file=sys.stderr)
            return 2
        exemple = avis[0]
        print(f"Test-témoin : {len(avis)} avis lus dans la liste complète (exemple : {exemple[0]} {exemple[1] or 'sans gravité'} {exemple[2]}).")
        return 0
    acceptes = set()
    if args.acceptes:
        try:
            with open(args.acceptes, encoding="utf-8") as fichier:
                acceptes = lire_acceptes(fichier.read())
        except (OSError, ValueError) as erreur:
            print(f"Liste des avis acceptés illisible : {erreur}", file=sys.stderr)
            return 2
    try:
        avis = lire(sys.stdin)
    except ValueError as erreur:
        print(f"Sortie de dnf illisible : {erreur}", file=sys.stderr)
        return 2
    print(rapport(avis, args.seuil, acceptes))
    return 1 if bloquants(avis, args.seuil, acceptes) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
