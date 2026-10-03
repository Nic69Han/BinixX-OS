"""Tests des éléments d'interface partagés (en-tête, cartes, grille, pastilles) et de leur usage par toutes les pages.

python3 -m unittest discover -s tests/image/centre -p 'test_widgets.py'   (ignoré sans PySide6)
"""

import os
import sys
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Elements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import theme, widgets
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.widgets, cls.theme = widgets, theme

    def textes(self, widget):
        return [etiquette.text() for etiquette in widget.findChildren(QLabel)]

    def test_une_carte_garde_son_bouton_et_ses_lignes(self):
        appels = []
        carte = self.widgets.carte("Titre", "Corps", "Ouvrir", lambda: appels.append(1), details="Détail",
                                   icone="folder", couleurs=self.theme.ACCENTS["vert"], avant="Avant")
        self.assertEqual(carte.bouton.text(), "Ouvrir")
        carte.bouton.click()
        self.assertEqual(appels, [1])
        textes = self.textes(carte)
        for attendu in ("Titre", "Corps", "Détail", "Avant"):
            self.assertIn(attendu, textes)
        # l'étiquette « avant » est au-dessus du titre, le détail en dessous
        self.assertLess(textes.index("Avant"), textes.index("Titre"))
        self.assertLess(textes.index("Titre"), textes.index("Détail"))
        self.assertEqual(carte.objectName(), "card")

    def test_une_carte_sans_bouton_ni_texte(self):
        carte = self.widgets.carte("Seulement un titre", "")
        self.assertIsNone(carte.bouton)
        self.assertEqual(self.textes(carte), ["Seulement un titre"])

    def test_une_carte_accepte_un_corps_a_la_place_du_texte(self):
        corps = QLabel("Un widget à moi")
        carte = self.widgets.carte("Titre", "ignoré", corps=corps)
        textes = self.textes(carte)
        self.assertIn("Un widget à moi", textes)
        self.assertNotIn("ignoré", textes)

    def test_une_carte_haute_a_son_bouton(self):
        carte = self.widgets.carte_haute("Titre", "Corps", "Aller", lambda: None, "home")
        self.assertEqual(carte.bouton.text(), "Aller")
        self.assertEqual(carte.bouton.objectName(), "primary")

    def test_l_entete_porte_titre_texte_et_elements(self):
        entete = self.widgets.entete("Mon titre", "Mon texte", "search", self.theme.ACCENTS["orange"])
        champ = self.widgets.recherche("Chercher…")
        entete.ajouter(champ)
        self.assertEqual(entete.titre.text(), "Mon titre")
        self.assertEqual(entete.texte.text(), "Mon texte")
        self.assertEqual(champ.placeholderText(), "Chercher…")
        entete.resize(800, 160)
        entete.show()
        self.app.processEvents()
        self.assertFalse(entete.grab().isNull())  # le dégradé se peint sans erreur
        entete.close()

    def test_la_section_change_de_couleur(self):
        section = self.widgets.section("Titre", self.theme.ACCENTS["rouge"])
        self.assertEqual(section.liseret.name().upper(), self.theme.ACCENTS["rouge"][0])
        section.colorer(self.theme.ACCENTS["vert"])
        self.assertEqual(section.liseret.name().upper(), self.theme.ACCENTS["vert"][0])
        section.setText("Autre titre")  # c'est un QLabel : le texte reste modifiable
        self.assertEqual(section.text(), "Autre titre")

    def test_les_pastilles_sont_en_cache_et_a_la_bonne_taille(self):
        w = self.widgets
        premiere = w.pastille("home", self.theme.ACCENTS["bleu"], 30)
        self.assertIs(premiere, w.pastille("home", self.theme.ACCENTS["bleu"], 30))
        self.assertIsNot(premiere, w.pastille("home", self.theme.ACCENTS["rouge"], 30))
        self.assertEqual(premiere.width(), 60)  # deux fois plus fine que l'écran
        large = w.pastille("home", self.theme.ACCENTS["bleu"], 30, marge_droite=8)
        self.assertEqual((large.width(), large.height()), (76, 60))
        self.assertFalse(w.verre("home", 64).isNull())
        self.assertFalse(w.glyphe("chevron", "#112233", 16).isNull())

    def test_une_icone_inconnue_ne_plante_pas(self):
        self.assertFalse(self.widgets.pastille("n-existe-pas", self.theme.ACCENTS["bleu"], 30).isNull())

    def test_la_grille_passe_de_trois_colonnes_a_une(self):
        cartes = [self.widgets.carte_haute(f"Carte {i}", "Texte", "Bouton", lambda: None, "home") for i in range(6)]
        grille = self.widgets.Grille(cartes, colonnes=3, largeur_min=250)
        fenetre = QWidget()
        from PySide6.QtWidgets import QVBoxLayout
        QVBoxLayout(fenetre).addWidget(grille)
        try:
            for largeur, colonnes in ((1000, 3), (600, 2), (300, 1)):
                fenetre.resize(largeur, 500)
                fenetre.show()
                self.app.processEvents()
                self.assertEqual(grille.colonnes, colonnes, f"largeur {largeur}")
                # toutes les cartes restent dans la grille, dans l'ordre, sans doublon
                self.assertEqual([grille.grille.itemAt(i).widget() for i in range(grille.grille.count())], cartes)
        finally:
            fenetre.close()

    def test_la_grille_ne_force_pas_la_largeur_de_la_page(self):
        cartes = [self.widgets.carte_haute(f"Carte {i}", "Texte", "Bouton", lambda: None, "home") for i in range(3)]
        grille = self.widgets.Grille(cartes, colonnes=3, largeur_min=250)
        self.assertLessEqual(grille.minimumSizeHint().width(), 250)


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Pages(unittest.TestCase):
    """Chaque page a son pictogramme et sa couleur, et le Centre les montre dans la barre latérale."""

    @classmethod
    def setUpClass(cls):
        from binixx_centre import app, icones, pages, theme
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.icones, cls.theme, cls.modules = icones, theme, pages.discover()
        cls.centre = app.Centre()

    @classmethod
    def tearDownClass(cls):
        cls.centre.close()

    def test_chaque_page_a_son_icone_et_sa_couleur(self):
        self.assertGreaterEqual(len(self.modules), 9)
        for module in self.modules:
            self.assertIn(getattr(module, "ICONE", None), self.icones.ICONES, module.KEY)
            self.assertIn(getattr(module, "ACCENT", None), self.theme.ACCENTS.values(), module.KEY)

    def test_deux_pages_n_ont_pas_la_meme_couleur(self):
        couleurs = [module.ACCENT for module in self.modules]
        self.assertEqual(len(couleurs), len(set(couleurs)))

    def test_la_barre_laterale_montre_une_icone_par_page(self):
        boutons = self.centre.boutons.buttons()
        self.assertEqual(len(boutons), len(self.modules))
        for bouton in boutons:
            self.assertFalse(bouton.icon().isNull(), bouton.text())
            self.assertIsInstance(bouton, QPushButton)

    def test_aucune_page_en_erreur(self):
        self.assertEqual(self.centre.errors, [])

    def test_chaque_action_d_aide_a_son_pictogramme(self):
        from binixx_centre.pages import aide
        for _, _, _, action in aide.PROBLEMES:
            self.assertIn(aide.ICONES_ACTIONS[action], self.icones.ICONES, action)

    def test_les_cartes_de_l_accueil_ont_icone_et_couleur(self):
        from binixx_centre.pages import accueil
        for titre, _, bouton, action, icone, couleurs in accueil.CARTES:
            self.assertIn(icone, self.icones.ICONES, titre)
            self.assertIn(couleurs, self.theme.ACCENTS.values(), titre)
            self.assertTrue(callable(action) and bouton)


if __name__ == "__main__":
    unittest.main()
