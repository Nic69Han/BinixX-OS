"""Tests de la page « Paramètres » : fichier des réglages, recherche sans accents, modules KDE, page.

python3 -m unittest discover -s tests/image/centre -p 'test_parametres.py'   (la partie Qt est ignorée sans PySide6)
"""

import glob
import os
import re
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
DEPOT = os.path.join(ICI, "../../..")
RACINE = os.environ.get("NICOS_CENTRE", os.path.join(DEPOT, "system_files/usr/lib/nicos/centre"))
FICHIER = os.environ.get("NICOS_PARAMETRES", os.path.join(DEPOT, "system_files/usr/share/nicos/parametres/parametres.tsv"))
LANCEURS = os.environ.get("NICOS_LANCEURS", os.path.join(DEPOT, "system_files/usr/share/applications"))
CATALOGUE = os.environ.get("NICOS_CATALOGUE", os.path.join(DEPOT, "system_files/usr/share/nicos/catalogue-windows/catalogue.tsv"))
FOURNIES = os.environ.get("NICOS_FLATPAKS", os.path.join(DEPOT, "flatpaks/system-flatpaks.list"))
CAPTURES = os.environ.get("NICOS_CAPTURES")
sys.path.insert(0, RACINE)

from nicos_centre import catalogue, launch, parametres as p  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

KCMSHELL = """The following modules are available:

  kcm_about-distro            - À propos de ce système
  kcm_bluetooth               - Bluetooth
  kcm_kscreen                 - Écrans et moniteurs
  kcm_lookandfeel             - Thème global
  kcm_networkmanagement       - Connexions
  kcm_pulseaudio              - Audio
"""


def lire_cles_des_pages():
    cles = set()
    for fichier in glob.glob(os.path.join(RACINE, "nicos_centre/pages/*.py")):
        with open(fichier, encoding="utf-8") as lecture:
            cles.update(re.findall(r'^KEY = "([a-z_]+)"', lecture.read(), re.M))
    return cles


class Fichier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reglages = p.charger(FICHIER)

    def test_les_categories_de_windows_11_dans_l_ordre(self):
        cats = p.categories(self.reglages)
        self.assertEqual(cats[0], "Système")
        for attendu in ("Bluetooth et appareils", "Réseau et Internet", "Personnalisation", "Applications", "Comptes",
                        "Heure et langue", "Accessibilité", "Confidentialité et sécurité"):
            self.assertIn(attendu, cats)
        self.assertGreaterEqual(len(self.reglages), 40)

    def test_pas_de_doublon_de_nom_dans_une_categorie(self):
        cles = [(r.categorie, r.nom) for r in self.reglages]
        self.assertEqual(len(cles), len(set(cles)))

    def test_chaque_reglage_a_des_mots_de_recherche_et_une_explication(self):
        for reglage in self.reglages:
            self.assertTrue(reglage.explication, reglage.nom)
            self.assertGreaterEqual(len(reglage.alias), 2, reglage.nom)

    def test_les_pages_du_centre_visees_existent(self):
        cles = lire_cles_des_pages()
        for reglage in self.reglages:
            if reglage.type == "page":
                self.assertIn(reglage.cible, cles, reglage.nom)

    def test_les_lanceurs_vises_existent(self):
        for reglage in self.reglages:
            if reglage.type == "app":
                self.assertTrue(os.path.exists(os.path.join(LANCEURS, reglage.cible + ".desktop")), reglage.cible)

    def test_les_applications_flatpak_visees_sont_connues(self):
        connues = catalogue.fournies((FOURNIES,)) | {e.cible for e in catalogue.charger(CATALOGUE) if e.type == "flatpak"}
        for reglage in self.reglages:
            if reglage.type == "flatpak":
                self.assertIn(reglage.cible, connues, reglage.cible)

    def test_les_modules_kde_ont_un_identifiant_valide(self):
        modules = [r for r in self.reglages if r.type == "kcm"]
        self.assertGreaterEqual(len(modules), 30)
        for reglage in modules:
            self.assertRegex(reglage.cible, r"^kcm_[A-Za-z0-9_-]+$")


