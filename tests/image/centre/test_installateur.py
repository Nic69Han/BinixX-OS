"""Tests de la fenêtre « Installer une application » (installe un Flatpak sans passer par Discover).

python3 -m unittest discover -s tests/image/centre -p 'test_installateur.py'   (la partie Qt est ignorée sans PySide6)
Flatpak est remplacé par un petit script (BINIXX_FLATPAK) : rien n'est installé pour de vrai.
"""

import os
import shutil
import stat
import sys
import tempfile
import time
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
DONNEES = os.path.join(ICI, "../../../system_files/usr/share/binixx/catalogue-windows")
FICHIER = os.environ.get("BINIXX_CATALOGUE", os.path.join(DONNEES, "catalogue.tsv"))
LIBEXEC = os.environ.get("BINIXX_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/binixx"))
sys.path.insert(0, RACINE)

from binixx_centre import catalogue, launch  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

LUTRIS = "net.lutris.Lutris"

# faux flatpak : note les arguments ; « remotes » dit si flathub est configuré ; « remote-add » et « install » réussissent ou échouent
FAUX_FLATPAK = """#!/bin/sh
echo "$@" >> "$FAUX_JOURNAL"
case "$1" in
    remotes)
        [ -n "$FAUX_DEPOT" ] && echo "$FAUX_DEPOT"
        exit 0 ;;
    remote-add)
        if [ "${FAUX_CODE_AJOUT:-0}" != 0 ]; then echo "${FAUX_ERREUR_AJOUT:-error: échec simulé}" >&2; exit "$FAUX_CODE_AJOUT"; fi
        exit 0 ;;
    install)
        printf 'Installing 1/1…\\rInstalling 1/1… 45%%\\r'
        if [ "${FAUX_CODE:-0}" != 0 ]; then echo "${FAUX_ERREUR:-error: échec simulé}" >&2; exit "$FAUX_CODE"; fi
        echo 'Terminé.'
        exit 0 ;;
esac
exit 0
"""


class Nom(unittest.TestCase):
    def test_le_nom_vient_du_catalogue(self):
        from binixx_centre import installateur
        self.assertEqual(installateur.nom_de(LUTRIS, catalogue.charger(FICHIER)), "Lutris")

    def test_a_defaut_l_identifiant(self):
        from binixx_centre import installateur
        self.assertEqual(installateur.nom_de("org.exemple.Inconnu", catalogue.charger(FICHIER)), "org.exemple.Inconnu")


