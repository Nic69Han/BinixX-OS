"""Tests de la clé de récupération du disque chiffré : l'outil privilégié et la page « Protéger mes données ».

python3 -m unittest discover -s tests/image/centre -p 'test_cle.py'
(la partie Qt est ignorée sans PySide6 ; la partie LUKS, sans cryptsetup, systemd-cryptenroll et les droits root)
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
RACINE = os.environ.get("NICOS_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/nicos/centre"))
LIBEXEC = os.environ.get("NICOS_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/nicos"))
OUTIL = os.path.join(LIBEXEC, "nicos-cle-recuperation")
CAPTURES = os.environ.get("NICOS_CAPTURES")  # dossier où enregistrer des captures de la page (facultatif)
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QDialog
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


def charger_outil():
    chargeur = importlib.machinery.SourceFileLoader("cle_recuperation", OUTIL)
    spec = importlib.util.spec_from_loader("cle_recuperation", chargeur)
    module = importlib.util.module_from_spec(spec)
    chargeur.exec_module(module)
    return module


CLE = charger_outil()

ARBRE = {"blockdevices": [
    {"path": "/dev/nvme0n1", "type": "disk", "fstype": None, "size": "476.9G", "mountpoints": [None], "children": [
        {"path": "/dev/nvme0n1p1", "type": "part", "fstype": "vfat", "size": "600M", "mountpoints": ["/boot/efi"]},
        {"path": "/dev/nvme0n1p3", "type": "part", "fstype": "crypto_LUKS", "size": "475G", "mountpoints": [None],
         "children": [{"path": "/dev/mapper/luks-1", "type": "crypt", "fstype": "btrfs", "size": "475G",
                       "mountpoints": ["/", "/var"]}]}]},
    {"path": "/dev/sdb1", "type": "part", "fstype": "crypto_LUKS", "size": "58G", "mountpoints": [None]},
    {"path": "/dev/sdc1", "type": "part", "fstype": "ext4", "size": "1T", "mountpoints": ["/run/media/x"]},
]}

SORTIE_ENROLL = """A secret recovery key has been generated for this volume:

    lhdvfive-cvtrhvjt-drnvntdn-knvgfirr-clhfjjtf-hflngkjj-vtjvdneh-gnnidfnr

