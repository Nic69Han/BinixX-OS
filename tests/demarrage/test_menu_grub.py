"""Tests du script qui rend le menu GRUB discret (binixx-menu-grub) : il écrit user.cfg, sans jamais toucher à celui d'un autre."""

import os
import shutil
import subprocess
import tempfile
import unittest

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SCRIPT = os.path.join(RACINE, "system_files", "usr", "libexec", "binixx", "binixx-menu-grub")
UNITE = os.path.join(RACINE, "system_files", "usr", "lib", "systemd", "system", "binixx-menu-grub.service")
KARGS = os.path.join(RACINE, "system_files", "usr", "lib", "bootc", "kargs.d", "10-binixx-demarrage.toml")
MARQUE = "# BinixX OS : menu de démarrage discret"


def lancer(dossier):
    env = dict(os.environ, BINIXX_GRUB_DIR=dossier)
    return subprocess.run(["bash", SCRIPT], env=env, capture_output=True, text=True, check=False)


class MenuGrubTest(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.fichier = os.path.join(self.dossier, "user.cfg")

    def tearDown(self):
        shutil.rmtree(self.dossier, ignore_errors=True)

    def lire(self):
        with open(self.fichier, encoding="utf-8") as f:
            return f.read()

    def test_ecrit_user_cfg_avec_la_marque_en_premiere_ligne(self):
        resultat = lancer(self.dossier)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(self.lire().startswith(MARQUE))

    def test_le_menu_n_est_cache_que_si_le_demarrage_precedent_a_reussi(self):
        lancer(self.dossier)
        texte = self.lire()
        self.assertIn('if [ "${boot_success}" = "1" ]; then', texte)
        self.assertIn("set timeout_style=hidden", texte)
        self.assertIn("set timeout=1", texte)
        # hidden et timeout=1 sont dans la branche « réussi », jamais dans la branche « sinon »
        reussi, _, sinon = texte.partition("else")
        self.assertIn("timeout_style=hidden", reussi)
        self.assertNotIn("timeout_style", sinon)
        self.assertNotIn("timeout=", sinon)

    def test_le_menu_n_est_jamais_cache_pour_toujours(self):
        # Échap doit pouvoir l'afficher : on attend une seconde au lieu de partir tout de suite (timeout=0)
        lancer(self.dossier)
        self.assertNotIn("timeout=0", self.lire())

    def test_laisse_une_trace_lisible_depuis_le_systeme(self):
        lancer(self.dossier)
        texte = self.lire()
        self.assertIn("set binixx_menu=cache", texte)
        self.assertIn("set binixx_menu=visible", texte)
        self.assertIn("save_env binixx_menu", texte)

    def test_ne_touche_pas_au_user_cfg_d_un_autre(self):
        with open(self.fichier, "w", encoding="utf-8") as f:
            f.write("# mon réglage\nset timeout=10\n")
        resultat = lancer(self.dossier)
        self.assertEqual(resultat.returncode, 0)
        self.assertEqual(self.lire(), "# mon réglage\nset timeout=10\n")
        self.assertIn("laissé tel quel", resultat.stdout)

    def test_remplace_une_ancienne_version_de_son_propre_fichier(self):
        with open(SCRIPT, encoding="utf-8") as script:
            marque = next(ligne for ligne in script if ligne.startswith("marque=")).split("'")[1]
        with open(self.fichier, "w", encoding="utf-8") as f:
            f.write(marque + "\nancien contenu\n")
        lancer(self.dossier)
        self.assertNotIn("ancien contenu", self.lire())
        self.assertIn("timeout_style=hidden", self.lire())

    def test_ne_reecrit_pas_un_fichier_deja_a_jour(self):
        lancer(self.dossier)
        premier = os.stat(self.fichier)
        resultat = lancer(self.dossier)
        self.assertEqual(resultat.returncode, 0)
        self.assertNotIn("écrit", resultat.stdout)
        self.assertEqual(os.stat(self.fichier).st_ino, premier.st_ino)

    def test_dossier_absent_n_est_pas_une_erreur(self):
        resultat = lancer(os.path.join(self.dossier, "inexistant"))
        self.assertEqual(resultat.returncode, 0)
        self.assertIn("rien à faire", resultat.stdout)

    def test_aucun_fichier_temporaire_ne_reste(self):
        lancer(self.dossier)
        lancer(self.dossier)
        self.assertEqual(os.listdir(self.dossier), ["user.cfg"])

    def test_syntaxe_grub_valide_si_l_outil_est_present(self):
        outil = shutil.which("grub2-script-check") or shutil.which("grub-script-check")
        if outil is None:
            self.skipTest("grub-script-check absent")
        lancer(self.dossier)
        resultat = subprocess.run([outil, self.fichier], capture_output=True, text=True, check=False)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)


class UniteTest(unittest.TestCase):
    def test_le_service_lance_le_script_au_demarrage(self):
        with open(UNITE, encoding="utf-8") as f:
            texte = f.read()
        self.assertIn("ExecStart=/usr/libexec/binixx/binixx-menu-grub", texte)
        self.assertIn("WantedBy=multi-user.target", texte)
        self.assertIn("RequiresMountsFor=/boot", texte)
        self.assertIn("Type=oneshot", texte)

    def test_le_script_est_executable(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK))


class ParametresDuNoyauTest(unittest.TestCase):
    def kargs(self):
        import tomllib
        with open(KARGS, "rb") as f:
            return tomllib.load(f)["kargs"]

    def test_quiet_et_splash_vont_ensemble(self):
        kargs = self.kargs()
        self.assertIn("quiet", kargs)
        self.assertIn("splash", kargs)

    def test_systemd_montre_l_avancement_seulement_si_le_demarrage_traine_ou_echoue(self):
        kargs = self.kargs()
        self.assertIn("systemd.show_status=auto", kargs)
        self.assertIn("rd.systemd.show_status=auto", kargs)
        self.assertNotIn("systemd.show_status=false", kargs)

    def test_rien_ne_coupe_l_ecran_de_demarrage_ni_la_console_de_secours(self):
        kargs = self.kargs()
        for interdit in ("plymouth.enable=0", "rd.plymouth=0", "nosplash", "vt.global_cursor_default=0", "console=ttyS0"):
            self.assertNotIn(interdit, kargs)

    def test_aucun_parametre_ne_contient_d_espace(self):
        for karg in self.kargs():
            self.assertNotIn(" ", karg)


if __name__ == "__main__":
    unittest.main()
