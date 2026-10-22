"""Tests du clavier virtuel seulement sur écran tactile (binixx_centre.clavier_virtuel), sans Qt ni kwriteconfig6.

python3 -m unittest discover tests/image/centre
"""

import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
sys.path.insert(0, RACINE)

from binixx_centre import clavier_virtuel as cv  # noqa: E402


class FauxRun:
    """Enregistre les commandes ; udevadm répond selon `tactiles` (chemins des écrans tactiles)."""

    def __init__(self, tactiles=(), notify=True):
        self.commandes, self.tactiles, self.notify = [], set(tactiles), notify

    def __call__(self, argv, timeout=None):
        self.commandes.append(argv)
        if argv[0] == "udevadm":
            return 0, "ID_INPUT=1\nID_INPUT_TOUCHSCREEN=1\n" if argv[-1] in self.tactiles else "ID_INPUT=1\nID_INPUT_MOUSE=1\n"
        if "--notify" in argv and not self.notify:
            return 1, ""
        return 0, ""

    def ecritures(self):
        return [a for a in self.commandes if a[0] == "kwriteconfig6"]


class ClavierVirtuel(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.kwinrc = os.path.join(self.dossier, "kwinrc")
        self.marqueur = os.path.join(self.dossier, "binixx", "clavier-virtuel-coupe")

    def ajuster(self, run, tactile):
        return cv.ajuster(run=run, tactile=tactile, kwinrc=self.kwinrc, marqueur=self.marqueur)

    def kwinrc_ecrit(self, texte):
        with open(self.kwinrc, "w", encoding="utf-8") as fichier:
            fichier.write(texte)

    def test_detection_de_l_ecran_tactile(self):
        run = FauxRun(tactiles={"/sys/class/input/event5"})
        self.assertTrue(cv.ecran_tactile(run, ["/sys/class/input/event2", "/sys/class/input/event5"]))
        self.assertFalse(cv.ecran_tactile(FauxRun(), ["/sys/class/input/event2"]))
        self.assertFalse(cv.ecran_tactile(FauxRun(), []))

    def test_sans_ecran_tactile_le_clavier_est_coupe(self):
        run = FauxRun()
        self.assertIn("coupé", self.ajuster(run, tactile=False))
        self.assertEqual(run.ecritures(), [["kwriteconfig6", "--file", "kwinrc", "--group", "Wayland", "--key", "InputMethod",
                                            "--notify", ""]])
        self.assertTrue(os.path.exists(self.marqueur))
        # à la session suivante, rien de plus
        self.kwinrc_ecrit("[Wayland]\nInputMethod=\n")
        run = FauxRun()
        self.ajuster(run, tactile=False)
        self.assertEqual(run.ecritures(), [])

    def test_le_choix_de_l_utilisateur_est_respecte(self):
        self.kwinrc_ecrit("[Other]\nInputMethod=x\n\n[Wayland]\nInputMethod[$e]=/usr/share/applications/org.kde.plasma.keyboard.desktop\n")
        self.assertEqual(cv.choix_utilisateur(self.kwinrc), "/usr/share/applications/org.kde.plasma.keyboard.desktop")
        run = FauxRun()
        self.ajuster(run, tactile=False)
        self.assertEqual(run.ecritures(), [])
        self.assertFalse(os.path.exists(self.marqueur))

    def test_ecran_tactile_le_clavier_coupe_par_binixx_revient(self):
        run = FauxRun()
        self.ajuster(run, tactile=False)
        self.kwinrc_ecrit("[Wayland]\nInputMethod=\n")
        run = FauxRun()
        self.assertIn("rétabli", self.ajuster(run, tactile=True))
        self.assertEqual(run.ecritures(), [["kwriteconfig6", "--file", "kwinrc", "--group", "Wayland", "--key", "InputMethod",
                                            "--notify", "--delete"]])
        self.assertFalse(os.path.exists(self.marqueur))

    def test_ecran_tactile_sans_rien_a_faire(self):
        run = FauxRun()
        self.ajuster(run, tactile=True)
        self.assertEqual(run.ecritures(), [])

    def test_kwriteconfig6_sans_notify(self):
        run = FauxRun(notify=False)
        self.ajuster(run, tactile=False)
        self.assertEqual(run.ecritures()[-1], ["kwriteconfig6", "--file", "kwinrc", "--group", "Wayland", "--key", "InputMethod", ""])
        self.assertTrue(os.path.exists(self.marqueur))

    def test_kwinrc_absent(self):
        self.assertIsNone(cv.choix_utilisateur(os.path.join(self.dossier, "absent")))


if __name__ == "__main__":
    unittest.main()
