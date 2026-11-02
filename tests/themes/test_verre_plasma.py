"""Tests du verre fumé de BinixX OS (build_files/verre_plasma.py) et de sa pose dans les thèmes Plasma Aube et Nuit
(build_files/variantes-themes.py) : chaque fond a ses neuf morceaux, ses marges et son ombre, aux bonnes tailles ; le verre est
translucide et sa version sans flou opaque ; la variante BinixX-Win11-* les lit à la place des fonds d'origine, sans « .svgz » qui les
cacherait.

python3 -m unittest discover -s tests/themes
"""

import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(RACINE, "build_files"))
import verre_plasma as V

try:
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer
    AVEC_QTSVG = True
except ImportError:
    AVEC_QTSVG = False

SVG = "{http://www.w3.org/2000/svg}"
MORCEAUX = ("topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright")


def elements(texte):
    """{id: élément} d'une image SVG ; échoue si un id est en double."""
    racine = ET.fromstring(texte)
    trouves = {}
    for element in racine.iter():
        ident = element.get("id")
        if ident:
            assert ident not in trouves, f"id en double : {ident}"
            trouves[ident] = element
    return trouves


def taille(element):
    """Largeur et hauteur d'un rectangle, ou du rectangle qui donne sa boîte à un groupe."""
    if element.tag == SVG + "g":
        element = element.find(SVG + "rect")
    return float(element.get("width")), float(element.get("height"))


