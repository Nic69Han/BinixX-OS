"""Tests de l'accueil de premier démarrage : il ne s'ouvre pas dans la session de l'assistant Plasma Setup, une seule fois pour
le vrai utilisateur.

python3 -m unittest discover -s tests/image/centre -p 'test_premiere_session.py'   (la partie Qt est ignorée sans PySide6)
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
sys.path.insert(0, RACINE)

from binixx_centre import premiere_session  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import PySide6  # noqa: F401
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

AUTOSTART = os.environ.get("BINIXX_AUTOSTART", os.path.join(ICI, "../../../system_files/etc/xdg/autostart/binixx-accueil.desktop"))


class SessionDeLAssistant(unittest.TestCase):
    def test_l_utilisateur_de_l_assistant_est_reconnu(self):
        self.assertTrue(premiere_session.session_de_l_assistant("plasma-setup", "/run/plasma-setup"))
        self.assertTrue(premiere_session.session_de_l_assistant("plasma-setup", "/home/autre"))

    def test_son_dossier_personnel_suffit(self):
        self.assertTrue(premiere_session.session_de_l_assistant("quelquun", "/run/plasma-setup"))
        self.assertTrue(premiere_session.session_de_l_assistant("quelquun", "/run/plasma-setup/"))
        self.assertTrue(premiere_session.session_de_l_assistant("quelquun", "/run/plasma-setup/.config"))

    def test_un_vrai_utilisateur_n_est_pas_l_assistant(self):
        self.assertFalse(premiere_session.session_de_l_assistant("alice", "/home/alice"))
        self.assertFalse(premiere_session.session_de_l_assistant("testeur", "/var/home/testeur"))

    def test_un_dossier_au_nom_voisin_n_est_pas_celui_de_l_assistant(self):
        self.assertFalse(premiere_session.session_de_l_assistant("alice", "/run/plasma-setup-autre"))
        self.assertFalse(premiere_session.session_de_l_assistant("alice", "/home/alice/run/plasma-setup"))

    def test_par_defaut_c_est_la_session_du_processus(self):
        with mock.patch("getpass.getuser", return_value="plasma-setup"):
            self.assertTrue(premiere_session.session_de_l_assistant())
        with mock.patch("getpass.getuser", return_value="alice"), mock.patch.dict(os.environ, {"HOME": "/home/alice"}):
            self.assertFalse(premiere_session.session_de_l_assistant())
        with mock.patch("getpass.getuser", return_value="alice"), mock.patch.dict(os.environ, {"HOME": "/run/plasma-setup"}):
            self.assertTrue(premiere_session.session_de_l_assistant())

    def test_un_utilisateur_introuvable_n_empeche_pas_l_accueil(self):
        with mock.patch("getpass.getuser", side_effect=KeyError("uid inconnu")), mock.patch.dict(os.environ, {"HOME": "/home/alice"}):
            self.assertFalse(premiere_session.session_de_l_assistant())


class LanceurDeLAccueil(unittest.TestCase):
    def test_l_accueil_se_lance_avec_l_option_premier_demarrage(self):
        # c'est cette option qui fait passer par session_de_l_assistant : sans elle l'accueil s'ouvrirait aussi dans Plasma Setup
        with open(AUTOSTART, encoding="utf-8") as f:
            self.assertIn("--premier-demarrage", f.read())


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Principal(unittest.TestCase):
    def lancer(self, utilisateur, maison):
        from binixx_centre import app
        with mock.patch("getpass.getuser", return_value=utilisateur), mock.patch.dict(os.environ, {"HOME": maison}), \
                mock.patch("binixx_centre.app.PREMIER_DEMARRAGE", os.path.join(maison, "accueil-vu")), \
                mock.patch("binixx_centre.app.QApplication", side_effect=AssertionError("la fenêtre ne doit pas s'ouvrir")):
            return app.main(["--premier-demarrage"]), os.path.join(maison, "accueil-vu")

    def test_dans_la_session_de_l_assistant_rien_ne_s_ouvre_et_rien_n_est_note(self):
        with tempfile.TemporaryDirectory() as dossier:
            maison = os.path.join(dossier, "run-plasma-setup")
            os.makedirs(maison)
            code, repere = self.lancer("plasma-setup", maison)
            self.assertEqual(code, 0)
            self.assertFalse(os.path.exists(repere))

    def test_apres_la_premiere_fois_rien_ne_s_ouvre(self):
        with tempfile.TemporaryDirectory() as maison:
            repere = os.path.join(maison, "accueil-vu")
            open(repere, "w", encoding="utf-8").close()
            code, _ = self.lancer("alice", maison)
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
