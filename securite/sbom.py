#!/usr/bin/python3
"""Inventaire des logiciels d'une image BinixX OS (SBOM) au format CycloneDX 1.6, sans dépendance.

Usage (voir `just sbom`) :
  podman run --rm IMAGE rpm -qa --qf "$(sbom.py --format-rpm)" | sbom.py --nom binixx --version testing \
      --os-release os-release > sbom.cdx.json

Entrée : une ligne par paquet RPM, champs séparés par des tabulations (nom, époque, version, release, architecture,
licence, RPM source, éditeur). Sortie : le SBOM en JSON sur la sortie standard, et un résumé (nombre de paquets,
licences) sur la sortie d'erreur. Les identifiants de paquet suivent la spécification « purl » : pkg:rpm/fedora/…

Les licences des paquets Fedora sont des expressions SPDX ; une licence qui n'en est pas une est conservée telle
quelle (champ « name ») plutôt que d'être devinée.
"""

import argparse
import collections
import datetime
import json
import re
import sys
import urllib.parse
import uuid

FORMAT_RPM = "%{NAME}\\t%{EPOCHNUM}\\t%{VERSION}\\t%{RELEASE}\\t%{ARCH}\\t%{LICENSE}\\t%{SOURCERPM}\\t%{VENDOR}\\n"
IDENTIFIANT = re.compile(r"^[A-Za-z0-9.\-]+\+?$")
IGNORES = {"gpg-pubkey"}  # clés de signature : des entrées de la base RPM, pas des logiciels
VIDE = {"", "(none)", "none"}


def est_spdx(texte):
    """Vrai si `texte` est une expression de licence SPDX bien formée : « A AND (B OR C WITH D) »."""
    jetons = re.findall(r"[()]|[^\s()]+", texte)
    position = 0

    def simple():
        nonlocal position
        if position >= len(jetons):
            return False
        if jetons[position] == "(":
            position += 1
            if not expression() or position >= len(jetons) or jetons[position] != ")":
                return False
            position += 1
            return True
        if jetons[position] in ("AND", "OR", "WITH", ")") or not IDENTIFIANT.match(jetons[position]):
            return False
        position += 1
        if position < len(jetons) and jetons[position] == "WITH":  # exception : « GPL-2.0-only WITH Classpath-exception-2.0 »
            position += 1
            if position >= len(jetons) or not IDENTIFIANT.match(jetons[position]):
                return False
            position += 1
        return True

    def expression():
        nonlocal position
        if not simple():
            return False
        while position < len(jetons) and jetons[position] in ("AND", "OR"):
            position += 1
            if not simple():
                return False
        return True

    return bool(jetons) and expression() and position == len(jetons)


def lire_os_release(texte):
    """Dictionnaire des lignes CLE=valeur d'un fichier os-release."""
    valeurs = {}
    for ligne in texte.splitlines():
        cle, sep, valeur = ligne.partition("=")
        if sep and not ligne.lstrip().startswith("#"):
            valeurs[cle.strip()] = valeur.strip().strip('"')
    return valeurs


def lire_paquets(lignes):
    """Paquets lus depuis `rpm -qa --qf FORMAT_RPM` (dictionnaires) ; lève ValueError sur une ligne mal formée."""
    paquets = []
    for numero, ligne in enumerate(lignes, 1):
        ligne = ligne.rstrip("\n")
        if not ligne.strip():
            continue
        champs = ligne.split("\t")
        if len(champs) != 8:
            raise ValueError(f"ligne {numero} : 8 champs attendus, {len(champs)} trouvés")
        nom, epoque, version, release, arch, licence, source, editeur = champs
        if nom in IGNORES:
            continue
        paquets.append({"nom": nom, "epoque": epoque if epoque not in VIDE else "0", "version": version,
                        "release": release, "arch": arch, "licence": licence.strip(), "source": source.strip(),
                        "editeur": editeur.strip()})
    return paquets


