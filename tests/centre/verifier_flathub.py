#!/usr/bin/env python3
"""Vérifie sur Flathub que chaque application « flatpak » du catalogue existe, et affiche sa licence.

Usage : tests/centre/verifier_flathub.py [catalogue.tsv]
Réseau nécessaire : à lancer à la main (ou en tâche planifiée), pas dans la CI d'image.
Code de sortie 1 si un identifiant est introuvable.
"""

import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAUT = Path(__file__).resolve().parents[2] / "system_files/usr/share/nicos/catalogue-windows/catalogue.tsv"


def main(chemin):
    lignes = [r for r in csv.reader(open(chemin, encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")]
    identifiants = sorted({r[4] for r in lignes if r[3] == "flatpak"})
    manquants = 0
    for ident in identifiants:
        try:
            with urllib.request.urlopen(f"https://flathub.org/api/v2/appstream/{ident}", timeout=30) as reponse:
                donnees = json.load(reponse)
            licence = donnees.get("project_license") or "?"
            print(f"  ok      {ident:45} {licence}")
        except urllib.error.HTTPError as erreur:
            manquants += 1
            print(f"  ÉCHEC   {ident:45} HTTP {erreur.code}")
    print(f"{len(identifiants)} applications Flatpak, {manquants} introuvable(s)")
    return 1 if manquants else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAUT))
