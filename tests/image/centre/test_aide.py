"""Tests de la page Aide : rapport de diagnostic et remise à zéro du bureau.

python3 -m unittest discover tests/image/centre   (la partie Qt est ignorée sans PySide6)
"""

import os
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
LIBEXEC = os.environ.get("BINIXX_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/binixx"))
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


def script(nom, *args, env=None):
    return subprocess.run([os.path.join(LIBEXEC, nom), *args], capture_output=True, text=True, timeout=120,
                          env={**os.environ, **(env or {})}, check=False)


class Diagnostic(unittest.TestCase):
    def test_le_rapport_est_complet_et_sans_secret(self):
        fini = script("binixx-diagnostic")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        for titre in ("Rapport de diagnostic BinixX OS", "== Système ==", "== Services en échec ==",
                      "== Espace disque ==", "Fin du rapport."):
            self.assertIn(titre, fini.stdout)
        self.assertNotIn("inet ", fini.stdout)  # aucune adresse IP


class Reinitialisation(unittest.TestCase):
    def setUp(self):
        self.maison = tempfile.TemporaryDirectory()
        self.config = os.path.join(self.maison.name, ".config")
        os.makedirs(os.path.join(self.config, "kdedefaults"))
        for nom in ("plasmashellrc", "kdeglobals", "kxkbrc", "plasma-localerc", "kdedefaults/package"):
            with open(os.path.join(self.config, nom), "w", encoding="utf-8") as f:
                f.write("x")
        self.env = {"HOME": self.maison.name, "XDG_CONFIG_HOME": self.config,
                    "XDG_STATE_HOME": os.path.join(self.maison.name, ".local/state"),
                    "XDG_DATA_HOME": os.path.join(self.maison.name, ".local/share")}

    def tearDown(self):
        self.maison.cleanup()

    def reste(self):
        return set(os.listdir(self.config))

    def test_sans_demande_rien_ne_bouge(self):
        script("binixx-reinitialiser-bureau", "appliquer", env=self.env)
        self.assertIn("plasmashellrc", self.reste())

    def test_programmer_puis_appliquer(self):
        script("binixx-reinitialiser-bureau", "programmer", env=self.env)
        self.assertEqual(script("binixx-reinitialiser-bureau", "etat", env=self.env).stdout.strip(), "programmee")
        self.assertIn("plasmashellrc", self.reste())  # rien tant que la session n'est pas fermée
        script("binixx-reinitialiser-bureau", "appliquer", env=self.env)
        self.assertEqual(self.reste(), {"kxkbrc", "plasma-localerc"})  # clavier et langue conservés
        sauvegardes = os.path.join(self.maison.name, ".local/share/binixx/sauvegardes")
        (dossier,) = os.listdir(sauvegardes)
        contenu = set(os.listdir(os.path.join(sauvegardes, dossier)))
        self.assertTrue({"plasmashellrc", "kdeglobals", "kdedefaults", "LISEZMOI.txt"} <= contenu)
        self.assertEqual(script("binixx-reinitialiser-bureau", "etat", env=self.env).stdout.strip(), "aucune")

    def test_annuler(self):
        script("binixx-reinitialiser-bureau", "programmer", env=self.env)
        script("binixx-reinitialiser-bureau", "annuler", env=self.env)
        script("binixx-reinitialiser-bureau", "appliquer", env=self.env)
        self.assertIn("plasmashellrc", self.reste())


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageAide(unittest.TestCase):
    def test_creer_un_rapport(self):
        from binixx_centre import launch
        from binixx_centre.pages import aide

        app = QApplication.instance() or QApplication(sys.argv[:1])
        with tempfile.TemporaryDirectory() as maison:
            ancien_home, os.environ["HOME"] = os.environ.get("HOME"), maison
            aide.DIAGNOSTIC = os.path.join(LIBEXEC, "binixx-diagnostic")
            ouvertures = []
            ancienne_ouverture, launch.open_app = launch.open_app, ouvertures.append
            try:
                chemin = aide.build(None).creer_rapport()
            finally:
                launch.open_app = ancienne_ouverture  # sans cela, les tests suivants n'ouvrent plus rien
                os.environ["HOME"] = ancien_home
            self.assertTrue(chemin.startswith(os.path.join(maison, "Documents", "Rapport-BinixX-OS-")))
            with open(chemin, encoding="utf-8") as f:
                self.assertIn("Fin du rapport.", f.read())
            self.assertEqual(ouvertures, ["org.kde.dolphin"])
        del app


if __name__ == "__main__":
    unittest.main()
