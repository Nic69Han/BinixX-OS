"""Tests de l'écran de verrouillage en verre (build_files/verre_verrouillage.py), sur un extrait du LockScreenUi.qml de KDE
(plasma-desktop, desktoppackage/contents/lockscreen) : les deux repères, l'horloge et la pile du mot de passe, tels qu'ils sont dans
le fichier de KDE.

python3 -m unittest discover -s tests/themes
"""

import os
import sys
import tempfile
import unittest

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(RACINE, "build_files"))
import verre_verrouillage as V

# Extrait du LockScreenUi.qml de plasma-desktop (GPL-2.0-or-later, voir l'en-tête du fichier de KDE), raccourci
EXTRAIT = """Item {
    id: lockScreenUi

    Kirigami.Theme.inherit: false
    Kirigami.Theme.colorSet: Kirigami.Theme.Complementary

    MouseArea {
        id: lockScreenRoot

        Clock {
            id: clock
            property Item shadow: clockShadow
            visible: y > 0 && config.alwaysShowClock
            anchors.horizontalCenter: parent.horizontalCenter
        }

        StackView {
            id: mainStack
            anchors {
                left: parent.left
                right: parent.right
            }
            height: lockScreenRoot.height + Kirigami.Units.gridUnit * 3
        }
    }
}
"""


def accolades_equilibrees(texte):
    profondeur = 0
    for caractere in texte:
        profondeur += {"{": 1, "}": -1}.get(caractere, 0)
        if profondeur < 0:
            return False
    return profondeur == 0


class Verrouillage(unittest.TestCase):
    def test_verre_derriere_la_pile_du_mot_de_passe(self):
        texte = V.modifier(EXTRAIT)
        self.assertLess(texte.index("id: binixxVerre"), texte.index("id: mainStack"))  # dessiné avant, donc derrière
        self.assertIn("opacity: mainStack.opacity", texte)  # apparaît avec l'avatar et le mot de passe
        self.assertIn("radius: Kirigami.Units.gridUnit", texte)
        self.assertIn(V.VERRE, texte)
        # au même niveau que la pile (même parent), avec son retrait
        self.assertIn("\n        Rectangle {\n            id: binixxVerre\n", texte)

    def test_horloge_blanche(self):
        texte = V.modifier(EXTRAIT)
        horloge = texte[texte.index("Clock {"):texte.index("property Item shadow")]
        self.assertIn('Kirigami.Theme.textColor: "#FFFFFF"', horloge)
        self.assertIn("Kirigami.Theme.inherit: false", horloge)

    def test_textes_blancs_sur_tout_l_ecran(self):
        texte = V.modifier(EXTRAIT)
        racine = texte[:texte.index("MouseArea {")]
        self.assertIn('Kirigami.Theme.textColor: "#FFFFFF"', racine)
        self.assertEqual(texte.count('Kirigami.Theme.textColor: "#FFFFFF"'), 2)  # l'écran et l'horloge

    def test_qml_reste_bien_forme(self):
        self.assertTrue(accolades_equilibrees(V.modifier(EXTRAIT)))

    def test_une_seule_fois(self):
        une = V.modifier(EXTRAIT)
        self.assertEqual(V.modifier(une), une)
        self.assertEqual(une.count("binixxVerre"), 1)

    def test_kde_a_change_la_construction_echoue(self):
        with self.assertRaises(ValueError):
            V.modifier(EXTRAIT.replace("id: clock", "id: horloge"))
        with self.assertRaises(ValueError):
            V.modifier(EXTRAIT.replace("id: mainStack", "id: pile"))
        with self.assertRaises(ValueError):
            V.modifier(EXTRAIT.replace("Kirigami.Theme.Complementary", "Kirigami.Theme.View"))

    def test_fichier_modifie_en_place(self):
        with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False, encoding="utf-8") as fichier:
            fichier.write(EXTRAIT)
        try:
            V.main([fichier.name])
            with open(fichier.name, encoding="utf-8") as lu:
                self.assertIn("binixxVerre", lu.read())
        finally:
            os.unlink(fichier.name)


if __name__ == "__main__":
    unittest.main()
