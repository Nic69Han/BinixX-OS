"""Tests du Centre en « verre fumé » (binixx_centre/theme.py, app.py) : une feuille de style claire (Aube) et une sombre (Nuit) aux
teintes de la barre des tâches, choisie d'après les couleurs du bureau et suivie quand elles changent ; la barre latérale est un
panneau détaché du bord.

python3 -m unittest discover -s tests/image/centre -p 'test_theme_verre.py'   (la partie Qt est ignorée sans PySide6)
"""

import os
import re
import sys
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
sys.path.insert(0, RACINE)

from binixx_centre import theme

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


class Feuilles(unittest.TestCase):
    def test_deux_feuilles_completes(self):
        clair, sombre = theme.feuille(False), theme.feuille(True)
        self.assertNotEqual(clair, sombre)
        for feuille in (clair, sombre):
            self.assertNotIn("{v.", feuille)
            self.assertNotIn("{{", feuille)
            self.assertEqual(feuille.count("{"), feuille.count("}"))
            for objet in ("QWidget#sidebar", "QPushButton#nav:checked", "QFrame#card", "QFrame#tuile", "QFrame#barre"):
                self.assertIn(objet, feuille)
        self.assertEqual(theme.STYLE, clair)

    def test_teintes_du_verre(self):
        # celles de la barre des tâches : fumé en Nuit, dépoli en Aube, liseré d'un pixel, accent bleu BinixX pour la page ouverte
        sombre, clair = theme.feuille(True), theme.feuille(False)
        self.assertIn("background: rgba(22,22,30,0.55)", sombre)
        self.assertIn("rgba(255,255,255,0.10)", sombre)
        self.assertIn("background: rgba(255,255,255,0.62)", clair)
        self.assertIn("rgba(0,0,0,0.08)", clair)
        for feuille in (sombre, clair):
            barre = re.search(r"QWidget#sidebar \{(.*?)\}", feuille, re.DOTALL).group(1)
            self.assertIn("border-radius: 22px", barre)
            self.assertIn(theme.BLUE, re.search(r"QPushButton#nav:checked \{(.*?)\}", feuille, re.DOTALL).group(1))

    def test_texte_lisible_sur_la_barre(self):
        # texte clair sur le verre fumé, sombre sur le verre dépoli
        self.assertIn("QLabel#sidebarTitle { color: #FFFFFF", theme.feuille(True))
        self.assertIn(f"QLabel#sidebarTitle {{ color: {theme.INK}", theme.feuille(False))


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Fenetre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import app
        cls.qt = QApplication.instance() or QApplication([])
        cls.module = app

    def palette(self, fond):
        palette = QPalette(self.qt.palette())
        palette.setColor(QPalette.Window, QColor(fond))
        return palette

    def setUp(self):
        self.ancienne = (QPalette(self.qt.palette()), self.qt.styleSheet())
        self.addCleanup(self.restaurer)

    def restaurer(self):
        self.qt.setPalette(self.ancienne[0])
        self.qt.setStyleSheet(self.ancienne[1])

    def test_feuille_d_apres_les_couleurs_du_bureau(self):
        self.assertTrue(theme.est_sombre(self.palette("#1E232E")))
        self.assertFalse(theme.est_sombre(self.palette("#F4F6FB")))
        self.qt.setPalette(self.palette("#1E232E"))
        self.module.appliquer_style(self.qt)
        self.assertEqual(self.qt.styleSheet(), theme.feuille(True))
        self.qt.setPalette(self.palette("#F4F6FB"))
        self.module.appliquer_style(self.qt)
        self.assertEqual(self.qt.styleSheet(), theme.feuille(False))

    def test_le_centre_suit_aube_et_nuit(self):
        self.qt.setPalette(self.palette("#F4F6FB"))
        self.module.appliquer_style(self.qt)
        centre = self.module.Centre()
        self.addCleanup(centre.close)
        centre.show()
        self.qt.setPalette(self.palette("#1E232E"))  # passage à Nuit, Centre ouvert
        self.qt.processEvents()
        self.assertEqual(self.qt.styleSheet(), theme.feuille(True))

    def test_barre_laterale_detachee_du_bord(self):
        centre = self.module.Centre()
        self.addCleanup(centre.close)
        centre.resize(1120, 720)
        centre.show()
        self.qt.processEvents()
        barre = centre.findChild(type(centre).__mro__[1], "sidebar")
        self.assertIsNotNone(barre)
        self.assertTrue(barre.testAttribute(Qt.WA_StyledBackground))
        self.assertGreaterEqual(barre.geometry().left(), 12)
        self.assertGreaterEqual(barre.geometry().top(), 12)
        self.assertLessEqual(barre.geometry().bottom(), centre.height() - 12)


if __name__ == "__main__":
    unittest.main()
