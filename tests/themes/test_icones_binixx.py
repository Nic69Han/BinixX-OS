"""Tests des dossiers de BinixX OS (build_files/icones-binixx.py) sur des extraits de Breeze (tests/themes/breeze-exemple) : forme
redessinée, couleur selon le contenu, pictogramme de Breeze gardé et recoloré, tons plus profonds en Nuit, petites tailles sans
pictogramme, liens de Breeze refaits, construction arrêtée si le dessin de Breeze change.

python3 -m unittest discover -s tests/themes
"""

import importlib.util
import os
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

ICI = os.path.dirname(os.path.abspath(__file__))
EXEMPLE = os.path.join(ICI, "breeze-exemple")
spec = importlib.util.spec_from_file_location("icones_binixx", os.path.join(ICI, "..", "..", "build_files", "icones-binixx.py"))
I = importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)


def lire(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return fichier.read()


class Dossiers(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dossier, True)
        self.nombre, self.liens = I.fabriquer(self.dossier, EXEMPLE, minimum=1)
        self.clair = os.path.join(self.dossier, I.NOM)
        self.sombre = os.path.join(self.dossier, I.NOM_SOMBRE)

    def test_tous_les_dossiers_sont_redessines(self):
        self.assertEqual(self.nombre, 8)  # 5 en 64, 2 en 32, 1 en 16
        for theme in (self.clair, self.sombre):
            for racine, _, fichiers in os.walk(os.path.join(theme, "places")):
                for nom in fichiers:
                    texte = lire(os.path.join(racine, nom))
                    ET.fromstring(texte)  # SVG valide
                    self.assertIn("build_files/icones-binixx.py", texte)
                    self.assertNotIn("current-color-scheme", texte)
                    self.assertNotIn("currentColor", texte)
                    self.assertNotIn("ColorScheme-", texte)

    def test_couleur_selon_le_contenu(self):
        attendus = {"folder": "jaune", "folder-documents": "bleu", "folder-pictures": "vert", "folder-blue": "bleu", "folder-git": "jaune"}
        for nom, couleur in attendus.items():
            with self.subTest(nom=nom):
                self.assertIn(f'fill="{I.COULEURS[couleur][0]}"', lire(os.path.join(self.clair, "places/64", nom + ".svg")))
                self.assertIn(f'fill="{I.COULEURS[couleur][1]}"', lire(os.path.join(self.sombre, "places/64", nom + ".svg")))
        self.assertEqual(I.couleur_de("folder-music.svg"), "rose")
        self.assertEqual(I.couleur_de("folder-download.svg"), "orange")
        self.assertEqual(I.couleur_de("folder-magenta.svg"), "rose")
        self.assertEqual(I.couleur_de("folder-inconnu.svg"), "jaune")

    def test_pictogramme_de_breeze_garde(self):
        breeze = lire(os.path.join(EXEMPLE, "places/64/folder-documents.svg"))
        picto_breeze = re.findall(r'\bd="([^"]*)"', breeze)[4:]
        binixx = lire(os.path.join(self.clair, "places/64/folder-documents.svg"))
        for d in picto_breeze:
            self.assertIn(d, binixx)
        # le dossier simple n'a que la forme BinixX (onglet, face, reflet)
        self.assertEqual(lire(os.path.join(self.clair, "places/64/folder.svg")).count("<path"), 2)
        # pictogramme d'une nuance foncée de la couleur en Aube, claire en Nuit
        _, _, picto_clair = I.nuances("bleu", False)
        _, _, picto_sombre = I.nuances("bleu", True)
        self.assertIn(f"fill:{picto_clair}", binixx)
        self.assertIn(f"fill:{picto_sombre}", lire(os.path.join(self.sombre, "places/64/folder-documents.svg")))

    def test_mise_a_l_echelle_et_petites_tailles(self):
        self.assertIn('viewBox="0 0 32 32"', lire(os.path.join(self.clair, "places/32/folder.svg")))
        self.assertIn("scale(0.5)", lire(os.path.join(self.clair, "places/32/folder.svg")))
        petit = lire(os.path.join(self.clair, "places/16/folder.svg"))
        self.assertIn('viewBox="0 0 16 16"', petit)
        self.assertEqual(petit.count("<path"), 2)  # sans pictogramme

    def test_liens_et_themes(self):
        self.assertEqual(self.liens, 1)
        for theme in (self.clair, self.sombre):
            lien = os.path.join(theme, "mimetypes/64/inode-directory.svg")
            self.assertEqual(os.path.realpath(lien), os.path.realpath(os.path.join(theme, "places/64/folder.svg")))
        self.assertIn("Inherits=breeze\n", lire(os.path.join(self.clair, "index.theme")))
        self.assertIn("Inherits=breeze-dark\n", lire(os.path.join(self.sombre, "index.theme")))
        self.assertIn("places/64", lire(os.path.join(self.clair, "index.theme")))
        self.assertTrue(os.path.isfile(os.path.join(self.clair, "LISEZMOI.txt")))

    def test_dessin_de_breeze_change(self):
        autre = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, autre, True)
        shutil.copytree(EXEMPLE, os.path.join(autre, "breeze"), symlinks=True)
        chemin = os.path.join(autre, "breeze/places/64/folder.svg")
        texte = lire(chemin)
        with open(chemin, "w", encoding="utf-8") as fichier:
            fichier.write(texte.replace('class="ColorScheme-Accent"', 'class="Autre"'))
        with self.assertRaises(SystemExit):
            I.fabriquer(autre, os.path.join(autre, "breeze"), minimum=1)


if __name__ == "__main__":
    unittest.main()
