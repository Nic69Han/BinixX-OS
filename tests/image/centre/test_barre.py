"""Tests de la barre des tâches (haut ou bas) : script envoyé à Plasma, lecture de la position, page du Centre.

python3 -m unittest discover -s tests/image/centre -p 'test_barre.py'   (la partie Qt est ignorée sans PySide6)
"""

import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import barre  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

# Ce que Plasma renvoie pour un panneau en haut / en bas (busctl écrit « s "…" » et échappe les guillemets)
DISPOSITION_HAUT = 's "var panel = new Panel\\npanel.location = \\"top\\"\\npanel.floating = true\\n"'
DISPOSITION_BAS = 's "var panel = new Panel\\npanel.location = \\"bottom\\"\\n"'
CONFIGURATION = """[ActionPlugins][0]
RightButton;NoModifier=org.kde.contextmenu

[Containments][1]
activityId=
location=0
plugin=org.kde.plasma.folder

[Containments][2]
location={code}
plugin=org.kde.panel

[Containments][2][Applets][3]
plugin=org.kde.plasma.kickoff

[Containments][2][Applets][3][Configuration][General]
icon=binixx
"""


def configuration(code):
    fichier = tempfile.NamedTemporaryFile("w", suffix="-appletsrc", delete=False, encoding="utf-8")
    fichier.write(CONFIGURATION.format(code=code))
    fichier.close()
    return fichier.name


class Faux:
    """Un `launch.run` qui répond dans l'ordre et se souvient de ce qu'on lui a demandé."""

    def __init__(self, *reponses):
        self.reponses = list(reponses)
        self.appels = []

    def __call__(self, argv, timeout=120):
        self.appels.append(list(argv))
        return self.reponses.pop(0) if self.reponses else (1, "")


class Script(unittest.TestCase):
    def test_haut_et_bas(self):
        self.assertIn('p[i].location = "top"', barre.script_de_deplacement("haut"))
        self.assertIn('p[i].location = "bottom"', barre.script_de_deplacement("bas"))

    def test_une_position_inconnue_est_refusee(self):
        for position in ("gauche", "", "bas; rm -rf /", "top", None):
            with self.assertRaises(ValueError):
                barre.script_de_deplacement(position)

    def test_le_script_ne_depend_que_de_la_liste_fermee(self):
        for position in barre.POSITIONS:
            script = barre.script_de_deplacement(position)
            self.assertEqual(script.count('"'), 2)
            self.assertNotIn("\n", script)


class Lecture(unittest.TestCase):
    def test_disposition_de_plasma(self):
        self.assertEqual(barre.position_dans_disposition(DISPOSITION_HAUT), "haut")
        self.assertEqual(barre.position_dans_disposition(DISPOSITION_BAS), "bas")
        self.assertEqual(barre.position_dans_disposition("panel.location = 'top'"), "haut")
        self.assertIsNone(barre.position_dans_disposition('panel.location = "left"'))
        self.assertIsNone(barre.position_dans_disposition(""))
        self.assertIsNone(barre.position_dans_disposition(None))

    def test_fichier_de_configuration(self):
        for code, attendu in (("3", "haut"), ("4", "bas")):
            chemin = configuration(code)
            self.addCleanup(os.unlink, chemin)
            self.assertEqual(barre.position_dans_configuration(chemin), attendu)

    def test_fichier_absent_ou_barre_sur_un_cote(self):
        self.assertIsNone(barre.position_dans_configuration("/n/existe/pas"))
        chemin = configuration("5")  # bord gauche : ni haut ni bas
        self.addCleanup(os.unlink, chemin)
        self.assertIsNone(barre.position_dans_configuration(chemin))

    def test_position_actuelle_prefere_la_disposition_puis_le_fichier(self):
        chemin = configuration("4")
        self.addCleanup(os.unlink, chemin)
        self.assertEqual(barre.position_actuelle(Faux((0, DISPOSITION_HAUT)), chemin), "haut")
        self.assertEqual(barre.position_actuelle(Faux((1, "")), chemin), "bas")             # bureau fermé : le fichier
        self.assertEqual(barre.position_actuelle(Faux((0, "rien d'utile")), chemin), "bas")  # sortie illisible : le fichier
        self.assertIsNone(barre.position_actuelle(Faux((1, "")), "/n/existe/pas"))


class Horloge:
    """Une horloge simulée : dormir() la fait avancer, aucun test n'attend pour de vrai."""

    def __init__(self):
        self.t = 0.0
        self.pauses = 0

    def __call__(self):
        return self.t

    def dormir(self, secondes):
        self.t += secondes
        self.pauses += 1


