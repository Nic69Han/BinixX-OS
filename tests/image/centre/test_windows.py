"""Tests de la page « Windows complet » : prérequis du PC, options proposées, entrées du catalogue.

python3 -m unittest discover -s tests/image/centre -p 'test_windows.py'   (la partie Qt est ignorée sans PySide6)
"""

import os
import sys
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("NICOS_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/nicos/centre"))
FICHIER = os.environ.get("NICOS_CATALOGUE", os.path.join(
    ICI, "../../../system_files/usr/share/nicos/catalogue-windows/catalogue.tsv"))
CAPTURES = os.environ.get("NICOS_CAPTURES")
sys.path.insert(0, RACINE)

from nicos_centre import catalogue, launch, virtualisation as v  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

INTEL = "processor\t: 0\nflags\t\t: fpu vme de pse tsc msr pae mce cx8 apic vmx ssse3\n\nprocessor\t: 1\nflags\t\t: fpu vmx\n"
AMD = "processor : 0\nflags : fpu svm nx\nprocessor : 1\nflags : fpu svm nx\nprocessor : 2\nflags : fpu\nprocessor : 3\nflags : fpu\n"
SANS = "processor : 0\nflags : fpu vme de pse tsc msr pae mce cx8 apic\n"


class Prerequis(unittest.TestCase):
    def test_le_processeur_annonce_la_virtualisation(self):
        self.assertTrue(v.processeur_sait_virtualiser(INTEL))
        self.assertTrue(v.processeur_sait_virtualiser(AMD))
        self.assertFalse(v.processeur_sait_virtualiser(SANS))
        self.assertFalse(v.processeur_sait_virtualiser("model name : un processeur avec vmx dans le nom\n"))

    def test_nombre_de_fils(self):
        self.assertEqual(v.nombre_de_fils(INTEL), 2)
        self.assertEqual(v.nombre_de_fils(AMD), 4)
        self.assertEqual(v.nombre_de_fils(""), 0)

    def test_virtualisation_trois_cas(self):
        self.assertEqual(v.virtualisation(INTEL, True).etat, v.OK)
        coupee = v.virtualisation(INTEL, False)
        self.assertEqual(coupee.etat, v.KO)
        self.assertIn("BIOS", coupee.detail)
        self.assertIn("VT-x", coupee.detail)
        self.assertEqual(v.virtualisation(SANS, False).etat, v.KO)

    def test_un_pc_de_8_go_est_juge_suffisant(self):
        # 8 Go annoncés donnent un peu moins dans /proc/meminfo
        self.assertEqual(v.memoire(v.memoire_go("MemTotal:        7861024 kB\n")).etat, v.OK)
        self.assertEqual(v.memoire(v.memoire_go("MemTotal:        3900000 kB\n")).etat, v.ATTENTION)
        self.assertEqual(v.memoire(v.memoire_go("MemTotal:        2000000 kB\n")).etat, v.KO)
        self.assertEqual(v.memoire(v.memoire_go("")).etat, v.KO)
        self.assertEqual(v.memoire(16).titre, "Mémoire : 16 Go")
        # ce que voit le système est un peu en dessous de ce qui est écrit sur la boîte
        self.assertEqual(v.memoire(v.memoire_go("MemTotal: 16000000 kB\n")).titre, "Mémoire : 16 Go")
        self.assertEqual(v.memoire(v.memoire_go("MemTotal: 7861024 kB\n")).titre, "Mémoire : 8 Go")
        self.assertEqual(v.memoire(v.memoire_go("MemTotal: 3900000 kB\n")).titre, "Mémoire : 4 Go")

    def test_espace_libre(self):
        self.assertEqual([v.espace(go).etat for go in (200, 64, 40, 31, 0)], [v.OK, v.OK, v.ATTENTION, v.KO, v.KO])

    def test_fils(self):
        self.assertEqual([v.fils(n).etat for n in (16, 4, 3, 2, 1)], [v.OK, v.OK, v.ATTENTION, v.ATTENTION, v.KO])

    def test_verifier_assemble_les_quatre_controles(self):
        resultat = v.verifier(cpuinfo=INTEL, meminfo="MemTotal: 16000000 kB\n", kvm=True, libre_go=120)
        self.assertEqual([r.cle for r in resultat], ["virtualisation", "memoire", "espace", "fils"])
        self.assertEqual([r.etat for r in resultat], [v.OK, v.OK, v.OK, v.ATTENTION])

    def test_verifier_sur_ce_pc_ne_plante_pas(self):
        self.assertEqual(len(v.verifier()), 4)

    def test_outils_de_winboat(self):
        tout = lambda nom: "/usr/bin/" + nom  # noqa: E731
        self.assertEqual(v.outils_winboat(tout), [("Podman", True), ("Podman Compose", True), ("FreeRDP", True)])
        seulement_xfreerdp = lambda nom: "/usr/bin/xfreerdp" if nom == "xfreerdp" else None  # noqa: E731
        self.assertEqual(v.outils_winboat(seulement_xfreerdp)[2], ("FreeRDP", True))
        rien = lambda nom: None  # noqa: E731
        self.assertEqual([present for _, present in v.outils_winboat(rien)], [False, False, False])