class Lancement(unittest.TestCase):
    def setUp(self):
        self.appels = []
        self.ancien = launch._start
        launch._start = lambda argv: self.appels.append(argv) or True
        self.addCleanup(lambda: setattr(launch, "_start", self.ancien))

    def test_un_identifiant_flatpak_ouvre_la_fenetre_d_installation(self):
        launch.install_application(LUTRIS)
        self.assertEqual(self.appels, [[launch.INSTALLATEUR, LUTRIS]])

    def test_ce_qui_n_est_pas_un_identifiant_passe_par_discover_jamais_par_la_fenetre(self):
        for texte in ("--user", "lutris", "net.lutris", "net.lutris.Lutris; rm -rf /", ""):
            self.appels.clear()
            launch.install_application(texte)
            self.assertNotIn(launch.INSTALLATEUR, [a[0] for a in self.appels], texte)

    def test_le_script_est_installe_et_executable(self):
        chemin = os.path.join(LIBEXEC, "binixx-installer-application")
        self.assertTrue(os.access(chemin, os.X_OK), chemin)
        with open(chemin, encoding="utf-8") as fichier:
            self.assertTrue(fichier.readline().startswith("#!/usr/bin/python3"))
        self.assertEqual(launch.INSTALLATEUR, "/usr/libexec/binixx/binixx-installer-application")


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Fenetre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from binixx_centre import installateur, theme
        cls.installateur = installateur
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.dossier, ignore_errors=True))
        self.journal = os.path.join(self.dossier, "journal")
        open(self.journal, "w").close()
        faux = os.path.join(self.dossier, "flatpak")
        with open(faux, "w") as fichier:
            fichier.write(FAUX_FLATPAK)
        os.chmod(faux, os.stat(faux).st_mode | stat.S_IXUSR)
        os.environ.update({"BINIXX_CATALOGUE": FICHIER, "BINIXX_FLATPAK": faux, "FAUX_JOURNAL": self.journal, "FAUX_DEPOT": "flathub"})
        self.addCleanup(self.nettoyer)
        self.appels = []
        self.anciens = (launch.open_discover, launch.run_flatpak)
        launch.open_discover = lambda ident="": self.appels.append(("discover", ident)) or True
        launch.run_flatpak = lambda ident: self.appels.append(("ouvrir", ident)) or True
        self.addCleanup(lambda: (setattr(launch, "open_discover", self.anciens[0]), setattr(launch, "run_flatpak", self.anciens[1])))

    @staticmethod
    def nettoyer():
        for cle in ("BINIXX_CATALOGUE", "BINIXX_FLATPAK", "FAUX_JOURNAL", "FAUX_DEPOT", "FAUX_CODE", "FAUX_ERREUR", "FAUX_CODE_AJOUT",
                    "FAUX_ERREUR_AJOUT"):
            os.environ.pop(cle, None)

    def lancer(self, identifiant=LUTRIS):
        fenetre = self.installateur.Fenetre(identifiant)
        self.addCleanup(fenetre.close)
        fenetre.demarrer()
        self.attendre(fenetre)
        return fenetre

    def attendre(self, fenetre, secondes=20):
        fin = time.time() + secondes
        while fenetre.etape != "fini" and time.time() < fin:
            self.app.processEvents()
            time.sleep(0.01)
        self.app.processEvents()
        self.assertEqual(fenetre.etape, "fini", "l'installation ne se termine pas")

    def lancees(self):
        with open(self.journal, encoding="utf-8") as fichier:
            return fichier.read().strip().splitlines()

    def visibles(self, fenetre):
        return {nom: not bouton.isHidden() for nom, bouton in
                (("discover", fenetre.discover), ("reessayer", fenetre.reessayer), ("ouvrir", fenetre.ouvrir))}

    def test_installation_quand_flathub_est_la(self):
        fenetre = self.lancer()
        self.assertEqual(self.lancees(), ["remotes --system --columns=name",
                                          f"install --system --noninteractive --assumeyes flathub {LUTRIS}"])
        self.assertTrue(fenetre.reussi)
        self.assertEqual(fenetre.statut.text(), "✓ Lutris est installé. Vous le trouverez dans le menu des applications.")
        self.assertEqual(self.visibles(fenetre), {"discover": False, "reessayer": False, "ouvrir": True})
        self.assertEqual(fenetre.fermer.text(), "Fermer")
        self.assertTrue(fenetre.progression.isHidden())

    def test_la_source_flathub_est_ajoutee_si_elle_manque(self):
        os.environ["FAUX_DEPOT"] = ""
        fenetre = self.lancer()
        lignes = self.lancees()
        self.assertEqual(lignes[1], f"remote-add --system --if-not-exists flathub {self.installateur.DEPOT}")
        self.assertTrue(lignes[2].startswith("install --system "))
        self.assertTrue(fenetre.reussi)

    def test_sans_reseau_une_phrase_dit_pourquoi_et_on_peut_reessayer(self):
        os.environ["FAUX_CODE"] = "1"
        os.environ["FAUX_ERREUR"] = "error: Unable to load summary from remote flathub: Could not resolve host: dl.flathub.org"
        fenetre = self.lancer()
        self.assertFalse(fenetre.reussi)
        self.assertIn("La connexion à Flathub a échoué", fenetre.statut.text())
        self.assertIn("L'installation s'est arrêtée", fenetre.statut.text())
        self.assertEqual(self.visibles(fenetre), {"discover": True, "reessayer": True, "ouvrir": False})
        # le réseau revient : « Réessayer » installe
        del os.environ["FAUX_CODE"]
        fenetre.reessayer.click()
        self.attendre(fenetre)
        self.assertTrue(fenetre.reussi)
        self.assertEqual(self.visibles(fenetre), {"discover": False, "reessayer": False, "ouvrir": True})

    def test_sans_droits_d_administrateur(self):
        os.environ["FAUX_CODE"] = "1"
        os.environ["FAUX_ERREUR"] = "error: Flatpak system operation Deploy not allowed for user"
        fenetre = self.lancer()
        self.assertIn("administrateur", fenetre.statut.text())

    def test_l_ajout_de_la_source_qui_echoue_arrete_tout(self):
        os.environ["FAUX_DEPOT"] = ""
        os.environ["FAUX_CODE_AJOUT"] = "1"
        os.environ["FAUX_ERREUR_AJOUT"] = "error: Unable to connect to dl.flathub.org: network is unreachable"
        fenetre = self.lancer()
        self.assertFalse(fenetre.reussi)
        self.assertIn("La connexion à Flathub a échoué", fenetre.statut.text())
        self.assertFalse(any(ligne.startswith("install") for ligne in self.lancees()))

    def test_flatpak_introuvable(self):
        os.environ["BINIXX_FLATPAK"] = "/inexistant/flatpak"
        fenetre = self.lancer()
        self.assertFalse(fenetre.reussi)
        self.assertIn("n'a pas pu démarrer", fenetre.statut.text())
        self.assertEqual(self.visibles(fenetre)["reessayer"], True)

    def test_les_boutons_ouvrent_l_application_ou_discover(self):
        fenetre = self.lancer()
        fenetre.ouvrir.click()
        self.assertEqual(self.appels, [("ouvrir", LUTRIS)])
        os.environ["FAUX_CODE"] = "1"
        autre = self.lancer("com.valvesoftware.Steam")
        autre.discover.click()
        self.assertEqual(self.appels[-1], ("discover", "com.valvesoftware.Steam"))

    def test_un_identifiant_dangereux_est_refuse(self):
        with self.assertRaises(ValueError):
            self.installateur.Fenetre("--user")
        self.assertEqual(self.installateur.main(["--user"]), 2)
        self.assertEqual(self.installateur.main([]), 2)
        self.assertEqual(self.installateur.main(["a", "b"]), 2)

    def test_le_titre_porte_le_nom_connu(self):
        fenetre = self.installateur.Fenetre(LUTRIS)
        self.assertEqual(fenetre.titre.text(), "Installation de Lutris")
        self.assertEqual(fenetre.windowTitle(), "Installer Lutris")


if __name__ == "__main__":
    unittest.main()
