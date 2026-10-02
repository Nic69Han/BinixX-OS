"""Tests de securite/avis-securite.py : lecture de `dnf updateinfo list --security`, seuil, avis acceptés."""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
OUTIL = os.path.join(ICI, "../../securite/avis-securite.py")


def charger():
    chargeur = importlib.machinery.SourceFileLoader("avis", OUTIL)
    spec = importlib.util.spec_from_loader("avis", chargeur)
    module = importlib.util.module_from_spec(spec)
    chargeur.exec_module(module)
    return module


A = charger()

# dnf 4 : « Avis  Gravité/Sec.  Paquet »
DNF4 = """FEDORA-2026-1a2b3c4d5e Critical/Sec.  openssl-libs-1:3.5.4-1.fc44.x86_64
FEDORA-2026-0099aabbcc Moderate/Sec.  curl-8.15.0-2.fc44.x86_64
"""
# dnf 5 : « Nom  Type  Gravité  Paquet  Date »
DNF5 = """Name                    Type     Severity   Package                       Issued
FEDORA-2026-1a2b3c4d5e  security Critical   openssl-libs-1:3.5.4-1.fc44.x86_64  2026-10-01 00:00:00
FEDORA-2026-77ee88dd99  security Important  kernel-6.17.4-200.fc44.x86_64        2026-09-30 12:00:00
FEDORA-2026-5544332211  security None       foo-1.0-1.fc44.noarch                2026-09-29 12:00:00
"""


class Lecture(unittest.TestCase):
    def test_format_dnf4(self):
        avis = A.lire(DNF4.splitlines())
        self.assertEqual([(a[0], a[1]) for a in avis], [("FEDORA-2026-1a2b3c4d5e", "Critical"), ("FEDORA-2026-0099aabbcc", "Moderate")])
        self.assertEqual(avis[0][2], "openssl-libs-1:3.5.4-1.fc44.x86_64")

    def test_format_dnf5_avec_en_tete(self):
        avis = A.lire(DNF5.splitlines())
        self.assertEqual([a[1] for a in avis], ["Critical", "Important", None])  # triés par gravité décroissante

    def test_gravite_en_minuscules(self):
        self.assertEqual(A.lire(["FEDORA-2026-aaaaaaaa11 important bar-2.0-1.fc44.noarch"])[0][1], "Important")

    def test_sans_avis(self):
        self.assertEqual(A.lire([]), [])
        self.assertEqual(A.lire(["Updating and loading repositories:", "Repositories loaded."]), [])

    def test_doublons_fusionnes(self):
        ligne = "FEDORA-2026-1a2b3c4d5e Critical/Sec. a-1.0-1.fc44.x86_64"
        self.assertEqual(len(A.lire([ligne, ligne])), 1)

    def test_format_inconnu_est_une_erreur(self):
        with self.assertRaises(ValueError):
            A.lire(["FEDORA-2026-1a2b3c4d5e Critical un format que personne ne comprend"])


class Seuil(unittest.TestCase):
    def setUp(self):
        self.avis = A.lire(DNF5.splitlines())

    def test_seuil_critique(self):
        self.assertEqual([a[0] for a in A.bloquants(self.avis, "Critical")], ["FEDORA-2026-1a2b3c4d5e"])

    def test_seuil_important(self):
        self.assertEqual(len(A.bloquants(self.avis, "Important")), 2)

    def test_sans_gravite_ne_bloque_jamais(self):
        self.assertNotIn("FEDORA-2026-5544332211", [a[0] for a in A.bloquants(self.avis, "Low")])

    def test_avis_accepte(self):
        self.assertEqual(A.bloquants(self.avis, "Critical", {"fedora-2026-1a2b3c4d5e"}), [])

    def test_rapport(self):
        texte = A.rapport(self.avis, "Critical")
        self.assertIn("3 avis de sécurité en attente : 1 Critical, 1 Important, 1 sans gravité", texte)
        self.assertRegex(texte, r"FEDORA-2026-1a2b3c4d5e\s+Critical\s+openssl-libs\S+\s+BLOQUANT")
        self.assertNotRegex(texte, r"kernel\S+\s+BLOQUANT")
        self.assertIn("accepté", A.rapport(self.avis, "Critical", {"FEDORA-2026-1a2b3c4d5e"}))


