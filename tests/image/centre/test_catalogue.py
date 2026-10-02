"""Tests du catalogue « Mon logiciel Windows » (sans Qt) : python3 -m unittest discover tests/image/centre"""

import os
import sys
import unittest

RACINE = os.environ.get("NICOS_CENTRE", os.path.join(os.path.dirname(__file__), "../../../system_files/usr/lib/nicos/centre"))
sys.path.insert(0, RACINE)
FICHIER = os.environ.get("NICOS_CATALOGUE", os.path.join(os.path.dirname(__file__),
                         "../../../system_files/usr/share/nicos/catalogue-windows/catalogue.tsv"))

from nicos_centre import catalogue  # noqa: E402


class Catalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrees = catalogue.charger(FICHIER)

    def noms(self, requete):
        return [e.windows for e in catalogue.chercher(self.entrees, requete)]

    def test_le_fichier_se_charge(self):
        self.assertGreater(len(self.entrees), 40)

    def test_chaque_categorie_a_plusieurs_entrees_ou_une_seule_voulue(self):
        self.assertIn("Bureautique", {e.categorie for e in self.entrees})

    def test_word_donne_onlyoffice(self):
        premier = catalogue.chercher(self.entrees, "word")[0]
        self.assertEqual(premier.windows, "Microsoft Word")
        self.assertEqual(premier.cible, "org.onlyoffice.desktopeditors")

    def test_recherche_sans_accent_ni_casse(self):
        self.assertIn("Microsoft Visio", self.noms("DIAGRAMME"))
        self.assertIn("Microsoft Publisher", self.noms("mise en page"))
        self.assertIn("Adobe Lightroom", self.noms("retouche"))

    def test_tous_les_mots_doivent_correspondre(self):
        self.assertEqual(self.noms("word zzzzzz"), [])

    def test_recherche_vide_renvoie_tout(self):
        self.assertEqual(len(catalogue.chercher(self.entrees, "")), len(self.entrees))

    def test_comptabilite_sans_equivalent(self):
        premier = catalogue.chercher(self.entrees, "sage")[0]
        self.assertEqual(premier.type, "windows")

    def test_adresses_web_en_https(self):
        for entree in self.entrees:
            if entree.type == "web":
                self.assertTrue(entree.cible.startswith("https://"), entree.windows)

    def test_pas_de_doublon(self):
        noms = [e.windows for e in self.entrees]
        self.assertEqual(len(noms), len(set(noms)))

    def test_chaque_categorie_a_son_pictogramme(self):
        from nicos_centre import icones
        for categorie in {e.categorie for e in self.entrees}:
            self.assertIn(categorie, catalogue.ICONES_CATEGORIES, categorie)
        for icone in catalogue.ICONES_CATEGORIES.values():
            self.assertIn(icone, icones.ICONES)
        self.assertEqual(catalogue.icone_de("Inconnue"), "package")

    def test_les_applications_fournies_sont_au_catalogue(self):
        cibles = {e.cible for e in self.entrees if e.type == "flatpak"}
        for identifiant in ("org.onlyoffice.desktopeditors", "org.mozilla.thunderbird_esr", "org.kde.okular"):
            self.assertIn(identifiant, cibles)


class Fichiers(unittest.TestCase):
    def test_noms_de_programmes(self):
        cas = {
            "/home/a/Téléchargements/Setup_Sage100_v2023.exe": "Sage",
            "ebp-compta-2024.msi": "ebp compta",
            "AcroRdrDC2300820360_fr_FR.exe": "AcroRdrDC",
            "7z2301-x64.exe": "",
            "TeamViewer_Setup.exe": "TeamViewer",
            "Photoshop_Set-Up.exe": "Photoshop",
        }
        for chemin, attendu in cas.items():
            self.assertEqual(catalogue.deviner_programme(chemin), attendu, chemin)

    def test_fichier_qui_ne_se_nomme_pas_comme_le_catalogue(self):
        entrees = catalogue.charger(FICHIER)
        requete, resultats = catalogue.chercher_fichier(entrees, "/tmp/AcroRdrDC2300820360_fr_FR.exe")
        self.assertEqual(requete, "acro")
        self.assertIn("Adobe Acrobat Reader", [r.windows for r in resultats])
        self.assertEqual(catalogue.chercher_fichier(entrees, "/tmp/7z2301-x64.exe"), ("", []))
        requete, resultats = catalogue.chercher_fichier(entrees, "/tmp/TeamViewer_Setup.exe")
        self.assertEqual(resultats[0].windows, "TeamViewer")

    def test_ligne_mal_formee(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8") as f:
            f.write("a\tb\tc\n")
        try:
            with self.assertRaises(ValueError):
                catalogue.charger(f.name)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
