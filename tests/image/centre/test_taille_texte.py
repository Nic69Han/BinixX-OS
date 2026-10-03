"""Tests de la taille du texte : calcul des polices, écriture dans kdeglobals, retour aux polices d'origine, page.

python3 -m unittest discover -s tests/image/centre -p 'test_taille_texte.py'   (la partie Qt est ignorée sans PySide6)
"""

import json
import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import taille_texte as T  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

STYLE = "-1,5,400,0,0,0,0,0,0,0,0,0,0,1"


class Kdeglobals:
    """Un faux kreadconfig6 / kwriteconfig6 : un dictionnaire {(groupe, clé) : valeur} et la liste des commandes."""

    def __init__(self, valeurs=None, sans_notify=False, panne=False):
        self.valeurs = dict(valeurs or {})
        self.commandes = []
        self.sans_notify = sans_notify
        self.panne = panne

    def __call__(self, argv, timeout=120):
        self.commandes.append(list(argv))
        if self.panne:
            return 1, ""
        groupe, cle = argv[argv.index("--group") + 1], argv[argv.index("--key") + 1]
        if argv[0] == "kreadconfig6":
            return 0, self.valeurs.get((groupe, cle), "") + "\n"
        if self.sans_notify and "--notify" in argv:
            return 1, "Unknown option 'notify'."
        if "--delete" in argv:
            self.valeurs.pop((groupe, cle), None)
        else:
            self.valeurs[(groupe, cle)] = argv[-1]
        return 0, ""


def police(famille="Noto Sans", taille=10):
    return f"{famille},{taille},{STYLE}"


class Calcul(unittest.TestCase):
    def test_taille_et_remplacement(self):
        self.assertEqual(T.taille_de(police(taille=10)), 10.0)
        self.assertEqual(T.taille_de(police(taille=10.5)), 10.5)
        self.assertIsNone(T.taille_de("n'importe quoi"))
        self.assertIsNone(T.taille_de("Noto Sans,grand,-1"))
        self.assertEqual(T.avec_taille(police(taille=10), 15), police(taille=15))
        self.assertEqual(T.avec_taille(police(taille=10), 12.5), police(taille=12.5))
        self.assertEqual(T.avec_taille(police(taille=10), 12.4), police(taille=12.5))     # au demi-point
        self.assertEqual(T.avec_taille(police("Une famille, avec virgule", 10), 11).split(",")[0], "Une famille")

    def test_facteurs_proposes(self):
        self.assertEqual(T.facteurs(), [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200])

    def test_borner(self):
        self.assertEqual(T.borner(50), 100)
        self.assertEqual(T.borner(999), 200)
        self.assertEqual(T.borner("125.4"), 125)
        with self.assertRaises(ValueError):
            T.borner("grand")

    def test_150_pour_cent_des_polices_de_kde(self):
        voulues = T.calculer(150, {})
        self.assertEqual(voulues[("General", "font")], "Noto Sans,15," + STYLE)
        self.assertEqual(voulues[("General", "smallestReadableFont")], "Noto Sans,12," + STYLE)
        self.assertEqual(T.taille_de(voulues[("General", "fixed")]), 15.0)
        self.assertEqual(T.taille_de(voulues[("WM", "activeFont")]), 15.0)
        self.assertEqual(set(voulues), set(T.CLES))

    def test_on_garde_la_famille_et_la_taille_choisies_par_l_utilisateur(self):
        voulues = T.calculer(120, {("General", "font"): police("Selawik", 11)})
        self.assertEqual(voulues[("General", "font")], police("Selawik", 13))              # 11 × 1,2 = 13,2 → 13
        self.assertTrue(voulues[("General", "font")].startswith("Selawik,13"))
        self.assertTrue(voulues[("General", "menuFont")].startswith("Noto Sans,12,"))

    def test_100_pour_cent_c_est_comme_avant(self):
        originales = {("General", "font"): police("Selawik", 11)}
        voulues = T.calculer(100, originales)
        self.assertEqual(voulues[("General", "font")], police("Selawik", 11))
        self.assertIsNone(voulues[("General", "fixed")])        # clé effacée : KDE reprend ses polices

    def test_apercu(self):
        self.assertEqual(T.apercu(100), 10.0)
        self.assertEqual(T.apercu(150), 15.0)
        self.assertEqual(T.apercu(125), 12.5)
        self.assertEqual(T.apercu(500), 20.0)