class Deplacement(unittest.TestCase):
    def deplacer(self, position, faux, attente=3.0):
        horloge = Horloge()
        resultat = barre.deplacer(position, faux, "/n/existe/pas", attente, horloge.dormir, horloge)
        return resultat, horloge

    def test_la_commande_est_celle_de_plasma_sans_shell(self):
        faux = Faux((0, "s \"\"\n"), (0, DISPOSITION_BAS))
        (reussi, message), _ = self.deplacer("bas", faux)
        self.assertTrue(reussi, message)
        self.assertEqual(message, "La barre est maintenant en bas.")
        self.assertEqual(faux.appels[0][:6], ["busctl", "--user", "call", "org.kde.plasmashell", "/PlasmaShell",
                                              "org.kde.PlasmaShell"])
        self.assertEqual(faux.appels[0][6:9], ["evaluateScript", "s", barre.script_de_deplacement("bas")])

    def test_plasma_met_du_temps_on_relit_jusqu_a_la_confirmation(self):
        # constaté en test VM : juste après evaluateScript, Plasma répond encore l'ancienne position
        faux = Faux((0, 's ""'), (0, DISPOSITION_HAUT), (0, DISPOSITION_HAUT), (0, DISPOSITION_BAS))
        (reussi, message), horloge = self.deplacer("bas", faux, attente=10.0)
        self.assertTrue(reussi, message)
        self.assertEqual(horloge.pauses, 2)  # deux relectures avant la bonne

    def test_sans_bureau_ouvert(self):
        (reussi, message), horloge = self.deplacer("haut", Faux((1, "")))
        self.assertFalse(reussi)
        self.assertIn("le bureau ne répond pas", message)
        self.assertEqual(horloge.pauses, 0)  # rien à attendre

    def test_erreur_de_script(self):
        (reussi, message), _ = self.deplacer("haut", Faux((0, 's "ReferenceError: panels is not defined"')))
        self.assertFalse(reussi)
        self.assertIn("ReferenceError", message)

    def test_la_barre_n_a_pas_bouge_apres_l_attente(self):
        reponses = [(0, 's ""')] + [(0, DISPOSITION_HAUT)] * 20
        (reussi, message), horloge = self.deplacer("bas", Faux(*reponses), attente=3.0)
        self.assertFalse(reussi)
        self.assertIn("La barre est restée en haut", message)
        self.assertIn("3 secondes", message)
        self.assertGreaterEqual(horloge.t, 3.0)

    def test_position_illisible_apres_coup_vaut_reussite(self):
        (reussi, _), _ = self.deplacer("haut", Faux((0, 's ""'), (1, "")))
        self.assertTrue(reussi)

    def test_position_inconnue(self):
        with self.assertRaises(ValueError):
            barre.deplacer("gauche", Faux())

    def test_envoyer_ne_relit_rien(self):
        faux = Faux((0, 's ""'))
        self.assertEqual(barre.envoyer("haut", faux), (True, ""))
        self.assertEqual(len(faux.appels), 1)
        self.assertEqual(barre.envoyer("haut", Faux((1, "")))[0], False)

    def test_a_bouge(self):
        self.assertTrue(barre.a_bouge("bas", "bas"))
        self.assertTrue(barre.a_bouge("bas", None))
        self.assertFalse(barre.a_bouge("bas", "haut"))


