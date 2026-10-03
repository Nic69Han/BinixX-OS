"""Tests de la page « Installer des applications » : liste tirée du catalogue, licences, commande, page.

python3 -m unittest discover -s tests/image/centre -p 'test_applications.py'   (la partie Qt est ignorée sans PySide6)
Flatpak est remplacé par un petit script (BINIXX_FLATPAK) : rien n'est installé pour de vrai.
"""

import os
import stat
import sys
import tempfile
import time
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
DONNEES = os.path.join(ICI, "../../../system_files/usr/share/binixx/catalogue-windows")
FICHIER = os.environ.get("BINIXX_CATALOGUE", os.path.join(DONNEES, "catalogue.tsv"))
LICENCES = os.environ.get("BINIXX_LICENCES", os.path.join(DONNEES, "licences.tsv"))
FOURNIES = os.environ.get("BINIXX_FLATPAKS", os.path.join(ICI, "../../../flatpaks/system-flatpaks.list"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import applications as a, catalogue, launch  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

PROPRIETAIRES = {"com.spotify.Client", "com.discordapp.Discord", "com.anydesk.Anydesk", "com.dropbox.Client",
                 "com.visualstudio.code"}


class Liste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrees = catalogue.charger(FICHIER)
        cls.fournies = catalogue.fournies((FOURNIES,))
        cls.apps = a.proposees(cls.entrees, cls.fournies)
        cls.ids = {x.identifiant for x in cls.apps}

    def test_les_applications_connues_sous_windows_sont_proposees(self):
        for ident in ("org.videolan.VLC", "com.spotify.Client", "com.discordapp.Discord", "com.bitwarden.desktop",
                      "org.libreoffice.LibreOffice", "com.rustdesk.RustDesk", "org.gimp.GIMP"):
            self.assertIn(ident, self.ids)
        self.assertGreaterEqual(len(self.apps), 20)

    def test_ni_les_jeux_ni_windows_complet_ni_ce_qui_est_deja_installe(self):
        for ident in ("com.valvesoftware.Steam", "net.lutris.Lutris", "com.usebottles.bottles", "org.gnome.Boxes"):
            self.assertNotIn(ident, self.ids)
        for ident in self.fournies:
            self.assertNotIn(ident, self.ids)
        self.assertNotIn("org.onlyoffice.desktopeditors", self.ids)

    def test_une_seule_ligne_par_application(self):
        self.assertEqual(len(self.ids), len(self.apps))

    def test_plusieurs_logiciels_windows_pour_une_application(self):
        gimp = next(x for x in self.apps if x.identifiant == "org.gimp.GIMP")
        self.assertIn("Adobe Photoshop", gimp.remplace)
        entrees = [e for e in self.entrees if e.cible == "org.kde.krita"]
        self.assertEqual(len(entrees), 1)

    def test_le_remplace_ne_repete_pas_le_nom_de_l_application(self):
        vlc = next(x for x in self.apps if x.identifiant == "org.videolan.VLC")
        self.assertEqual(a.remplace_vraiment(vlc), ())
        rustdesk = next(x for x in self.apps if x.identifiant == "com.rustdesk.RustDesk")
        self.assertEqual(a.remplace_vraiment(rustdesk), ("TeamViewer",))

    def test_groupes_par_categorie_dans_l_ordre_alphabetique(self):
        groupes = a.par_categorie(self.apps)
        noms = [nom for nom, _ in groupes]
        self.assertEqual(noms, sorted(noms, key=str.lower))
        self.assertEqual(sum(len(g) for _, g in groupes), len(self.apps))

    def test_chaque_identifiant_propose_est_valide(self):
        for ident in self.ids:
            a.valider(ident)


class Licences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.licences = a.lire_licences(LICENCES)
        cls.entrees = catalogue.charger(FICHIER)

    def test_chaque_application_proposee_a_sa_licence(self):
        for application in a.proposees(self.entrees, catalogue.fournies((FOURNIES,))):
            self.assertIn(application.identifiant, self.licences, application.nom)

    def test_le_fichier_ne_parle_que_d_applications_du_catalogue(self):
        cibles = {e.cible for e in self.entrees if e.type == "flatpak"}
        self.assertLessEqual(set(self.licences), cibles)

    def test_les_applications_proprietaires_sont_signalees(self):
        for ident in PROPRIETAIRES:
            self.assertTrue(a.est_proprietaire(self.licences[ident]), ident)
            self.assertEqual(a.libelle_licence(self.licences[ident]), "Propriétaire")
        for ident in ("org.videolan.VLC", "org.gimp.GIMP", "com.bitwarden.desktop"):
            self.assertFalse(a.est_proprietaire(self.licences[ident]), ident)

    def test_libelles(self):
        self.assertEqual(a.libelle_licence("GPL-3.0-or-later"), "Libre · GPL-3.0-or-later")
        self.assertEqual(a.libelle_licence("GPL-3.0+ AND LGPL-3.0+"), "Libre")
        self.assertEqual(a.libelle_licence("LicenseRef-proprietary"), "Propriétaire")
        self.assertEqual(a.libelle_licence(""), "Licence non vérifiée")

    def test_fichier_absent(self):
        self.assertEqual(a.lire_licences("/inexistant/licences.tsv"), {})


class Commande(unittest.TestCase):
    def test_commande_pour_tout_le_systeme_sans_question(self):
        self.assertEqual(a.commande(["org.videolan.VLC", "com.spotify.Client"]),
                         ["flatpak", "install", "--system", "--noninteractive", "--assumeyes", "flathub",
                          "org.videolan.VLC", "com.spotify.Client"])

    def test_identifiants_dangereux_refuses(self):
        for mauvais in ("", "--user", "-y", "vlc", "org.videolan.VLC; rm -rf /", "org.videolan.VLC org.evil.App",
                        "$(id).app.x", "org..VLC", "../../etc/passwd", "org.videolan.VLC\n--user", "a.b"):
            with self.assertRaises(ValueError, msg=repr(mauvais)):
                a.commande([mauvais])

    def test_aucune_application(self):
        with self.assertRaises(ValueError):
            a.commande([])

    def test_derniere_ligne_de_progression(self):
        sortie = "Installing 1/2…\rInstalling 1/2… ████████▌     45%\rInstalling 1/2… ███████████ 100%\n"
        self.assertEqual(a.derniere_ligne(sortie), "Installing 1/2… 100%")
        self.assertEqual(a.derniere_ligne("Installing 1/2…\rInstalling 1/2… ████▌   45%\r"), "Installing 1/2… 45%")
        self.assertEqual(a.derniere_ligne(""), "")
        self.assertLessEqual(len(a.derniere_ligne("x" * 500)), 110)

    def test_explications_des_echecs(self):
        self.assertIn("administrateur", a.explication_echec("error: Flatpak system operation Deploy not allowed for user"))
        self.assertIn("réseau", a.explication_echec("error: Unable to connect to dl.flathub.org"))
        self.assertIn("Flathub", a.explication_echec("error: No remote refs found for 'org.nope.App'; not found"))
        self.assertIn("place", a.explication_echec("error: No space left on device"))
        self.assertEqual(a.explication_echec("quelque chose d'inattendu"), "")


FAUX_FLATPAK = """#!/bin/sh
# faux flatpak : note les arguments, « installe » en écrivant dans un fichier d'état, imite la progression
echo "$@" >> "$FAUX_JOURNAL"
printf 'Installing 1/2…\\rInstalling 1/2… 45%%\\r'
if [ "${FAUX_CODE:-0}" != 0 ]; then
    echo "${FAUX_ERREUR:-error: échec simulé}" >&2
    exit "$FAUX_CODE"
fi
for ident in "$@"; do
    case "$ident" in *.*.*) echo "$ident" >> "$FAUX_ETAT" ;; esac
done
echo 'Terminé.'
"""


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from binixx_centre import theme
        from binixx_centre.pages import applications
        cls.module = applications
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dossier, ignore_errors=True))
        self.journal = os.path.join(self.dossier, "journal")
        self.etat = os.path.join(self.dossier, "etat")
        for fichier in (self.journal, self.etat):
            open(fichier, "w").close()
        faux = os.path.join(self.dossier, "flatpak")
        with open(faux, "w") as fichier:
            fichier.write(FAUX_FLATPAK)
        os.chmod(faux, os.stat(faux).st_mode | stat.S_IXUSR)
        os.environ.update({"BINIXX_CATALOGUE": FICHIER, "BINIXX_LICENCES": LICENCES, "BINIXX_FLATPAK": faux,
                           "FAUX_JOURNAL": self.journal, "FAUX_ETAT": self.etat})
        os.environ.pop("FAUX_CODE", None)
        self.anciens = (launch.installed_flatpaks, catalogue.fournies)
        launch.installed_flatpaks = lambda: set(self.lire(self.etat).split()) | self.deja
        catalogue.fournies = lambda listes=None: set(self.anciens[1]((FOURNIES,)))
        self.deja = set()

    def tearDown(self):
        launch.installed_flatpaks, catalogue.fournies = self.anciens
        for cle in ("BINIXX_CATALOGUE", "BINIXX_LICENCES", "BINIXX_FLATPAK", "FAUX_JOURNAL", "FAUX_ETAT", "FAUX_CODE",
                    "FAUX_ERREUR"):
            os.environ.pop(cle, None)

    def attendre(self, page, secondes=20):
        fin = time.time() + secondes
        while page.en_cours() and time.time() < fin:
            self.app.processEvents()
            time.sleep(0.01)
        self.app.processEvents()
        self.assertFalse(page.en_cours(), "l'installation ne se termine pas")

    @staticmethod
    def lire(chemin):
        with open(chemin, encoding="utf-8") as fichier:
            return fichier.read()

    def lancees(self):
        return self.lire(self.journal).strip().splitlines()

    def test_rien_de_coche_au_depart_et_le_bouton_attend(self):
        page = self.module.build(None)
        self.assertGreaterEqual(len(page.cases), 20)
        self.assertEqual(page.choisies(), [])
        self.assertFalse(page.bouton.isEnabled())
        self.assertEqual(page.bouton.text(), "Installer la sélection")
        page.cases["org.videolan.VLC"].setChecked(True)
        self.assertTrue(page.bouton.isEnabled())
        self.assertEqual(page.bouton.text(), "Installer la sélection (1)")

    def test_installation_de_deux_applications(self):
        page = self.module.build(None)
        page.cases["com.spotify.Client"].setChecked(True)
        page.cases["org.videolan.VLC"].setChecked(True)
        page.installer()
        self.assertFalse(page.bouton.isEnabled())  # pas de seconde installation en même temps
        self.attendre(page)
        ligne = self.lancees()[0]
        self.assertTrue(ligne.startswith("install --system --noninteractive --assumeyes flathub "))
        self.assertEqual(sorted(ligne.split()[-2:]), ["com.spotify.Client", "org.videolan.VLC"])
        self.assertIn("Terminé : 2 application(s) installée(s)", page.statut.text())
        for ident in ("com.spotify.Client", "org.videolan.VLC"):
            self.assertEqual(page.etiquettes[ident].text(), "✓ Installée")
            self.assertFalse(page.cases[ident].isEnabled())
            self.assertFalse(page.cases[ident].isChecked())
        self.assertEqual(page.choisies(), [])
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            page.resize(1040, 1300)
            page.show()
            self.app.processEvents()
            page.grab().save(os.path.join(CAPTURES, "applications.png"))

    def test_une_application_deja_installee_n_est_pas_reproposee(self):
        self.deja = {"org.videolan.VLC"}
        page = self.module.build(None)
        self.assertEqual(page.etiquettes["org.videolan.VLC"].text(), "✓ Installée")
        self.assertFalse(page.cases["org.videolan.VLC"].isEnabled())
        self.assertTrue(page.cases["org.gimp.GIMP"].isEnabled())

    def test_echec_faute_de_droits(self):
        os.environ["FAUX_CODE"] = "1"
        os.environ["FAUX_ERREUR"] = "error: Flatpak system operation Deploy not allowed for user"
        page = self.module.build(None)
        page.cases["org.videolan.VLC"].setChecked(True)
        page.installer()
        self.attendre(page)
        self.assertIn("administrateur", page.statut.text())
        self.assertIn("s'est arrêtée", page.statut.text())
        self.assertTrue(page.cases["org.videolan.VLC"].isEnabled())  # on peut réessayer
        self.assertTrue(page.bouton.isEnabled())
        self.assertFalse(page.progression.isVisible())

    def test_flatpak_introuvable(self):
        os.environ["BINIXX_FLATPAK"] = "/inexistant/flatpak"
        page = self.module.build(None)
        page.cases["org.videolan.VLC"].setChecked(True)
        page.installer()
        self.attendre(page)
        self.assertIn("n'a pas pu démarrer", page.statut.text())
        self.assertTrue(page.bouton.isEnabled())

    def test_rien_a_installer_ne_lance_rien(self):
        page = self.module.build(None)
        page.installer()
        self.assertEqual(self.lancees(), [])
        self.assertIn("aucune application", page.statut.text())

    def test_l_accueil_renvoie_vers_la_page(self):
        from binixx_centre.pages import accueil
        appels = []
        centre = type("Centre", (), {"show_page": lambda self, cle: appels.append(cle)})()
        carte = next(c for c in accueil.CARTES if c[2] == "Choisir mes applications")
        carte[3](centre)
        self.assertEqual(appels, ["applications"])

    def test_chaque_ligne_dit_la_licence(self):
        from PySide6.QtWidgets import QLabel
        page = self.module.build(None)
        textes = " ".join(label.text() for label in page.findChildren(QLabel))
        self.assertIn("Propriétaire", textes)
        self.assertIn("Libre · GPL-2.0+", textes)  # VLC
        self.assertIn("Remplace : Adobe Photoshop", textes)


if __name__ == "__main__":
    unittest.main()