class Acceptes(unittest.TestCase):
    def test_lecture(self):
        texte = "# commentaire\n\nFEDORA-2026-1a2b3c4d5e  # pas utilisé sur un poste de bureau\n"
        self.assertEqual(A.lire_acceptes(texte), {"FEDORA-2026-1A2B3C4D5E"})

    def test_raison_obligatoire(self):
        with self.assertRaises(ValueError) as erreur:
            A.lire_acceptes("FEDORA-2026-1a2b3c4d5e\n")
        self.assertIn("raison", str(erreur.exception))

    def test_identifiant_invalide(self):
        with self.assertRaises(ValueError):
            A.lire_acceptes("CVE-2026-1234  # un CVE n'est pas un avis Fedora\n")

    def test_le_fichier_du_depot_est_valide(self):
        with open(os.path.join(ICI, "../../securite/avis-acceptes.txt"), encoding="utf-8") as fichier:
            self.assertEqual(A.lire_acceptes(fichier.read()), set())  # le dépôt n'accepte aucun avis tant que ce n'est pas justifié


class LigneDeCommande(unittest.TestCase):
    def lancer(self, entree, *args):
        return subprocess.run([sys.executable, OUTIL, *args], input=entree, capture_output=True, text=True, check=False)

    def test_rien_en_attente(self):
        r = self.lancer("")
        self.assertEqual((r.returncode, "Aucun avis" in r.stdout), (0, True))

    def test_bloque_au_seuil(self):
        self.assertEqual(self.lancer(DNF5).returncode, 1)
        self.assertEqual(self.lancer(DNF4, "--seuil", "Important").returncode, 1)
        self.assertEqual(self.lancer("FEDORA-2026-0099aabbcc Moderate/Sec. curl-8.15.0-2.fc44.x86_64\n").returncode, 0)

    def test_avis_accepte_par_fichier(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fichier:
            fichier.write("FEDORA-2026-1a2b3c4d5e  # raison de test\n")
        self.addCleanup(os.unlink, fichier.name)
        self.assertEqual(self.lancer("FEDORA-2026-1a2b3c4d5e Critical/Sec. a-1.0-1.fc44.x86_64\n", "--acceptes", fichier.name).returncode, 0)

    def test_sortie_incomprise_donne_le_code_2(self):
        r = self.lancer("FEDORA-2026-1a2b3c4d5e Critical format inconnu\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("illisible", r.stderr)

    def test_temoin_reconnait_le_format(self):
        r = self.lancer(DNF5, "--temoin")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("3 avis lus", r.stdout)

    def test_temoin_echoue_si_rien_n_est_compris(self):
        for entree in ("", "Updating and loading repositories:\nRepositories loaded.\n"):
            r = self.lancer(entree, "--temoin")
            self.assertEqual(r.returncode, 2)
            self.assertIn("format de dnf n'est pas reconnu", r.stderr)

    def test_temoin_echoue_sur_un_format_inconnu(self):
        self.assertEqual(self.lancer("FEDORA-2026-1a2b3c4d5e Critical format inconnu\n", "--temoin").returncode, 2)

    def test_fichier_d_acceptes_sans_raison_donne_le_code_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fichier:
            fichier.write("FEDORA-2026-1a2b3c4d5e\n")
        self.addCleanup(os.unlink, fichier.name)
        self.assertEqual(self.lancer("", "--acceptes", fichier.name).returncode, 2)


if __name__ == "__main__":
    unittest.main()
