"""Tests de l'aiguillage des programmes Windows (moteurs.py, aiguillage_fenetre.py) : le conseil (équivalent, Wine,
Windows), le choix retenu, les commandes Bottles (lecture seule, jamais de shell), et la fenêtre avec un faux Flatpak qui
joue Bottles : installation, première bouteille, lancement, échec.

python3 -m unittest discover -s tests/image/centre -p test_moteurs.py
"""

import os
import stat
import sys
import tempfile
import time
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
sys.path.insert(0, RACINE)
DONNEES = os.path.join(ICI, "../../../system_files/usr/share/binixx/catalogue-windows")
CATALOGUE = os.environ.get("BINIXX_CATALOGUE", os.path.join(DONNEES, "catalogue.tsv"))
REQUIS = os.environ.get("BINIXX_WINDOWS_REQUIS", os.path.join(DONNEES, "windows-requis.tsv"))

from binixx_centre import catalogue, moteurs  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from binixx_centre import aiguillage_fenetre
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


class Conseil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrees = catalogue.charger(CATALOGUE)
        cls.regles = moteurs.charger_windows_requis(REQUIS)

    def conseil(self, nom, memoire=None):
        return moteurs.conseiller(f"/home/a/Téléchargements/{nom}", self.entrees, self.regles, memoire)

    def test_equivalent_d_abord(self):
        conseil = self.conseil("WordSetup.exe")
        self.assertEqual(conseil.moteur, "equivalent")
        self.assertEqual(conseil.equivalent.cible, "org.onlyoffice.desktopeditors")

    def test_programme_inconnu_avec_wine(self):
        conseil = self.conseil("Setup_Zorglub_Pro_v3.exe")
        self.assertEqual(conseil.moteur, "wine")
        self.assertIsNone(conseil.equivalent)

    def test_programme_connu_pour_echouer_avec_wine(self):
        conseil = self.conseil("SolidWorks2025_x64.msi")
        self.assertEqual(conseil.moteur, "windows")
        self.assertIn("CAO", conseil.raison)

    def test_logiciel_metier_sans_equivalent(self):
        # « Sage » est au catalogue sans équivalent direct : Windows est conseillé
        self.assertEqual(self.conseil("Sage100_Setup.exe").moteur, "windows")

    def test_choix_retenu(self):
        chemin = "/home/a/Téléchargements/Setup_Zorglub_Pro_v3.exe"
        conseil = self.conseil("Setup_Zorglub_Pro_v3.exe", {chemin: "windows"})
        self.assertEqual((conseil.moteur, conseil.retenu), ("windows", True))
        # un équivalent retenu qui n'existe plus (catalogue changé) n'est pas suivi
        self.assertEqual(self.conseil("Setup_Zorglub_Pro_v3.exe", {chemin: "equivalent"}).moteur, "wine")

    def test_regles_sans_faux_positifs(self):
        for nom in ("webpconverter.exe", "logiciel-ciel-bleu.exe", "inventory.exe", "ccleaner.exe", "psftp.exe"):
            self.assertIsNone(moteurs.windows_requis(self.regles, nom), nom)
        self.assertIsNotNone(moteurs.windows_requis(self.regles, "Photoshop_Set-Up.exe"))

    def test_regles_mal_formees(self):
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as fichier:
            fichier.write("photoshop\n")
        try:
            with self.assertRaises(ValueError):
                moteurs.charger_windows_requis(fichier.name)
        finally:
            os.unlink(fichier.name)


