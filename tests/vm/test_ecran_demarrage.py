"""Tests de l'outil qui décrit l'écran de la VM pendant le démarrage (ecran_demarrage.py)."""

import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ecran_demarrage as ecran  # noqa: E402

L, H = 320, 200


def ppm(couleur_de, largeur=L, hauteur=H):
    """Image PPM binaire (comme celle de QEMU) dont chaque pixel vient de couleur_de(x, y)."""
    octets = bytearray()
    for y in range(hauteur):
        for x in range(largeur):
            octets += bytes(couleur_de(x, y))
    return b"P6\n%d %d\n255\n" % (largeur, hauteur) + bytes(octets)


def fond_bleu_nuit(x, y):
    """Le dégradé du thème Plymouth : 0b0f1a en haut, 10163a en bas."""
    t = y / (H - 1)
    return (round(11 + 5 * t), round(15 + 7 * t), round(26 + 32 * t))


def logo_au_centre(x, y):
    """Fond bleu nuit et un logo clair au centre."""
    if 130 <= x < 190 and 50 <= y < 110:
        return (230, 240, 255)
    return fond_bleu_nuit(x, y)


def console_de_texte(x, y):
    """Fond noir et quelques lignes de texte gris clair en haut à gauche."""
    if y % 12 < 6 and y < 120 and 4 <= x < 250 and (x // 3) % 3:
        return (170, 170, 170)
    return (0, 0, 0)


def bureau(x, y):
    return (200, 215, 235)


class LireTest(unittest.TestCase):
    def test_dimensions_et_octets(self):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(lambda x, y: (1, 2, 3), 4, 3))
        self.assertEqual((largeur, hauteur), (4, 3))
        self.assertEqual(len(pixels), 4 * 3 * 3)

    def test_commentaire_dans_l_entete(self):
        donnees = b"P6\n# fait par QEMU\n2 1\n255\n" + bytes(6)
        self.assertEqual(ecran.lire_ppm(donnees)[:2], (2, 1))

    def test_refuse_ce_qui_n_est_pas_un_ppm(self):
        with self.assertRaises(ValueError):
            ecran.lire_ppm(b"\x89PNG\r\n")

    def test_refuse_une_image_tronquee(self):
        with self.assertRaises(ValueError):
            ecran.lire_ppm(b"P6\n10 10\n255\n" + bytes(30))


class NatureTest(unittest.TestCase):
    def nature(self, couleur_de):
        return ecran.examiner(ppm(couleur_de))[4]

    def test_ecran_noir(self):
        self.assertEqual(self.nature(lambda x, y: (0, 0, 0)), ecran.NOIR)

    def test_ecran_de_demarrage_avec_logo(self):
        self.assertEqual(self.nature(logo_au_centre), ecran.DEMARRAGE)

    def test_fond_seul_est_un_ecran_de_demarrage(self):
        self.assertEqual(self.nature(fond_bleu_nuit), ecran.DEMARRAGE)

    def test_console_de_texte(self):
        self.assertEqual(self.nature(console_de_texte), ecran.TEXTE)

    def test_bureau_clair(self):
        self.assertEqual(self.nature(bureau), ecran.CLAIR)

    def test_ecran_sombre_sans_etre_noir(self):
        self.assertEqual(self.nature(lambda x, y: (40, 44, 52)), ecran.SOMBRE)

    def test_le_texte_n_est_jamais_pris_pour_l_ecran_de_demarrage(self):
        self.assertNotEqual(self.nature(console_de_texte), ecran.DEMARRAGE)

    def test_l_ecran_de_demarrage_n_est_jamais_pris_pour_du_texte(self):
        self.assertNotEqual(self.nature(logo_au_centre), ecran.TEXTE)


class MesuresTest(unittest.TestCase):
    def test_parts_entre_zero_et_un(self):
        _, _, _, mesures, _ = ecran.examiner(ppm(console_de_texte))
        for cle in ("noir", "fond", "clair"):
            self.assertGreaterEqual(mesures[cle], 0)
            self.assertLessEqual(mesures[cle], 1)

    def test_le_fond_du_theme_est_reconnu(self):
        for couleur in ((11, 15, 26), (16, 22, 58), (13, 18, 40)):
            self.assertTrue(ecran.fond_demarrage(*couleur), couleur)

    def test_le_noir_et_le_gris_ne_sont_pas_le_fond_du_theme(self):
        for couleur in ((0, 0, 0), (170, 170, 170), (40, 44, 52), (255, 255, 255)):
            self.assertFalse(ecran.fond_demarrage(*couleur), couleur)


class VignetteTest(unittest.TestCase):
    def test_dimensions(self):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(logo_au_centre))
        lignes = ecran.vignette(largeur, hauteur, pixels)
        self.assertEqual(len(lignes), ecran.LIGNES)
        self.assertTrue(all(len(ligne) <= ecran.COLONNES for ligne in lignes))

    def test_le_logo_se_voit_au_centre(self):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(logo_au_centre))
        lignes = ecran.vignette(largeur, hauteur, pixels)
        milieu = lignes[len(lignes) // 4 + 1]
        self.assertIn("@", milieu)
        self.assertEqual(lignes[0].strip(" .:"), "")

    def test_le_texte_se_voit_en_haut_a_gauche(self):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(console_de_texte))
        lignes = ecran.vignette(largeur, hauteur, pixels)
        self.assertTrue(lignes[1].strip())
        self.assertEqual(lignes[-1].strip(), "")


class DecrireTest(unittest.TestCase):
    def test_une_ligne_de_resume_avec_la_seconde_puis_la_vignette(self):
        largeur, hauteur, pixels, mesures, nature = ecran.examiner(ppm(logo_au_centre))
        lignes = ecran.decrire(largeur, hauteur, pixels, mesures, nature, seconde=7, avec_vignette=True)
        self.assertTrue(lignes[0].startswith("t=  7 s"))
        self.assertIn(ecran.DEMARRAGE, lignes[0])
        self.assertEqual(len(lignes), 1 + ecran.LIGNES)

    def test_sans_vignette_une_seule_ligne(self):
        largeur, hauteur, pixels, mesures, nature = ecran.examiner(ppm(bureau))
        self.assertEqual(len(ecran.decrire(largeur, hauteur, pixels, mesures, nature)), 1)


class LigneDeCommandeTest(unittest.TestCase):
    def test_resume_d_un_fichier(self):
        with tempfile.NamedTemporaryFile(suffix=".ppm") as fichier:
            fichier.write(ppm(logo_au_centre))
            fichier.flush()
            with contextlib.redirect_stdout(io.StringIO()) as sortie:
                self.assertEqual(ecran.main(["x", "resume", fichier.name]), 0)
        self.assertIn(ecran.DEMARRAGE, sortie.getvalue())

    def test_sans_argument_affiche_l_aide(self):
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            self.assertEqual(ecran.main(["x"]), 2)
        self.assertIn("surveiller", sortie.getvalue())


if __name__ == "__main__":
    unittest.main()
