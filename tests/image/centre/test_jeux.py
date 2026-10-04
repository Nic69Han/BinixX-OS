"""Tests de la page Jeux : entrées du catalogue, état des boutiques, cartes graphiques.

python3 -m unittest discover -s tests/image/centre -p 'test_jeux.py'   (la partie Qt est ignorée sans PySide6)
"""

import os
import sys
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
FICHIER = os.environ.get("BINIXX_CATALOGUE", os.path.join(
    ICI, "../../../system_files/usr/share/binixx/catalogue-windows/catalogue.tsv"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import catalogue, launch, materiel  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

# Identifiants vérifiés sur Flathub le 2 octobre 2026 (tests/centre/verifier_flathub.py les revérifie en ligne)
ATTENDUS = {"com.valvesoftware.Steam", "com.heroicgameslauncher.hgl", "net.lutris.Lutris",
            "org.prismlauncher.PrismLauncher", "net.davidotek.pupgui2"}

SWITCHEROO = """Device: 0
  Name:        Intel Corporation HD Graphics 630
  Default:     yes
  Discrete:    no
  Environment: DRI_PRIME=pci-0000_00_02_0

Device: 1
  Name:        NVIDIA Corporation GP107M [GeForce GTX 1050 Ti Mobile]
  Default:     no
  Discrete:    yes
  Environment: DRI_PRIME=pci-0000_01_00_0
"""

LSPCI = '''00:00.0 "Host bridge" "Intel Corporation" "Device 3e0f" -r08 "Dell" "Device 0875"
00:02.0 "VGA compatible controller" "Intel Corporation" "UHD Graphics 630" -r02 "Dell" "Device 0875"
01:00.0 "3D controller" "NVIDIA Corporation" "GP107M [GeForce GTX 1050 Ti Mobile]" -ra1 "Dell" "Device 0875"
02:00.0 "Ethernet controller" "Realtek" "RTL8111" -r15
'''


class Catalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrees = catalogue.charger(FICHIER)
        cls.jeux = catalogue.remplacants(cls.entrees, "Jeux")

    def test_les_boutiques_attendues_sont_proposees(self):
        cibles = {r.entree.cible for r in self.jeux if r.entree.type == "flatpak"}
        self.assertEqual(cibles, ATTENDUS)

    def test_une_application_pour_plusieurs_logiciels_windows(self):
        heroic = next(r for r in self.jeux if r.entree.cible == "com.heroicgameslauncher.hgl")
        self.assertEqual(heroic.remplace, ("Epic Games Store", "GOG Galaxy"))
        self.assertEqual(len({r.entree.cible for r in self.jeux}), len(self.jeux))  # un seul bloc par application

    def test_les_services_en_ligne_sont_en_https(self):
        en_ligne = [r.entree for r in self.jeux if r.entree.type == "web"]
        self.assertEqual(len(en_ligne), 2)
        self.assertTrue(all(e.cible.startswith("https://") for e in en_ligne))

    def test_chaque_entree_explique_ses_limites(self):
        for entree in self.entrees:
            if entree.categorie == "Jeux":
                self.assertTrue(entree.remarque, entree.windows)

    def test_recherche_par_nom_de_boutique(self):
        for requete, attendu in (("epic", "com.heroicgameslauncher.hgl"), ("battle net", "net.lutris.Lutris"),
                                 ("minecraft", "org.prismlauncher.PrismLauncher"), ("steam", "com.valvesoftware.Steam")):
            premier = catalogue.chercher(self.entrees, requete)[0]
            self.assertEqual(premier.cible, attendu, requete)

    def test_etat_selon_l_installation(self):
        steam = next(e for e in self.entrees if e.cible == "com.valvesoftware.Steam")
        self.assertEqual(catalogue.etat(steam, set(), set()),
                         ("À installer depuis Flathub", "Installer", ("discover", "com.valvesoftware.Steam")))
        self.assertEqual(catalogue.etat(steam, {"com.valvesoftware.Steam"}, set()),
                         ("Installé", "Ouvrir", ("flatpak", "com.valvesoftware.Steam")))
        self.assertEqual(catalogue.etat(steam, set(), {"com.valvesoftware.Steam"})[1], "Installer maintenant")
        site = next(e for e in self.entrees if e.type == "web" and e.categorie == "Jeux")
        self.assertEqual(catalogue.etat(site, set(), set())[2], ("url", site.cible))


class Lancement(unittest.TestCase):
    def test_executer_n_utilise_jamais_de_shell(self):
        appels = []
        ancien = launch._start
        launch._start = lambda argv: appels.append(argv) or True
        try:
            launch.executer(("discover", "net.lutris.Lutris"))
            launch.executer(("flatpak", "net.lutris.Lutris"))
            launch.executer(("url", "https://www.protondb.com/"))
            self.assertFalse(launch.executer(("url", "file:///etc/passwd")))
        finally:
            launch._start = ancien
        self.assertEqual(appels, [[launch.INSTALLATEUR, "net.lutris.Lutris"],
                                  ["flatpak", "run", "net.lutris.Lutris"],
                                  ["xdg-open", "https://www.protondb.com/"]])

    def test_genre_inconnu(self):
        with self.assertRaises(KeyError):
            launch.executer(("shell", "rm -rf /"))


class Materiel(unittest.TestCase):
    def test_switcheroo(self):
        cartes = materiel.analyser_switcheroo(SWITCHEROO)
        self.assertEqual([c["nom"] for c in cartes], ["Intel Corporation HD Graphics 630",
                                                       "NVIDIA Corporation GP107M [GeForce GTX 1050 Ti Mobile]"])
        self.assertEqual([c["defaut"] for c in cartes], [True, False])
        self.assertEqual([c["dedie"] for c in cartes], [False, True])

    def test_lspci_ne_garde_que_les_cartes_graphiques(self):
        cartes = materiel.analyser_lspci(LSPCI)
        self.assertEqual([c["nom"] for c in cartes], ["Intel Corporation UHD Graphics 630",
                                                       "NVIDIA Corporation GP107M [GeForce GTX 1050 Ti Mobile]"])

    def test_sorties_vides_ou_incorrectes(self):
        self.assertEqual(materiel.analyser_switcheroo(""), [])
        self.assertEqual(materiel.analyser_lspci('01:00.0 "VGA compatible controller" "guillemet non fermé'), [])

    def test_aucun_programme_n_a_besoin_d_etre_installe(self):
        ancien = materiel._lancer
        materiel._lancer = lambda argv: ""
        try:
            self.assertEqual(materiel.cartes_graphiques(), ([], False))
        finally:
            materiel._lancer = ancien


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from binixx_centre import theme
        from binixx_centre.pages import jeux
        cls.jeux = jeux
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        os.environ["BINIXX_CATALOGUE"] = FICHIER
        self.anciens = (launch.installed_flatpaks, launch._start, materiel.cartes_graphiques, catalogue.fournies)
        launch.installed_flatpaks = lambda: {"net.lutris.Lutris"}
        catalogue.fournies = lambda listes=None: set()
        self.lances = []
        launch._start = lambda argv: self.lances.append(argv) or True
        materiel.cartes_graphiques = lambda: (materiel.analyser_switcheroo(SWITCHEROO), True)

    def tearDown(self):
        launch.installed_flatpaks, launch._start, materiel.cartes_graphiques, catalogue.fournies = self.anciens
        os.environ.pop("BINIXX_CATALOGUE", None)

    def test_une_carte_par_application_et_les_boutons_agissent(self):
        page = self.jeux.build(None)
        self.assertEqual(len(page.cartes), 7)  # 5 applications Flatpak et 2 services en ligne
        boutons = {c.bouton.text() for c in page.cartes}
        self.assertEqual(boutons, {"Installer", "Ouvrir", "Ouvrir le site"})
        steam = page.cartes[0]  # première entrée « Jeux » du catalogue
        steam.bouton.click()
        self.assertEqual(self.lances[-1], [launch.INSTALLATEUR, "com.valvesoftware.Steam"])
        installe = next(c for c in page.cartes if c.bouton.text() == "Ouvrir")
        installe.bouton.click()
        self.assertEqual(self.lances[-1], ["flatpak", "run", "net.lutris.Lutris"])
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            page.resize(1040, 1100)
            page.show()
            self.app.processEvents()
            page.grab().save(os.path.join(CAPTURES, "jeux.png"))

    def test_deux_cartes_graphiques_dont_une_nvidia(self):
        texte = self.jeux.texte_cartes(*materiel.cartes_graphiques(), variante="")
        self.assertIn("Intel Corporation HD Graphics 630", texte)
        self.assertIn("carte graphique dédiée", texte)
        self.assertIn("variante NVIDIA", texte)

    def test_la_variante_nvidia_n_a_pas_de_conseil_de_plus(self):
        cartes, via = materiel.cartes_graphiques()
        self.assertNotIn("variante NVIDIA", self.jeux.texte_cartes(cartes, via, variante="nvidia"))

    def test_une_seule_carte_ou_aucune(self):
        une = [{"nom": "AMD Radeon RX 6600", "defaut": True, "dedie": True}]
        self.assertEqual(self.jeux.texte_cartes(une, True), "Carte graphique : AMD Radeon RX 6600.")
        self.assertIn("n'a pas pu être identifiée", self.jeux.texte_cartes([], False))
        # sans switcheroo-control, on ne promet pas une action de clic droit qui n'existerait pas
        deux = materiel.analyser_lspci(LSPCI)
        self.assertNotIn("clic droit", self.jeux.texte_cartes(deux, False))


if __name__ == "__main__":
    unittest.main()