class LigneDeCommande(unittest.TestCase):
    def setUp(self):
        self.anciens = (barre.deplacer, barre.position_actuelle)
        self.sortie = []
        self.imprime = barre.__dict__.get("print")
        barre.print = lambda *args: self.sortie.append(" ".join(map(str, args)))

    def tearDown(self):
        barre.deplacer, barre.position_actuelle = self.anciens
        if self.imprime is None:
            del barre.print
        else:
            barre.print = self.imprime

    def test_deplacer(self):
        barre.deplacer = lambda position: (True, f"fait {position}")
        self.assertEqual(barre.main(["bas"]), 0)
        self.assertEqual(self.sortie, ["fait bas"])

    def test_echec(self):
        barre.deplacer = lambda position: (False, "non")
        self.assertEqual(barre.main(["haut"]), 1)

    def test_etat(self):
        barre.position_actuelle = lambda: "haut"
        self.assertEqual(barre.main(["etat"]), 0)
        self.assertEqual(self.sortie, ["haut"])
        barre.position_actuelle = lambda: None
        self.assertEqual(barre.main(["etat"]), 1)
        self.assertEqual(self.sortie[-1], "inconnue")

    def test_action_inconnue(self):
        with self.assertRaises(SystemExit):
            barre.main(["gauche"])


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageDuCentre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import theme
        from binixx_centre.pages import barre as page
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.module = page

    def setUp(self):
        self.anciens = (barre.position_actuelle, barre.envoyer)
        self.position = "haut"      # ce que Plasma répond
        self.demandes = []
        self.ordre = (True, "")     # ce que répond l'envoi de l'ordre
        barre.position_actuelle = lambda *a, **k: self.position
        barre.envoyer = lambda position, *a, **k: self.demandes.append(position) or self.ordre
        self.pages = []
        self.centre = type("Centre", (), {"show_page": lambda s, cle: self.pages.append(cle)})()

    def tearDown(self):
        barre.position_actuelle, barre.envoyer = self.anciens

    def ouvrir(self):
        page = self.module.build(self.centre)
        self.addCleanup(page.minuteur.stop)
        page.show()
        self.app.processEvents()
        return page

    def test_la_page_n_a_pas_de_bouton_et_depend_de_parametres(self):
        self.assertFalse(self.module.MENU)
        self.assertEqual(self.module.PARENT, "parametres")
        self.assertEqual(self.module.KEY, "barre")

    def test_la_position_actuelle_est_marquee(self):
        page = self.ouvrir()
        self.assertEqual(page.actuelle, "haut")
        self.assertTrue(page.cartes["haut"].apercu.actif)
        self.assertFalse(page.cartes["bas"].apercu.actif)
        self.assertEqual(page.cartes["haut"].bouton.text(), "Position actuelle")
        self.assertFalse(page.cartes["haut"].bouton.isEnabled())
        self.assertEqual(page.cartes["bas"].bouton.text(), "Choisir")
        self.assertTrue(page.cartes["bas"].bouton.isEnabled())
        self.assertEqual(page.etat.text(), "La barre est actuellement en haut.")
        page.close()

    def test_un_clic_envoie_l_ordre_puis_attend_la_confirmation(self):
        page = self.ouvrir()
        page.cartes["bas"].bouton.click()
        self.assertEqual(self.demandes, ["bas"])
        # tant que Plasma n'a pas bougé : message d'attente, boutons bloqués, minuteur en marche
        self.assertTrue(page.minuteur.isActive())
        self.assertIn("se déplace en bas", page.etat.text())
        self.assertFalse(any(carte.bouton.isEnabled() for carte in page.cartes.values()))
        page.verifier()                      # Plasma répond encore « haut »
        self.assertTrue(page.minuteur.isActive())
        self.position = "bas"
        page.verifier()                      # cette fois la barre est en bas
        self.assertFalse(page.minuteur.isActive())
        self.assertEqual(page.etat.text(), "La barre est maintenant en bas.")
        self.assertTrue(page.cartes["bas"].apercu.actif)
        self.assertFalse(page.cartes["bas"].bouton.isEnabled())
        self.assertTrue(page.cartes["haut"].bouton.isEnabled())
        page.close()

    def test_un_ordre_refuse_garde_la_position_et_l_explique(self):
        self.ordre = (False, "La barre n'a pas pu être déplacée : le bureau ne répond pas.")
        page = self.ouvrir()
        page.cartes["bas"].bouton.click()
        self.assertIn("ne répond pas", page.etat.text())
        self.assertFalse(page.minuteur.isActive())
        self.assertTrue(page.cartes["haut"].apercu.actif)
        page.close()

    def test_plasma_n_applique_jamais_le_changement(self):
        page = self.ouvrir()
        page.cartes["bas"].bouton.click()
        page.fin = 0.0                       # le délai est écoulé
        page.verifier()
        self.assertFalse(page.minuteur.isActive())
        self.assertIn("est restée en haut", page.etat.text())
        self.assertTrue(page.cartes["haut"].apercu.actif)
        self.assertTrue(page.cartes["bas"].bouton.isEnabled())   # on peut réessayer
        page.close()

    def test_position_illisible_pendant_l_attente_vaut_reussite(self):
        page = self.ouvrir()
        page.cartes["bas"].bouton.click()
        self.position = None
        page.verifier()
        self.assertFalse(page.minuteur.isActive())
        self.assertEqual(page.etat.text(), "La barre est maintenant en bas.")
        page.close()

    def test_sans_session_on_le_dit(self):
        self.position = None
        page = self.ouvrir()
        self.assertIn("n'a pas pu être lue", page.etat.text())
        self.assertFalse(any(carte.apercu.actif for carte in page.cartes.values()))
        page.close()

    def test_retour_aux_parametres(self):
        from PySide6.QtWidgets import QPushButton
        page = self.module.build(self.centre)
        retour = next(b for b in page.findChildren(QPushButton) if b.text().startswith("←"))
        retour.click()
        self.assertEqual(self.pages, ["parametres"])

    def test_capture(self):
        if not CAPTURES:
            self.skipTest("BINIXX_CAPTURES non défini")
        os.makedirs(CAPTURES, exist_ok=True)
        page = self.module.build(self.centre)
        page.resize(1000, 760)
        page.show()
        self.app.processEvents()
        self.assertFalse(page.grab().isNull())
        page.grab().save(os.path.join(CAPTURES, "barre.png"))
        page.close()


if __name__ == "__main__":
    unittest.main()