def purl(paquet, distro):
    """Identifiant purl d'un paquet RPM : pkg:rpm/fedora/nom@version-release?arch=…&distro=fedora-44[&epoch=…]."""
    quote = lambda texte: urllib.parse.quote(texte, safe="")  # noqa: E731
    base = f"pkg:rpm/{quote(distro['ID'])}/{quote(paquet['nom'])}@{quote(paquet['version'] + '-' + paquet['release'])}"
    parametres = [("arch", paquet["arch"]), ("distro", f"{distro['ID']}-{distro['VERSION_ID']}")]
    if paquet["epoque"] != "0":
        parametres.insert(0, ("epoch", paquet["epoque"]))
    return base + "?" + "&".join(f"{cle}={quote(valeur)}" for cle, valeur in sorted(parametres))


def composant(paquet, distro):
    identifiant = purl(paquet, distro)
    element = {"type": "library", "bom-ref": identifiant, "name": paquet["nom"],
               "version": paquet["version"] + "-" + paquet["release"], "purl": identifiant}
    if paquet["editeur"].lower() not in VIDE:
        element["supplier"] = {"name": paquet["editeur"]}
    if paquet["licence"].lower() not in VIDE:
        if est_spdx(paquet["licence"]):
            element["licenses"] = [{"expression": paquet["licence"]}]
        else:
            element["licenses"] = [{"license": {"name": paquet["licence"]}}]
    if paquet["source"].lower() not in VIDE:
        element["properties"] = [{"name": "rpm:sourcerpm", "value": paquet["source"]}]
    return element


def fabriquer(paquets, nom, version, distro, maintenant=None, numero=None):
    """Le document CycloneDX complet. `maintenant` et `numero` ne servent qu'aux tests (sortie reproductible)."""
    maintenant = maintenant or datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    racine = f"pkg:oci/{urllib.parse.quote(nom, safe='')}?tag={urllib.parse.quote(version, safe='')}"
    composants = sorted((composant(p, distro) for p in paquets), key=lambda c: c["bom-ref"])
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": "urn:uuid:" + (numero or str(uuid.uuid4())),
        "version": 1,
        "metadata": {
            "timestamp": maintenant.isoformat().replace("+00:00", "Z"),
            "tools": {"components": [{"type": "application", "name": "binixx-sbom", "version": "1"}]},
            "component": {"type": "container", "bom-ref": racine, "name": nom, "version": version, "purl": racine,
                          "description": distro.get("PRETTY_NAME", "BinixX OS")},
        },
        "components": composants,
    }


def resume(document):
    """Texte court : nombre de paquets, licences les plus fréquentes, paquets sans licence."""
    composants = document["components"]
    licences = collections.Counter()
    sans = 0
    for element in composants:
        declarees = element.get("licenses")
        if not declarees:
            sans += 1
            continue
        licences[declarees[0].get("expression") or declarees[0]["license"]["name"]] += 1
    lignes = [f"{len(composants)} paquets, {len(licences)} licences distinctes, {sans} sans licence déclarée."]
    lignes += [f"  {nombre:5d}  {licence}" for licence, nombre in licences.most_common(10)]
    return "\n".join(lignes)


def main(argv):
    analyseur = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    analyseur.add_argument("--format-rpm", action="store_true", help="affiche le format à passer à `rpm -qa --qf`")
    analyseur.add_argument("--nom", default="binixx")
    analyseur.add_argument("--version", default="testing")
    analyseur.add_argument("--os-release", help="fichier os-release de l'image")
    analyseur.add_argument("--minimum", type=int, default=500, help="nombre de paquets en dessous duquel on refuse")
    args = analyseur.parse_args(argv)
    if args.format_rpm:
        sys.stdout.write(FORMAT_RPM)
        return 0
    if not args.os_release:
        analyseur.error("--os-release est obligatoire")
    with open(args.os_release, encoding="utf-8") as fichier:
        distro = lire_os_release(fichier.read())
    if "ID" not in distro or "VERSION_ID" not in distro:
        print("os-release : ID ou VERSION_ID absent", file=sys.stderr)
        return 2
    try:
        paquets = lire_paquets(sys.stdin)
    except ValueError as erreur:
        print(f"Entrée illisible : {erreur}", file=sys.stderr)
        return 2
    if len(paquets) < args.minimum:  # un inventaire presque vide est une erreur, pas un résultat
        print(f"Seulement {len(paquets)} paquets (minimum {args.minimum}) : l'inventaire est incomplet.", file=sys.stderr)
        return 2
    document = fabriquer(paquets, args.nom, args.version, distro)
    json.dump(document, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")
    print(resume(document), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