class Lecture(unittest.TestCase):
    def ecrire(self, contenu):
        fichier = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, fichier.name)
        fichier.write(contenu)
        fichier.close()
        return fichier.name

    def refuse(self, ligne, morceau):
        with self.assertRaises(ValueError) as erreur:
            p.charger(self.ecrire(ligne + "\n"))
        self.assertIn(morceau, str(erreur.exception))

    def test_ligne_valide_et_info_sans_tabulation_finale(self):
        reglages = p.charger(self.ecrire("# commentaire\n\nC\tA\tx;y\tExplication.\tkcm\tkcm_a\nC\tB\tz\tTexte.\tinfo\n"))
        self.assertEqual([(r.nom, r.type, r.cible) for r in reglages], [("A", "kcm", "kcm_a"), ("B", "info", "")])

    def test_lignes_refusees(self):
        self.refuse("C\tA\tx\tE.\tkcm", "colonnes")
        self.refuse("C\tA\tx\tE.\tinconnu\tz", "type")
        self.refuse("C\tA\tx\tE.\tkcm\tkcm_a; rm -rf /", "invalide")
        self.refuse("C\tA\tx\tE.\tkcm\tpas_un_module", "invalide")
        self.refuse("C\tA\tx\tE.\tpage\tSecurite", "invalide")
        self.refuse("C\tA\tx\tE.\tpage\t../aide", "invalide")
        self.refuse("C\tA\tx\tE.\tdiscover\tbrowse; id", "Discover")
        self.refuse("C\tA\tx\tE.\tflatpak\t-y", "invalide")
        self.refuse("C\tA\tx\tE.\tinfo\tkcm_a", "info")
        self.refuse("\tA\tx\tE.\tkcm\tkcm_a", "obligatoires")


