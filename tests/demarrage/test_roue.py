"""Tests de la roue de chargement de l'écran de démarrage (branding/roue_demarrage.py) : sans elle, ou avec une animation à trous,
on croit l'ordinateur figé."""

import glob
import os
import struct
import sys
import unittest

RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
THEME = os.path.join(RACINE, "system_files", "usr", "share", "plymouth", "themes", "binixx")
BUILD = os.path.join(RACINE, "build_files", "build.sh")
sys.path.insert(0, os.path.join(RACINE, "branding"))

try:
    import numpy  # noqa: F401
    from PIL import Image

    import roue_demarrage
except ImportError:  # le dessin demande numpy et pillow (outils de l'identité visuelle) ; le reste se vérifie sans
    roue_demarrage = None


def images():
    return sorted(glob.glob(os.path.join(THEME, "throbber-*.png")))


def entete_png(chemin):
    with open(chemin, "rb") as f:
        octets = f.read(26)
    return octets[:8], octets[12:16], struct.unpack(">II", octets[16:24]), octets[24], octets[25]


class ImagesDeLaRoueTest(unittest.TestCase):
    def test_images_numerotees_sans_trou_a_partir_de_0001(self):
        noms = [os.path.basename(f) for f in images()]
        self.assertGreaterEqual(len(noms), 12)
        self.assertEqual(noms, [f"throbber-{i + 1:04d}.png" for i in range(len(noms))])

    def test_ce_sont_des_png_de_meme_taille_avec_transparence(self):
        tailles = set()
        for chemin in images():
            signature, ihdr, taille, profondeur, type_de_couleur = entete_png(chemin)
            self.assertEqual(signature, b"\x89PNG\r\n\x1a\n", chemin)
            self.assertEqual(ihdr, b"IHDR", chemin)
            self.assertEqual((profondeur, type_de_couleur), (8, 6), chemin)  # 8 bits, RGBA
            tailles.add(taille)
        self.assertEqual(len(tailles), 1, tailles)

    def test_la_roue_est_plus_grande_que_celle_de_fedora(self):
        # celle de Fedora : 32 px de côté, 24 px de diamètre : trop petite sur un écran moderne
        _, _, (largeur, hauteur), _, _ = entete_png(images()[0])
        self.assertGreaterEqual(min(largeur, hauteur), 48)

    def test_le_theme_cherche_les_images_dans_son_dossier(self):
        with open(os.path.join(THEME, "binixx.plymouth"), encoding="utf-8") as f:
            theme = f.read()
        self.assertIn("ImageDir=/usr/share/plymouth/themes/binixx", theme)

    def test_le_build_ne_copie_pas_la_roue_de_fedora(self):
        # une image de plus ou de moins dans l'animation la ferait sauter
        with open(BUILD, encoding="utf-8") as f:
            texte = f.read()
        self.assertIn("! -name 'throbber-*'", texte)


@unittest.skipIf(roue_demarrage is None, "numpy et pillow absents : dessin de la roue non vérifié ici")
class DessinTest(unittest.TestCase):
    def test_les_images_du_depot_sont_celles_que_le_script_dessine(self):
        for i, chemin in enumerate(images()):
            attendue = roue_demarrage.dessiner(-roue_demarrage.math.pi / 2 + 2 * roue_demarrage.math.pi * i / len(images()))
            with Image.open(chemin) as image:
                self.assertEqual(image.convert("RGBA").tobytes(), attendue.tobytes(), chemin)

    def test_un_tour_complet_revient_a_la_premiere_image(self):
        premiere = roue_demarrage.dessiner(-roue_demarrage.math.pi / 2)
        apres_un_tour = roue_demarrage.dessiner(-roue_demarrage.math.pi / 2 + 2 * roue_demarrage.math.pi)
        self.assertEqual(premiere.tobytes(), apres_un_tour.tobytes())

    def test_la_roue_tourne_chaque_image_differe_de_la_precedente(self):
        octets = [Image.open(chemin).convert("RGBA").tobytes() for chemin in images()]
        for avant, apres in zip(octets, octets[1:] + octets[:1]):
            self.assertNotEqual(avant, apres)

    def test_les_coins_sont_transparents_et_l_arc_est_opaque_et_clair(self):
        with Image.open(images()[0]) as image:
            rgba = image.convert("RGBA")
        largeur, hauteur = rgba.size
        for coin in ((0, 0), (largeur - 1, 0), (0, hauteur - 1), (largeur - 1, hauteur - 1)):
            self.assertEqual(rgba.getpixel(coin)[3], 0, coin)
        octets = rgba.tobytes()
        opaques = [octets[i:i + 4] for i in range(0, len(octets), 4) if octets[i + 3] >= 250]
        self.assertGreater(len(opaques), 20)
        # visible sur le fond bleu nuit du thème (luminance 20 environ) : la tête de l'arc est franchement plus claire
        self.assertGreater(max(0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] for p in opaques), 150)


if __name__ == "__main__":
    unittest.main()