class Fonds(unittest.TestCase):
    def test_neuf_morceaux_marges_et_ombre(self):
        for teinte, matieres in V.MATIERES.items():
            for nom_matiere, matiere in matieres.items():
                for fond, forme in V.FONDS.items():
                    with self.subTest(teinte=teinte, matiere=nom_matiere, fond=fond):
                        ids = elements(V.svg(forme, matiere))
                        for morceau in MORCEAUX:
                            self.assertIn(morceau, ids)
                            self.assertIn("shadow-" + morceau, ids)
                        r, c, k = forme.rayon, V.CENTRE, forme.ombre + forme.rayon
                        for coin in ("topleft", "topright", "bottomleft", "bottomright"):
                            self.assertEqual(taille(ids[coin]), (r, r))
                            self.assertEqual(taille(ids["shadow-" + coin]), (k, k))
                        self.assertEqual(taille(ids["top"]), (c, r))
                        self.assertEqual(taille(ids["left"]), (r, c))
                        self.assertEqual(taille(ids["center"]), (c, c))
                        haut, droite, bas, gauche = forme.marges
                        self.assertEqual(taille(ids["hint-top-margin"])[1], haut)
                        self.assertEqual(taille(ids["hint-right-margin"])[0], droite)
                        self.assertEqual(taille(ids["hint-bottom-margin"])[1], bas)
                        self.assertEqual(taille(ids["hint-left-margin"])[0], gauche)
                        self.assertEqual(taille(ids["shadow-hint-top-margin"])[1], forme.ombre)
                        self.assertEqual(taille(ids["shadow-hint-left-margin"])[0], forme.ombre)
                        self.assertEqual(taille(ids["shadow-top"])[1], forme.ombre)

    def test_verre_translucide_opaque_plein(self):
        for teinte, matieres in V.MATIERES.items():
            with self.subTest(teinte=teinte):
                self.assertLess(matieres["verre"].opacite, 0.8)
                self.assertGreater(matieres["verre"].opacite, 0.4)  # lisible même si le flou est faible
                self.assertEqual(matieres["opaque"].opacite, 1.0)
                for nom_matiere, matiere in matieres.items():
                    centre = elements(V.svg(V.FONDS["dialogs/background"], matiere))["center"]
                    self.assertEqual(float(centre.get("fill-opacity")), matiere.opacite, nom_matiere)
                    self.assertEqual(centre.get("fill"), matiere.fond)

    def test_barre_en_pilule(self):
        # la barre (≈ 46 px de haut à l'échelle 100 %) : des coins de presque la moitié de sa hauteur, sans dépasser
        forme = V.FONDS["widgets/panel-background"]
        self.assertGreaterEqual(forme.rayon, 18)
        self.assertLessEqual(2 * forme.rayon, 44)
        # le contenu ne déborde pas dans l'arrondi : marge gauche et droite assez grandes
        self.assertGreaterEqual(forme.marges[1], forme.rayon // 2)
        self.assertGreaterEqual(forme.marges[3], forme.rayon // 2)

    def test_aucun_trait_qui_deborderait_des_morceaux(self):
        # un trait (stroke) déborde de sa forme d'une demi-épaisseur : le morceau grandit et Plasma laisse un raccord visible
        for teinte, matieres in V.MATIERES.items():
            for matiere in matieres.values():
                for fond, forme in V.FONDS.items():
                    self.assertNotIn("stroke", V.svg(forme, matiere), (teinte, fond))

    @unittest.skipUnless(AVEC_QTSVG, "PySide6 (QtSvg) absent")
    def test_morceaux_aux_tailles_exactes_pour_qt(self):
        # Plasma (KSvg) prend la taille de chaque morceau dans QSvgRenderer.boundsOnElement : elle doit tomber juste, au pixel
        for teinte, matieres in V.MATIERES.items():
            for matiere in matieres.values():
                for fond, forme in V.FONDS.items():
                    rendu = QSvgRenderer(QByteArray(V.svg(forme, matiere).encode()))
                    r, c, k = forme.rayon, V.CENTRE, forme.ombre + forme.rayon
                    attendu = {"topleft": (r, r), "top": (c, r), "topright": (r, r), "left": (r, c), "center": (c, c), "right": (r, c),
                               "bottomleft": (r, r), "bottom": (c, r), "bottomright": (r, r)}
                    attendu.update({f"shadow-{coin}": (k, k) for coin in ("topleft", "topright", "bottomleft", "bottomright")})
                    for morceau, (largeur, hauteur) in attendu.items():
                        with self.subTest(teinte=teinte, fond=fond, morceau=morceau):
                            boite = rendu.boundsOnElement(morceau)
                            self.assertAlmostEqual(boite.width(), largeur, places=3)
                            self.assertAlmostEqual(boite.height(), hauteur, places=3)

    def test_meme_image_a_chaque_fois(self):
        forme, matiere = V.FONDS["widgets/tooltip"], V.MATIERES["dark"]["verre"]
        self.assertEqual(V.svg(forme, matiere), V.svg(forme, matiere))


def charger_variantes():
    spec = importlib.util.spec_from_file_location("variantes_themes", os.path.join(RACINE, "build_files", "variantes-themes.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Pose(unittest.TestCase):
    """variantes-themes.py sur une copie des thèmes Win11OS du dépôt, et un faux Breeze."""

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        share = os.path.join(RACINE, "system_files", "usr", "share")
        shutil.copytree(os.path.join(share, "Kvantum"), os.path.join(self.dossier, "Kvantum"), symlinks=True)
        shutil.copytree(os.path.join(share, "aurorae"), os.path.join(self.dossier, "aurorae"), symlinks=True)
        themes = os.path.join(self.dossier, "plasma", "desktoptheme")
        for variante in ("light", "dark"):
            shutil.copytree(os.path.join(share, "plasma", "desktoptheme", f"Win11OS-{variante}"),
                            os.path.join(themes, f"Win11OS-{variante}"), symlinks=True)
        breeze = os.path.join(themes, "default")
        for fond in ("dialogs/background", "widgets/background", "widgets/panel-background", "widgets/tooltip", "widgets/tasks"):
            for dossier in ("", "solid", "translucent"):
                if fond.endswith("tasks") and dossier:
                    continue
                chemin = os.path.join(breeze, dossier, fond + ".svgz")
                os.makedirs(os.path.dirname(chemin), exist_ok=True)
                open(chemin, "w").close()
        with open(os.path.join(breeze, "metadata.json"), "w") as fichier:
            json.dump({"KPlugin": {"Id": "default", "Name": "Breeze"}}, fichier)
        with open(os.path.join(breeze, "plasmarc"), "w") as fichier:
            fichier.write("[Wallpaper]\ndefaultWallpaperTheme=Next\n")
        charger_variantes().fabriquer(self.dossier)
        self.themes = themes

    def tearDown(self):
        shutil.rmtree(self.dossier)

    def test_verre_pose_dans_aube_et_nuit(self):
        for variante in ("light", "dark"):
            aval = os.path.join(self.themes, f"BinixX-Win11-{variante}")
            amont = os.path.join(self.themes, f"Win11OS-{variante}")
            self.assertFalse(os.path.islink(os.path.join(aval, "translucent")))
            for fond in V.FONDS:
                for dossier, matiere in ((aval, "opaque"), (os.path.join(aval, "translucent"), "verre")):
                    with self.subTest(variante=variante, fond=fond, matiere=matiere):
                        nom = os.path.basename(fond)
                        voisins = [f for f in os.listdir(os.path.join(dossier, os.path.dirname(fond))) if re.fullmatch(rf"{nom}\.svgz?", f)]
                        self.assertEqual(voisins, [nom + ".svg"])  # pas de « .svgz » qui cacherait le fond
                        chemin = os.path.join(dossier, fond + ".svg")
                        self.assertFalse(os.path.islink(chemin))
                        with open(chemin, encoding="utf-8") as fichier:
                            texte = fichier.read()
                        self.assertEqual(texte, V.svg(V.FONDS[fond], V.MATIERES[variante][matiere]))
            # le reste vient du thème d'origine
            self.assertEqual(os.path.realpath(os.path.join(aval, "translucent", "widgets", "background.svg")),
                             os.path.realpath(os.path.join(amont, "translucent", "widgets", "background.svg")))
            self.assertEqual(os.path.realpath(os.path.join(aval, "solid")), os.path.realpath(os.path.join(amont, "solid")))
            self.assertEqual(os.path.realpath(os.path.join(aval, "widgets", "tasks.svgz")),
                             os.path.realpath(os.path.join(amont, "widgets", "tasks.svgz")))

    def test_fenetres_en_verre(self):
        for variante in ("light", "dark"):
            with self.subTest(variante=variante):
                kvantum = os.path.join(self.dossier, "Kvantum", f"BinixX-Win11-{variante}-verre", f"BinixX-Win11-{variante}-verre.kvconfig")
                with open(kvantum, encoding="utf-8") as fichier:
                    texte = fichier.read()
                for cle in ("translucent_windows", "blurring", "popup_blurring"):
                    self.assertRegex(texte, rf"(?m)^{cle}=true$")
                for cle in ("transparent_dolphin_view", "transparent_pcmanfm_view"):
                    self.assertRegex(texte, rf"(?m)^{cle}=false$")
                aurorae = os.path.join(self.dossier, "aurorae", "themes", f"BinixX-Verre-{variante}")
                self.assertTrue(os.path.isfile(os.path.join(aurorae, f"BinixX-Verre-{variante}rc")))
                self.assertFalse(os.path.islink(os.path.join(aurorae, "decoration.svg")))
                self.assertTrue(os.path.islink(os.path.join(aurorae, "close.svg")))
                self.assertTrue(os.path.exists(os.path.join(aurorae, "close.svg")))
                with open(os.path.join(aurorae, "metadata.desktop"), encoding="utf-8") as fichier:
                    self.assertIn(f"X-KDE-PluginInfo-Name=BinixX-Verre-{variante}", fichier.read())

    def test_contraste_sans_verre(self):
        contraste = os.path.join(self.themes, "BinixX-contraste")
        for fond in V.FONDS:
            with self.subTest(fond=fond):
                self.assertFalse(os.path.exists(os.path.join(contraste, fond + ".svg")))
                self.assertFalse(os.path.exists(os.path.join(contraste, "translucent", fond + ".svg")))


if __name__ == "__main__":
    unittest.main()
