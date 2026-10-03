#!/usr/bin/env python3
"""Vérifie sur Flathub que chaque application « flatpak » du catalogue existe, et affiche sa licence.

Usage : tests/centre/verifier_flathub.py [catalogue.tsv] [--ecrire licences.tsv]
Réseau nécessaire : à lancer à la main (ou en tâche planifiée), pas dans la CI d'image.
Code de sortie 1 si un identifiant est introuvable, ou si licences.tsv (à côté du catalogue) ne correspond plus à Flathub.
Avec --ecrire, régénère le fichier des licences (celui que la page « Applications » affiche) depuis Flathub.
"""

import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAUT = Path(__file__).resolve().parents[2] / "system_files/usr/share/binixx/catalogue-windows/catalogue.tsv"


ENTETE = """# Licences des applications Flatpak du catalogue, lues sur Flathub (champ project_license).
# Fichier généré : tests/centre/verifier_flathub.py --ecrire <ce fichier>. Une ligne : identifiant, tabulation, licence.
# « LicenseRef-proprietary » = code fermé ; tout le reste est une licence libre (identifiant SPDX).
"""


def licence_de(donnees):
    """Licence telle que Flathub la donne, sans l'adresse qui suit parfois « LicenseRef-proprietary= »."""
    return (donnees.get("project_license") or "").split("=", 1)[0].strip()


def lire_licences(chemin):
    licences = {}
    if chemin.exists():
        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            if ligne and not ligne.startswith("#"):
                ident, _, licence = ligne.partition("\t")
                licences[ident] = licence
    return licences


def main(chemin, ecrire=None):
    lignes = [r for r in csv.reader(open(chemin, encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")]
    identifiants = sorted({r[4] for r in lignes if r[3] == "flatpak"})
    manquants = 0
    trouvees = {}
    for ident in identifiants:
        try:
            with urllib.request.urlopen(f"https://flathub.org/api/v2/appstream/{ident}", timeout=30) as reponse:
                donnees = json.load(reponse)
            licence = licence_de(donnees)
            trouvees[ident] = licence
            print(f"  ok      {ident:45} {licence or '?'}")
        except urllib.error.HTTPError as erreur:
            manquants += 1
            print(f"  ÉCHEC   {ident:45} HTTP {erreur.code}")
    print(f"{len(identifiants)} applications Flatpak, {manquants} introuvable(s)")
    if ecrire:
        corps = "".join(f"{ident}\t{licence}\n" for ident, licence in sorted(trouvees.items()) if licence)
        ecrire.write_text(ENTETE + corps, encoding="utf-8")
        print(f"{ecrire} écrit ({len(trouvees)} applications)")
        return 1 if manquants else 0
    ecarts = 0
    connues = lire_licences(Path(chemin).with_name("licences.tsv"))
    for ident, licence in sorted(trouvees.items()):
        if licence and connues.get(ident) != licence:
            ecarts += 1
            print(f"  ÉCART   {ident:45} licences.tsv : {connues.get(ident, '(absente)')} ; Flathub : {licence}")
    if ecarts:
        print(f"{ecarts} licence(s) à mettre à jour : relancer avec --ecrire")
    return 1 if manquants or ecarts else 0


if __name__ == "__main__":
    arguments = sys.argv[1:]
    sortie = None
    if "--ecrire" in arguments:
        position = arguments.index("--ecrire")
        sortie = Path(arguments[position + 1])
        del arguments[position:position + 2]
    sys.exit(main(arguments[0] if arguments else DEFAUT, sortie))