class Reglage(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.marqueur = os.path.join(self.dossier, "binixx", "taille-du-texte.json")

    def appliquer(self, pourcentage, faux):
        return T.appliquer(pourcentage, faux, self.marqueur)

    def test_la_premiere_fois_les_polices_d_origine_sont_gardees(self):
        faux = Kdeglobals({("General", "font"): police("Selawik", 11)})
        reussi, message = self.appliquer(150, faux)
        self.assertTrue(reussi)
        self.assertIn("150 %", message)
        self.assertEqual(faux.valeurs[("General", "font")], police("Selawik", 16.5))
        self.assertEqual(faux.valeurs[("General", "fixed")], "Monospace,15," + STYLE)
        marqueur = T.lire_marqueur(self.marqueur)
        self.assertEqual(marqueur["pourcentage"], 150)
        self.assertEqual(marqueur["originales"][("General", "font")], police("Selawik", 11))
        self.assertIsNone(marqueur["originales"][("General", "fixed")])
        self.assertEqual(T.pourcentage_actuel(self.marqueur), 150)

    def test_changer_de_taille_repart_toujours_des_polices_d_origine(self):
        faux = Kdeglobals()
        self.appliquer(150, faux)
        self.appliquer(120, faux)
        self.assertEqual(faux.valeurs[("General", "font")], "Noto Sans,12," + STYLE)    # 10 × 1,2, pas 15 × 1,2
        self.appliquer(100, faux)
        self.assertNotIn(("General", "font"), faux.valeurs)                              # comme avant : rien d'écrit
        self.assertEqual(T.pourcentage_actuel(self.marqueur), 100)

    def test_retablir_remet_les_polices_d_origine(self):
        faux = Kdeglobals({("General", "font"): police("Selawik", 11), ("General", "menuFont"): police("Selawik", 11)})
        self.appliquer(180, faux)
        reussi, message = T.retablir(faux, self.marqueur)
        self.assertTrue(reussi)
        self.assertEqual(faux.valeurs[("General", "font")], police("Selawik", 11))
        self.assertEqual(faux.valeurs[("General", "menuFont")], police("Selawik", 11))
        self.assertNotIn(("General", "fixed"), faux.valeurs)
        self.assertFalse(os.path.exists(self.marqueur))
        self.assertEqual(T.pourcentage_actuel(self.marqueur), 100)
        self.assertIn("d'origine", message)

    def test_retablir_ne_touche_pas_a_une_police_changee_a_la_main(self):
        faux = Kdeglobals()
        self.appliquer(150, faux)
        faux.valeurs[("General", "font")] = police("Ubuntu", 14)                         # l'utilisateur change sa police
        T.retablir(faux, self.marqueur)
        self.assertEqual(faux.valeurs[("General", "font")], police("Ubuntu", 14))
        self.assertNotIn(("General", "fixed"), faux.valeurs)                              # les autres reviennent

    def test_une_police_changee_a_la_main_devient_la_nouvelle_reference(self):
        faux = Kdeglobals()
        self.appliquer(150, faux)
        faux.valeurs[("General", "font")] = police("Ubuntu", 12)
        self.appliquer(200, faux)
        self.assertEqual(faux.valeurs[("General", "font")], police("Ubuntu", 24))

    def test_rien_a_retablir(self):
        faux = Kdeglobals()
        reussi, message = T.retablir(faux, self.marqueur)
        self.assertTrue(reussi)
        self.assertIn("déjà", message)
        self.assertEqual(faux.commandes, [])

    def test_sans_notify_on_ecrit_quand_meme(self):
        faux = Kdeglobals(sans_notify=True)
        reussi, _ = self.appliquer(150, faux)
        self.assertTrue(reussi)
        self.assertEqual(faux.valeurs[("General", "font")], "Noto Sans,15," + STYLE)

    def test_le_bureau_ne_repond_pas(self):
        reussi, message = self.appliquer(150, Kdeglobals(panne=True))
        self.assertFalse(reussi)
        self.assertIn("ne répond pas", message)
        self.assertFalse(os.path.exists(self.marqueur))

    def test_la_commande_est_celle_de_kde_sans_shell(self):
        faux = Kdeglobals()
        self.appliquer(150, faux)
        ecriture = next(c for c in faux.commandes if c[0] == "kwriteconfig6" and "font" in c)
        self.assertEqual(ecriture[:7], ["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "font"])
        self.assertIn("--notify", ecriture)
        self.assertEqual(ecriture[-1], "Noto Sans,15," + STYLE)

    def test_pourcentage_invalide(self):
        reussi, message = self.appliquer("grand", Kdeglobals())
        self.assertFalse(reussi)
        self.assertIn("entre 100 et 200", message)

    def test_marqueur_illisible_ou_incomplet(self):
        os.makedirs(os.path.dirname(self.marqueur))
        for contenu in ("pas du json", "[]", json.dumps({"pourcentage": 150})):
            with open(self.marqueur, "w", encoding="utf-8") as f:
                f.write(contenu)
            self.assertIsNone(T.lire_marqueur(self.marqueur), contenu)
        with open(self.marqueur, "w", encoding="utf-8") as f:
            f.write(json.dumps({"pourcentage": 150, "originales": {"sans-barre": "x", "General/font": "y"}}))
        self.assertEqual(T.lire_marqueur(self.marqueur)["originales"], {("General", "font"): "y"})
        self.assertEqual(T.pourcentage_actuel("/n/existe/pas.json"), 100)


class LigneDeCommande(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.marqueur = os.path.join(self.dossier, "m.json")

    def lancer(self, *argv, faux=None):
        sortie = []
        code = T.main(list(argv), run=faux or Kdeglobals(), sortie=sortie.append, chemin=self.marqueur)
        return code, "\n".join(sortie)

    def test_appliquer_etat_retablir(self):
        faux = Kdeglobals()
        self.assertEqual(self.lancer("etat", faux=faux), (0, "100"))
        code, texte = self.lancer("appliquer", "150", faux=faux)
        self.assertEqual((code, texte), (0, "Le texte est à 150 %."))
        self.assertEqual(self.lancer("etat", faux=faux), (0, "150"))
        code, texte = self.lancer("retablir", faux=faux)
        self.assertEqual(code, 0)
        self.assertEqual(self.lancer("etat", faux=faux), (0, "100"))

    def test_virgule_decimale_et_bornes(self):
        self.assertEqual(self.lancer("appliquer", "125,5")[0], 0)
        self.assertEqual(T.pourcentage_actuel(self.marqueur), 126)
        self.assertEqual(self.lancer("appliquer", "999")[0], 0)
        self.assertEqual(T.pourcentage_actuel(self.marqueur), 200)

    def test_pourcentage_absent_ou_mal_ecrit(self):
        for argv in (("appliquer",), ("appliquer", "grand"), ("appliquer", "-5"), ("appliquer", "1;rm")):
            code, texte = self.lancer(*argv)
            self.assertEqual(code, 1, argv)
            self.assertIn("entre 100 et 200", texte)

    def test_echec_du_bureau(self):
        code, texte = self.lancer("appliquer", "150", faux=Kdeglobals(panne=True))
        self.assertEqual(code, 1)
        self.assertIn("ne répond pas", texte)

    def test_action_inconnue(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            T.main(["bidule"])


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageDuCentre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import theme
        from binixx_centre.pages import taille_texte as page
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.module = page

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.marqueur = os.path.join(self.dossier, "m.json")
        self.faux = Kdeglobals()
        self.pages = []
        self.centre = type("Centre", (), {"show_page": lambda s, cle: self.pages.append(cle)})()
        self.anciens = (T.MARQUEUR, T.launch.run)
        T.MARQUEUR = self.marqueur
        T.launch.run = self.faux
        self.addCleanup(self.restaurer)

    def restaurer(self):
        T.MARQUEUR, T.launch.run = self.anciens

    def ouvrir(self):
        page = self.module.build(self.centre)
        page.resize(980, 760)
        page.show()
        self.app.processEvents()
        return page

    def test_la_page_depend_de_parametres_et_a_sa_couleur(self):
        self.assertFalse(self.module.MENU)
        self.assertEqual(self.module.PARENT, "parametres")
        self.assertEqual(self.module.KEY, "taille_texte")

    def test_au_depart_la_taille_d_origine(self):
        page = self.ouvrir()
        self.assertEqual(page.curseur.value(), 100)
        self.assertEqual(page.valeur.text(), "100 %")
        self.assertFalse(page.appliquer.isEnabled())
        self.assertFalse(page.retablir.isEnabled())
        self.assertIn("taille d'origine", page.etat.text())
        page.close()

    def test_le_curseur_change_l_apercu_sans_rien_appliquer(self):
        page = self.ouvrir()
        avant = page.apercu.font().pointSizeF()
        page.curseur.setValue(150)
        self.assertEqual(page.valeur.text(), "150 %")
        self.assertAlmostEqual(page.apercu.font().pointSizeF(), 15.0)
        self.assertGreater(page.apercu.font().pointSizeF(), avant)
        self.assertTrue(page.appliquer.isEnabled())
        self.assertEqual(self.faux.commandes, [])           # rien n'a été écrit
        page.close()

    def test_appliquer_ecrit_les_polices_et_le_dit(self):
        page = self.ouvrir()
        page.curseur.setValue(150)
        page.appliquer.click()
        self.assertEqual(self.faux.valeurs[("General", "font")], "Noto Sans,15," + STYLE)
        self.assertEqual(page.actuel, 150)
        self.assertIn("150 %", page.etat.text())
        self.assertFalse(page.appliquer.isEnabled())
        self.assertTrue(page.retablir.isEnabled())
        page.close()

    def test_retablir_remet_le_curseur_a_100(self):
        page = self.ouvrir()
        page.curseur.setValue(170)
        page.appliquer.click()
        page.retablir.click()
        self.assertEqual(page.curseur.value(), 100)
        self.assertEqual(page.actuel, 100)
        self.assertNotIn(("General", "font"), self.faux.valeurs)
        self.assertIn("d'origine", page.etat.text())
        page.close()

    def test_la_page_s_ouvre_sur_la_taille_deja_appliquee(self):
        T.appliquer(130, self.faux, self.marqueur)
        page = self.ouvrir()
        self.assertEqual(page.curseur.value(), 130)
        self.assertIn("130 %", page.etat.text())
        self.assertTrue(page.retablir.isEnabled())
        page.close()

    def test_echec_du_bureau(self):
        page = self.ouvrir()
        self.faux.panne = True
        page.curseur.setValue(150)
        page.appliquer.click()
        self.assertIn("ne répond pas", page.etat.text())
        self.assertEqual(page.actuel, 100)
        self.assertTrue(page.appliquer.isEnabled())
        page.close()

    def test_retour_aux_parametres(self):
        page = self.ouvrir()
        from PySide6.QtWidgets import QPushButton
        next(b for b in page.findChildren(QPushButton) if b.text().startswith("←")).click()
        self.assertEqual(self.pages, ["parametres"])
        page.close()

    def test_capture(self):
        if not CAPTURES:
            self.skipTest("BINIXX_CAPTURES non défini")
        os.makedirs(CAPTURES, exist_ok=True)
        page = self.ouvrir()
        page.curseur.setValue(150)
        self.app.processEvents()
        page.grab().save(os.path.join(CAPTURES, "taille_texte.png"))
        page.close()


if __name__ == "__main__":
    unittest.main()
