"""Tests de l'outil qui décrit l'écran de la VM pendant le démarrage (ecran_demarrage.py)."""

import contextlib
import io
import os
import shutil
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


def deux_lignes_en_haut(x, y):
    """Fond noir et une ou deux lignes de texte gris clair tout en haut à gauche : ce qu'écrit le chargement du noyau."""
    return (170, 170, 170) if y < 9 and 4 <= x < 250 and (x // 3) % 3 and y % 12 < 6 else (0, 0, 0)


def logo_sur_noir(x, y):
    """Fond noir et un logo clair au centre : l'écran du micrologiciel, ou la première image de la connexion."""
    return (230, 240, 255) if 120 <= x < 200 and 70 <= y < 110 else (0, 0, 0)


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

    def test_quelques_lignes_en_haut_a_gauche_ne_sont_pas_un_ecran_de_texte(self):
        self.assertEqual(self.nature(deux_lignes_en_haut), ecran.QUELQUES_LIGNES)

    def test_un_ecran_de_texte_couvre_beaucoup_plus_que_quelques_lignes(self):
        _, _, _, lignes, _ = ecran.examiner(ppm(deux_lignes_en_haut))
        _, _, _, texte, _ = ecran.examiner(ppm(console_de_texte))
        self.assertLess(lignes["clair"], ecran.PART_ECRAN_DE_TEXTE)
        self.assertGreater(texte["clair"], ecran.PART_ECRAN_DE_TEXTE)

    def test_logo_centre_sur_fond_noir_n_est_pas_du_texte(self):
        # le micrologiciel (UEFI) et la première image de la connexion ressemblent à du texte pour des mesures grossières
        self.assertEqual(self.nature(logo_sur_noir), ecran.LOGO)

    def test_le_texte_est_au_bord_gauche_le_logo_au_centre(self):
        _, _, _, texte, _ = ecran.examiner(ppm(console_de_texte))
        _, _, _, logo, _ = ecran.examiner(ppm(logo_sur_noir))
        self.assertGreaterEqual(texte["gauche"], ecran.PART_TEXTE)
        self.assertEqual(logo["gauche"], 0)

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


def captures(*suites):
    """[(seconde, code)] à partir de suites « (code, nombre) » : captures(("NOIR", 2), ("DEMARRAGE", 5))."""
    resultat = []
    for code, nombre in suites:
        resultat += [(len(resultat) + i, code) for i in range(nombre)]
    return resultat


class VerifierTest(unittest.TestCase):
    def bon_demarrage(self):
        return captures(("NOIR", 1), ("LOGO", 1), ("NOIR", 6), ("DEMARRAGE", 12), ("NOIR", 8), ("LOGO", 2), ("SOMBRE", 3), ("CLAIR", 5))

    def redemarrage_complet(self):
        """Ce que le test VM a mesuré : le bureau qui s'arrête, l'écran de démarrage de l'arrêt, le micrologiciel, puis le démarrage."""
        return captures(("SOMBRE", 1), ("DEMARRAGE", 1), ("NOIR", 1), ("LOGO", 7), ("DEMARRAGE", 8), ("NOIR", 8), ("LOGO", 2),
                        ("SOMBRE", 50))

    def test_un_redemarrage_complet_est_accepte(self):
        erreurs, infos = ecran.verifier(self.redemarrage_complet())
        self.assertEqual(erreurs, [])
        self.assertTrue(any("8 capture(s)" in info and "écran de démarrage BinixX OS visible" in info for info in infos))

    def test_l_ecran_de_demarrage_de_l_arret_ne_compte_pas_comme_celui_du_demarrage(self):
        # seul l'arrêt montre l'écran de démarrage, le démarrage montre du texte : à refuser
        erreurs, _ = ecran.verifier(captures(("SOMBRE", 1), ("DEMARRAGE", 3), ("NOIR", 1), ("TEXTE", 12), ("CLAIR", 5)))
        self.assertTrue(any("réapparu" in e or "avant l'écran de démarrage" in e for e in erreurs))

    def test_le_texte_de_l_arret_compte_avant_l_ecran_de_demarrage(self):
        erreurs, _ = ecran.verifier(captures(("SOMBRE", 1), ("TEXTE", 6), ("NOIR", 2), ("DEMARRAGE", 8), ("CLAIR", 5)))
        self.assertTrue(any("avant l'écran de démarrage" in e for e in erreurs))

    def test_quelques_lignes_avant_l_ecran_de_demarrage_sont_toleres(self):
        # ce que le test VM mesure : deux lignes du micrologiciel (OVMF) en haut à gauche, avant l'écran de démarrage
        erreurs, infos = ecran.verifier(captures(("NOIR", 2), ("LOGO", 1), ("LIGNES", 6), ("DEMARRAGE", 8), ("NOIR", 8), ("SOMBRE", 5)))
        self.assertEqual(erreurs, [])
        self.assertTrue(any("quelques lignes de texte avant l'écran de démarrage : 6" in info for info in infos))

    def test_des_lignes_qui_restent_trop_longtemps_sont_refusees(self):
        erreurs, _ = ecran.verifier(captures(("LIGNES", ecran.LIGNES_TOLEREES_AVANT + 1), ("DEMARRAGE", 8), ("CLAIR", 3)))
        self.assertTrue(any("quelques lignes de texte sont restées" in e for e in erreurs))

    def test_des_lignes_apres_l_ecran_de_demarrage_sont_refusees(self):
        erreurs, _ = ecran.verifier(captures(("DEMARRAGE", 8), ("LIGNES", 2), ("CLAIR", 3)))
        self.assertTrue(any("réapparu" in e for e in erreurs))

    def test_le_cas_sans_quiet_reste_refuse(self):
        # le test VM sans correctif : douze secondes d'écran de texte, jamais d'écran de démarrage
        erreurs, _ = ecran.verifier(captures(("NOIR", 2), ("LIGNES", 6), ("TEXTE", 12), ("NOIR", 2), ("SOMBRE", 30)))
        self.assertTrue(any("jamais apparu" in e for e in erreurs))
        self.assertTrue(any("écran de texte de console" in e for e in erreurs))

    def test_les_logos_ne_comptent_jamais_comme_du_texte(self):
        erreurs, _ = ecran.verifier(captures(("LOGO", 20), ("DEMARRAGE", 8), ("LOGO", 20), ("CLAIR", 3)))
        self.assertEqual(erreurs, [])

    def test_derniere_serie(self):
        self.assertEqual(ecran.derniere_serie(["A", "B", "A", "A", "C"], "A"), (2, 4))
        self.assertEqual(ecran.derniere_serie(["A", "A"], "A"), (0, 2))
        self.assertIsNone(ecran.derniere_serie(["B"], "A"))

    def test_un_demarrage_a_la_windows_est_accepte(self):
        erreurs, infos = ecran.verifier(self.bon_demarrage())
        self.assertEqual(erreurs, [])
        self.assertTrue(any("12 capture(s)" in info for info in infos))

    def test_pas_d_ecran_de_demarrage_est_refuse(self):
        erreurs, _ = ecran.verifier(captures(("NOIR", 10), ("CLAIR", 5)))
        self.assertTrue(any("jamais apparu" in e for e in erreurs))

    def test_du_texte_apres_l_ecran_de_demarrage_est_refuse(self):
        erreurs, _ = ecran.verifier(captures(("NOIR", 3), ("DEMARRAGE", 5), ("TEXTE", 2), ("CLAIR", 4)))
        self.assertTrue(any("réapparu" in e for e in erreurs))

    def test_beaucoup_de_texte_avant_l_ecran_de_demarrage_est_refuse(self):
        # le cas sans « quiet » : le noyau et systemd écrivent pendant une dizaine de secondes
        erreurs, _ = ecran.verifier(captures(("NOIR", 1), ("TEXTE", 12), ("DEMARRAGE", 4), ("CLAIR", 3)))
        self.assertTrue(any("avant l'écran de démarrage" in e for e in erreurs))

    def test_le_texte_du_micrologiciel_et_de_grub_est_toleré(self):
        erreurs, _ = ecran.verifier(captures(("TEXTE", ecran.TEXTE_TOLERE_AVANT), ("DEMARRAGE", 6), ("CLAIR", 3)))
        self.assertEqual(erreurs, [])

    def test_un_ecran_de_demarrage_qui_ne_part_pas_est_refuse(self):
        # le gestionnaire de connexion ne prend jamais la main : l'écran reste bloqué sur le logo
        erreurs, _ = ecran.verifier(captures(("NOIR", 2), ("DEMARRAGE", 60)))
        self.assertTrue(any("connexion" in e for e in erreurs))

    def test_un_ecran_noir_a_la_fin_est_refuse(self):
        erreurs, _ = ecran.verifier(captures(("DEMARRAGE", 6), ("NOIR", 30)))
        self.assertTrue(any("connexion" in e for e in erreurs))

    def test_la_connexion_peut_ne_pas_etre_exigee(self):
        erreurs, _ = ecran.verifier(captures(("DEMARRAGE", 6), ("NOIR", 3)), exiger_connexion=False)
        self.assertEqual(erreurs, [])

    def test_un_ecran_de_demarrage_trop_bref_est_refuse(self):
        erreurs, _ = ecran.verifier(captures(("NOIR", 5), ("DEMARRAGE", 1), ("CLAIR", 5)))
        self.assertTrue(any("n'est resté que" in e for e in erreurs))

    def test_aucune_capture_est_refusee(self):
        erreurs, _ = ecran.verifier([])
        self.assertTrue(erreurs)

    def test_le_plus_long_ecran_noir_apres_l_ecran_de_demarrage_est_signalé(self):
        _, infos = ecran.verifier(self.bon_demarrage())
        self.assertTrue(any("le plus long après l'écran de démarrage : 8" in info for info in infos))


class TableauTest(unittest.TestCase):
    def test_lecture_du_tableau_ecrit_par_surveiller(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fichier:
            fichier.write("seconde;nature;noir;fond;clair;luminance\n0;NOIR;1.000;0.000;0.000;0\n3;DEMARRAGE;0.000;0.990;0.005;21\n")
        try:
            self.assertEqual(ecran.lire_tableau(fichier.name), [(0, "NOIR"), (3, "DEMARRAGE")])
        finally:
            os.remove(fichier.name)

    def test_chaque_nature_a_un_code(self):
        for nature in (ecran.NOIR, ecran.TEXTE, ecran.QUELQUES_LIGNES, ecran.LOGO, ecran.DEMARRAGE, ecran.CLAIR, ecran.SOMBRE, ecran.AUTRE):
            self.assertIn(nature, ecran.CODES)

    def test_verifier_en_ligne_de_commande(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fichier:
            fichier.write("seconde;nature;noir;fond;clair;luminance\n")
            for seconde, code in captures(("NOIR", 2), ("DEMARRAGE", 5), ("CLAIR", 3)):
                fichier.write(f"{seconde};{code};0;0;0;0\n")
        try:
            with contextlib.redirect_stdout(io.StringIO()) as sortie:
                self.assertEqual(ecran.main(["x", "verifier", fichier.name]), 0)
            self.assertIn("ressemble à celui de Windows", sortie.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ecran.main(["x", "verifier", fichier.name, "--sans-connexion"]), 0)
        finally:
            os.remove(fichier.name)


class LectureDuTexteTest(unittest.TestCase):
    def test_sans_tesseract_la_lecture_est_vide(self):
        original = ecran.shutil.which
        ecran.shutil.which = lambda nom: None
        try:
            self.assertEqual(ecran.lire_le_texte(ppm(deux_lignes_en_haut)), "")
        finally:
            ecran.shutil.which = original

    def test_la_lecture_envoie_une_image_agrandie_et_inversee_a_tesseract(self):
        # faux tesseract : il copie l'image reçue dans un fichier et répond « bonjour »
        dossier = tempfile.mkdtemp()
        copie = os.path.join(dossier, "vue.ppm")
        faux = os.path.join(dossier, "tesseract")
        with open(faux, "w", encoding="utf-8") as f:
            f.write(f"#!/bin/sh\ncp \"$1\" {copie}\necho bonjour\n")
        os.chmod(faux, 0o755)
        original = ecran.shutil.which
        ecran.shutil.which = lambda nom: faux
        try:
            self.assertEqual(ecran.lire_le_texte(ppm(deux_lignes_en_haut), hauteur_lue=40, agrandissement=2), "bonjour")
            with open(copie, "rb") as f:
                largeur, hauteur, pixels = ecran.lire_ppm(f.read())
            self.assertEqual((largeur, hauteur), (L * 2, 40 * 2))
            self.assertEqual(tuple(pixels[:3]), (255, 255, 255))  # le fond noir devient blanc : texte foncé sur fond clair
        finally:
            ecran.shutil.which = original
            shutil.rmtree(dossier, ignore_errors=True)


def logo_en_haut(x, y):
    """Fond bleu nuit et un logo clair dans la moitié haute : comme à l'écran, il est au-dessus de la roue."""
    return (230, 240, 255) if 130 <= x < 190 and 10 <= y < 60 else fond_bleu_nuit(x, y)


def roue(angle, rayon=12, points=8):
    """Fond de démarrage, logo, et une roue de `points` points clairs qui tourne sous le logo (centre : 50 % de la largeur, 72 % de la hauteur)."""
    import math
    centres = [(L * ecran.INDICATEUR_X + rayon * math.cos(angle + k * 0.25), H * ecran.INDICATEUR_Y + rayon * math.sin(angle + k * 0.25))
               for k in range(points)]

    def couleur(x, y):
        if any((x - cx) ** 2 + (y - cy) ** 2 <= 4 for cx, cy in centres):
            return (255, 255, 255)
        return logo_en_haut(x, y)
    return couleur


def captures_avec_indicateur(*suites):
    """[(seconde, code, pixels clairs, pixels changés)] à partir de suites « (code, nombre, clairs, changés) »."""
    resultat = []
    for code, nombre, clairs, changes in suites:
        resultat += [(len(resultat) + i, code, clairs, changes) for i in range(nombre)]
    return resultat


class IndicateurTest(unittest.TestCase):
    def zone_de(self, angle):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(roue(angle)))
        return ecran.luminances_de_la_zone(largeur, hauteur, pixels)

    def test_la_zone_est_bornee_a_l_image(self):
        x0, y0, x1, y1 = ecran.zone_indicateur(L, H)
        self.assertTrue(0 <= x0 < x1 <= L and 0 <= y0 < y1 <= H)
        self.assertEqual((x0, x1), (int(L * ecran.INDICATEUR_X) - ecran.INDICATEUR_DEMI_COTE, int(L * ecran.INDICATEUR_X) + ecran.INDICATEUR_DEMI_COTE))

    def test_la_roue_est_vue_dans_la_zone(self):
        _, zone = self.zone_de(0.0)
        self.assertGreaterEqual(ecran.pixels_clairs(zone), ecran.INDICATEUR_MIN)

    def test_un_fond_seul_n_a_pas_d_indicateur(self):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(logo_en_haut))
        _, zone = ecran.luminances_de_la_zone(largeur, hauteur, pixels)
        self.assertLess(ecran.pixels_clairs(zone), ecran.INDICATEUR_MIN)

    def test_le_logo_de_l_ecran_n_est_pas_dans_la_zone(self):
        # logo BinixX OS : 213 px de haut, centré à 40 % de la hauteur (binixx.plymouth) ; la zone commence plus bas, à toute résolution usuelle
        for largeur, hauteur in ((1024, 768), (1280, 800), (1920, 1080), (2560, 1440), (3840, 2160)):
            bas_du_logo = 0.4 * (hauteur - 213) + 213
            self.assertGreater(ecran.zone_indicateur(largeur, hauteur)[1], bas_du_logo, (largeur, hauteur))

    def test_la_roue_qui_tourne_change_des_pixels(self):
        _, avant = self.zone_de(0.0)
        _, apres = self.zone_de(1.5)
        self.assertGreaterEqual(ecran.pixels_changes(apres, avant), ecran.MOUVEMENT_MIN)

    def test_la_meme_image_ne_change_rien(self):
        _, zone = self.zone_de(0.7)
        self.assertEqual(ecran.pixels_changes(zone, zone), 0)

    def test_sans_capture_precedente_on_ne_compare_pas(self):
        _, zone = self.zone_de(0.0)
        self.assertEqual(ecran.pixels_changes(zone, None), -1)
        self.assertEqual(ecran.pixels_changes(zone, zone[:-1]), -1)

    def test_l_ecran_avec_roue_reste_un_ecran_de_demarrage(self):
        largeur, hauteur, pixels = ecran.lire_ppm(ppm(roue(0.3)))
        self.assertEqual(ecran.classer(ecran.analyser(largeur, hauteur, pixels)), ecran.DEMARRAGE)

    def test_la_vignette_de_la_zone_montre_la_roue(self):
        largeur_zone, zone = self.zone_de(0.0)
        lignes = ecran.vignette_de_la_zone(largeur_zone, zone)
        self.assertTrue(any(ligne.strip() for ligne in lignes))
        self.assertEqual(len(lignes), -(-(len(zone) // largeur_zone) // 4))

    def bon(self):
        return captures_avec_indicateur(("NOIR", 6, 0, -1), ("DEMARRAGE", 1, 90, -1), ("DEMARRAGE", 7, 90, 27), ("NOIR", 4, 0, -1),
                                        ("SOMBRE", 3, 0, -1))

    def test_un_indicateur_visible_qui_bouge_est_accepte(self):
        erreurs, infos = ecran.verifier(self.bon())
        self.assertEqual(erreurs, [])
        self.assertTrue(any("indicateur de chargement : visible sur 8 capture(s) sur 8, en mouvement entre 7 paire(s) de captures sur 7" in i
                            for i in infos))

    def test_un_indicateur_absent_est_refuse(self):
        erreurs, _ = ecran.verifier(captures_avec_indicateur(("NOIR", 2, 0, -1), ("DEMARRAGE", 8, 0, 0), ("SOMBRE", 3, 0, -1)))
        self.assertTrue(any("pas d'indicateur de chargement visible" in e for e in erreurs))

    def test_un_indicateur_qui_ne_bouge_pas_est_refuse(self):
        erreurs, _ = ecran.verifier(captures_avec_indicateur(("NOIR", 2, 0, -1), ("DEMARRAGE", 1, 90, -1), ("DEMARRAGE", 7, 90, 0),
                                                              ("SOMBRE", 3, 0, -1)))
        self.assertTrue(any("ne bouge pas" in e for e in erreurs))

    def test_un_indicateur_qui_bouge_une_seule_fois_suffit(self):
        # une capture par seconde pour une animation à 30 images par seconde : deux captures peuvent tomber sur la même image
        erreurs, _ = ecran.verifier(captures_avec_indicateur(("NOIR", 2, 0, -1), ("DEMARRAGE", 1, 90, -1), ("DEMARRAGE", 5, 90, 0),
                                                              ("DEMARRAGE", 1, 90, 25), ("SOMBRE", 3, 0, -1)))
        self.assertEqual(erreurs, [])

    def test_trop_peu_de_comparaisons_ne_suffisent_pas_pour_refuser(self):
        erreurs, _ = ecran.verifier(captures_avec_indicateur(("NOIR", 2, 0, -1), ("DEMARRAGE", 1, 90, -1), ("DEMARRAGE", 2, 90, 0),
                                                              ("SOMBRE", 3, 0, -1)))
        self.assertEqual(erreurs, [])

    def test_sans_mesure_de_l_indicateur_rien_n_est_exige(self):
        erreurs, infos = ecran.verifier(captures(("NOIR", 2), ("DEMARRAGE", 8), ("SOMBRE", 3)))
        self.assertEqual(erreurs, [])
        self.assertFalse(any("indicateur" in info for info in infos))

    def test_lecture_du_tableau_avec_l_indicateur(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fichier:
            fichier.write("seconde;nature;noir;fond;clair;luminance;indicateur;mouvement\n"
                          "0;NOIR;1.000;0.000;0.000;0;0;-1\n3;DEMARRAGE;0.000;0.990;0.005;21;90;27\n")
        try:
            self.assertEqual(ecran.lire_tableau(fichier.name), [(0, "NOIR", 0, -1), (3, "DEMARRAGE", 90, 27)])
        finally:
            os.remove(fichier.name)

    def test_verifier_en_ligne_de_commande_refuse_un_indicateur_figé(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fichier:
            fichier.write("seconde;nature;noir;fond;clair;luminance;indicateur;mouvement\n")
            for seconde, code, clairs, changes in captures_avec_indicateur(("NOIR", 2, 0, -1), ("DEMARRAGE", 1, 90, -1),
                                                                          ("DEMARRAGE", 6, 90, 0), ("CLAIR", 3, 0, -1)):
                fichier.write(f"{seconde};{code};0;0;0;0;{clairs};{changes}\n")
        try:
            with contextlib.redirect_stdout(io.StringIO()) as sortie:
                self.assertEqual(ecran.main(["x", "verifier", fichier.name]), 1)
            self.assertIn("ne bouge pas", sortie.getvalue())
        finally:
            os.remove(fichier.name)


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