class Catalogue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrees = catalogue.charger(FICHIER)

    def test_boxes_repond_aux_noms_connus_sous_windows(self):
        for requete in ("virtualbox", "vmware", "machine virtuelle", "hyper v", "logiciel indispensable"):
            premier = catalogue.chercher(self.entrees, requete)[0]
            self.assertEqual(premier.cible, "org.gnome.Boxes", requete)

    def test_windows_365_est_une_adresse_https(self):
        entree = catalogue.chercher(self.entrees, "windows 365")[0]
        self.assertEqual((entree.type, entree.cible), ("web", "https://windows365.microsoft.com/"))

    def test_les_logiciels_sans_equivalent_renvoient_vers_la_page(self):
        sans = [e for e in self.entrees if e.type == "windows"]
        self.assertTrue(sans)
        for entree in sans:
            self.assertIn("Windows complet", entree.remarque, entree.windows)


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from nicos_centre import theme
        from nicos_centre.pages import catalogue as page_catalogue, windows
        cls.windows, cls.page_catalogue = windows, page_catalogue
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        self.anciens = (launch.installed_flatpaks, launch._start, v.verifier, v.outils_winboat, catalogue.fournies)
        launch.installed_flatpaks = lambda: set()
        self.lances = []
        launch._start = lambda argv: self.lances.append(argv) or True
        v.verifier = lambda: v.verifier.__wrapped__(cpuinfo=INTEL, meminfo="MemTotal: 16000000 kB\n", kvm=False,
                                                    libre_go=28)
        v.verifier.__wrapped__ = self.anciens[2]
        v.outils_winboat = lambda: [("Podman", True), ("Podman Compose", False), ("FreeRDP", True)]
        catalogue.fournies = lambda listes=None: set()
        os.environ["NICOS_CATALOGUE"] = FICHIER

    def tearDown(self):
        launch.installed_flatpaks, launch._start, v.verifier, v.outils_winboat, catalogue.fournies = self.anciens
        os.environ.pop("NICOS_CATALOGUE", None)

    def textes(self, page):
        from PySide6.QtWidgets import QLabel
        return " | ".join(label.text() for label in page.findChildren(QLabel))

    def test_les_verifications_sont_montrees_avec_leur_etat(self):
        page = self.windows.build(None)
        textes = self.textes(page)
        for titre in ("Virtualisation matérielle désactivée", "Mémoire : 16 Go", "Espace libre : 28 Go",
                      "Processeur : 2 fils"):
            self.assertIn(titre, textes)
        # chaque carte porte son état (vert, orange, rouge) : la page n'en dépend plus que par le pictogramme
        etats = [carte.etat for carte in page.verifs]
        self.assertEqual(etats, [v.etat for v in page.verifications])
        self.assertEqual({v.OK, v.ATTENTION, v.KO}, set(etats))
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            page.resize(1040, 1000)
            page.show()
            self.app.processEvents()
            page.grab().save(os.path.join(CAPTURES, "windows.png"))

    def test_trois_options_et_leurs_actions(self):
        page = self.windows.build(None)
        boxes, winboat, nuage = page.cartes
        self.assertEqual(boxes.bouton.text(), "Installer")
        boxes.bouton.click()
        self.assertEqual(self.lances[-1], ["plasma-discover", "--application", "org.gnome.Boxes"])
        winboat.bouton.click()
        self.assertEqual(self.lances[-1], ["xdg-open", "https://www.winboat.app/"])
        nuage.bouton.click()
        self.assertEqual(self.lances[-1], ["xdg-open", "https://windows365.microsoft.com/"])

    def test_boxes_deja_installe(self):
        launch.installed_flatpaks = lambda: {"org.gnome.Boxes"}
        page = self.windows.build(None)
        self.assertEqual(page.cartes[0].bouton.text(), "Ouvrir")
        page.cartes[0].bouton.click()
        self.assertEqual(self.lances[-1], ["flatpak", "run", "org.gnome.Boxes"])

    def test_winboat_dit_ce_qui_manque(self):
        textes = self.textes(self.windows.build(None))
        self.assertIn("Il manque : Podman Compose.", textes)
        v.outils_winboat = lambda: [("Podman", True), ("Podman Compose", True), ("FreeRDP", True)]
        self.assertIn("il ne reste qu'à télécharger WinBoat", self.textes(self.windows.build(None)))

    def test_la_licence_windows_est_rappelee(self):
        self.assertIn("licence Windows", self.textes(self.windows.build(None)))

    def test_le_catalogue_renvoie_vers_la_page(self):
        class Centre:
            pages = []

            def show_page(self, cle):
                self.pages.append(cle)
        centre = Centre()
        page = self.page_catalogue.build(centre)
        from PySide6.QtWidgets import QPushButton
        bouton = next(b for b in page.findChildren(QPushButton) if b.text() == "Windows complet")
        bouton.click()
        self.assertEqual(centre.pages, ["windows"])


if __name__ == "__main__":
    unittest.main()
