"""Tests du module de build build_files/modules.d/20-securite.sh : il applique les correctifs de sécurité déjà publiés,
sans toucher au noyau, et s'exécute avant le contrôle des avis.

python3 -m unittest discover -s tests/securite
"""

import os
import re
import subprocess
import unittest

ICI = os.path.dirname(__file__)
DEPOT = os.path.join(ICI, "../..")
MODULE = os.path.join(DEPOT, "build_files/modules.d/20-securite.sh")
BUILD = os.path.join(DEPOT, "build_files/build.sh")


def lire(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return fichier.read()


def commandes(texte):
    """Les lignes qui ne sont ni vides ni des commentaires."""
    return [ligne.strip() for ligne in texte.splitlines() if ligne.strip() and not ligne.strip().startswith("#")]


class Module(unittest.TestCase):
    def setUp(self):
        self.texte = lire(MODULE)
        self.commandes = commandes(self.texte)

    def test_syntaxe_bash(self):
        subprocess.run(["bash", "-n", MODULE], check=True)

    def test_echoue_au_moindre_probleme(self):
        self.assertIn("set -ouex pipefail", self.commandes)

    def test_applique_les_correctifs_de_securite_et_eux_seuls(self):
        mises_a_jour = [c for c in self.commandes if "upgrade" in c]
        self.assertEqual(len(mises_a_jour), 1, mises_a_jour)
        self.assertTrue(mises_a_jour[0].startswith("dnf5 -y upgrade"), mises_a_jour[0])
        self.assertIn("--security", mises_a_jour[0])   # pas de « dnf upgrade » complet : seulement les avis de sécurité

    def test_le_noyau_et_ses_modules_sont_exclus(self):
        mise_a_jour = next(c for c in self.commandes if "upgrade" in c)
        exclusions = re.search(r"--exclude=['\"]?([^'\"\s]+)", mise_a_jour)
        self.assertIsNotNone(exclusions, mise_a_jour)
        motifs = exclusions.group(1).split(",")
        for motif in ("kernel*", "kmod-*", "akmod-*"):
            self.assertIn(motif, motifs)

    def test_la_liste_des_avis_restants_n_arrete_pas_le_build(self):
        ligne = next(c for c in self.commandes if "updateinfo" in c)
        self.assertTrue(ligne.endswith("|| true"), ligne)

    def test_executable(self):
        self.assertTrue(os.access(MODULE, os.X_OK))


class Ordre(unittest.TestCase):
    def test_build_sh_lance_les_modules_dans_l_ordre_et_celui_ci_est_pris(self):
        texte = lire(BUILD)
        self.assertIn("for module in /ctx/modules.d/*.sh", texte)  # ordre alphabétique : 20- passe avant 45-, 50-, 70-…
        noms = sorted(f for f in os.listdir(os.path.dirname(MODULE)) if f.endswith(".sh"))
        self.assertIn("20-securite.sh", noms)
        self.assertEqual(noms[0], "20-securite.sh")  # avant les modules de fonctionnalités : tout ce qu'ils installent est à jour


if __name__ == "__main__":
    unittest.main()