class Memoire(unittest.TestCase):
    def test_retenir_puis_oublier(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "binixx", "moteurs-windows.json")
            moteurs.retenir("/tmp/a.exe", "wine", chemin)
            moteurs.retenir("/tmp/b.exe", "windows", chemin)
            self.assertEqual(moteurs.lire_memoire(chemin), {"/tmp/a.exe": "wine", "/tmp/b.exe": "windows"})
            moteurs.retenir("/tmp/a.exe", None, chemin)
            self.assertEqual(moteurs.lire_memoire(chemin), {"/tmp/b.exe": "windows"})
            with self.assertRaises(ValueError):
                moteurs.retenir("/tmp/a.exe", "dos", chemin)

    def test_fichier_abime(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = os.path.join(dossier, "m.json")
            with open(chemin, "w") as fichier:
                fichier.write('{"/a.exe": "wine", "/b.exe": "rm -rf", "x": 3')
            self.assertEqual(moteurs.lire_memoire(chemin), {})
            with open(chemin, "w") as fichier:
                fichier.write('{"/a.exe": "wine", "/b.exe": "rm -rf"}')
            self.assertEqual(moteurs.lire_memoire(chemin), {"/a.exe": "wine"})


class Commandes(unittest.TestCase):
    def test_lancer_en_lecture_seule_sans_shell(self):
        programme = "/home/a/Téléchargements/mon setup; rm -rf ~.exe"
        argv = moteurs.commande_lancer(programme)
        self.assertEqual(argv[:3], ["flatpak", "run", "--command=bottles-cli"])
        self.assertIn("--filesystem=/home/a/Téléchargements:ro", argv)
        self.assertEqual(argv[argv.index(moteurs.BOTTLES) + 1:], ["run", "-b", "BinixX", "-e", programme])
        self.assertNotIn("sh", argv)

    def test_partage_limite_au_fichier_hors_sous_dossier(self):
        self.assertEqual(moteurs.dossier_partage("/home/a/x.exe", maison="/home/a"), "/home/a/x.exe")
        self.assertEqual(moteurs.dossier_partage("/home/b.exe", maison="/home/a"), "/home/b.exe")
        self.assertEqual(moteurs.dossier_partage("/media/x.exe", maison="/home/a"), "/media/x.exe")
        self.assertEqual(moteurs.dossier_partage("/run/media/a/CLE/setup.exe", maison="/home/a"), "/run/media/a/CLE")

    def test_bouteille_existe(self):
        self.assertTrue(moteurs.bouteille_existe("Found 2 bottles:\n- Jeux\n- BinixX\n"))
        self.assertFalse(moteurs.bouteille_existe("Found 1 bottles:\n- BinixX-ancienne\n"))
        self.assertFalse(moteurs.bouteille_existe(""))

    def test_creer_bouteille_application(self):
        argv = moteurs.commande_creer()
        self.assertEqual(argv[-5:], ["new", "--bottle-name", "BinixX", "--environment", "application"])

    def test_trouver_winboat(self):
        with tempfile.TemporaryDirectory() as dossier:
            self.assertIsNone(moteurs.trouver_winboat([dossier, "/nexiste/pas"]))
            open(os.path.join(dossier, "appimagekit_1234-WinBoat.desktop"), "w").close()
            self.assertTrue(moteurs.trouver_winboat([dossier]).endswith("WinBoat.desktop"))

    def test_windows_possible(self):
        from binixx_centre import virtualisation as v
        bon = v.verifier(cpuinfo="processor : 0\nprocessor : 1\nprocessor : 2\nprocessor : 3\nflags : vmx\n",
                         meminfo="MemTotal: 16000000 kB\n", kvm=True, libre_go=200)
        self.assertTrue(moteurs.windows_possible(bon))
        sans_kvm = v.verifier(cpuinfo="flags : vmx\n", meminfo="MemTotal: 16000000 kB\n", kvm=False, libre_go=200)
        self.assertFalse(moteurs.windows_possible(sans_kvm))

    def test_json(self):
        import contextlib
        import io
        import json
        sortie = io.StringIO()
        os.environ["BINIXX_CATALOGUE"], os.environ["BINIXX_WINDOWS_REQUIS"] = CATALOGUE, REQUIS
        with tempfile.TemporaryDirectory() as dossier, contextlib.redirect_stdout(sortie):
            os.environ["XDG_CONFIG_HOME"] = dossier
            moteurs.main(["--json", "/tmp/Setup_Zorglub_Pro_v3.exe"])
        donnees = json.loads(sortie.getvalue())
        self.assertEqual(donnees["moteur"], "wine")
        self.assertIn("-e", donnees["wine"])


FAUX_FLATPAK = """#!/bin/bash
# Joue Flatpak et Bottles : « info » répond selon $ETAT/installe, « list bottles » selon $ETAT/bouteille
echo "$*" >> "$ETAT/journal"
case "$1" in
    info) [[ -e "$ETAT/installe" ]] ;;
    run)
        shift; while [[ "$1" == --* ]]; do shift; done; shift   # options de flatpak run, puis l'application
        case "$1" in
            list) echo "Found 1 bottles:"; [[ -e "$ETAT/bouteille" ]] && echo "- BinixX"; exit 0 ;;
            new) touch "$ETAT/bouteille" ;;
            run) [[ -e "$ETAT/echec" ]] && { echo "Wine: erreur de démarrage"; exit 1; }; exit 0 ;;
        esac ;;
esac
"""

FAUX_INSTALLATEUR = """#!/bin/bash
echo "installateur $*" >> "$ETAT/journal"
touch "$ETAT/installe"
"""


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Fenetre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.entrees = catalogue.charger(CATALOGUE)
        cls.regles = moteurs.charger_windows_requis(REQUIS)

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.etat = os.path.join(self.dossier, "etat")
        os.makedirs(self.etat)
        os.environ["ETAT"] = self.etat
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.dossier, "config")
        self.flatpak = self._script("flatpak", FAUX_FLATPAK)
        self.installateur = self._script("installateur", FAUX_INSTALLATEUR)
        self.programme = os.path.join(self.dossier, "Setup_Zorglub_Pro_v3.exe")
        open(self.programme, "w").close()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dossier)

    def _script(self, nom, texte):
        chemin = os.path.join(self.dossier, nom)
        with open(chemin, "w") as fichier:
            fichier.write(texte)
        os.chmod(chemin, os.stat(chemin).st_mode | stat.S_IXUSR)
        return chemin

    def fenetre(self, programme=None, moteur=None, **options):
        options.setdefault("winboat", lambda: None)
        return aiguillage_fenetre.Fenetre(programme or self.programme, self.entrees, self.regles, moteur=moteur,
                                          flatpak=self.flatpak, installateur=self.installateur, installees=set(),
                                          **options)

    def attendre(self, fenetre, secondes=10):
        fin = time.monotonic() + secondes
        while fenetre.etape != "fini" and time.monotonic() < fin:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertEqual(fenetre.etape, "fini", fenetre.statut.text())

    def journal(self):
        with open(os.path.join(self.etat, "journal")) as fichier:
            return fichier.read()

    def test_ordre_des_choix(self):
        self.assertEqual(list(self.fenetre().cartes), ["wine", "windows"])  # pas d'équivalent connu
        word = os.path.join(self.dossier, "WordSetup.exe")
        self.assertEqual(list(self.fenetre(word).cartes), ["equivalent", "wine", "windows"])
        adobe = os.path.join(self.dossier, "Photoshop_Set-Up.exe")
        cartes = list(self.fenetre(adobe).cartes)
        self.assertLess(cartes.index("windows"), cartes.index("wine"))

    def test_wine_installe_bottles_prepare_la_bouteille_puis_ouvre(self):
        fenetre = self.fenetre()
        fenetre.retenir.setChecked(True)
        fenetre.choisir("wine")
        self.attendre(fenetre)
        journal = self.journal()
        self.assertIn("installateur com.usebottles.bottles", journal)
        self.assertIn("new --bottle-name BinixX --environment application", journal)
        self.assertIn(f"--filesystem={self.dossier}:ro", journal)
        self.assertIn(f"run -b BinixX -e {self.programme}", journal)
        self.assertIn("démarre avec Wine", fenetre.statut.text())
        self.assertFalse(fenetre.essayer_windows.isHidden())
        self.assertEqual(moteurs.lire_memoire(), {self.programme: "wine"})

    def test_wine_deja_pret(self):
        open(os.path.join(self.etat, "installe"), "w").close()
        open(os.path.join(self.etat, "bouteille"), "w").close()
        fenetre = self.fenetre(moteur="wine")   # choix retenu : directement au travail
        self.attendre(fenetre)
        journal = self.journal()
        self.assertNotIn("installateur", journal)
        self.assertNotIn("new --bottle-name", journal)
        self.assertIn("démarre avec Wine", fenetre.statut.text())
        self.assertEqual(moteurs.lire_memoire(), {})   # « Retenir » n'est pas coché

    def test_echec_de_wine_propose_windows(self):
        for nom in ("installe", "bouteille", "echec"):
            open(os.path.join(self.etat, nom), "w").close()
        fenetre = self.fenetre(moteur="wine")
        self.attendre(fenetre)
        self.assertIn("Wine n'a pas pu ouvrir", fenetre.statut.text())
        self.assertIn("erreur de démarrage", fenetre.statut.text())
        self.assertFalse(fenetre.bandeau.isHidden())
        self.assertFalse(fenetre.essayer_windows.isHidden())

    def test_installation_refusee(self):
        self.installateur = self._script("installateur", "#!/bin/bash\nexit 0\n")  # l'utilisateur ferme la fenêtre
        fenetre = self.fenetre(moteur="wine")
        self.attendre(fenetre)
        self.assertIn("Bottles n'est pas installé", fenetre.statut.text())

    def test_windows_ouvre_winboat_ou_la_page_du_centre(self):
        appels = []
        from binixx_centre import launch
        anciens = launch.open_desktop_file, launch.open_centre
        launch.open_desktop_file = lambda chemin: appels.append(("winboat", chemin)) or True
        launch.open_centre = lambda page, recherche="": appels.append(("centre", page)) or True
        try:
            fenetre = self.fenetre(winboat=lambda: "/usr/share/applications/winboat.desktop", verifier=lambda: [])
            fenetre.choisir("windows")
            self.assertEqual(appels, [("winboat", "/usr/share/applications/winboat.desktop")])
            self.assertIn("Add custom", fenetre.statut.text())
            from binixx_centre.virtualisation import Verification
            fenetre = self.fenetre(winboat=lambda: "/w.desktop", verifier=lambda: [Verification("v", "ko", "", "")])
            fenetre.choisir("windows")
            self.assertEqual(appels[-1], ("centre", "windows"))
        finally:
            launch.open_desktop_file, launch.open_centre = anciens


if __name__ == "__main__":
    unittest.main()
