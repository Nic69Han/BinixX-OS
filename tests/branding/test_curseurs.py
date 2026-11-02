"""Tests du pointeur BinixX (branding/curseurs.py → system_files/usr/share/icons/binixx-curseurs) : des fichiers Xcursor valides, à toutes
les tailles, point actif dans l'image, attente animée, flèche blanche au contour bleu BinixX pastel, et les noms X11, CSS et Qt qui
mènent aux bonnes formes.

python3 -m unittest discover -s tests/branding
"""

import os
import struct
import sys
import unittest

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(RACINE, "branding"))
THEME = os.path.join(RACINE, "system_files", "usr", "share", "icons", "binixx-curseurs")
CURSEURS = os.path.join(THEME, "cursors")

try:
    import curseurs as C  # numpy ; PySide6 n'est importé que pour fabriquer
    AVEC_MODULE = True
except ImportError:
    AVEC_MODULE = False


def lire(chemin):
    """[(taille nominale, largeur, hauteur, x actif, y actif, délai, pixels ARGB)] d'un fichier Xcursor."""
    with open(chemin, "rb") as fichier:
        octets = fichier.read()
    magie, entete, version, nombre = struct.unpack_from("<4sIII", octets, 0)
    assert magie == b"Xcur" and entete == 16 and version == 0x10000, chemin
    images = []
    for i in range(nombre):
        genre, nominal, position = struct.unpack_from("<III", octets, 16 + 12 * i)
        assert genre == 0xFFFD0002, chemin
        taille_entete, genre2, nominal2, version2, l, h, xh, yh, delai = struct.unpack_from("<IIIIIIIII", octets, position)
        assert (taille_entete, genre2, nominal2, version2) == (36, genre, nominal, 1), chemin
        pixels = struct.unpack_from(f"<{l * h}I", octets, position + 36)
        images.append((nominal, l, h, xh, yh, delai, pixels))
    return images


@unittest.skipUnless(AVEC_MODULE, "numpy absent")
class Pointeur(unittest.TestCase):
    def test_un_fichier_valide_par_forme_a_toutes_les_tailles(self):
        for nom in C.FORMES:
            with self.subTest(forme=nom):
                chemin = os.path.join(CURSEURS, nom)
                self.assertTrue(os.path.isfile(chemin) and not os.path.islink(chemin))
                images = lire(chemin)
                self.assertEqual(sorted({i[0] for i in images}), sorted(C.TAILLES))
                for nominal, l, h, xh, yh, delai, _ in images:
                    self.assertEqual((l, h), (nominal, nominal))
                    self.assertTrue(0 <= xh < l and 0 <= yh < h)

    def test_attente_animee(self):
        for nom in ("wait", "progress"):
            images = lire(os.path.join(CURSEURS, nom))
            for taille in C.TAILLES:
                images_taille = [i for i in images if i[0] == taille]
                self.assertEqual(len(images_taille), C.IMAGES_ATTENTE, (nom, taille))
                self.assertTrue(all(i[5] == C.DELAI_MS for i in images_taille))
                self.assertGreater(len({i[6] for i in images_taille}), 1, "les images doivent tourner")

    def test_fleche_blanche_au_contour_pastel(self):
        _, l, h, xh, yh, _, pixels = next(i for i in lire(os.path.join(CURSEURS, "default")) if i[0] == 48)
        opaques = [p for p in pixels if p >> 24 == 255]
        rgb = [((p >> 16) & 255, (p >> 8) & 255, p & 255) for p in opaques]
        blancs = sum(1 for r, g, b in rgb if min(r, g, b) > 245)
        pastels = sum(1 for r, g, b in rgb if abs(r - 0xAD) < 24 and abs(g - 0xCF) < 24 and abs(b - 0xFB) < 16 and b - r > 50)
        sombres = sum(1 for r, g, b in rgb if max(r, g, b) < 120)
        self.assertGreater(blancs, 150)
        self.assertGreater(pastels, 40)
        self.assertEqual(sombres, 0)
        # le point actif est la pointe de la flèche, en haut à gauche
        self.assertLess(xh, l // 3)
        self.assertLess(yh, h // 6)

    def test_noms_des_applications(self):
        for nom, autres in C.ALIAS.items():
            for autre in autres:
                with self.subTest(nom=autre):
                    chemin = os.path.join(CURSEURS, autre)
                    self.assertTrue(os.path.islink(chemin))
                    self.assertEqual(os.readlink(chemin), nom)
        for indispensable in ("left_ptr", "xterm", "hand2", "watch", "left_ptr_watch", "fleur", "sb_h_double_arrow", "sb_v_double_arrow",
                              "top_left_corner", "top_right_corner", "crossed_circle", "openhand", "closedhand"):
            self.assertTrue(os.path.exists(os.path.join(CURSEURS, indispensable)), indispensable)
        # chaque fichier du dossier est une forme ou un nom connu (pas de reste d'une ancienne version)
        connus = set(C.FORMES) | {a for liste in C.ALIAS.values() for a in liste}
        self.assertEqual(set(os.listdir(CURSEURS)), connus)

    def test_theme(self):
        with open(os.path.join(THEME, "index.theme"), encoding="utf-8") as fichier:
            texte = fichier.read()
        self.assertIn("Name=BinixX", texte)
        self.assertIn("Inherits=breeze_cursors", texte)


if __name__ == "__main__":
    unittest.main()
