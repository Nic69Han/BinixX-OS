"""Tests de la barre de titre « verre fumé » (build_files/verre_fenetres.py) et de sa pose (build_files/variantes-themes.py) : le fond
de la décoration de Win11OS KDE est recoloré, le masque de flou couvre la barre de titre et le cadre sans l'ombre, les côtés droits
(dessinés en miroir des gauches) ont leur masque en miroir aussi ; le thème Kvantum « verre » floute les fenêtres mais garde la liste
des fichiers opaque.

python3 -m unittest discover -s tests/themes
"""

import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(RACINE, "build_files"))
import verre_fenetres as F

SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}href"
AURORAE = os.path.join(RACINE, "system_files", "usr", "share", "aurorae", "themes")


def origine(teinte):
    with open(os.path.join(AURORAE, f"Win11OS-{teinte}", "decoration.svg"), encoding="utf-8") as fichier:
        return fichier.read()


def style(element):
    return dict(p.split(":", 1) for p in element.get("style", "").split(";") if ":" in p)


class Decoration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svg = {t: F.decoration_verre(origine(t), t) for t in ("dark", "light")}
        cls.racines = {t: ET.fromstring(s.split("\n", 2)[2]) for t, s in cls.svg.items()}

    def ids(self, teinte):
        return {e.get("id"): e for e in self.racines[teinte].iter() if e.get("id")}

    def test_fond_recolore_en_verre_fume(self):
        for teinte, (couleur, opacite) in F.VERRE.items():
            with self.subTest(teinte=teinte):
                self.assertNotIn(F.FOND_ORIGINE[teinte], self.svg[teinte].lower())
                fonds = [style(e) for e in self.racines[teinte].iter() if style(e).get("fill") == couleur]
                self.assertGreaterEqual(len(fonds), 2 * len(F.MORCEAUX))  # décoration et masque
                self.assertTrue(all("mix-blend-mode" not in s for s in fonds))
                decoration = [s for s in fonds if s.get("opacity") != "1"]
                self.assertTrue(decoration and all(float(s["opacity"]) == opacite for s in decoration))
                self.assertGreaterEqual(opacite, 0.8)  # lisible même sans flou

    def test_masque_de_flou_sans_l_ombre(self):
        for teinte in ("dark", "light"):
            ids = self.ids(teinte)
            for morceau in F.MORCEAUX:
                with self.subTest(teinte=teinte, morceau=morceau):
                    self.assertIn(f"decoration-{morceau}", ids)
                    self.assertIn(f"decoration-inactive-{morceau}", ids)
                    masque = ids[f"mask-{morceau}"]
                    if masque.tag == SVG + "use":
                        # côté droit : le masque du côté gauche en miroir, pas sa décoration
                        self.assertTrue(masque.get(XLINK).startswith("#mask-"), masque.get(XLINK))
                        continue
                    visibles = [style(e) for e in masque.iter() if e.tag in (SVG + "rect", SVG + "path") and style(e).get("opacity") != "0"]
                    self.assertTrue(visibles)
                    self.assertTrue(all(s.get("fill") == F.VERRE[teinte][0] and s.get("opacity") == "1" for s in visibles))

    def test_ids_uniques(self):
        for teinte, texte in self.svg.items():
            ids = re.findall(r'\bid="([^"]+)"', texte)
            self.assertEqual(len(ids), len(set(ids)), teinte)

    def test_un_dessin_d_origine_change_arrete_la_construction(self):
        with self.assertRaises(SystemExit):
            F.decoration_verre(origine("dark").replace('id="decoration-top"', 'id="autre"'), "dark")
        with self.assertRaises(SystemExit):
            F.decoration_verre(origine("dark").replace("#282828", "#303030"), "dark")
