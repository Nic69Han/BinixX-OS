"""Tests des icônes d'applications BinixX (binixx_centre/plaques.py) : logo trouvé dans les thèmes, fond reconnu (carré ou rond plein)
ou verre teinté, squircle commun, version Nuit plus profonde, index.theme, et dans la session seules les applications nouvelles.

python3 -m unittest discover -s tests/image/centre -p 'test_plaques.py'   (ignoré sans PySide6)
"""

import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
LOGOS = os.path.join(ICI, "logos-exemple")
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtSvg import QSvgRenderer  # noqa: F401
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

from binixx_centre import plaques as P  # noqa: E402


class SansQt(unittest.TestCase):
    def test_applications_et_logos(self):
        dossier = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dossier, True)
        apps = os.path.join(dossier, "applications")
        os.makedirs(apps)
        for nom, contenu in (("visible", "Icon=video\nName=Vidéo\n"), ("cachee", "Icon=cache\nNoDisplay=true\n"),
                             ("chemin", "Icon=/opt/app/logo.png\n"), ("sans", "Name=Rien\n")):
            with open(os.path.join(apps, f"{nom}.desktop"), "w") as f:
                f.write("[Desktop Entry]\nType=Application\n" + contenu)
        self.assertEqual(P.applications((apps,)), {"video": "Vidéo"})
        # le dessin vectoriel passe avant la plus grande image
        icones = os.path.join(dossier, "icons")
        for chemin in ("hicolor/48x48/apps/video.png", "hicolor/256x256/apps/video.png", "hicolor/scalable/apps/video.svg",
                       "breeze/actions/24/video.svg", "hicolor/symbolic/apps/video-symbolic.svg"):
            os.makedirs(os.path.dirname(os.path.join(icones, chemin)), exist_ok=True)
            open(os.path.join(icones, chemin), "w").close()
        self.assertTrue(P.trouver_logo("video", (icones,)).endswith("hicolor/scalable/apps/video.svg"))
        os.remove(os.path.join(icones, "hicolor/scalable/apps/video.svg"))
        self.assertTrue(P.trouver_logo("video", (icones,)).endswith("256x256/apps/video.png"))
        self.assertIsNone(P.trouver_logo("absente", (icones,)))


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Plaques(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dossier, True)
        self.icones = os.path.join(self.dossier, "icons", "hicolor", "scalable", "apps")
        os.makedirs(self.icones)
        for nom in ("carre-plein", "rond-plein", "sans-fond"):
            shutil.copy(os.path.join(LOGOS, f"{nom}.svg"), self.icones)
        self.sortie = os.path.join(self.dossier, "sortie")

    def test_fond_reconnu(self):
        carre = P.analyser(P.rendre(os.path.join(self.icones, "carre-plein.svg"), P.TAILLE_ANALYSE))
        self.assertTrue(carre["fond"])
        self.assertEqual(carre["couleur_fond"], "#4a92fd")
        rond = P.analyser(P.rendre(os.path.join(self.icones, "rond-plein.svg"), P.TAILLE_ANALYSE))
        self.assertTrue(rond["fond"])
        self.assertEqual(rond["couleur_fond"][:2], "#2")  # le vert du disque (#21d461), pas le noir des traits
        sans = P.analyser(P.rendre(os.path.join(self.icones, "sans-fond.svg"), P.TAILLE_ANALYSE))
        self.assertFalse(sans["fond"])
        self.assertEqual(sans["dominante"][:3], "#fe")

    def test_icones_ecrites_dans_les_deux_themes(self):
        apps = {"carre-plein": "A", "rond-plein": "B", "sans-fond": "C", "absente": "D"}
        ecrites, sans_logo = P.fabriquer(self.sortie, apps, (os.path.join(self.dossier, "icons"),))
        self.assertEqual(sorted(ecrites), ["carre-plein", "rond-plein", "sans-fond"])
        self.assertEqual(sans_logo, ["absente"])
        for theme in (P.NOM, P.NOM_SOMBRE):
            for nom in ecrites:
                chemin = os.path.join(self.sortie, theme, P.REPERTOIRE, f"{nom}.svg")
                with open(chemin, encoding="utf-8") as f:
                    texte = f.read()
                ET.fromstring(texte)
                self.assertIn(P.MARQUE, texte)
                self.assertIn(P.SQUIRCLE, texte)
                self.assertIn("data:image/png;base64,", texte)
                self.assertTrue(QSvgRenderer(chemin).isValid())
            with open(os.path.join(self.sortie, theme, "index.theme"), encoding="utf-8") as f:
                index = f.read()
            self.assertIn("Directories=apps/scalable", index)
            self.assertIn("Type=Scalable", index)
        # fond repris (carré), verre teinté (sans fond), plus profond en Nuit
        with open(os.path.join(self.sortie, P.NOM, P.REPERTOIRE, "carre-plein.svg")) as f:
            self.assertIn('fill="#4a92fd"', f.read())
        with open(os.path.join(self.sortie, P.NOM_SOMBRE, P.REPERTOIRE, "carre-plein.svg")) as f:
            self.assertNotIn('fill="#4a92fd"', f.read())
        with open(os.path.join(self.sortie, P.NOM, P.REPERTOIRE, "sans-fond.svg")) as f:
            texte = f.read()
        self.assertIn("fill-opacity=", texte)
        self.assertIn('id="reflet"', texte)

    def test_index_existant_complete(self):
        os.makedirs(os.path.join(self.sortie, P.NOM))
        with open(os.path.join(self.sortie, P.NOM, "index.theme"), "w") as f:
            f.write("[Icon Theme]\nName=BinixX OS\nInherits=breeze\nDirectories=places/64\n\n[places/64]\nSize=64\nType=Fixed\n")
        P.fabriquer(self.sortie, {"sans-fond": "C"}, (os.path.join(self.dossier, "icons"),))
        with open(os.path.join(self.sortie, P.NOM, "index.theme")) as f:
            index = f.read()
        self.assertIn("Directories=places/64,apps/scalable", index)
        self.assertIn("[places/64]", index)


if __name__ == "__main__":
    unittest.main()
