"""Tests du fond d'écran « Lever de gemme » (branding/lever_de_gemme.py) : le même fond à chaque exécution, la gemme du
logo bien dessinée, un ciel sombre et un horizon lumineux, les fichiers produits pour l'image.

python3 -m unittest discover -s tests/branding   (ignoré sans numpy, scipy et Pillow : pip install numpy scipy pillow)
"""

import os
import sys
import tempfile
import unittest

BRANDING = os.path.join(os.path.dirname(__file__), "../../branding")
sys.path.insert(0, BRANDING)

try:
    import numpy as np
    from PIL import Image
    import lever_de_gemme as L
    AVEC_CALCUL = True
except ImportError:
    AVEC_CALCUL = False


def clarte(image):
    """Luminosité moyenne d'une image Pillow, de 0 à 1."""
    return float(np.asarray(image.convert("L"), np.float32).mean() / 255)


@unittest.skipUnless(AVEC_CALCUL, "numpy, scipy ou Pillow absent")
class Fond(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clair = L.rendre(480, "clair")
        cls.nuit = L.rendre(480, "nuit")

    def test_taille_16_9(self):
        self.assertEqual(self.clair.size, (480, 270))
        self.assertEqual(L.rendre(320, "clair").size, (320, 180))

    def test_le_meme_fond_a_chaque_execution(self):
        self.assertTrue(np.array_equal(np.asarray(self.clair), np.asarray(L.rendre(480, "clair"))))

    def test_une_graine_differente_change_les_etoiles(self):
        autre = L.rendre(480, "clair", graine=L.GRAINE + 1)
        self.assertFalse(np.array_equal(np.asarray(self.clair), np.asarray(autre)))

    def test_le_mode_sombre_est_plus_sombre(self):
        self.assertLess(clarte(self.nuit), clarte(self.clair))

    def test_mode_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            L.rendre(320, "jour")

    def test_ciel_sombre_en_haut_horizon_lumineux(self):
        a = np.asarray(self.clair.convert("L"), np.float32) / 255
        h = a.shape[0]
        haut = a[: h // 10].mean()
        horizon = a[int(h * 0.62): int(h * 0.74)].mean()
        planete = a[int(h * 0.92):].mean()
        self.assertLess(haut, 0.25)          # le haut du ciel reste sombre
        self.assertGreater(horizon, haut + 0.10)  # la lumière est du côté de l'horizon
        self.assertLess(planete, 0.08)       # la planète est presque noire

    def test_la_gemme_est_au_dessus_de_l_horizon_a_droite(self):
        a = np.asarray(self.clair, np.float32)
        h, w, _ = a.shape
        # le centre de la gemme (62 % de la largeur) est bleu : le bleu domine le rouge
        bloc = a[int(h * 0.55): int(h * 0.62), int(w * 0.60): int(w * 0.64)]
        self.assertGreater(bloc[..., 2].mean(), bloc[..., 0].mean() + 60)

    def test_pas_de_valeur_hors_plage_ni_d_image_vide(self):
        a = np.asarray(self.clair)
        self.assertEqual(a.dtype, np.uint8)
        self.assertGreater(a.std(), 20)


@unittest.skipUnless(AVEC_CALCUL, "numpy, scipy ou Pillow absent")
class Gemme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taille = 160
        cls.couleur, cls.opacite = L.gemme(cls.taille)

    def test_formes(self):
        self.assertEqual(self.couleur.shape, (self.taille, self.taille, 3))
        self.assertEqual(self.opacite.shape, (self.taille, self.taille))
        self.assertTrue(0 <= self.opacite.min() and self.opacite.max() <= 1.0001)

    def test_losange_centre_et_coins_vides(self):
        n = self.taille
        self.assertGreater(self.opacite[n // 2, n // 2], 0.9)
        for y, x in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
            self.assertLess(self.opacite[y, x], 0.01)

    def test_trois_lames_separees_par_deux_entailles(self):
        n = self.taille
        # la diagonale du haut-gauche au bas-droit traverse les lames en travers
        ligne = np.array([self.opacite[i, i] for i in range(n)])
        lames, dans = 0, False
        for plein in ligne > 0.9:
            if plein and not dans:
                lames += 1
            dans = plein
        self.assertEqual(lames, 3)

    def test_degrade_ciel_vers_indigo(self):
        n = self.taille
        gauche = self.couleur[n // 2, int(n * 0.12)]
        droite = self.couleur[n // 2, int(n * 0.88)]
        self.assertGreater(gauche[1], droite[1] + 0.10)  # plus de vert (plus clair) à gauche

    def test_le_degrade_est_celui_du_logo(self):
        try:
            import generer
        except ImportError:
            self.skipTest("fonttools ou uharfbuzz absent (generer.py)")
        logo = [(float(o), c.upper()) for o, c in generer.GEM_LIGHT]
        self.assertEqual([(o, c.upper()) for o, c in L.GEM_LIGHT], logo)


@unittest.skipUnless(AVEC_CALCUL, "numpy, scipy ou Pillow absent")
class Fichiers(unittest.TestCase):
    def test_ecrire_fonds(self):
        with tempfile.TemporaryDirectory() as dossier:
            L.ecrire_fonds(dossier, tailles=((320, 180), (640, 360)))
            for sous_dossier in ("images", "images_dark"):
                for taille in ("320x180", "640x360"):
                    chemin = os.path.join(dossier, sous_dossier, f"{taille}.jpg")
                    self.assertTrue(os.path.getsize(chemin) > 1000, chemin)
                    with Image.open(chemin) as image:
                        self.assertEqual(f"{image.width}x{image.height}", taille)
            with Image.open(os.path.join(dossier, "screenshot.jpg")) as apercu:
                self.assertEqual(apercu.size, (640, 360))
            # même ciel dans toutes les tailles : la petite est la grande réduite
            with Image.open(os.path.join(dossier, "images", "320x180.jpg")) as petite, \
                    Image.open(os.path.join(dossier, "images", "640x360.jpg")) as grande:
                reduite = grande.resize(petite.size, Image.LANCZOS)
                ecart = np.abs(np.asarray(reduite, np.float32) - np.asarray(petite, np.float32)).mean()
                self.assertLess(ecart, 3)


if __name__ == "__main__":
    unittest.main()
