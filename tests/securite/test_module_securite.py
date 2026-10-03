"""Tests du script de build build_files/securite.sh : il applique les correctifs de sécurité déjà publiés, sans toucher
au noyau, et build.sh le lance AVANT toute personnalisation (sinon la mise à jour d'un paquet comme Firefox remet ses
fichiers d'origine par-dessus ceux de BinixX OS).

python3 -m unittest discover -s tests/securite
"""

import os
import re
import subprocess
import unittest

ICI = os.path.dirname(__file__)
DEPOT = os.path.join(ICI, "../..")
MODULE = os.path.join(DEPOT, "build_files/securite.sh")
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
    def setUp(self):
        self.lignes = lire(BUILD).splitlines()

    def numero(self, motif):
        """Numéro (à partir de 0) de la première ligne de build.sh qui contient `motif`."""
        return next(i for i, ligne in enumerate(self.lignes) if motif in ligne)

    def test_build_sh_lance_le_script_de_securite(self):
        self.assertEqual([l for l in self.lignes if "securite.sh" in l and not l.lstrip().startswith("#")],
                         ["bash /ctx/securite.sh"])

    def test_il_passe_avant_toute_personnalisation(self):
        securite = self.numero("bash /ctx/securite.sh")
        self.assertLess(securite, self.numero("cp -avf /ctx/system_files/. /"))   # avant les fichiers système
        self.assertLess(securite, self.numero("FIREFOX_DIR="))                    # avant les réglages de Firefox
        self.assertLess(securite, self.numero("for module in /ctx/modules.d/"))   # avant les modules

    def test_pas_de_mise_a_jour_apres_la_personnalisation(self):
        # une seule mise à jour, celle du script : build.sh et modules.d n'en lancent aucune autre
        fichiers = [BUILD] + [os.path.join(DEPOT, "build_files/modules.d", f)
                              for f in os.listdir(os.path.join(DEPOT, "build_files/modules.d")) if f.endswith(".sh")]
        for fichier in fichiers:
            for ligne in commandes(lire(fichier)):
                self.assertNotRegex(ligne, r"\b(dnf5?|rpm-ostree)\b.*\b(upgrade|update|distro-sync)\b", fichier)


if __name__ == "__main__":
    unittest.main()
