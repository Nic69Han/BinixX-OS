"""Tests de l'aide-mémoire des raccourcis : fichier, codes de touches de Qt, lecture de ce que KDE a enregistré,
cohérence avec les raccourcis fournis par l'image, page du Centre.

python3 -m unittest discover -s tests/image/centre -p 'test_raccourcis.py'   (la partie Qt est ignorée sans PySide6)
"""

import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr

ICI = os.path.dirname(__file__)
DEPOT = os.path.join(ICI, "../../..")
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(DEPOT, "system_files/usr/lib/binixx/centre"))
FICHIER = os.environ.get("BINIXX_RACCOURCIS", os.path.join(DEPOT, "system_files/usr/share/binixx/raccourcis/raccourcis.tsv"))
XDG = os.environ.get("BINIXX_XDG_RACCOURCIS", os.path.join(DEPOT, "system_files/etc/xdg/kglobalshortcutsrc"))
LANCEURS = os.environ.get("BINIXX_LANCEURS", os.path.join(DEPOT, "system_files/usr/share/applications"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import raccourcis as R  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

ENTETE = "# test\n"


def fichier_tsv(*lignes):
    f = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8")
    f.write(ENTETE + "".join("\t".join(ligne) + "\n" if isinstance(ligne, tuple) else ligne + "\n" for ligne in lignes))
    f.close()
    return f.name


def structure(composant, action, *touches):
    """Une action telle que KDE la renvoie (busctl --json) : nom de l'action, nom affiché, composant, nom affiché du composant,
    contexte, nom affiché du contexte, puis les touches actuelles et celles par défaut."""
    return [action, action, composant, composant, "default", "default", [[[t]] for t in touches], []]


def reponse(*structures):
    return json.dumps({"type": "a(ssssssa(ai)a(ai))", "data": [list(structures)]})


COMPOSANTS = json.dumps({"type": "ao", "data": [["/component/kwin", "/component/org_kde_dolphin_desktop"]]})
KWIN = reponse(structure("kwin", "Show Desktop", 0x10000044), structure("kwin", "Walk Through Windows", 0x9000001),
               structure("kwin", "Sans touche"))
DOLPHIN = reponse(structure("org.kde.dolphin.desktop", "_launch", 0x10000045))


class Faux:
    """Un `launch.run` qui répond selon la commande et se souvient de ce qu'on lui a demandé."""

    def __init__(self, composants=COMPOSANTS, reponses=None, echoue_sans_argument=False):
        self.composants = composants
        self.reponses = reponses or {"/component/kwin": KWIN, "/component/org_kde_dolphin_desktop": DOLPHIN}
        self.echoue_sans_argument = echoue_sans_argument
        self.appels = []

    def __call__(self, argv, timeout=120):
        self.appels.append(list(argv))
        if "allComponents" in argv:
            return (0, self.composants) if self.composants is not None else (1, "")
        chemin = next(a for a in argv if a.startswith("/component/"))
        if self.echoue_sans_argument and argv[-1] != "":
            return 1, ""
        return 0, self.reponses.get(chemin, reponse())


class Fichier(unittest.TestCase):
    def test_le_fichier_du_depot_est_valide(self):
        liste = R.charger(FICHIER)
        self.assertGreaterEqual(len(liste), 10)
        self.assertEqual(len({r.touches for r in liste}), len(liste))
        for r in liste:
            self.assertTrue(r.action, r)
            self.assertIn(r.source, R.SOURCES)

    def test_les_categories_gardent_l_ordre_du_fichier(self):
        liste = R.charger(FICHIER)
        self.assertEqual(R.categories(liste)[0], liste[0].categorie)
        self.assertEqual(len(R.categories(liste)), len(set(R.categories(liste))))

    def test_les_raccourcis_de_windows_les_plus_courants_y_sont(self):
        touches = {r.touches for r in R.charger(FICHIER)}
        for attendu in ("Meta+E", "Meta+D", "Meta+L", "Meta+V", "Meta+R", "Meta+I", "Alt+Tab", "Alt+F4",
                        "Ctrl+Shift+Esc", "Meta+Shift+S"):
            self.assertIn(attendu, touches)

    def test_colonnes_source_et_doublons(self):
        with self.assertRaises(ValueError) as e:
            R.charger(fichier_tsv(("Cat", "Meta+E", "Action", "", "kde", "en trop")))
        self.assertIn("6 colonnes", str(e.exception))
        with self.assertRaises(ValueError) as e:
            R.charger(fichier_tsv(("Cat", "Meta+E", "Action", "", "windows")))
        self.assertIn("source", str(e.exception))
        with self.assertRaises(ValueError) as e:
            R.charger(fichier_tsv(("Cat", "Meta+E", "A", "", "kde"), ("Cat", "Meta+E", "B", "", "kde")))
        self.assertIn("déjà donné ligne 2", str(e.exception))
        with self.assertRaises(ValueError):
            R.charger(fichier_tsv(("", "Meta+E", "A", "", "kde")))

    def test_le_numero_de_ligne_est_dans_l_erreur(self):
        with self.assertRaises(ValueError) as e:
            R.charger(fichier_tsv(("Cat", "Meta+E", "A", "", "kde"), ("Cat", "Meta+Meta+X", "B", "", "kde")))
        self.assertRegex(str(e.exception), r":3 : ")

    def test_une_variable_d_environnement_choisit_le_fichier(self):
        chemin = fichier_tsv(("Cat", "Meta+Z", "A", "", "kde"))
        os.environ["BINIXX_RACCOURCIS"] = chemin
        self.addCleanup(os.environ.pop, "BINIXX_RACCOURCIS")
        self.assertEqual([r.touches for r in R.charger()], ["Meta+Z"])


class Touches(unittest.TestCase):
    def test_codes_de_qt(self):
        self.assertEqual(R.code_qt("Meta+E"), 0x10000045)
        self.assertEqual(R.code_qt("Meta+Shift+S"), 0x10000000 + 0x02000000 + 0x53)
        self.assertEqual(R.code_qt("Ctrl+Shift+Esc"), 0x04000000 + 0x02000000 + 0x01000000)
        self.assertEqual(R.code_qt("Alt+F4"), 0x08000000 + 0x01000033)
        self.assertEqual(R.code_qt("Meta+Left"), 0x10000000 + 0x01000012)
        self.assertEqual(R.code_qt("Meta+."), 0x10000000 + 0x2E)
        self.assertEqual(R.code_qt("Meta+1"), 0x10000000 + 0x31)
        self.assertEqual(R.code_qt("Print"), 0x01000009)

    def test_on_retrouve_l_ecriture_a_partir_du_code(self):
        for r in R.charger(FICHIER):
            self.assertEqual(R.ecriture(R.code_qt(r.touches)), r.touches)
        self.assertEqual(R.ecriture(0x10000000 + 0x7F00), "Meta+0x7f00")

    def test_affichage_en_francais(self):
        self.assertEqual(R.affichage("Meta+Shift+S"), ["Windows", "Maj", "S"])
        self.assertEqual(R.affichage("Ctrl+Alt+Del"), ["Ctrl", "Alt", "Suppr"])
        self.assertEqual(R.affichage("Ctrl+Shift+Esc"), ["Ctrl", "Maj", "Échap"])
        self.assertEqual(R.affichage("Meta+Left"), ["Windows", "←"])
        self.assertEqual(R.affichage("Print"), ["Impr. écran"])

    def test_ecritures_refusees(self):
        for mauvaise in ("E", "Meta+Meta+E", "Hyper+E", "Meta+é", "Meta+", "", "Meta+F13", "Ctrl+Alt+Esc+Tab"):
            with self.assertRaises(ValueError, msg=mauvaise):
                R.code_qt(mauvaise)

    def test_touches_de_fonction_et_impression_seules(self):
        self.assertEqual(R.code_qt("F5"), 0x01000034)
        self.assertEqual(R.code_qt("Print"), 0x01000009)


class Recherche(unittest.TestCase):
    def setUp(self):
        self.liste = R.charger(FICHIER)

    def touches(self, requete):
        return [r.touches for r in R.chercher(self.liste, requete)]

    def test_requete_vide_donne_tout(self):
        self.assertEqual(len(R.chercher(self.liste, "  ")), len(self.liste))

    def test_sans_accents_ni_majuscules(self):
        self.assertIn("Alt+Tab", self.touches("FENETRE"))
        self.assertIn("Meta+Shift+S", self.touches("capture zone"))

    def test_par_les_touches(self):
        self.assertIn("Meta+E", self.touches("windows e"))
        self.assertIn("Meta+E", self.touches("meta e"))
        self.assertIn("Ctrl+Shift+Esc", self.touches("ctrl maj echap"))

    def test_tous_les_mots_doivent_correspondre(self):
        self.assertEqual(self.touches("capture presse-papiers verrouiller"), [])

    def test_rien_ne_correspond(self):
        self.assertEqual(self.touches("zzzz"), [])


class Lecture(unittest.TestCase):
    def test_composants(self):
        self.assertEqual(R.composants(COMPOSANTS), ["/component/kwin", "/component/org_kde_dolphin_desktop"])
        self.assertEqual(R.composants("pas du json"), [])
        self.assertEqual(R.composants(json.dumps({"data": []})), [])

    def test_actions_du_composant(self):
        actions = R.actions_du_composant(KWIN)
        self.assertEqual(actions[0], ("kwin", "Show Desktop", [0x10000044]))
        self.assertEqual(actions[1], ("kwin", "Walk Through Windows", [0x9000001]))
        self.assertEqual(actions[2], ("kwin", "Sans touche", []))
        self.assertEqual(R.actions_du_composant("pas du json"), [])

    def test_une_sequence_de_plusieurs_touches_est_lue_a_plat(self):
        sortie = reponse(["a", "a", "c", "c", "default", "default", [[[1, 2]], [[3]]], []])
        self.assertEqual(R.actions_du_composant(sortie), [("c", "a", [1, 2, 3])])

    def test_enregistres(self):
        faux = Faux()
        registre = R.enregistres(faux)
        self.assertEqual(registre[0x10000044], [("kwin", "Show Desktop")])
        self.assertEqual(registre[0x10000045], [("org.kde.dolphin.desktop", "_launch")])
        self.assertNotIn(0, registre)
        # une commande par composant, sans shell, vers le service de raccourcis
        self.assertEqual(len(faux.appels), 3)
        for appel in faux.appels:
            self.assertEqual(appel[:5], ["busctl", "--user", "--json=short", "call", "org.kde.kglobalaccel"])

    def test_certaines_versions_veulent_le_contexte_en_argument(self):
        faux = Faux(echoue_sans_argument=True)
        registre = R.enregistres(faux)
        self.assertEqual(registre[0x10000044], [("kwin", "Show Desktop")])
        self.assertTrue(any(appel[-2:] == ["s", ""] for appel in faux.appels))

    def test_pas_de_session(self):
        self.assertIsNone(R.enregistres(Faux(composants=None)))
        self.assertIsNone(R.enregistres(Faux(composants="n'importe quoi")))
        self.assertIsNone(R.enregistres(Faux(composants=json.dumps({"data": [[]]}))))

    def test_un_composant_illisible_n_empeche_pas_les_autres(self):
        def run(argv, timeout=120):
            if "allComponents" in argv:
                return 0, COMPOSANTS
            return (0, KWIN) if "/component/kwin" in argv else (1, "")
        registre = R.enregistres(run)
        self.assertIn(0x10000044, registre)
        self.assertNotIn(0x10000045, registre)

    def test_verifier(self):
        liste = [r for r in R.charger(FICHIER) if r.touches in ("Meta+D", "Meta+E", "Meta+L")]
        presents, absents = R.verifier(liste, R.enregistres(Faux()))
        self.assertEqual([r.touches for r, _ in presents], ["Meta+D", "Meta+E"])
        self.assertEqual([r.touches for r in absents], ["Meta+L"])
        self.assertEqual(presents[0][1], [("kwin", "Show Desktop")])

    def test_verifier_sans_registre_tout_manque(self):
        presents, absents = R.verifier(R.charger(FICHIER), None)
        self.assertEqual(presents, [])
        self.assertEqual(len(absents), len(R.charger(FICHIER)))


class LigneDeCommande(unittest.TestCase):
    def lancer(self, *argv, run=None):
        sortie = []
        code = R.main(list(argv), run=run or Faux(), sortie=sortie.append)
        return code, "\n".join(sortie)

    def setUp(self):
        self.vieux = os.environ.get("BINIXX_RACCOURCIS")
        # un petit fichier : une touche enregistrée par KDE, une absente
        os.environ["BINIXX_RACCOURCIS"] = fichier_tsv(("Cat", "Meta+D", "Afficher le bureau", "", "kde"),
                                                      ("Cat", "Meta+L", "Verrouiller", "", "kde"))

    def tearDown(self):
        if self.vieux is None:
            os.environ.pop("BINIXX_RACCOURCIS", None)
        else:
            os.environ["BINIXX_RACCOURCIS"] = self.vieux

    def test_liste(self):
        code, texte = self.lancer("liste")
        self.assertEqual(code, 0)
        self.assertIn("Windows + D", texte)
        self.assertIn("Verrouiller", texte)

    def test_verifier_echoue_si_une_touche_manque_et_la_nomme(self):
        code, texte = self.lancer("verifier")
        self.assertEqual(code, 1)
        self.assertIn("ok       Meta+D", texte)
        self.assertIn("kwin / Show Desktop", texte)
        self.assertIn("MANQUE   Meta+L", texte)
        self.assertIn("1 raccourcis enregistrés sur 2", texte)

    def test_verifier_reussit_quand_tout_est_enregistre(self):
        os.environ["BINIXX_RACCOURCIS"] = fichier_tsv(("Cat", "Meta+D", "Afficher le bureau", "", "kde"))
        code, texte = self.lancer("verifier")
        self.assertEqual(code, 0)
        self.assertIn("1 raccourcis enregistrés sur 1", texte)

    def test_sans_session_message_clair(self):
        code, texte = self.lancer("verifier", run=Faux(composants=None))
        self.assertEqual(code, 1)
        self.assertIn("impossible de lire", texte)
        code, texte = self.lancer("registre", run=Faux(composants=None))
        self.assertEqual(code, 1)

    def test_registre(self):
        code, texte = self.lancer("registre")
        self.assertEqual(code, 0)
        self.assertIn("Meta+D", texte)
        self.assertIn("kwin / Show Desktop", texte)
        self.assertIn("Alt+Tab", texte)

    def test_action_inconnue(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            R.main(["bidule"])


class RaccourcisFournisParLImage(unittest.TestCase):
    """Chaque touche de source « binixx » doit être posée par l'image, sur un lanceur qui existe."""

    def test_le_fichier_xdg_est_lu(self):
        fournis = R.touches_du_fichier_xdg(XDG)
        self.assertEqual(fournis["binixx-parametres.desktop"], "Meta+I")
        self.assertEqual(R.touches_du_fichier_xdg("/n/existe/pas"), {})

    def test_chaque_touche_binixx_a_sa_ligne_et_son_lanceur(self):
        fournis = R.touches_du_fichier_xdg(XDG)
        par_touches = {touches: lanceur for lanceur, touches in fournis.items()}
        manquantes = []
        for r in R.charger(FICHIER):
            if r.source != "binixx":
                continue
            lanceur = par_touches.get(r.touches)
            if lanceur is None:
                manquantes.append(f"{r.touches} : aucune ligne _launch dans kglobalshortcutsrc")
            elif not lanceur.startswith("org.kde.") and not os.path.exists(os.path.join(LANCEURS, lanceur)):
                manquantes.append(f"{r.touches} : lanceur {lanceur} absent")
        self.assertEqual(manquantes, [])

    def test_aucune_ligne_posee_par_l_image_ne_sort_du_fichier(self):
        # une touche ajoutée dans kglobalshortcutsrc sans être annoncée à l'utilisateur serait un raccourci caché
        annoncees = {r.touches for r in R.charger(FICHIER)}
        for lanceur, touches in R.touches_du_fichier_xdg(XDG).items():
            self.assertIn(touches, annoncees, lanceur)

    def test_le_lanceur_declare_la_meme_touche_que_le_fichier_xdg(self):
        for lanceur, touches in R.touches_du_fichier_xdg(XDG).items():
            chemin = os.path.join(LANCEURS, lanceur)
            if not lanceur.startswith("binixx-") or not os.path.exists(chemin):
                continue  # lanceur de KDE (Dolphin) : c'est KDE qui décide de ses propres touches
            with open(chemin, encoding="utf-8") as fichier:
                declarees = re.findall(r"^X-KDE-Shortcuts=(.*)$", fichier.read(), re.M)
            self.assertEqual(declarees, [touches], lanceur)

    def test_les_lanceurs_ajoutes_ont_le_necessaire(self):
        for nom in ("binixx-executer", "binixx-gestionnaire-taches"):
            with open(os.path.join(LANCEURS, nom + ".desktop"), encoding="utf-8") as fichier:
                texte = fichier.read()
            for cle in ("Type=Application", "Name=", "Exec=", "Icon=", "Categories="):
                self.assertIn(cle, texte, nom)

    def test_aucun_raccourci_en_double_entre_le_fichier_xdg_et_ses_lanceurs(self):
        touches = list(R.touches_du_fichier_xdg(XDG).values())
        self.assertEqual(len(touches), len(set(touches)))


class Conflits(unittest.TestCase):
    """Une touche annoncée que KDE donne à deux actions : une seule la reçoit, l'autre est ignorée."""

    def registre_disputant_meta_d(self):
        autre = reponse(structure("org.kde.spectacle.desktop", "RecordRegion", 0x10000044))
        composants = json.dumps({"type": "ao", "data": [["/component/kwin", "/component/org_kde_spectacle_desktop"]]})
        return Faux(composants=composants, reponses={"/component/kwin": KWIN, "/component/org_kde_spectacle_desktop": autre})

    def test_la_touche_disputee_est_signalee(self):
        liste = [r for r in R.charger(FICHIER) if r.touches in ("Meta+D", "Alt+Tab")]
        registre = R.enregistres(self.registre_disputant_meta_d())
        presents, absents = R.verifier(liste, registre)
        disputees = R.conflits(presents)
        self.assertEqual([r.touches for r, _ in disputees], ["Meta+D"])
        self.assertEqual(sorted(disputees[0][1]), [("kwin", "Show Desktop"), ("org.kde.spectacle.desktop", "RecordRegion")])

    def test_deux_actions_d_un_meme_composant_se_disputent_aussi(self):
        composants = json.dumps({"type": "ao", "data": [["/component/kwin"]]})
        kwin = reponse(structure("kwin", "A", 0x10000044), structure("kwin", "B", 0x10000044))
        registre = R.enregistres(Faux(composants=composants, reponses={"/component/kwin": kwin}))
        liste = [r for r in R.charger(FICHIER) if r.touches == "Meta+D"]
        self.assertEqual(len(R.conflits(R.verifier(liste, registre)[0])), 1)

    def test_une_touche_a_un_seul_proprietaire_n_est_pas_un_conflit(self):
        liste = [r for r in R.charger(FICHIER) if r.touches in ("Meta+D", "Meta+E")]
        presents, _ = R.verifier(liste, R.enregistres(Faux()))
        self.assertEqual(R.conflits(presents), [])

    def test_verifier_echoue_et_nomme_les_actions_en_conflit(self):
        vieux = os.environ.get("BINIXX_RACCOURCIS")
        os.environ["BINIXX_RACCOURCIS"] = fichier_tsv(("Cat", "Meta+D", "Afficher le bureau", "", "kde"),
                                                      ("Cat", "Alt+Tab", "Passer d'une fenêtre à l'autre", "", "kde"))
        self.addCleanup(lambda: os.environ.pop("BINIXX_RACCOURCIS") if vieux is None
                        else os.environ.__setitem__("BINIXX_RACCOURCIS", vieux))
        sortie = []
        code = R.main(["verifier"], run=self.registre_disputant_meta_d(), sortie=sortie.append)
        texte = "\n".join(sortie)
        self.assertEqual(code, 1)
        self.assertIn("CONFLIT  Meta+D", texte)
        self.assertIn("org.kde.spectacle.desktop / RecordRegion", texte)
        self.assertIn("kwin / Show Desktop", texte)
        self.assertIn("ok       Alt+Tab", texte)         # sans conflit : un seul propriétaire
        self.assertIn("1 en conflit", texte)

    def test_le_registre_dit_composant_puis_action(self):
        vieux = os.environ.get("BINIXX_RACCOURCIS")
        os.environ["BINIXX_RACCOURCIS"] = FICHIER
        self.addCleanup(lambda: os.environ.pop("BINIXX_RACCOURCIS") if vieux is None
                        else os.environ.__setitem__("BINIXX_RACCOURCIS", vieux))
        sortie = []
        R.main(["registre"], run=Faux(), sortie=sortie.append)
        self.assertIn(f"{'Meta+D':<24} kwin / Show Desktop", "\n".join(sortie))


def ecrire(chemin, texte):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write(texte)


class UneToucheUnProprietaire(unittest.TestCase):
    """Au build, les lanceurs de KDE qui prennent une touche de BinixX OS la perdent (kglobalshortcutsrc)."""

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.apps = os.path.join(self.dossier, "applications")
        self.xdg = os.path.join(self.dossier, "kglobalshortcutsrc")
        ecrire(os.path.join(self.apps, "org.kde.spectacle.desktop"),
               "[Desktop Entry]\nName=Spectacle\nX-KDE-Shortcuts=Print\nActions=A;B;\n\n"
               "[Desktop Action RecordRegion]\nName=Record\nX-KDE-Shortcuts=Meta+R,Meta+Shift+R\n\n"
               "[Desktop Action RectangularRegionScreenShot]\nX-KDE-Shortcuts=Meta+Shift+S\n")
        ecrire(os.path.join(self.apps, "systemsettings.desktop"), "[Desktop Entry]\nName=Paramètres\nX-KDE-Shortcuts=Tools,Meta+I\n")
        ecrire(os.path.join(self.apps, "org.kde.dolphin.desktop"), "[Desktop Entry]\nName=Dolphin\nX-KDE-Shortcuts=Meta+E\n")
        ecrire(os.path.join(self.apps, "binixx-executer.desktop"), "[Desktop Entry]\nName=Exécuter\nX-KDE-Shortcuts=Meta+R\n")
        ecrire(os.path.join(self.apps, "autre.desktop"), "[Desktop Entry]\nName=Sans raccourci\n")
        ecrire(self.xdg, "# test\n[services][org.kde.dolphin.desktop]\n_launch=Meta+E\n\n[services][binixx-executer.desktop]\n_launch=Meta+R\n")
        self.liste = R.charger(fichier_tsv(
            ("Cat", "Meta+R", "Exécuter", "", "binixx"), ("Cat", "Meta+I", "Paramètres", "", "binixx"),
            ("Cat", "Meta+E", "Explorateur", "", "binixx"), ("Cat", "Meta+Shift+S", "Capture", "", "kde")))

    def calculer(self):
        return R.surcharges(self.liste, self.apps, self.xdg)

    def test_lire_les_touches_d_un_lanceur(self):
        self.assertEqual(R.touches_du_lanceur(os.path.join(self.apps, "org.kde.spectacle.desktop")),
                         {"_launch": ["Print"], "RecordRegion": ["Meta+R", "Meta+Shift+R"],
                          "RectangularRegionScreenShot": ["Meta+Shift+S"]})
        self.assertEqual(R.touches_du_lanceur(os.path.join(self.apps, "autre.desktop")), {})
        self.assertEqual(R.touches_du_lanceur("/n/existe/pas.desktop"), {})

    def test_une_touche_de_binixx_est_retiree_aux_autres_lanceurs(self):
        retirees = self.calculer()
        self.assertEqual(retirees["org.kde.spectacle.desktop"], {"RecordRegion": ["Meta+Shift+R"]})
        self.assertEqual(retirees["systemsettings.desktop"], {"_launch": ["Tools"]})   # la touche « Tools » reste

    def test_les_touches_de_kde_ne_sont_pas_touchees(self):
        retirees = self.calculer()
        self.assertNotIn("RectangularRegionScreenShot", retirees["org.kde.spectacle.desktop"])   # Windows + Maj + S : source kde
        self.assertNotIn("_launch", retirees["org.kde.spectacle.desktop"])                        # Print

    def test_nos_lanceurs_et_le_lanceur_choisi_par_l_image_restent(self):
        retirees = self.calculer()
        self.assertNotIn("binixx-executer.desktop", retirees)
        self.assertNotIn("org.kde.dolphin.desktop", retirees)      # Meta+E : l'image le lui donne elle-même
        self.assertNotIn("autre.desktop", retirees)

    def lire(self, nom):
        with open(os.path.join(self.apps, nom), encoding="utf-8") as fichier:
            return fichier.read()

    def test_les_touches_sont_retirees_dans_les_fichiers_desktop(self):
        avant = self.lire("org.kde.spectacle.desktop")
        R.retirer_des_lanceurs(self.calculer(), self.apps)
        apres = self.lire("org.kde.spectacle.desktop")
        self.assertIn("[Desktop Action RecordRegion]\nName=Record\nX-KDE-Shortcuts=Meta+Shift+R\n", apres)
        self.assertNotIn("Meta+R,", apres)
        # tout le reste du fichier est intact
        self.assertEqual(avant.replace("Meta+R,Meta+Shift+R", "Meta+Shift+R"), apres)
        self.assertIn("X-KDE-Shortcuts=Tools\n", self.lire("systemsettings.desktop"))
        self.assertEqual(self.lire("org.kde.dolphin.desktop"), "[Desktop Entry]\nName=Dolphin\nX-KDE-Shortcuts=Meta+E\n")

    def test_un_lanceur_qui_perd_toutes_ses_touches_n_a_plus_de_ligne(self):
        ecrire(os.path.join(self.apps, "seul.desktop"), "[Desktop Entry]\nName=Seul\nX-KDE-Shortcuts=Meta+R\nExec=seul\n")
        R.retirer_des_lanceurs(self.calculer(), self.apps)
        self.assertEqual(self.lire("seul.desktop"), "[Desktop Entry]\nName=Seul\nExec=seul\n")
        self.assertEqual(R.touches_du_lanceur(os.path.join(self.apps, "seul.desktop")), {})

    def test_apres_la_reecriture_il_ne_reste_aucun_conflit(self):
        R.retirer_des_lanceurs(self.calculer(), self.apps)
        self.assertEqual(self.calculer(), {})

    def test_recommencer_ne_change_plus_rien(self):
        R.retirer_des_lanceurs(self.calculer(), self.apps)
        un = {nom: self.lire(nom) for nom in os.listdir(self.apps)}
        R.retirer_des_lanceurs(self.calculer(), self.apps)
        self.assertEqual({nom: self.lire(nom) for nom in os.listdir(self.apps)}, un)

    def test_une_touche_du_meme_nom_dans_une_autre_action_n_est_pas_touchee(self):
        ecrire(os.path.join(self.apps, "deux.desktop"),
               "[Desktop Entry]\nX-KDE-Shortcuts=Meta+R\n\n[Desktop Action Autre]\nX-KDE-Shortcuts=Meta+Alt+R\n")
        retirees = self.calculer()
        self.assertEqual(retirees["deux.desktop"], {"_launch": []})
        R.retirer_des_lanceurs(retirees, self.apps)
        self.assertEqual(self.lire("deux.desktop"), "[Desktop Entry]\n\n[Desktop Action Autre]\nX-KDE-Shortcuts=Meta+Alt+R\n")

    def test_decrire_les_retraits(self):
        retirees = self.calculer()
        avant = {nom: R.touches_du_lanceur(os.path.join(self.apps, nom)) for nom in retirees}
        self.assertEqual(R.decrire_retraits(avant, retirees), [
            "org.kde.spectacle.desktop / RecordRegion : Meta+R, Meta+Shift+R -> Meta+Shift+R",
            "systemsettings.desktop / _launch : Tools, Meta+I -> Tools"])

    def test_ligne_de_commande(self):
        journal = os.path.join(self.dossier, "journal.txt")
        anciens = {cle: os.environ.get(cle) for cle in
                   ("BINIXX_RACCOURCIS", "BINIXX_LANCEURS", "BINIXX_XDG_RACCOURCIS", "BINIXX_JOURNAL_RETRAITS")}
        os.environ.update({"BINIXX_RACCOURCIS": fichier_tsv(("Cat", "Meta+R", "Exécuter", "", "binixx"),
                                                            ("Cat", "Meta+I", "Paramètres", "", "binixx")),
                           "BINIXX_LANCEURS": self.apps, "BINIXX_XDG_RACCOURCIS": self.xdg,
                           "BINIXX_JOURNAL_RETRAITS": journal})
        try:
            sortie = []
            self.assertEqual(R.main(["surcharger", "--verifier"], sortie=sortie.append), 1)       # des conflits au départ
            self.assertIn("CONFLIT  org.kde.spectacle.desktop / RecordRegion", "\n".join(sortie))
            sortie = []
            self.assertEqual(R.main(["surcharger"], sortie=sortie.append), 0)
            self.assertIn("touche retirée : systemsettings.desktop / _launch : Tools, Meta+I -> Tools", "\n".join(sortie))
            with open(journal, encoding="utf-8") as fichier:
                self.assertIn("org.kde.spectacle.desktop / RecordRegion : Meta+R, Meta+Shift+R -> Meta+Shift+R", fichier.read())
            sortie = []
            self.assertEqual(R.main(["surcharger", "--verifier"], sortie=sortie.append), 0)       # plus aucun après
            self.assertIn("0 conflits", "\n".join(sortie))
            sortie = []
            self.assertEqual(R.main(["surcharger"], sortie=sortie.append), 0)                     # relancer : rien de plus
            self.assertIn("0 touches retirées", "\n".join(sortie))
        finally:
            for cle, valeur in anciens.items():
                if valeur is None:
                    os.environ.pop(cle, None)
                else:
                    os.environ[cle] = valeur

    def test_dans_le_depot_ou_dans_l_image_aucun_lanceur_ne_dispute_une_touche_de_binixx(self):
        """Dans l'image, c'est le module 78-raccourcis.sh qui a retiré les touches ; dans le dépôt, il n'y a pas de lanceur de KDE."""
        self.assertEqual(R.surcharges(R.charger(FICHIER), LANCEURS, XDG), {})


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageDuCentre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import theme
        from binixx_centre.pages import raccourcis as page
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.module = page

    def setUp(self):
        os.environ["BINIXX_RACCOURCIS"] = FICHIER
        self.addCleanup(os.environ.pop, "BINIXX_RACCOURCIS", None)
        from binixx_centre import launch
        self.launch = launch
        self.ancien = launch.open_settings
        self.ouverts = []
        launch.open_settings = lambda module="": self.ouverts.append(module) or True
        self.addCleanup(setattr, launch, "open_settings", self.ancien)
        self.pages = []
        self.centre = type("Centre", (), {"show_page": lambda s, cle: self.pages.append(cle)})()

    def ouvrir(self):
        page = self.module.build(self.centre)
        page.resize(980, 700)
        page.show()
        self.app.processEvents()
        return page

    def test_la_page_n_a_pas_de_bouton_et_depend_de_parametres(self):
        self.assertFalse(self.module.MENU)
        self.assertEqual(self.module.PARENT, "parametres")
        self.assertEqual(self.module.KEY, "raccourcis")

    def test_une_ligne_par_raccourci_et_une_section_par_categorie(self):
        page = self.ouvrir()
        liste = R.charger(FICHIER)
        self.assertEqual(len(page.lignes), len(liste))
        self.assertEqual(list(page.sections), R.categories(liste))
        self.assertTrue(all(rangee.isVisible() for rangee in page.lignes))
        self.assertFalse(page.vide.isVisible())
        page.close()

    def test_les_touches_sont_dessinees_avec_les_noms_francais(self):
        page = self.ouvrir()
        rangee = next(r for r in page.lignes if r.element.touches == "Meta+Shift+S")
        self.assertEqual(rangee.touches.libelles, ["Windows", "Maj", "S"])
        self.assertGreater(rangee.touches.sizeHint().width(), 100)
        image = rangee.touches.grab()
        self.assertFalse(image.isNull())
        page.close()

    def test_la_recherche_filtre_les_lignes_et_les_sections(self):
        page = self.ouvrir()
        page.recherche.setText("capture")
        self.app.processEvents()
        visibles = [r.element.touches for r in page.lignes if r.isVisible()]
        self.assertIn("Meta+Shift+S", visibles)
        self.assertNotIn("Meta+L", visibles)
        self.assertTrue(page.sections["Saisie et captures d'écran"].isVisible())
        self.assertFalse(page.sections["Session"].isVisible())
        self.assertFalse(page.pied.isVisible())
        page.recherche.setText("")
        self.app.processEvents()
        self.assertTrue(all(r.isVisible() for r in page.lignes))
        self.assertTrue(page.pied.isVisible())
        page.close()

    def test_rien_ne_correspond(self):
        page = self.ouvrir()
        page.recherche.setText("zzzz")
        self.app.processEvents()
        self.assertFalse(any(r.isVisible() for r in page.lignes))
        self.assertTrue(page.vide.isVisible())
        page.close()

    def test_personnaliser_ouvre_les_raccourcis_de_kde(self):
        page = self.ouvrir()
        page.personnaliser.bouton.click()
        self.assertEqual(self.ouverts, ["kcm_keys"])
        page.close()

    def test_retour_aux_parametres(self):
        page = self.ouvrir()
        from PySide6.QtWidgets import QPushButton
        retour = next(b for b in page.findChildren(QPushButton) if b.text().startswith("←"))
        retour.click()
        self.assertEqual(self.pages, ["parametres"])
        page.close()

    def test_sans_fichier_la_page_s_ouvre_quand_meme(self):
        os.environ["BINIXX_RACCOURCIS"] = "/n/existe/pas.tsv"
        page = self.ouvrir()
        self.assertEqual(page.lignes, [])
        page.close()

    def test_capture(self):
        if not CAPTURES:
            self.skipTest("BINIXX_CAPTURES non défini")
        os.makedirs(CAPTURES, exist_ok=True)
        page = self.ouvrir()
        page.grab().save(os.path.join(CAPTURES, "raccourcis.png"))
        page.close()


if __name__ == "__main__":
    unittest.main()
