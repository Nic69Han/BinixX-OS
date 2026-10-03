"""Tests du fond d'écran « Le marcheur de l'aube » (branding/fond_ecran.py) : le même fond à chaque exécution, un ciel
sombre et un horizon lumineux, un homme qui marche dessiné d'un seul tenant et posé sur l'horizon, les fichiers produits
pour l'image.

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
    from scipy.ndimage import label
    import fond_ecran as F
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
        cls.clair = F.rendre(480, "clair")
        cls.nuit = F.rendre(480, "nuit")

    def test_taille_16_9(self):
        self.assertEqual(self.clair.size, (480, 270))
        self.assertEqual(F.rendre(320, "clair").size, (320, 180))

    def test_le_meme_fond_a_chaque_execution(self):
        self.assertTrue(np.array_equal(np.asarray(self.clair), np.asarray(F.rendre(480, "clair"))))

    def test_une_graine_differente_change_les_etoiles(self):
        autre = F.rendre(480, "clair", graine=F.GRAINE + 1)
        self.assertFalse(np.array_equal(np.asarray(self.clair), np.asarray(autre)))

    def test_le_mode_sombre_est_plus_sombre(self):
        self.assertLess(clarte(self.nuit), clarte(self.clair))

    def test_mode_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            F.rendre(320, "jour")

    def test_ciel_sombre_en_haut_horizon_lumineux(self):
        a = np.asarray(self.clair.convert("L"), np.float32) / 255
        h = a.shape[0]
        haut = a[: h // 10].mean()
        horizon = a[int(h * 0.62): int(h * 0.74)].mean()
        planete = a[int(h * 0.92):].mean()
        self.assertLess(haut, 0.25)          # le haut du ciel reste sombre
        self.assertGreater(horizon, haut + 0.10)  # la lumière est du côté de l'horizon
        self.assertLess(planete, 0.08)       # la planète est presque noire

    def test_le_soleil_se_leve_a_droite(self):
        a = np.asarray(self.clair.convert("L"), np.float32) / 255
        h, w = a.shape
        soleil = a[int(h * 0.64): int(h * 0.72), int(w * 0.58): int(w * 0.66)].mean()
        loin = a[int(h * 0.64): int(h * 0.72), int(w * 0.05): int(w * 0.13)].mean()
        self.assertGreater(soleil, loin + 0.25)

    def test_pas_de_valeur_hors_plage_ni_d_image_vide(self):
        a = np.asarray(self.clair)
        self.assertEqual(a.dtype, np.uint8)
        self.assertGreater(a.std(), 20)

    def test_le_marcheur_est_une_forme_sombre_sur_la_lumiere(self):
        grand = F.rendre(1280, "clair")       # assez grand pour que l'homme fasse quelques pixels de large
        w, h = grand.size
        lieux = F.geometrie(w, h)
        xf, yf = lieux["pieds"]
        taille = lieux["taille"]
        a = np.asarray(grand.convert("L"), np.float32) / 255
        # le buste (au milieu de sa hauteur) est presque noir ; derrière lui, c'est le ciel de l'aube
        y = int(yf - 0.55 * taille)
        buste = a[y - 1: y + 2, int(xf) - 1: int(xf) + 2].mean()
        ciel = a[y, int(xf + 0.40 * taille)]
        self.assertLess(buste, 0.10)
        self.assertGreater(ciel, buste + 0.30)
        # et il se tient sur l'horizon : sous ses pieds, la planète est bien plus sombre que le ciel d'aube
        self.assertLess(a[int(yf) + 4, int(xf)], ciel - 0.40)

    def test_le_marcheur_est_en_vue_a_toutes_les_tailles(self):
        for largeur in (320, 1280):
            lieux = F.geometrie(largeur, round(largeur * 9 / 16))
            xf, yf = lieux["pieds"]
            self.assertGreater(lieux["taille"], 8)
            self.assertTrue(0 < xf < largeur and lieux["taille"] < yf < largeur * 9 / 16)


@unittest.skipUnless(AVEC_CALCUL, "numpy, scipy ou Pillow absent")
class Marcheur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taille = 120
        cls.masque, cls.pied_x, cls.pied_y = F.marcheur(cls.taille)

    def lignes(self, seuil=0.5):
        return self.masque > seuil

    def test_masque_en_niveaux_de_0_a_1(self):
        self.assertEqual(self.masque.dtype, np.float32)
        self.assertTrue(0 <= self.masque.min() and self.masque.max() <= 1.0001)
        self.assertGreater(self.masque.max(), 0.99)

    def test_une_seule_forme_sans_morceau_perdu(self):
        _, nombre = label(self.lignes(0.3))
        self.assertEqual(nombre, 1)          # l'écharpe tient au cou, les bras au tronc, les pieds aux jambes

    def test_il_a_la_taille_demandee_les_pieds_au_sol(self):
        pleines = np.where(self.lignes().any(axis=1))[0]
        haut, bas = pleines.min(), pleines.max()
        self.assertAlmostEqual(self.pied_y - haut, self.taille, delta=0.08 * self.taille)   # de la tête au sol
        self.assertLessEqual(abs(bas - (self.pied_y - 1)), 2)                                # le bas touche le sol
        self.assertFalse(self.lignes()[self.pied_y + 2:].any())                              # rien sous le sol

    def morceau(self, rang, colonne):
        """Largeur du morceau de la rangée `rang` (nombre de pixels depuis le sol) qui contient la colonne donnée."""
        ligne = self.lignes()[self.pied_y - rang]
        morceaux, _ = label(ligne)
        numero = morceaux[colonne]
        return int((morceaux == numero).sum()) if numero else 0

    def test_proportions_humaines(self):
        t = self.taille
        # la tête (à la hauteur du front, loin de l'écharpe) fait à peu près un huitième de la taille
        tete = self.morceau(int(0.93 * t), self.pied_x + int((0.028 + 0.025 * 0.93) * t))
        self.assertGreater(tete / t, 0.09)
        self.assertLess(tete / t, 0.17)
        # les jambes se rejoignent au tiers de la taille environ : en dessous, deux jambes ; au-dessus, un seul corps
        m = self.lignes()
        rangs = [r for r in range(1, int(0.7 * t)) if label(m[self.pied_y - r])[1] == 1]
        self.assertGreater(rangs[0] / t, 0.2)
        self.assertLess(rangs[0] / t, 0.5)

    def test_deux_jambes_en_enjambee(self):
        ligne = self.lignes()[self.pied_y - int(0.12 * self.taille)]
        morceaux, nombre = label(ligne)
        self.assertEqual(nombre, 2)          # une jambe devant, une derrière
        colonnes = [np.where(morceaux == i)[0].mean() for i in (1, 2)]
        self.assertGreater(colonnes[1] - colonnes[0], 0.25 * self.taille)   # bien écartées

    def test_tourne_vers_la_droite_avec_l_echarpe_derriere(self):
        m = self.lignes()
        colonnes = np.where(m.any(axis=0))[0]
        # l'écharpe flotte à gauche (derrière) : la forme s'étend plus loin à gauche du pied qu'à droite
        self.assertGreater(self.pied_x - colonnes.min(), colonnes.max() - self.pied_x)
        # le nez regarde à droite : au niveau du nez, la tête dépasse plus à droite de son centre qu'à gauche
        t = self.taille
        rang = self.pied_y - int(0.918 * t)
        centre = self.pied_x + int((0.028 + 0.025 * 0.918) * t)
        morceaux, _ = label(m[rang])
        colonnes = np.where(morceaux == morceaux[centre])[0]
        self.assertGreaterEqual((colonnes.max() - centre) - (centre - colonnes.min()), 1)

    def test_le_meme_dessin_a_chaque_fois(self):
        autre, _, _ = F.marcheur(self.taille)
        self.assertTrue(np.array_equal(self.masque, autre))


@unittest.skipUnless(AVEC_CALCUL, "numpy, scipy ou Pillow absent")
class Fichiers(unittest.TestCase):
    def test_ecrire_fonds(self):
        with tempfile.TemporaryDirectory() as dossier:
            F.ecrire_fonds(dossier, tailles=((320, 180), (640, 360)))
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
