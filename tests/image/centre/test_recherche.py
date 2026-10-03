"""Tests de la recherche unique (Windows + S) : notation, lecture des lanceurs, regroupement, ouverture, fenêtre.

python3 -m unittest discover -s tests/image/centre -p 'test_recherche.py'   (la partie Qt est ignorée sans PySide6)
"""

import json
import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
DEPOT = os.path.join(ICI, "../../..")
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(DEPOT, "system_files/usr/lib/binixx/centre"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
PARAMETRES = os.environ.get("BINIXX_PARAMETRES", os.path.join(DEPOT, "system_files/usr/share/binixx/parametres/parametres.tsv"))
CATALOGUE = os.environ.get("BINIXX_CATALOGUE", os.path.join(DEPOT, "system_files/usr/share/binixx/catalogue-windows/catalogue.tsv"))
sys.path.insert(0, RACINE)

from binixx_centre import catalogue, launch, parametres  # noqa: E402
from binixx_centre import recherche as R  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


def lanceur(dossier, fichier, **champs):
    """Écrit un fichier .desktop de test et renvoie son chemin."""
    base = {"Type": "Application", "Name": "Sans nom", "Exec": "vrai"}
    base.update(champs)
    chemin = os.path.join(dossier, fichier)
    with open(chemin, "w", encoding="utf-8") as sortie:
        sortie.write("[Desktop Entry]\n" + "".join(f"{cle}={valeur}\n" for cle, valeur in base.items() if valeur is not None))
    return chemin


def index(**autres):
    """Un index sur les vrais fichiers de réglages et de catalogue du dépôt, avec les applications données."""
    os.environ["BINIXX_PARAMETRES"], os.environ["BINIXX_CATALOGUE"] = PARAMETRES, CATALOGUE
    return R.Index(**{"applications": [], **autres})


def application(nom, generique="", mots=(), commentaire="", identifiant=None):
    return {"nom": nom, "generique": generique, "commentaire": commentaire, "mots": list(mots), "icone": "",
            "id": identifiant or nom.lower().replace(" ", "-"), "chemin": f"/usr/share/applications/{nom}.desktop"}


class Notation(unittest.TestCase):
    def note(self, requete, nom, synonymes=(), autres=""):
        return R.noter(R.mots_de(requete), nom, synonymes, autres)

    def test_un_mot_absent_donne_zero(self):
        self.assertEqual(self.note("imprimante scanner", "Imprimantes"), 0)
        self.assertEqual(self.note("", "Imprimantes"), 0)

    def test_du_plus_precis_au_moins_precis(self):
        exact = self.note("firefox", "Firefox")
        synonyme = self.note("navigateur", "Firefox", ["Navigateur"])
        debut = self.note("imprim", "Imprimantes et scanners")
        mot = self.note("scanners", "Imprimantes et scanners")
        milieu = self.note("rimante", "Imprimantes et scanners")
        texte = self.note("pdf", "Imprimantes", (), "Créer un PDF")
        self.assertGreater(exact, synonyme)
        self.assertGreater(synonyme, debut)
        self.assertGreater(debut, mot)
        self.assertGreater(mot, milieu)
        self.assertGreater(milieu, texte)
        self.assertGreater(texte, 0)

    def test_sans_accents_ni_majuscules(self):
        self.assertGreater(self.note("ecran", "Écran de verrouillage"), 0)
        self.assertGreaterEqual(self.note("WIFI", "Wi-Fi"), 100)
        self.assertGreaterEqual(self.note("wi fi", "Wi-Fi"), 100)
        self.assertGreater(self.note("wifi", "Réseau", ["Wi-Fi"]), 0)

    def test_plusieurs_mots_dans_un_autre_ordre(self):
        self.assertGreater(self.note("scanners imprimantes", "Imprimantes et scanners"), 0)

    def test_un_mot_de_plus_qui_correspond_ajoute_un_point(self):
        self.assertGreater(self.note("mode sombre", "Mode sombre"), self.note("mode", "Mode sombre") - 100 + 99)


class Lanceurs(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)

    def lire(self, fichier="x.desktop", lang="fr", **champs):
        return R.lire_lanceur(lanceur(self.dossier, fichier, **champs), lang)

    def test_nom_traduit_et_mots_cles(self):
        l = self.lire(**{"Name": "Files", "Name[fr]": "Fichiers", "GenericName[fr]": "Gestionnaire de fichiers",
                         "Keywords": "files;", "Keywords[fr]": "fichiers;dossiers;explorateur;", "Icon": "system-file-manager"})
        self.assertEqual(l["nom"], "Fichiers")
        self.assertEqual(l["generique"], "Gestionnaire de fichiers")
        self.assertEqual(l["mots"], ["fichiers", "dossiers", "explorateur"])
        self.assertEqual(l["id"], "x")
        self.assertEqual(l["icone"], "system-file-manager")

    def test_langue_de_la_region(self):
        l = self.lire(**{"Name": "Files", "Name[fr_FR]": "Fichiers (France)", "Name[fr]": "Fichiers"})
        self.assertEqual(l["nom"], "Fichiers (France)")
        self.assertEqual(self.lire(lang="de", **{"Name": "Files", "Name[fr]": "Fichiers"})["nom"], "Files")

    def test_ce_qu_on_ne_montre_pas(self):
        self.assertIsNone(self.lire(NoDisplay="true"))
        self.assertIsNone(self.lire(Hidden="true"))
        self.assertIsNone(self.lire(Type="Link"))
        self.assertIsNone(self.lire(OnlyShowIn="GNOME;"))
        self.assertIsNone(self.lire(NotShowIn="KDE;"))
        self.assertIsNone(self.lire(Name=None))
        self.assertIsNotNone(self.lire(OnlyShowIn="KDE;"))
        self.assertIsNotNone(self.lire(NoDisplay="false"))

    def test_seul_le_bloc_principal_compte(self):
        chemin = os.path.join(self.dossier, "y.desktop")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("[Desktop Entry]\nType=Application\nName=Vrai\n[Desktop Action nouvelle]\nName=Faux\n")
        self.assertEqual(R.lire_lanceur(chemin)["nom"], "Vrai")

    def test_fichier_absent_ou_illisible(self):
        self.assertIsNone(R.lire_lanceur("/n/existe/pas.desktop"))

    def test_dossiers_le_premier_gagne(self):
        autre = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, autre, True)
        lanceur(self.dossier, "a.desktop", Name="Dans le premier")
        lanceur(autre, "a.desktop", Name="Dans le second")
        lanceur(autre, "b.desktop", Name="Autre")
        lanceur(autre, "pas-un-lanceur.txt", Name="Non")
        noms = sorted(l["nom"] for l in R.lanceurs([self.dossier, autre, "/n/existe/pas"], "fr"))
        self.assertEqual(noms, ["Autre", "Dans le premier"])

    def test_variable_d_environnement(self):
        lanceur(self.dossier, "e.desktop", Name="Essai")
        os.environ["BINIXX_LANCEURS"] = self.dossier
        self.addCleanup(os.environ.pop, "BINIXX_LANCEURS")
        self.assertEqual([l["nom"] for l in R.lanceurs()], ["Essai"])

    def test_langue(self):
        anciennes = {v: os.environ.pop(v, None) for v in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")}
        self.addCleanup(lambda: [os.environ.__setitem__(k, v) for k, v in anciennes.items() if v is not None])
        self.assertEqual(R.langue(), "fr")
        os.environ["LANG"] = "en_GB.UTF-8"
        self.assertEqual(R.langue(), "en")
        os.environ["LC_ALL"] = "C"
        self.assertEqual(R.langue(), "en")
        os.environ["LANGUAGE"] = "de:en"
        self.assertEqual(R.langue(), "de")


class Applications(unittest.TestCase):
    def test_le_nom_passe_avant_les_mots_cles(self):
        liste = [application("Mon logiciel Windows", mots=["word", "excel"]), application("Word (web)"),
                 application("Traitement", "Éditeur de texte", mots=["word"])]
        resultats = sorted(R.chercher_applications(R.mots_de("word"), liste), key=lambda r: -r.score)
        self.assertEqual(resultats[0].titre, "Word (web)")
        self.assertEqual({r.titre for r in resultats}, {"Word (web)", "Mon logiciel Windows", "Traitement"})

    def test_la_precision_est_le_nom_generique_ou_le_commentaire(self):
        r = R.chercher_applications(["dolphin"], [application("Dolphin", "Fichiers")])[0]
        self.assertEqual((r.categorie, r.precision, r.action[0]), ("Applications", "Fichiers", "lanceur"))
        r = R.chercher_applications(["dolphin"], [application("Dolphin", commentaire="Explorer")])[0]
        self.assertEqual(r.precision, "Explorer")


class Ensemble(unittest.TestCase):
    def premier(self, requete, **autres):
        groupes = index(**autres).chercher(requete)
        self.assertTrue(groupes, requete)
        return groupes[0][0], groupes[0][1][0]

    def test_imprimante_ouvre_le_reglage_des_imprimantes(self):
        categorie, resultat = self.premier("imprimante")
        self.assertEqual(categorie, "Réglages")
        self.assertEqual(resultat.titre, "Imprimantes et scanners")
        self.assertEqual(resultat.action, ("kcm", "kcm_printer_manager"))

    def test_les_mots_de_windows_trouvent_le_bon_reglage(self):
        for requete, kcm in (("wifi", "kcm_networkmanagement"), ("bluetooth", "kcm_bluetooth"),
                             ("fond d'écran", "kcm_wallpaper"), ("souris", "kcm_mouse")):
            categorie, resultat = self.premier(requete)
            self.assertEqual(resultat.action, ("kcm", kcm), requete)

    def test_word_ouvre_le_catalogue_sur_word(self):
        categorie, resultat = self.premier("word", applications=[application("Mon logiciel Windows", mots=["word"])])
        self.assertEqual(categorie, "Logiciels Windows")
        self.assertEqual(resultat.titre, "Microsoft Word")
        self.assertEqual(resultat.action, ("centre", "catalogue", "word"))
        self.assertIn("OnlyOffice", resultat.precision)

    def test_un_logiciel_inclus_s_ouvre_tout_de_suite(self):
        categorie, resultat = self.premier("gestionnaire des tâches")
        self.assertEqual(resultat.action, ("executer", "app", "org.kde.plasma-systemmonitor"))

    def test_le_reglage_du_catalogue_ne_fait_pas_doublon(self):
        titres = [r.titre for _, liste in index().chercher("word") for r in liste if r.categorie == "Réglages"]
        self.assertNotIn("Mon logiciel Windows", titres)

    def test_les_categories_sont_rangees_par_leur_meilleur_resultat(self):
        groupes = index(applications=[application("Imprimer plus"), application("Obtenir de l'aide", mots=["imprimante"])]
                        ).chercher("imprimante")
        meilleurs = [liste[0].score for _, liste in groupes]
        self.assertEqual(meilleurs, sorted(meilleurs, reverse=True))
        self.assertEqual(groupes[0][0], "Réglages")

    def test_au_plus_cinq_par_categorie(self):
        liste = [application(f"Editeur {i}") for i in range(12)]
        groupes = dict(index(applications=liste).chercher("editeur"))
        self.assertEqual(len(groupes["Applications"]), R.PAR_CATEGORIE)

    def test_requete_vide_ou_sans_reponse(self):
        self.assertEqual(index().chercher(""), [])
        self.assertEqual(index().chercher("   !!! "), [])
        self.assertEqual(index().chercher("zzzzqqqqxxxx"), [])

    def test_l_aide(self):
        sujets = [("Mon imprimante n'imprime pas", "Imprimante allumée ?"), ("Je n'entends rien", "Vérifiez le volume.")]
        groupes = dict(index(aide=sujets).chercher("imprimante"))
        self.assertEqual(groupes["Aide"][0].action, ("centre", "aide", ""))
        self.assertNotIn("Aide", dict(index(aide=sujets).chercher("wifi")))

    def test_un_fichier_illisible_n_empeche_pas_de_chercher(self):
        os.environ["BINIXX_PARAMETRES"], os.environ["BINIXX_CATALOGUE"] = "/n/existe/pas", CATALOGUE
        groupes = R.Index(applications=[application("Firefox")]).chercher("firefox")
        self.assertEqual(groupes[0][1][0].titre, "Firefox")
        self.assertEqual(R.Index(applications=[]).reglages, [])

    def test_a_plat_et_fichiers_ajoutes_a_la_fin(self):
        groupes = index().chercher("imprimante")
        fichiers = R.lire_fichiers("/home/u/Documents/imprimante.pdf\n/home/u/notes.txt\n")
        complet = R.ajouter_fichiers(groupes, fichiers)
        self.assertEqual(complet[-1][0], "Fichiers")
        self.assertEqual(R.a_plat(complet)[-1].titre, "notes.txt")
        self.assertEqual(R.ajouter_fichiers(groupes, []), list(groupes))

    def test_json_et_texte(self):
        groupes = index().chercher("imprimante")
        donnees = json.loads(R.en_json(groupes))
        self.assertEqual(donnees[0]["categorie"], "Réglages")
        self.assertEqual(donnees[0]["resultats"][0]["action"], ["kcm", "kcm_printer_manager"])
        self.assertIn("Imprimantes et scanners", R.texte(groupes))
        self.assertEqual(R.texte([]), "Aucun résultat.")

    def test_ligne_de_commande(self):
        sortie = []
        os.environ["BINIXX_PARAMETRES"], os.environ["BINIXX_CATALOGUE"] = PARAMETRES, CATALOGUE
        os.environ["BINIXX_LANCEURS"] = tempfile.mkdtemp()
        self.addCleanup(os.environ.pop, "BINIXX_LANCEURS")
        self.assertEqual(R.main(["--texte", "imprimante"], sortie.append), 0)
        self.assertIn("kcm kcm_printer_manager", sortie[-1])
        self.assertEqual(R.main(["--texte", "zzzzqqqq"], sortie.append), 1)
        self.assertEqual(R.main(["--texte", "imprimante", "--json"], sortie.append), 0)
        self.assertEqual(json.loads(sortie[-1])[0]["categorie"], "Réglages")


class Fichiers(unittest.TestCase):
    def test_seuls_les_chemins_absolus_comptent(self):
        sortie = "Elapsed: 12 ms\n/home/u/Documents/rapport.pdf\n\n  /home/u/Images/photo.png  \nrelatif/pas.txt\n"
        resultats = R.lire_fichiers(sortie)
        self.assertEqual([r.titre for r in resultats], ["rapport.pdf", "photo.png"])
        self.assertEqual(resultats[0].precision, "/home/u/Documents")
        self.assertEqual(resultats[0].action, ("fichier", "/home/u/Documents/rapport.pdf"))
        self.assertGreater(resultats[0].score, resultats[1].score)

    def test_commande_sans_shell_et_sans_option_cachee(self):
        self.assertEqual(R.commande_fichiers("Rapport  Annuel"), ["baloosearch6", "-l", "6", "--", "rapport annuel"])
        self.assertEqual(R.commande_fichiers("--help; rm -rf /"), ["baloosearch6", "-l", "6", "--", "help rm rf"])
        self.assertIsNone(R.commande_fichiers("  !!  "))


class Ouverture(unittest.TestCase):
    class Faux:
        def __init__(self, reussite=True):
            self.appels, self.reussite = [], reussite

        def __getattr__(self, nom):
            def appel(*args):
                self.appels.append((nom, *args))
                return self.reussite
            return appel

    def ouvrir(self, action, reussite=True):
        faux = self.Faux(reussite)
        retour = R.ouvrir(R.Resultat("c", "t", "", "", action, 1), faux)
        return retour, faux.appels

    def test_chaque_genre_a_sa_fonction(self):
        for action, attendu in ((("lanceur", "/a.desktop"), ("open_desktop_file", "/a.desktop")),
                                (("kcm", "kcm_keys"), ("open_settings", "kcm_keys")),
                                (("centre", "catalogue", "word"), ("open_centre", "catalogue", "word")),
                                (("centre", "aide"), ("open_centre", "aide", "")),
                                (("app", "binixx-aide"), ("open_app", "binixx-aide")),
                                (("flatpak", "org.x.Y"), ("run_flatpak", "org.x.Y")),
                                (("discover", "update"), ("open_discover_mode", "update")),
                                (("executer", "app", "org.kde.dolphin"), ("executer", ("app", "org.kde.dolphin"))),
                                (("fichier", "/home/u/a.pdf"), ("open_file", "/home/u/a.pdf"))):
            retour, appels = self.ouvrir(action)
            self.assertTrue(retour, action)
            self.assertEqual(appels, [attendu], action)

    def test_un_echec_est_rapporte(self):
        self.assertFalse(self.ouvrir(("kcm", "kcm_keys"), reussite=False)[0])

    def test_une_ligne_d_explication_ou_un_genre_inconnu_ne_s_ouvre_pas(self):
        self.assertEqual(self.ouvrir(("info", ""))[0], False)
        self.assertEqual(self.ouvrir(("rien", "x"))[0], False)


class LancementsSansShell(unittest.TestCase):
    def setUp(self):
        self.lances = []
        self.ancien = launch._start
        launch._start = lambda argv: self.lances.append(argv) or True
        self.addCleanup(setattr, launch, "_start", self.ancien)

    def test_open_desktop_file(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = lanceur(dossier, "a.desktop")
            self.assertTrue(launch.open_desktop_file(chemin))
            self.assertEqual(self.lances[-1], ["kioclient", "exec", chemin])
            autre = os.path.join(dossier, "a.txt")
            open(autre, "w").close()
            self.assertFalse(launch.open_desktop_file(autre))
            self.assertFalse(launch.open_desktop_file(os.path.join(dossier, "absent.desktop")))
            self.assertFalse(launch.open_desktop_file("a.desktop"))
        self.assertEqual(len(self.lances), 1)

    def test_open_centre(self):
        self.assertTrue(launch.open_centre("catalogue", "word"))
        self.assertEqual(self.lances[-1], ["/usr/libexec/binixx/binixx-centre", "--page", "catalogue", "--recherche=word"])
        self.assertTrue(launch.open_centre("aide"))
        self.assertEqual(self.lances[-1], ["/usr/libexec/binixx/binixx-centre", "--page", "aide"])
        launch.open_centre("catalogue", "--help")
        self.assertEqual(self.lances[-1][-1], "--recherche=--help")     # jamais pris pour une option
        for mauvaise in ("../x", "Aide", "a b", "", "a;rm"):
            self.assertFalse(launch.open_centre(mauvaise), mauvaise)

    def test_open_file(self):
        with tempfile.NamedTemporaryFile() as fichier:
            self.assertTrue(launch.open_file(fichier.name))
            self.assertEqual(self.lances[-1], ["xdg-open", fichier.name])
        self.assertFalse(launch.open_file("/n/existe/pas"))
        self.assertFalse(launch.open_file("relatif.txt"))


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Fenetre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import recherche_fenetre, theme
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.module = recherche_fenetre

    def setUp(self):
        self.ouverts = []
        self.reponse = True
        self.fenetres = []

    def tearDown(self):
        for f in self.fenetres:
            f.close()

    def ouvrir(self, **autres):
        fenetre = self.module.Fenetre(index=index(**autres), ouvrir=lambda r: self.ouverts.append(r) or self.reponse)
        fenetre._lancer_les_fichiers = lambda argv: None        # pas de baloosearch6 dans les tests
        self.fenetres.append(fenetre)
        fenetre.show()
        self.app.processEvents()
        return fenetre

    def taper(self, fenetre, texte):
        fenetre.champ.setText(texte)
        fenetre.minuteur.stop()
        fenetre.chercher()
        self.app.processEvents()

    def test_au_depart_une_aide_et_pas_de_liste(self):
        f = self.ouvrir()
        self.assertTrue(f.aide.isVisible())
        self.assertFalse(f.liste.isVisible())
        self.assertTrue(f.champ.hasFocus() or f.champ.text() == "")

    def test_les_resultats_sont_groupes_et_le_premier_est_choisi(self):
        f = self.ouvrir(applications=[application("Imprimer plus")])
        self.taper(f, "imprimante")
        self.assertTrue(f.liste.isVisible())
        self.assertFalse(f.aide.isVisible())
        elements = f.elements()
        self.assertEqual(f.liste.currentItem(), elements[0])
        self.assertEqual(elements[0].data(0x0100).titre, "Imprimantes et scanners")   # Qt.UserRole
        # une ligne de titre par catégorie, que la sélection ne peut pas atteindre
        titres = [f.liste.item(i) for i in range(f.liste.count()) if f.liste.item(i).data(0x0100) is None]
        self.assertEqual(len(titres), len(f.groupes))
        from PySide6.QtCore import Qt
        self.assertTrue(all(not (t.flags() & Qt.ItemIsSelectable) for t in titres))

    def test_entree_ouvre_le_premier_et_ferme(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        f = self.ouvrir()
        self.taper(f, "wifi")
        QTest.keyClick(f.champ, Qt.Key_Return)
        self.assertEqual([r.action for r in self.ouverts], [("kcm", "kcm_networkmanagement")])
        self.assertFalse(f.isVisible())

    def test_si_l_ouverture_echoue_la_fenetre_reste(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        self.reponse = False
        f = self.ouvrir()
        self.taper(f, "wifi")
        QTest.keyClick(f.champ, Qt.Key_Return)
        self.assertTrue(f.isVisible())

    def test_les_fleches_sautent_les_titres_et_font_le_tour(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        f = self.ouvrir(applications=[application("Imprimer plus"), application("Imprimante magique")])
        self.taper(f, "imprim")
        elements = f.elements()
        self.assertGreater(len(elements), 2)
        QTest.keyClick(f.champ, Qt.Key_Down)
        self.assertEqual(f.liste.currentItem(), elements[1])
        QTest.keyClick(f.champ, Qt.Key_Up)
        QTest.keyClick(f.champ, Qt.Key_Up)
        self.assertEqual(f.liste.currentItem(), elements[-1])       # on repart par la fin
        QTest.keyClick(f.champ, Qt.Key_Down)
        self.assertEqual(f.liste.currentItem(), elements[0])
        QTest.keyClick(f.champ, Qt.Key_Down)
        QTest.keyClick(f.champ, Qt.Key_Return)
        self.assertEqual(self.ouverts[-1], elements[1].data(0x0100))

    def test_echap_ferme(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        f = self.ouvrir()
        QTest.keyClick(f.champ, Qt.Key_Escape)
        self.assertFalse(f.isVisible())

    def test_un_clic_ouvre_la_ligne(self):
        f = self.ouvrir()
        self.taper(f, "wifi")
        f.liste.itemClicked.emit(f.elements()[0])
        self.assertEqual(len(self.ouverts), 1)

    def test_effacer_le_texte_vide_la_liste(self):
        f = self.ouvrir()
        self.taper(f, "wifi")
        self.assertTrue(f.liste.isVisible())
        f.champ.setText("")
        self.app.processEvents()
        self.assertEqual(f.liste.count(), 0)
        self.assertTrue(f.aide.isVisible())

    def test_la_recherche_attend_la_fin_de_la_frappe(self):
        from PySide6.QtTest import QTest
        f = self.ouvrir()
        f.champ.setText("wi")
        f.champ.setText("wifi")
        self.assertEqual(f.liste.count(), 0)                         # pas encore
        QTest.qWait(self.module.DELAI_FRAPPE + 150)
        self.assertGreater(f.liste.count(), 0)

    def test_entree_juste_apres_la_frappe_cherche_d_abord(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        f = self.ouvrir()
        f.champ.setText("wifi")
        QTest.keyClick(f.champ, Qt.Key_Return)
        self.assertEqual([r.action for r in self.ouverts], [("kcm", "kcm_networkmanagement")])

    def test_les_fichiers_arrivent_apres_les_autres_resultats(self):
        f = self.ouvrir()
        self.taper(f, "wifi")
        f.liste.setCurrentRow(f.liste.row(f.elements()[0]))
        f.fichiers = R.lire_fichiers("/home/u/wifi.txt\n")
        f.afficher(R.ajouter_fichiers(f.groupes, f.fichiers))
        self.assertEqual(f.elements()[-1].data(0x0100).titre, "wifi.txt")
        self.assertEqual(f.groupes[-1][0], "Fichiers")

    def test_perdre_le_focus_ferme_mais_pas_a_l_ouverture(self):
        from PySide6.QtCore import QEvent
        f = self.ouvrir()
        f.isActiveWindow = lambda: False
        f.prete = False
        f.changeEvent(QEvent(QEvent.ActivationChange))
        self.assertTrue(f.isVisible())
        f.prete = True
        f.changeEvent(QEvent(QEvent.ActivationChange))
        self.assertFalse(f.isVisible())

    def test_icones(self):
        from PySide6.QtGui import QIcon
        self.assertFalse(self.module.icone(":settings").isNull())
        self.assertIsInstance(self.module.icone("nom-inconnu"), QIcon)
        self.assertIsInstance(self.module.icone(""), QIcon)
        self.assertIsInstance(self.module.icone("/n/existe/pas.png"), QIcon)

    def test_les_sujets_d_aide_viennent_de_la_page_d_aide(self):
        sujets = self.module.Fenetre._sujets_d_aide()
        self.assertTrue(any("imprimante" in titre.lower() for titre, _ in sujets))

    def test_capture(self):
        if not CAPTURES:
            self.skipTest("BINIXX_CAPTURES non défini")
        os.makedirs(CAPTURES, exist_ok=True)
        f = self.ouvrir(applications=[application("Imprimer plus", "Impression de documents")])
        self.taper(f, "imprimante")
        f.grab().save(os.path.join(CAPTURES, "recherche.png"))


if __name__ == "__main__":
    unittest.main()
