"""Tests de la couleur d'un dossier (binixx_centre/couleur_dossier.py, menu « Couleur du dossier » de Dolphin).

python3 -m unittest discover -s tests/image/centre -p 'test_couleur_dossier.py'
"""

import configparser
import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
DEPOT = os.path.join(ICI, "../../../system_files")
sys.path.insert(0, RACINE)

from binixx_centre import couleur_dossier as C  # noqa: E402


class FauxKwriteconfig:
    """kwriteconfig6 sur de vrais fichiers .directory, comme le vrai (groupe [Desktop Entry], clé Icon)."""

    def __init__(self, panne=False):
        self.commandes = []
        self.panne = panne

    def __call__(self, argv, timeout=None):
        self.commandes.append(list(argv))
        if self.panne:
            return 1, "kwriteconfig6: erreur"
        fichier, groupe, cle = argv[argv.index("--file") + 1], argv[argv.index("--group") + 1], argv[argv.index("--key") + 1]
        lecteur = configparser.ConfigParser(interpolation=None)
        lecteur.optionxform = str
        lecteur.read(fichier)
        if "--delete" in argv:
            if lecteur.has_section(groupe):
                lecteur.remove_option(groupe, cle)
        else:
            if not lecteur.has_section(groupe):
                lecteur.add_section(groupe)
            lecteur.set(groupe, cle, argv[-1])
        with open(fichier, "w") as f:
            lecteur.write(f, space_around_delimiters=False)
        return 0, ""


def icone(dossier):
    lecteur = configparser.ConfigParser(interpolation=None)
    lecteur.optionxform = str
    lecteur.read(os.path.join(dossier, ".directory"))
    return lecteur.get("Desktop Entry", "Icon", fallback=None)


class Couleur(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)

    def test_choisir_puis_revenir_a_l_origine(self):
        faux = FauxKwriteconfig()
        reussi, message = C.colorer(self.dossier, "vert", faux)
        self.assertTrue(reussi, message)
        self.assertEqual(icone(self.dossier), "folder-green")
        self.assertTrue(C.colorer(self.dossier, "rose", faux)[0])
        self.assertEqual(icone(self.dossier), "folder-magenta")
        self.assertTrue(C.colorer(self.dossier, "defaut", faux)[0])
        self.assertIsNone(icone(self.dossier))

    def test_les_autres_reglages_du_dossier_restent(self):
        with open(os.path.join(self.dossier, ".directory"), "w") as f:
            f.write("[Dolphin]\nViewMode=1\n")
        C.colorer(self.dossier, "bleu", FauxKwriteconfig())
        with open(os.path.join(self.dossier, ".directory")) as f:
            texte = f.read()
        self.assertIn("ViewMode=1", texte)
        self.assertEqual(icone(self.dossier), "folder-blue")

    def test_couleur_inconnue_et_pas_un_dossier(self):
        faux = FauxKwriteconfig()
        self.assertFalse(C.colorer(self.dossier, "fuchsia", faux)[0])
        self.assertFalse(C.colorer(os.path.join(self.dossier, "absent"), "bleu", faux)[0])
        self.assertEqual(faux.commandes, [])

    def test_defaut_sans_reglage_ne_cree_rien(self):
        faux = FauxKwriteconfig()
        self.assertTrue(C.colorer(self.dossier, "defaut", faux)[0])
        self.assertFalse(os.path.exists(os.path.join(self.dossier, ".directory")))
        self.assertEqual(faux.commandes, [])

    def test_le_bureau_ne_repond_pas(self):
        reussi, message = C.colorer(self.dossier, "bleu", FauxKwriteconfig(panne=True))
        self.assertFalse(reussi)
        self.assertIn(".directory", message)

    def test_ligne_de_commande_plusieurs_dossiers(self):
        autre = tempfile.mkdtemp(dir=self.dossier)
        lignes = []
        code = C.main(["orange", self.dossier, autre], FauxKwriteconfig(), lignes.append)
        self.assertEqual(code, 0)
        self.assertEqual((icone(self.dossier), icone(autre)), ("folder-orange", "folder-orange"))
        self.assertEqual(C.main(["orange"], FauxKwriteconfig(), lignes.append), 2)
        self.assertEqual(C.main(["fuchsia", self.dossier], FauxKwriteconfig(), lignes.append), 1)

    def test_le_menu_propose_chaque_couleur(self):
        menu = configparser.ConfigParser(interpolation=None)
        menu.optionxform = str
        menu.read(os.path.join(DEPOT, "usr/share/kio/servicemenus/binixx-couleur-dossier.desktop"))
        entete = menu["Desktop Entry"]
        self.assertIn("inode/directory", entete["MimeType"])
        actions = [a for a in entete["Actions"].split(";") if a]
        self.assertEqual(set(actions), set(C.COULEURS) | {C.DEFAUT})
        for action in actions:
            section = menu[f"Desktop Action {action}"]
            self.assertEqual(section["Exec"], f"/usr/libexec/binixx/binixx-couleur-dossier {action} %F")
            if action != C.DEFAUT:
                self.assertEqual(section["Icon"], C.COULEURS[action])


if __name__ == "__main__":
    unittest.main()
