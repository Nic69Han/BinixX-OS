"""Tests du relevé de mémoire vive (binixx-memoire), sur un faux /proc.

python3 -m unittest discover tests/image/centre
"""

import os
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
LIBEXEC = os.environ.get("BINIXX_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/binixx"))
SCRIPT = os.path.join(LIBEXEC, "binixx-memoire")

MEMINFO = """MemTotal:        4000000 kB
MemFree:          500000 kB
MemAvailable:    2976000 kB
SwapTotal:       3999744 kB
SwapFree:        3897344 kB
"""


def faux_proc(dossier, processus):
    with open(os.path.join(dossier, "meminfo"), "w", encoding="utf-8") as fichier:
        fichier.write(MEMINFO)
    for pid, (nom, pss) in processus.items():
        os.makedirs(os.path.join(dossier, str(pid)))
        with open(os.path.join(dossier, str(pid), "comm"), "w", encoding="utf-8") as fichier:
            fichier.write(nom + "\n")
        if pss is not None:
            with open(os.path.join(dossier, str(pid), "smaps_rollup"), "w", encoding="utf-8") as fichier:
                fichier.write(f"00400000-7fff [rollup]\nRss:  {pss * 2} kB\nPss:  {pss} kB\n")
    os.makedirs(os.path.join(dossier, "self"))  # entrée non numérique : ignorée


def lancer(*args):
    return subprocess.run([SCRIPT, *args], capture_output=True, text=True, timeout=30, check=False)


class Memoire(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        faux_proc(self.dossier, {
            10: ("plasmashell", 300 * 1024),
            11: ("chrome", 100 * 1024),
            12: ("chrome", 150 * 1024),
            13: ("kworker/0:1", 0),        # fil du noyau : pas de mémoire propre
            14: ("secret", None),          # smaps_rollup illisible (processus d'un autre utilisateur)
        })

    def test_valeurs_en_mo(self):
        fini = lancer("--racine", self.dossier, "--valeurs")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        valeurs = dict(ligne.split("=") for ligne in fini.stdout.split())
        self.assertEqual(valeurs, {"total": "3906", "utilise": "1000", "disponible": "2906",
                                   "echange_total": "3906", "echange_utilise": "100"})

    def test_les_processus_du_meme_nom_sont_reunis(self):
        fini = lancer("--racine", self.dossier)
        self.assertEqual(fini.returncode, 0, fini.stderr)
        lignes = fini.stdout.splitlines()
        self.assertIn("1000 Mo utilisés sur 3906 Mo", lignes[0])
        self.assertIn("100 Mo utilisés sur 3906 Mo", lignes[1])
        self.assertRegex(lignes[3], r"^\s+300\.0 Mo  plasmashell$")
        self.assertRegex(lignes[4], r"^\s+250\.0 Mo  chrome \(×2\)$")
        self.assertEqual(len(lignes), 5)  # ni fil du noyau, ni processus illisible

    def test_un_processus_par_ligne(self):
        fini = lancer("--racine", self.dossier, "--processus", "--top", "2")
        lignes = fini.stdout.splitlines()[3:]
        self.assertEqual([l.split()[-1] for l in lignes], ["plasmashell", "chrome"])

    def test_sur_le_vrai_proc(self):
        fini = lancer("--valeurs")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        self.assertIn("disponible=", fini.stdout)


class AccueilDejaVu(unittest.TestCase):
    """binixx-centre --premier-demarrage, accueil déjà vu : sortie avant de charger Qt (pas de PySide6, ni de Centre à importer)."""

    def lancer(self, marqueur):
        config = tempfile.mkdtemp()
        if marqueur:
            os.makedirs(os.path.join(config, "binixx"))
            open(os.path.join(config, "binixx", "accueil-vu"), "w", encoding="utf-8").close()
        env = {**os.environ, "XDG_CONFIG_HOME": config, "PYTHONPATH": "", "QT_QPA_PLATFORM": "offscreen"}
        return subprocess.run([sys.executable, "-X", "importtime", os.path.join(LIBEXEC, "binixx-centre"), "--premier-demarrage"],
                              capture_output=True, text=True, timeout=60, env=env, check=False)

    def test_sort_sans_importer_qt(self):
        fini = self.lancer(marqueur=True)
        self.assertEqual(fini.returncode, 0, fini.stderr[-500:])
        self.assertNotIn("PySide6", fini.stderr)
        self.assertNotIn("binixx_centre", fini.stderr)

    def test_premiere_fois_le_centre_est_charge(self):
        fini = self.lancer(marqueur=False)
        self.assertIn("binixx_centre", fini.stderr)


if __name__ == "__main__":
    unittest.main()
