"""Tests du profil léger (binixx_centre.leger), sur un faux kreadconfig6 / kwriteconfig6 : aucun bureau n'est touché.

python3 -m unittest discover tests/image/centre
"""

import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
sys.path.insert(0, RACINE)

from binixx_centre import leger  # noqa: E402

MEMINFO_4_GO = "MemTotal:        3906000 kB\nMemFree:  100 kB\n"
MEMINFO_16_GO = "MemTotal:       16093000 kB\n"


class FauxBureau:
    """Un kdeglobals et un kwinrc en mémoire ; enregistre les commandes."""

    def __init__(self, reglages=None, kwin=True, notify=True):
        self.reglages = dict(reglages or {})      # (fichier, groupe, clé) -> valeur
        self.commandes, self.kwin, self.notify = [], kwin, notify

    def __call__(self, argv, timeout=None):
        self.commandes.append(argv)
        if argv[0] == "kreadconfig6":
            cle = (argv[argv.index("--file") + 1], argv[argv.index("--group") + 1], argv[argv.index("--key") + 1])
            return 0, self.reglages.get(cle, "") + "\n"
        if argv[0] == "kwriteconfig6":
            if "--notify" in argv and not self.notify:
                return 1, ""
            cle = (argv[argv.index("--file") + 1], argv[argv.index("--group") + 1], argv[argv.index("--key") + 1])
            if "--delete" in argv:
                self.reglages.pop(cle, None)
            else:
                self.reglages[cle] = argv[-1]
            return 0, ""
        if argv[0] == "busctl":
            return (0 if self.kwin else 1), ""
        raise AssertionError(argv)

    def reconfigurations(self):
        return [a for a in self.commandes if a[0] == "busctl"]


def voulus():
    return {(f, g, c): valeur for f, g, c, valeur in leger.REGLAGES}


class ProfilLeger(unittest.TestCase):
    def setUp(self):
        self.marqueur = os.path.join(tempfile.mkdtemp(), "binixx", "profil-leger.json")

    def test_activer_pose_les_reglages_et_recharge_kwin(self):
        bureau = FauxBureau()
        reussi, message = leger.activer(bureau, self.marqueur)
        self.assertTrue(reussi)
        self.assertIn("sans flou ni animations", message)
        self.assertEqual(bureau.reglages, voulus())
        self.assertEqual(len(bureau.reconfigurations()), 1)
        self.assertTrue(leger.actif(bureau, self.marqueur))

    def test_sans_session_les_reglages_sont_poses_pour_la_prochaine(self):
        bureau = FauxBureau(kwin=False)
        reussi, message = leger.activer(bureau, self.marqueur)
        self.assertTrue(reussi)
        self.assertIn("prochaine ouverture de session", message)
        self.assertEqual(bureau.reglages, voulus())

    def test_desactiver_remet_les_reglages_d_origine(self):
        origine = {("kdeglobals", "KDE", "AnimationDurationFactor"): "0.5", ("kwinrc", "Plugins", "blurEnabled"): "true"}
        bureau = FauxBureau(origine)
        leger.activer(bureau, self.marqueur)
        self.assertNotEqual(bureau.reglages, origine)
        reussi, _ = leger.desactiver(bureau, self.marqueur)
        self.assertTrue(reussi)
        self.assertEqual(bureau.reglages, origine)       # ce qui n'était pas écrit est effacé, le reste est remis
        self.assertFalse(os.path.exists(self.marqueur))
        self.assertFalse(leger.actif(bureau, self.marqueur))

    def test_un_reglage_change_a_la_main_est_laisse(self):
        bureau = FauxBureau()
        leger.activer(bureau, self.marqueur)
        bureau.reglages[("kwinrc", "Plugins", "blurEnabled")] = "true"        # l'utilisateur remet le flou
        self.assertFalse(leger.actif(bureau, self.marqueur))
        leger.desactiver(bureau, self.marqueur)
        self.assertEqual(bureau.reglages, {("kwinrc", "Plugins", "blurEnabled"): "true"})

    def test_activer_deux_fois_garde_l_origine(self):
        origine = {("kwinrc", "Plugins", "blurEnabled"): "true"}
        bureau = FauxBureau(origine)
        leger.activer(bureau, self.marqueur)
        leger.activer(bureau, self.marqueur)
        leger.desactiver(bureau, self.marqueur)
        self.assertEqual(bureau.reglages, origine)

    def test_desactiver_sans_avoir_active(self):
        bureau = FauxBureau({("kwinrc", "Plugins", "blurEnabled"): "true"})
        reussi, message = leger.desactiver(bureau, self.marqueur)
        self.assertTrue(reussi)
        self.assertIn("n'était pas activé", message)
        self.assertEqual([a for a in bureau.commandes if a[0] == "kwriteconfig6"], [])

    def test_kwriteconfig6_sans_notify(self):
        bureau = FauxBureau(notify=False)
        self.assertTrue(leger.activer(bureau, self.marqueur)[0])
        self.assertEqual(bureau.reglages, voulus())

    def test_marqueur_illisible(self):
        os.makedirs(os.path.dirname(self.marqueur))
        with open(self.marqueur, "w", encoding="utf-8") as fichier:
            fichier.write("pas du json")
        self.assertIsNone(leger.lire_marqueur(self.marqueur))
        self.assertFalse(leger.actif(FauxBureau(voulus()), self.marqueur))

    def test_conseil_selon_la_memoire(self):
        self.assertTrue(leger.conseille(MEMINFO_4_GO))
        self.assertFalse(leger.conseille(MEMINFO_16_GO))
        self.assertFalse(leger.conseille("rien"))
        self.assertTrue(leger.conseille("MemTotal: 4718592 kB\n"))        # 4,5 Go pile
        self.assertFalse(leger.conseille("MemTotal: 4718593 kB\n"))

    def test_les_effets_coupes_sont_ceux_qui_comptent(self):
        cles = {c for _, _, c, _ in leger.REGLAGES}
        self.assertIn("blurEnabled", cles)
        self.assertIn("AnimationDurationFactor", cles)
        self.assertTrue(all(valeur in ("0", "false") for *_, valeur in leger.REGLAGES))


class LigneDeCommande(unittest.TestCase):
    def setUp(self):
        self.marqueur = os.path.join(tempfile.mkdtemp(), "binixx", "profil-leger.json")

    def lancer(self, action, bureau, meminfo=MEMINFO_4_GO):
        lignes = []
        code = leger.main([action], run=bureau, sortie=lignes.append, chemin=self.marqueur, meminfo=meminfo)
        return code, lignes

    def test_etat_et_conseil(self):
        bureau = FauxBureau()
        self.assertEqual(self.lancer("etat", bureau), (0, ["leger=non", "conseille=oui"]))
        self.assertEqual(self.lancer("conseil", bureau, MEMINFO_16_GO), (0, ["non"]))
        self.assertEqual(self.lancer("activer", bureau)[0], 0)
        self.assertEqual(self.lancer("etat", bureau, MEMINFO_16_GO), (0, ["leger=oui", "conseille=non"]))
        self.assertEqual(self.lancer("desactiver", bureau)[0], 0)
        self.assertEqual(self.lancer("etat", bureau)[1][0], "leger=non")


if __name__ == "__main__":
    unittest.main()
