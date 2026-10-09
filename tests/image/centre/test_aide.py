"""Tests de la page Aide : rapport de diagnostic et remise à zéro du bureau.

python3 -m unittest discover tests/image/centre   (la partie Qt est ignorée sans PySide6)
"""

import os
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
LIBEXEC = os.environ.get("BINIXX_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/binixx"))
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


def script(nom, *args, env=None):
    return subprocess.run([os.path.join(LIBEXEC, nom), *args], capture_output=True, text=True, timeout=120,
                          env={**os.environ, **(env or {})}, check=False)


class Diagnostic(unittest.TestCase):
    def test_le_rapport_est_complet_et_sans_secret(self):
        fini = script("binixx-diagnostic")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        for titre in ("Rapport de diagnostic BinixX OS", "== Système ==", "== Services en échec ==",
                      "== Espace disque ==", "Fin du rapport."):
            self.assertIn(titre, fini.stdout)
        self.assertNotIn("inet ", fini.stdout)  # aucune adresse IP
        self.assertIn("== Applications : source Flathub et installation au premier démarrage ==", fini.stdout)


class DiagnosticFlathub(unittest.TestCase):
    """La section « Flathub » du rapport, avec de fausses commandes : les applications manquantes, l'état du service et la
    joignabilité de Flathub doivent se lire d'un coup d'œil, même sur un PC où il n'y a rien d'installé."""

    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        base = self.dossier.name
        self.faux = os.path.join(base, "bin")
        self.flatpaks = os.path.join(base, "flatpaks")
        self.etat = os.path.join(base, "etat")
        for d in (self.faux, os.path.join(self.flatpaks, "system-flatpaks.d"), self.etat):
            os.makedirs(d)
        with open(os.path.join(self.flatpaks, "system-flatpaks.list"), "w", encoding="utf-8") as f:
            f.write("# applications\norg.kde.okular  # lecteur PDF\norg.kde.gwenview\n\n")
        with open(os.path.join(self.flatpaks, "system-flatpaks.d", "entreprise.list"), "w", encoding="utf-8") as f:
            f.write("org.example.Metier\n")
        self.installees = os.path.join(base, "installees")
        with open(self.installees, "w", encoding="utf-8") as f:
            f.write("org.kde.okular\n")
        self.ecrire("flatpak", f'''case "$1" in
    remotes) printf 'flathub\\tsystem\\n' ;;
    list) cat "{self.installees}" ;;
esac''')
        self.ecrire("systemctl", 'printf "ActiveState=failed\\nResult=exit-code\\n"')
        self.ecrire("journalctl", 'printf "flatpak install : erreur de test\\n"')

    def tearDown(self):
        self.dossier.cleanup()

    def ecrire(self, nom, corps):
        chemin = os.path.join(self.faux, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n" + corps + "\n")
        os.chmod(chemin, 0o755)

    def rapport(self, code_http):
        self.ecrire("curl", f"printf '{code_http}'")
        env = {"PATH": self.faux + os.pathsep + os.environ["PATH"], "BINIXX_FLATPAKS_DIR": self.flatpaks,
               "BINIXX_ETAT_DIR": self.etat}
        fini = script("binixx-diagnostic", env=env)
        self.assertEqual(fini.returncode, 0, fini.stderr)
        debut = fini.stdout.index("== Applications : source Flathub")
        return fini.stdout[debut:].split("\n== ", 2)[0]

    def test_les_applications_manquantes_sont_nommees_listes_de_l_entreprise_comprises(self):
        section = self.rapport("200")
        self.assertIn("Applications prévues d'office : 3 ; manquantes : 2 (org.example.Metier org.kde.gwenview)", section)
        self.assertIn("flathub", section)

    def test_installation_pas_terminee_puis_terminee(self):
        self.assertIn("Installation des applications prévues : pas encore terminée", self.rapport("200"))
        with open(os.path.join(self.etat, "flatpaks.sha256"), "w", encoding="utf-8") as f:
            f.write("x\n")
        self.assertIn("Installation des applications prévues : terminée (le ", self.rapport("200"))

    def test_etat_du_service_et_journal(self):
        section = self.rapport("200")
        self.assertIn("ActiveState=failed", section)
        self.assertIn("flatpak install : erreur de test", section)

    def test_flathub_joignable_ou_non(self):
        self.assertIn("Flathub joignable depuis ce PC : oui", self.rapport("200"))
        self.assertIn("Flathub joignable depuis ce PC : non (code 000)", self.rapport("000"))

    def test_sans_catalogue_le_rapport_le_dit(self):
        # sur la machine de test il n'y a pas de catalogue Flathub : le rapport l'écrit au lieu de se taire
        if not os.path.exists("/var/lib/flatpak/appstream/flathub"):
            self.assertIn("aucun : Discover ne trouvera pas les applications de Flathub", self.rapport("200"))

    def test_sans_adresse_ip_ni_adresse_de_site(self):
        section = self.rapport("200")
        self.assertNotIn("inet ", section)
        self.assertNotIn("https://", section)


class Reinitialisation(unittest.TestCase):
    def setUp(self):
        self.maison = tempfile.TemporaryDirectory()
        self.config = os.path.join(self.maison.name, ".config")
        os.makedirs(os.path.join(self.config, "kdedefaults"))
        for nom in ("plasmashellrc", "kdeglobals", "kxkbrc", "plasma-localerc", "kdedefaults/package"):
            with open(os.path.join(self.config, nom), "w", encoding="utf-8") as f:
                f.write("x")
        self.env = {"HOME": self.maison.name, "XDG_CONFIG_HOME": self.config,
                    "XDG_STATE_HOME": os.path.join(self.maison.name, ".local/state"),
                    "XDG_DATA_HOME": os.path.join(self.maison.name, ".local/share")}

    def tearDown(self):
        self.maison.cleanup()

    def reste(self):
        return set(os.listdir(self.config))

    def test_sans_demande_rien_ne_bouge(self):
        script("binixx-reinitialiser-bureau", "appliquer", env=self.env)
        self.assertIn("plasmashellrc", self.reste())

    def test_programmer_puis_appliquer(self):
        script("binixx-reinitialiser-bureau", "programmer", env=self.env)
        self.assertEqual(script("binixx-reinitialiser-bureau", "etat", env=self.env).stdout.strip(), "programmee")
        self.assertIn("plasmashellrc", self.reste())  # rien tant que la session n'est pas fermée
        script("binixx-reinitialiser-bureau", "appliquer", env=self.env)
        self.assertEqual(self.reste(), {"kxkbrc", "plasma-localerc"})  # clavier et langue conservés
        sauvegardes = os.path.join(self.maison.name, ".local/share/binixx/sauvegardes")
        (dossier,) = os.listdir(sauvegardes)
        contenu = set(os.listdir(os.path.join(sauvegardes, dossier)))
        self.assertTrue({"plasmashellrc", "kdeglobals", "kdedefaults", "LISEZMOI.txt"} <= contenu)
        self.assertEqual(script("binixx-reinitialiser-bureau", "etat", env=self.env).stdout.strip(), "aucune")

    def test_annuler(self):
        script("binixx-reinitialiser-bureau", "programmer", env=self.env)
        script("binixx-reinitialiser-bureau", "annuler", env=self.env)
        script("binixx-reinitialiser-bureau", "appliquer", env=self.env)
        self.assertIn("plasmashellrc", self.reste())


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageAide(unittest.TestCase):
    def test_creer_un_rapport(self):
        from binixx_centre import launch
        from binixx_centre.pages import aide

        app = QApplication.instance() or QApplication(sys.argv[:1])
        with tempfile.TemporaryDirectory() as maison:
            ancien_home, os.environ["HOME"] = os.environ.get("HOME"), maison
            aide.DIAGNOSTIC = os.path.join(LIBEXEC, "binixx-diagnostic")
            ouvertures = []
            ancienne_ouverture, launch.open_app = launch.open_app, ouvertures.append
            try:
                chemin = aide.build(None).creer_rapport()
            finally:
                launch.open_app = ancienne_ouverture  # sans cela, les tests suivants n'ouvrent plus rien
                os.environ["HOME"] = ancien_home
            self.assertTrue(chemin.startswith(os.path.join(maison, "Documents", "Rapport-BinixX-OS-")))
            with open(chemin, encoding="utf-8") as f:
                self.assertIn("Fin du rapport.", f.read())
            self.assertEqual(ouvertures, ["org.kde.dolphin"])
        del app


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class RetourALaVersionPrecedente(unittest.TestCase):
    """« Depuis la dernière mise à jour, quelque chose ne marche plus » mène à la page Mises à jour, pas à Cockpit."""

    def test_le_cas_d_aide_ouvre_la_page_mises_a_jour(self):
        from PySide6.QtWidgets import QPushButton
        from binixx_centre.pages import aide, mises_a_jour

        app = QApplication.instance() or QApplication(sys.argv[:1])
        ouvertes = []
        centre = type("Centre", (), {"show_page": lambda self, cle: ouvertes.append(cle)})()
        page = aide.build(centre)
        bouton = next(b for b in page.findChildren(QPushButton) if b.text() == "Ouvrir les mises à jour")
        bouton.click()
        self.assertEqual(ouvertes, [mises_a_jour.KEY])
        self.assertEqual(mises_a_jour.KEY, "mises_a_jour")
        del app

    def test_le_texte_dit_ou_cliquer_et_ne_parle_plus_de_cockpit(self):
        from binixx_centre.pages import aide

        titre, texte, bouton, action = next(p for p in aide.PROBLEMES if p[3] == "retour")
        self.assertIn("Paramètres → Mises à jour du système → « Revenir en arrière »", texte)
        self.assertEqual(bouton, "Ouvrir les mises à jour")
        for p in aide.PROBLEMES:
            self.assertNotIn("9090", " ".join(p))
            self.assertNotIn("Administration du PC", p[1] if p[3] == "retour" else "")


if __name__ == "__main__":
    unittest.main()
