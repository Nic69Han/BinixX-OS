"""Tests de « Réparer le système » : comparaison de /etc avec l'image, remise à l'origine, annulation, page.

python3 -m unittest discover -s tests/image/centre -p 'test_reparer.py'   (la partie Qt est ignorée sans PySide6)
Les arborescences sont fabriquées dans un dossier temporaire : le /etc du poste n'est jamais touché.
"""

import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
LIBEXEC = os.environ.get("BINIXX_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/binixx"))
OUTIL = os.path.join(LIBEXEC, "binixx-reparer-systeme")
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


def charger_outil():
    chargeur = importlib.machinery.SourceFileLoader("reparer_systeme", OUTIL)
    spec = importlib.util.spec_from_loader("reparer_systeme", chargeur)
    module = importlib.util.module_from_spec(spec)
    chargeur.exec_module(module)
    return module


R = charger_outil()


def ecrire(racine, relatif, contenu="x\n", mode=0o644):
    chemin = os.path.join(racine, relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write(contenu)
    os.chmod(chemin, mode)
    return chemin


def lire(racine, relatif):
    with open(os.path.join(racine, relatif), encoding="utf-8") as fichier:
        return fichier.read()


class Arbres(unittest.TestCase):
    """Une image (defaut) et un /etc (etc) qui en dérive, avec des changements de toutes sortes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.defaut = os.path.join(self.tmp.name, "usr-etc")
        self.etc = os.path.join(self.tmp.name, "etc")
        self.sauv = os.path.join(self.tmp.name, "sauvegardes")
        for racine in (self.defaut,):
            ecrire(racine, "sddm.conf.d/10-binixx.conf", "[Theme]\nCurrent=binixx\n")
            ecrire(racine, "xdg/plasma-welcomerc", "[General]\nLastSeenVersion=99.0.0\n")
            ecrire(racine, "sysctl.d/10-binixx.conf", "kernel.dmesg_restrict=1\n")
            ecrire(racine, "profile.d/binixx.sh", "export A=1\n", 0o755)
            ecrire(racine, "passwd", "root:x:0:0\n")
            ecrire(racine, "ssh/sshd_config", "PermitRootLogin no\n")
        os.makedirs(os.path.join(self.defaut, "systemd/system/multi-user.target.wants"))
        shutil.copytree(self.defaut, self.etc, symlinks=True)
        # changements de l'utilisateur
        ecrire(self.etc, "sddm.conf.d/10-binixx.conf", "[Theme]\nCurrent=cassé\n")          # modifié
        os.remove(os.path.join(self.etc, "xdg/plasma-welcomerc"))                          # supprimé
        ecrire(self.etc, "sddm.conf.d/zz-essai.conf", "[General]\nSession=trop-bizarre\n")  # ajouté
        ecrire(self.etc, "sysctl.d/99-essai.conf", "vm.swappiness=0\n")                    # ajouté
        os.chmod(os.path.join(self.etc, "profile.d/binixx.sh"), 0o644)                      # droits changés
        # changements qu'il ne faut jamais proposer
        ecrire(self.etc, "passwd", "root:x:0:0\nmoi:x:1000:1000\n")
        ecrire(self.etc, "ssh/ssh_host_rsa_key", "secret\n", 0o600)
        ecrire(self.etc, "hostname", "mon-pc\n")
        os.symlink("../x.service", os.path.join(self.etc, "systemd/system/multi-user.target.wants/x.service"))

    def tearDown(self):
        self.tmp.cleanup()

    def differences(self):
        return {d["chemin"]: d["etat"] for d in R.differences(self.etc, self.defaut)}

    def restaurer(self, chemins, horodatage="20261002-120000"):
        return R.restaurer(chemins, self.etc, self.defaut, self.sauv, horodatage)

    def annuler(self, date=None):
        return R.annuler(date, self.etc, self.sauv)


class Comparaison(Arbres):
    def test_seuls_les_reglages_modifies_sont_proposes(self):
        self.assertEqual(self.differences(), {
            "sddm.conf.d/10-binixx.conf": "modifie",
            "sddm.conf.d/zz-essai.conf": "ajoute",
            "xdg/plasma-welcomerc": "supprime",
            "sysctl.d/99-essai.conf": "ajoute",
            "profile.d/binixx.sh": "modifie",  # seuls les droits ont changé
        })

    def test_comptes_cles_reseau_et_services_ne_sont_jamais_proposes(self):
        propose = set(self.differences())
        for interdit in ("passwd", "ssh/ssh_host_rsa_key", "hostname", "systemd/system/multi-user.target.wants/x.service"):
            self.assertNotIn(interdit, propose)

    def test_categories_lisibles(self):
        parcat = {d["chemin"]: d["categorie"] for d in R.differences(self.etc, self.defaut)}
        self.assertEqual(parcat["sddm.conf.d/10-binixx.conf"], "Écran de connexion")
        self.assertEqual(parcat["sysctl.d/99-essai.conf"], "Réglages du noyau")

    def test_rien_ne_change_rien_a_proposer(self):
        shutil.rmtree(self.etc)
        shutil.copytree(self.defaut, self.etc, symlinks=True)
        self.assertEqual(R.differences(self.etc, self.defaut), [])

    def test_les_liens_ne_sont_jamais_proposes(self):
        # un lien porte l'état du système (service activé, cible de démarrage) : le retirer serait dangereux
        os.symlink("a", os.path.join(self.defaut, "xdg/lien"))
        os.symlink("a", os.path.join(self.etc, "xdg/lien"))
        os.remove(os.path.join(self.etc, "xdg/lien"))
        os.symlink("b", os.path.join(self.etc, "xdg/lien"))
        os.symlink("/usr/lib/systemd/system/graphical.target", os.path.join(self.etc, "systemd/system/default.target"))
        os.symlink("../x", os.path.join(self.etc, "sysctl.d/lien-ajoute.conf"))
        propose = self.differences()
        for lien in ("xdg/lien", "systemd/system/default.target", "sysctl.d/lien-ajoute.conf"):
            self.assertNotIn(lien, propose)

    def test_ce_que_le_systeme_ecrit_lui_meme_n_est_pas_propose(self):
        # constaté sur un poste neuf : le système et ses outils écrivent ces fichiers, ce ne sont pas des erreurs
        for relatif in ("systemd/system.control/user.slice.d/50-MemoryMin.conf",
                        "systemd/system.attached/x.conf", "X11/xorg.conf.d/00-keyboard.conf", "modprobe.d/tuned.conf",
                        "systemd/system/default.target"):
            ecrire(self.etc, relatif, "écrit par le système\n")
        self.assertEqual(self.differences(), {
            "sddm.conf.d/10-binixx.conf": "modifie", "sddm.conf.d/zz-essai.conf": "ajoute",
            "xdg/plasma-welcomerc": "supprime", "sysctl.d/99-essai.conf": "ajoute", "profile.d/binixx.sh": "modifie"})
        code, _ = self.restaurer(["X11/xorg.conf.d/00-keyboard.conf"])
        self.assertEqual(code, 2)

    def test_dossier_d_un_cote_fichier_de_l_autre_est_ignore(self):
        os.makedirs(os.path.join(self.etc, "xdg/curieux"))
        ecrire(self.defaut, "xdg/curieux", "fichier dans l'image\n")
        self.assertNotIn("xdg/curieux", self.differences())

    def test_image_absente_on_ne_propose_rien(self):
        # sans /usr/etc, tout /etc paraîtrait « ajouté » : l'outil refuse au lieu de proposer de tout retirer
        absente = os.path.join(self.tmp.name, "rien")
        with self.assertRaises(OSError):
            R.differences(self.etc, absente)
        code, message = R.restaurer(["sddm.conf.d/zz-essai.conf"], self.etc, absente, self.sauv)
        self.assertEqual(code, 5)
        self.assertTrue(os.path.exists(os.path.join(self.etc, "sddm.conf.d/zz-essai.conf")))


class Reparation(Arbres):
    def test_remise_a_l_origine_des_trois_sortes_de_changement(self):
        code, resultat = self.restaurer(["sddm.conf.d/10-binixx.conf", "xdg/plasma-welcomerc",
                                         "sddm.conf.d/zz-essai.conf", "profile.d/binixx.sh"])
        self.assertEqual(code, 0, resultat)
        self.assertEqual(lire(self.etc, "sddm.conf.d/10-binixx.conf"), "[Theme]\nCurrent=binixx\n")
        self.assertEqual(lire(self.etc, "xdg/plasma-welcomerc"), "[General]\nLastSeenVersion=99.0.0\n")
        self.assertFalse(os.path.exists(os.path.join(self.etc, "sddm.conf.d/zz-essai.conf")))
        self.assertEqual(os.stat(os.path.join(self.etc, "profile.d/binixx.sh")).st_mode & 0o777, 0o755)
        # ce qui n'a pas été choisi reste comme il est
        self.assertTrue(os.path.exists(os.path.join(self.etc, "sysctl.d/99-essai.conf")))
        self.assertEqual(set(self.differences()), {"sysctl.d/99-essai.conf"})

    def test_la_version_remplacee_est_sauvegardee(self):
        self.restaurer(["sddm.conf.d/10-binixx.conf", "sddm.conf.d/zz-essai.conf"])
        dossier = os.path.join(self.sauv, "20261002-120000")
        self.assertEqual(lire(dossier, "etc/sddm.conf.d/10-binixx.conf"), "[Theme]\nCurrent=cassé\n")
        self.assertEqual(lire(dossier, "etc/sddm.conf.d/zz-essai.conf"), "[General]\nSession=trop-bizarre\n")
        with open(os.path.join(dossier, "MANIFESTE.json"), encoding="utf-8") as fichier:
            faits = {f["chemin"]: f["avant"] for f in json.load(fichier)["faits"]}
        self.assertEqual(faits, {"sddm.conf.d/10-binixx.conf": "present", "sddm.conf.d/zz-essai.conf": "present"})
        self.assertEqual(os.stat(self.sauv).st_mode & 0o777, 0o700)

    def test_fichier_non_reparable_rien_n_est_modifie(self):
        avant = lire(self.etc, "sddm.conf.d/10-binixx.conf")
        for intrus in ("passwd", "../etc/passwd", "/etc/passwd", "xdg/../passwd", "ssh/ssh_host_rsa_key",
                       "n-existe-pas", "sysctl.d/10-binixx.conf", ""):
            with self.subTest(intrus=intrus):
                code, message = self.restaurer(["sddm.conf.d/10-binixx.conf", intrus])
                self.assertEqual(code, 2)
                self.assertEqual(lire(self.etc, "sddm.conf.d/10-binixx.conf"), avant)
                self.assertFalse(os.path.exists(self.sauv), "aucune sauvegarde pour une demande refusée")
        self.assertEqual(self.restaurer([])[0], 2)

    def test_un_lien_dans_etc_ne_permet_pas_de_sortir_du_dossier(self):
        cible = os.path.join(self.tmp.name, "ailleurs")
        os.makedirs(cible)
        os.symlink(cible, os.path.join(self.etc, "xdg/evasion"))
        ecrire(cible, "fichier", "hors de /etc\n")
        code, _ = self.restaurer(["xdg/evasion/fichier"])
        self.assertEqual(code, 2)
        self.assertEqual(lire(cible, "fichier"), "hors de /etc\n")

    def test_annuler_retrouve_la_version_d_avant(self):
        self.restaurer(["sddm.conf.d/10-binixx.conf", "xdg/plasma-welcomerc", "sddm.conf.d/zz-essai.conf"])
        code, resultat = self.annuler()
        self.assertEqual(code, 0, resultat)
        self.assertEqual(lire(self.etc, "sddm.conf.d/10-binixx.conf"), "[Theme]\nCurrent=cassé\n")
        self.assertFalse(os.path.exists(os.path.join(self.etc, "xdg/plasma-welcomerc")))  # il était absent avant
        self.assertEqual(lire(self.etc, "sddm.conf.d/zz-essai.conf"), "[General]\nSession=trop-bizarre\n")
        self.assertEqual(self.annuler()[0], 2, "une réparation ne s'annule qu'une fois")
        self.assertTrue(R.liste_sauvegardes(self.sauv)[0]["annulee"])

    def test_annuler_cible_la_derniere_ou_celle_demandee(self):
        self.restaurer(["sddm.conf.d/10-binixx.conf"], "20261002-100000")
        self.restaurer(["sysctl.d/99-essai.conf"], "20261002-110000")
        self.assertEqual(self.annuler("20261002-100000")[1]["annulee"], "20261002-100000")
        self.assertEqual(self.annuler()[1]["annulee"], "20261002-110000")
        self.assertEqual(self.annuler("20269999-000000")[0], 2)

    def test_deux_reparations_la_meme_seconde(self):
        self.restaurer(["sddm.conf.d/10-binixx.conf"], "20261002-120000")
        self.restaurer(["sysctl.d/99-essai.conf"], "20261002-120000")
        self.assertEqual([s["date"] for s in R.liste_sauvegardes(self.sauv)], ["20261002-120000", "20261002-120000+2"])

    def test_on_ne_garde_que_les_dernieres_reparations(self):
        ancien, R.CONSERVEES = R.CONSERVEES, 2
        try:
            for heure, chemin in (("10", "sddm.conf.d/10-binixx.conf"), ("11", "sysctl.d/99-essai.conf"),
                                  ("12", "profile.d/binixx.sh")):
                self.restaurer([chemin], f"20261002-{heure}0000")
        finally:
            R.CONSERVEES = ancien
        self.assertEqual([s["date"] for s in R.liste_sauvegardes(self.sauv)], ["20261002-110000", "20261002-120000"])


class Outil(unittest.TestCase):
    def lancer(self, *args):
        return subprocess.run([OUTIL, *args], capture_output=True, text=True, timeout=60, check=False)

    def test_liste_en_json_et_en_texte(self):
        # /usr/etc n'existe que sur un système installé (pas dans le conteneur de l'image, ni sur un poste de dev)
        attendu = 0 if os.path.isdir("/usr/etc") else 5
        fini = self.lancer("liste")
        self.assertEqual(fini.returncode, attendu, fini.stderr)
        if attendu == 0:
            self.assertIsInstance(json.loads(fini.stdout), list)
        self.assertEqual(self.lancer("liste", "--texte").returncode, attendu)

    def test_appel_incorrect(self):
        for args in ((), ("liste", "--autre"), ("n-importe-quoi",), ("sauvegardes", "x")):
            with self.subTest(args=args):
                self.assertEqual(self.lancer(*args).returncode, 2)

    @unittest.skipIf(os.geteuid() == 0, "le refus ne se produit que sans les droits d'administrateur")
    def test_restaurer_demande_les_droits_d_administrateur(self):
        fini = self.lancer("restaurer", "xdg/kdeglobals")
        self.assertEqual(fini.returncode, 2)
        self.assertIn("pkexec", fini.stderr)

    @unittest.skipUnless(os.geteuid() == 0, "il faut les droits d'administrateur")
    def test_un_fichier_quelconque_est_refuse(self):
        fini = self.lancer("restaurer", "passwd")
        if os.path.isdir("/usr/etc"):
            self.assertEqual(fini.returncode, 2)
            self.assertIn("ne peut pas être réparé", fini.stderr)
        else:  # conteneur ou poste de développement : pas d'image de référence, l'outil ne fait rien
            self.assertEqual(fini.returncode, 5)
            self.assertIn("/usr/etc est absent", fini.stderr)


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from binixx_centre import launch, theme
        from binixx_centre.pages import aide
        cls.launch, cls.aide = launch, aide
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        self.appels = []
        self.ancien = self.launch.run
        self.reponses = {"sauvegardes": (0, "[]")}
        self.launch.run = self.faux_run

    def tearDown(self):
        self.launch.run = self.ancien

    def faux_run(self, argv, timeout=120):
        self.appels.append(argv)
        cle = "pkexec" if argv[0] == "pkexec" else argv[1]
        return self.reponses[cle]

    CHANGEMENTS = [{"chemin": "sddm.conf.d/10-binixx.conf", "etat": "modifie", "categorie": "Écran de connexion"},
                   {"chemin": "sysctl.d/99-essai.conf", "etat": "ajoute", "categorie": "Réglages du noyau"}]

    def page(self):
        page = self.aide.build(None)
        page.messages = []
        page.informer = lambda titre, texte: page.messages.append((titre, texte))
        page.choisir_reparations = lambda changements, peut_annuler=False: page.choix
        page.choix = None
        return page

    def test_une_carte_dans_les_cas_frequents(self):
        titres = [p[0] for p in self.aide.PROBLEMES]
        self.assertTrue(any("réglage" in t.lower() and "système" in t.lower() for t in titres), titres)
        self.assertIn("reparer", {p[3] for p in self.aide.PROBLEMES})

    def test_aucun_changement_on_le_dit(self):
        self.reponses["liste"] = (0, "[]")
        page = self.page()
        page.reparer_systeme()
        self.assertEqual(len(page.messages), 1)
        self.assertIn("aucun", page.messages[0][1].lower())
        self.assertEqual([a for a in self.appels if a[0] == "pkexec"], [])

    def test_la_selection_part_vers_pkexec_avec_des_chemins_de_l_outil(self):
        self.reponses["liste"] = (0, json.dumps(self.CHANGEMENTS))
        self.reponses["pkexec"] = (0, json.dumps({"sauvegarde": "20261002-120000", "faits": []}))
        page = self.page()
        page.choix = ["sddm.conf.d/10-binixx.conf"]
        page.reparer_systeme()
        pkexec = [a for a in self.appels if a[0] == "pkexec"]
        self.assertEqual(pkexec, [["pkexec", self.aide.REPARER, "restaurer", "sddm.conf.d/10-binixx.conf"]])
        self.assertIn("redémarr", page.messages[-1][1].lower())

    def test_rien_de_coche_rien_ne_part(self):
        self.reponses["liste"] = (0, json.dumps(self.CHANGEMENTS))
        page = self.page()
        page.choix = []
        page.reparer_systeme()
        self.assertEqual([a for a in self.appels if a[0] == "pkexec"], [])

    def test_echec_message_clair_et_liste_illisible(self):
        self.reponses["liste"] = (0, "pas du json")
        page = self.page()
        page.reparer_systeme()
        self.assertIn("lire", page.messages[-1][1].lower())

    def test_boite_de_choix(self):
        dialogue = self.aide.ReparationDialog(None, self.CHANGEMENTS)
        self.assertEqual(dialogue.selection(), [])  # rien n'est coché d'avance : c'est à l'utilisateur de choisir
        dialogue.liste.item(0).setCheckState(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.Checked)
        self.assertEqual(dialogue.selection(), ["sddm.conf.d/10-binixx.conf"])
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            dialogue.adjustSize()
            dialogue.show()
            self.app.processEvents()
            dialogue.grab().save(os.path.join(CAPTURES, "reparer.png"))


if __name__ == "__main__":
    unittest.main()