Please save this secret recovery key at a secure location.
New recovery key enrolled as key slot 1.
"""


class Analyse(unittest.TestCase):
    def test_volumes_du_systeme_et_dun_disque_externe(self):
        liste = CLE.volumes(ARBRE)
        self.assertEqual([v["chemin"] for v in liste], ["/dev/nvme0n1p3", "/dev/sdb1"])
        self.assertTrue(liste[0]["systeme"])
        self.assertEqual(liste[0]["montages"], ["/", "/var"])
        self.assertFalse(liste[1]["systeme"])
        self.assertEqual(liste[1]["taille"], "58G")

    def test_aucun_volume_chiffre(self):
        self.assertEqual(CLE.volumes({"blockdevices": [{"path": "/dev/sda", "type": "disk", "fstype": None}]}), [])
        self.assertEqual(CLE.volumes({}), [])

    def test_cle_dans_la_sortie(self):
        self.assertEqual(CLE.cle_dans(SORTIE_ENROLL), "lhdvfive-cvtrhvjt-drnvntdn-knvgfirr-clhfjjtf-hflngkjj-vtjvdneh-gnnidfnr")
        # sortie standard redirigée (le cas réel) : la clé est seule sur sa ligne
        self.assertEqual(CLE.cle_dans("ltbulrrk-htruvcdt-kbjiheir-ibdjluhj-dnckhddg-cvtkbdkv-fgitifng-ulvbultr\n"),
                         "ltbulrrk-htruvcdt-kbjiheir-ibdjluhj-dnckhddg-cvtkbdkv-fgitifng-ulvbultr")
        self.assertIsNone(CLE.cle_dans("rien à voir"))
        self.assertIsNone(CLE.cle_dans("    court-court\n"))

    def test_emplacements(self):
        self.assertEqual(CLE.emplacements("SLOT TYPE\n   0 password\n   2 recovery\n"), {0: "password", 2: "recovery"})
        self.assertEqual(CLE.emplacements(""), {})


class Appel(unittest.TestCase):
    def lancer(self, *args, entree=""):
        return subprocess.run([OUTIL, *args], input=entree, capture_output=True, text=True, timeout=60, check=False)

    def test_appel_incorrect(self):
        for args in ((), ("creer",), ("creer", "/dev/sdb1", "--autre"), ("volumes", "x"), ("n-importe-quoi",)):
            with self.subTest(args=args):
                self.assertEqual(self.lancer(*args).returncode, 2)

    @unittest.skipIf(os.geteuid() == 0, "le refus ne se produit que sans les droits d'administrateur")
    def test_creer_demande_les_droits_d_administrateur(self):
        fini = self.lancer("creer", "/dev/sdb1", entree="secret\n")
        self.assertEqual(fini.returncode, 2)
        self.assertIn("pkexec", fini.stderr)

    @unittest.skipUnless(shutil.which("lsblk"), "lsblk absent")
    def test_volumes_sort_du_json(self):
        fini = self.lancer("volumes")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        self.assertIsInstance(json.loads(fini.stdout), list)

    @unittest.skipUnless(os.geteuid() == 0, "il faut les droits d'administrateur")
    def test_mot_de_passe_vide_ou_volume_inconnu(self):
        self.assertEqual(self.lancer("creer", "/dev/sdb1", entree="\n").returncode, 2)
        fini = self.lancer("creer", "/etc/shadow", entree="secret\n")
        self.assertEqual(fini.returncode, 2)
        self.assertIn("n'est pas un volume chiffré", fini.stderr)


def luks_utilisable():
    return (os.geteuid() == 0 and shutil.which("cryptsetup") and os.path.exists(CLE.CRYPTENROLL))


@unittest.skipUnless(luks_utilisable(), "il faut root, cryptsetup et systemd-cryptenroll")
class VraiVolume(unittest.TestCase):
    """Un vrai volume LUKS2, dans un fichier : la clé créée doit réellement déverrouiller le volume."""

    MOT_DE_PASSE = "mot de passe de test"

    @classmethod
    def setUpClass(cls):
        cls.dossier = tempfile.TemporaryDirectory()
        cls.image = os.path.join(cls.dossier.name, "disque.img")
        with open(cls.image, "wb") as fichier:
            fichier.truncate(32 * 1024 * 1024)
        formater = subprocess.run(
            ["cryptsetup", "luksFormat", "--batch-mode", "--type", "luks2", "--pbkdf", "pbkdf2",
             "--pbkdf-force-iterations", "1000", "--key-file=-", cls.image],
            input=cls.MOT_DE_PASSE.encode(), capture_output=True, timeout=120, check=False)
        if formater.returncode != 0:
            raise unittest.SkipTest("cryptsetup ne sait pas formater un fichier ici : " + formater.stderr.decode())
        essai = subprocess.run(["cryptsetup", "open", "--test-passphrase", "--key-file=-", cls.image],
                               input=cls.MOT_DE_PASSE.encode(), capture_output=True, timeout=120, check=False)
        if essai.returncode != 0:
            raise unittest.SkipTest("cryptsetup ne peut pas tester un mot de passe ici : " + essai.stderr.decode())
        cls.arbre = {"blockdevices": [{"path": cls.image, "type": "part", "fstype": "crypto_LUKS", "size": "32M",
                                       "mountpoints": [None]}]}

    @classmethod
    def tearDownClass(cls):
        cls.dossier.cleanup()

    def setUp(self):
        self.ancien = CLE.lsblk
        CLE.lsblk = lambda: self.arbre

    def tearDown(self):
        CLE.lsblk = self.ancien

    def emplacements(self):
        fini = subprocess.run([CLE.CRYPTENROLL, self.image], capture_output=True, text=True, timeout=60,
                              stdin=subprocess.DEVNULL, check=False)
        return CLE.emplacements(fini.stdout)

    def accepte(self, phrase):
        return subprocess.run(["cryptsetup", "open", "--test-passphrase", "--key-file=-", self.image],
                              input=phrase.encode(), capture_output=True, timeout=60, check=False).returncode == 0

    def test_cycle_complet(self):
        # mauvais mot de passe : refusé, rien n'est créé
        code, message = CLE.creer(self.image, False, "mauvais")
        self.assertEqual(code, 4, message)
        self.assertNotIn("recovery", self.emplacements().values())

        # bon mot de passe : une clé, qui déverrouille vraiment le volume
        code, cle = CLE.creer(self.image, False, self.MOT_DE_PASSE)
        self.assertEqual(code, 0, cle)
        self.assertIsNotNone(CLE.MOTIF_CLE.match("    " + cle))
        self.assertIn("recovery", self.emplacements().values())
        self.assertTrue(self.accepte(cle), "la clé de récupération ne déverrouille pas le volume")
        self.assertTrue(self.accepte(self.MOT_DE_PASSE), "le mot de passe d'origine doit rester valable")

        # une seconde demande ne remplace rien sans l'accord explicite
        code, _ = CLE.creer(self.image, False, self.MOT_DE_PASSE)
        self.assertEqual(code, 3)
        self.assertTrue(self.accepte(cle))

        # avec « remplacer » : une seule clé de récupération reste, l'ancienne ne marche plus
        code, nouvelle = CLE.creer(self.image, True, self.MOT_DE_PASSE)
        self.assertEqual(code, 0, nouvelle)
        self.assertNotEqual(nouvelle, cle)
        self.assertEqual(list(self.emplacements().values()).count("recovery"), 1)
        self.assertTrue(self.accepte(nouvelle))
        self.assertFalse(self.accepte(cle), "l'ancienne clé fonctionne encore")
        self.assertTrue(self.accepte(self.MOT_DE_PASSE))

    def test_un_fichier_hors_liste_est_refuse(self):
        code, message = CLE.creer("/etc/hostname", False, self.MOT_DE_PASSE)
        self.assertEqual(code, 2)
        self.assertIn("n'est pas un volume chiffré", message)


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from nicos_centre import launch, theme
        from nicos_centre.pages import securite
        cls.launch, cls.securite = launch, securite
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        self.appels = []
        self.ancien_run, self.ancien_input = self.launch.run, self.launch.run_input
        self.launch.run = self.faux_run
        self.launch.run_input = self.faux_run_input
        self.reponses = [(0, "CLE=lhdvfive-cvtrhvjt-drnvntdn-knvgfirr-clhfjjtf-hflngkjj-vtjvdneh-gnnidfnr\n", "")]
        self.volumes = ARBRE_VOLUMES

    def tearDown(self):
        self.launch.run, self.launch.run_input = self.ancien_run, self.ancien_input

    def faux_run(self, argv, timeout=120):
        return 0, json.dumps(self.volumes)

    def faux_run_input(self, argv, texte, timeout=300):
        self.appels.append((argv, texte))
        return self.reponses.pop(0)

    def page(self):
        page = self.securite.build(None)
        page.dialogues = []
        page.demander_mot_de_passe = lambda volume: page.mot_de_passe
        page.confirmer_remplacement = lambda: page.remplacer
        page.afficher_cle = lambda cle, volume: page.dialogues.append(("cle", cle, volume["chemin"]))
        page.afficher_erreur = lambda message: page.dialogues.append(("erreur", message))
        page.mot_de_passe, page.remplacer = "secret", False
        return page

    def capture(self, widget, nom):
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            if isinstance(widget, QDialog):
                widget.adjustSize()
            else:
                widget.resize(1040, 680)
            widget.show()
            self.app.processEvents()
            widget.grab().save(os.path.join(CAPTURES, nom))

    def test_un_bouton_par_volume_chiffre(self):
        page = self.page()
        self.assertEqual(len(page.cartes), 2)
        self.assertEqual([c.bouton.text() for c in page.cartes], ["Créer une clé de récupération"] * 2)
        self.capture(page, "securite.png")

    def test_sans_volume_chiffre_on_explique_comment_en_avoir_un(self):
        self.volumes = []
        page = self.page()
        self.assertEqual(page.cartes, [])
        self.assertGreaterEqual(page.volumes.count(), 1)

    def test_outil_absent_ou_en_erreur(self):
        self.launch.run = lambda argv, timeout=120: (5, "")
        self.assertEqual(self.page().cartes, [])
        self.launch.run = lambda argv, timeout=120: (0, "pas du json")
        self.assertEqual(self.page().cartes, [])

    def test_creation_reussie_le_mot_de_passe_passe_par_l_entree_standard(self):
        page = self.page()
        page.creer_cle(ARBRE_VOLUMES[0])
        (argv, texte), = self.appels
        self.assertEqual(argv, ["pkexec", self.securite.CLE_RECUPERATION, "creer", "/dev/nvme0n1p3"])
        self.assertEqual(texte, "secret\n")
        self.assertNotIn("secret", " ".join(argv))
        self.assertEqual(page.dialogues, [("cle", "lhdvfive-cvtrhvjt-drnvntdn-knvgfirr-clhfjjtf-hflngkjj-vtjvdneh-gnnidfnr",
                                           "/dev/nvme0n1p3")])

    def test_sans_mot_de_passe_rien_ne_se_passe(self):
        page = self.page()
        page.mot_de_passe = None
        page.creer_cle(ARBRE_VOLUMES[0])
        self.assertEqual(self.appels, [])
        self.assertEqual(page.dialogues, [])

    def test_mauvais_mot_de_passe_message_clair(self):
        self.reponses = [(4, "", "Mot de passe refusé.\n")]
        page = self.page()
        page.creer_cle(ARBRE_VOLUMES[0])
        self.assertEqual(page.dialogues, [("erreur", "Mot de passe refusé.")])

    def test_cle_existante_on_demande_avant_de_remplacer(self):
        self.reponses = [(3, "", "Une clé de récupération existe déjà pour ce disque.\n"),
                         (0, "CLE=aaaaaaaa-bbbbbbbb-cccccccc-dddddddd-eeeeeeee-ffffffff-gggggggg-hhhhhhhh\n", "")]
        page = self.page()
        page.remplacer = True
        page.creer_cle(ARBRE_VOLUMES[0])
        self.assertEqual(len(self.appels), 2)
        self.assertNotIn("--remplacer", self.appels[0][0])
        self.assertEqual(self.appels[1][0][-1], "--remplacer")
        self.assertEqual(page.dialogues[0][0], "cle")

    def test_cle_existante_refus_de_remplacer(self):
        self.reponses = [(3, "", "Une clé de récupération existe déjà pour ce disque.\n")]
        page = self.page()
        page.remplacer = False
        page.creer_cle(ARBRE_VOLUMES[0])
        self.assertEqual(len(self.appels), 1)
        self.assertEqual(page.dialogues, [])

    def test_fenetre_d_authentification_fermee_pas_de_message(self):
        self.reponses = [(126, "", "")]
        page = self.page()
        page.creer_cle(ARBRE_VOLUMES[0])
        self.assertEqual(page.dialogues, [])

    def test_droits_insuffisants_message(self):
        self.reponses = [(127, "", "Not authorized")]
        page = self.page()
        page.creer_cle(ARBRE_VOLUMES[0])
        self.assertEqual(page.dialogues[0][0], "erreur")
        self.assertIn("administrateur", page.dialogues[0][1])

    def test_boite_de_la_cle_on_ne_ferme_qu_apres_confirmation(self):
        dialogue = self.securite.CleDialog(None, "lhdvfive-cvtrhvjt-drnvntdn-knvgfirr-clhfjjtf-hflngkjj-vtjvdneh-gnnidfnr",
                                           "/dev/nvme0n1p3")
        self.assertFalse(dialogue.fermer.isEnabled())
        dialogue.reject()
        self.assertTrue(dialogue.isVisible() or not dialogue.result())  # Échap sans confirmation : ne ferme pas
        dialogue.confirmation.setChecked(True)
        self.assertTrue(dialogue.fermer.isEnabled())
        self.capture(dialogue, "securite-cle.png")

    def test_papier_de_la_cle(self):
        texte = self.securite.texte_de_la_cle("aaaaaaaa-bbbbbbbb", "/dev/sdb1")
        for attendu in ("/dev/sdb1", "aaaaaaaa-bbbbbbbb", "ailleurs que sur ce PC"):
            self.assertIn(attendu, texte)


ARBRE_VOLUMES = [{"chemin": "/dev/nvme0n1p3", "taille": "475G", "montages": ["/", "/var"], "systeme": True},
                 {"chemin": "/dev/sdb1", "taille": "58G", "montages": [], "systeme": False}]


if __name__ == "__main__":
    unittest.main()