class Recherche(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reglages = p.charger(FICHIER)

    def premier(self, requete):
        trouves = p.chercher(self.reglages, requete)
        self.assertTrue(trouves, requete)
        return trouves[0].nom

    def test_les_mots_de_windows_trouvent_le_bon_reglage(self):
        attendus = {"wifi": "Wi-Fi, Ethernet et VPN", "Wi-Fi": "Wi-Fi, Ethernet et VPN",
                    "imprimante": "Imprimantes et scanners", "bluetooth": "Bluetooth",
                    "fond d'écran": "Arrière-plan", "mode sombre": "Thèmes : clair ou sombre",
                    "bitlocker": "Protéger mes données", "windows update": "Mises à jour du système",
                    "panneau de configuration": "Administration du PC", "fuseau horaire": "Date et heure",
                    "mot de passe": "Votre compte", "desinstaller": "Applications installées",
                    "clé usb": "Lecture automatique", "veille": "Alimentation et batterie",
                    "reinitialiser ce pc": "Récupération", "barre des taches": "Barre des tâches"}
        for requete, nom in attendus.items():
            self.assertEqual(self.premier(requete), nom, requete)

    def test_sans_accents_ni_majuscules(self):
        self.assertEqual([r.nom for r in p.chercher(self.reglages, "ÉCRAN")], [r.nom for r in p.chercher(self.reglages, "ecran")])
        self.assertIn("Affichage", [r.nom for r in p.chercher(self.reglages, "ecran")])

    def test_requete_vide_ou_sans_resultat(self):
        self.assertEqual(p.chercher(self.reglages, ""), [])
        self.assertEqual(p.chercher(self.reglages, "   "), [])
        self.assertEqual(p.chercher(self.reglages, "zzzzqqqq"), [])

    def test_tous_les_mots_doivent_correspondre(self):
        self.assertEqual(self.premier("souris sans fil"), "Bluetooth")
        self.assertEqual(p.chercher(self.reglages, "souris bluetooth imprimante"), [])


class Modules(unittest.TestCase):
    def test_lecture_de_kcmshell(self):
        self.assertEqual(p.modules_disponibles(KCMSHELL),
                         {"kcm_about-distro", "kcm_bluetooth", "kcm_kscreen", "kcm_lookandfeel", "kcm_networkmanagement",
                          "kcm_pulseaudio"})

    def test_sortie_inutilisable_ne_masque_rien(self):
        self.assertIsNone(p.modules_disponibles(""))
        self.assertIsNone(p.modules_disponibles("kcmshell6: command not found"))

    def test_un_module_absent_est_masque_le_reste_non(self):
        reglages = p.charger(FICHIER)
        visibles = p.visibles(reglages, p.modules_disponibles(KCMSHELL))
        noms = {r.nom for r in visibles}
        self.assertIn("Affichage", noms)
        self.assertNotIn("Écran tactile", noms)
        self.assertIn("Barre des tâches", noms)  # « info » : jamais masqué
        self.assertIn("Protéger mes données", noms)  # page du Centre : jamais masquée
        self.assertEqual(len(p.visibles(reglages, None)), len(reglages))


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from nicos_centre import theme
        from nicos_centre.pages import parametres
        cls.module = parametres
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        os.environ["NICOS_PARAMETRES"] = FICHIER
        self.anciens = (launch.run, launch.installed_flatpaks, launch._start)
        self.tous = {"kcm_" + r.cible[4:] for r in p.charger(FICHIER) if r.type == "kcm"}
        self.modules = set(self.tous)
        launch.run = lambda argv, timeout=120: (0, "\n".join(f"  {m} - un module" for m in sorted(self.modules)))
        launch.installed_flatpaks = lambda: {"org.gnome.DejaDup"}
        self.lances = []
        launch._start = lambda argv: self.lances.append(argv) or True
        self.pages = []
        self.centre = type("Centre", (), {"show_page": lambda s, cle: self.pages.append(cle)})()

    def tearDown(self):
        launch.run, launch.installed_flatpaks, launch._start = self.anciens
        os.environ.pop("NICOS_PARAMETRES", None)

    def carte(self, page, nom):
        return next(c for c in page.cartes if c.reglage.nom == nom)

    def choisir(self, page, categorie):
        for rang in range(page.liste.count()):
            if page.liste.item(rang).text() == categorie:
                page.liste.setCurrentRow(rang)
                return
        self.fail(categorie)

    def test_la_premiere_categorie_est_affichee_et_chaque_clic_ouvre_le_bon_module(self):
        page = self.module.build(self.centre)
        self.assertEqual(page.categorie_courante(), "Système")
        self.assertEqual(page.liste.count(), 11)
        self.carte(page, "Affichage").bouton.click()
        self.assertEqual(self.lances[-1], ["systemsettings", "kcm_kscreen"])
        self.carte(page, "Son").bouton.click()
        self.assertEqual(self.lances[-1], ["systemsettings", "kcm_pulseaudio"])
        self.carte(page, "Stockage et disques").bouton.click()
        self.assertEqual(self.lances[-1], ["kioclient", "exec", "/usr/share/applications/nicos-administration.desktop"])
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            page.resize(1040, 900)
            page.show()
            self.app.processEvents()
            page.grab().save(os.path.join(CAPTURES, "parametres.png"))
            page.recherche.setText("mot de passe")
            self.app.processEvents()
            page.grab().save(os.path.join(CAPTURES, "parametres-recherche.png"))

    def test_la_recherche_traverse_les_categories(self):
        page = self.module.build(self.centre)
        page.recherche.setText("Bluetooth")
        self.assertEqual(page.cartes[0].reglage.nom, "Bluetooth")
        self.assertEqual(page.liste.currentRow(), -1)  # aucune catégorie choisie pendant la recherche
        page.recherche.setText("")
        self.assertEqual(page.categorie_courante(), "Système")
        page.recherche.setText("zzzzqqqq")
        self.assertEqual(page.cartes, [])

    def test_une_page_du_centre_et_discover(self):
        page = self.module.build(self.centre)
        self.choisir(page, "Confidentialité et sécurité")
        self.carte(page, "Protéger mes données").bouton.click()
        self.assertEqual(self.pages, ["securite"])
        self.choisir(page, "Mises à jour et récupération")
        self.carte(page, "Mises à jour du système").bouton.click()
        self.assertEqual(self.lances[-1], ["plasma-discover", "--mode", "update"])
        self.carte(page, "Récupération").bouton.click()
        self.assertEqual(self.pages[-1], "aide")

    def test_une_explication_sans_bouton(self):
        page = self.module.build(self.centre)
        self.choisir(page, "Personnalisation")
        self.assertIsNone(self.carte(page, "Barre des tâches").bouton)
        self.assertIsNotNone(self.carte(page, "Arrière-plan").bouton)

    def test_application_flatpak_installee_ou_a_installer(self):
        page = self.module.build(self.centre)
        self.choisir(page, "Mises à jour et récupération")
        carte = self.carte(page, "Sauvegarde")
        self.assertEqual(carte.bouton.text(), "Ouvrir")
        carte.bouton.click()
        self.assertEqual(self.lances[-1], ["flatpak", "run", "org.gnome.DejaDup"])
        launch.installed_flatpaks = lambda: set()
        page = self.module.build(self.centre)
        self.choisir(page, "Mises à jour et récupération")
        carte = self.carte(page, "Sauvegarde")
        self.assertEqual(carte.bouton.text(), "Installer")
        carte.bouton.click()
        self.assertEqual(self.lances[-1], ["plasma-discover", "--application", "org.gnome.DejaDup"])

    def test_un_module_absent_de_ce_pc_est_masque(self):
        self.modules.discard("kcm_touchscreen")
        page = self.module.build(self.centre)
        page.recherche.setText("tactile")
        self.assertNotIn("Écran tactile", [c.reglage.nom for c in page.cartes])

    def test_kcmshell_en_panne_ne_masque_rien(self):
        launch.run = lambda argv, timeout=120: (1, "")
        page = self.module.build(self.centre)
        self.assertEqual(page.liste.count(), 11)
        page.recherche.setText("tactile")
        self.assertIn("Écran tactile", [c.reglage.nom for c in page.cartes])

    def test_les_reglages_avances_ouvrent_la_configuration_du_systeme(self):
        page = self.module.build(self.centre)
        from PySide6.QtWidgets import QPushButton
        bouton = next(b for b in page.findChildren(QPushButton) if b.text().startswith("Tous les réglages avancés"))
        bouton.click()
        self.assertEqual(self.lances[-1], ["systemsettings"])


if __name__ == "__main__":
    unittest.main()
