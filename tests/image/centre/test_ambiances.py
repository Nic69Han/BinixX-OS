"""Tests des ambiances : schéma « contraste élevé », outils de Plasma, « Grand texte », ligne de commande, page.

python3 -m unittest discover -s tests/image/centre -p 'test_ambiances.py'   (la partie Qt est ignorée sans PySide6)
"""

import configparser
import json
import os
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
DEPOT = os.path.join(ICI, "../../../system_files")
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import ambiances as A  # noqa: E402
from binixx_centre import icones, taille_texte as T  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

SCHEMA = os.environ.get("BINIXX_SCHEMA_CONTRASTE", os.path.join(DEPOT, "usr/share/color-schemes/BinixXContraste.colors"))
LNF = os.environ.get("BINIXX_LNF", os.path.join(DEPOT, "usr/share/plasma/look-and-feel"))
PARAMETRES = os.environ.get("BINIXX_PARAMETRES", os.path.join(DEPOT, "usr/share/binixx/parametres/parametres.tsv"))
THEMES = {"org.binixx.desktop": "BinixXClair", "org.binixx.dark.desktop": "BinixXSombre"}


class FauxKde:
    """Un faux bureau : kreadconfig6 / kwriteconfig6 sur une table {(fichier, groupe, clé) : valeur}, et les outils de Plasma
    (plasma-apply-lookandfeel, plasma-apply-colorscheme, plasma-apply-cursortheme) qui écrivent comme les vrais."""

    def __init__(self, valeurs=None, absents=(), panne=False, curseur_bloque=False, exige_offscreen=False,
                 sans_effet=()):
        self.valeurs = dict(valeurs or {})
        self.commandes = []
        self.environnements = []
        self.exige_offscreen = exige_offscreen         # comme les vrais outils sans écran : ils plantent sans « offscreen »
        self.sans_effet = set(sans_effet)              # outils qui répondent « réussi » sans rien écrire
        self.absents = set(absents)
        self.panne = panne
        self.curseur_bloque = curseur_bloque

    def __call__(self, argv, timeout=120, env=None):
        self.commandes.append(list(argv))
        self.environnements.append(env)
        nom = argv[0]
        if env is None and nom.startswith("plasma-apply-") and self.exige_offscreen:
            return 1, "qt.qpa.xcb: could not connect to display"
        if nom in self.absents:
            return 127, "commande introuvable"
        if self.panne:
            return 1, ""
        if nom == "kreadconfig6":
            cle = self.cle(argv)
            return 0, self.valeurs.get(cle, "") + "\n"
        if nom == "kwriteconfig6":
            cle = self.cle(argv)
            if self.curseur_bloque and cle[2] == "cursorSize":
                return 1, ""
            if "--delete" in argv:
                self.valeurs.pop(cle, None)
            else:
                self.valeurs[cle] = argv[-1]
            return 0, ""
        if nom in self.sans_effet:
            return 0, ""
        if nom in ("plasma-apply-lookandfeel", "lookandfeeltool"):
            if argv[-1] not in THEMES:
                return 1, "thème inconnu"
            self.valeurs[("kdeglobals", "KDE", "LookAndFeelPackage")] = argv[-1]
            self.valeurs[("kdeglobals", "General", "ColorScheme")] = THEMES[argv[-1]]
            return 0, ""
        if nom == "plasma-apply-colorscheme":
            self.valeurs[("kdeglobals", "General", "ColorScheme")] = argv[-1]
            return 0, ""
        if nom == "plasma-apply-cursortheme":
            if self.curseur_bloque:
                return 1, ""
            self.valeurs[("kcminputrc", "Mouse", "cursorTheme")] = argv[-1]
            if "--size" in argv:
                self.valeurs[("kcminputrc", "Mouse", "cursorSize")] = argv[argv.index("--size") + 1]
            return 0, ""
        return 127, "outil inconnu : " + nom

    @staticmethod
    def cle(argv):
        return argv[argv.index("--file") + 1], argv[argv.index("--group") + 1], argv[argv.index("--key") + 1]

    def couleurs(self):
        return self.valeurs.get(("kdeglobals", "General", "ColorScheme"), "")

    def pointeur(self):
        return self.valeurs.get(("kcminputrc", "Mouse", "cursorSize"), "")


def luminance(rvb):
    def lineaire(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, v, b = (lineaire(c) for c in rvb)
    return 0.2126 * r + 0.7152 * v + 0.0722 * b


def contraste(a, b):
    """Le rapport de contraste (de 1 à 21) de la norme WCAG entre deux couleurs (r, v, b)."""
    haut, bas = sorted((luminance(a), luminance(b)), reverse=True)
    return (haut + 0.05) / (bas + 0.05)


def rvb(texte):
    parties = [int(x) for x in texte.split(",")]
    assert len(parties) == 3 and all(0 <= x <= 255 for x in parties), texte
    return tuple(parties)


def lire_schema():
    lecteur = configparser.ConfigParser(interpolation=None)
    lecteur.optionxform = str
    with open(SCHEMA, encoding="utf-8") as fichier:
        lecteur.read_file(fichier)
    return lecteur


class Ambiances(unittest.TestCase):
    def test_trois_allures(self):
        self.assertEqual(A.CLES, ("aube", "nuit", "contraste"))
        self.assertEqual(len(set(A.CLES)), 3)
        self.assertEqual(len({a.couleurs for a in A.AMBIANCES}), 3)
        self.assertEqual(A.trouver("nuit").titre, "Nuit")
        self.assertIsNone(A.trouver("inconnue"))

    def test_chaque_ambiance_est_decrite_en_francais(self):
        for a in A.AMBIANCES:
            self.assertGreater(len(a.texte), 40, a.cle)
            self.assertEqual(len(a.apercu), 4, a.cle)
            for couleur in a.apercu:
                self.assertRegex(couleur, r"^#[0-9A-Fa-f]{6}$", a.cle)

    def test_les_themes_globaux_posent_les_couleurs_annoncees(self):
        for cle in ("aube", "nuit"):
            ambiance = A.trouver(cle)
            with open(os.path.join(LNF, ambiance.theme, "contents", "defaults"), encoding="utf-8") as fichier:
                self.assertIn(f"ColorScheme={ambiance.couleurs}", fichier.read().splitlines(), cle)
        self.assertEqual(A.trouver("contraste").theme, A.trouver("nuit").theme)   # le contraste part du thème sombre

    def test_les_icones_de_la_page_existent(self):
        for nom in ("sun", "moon", "eye", "type"):
            self.assertIn(nom, icones.ICONES)


class SchemaContrasteEleve(unittest.TestCase):
    GROUPES = ("Button", "Complementary", "Header", "Selection", "Tooltip", "View", "Window")
    ROLES = ("Active", "Inactive", "Link", "Visited", "Negative", "Neutral", "Positive")

    @classmethod
    def setUpClass(cls):
        cls.schema = lire_schema()

    def test_le_fichier_se_presente_comme_un_schema_de_kde(self):
        self.assertEqual(self.schema["General"]["ColorScheme"], "BinixXContraste")
        self.assertEqual(os.path.basename(SCHEMA), "BinixXContraste.colors")
        self.assertEqual(self.schema["General"]["Name"], "BinixX OS contraste élevé")
        self.assertIn("ColorEffects:Disabled", self.schema)
        self.assertIn("ColorEffects:Inactive", self.schema)
        self.assertIn("KDE", self.schema)
        for groupe in self.GROUPES:
            self.assertIn(f"Colors:{groupe}", self.schema, groupe)

    def test_chaque_groupe_a_toutes_ses_couleurs(self):
        attendues = {f"Foreground{r}" for r in self.ROLES + ("Normal",)} | {
            "BackgroundNormal", "BackgroundAlternate", "DecorationFocus", "DecorationHover"}
        for groupe in self.GROUPES:
            section = self.schema[f"Colors:{groupe}"]
            self.assertEqual(set(section), attendues, groupe)
            for couleur in section.values():
                rvb(couleur)

    def test_le_texte_se_lit_tres_bien_sur_son_fond(self):
        """Contraste d'au moins 7:1 (niveau AAA de la norme WCAG) pour le texte normal, sur le fond et sur le fond alterné."""
        for groupe in self.GROUPES:
            section = self.schema[f"Colors:{groupe}"]
            texte = rvb(section["ForegroundNormal"])
            for fond in ("BackgroundNormal", "BackgroundAlternate"):
                self.assertGreaterEqual(contraste(texte, rvb(section[fond])), 7.0, f"{groupe} / {fond}")

    def test_les_autres_textes_se_lisent_aussi(self):
        """Liens, textes grisés, erreurs, avertissements… : au moins 4,5:1 (niveau AA) sur le fond."""
        for groupe in self.GROUPES:
            section = self.schema[f"Colors:{groupe}"]
            fond = rvb(section["BackgroundNormal"])
            for role in self.ROLES:
                self.assertGreaterEqual(contraste(rvb(section[f"Foreground{role}"]), fond), 4.5, f"{groupe} / {role}")

    def test_le_focus_et_le_survol_se_voient(self):
        for groupe in self.GROUPES:
            section = self.schema[f"Colors:{groupe}"]
            fond = rvb(section["BackgroundNormal"])
            for cle in ("DecorationFocus", "DecorationHover"):
                self.assertGreaterEqual(contraste(rvb(section[cle]), fond), 7.0, f"{groupe} / {cle}")

    def test_la_selection_se_detache_du_contenu(self):
        selection = rvb(self.schema["Colors:Selection"]["BackgroundNormal"])
        self.assertGreaterEqual(contraste(selection, rvb(self.schema["Colors:View"]["BackgroundNormal"])), 7.0)
        self.assertGreaterEqual(contraste(selection, rvb(self.schema["Colors:Window"]["BackgroundNormal"])), 7.0)

    def test_les_barres_de_titre(self):
        wm = self.schema["WM"]
        self.assertGreaterEqual(contraste(rvb(wm["activeForeground"]), rvb(wm["activeBackground"])), 7.0)
        self.assertGreaterEqual(contraste(rvb(wm["inactiveForeground"]), rvb(wm["inactiveBackground"])), 7.0)
        # la fenêtre active se distingue de celle qui ne l'est pas
        self.assertGreaterEqual(contraste(rvb(wm["activeBackground"]), rvb(wm["inactiveBackground"])), 7.0)

    def test_l_apercu_de_la_page_montre_les_vraies_couleurs(self):
        fond, texte, accent, barre = (c.lstrip("#").upper() for c in A.trouver("contraste").apercu)
        en_hex = lambda cle: "%02X%02X%02X" % rvb(cle)  # noqa: E731
        self.assertEqual(fond, en_hex(self.schema["Colors:View"]["BackgroundNormal"]))
        self.assertEqual(texte, en_hex(self.schema["Colors:View"]["ForegroundNormal"]))
        self.assertEqual(accent, en_hex(self.schema["Colors:Selection"]["BackgroundNormal"]))
        self.assertEqual(barre, en_hex(self.schema["WM"]["activeBackground"]))


class Allure(unittest.TestCase):
    def test_aube_pose_le_theme_clair_puis_ses_couleurs(self):
        faux = FauxKde({("kdeglobals", "General", "ColorScheme"): "BinixXSombre"})
        reussi, message = A.appliquer("aube", faux)
        self.assertTrue(reussi)
        self.assertEqual(message, "L'ambiance « Aube » est en place.")
        self.assertEqual(faux.couleurs(), "BinixXClair")
        self.assertEqual(faux.commandes[0], ["plasma-apply-lookandfeel", "--apply", "org.binixx.desktop"])
        self.assertEqual(faux.commandes[1], ["plasma-apply-colorscheme", "BinixXClair"])

    def test_nuit(self):
        faux = FauxKde()
        self.assertTrue(A.appliquer("nuit", faux)[0])
        self.assertEqual(faux.couleurs(), "BinixXSombre")
        self.assertEqual(faux.valeurs[("kdeglobals", "KDE", "LookAndFeelPackage")], "org.binixx.dark.desktop")

    def test_contraste_part_du_theme_sombre_et_remplace_les_couleurs(self):
        faux = FauxKde()
        self.assertTrue(A.appliquer("contraste", faux)[0])
        self.assertEqual(faux.couleurs(), "BinixXContraste")
        self.assertEqual(faux.valeurs[("kdeglobals", "KDE", "LookAndFeelPackage")], "org.binixx.dark.desktop")

    def test_contraste_enleve_une_couleur_d_accentuation_choisie_a_la_main(self):
        faux = FauxKde({("kdeglobals", "General", "AccentColor"): "255,0,0"})
        A.appliquer("contraste", faux)
        self.assertNotIn(("kdeglobals", "General", "AccentColor"), faux.valeurs)
        autre = FauxKde({("kdeglobals", "General", "AccentColor"): "255,0,0"})
        A.appliquer("nuit", autre)
        self.assertIn(("kdeglobals", "General", "AccentColor"), autre.valeurs)       # les autres allures n'y touchent pas

    def test_sans_plasma_apply_lookandfeel_on_essaie_lookandfeeltool(self):
        faux = FauxKde(absents={"plasma-apply-lookandfeel"})
        self.assertTrue(A.appliquer("nuit", faux)[0])
        self.assertIn(["lookandfeeltool", "--apply", "org.binixx.dark.desktop"], faux.commandes)

    def test_sans_plasma_apply_colorscheme_on_ne_pretend_pas(self):
        """Écrire seulement le nom du schéma ne changerait rien à l'écran (les couleurs sont copiées par l'outil) : échec honnête."""
        faux = FauxKde(absents={"plasma-apply-lookandfeel", "lookandfeeltool", "plasma-apply-colorscheme"})
        reussi, message = A.appliquer("contraste", faux)
        self.assertFalse(reussi)
        self.assertIn("n'a pas pu être appliquée", message)
        self.assertEqual(faux.couleurs(), "")
        self.assertFalse([c for c in faux.commandes if c[0] == "kwriteconfig6" and "ColorScheme" in c])

    def test_le_bureau_ne_repond_pas(self):
        reussi, message = A.appliquer("nuit", FauxKde(panne=True))
        self.assertFalse(reussi)
        self.assertIn("ne répond pas", message)
        self.assertIn("« Nuit »", message)

    def test_on_ne_croit_pas_le_code_de_sortie_d_un_outil(self):
        """Un outil qui réussit sans rien changer ne fait pas dire « c'est en place »."""
        faux = FauxKde()
        faux.valeurs[("kdeglobals", "General", "ColorScheme")] = "BinixXClair"

        def menteur(argv, timeout=120, env=None):
            if argv[0].startswith("plasma-apply") or argv[0] == "lookandfeeltool":
                return 0, ""
            return faux(argv, timeout)

        reussi, _ = A.appliquer("nuit", menteur)
        self.assertFalse(reussi)

    def test_ambiance_inconnue(self):
        reussi, message = A.appliquer("disco", FauxKde())
        self.assertFalse(reussi)
        self.assertIn("aube, nuit, contraste", message)

    def test_aucune_commande_ne_passe_par_un_shell(self):
        faux = FauxKde()
        for cle in A.CLES:
            A.appliquer(cle, faux)
        A.activer_grand_texte(faux, "/tmp/binixx-test-m1.json", "/tmp/binixx-test-t1.json")
        for argv in faux.commandes:
            self.assertIsInstance(argv, list)
            self.assertTrue(all(isinstance(x, str) for x in argv))
            self.assertIn(argv[0], {"kreadconfig6", "kwriteconfig6", "plasma-apply-lookandfeel",
                                    "plasma-apply-colorscheme", "plasma-apply-cursortheme"})
        for chemin in ("/tmp/binixx-test-m1.json", "/tmp/binixx-test-t1.json"):
            if os.path.exists(chemin):
                os.remove(chemin)

    def test_reconnaitre_l_ambiance_en_cours(self):
        for cle, schema in (("aube", "BinixXClair"), ("nuit", "BinixXSombre"), ("contraste", "BinixXContraste")):
            faux = FauxKde({("kdeglobals", "General", "ColorScheme"): schema})
            self.assertEqual(A.ambiance_actuelle(faux).cle, cle)
        for schema in ("BreezeDark", "MonSchema", ""):
            faux = FauxKde({("kdeglobals", "General", "ColorScheme"): schema})
            self.assertIsNone(A.ambiance_actuelle(faux), schema)
        self.assertIsNone(A.ambiance_actuelle(FauxKde(panne=True)))


class SansEcran(unittest.TestCase):
    """Les outils de Plasma plantent sans écran (ssh, test VM) : on leur donne la plateforme « offscreen »."""

    def setUp(self):
        self.anciens = {cle: os.environ.pop(cle, None) for cle in ("WAYLAND_DISPLAY", "DISPLAY")}
        self.addCleanup(self.rendre)

    def rendre(self):
        for cle in ("WAYLAND_DISPLAY", "DISPLAY"):
            os.environ.pop(cle, None)
            if self.anciens[cle] is not None:
                os.environ[cle] = self.anciens[cle]

    def test_sans_ecran_les_outils_de_plasma_tournent_en_offscreen(self):
        faux = FauxKde(exige_offscreen=True)
        reussi, _ = A.appliquer("contraste", faux)
        self.assertTrue(reussi)
        self.assertEqual(faux.couleurs(), "BinixXContraste")
        outils = [(c, e) for c, e in zip(faux.commandes, faux.environnements) if c[0].startswith("plasma-apply-")]
        self.assertTrue(outils)
        for commande, env in outils:
            self.assertEqual(env, {"QT_QPA_PLATFORM": "offscreen"}, commande)

    def test_kreadconfig6_et_kwriteconfig6_n_ont_pas_besoin_d_ecran(self):
        faux = FauxKde()
        A.appliquer("nuit", faux)
        for commande, env in zip(faux.commandes, faux.environnements):
            if commande[0] in ("kreadconfig6", "kwriteconfig6"):
                self.assertIsNone(env, commande)

    def test_avec_un_ecran_on_ne_change_rien(self):
        os.environ["WAYLAND_DISPLAY"] = "wayland-0"
        faux = FauxKde()
        A.appliquer("nuit", faux)
        self.assertEqual([e for e in faux.environnements if e is not None], [])

    def test_le_pointeur_aussi(self):
        faux = FauxKde(exige_offscreen=True)
        self.assertTrue(A.poser_pointeur(36, faux))
        self.assertEqual(faux.pointeur(), "36")
        self.assertIn({"QT_QPA_PLATFORM": "offscreen"}, faux.environnements)


class SchemaParDefaut(unittest.TestCase):
    """Sur une installation neuve, le schéma est dans kdedefaults, pas dans kdeglobals : c'est bien Aube."""

    def test_le_schema_de_kdedefaults_fait_foi_tant_que_rien_n_est_choisi(self):
        defaut = os.path.join(os.path.expanduser("~/.config"), "kdedefaults", "kdeglobals")
        faux = FauxKde({(defaut, "General", "ColorScheme"): "BinixXClair"})
        self.assertEqual(A.couleurs_actuelles(faux), "BinixXClair")
        self.assertEqual(A.ambiance_actuelle(faux).cle, "aube")

    def test_un_choix_de_l_utilisateur_passe_avant_les_defauts(self):
        defaut = os.path.join(os.path.expanduser("~/.config"), "kdedefaults", "kdeglobals")
        faux = FauxKde({(defaut, "General", "ColorScheme"): "BinixXClair",
                        ("kdeglobals", "General", "ColorScheme"): "BinixXSombre"})
        self.assertEqual(A.ambiance_actuelle(faux).cle, "nuit")

    def test_rien_nulle_part(self):
        self.assertEqual(A.couleurs_actuelles(FauxKde()), "")
        self.assertIsNone(A.ambiance_actuelle(FauxKde()))

    def test_xdg_config_home_est_respecte(self):
        ancien = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = "/tmp/autre-config"
        self.addCleanup(lambda: os.environ.pop("XDG_CONFIG_HOME") if ancien is None
                        else os.environ.__setitem__("XDG_CONFIG_HOME", ancien))
        faux = FauxKde({("/tmp/autre-config/kdedefaults/kdeglobals", "General", "ColorScheme"): "BinixXSombre"})
        self.assertEqual(A.ambiance_actuelle(faux).cle, "nuit")


class GrandTexte(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.marqueur = os.path.join(self.dossier, "grand-texte.json")
        self.texte = os.path.join(self.dossier, "taille-du-texte.json")

    def activer(self, faux):
        return A.activer_grand_texte(faux, self.marqueur, self.texte)

    def desactiver(self, faux):
        return A.desactiver_grand_texte(faux, self.marqueur, self.texte)

    def actif(self):
        return A.grand_texte_actif(self.marqueur, self.texte)

    def test_activer_agrandit_le_texte_et_le_pointeur(self):
        faux = FauxKde()
        reussi, message = self.activer(faux)
        self.assertTrue(reussi, message)
        self.assertIn("130 %", message)
        self.assertEqual(T.pourcentage_actuel(self.texte), 130)
        self.assertEqual(faux.valeurs[("kdeglobals", "General", "font")], "Noto Sans,13," + "-1,5,400,0,0,0,0,0,0,0,0,0,0,1")
        self.assertEqual(faux.pointeur(), "36")
        self.assertTrue(self.actif())
        self.assertEqual(A.lire_marqueur(self.marqueur), {"curseur": None})    # aucune taille de pointeur écrite avant

    def test_la_commande_du_pointeur_est_celle_de_plasma(self):
        faux = FauxKde()
        self.activer(faux)
        self.assertIn(["plasma-apply-cursortheme", "--size", "36", "breeze_cursors"], faux.commandes)

    def test_le_pointeur_garde_le_theme_choisi(self):
        faux = FauxKde({("kcminputrc", "Mouse", "cursorTheme"): "Oxygen_White"})
        self.activer(faux)
        self.assertIn(["plasma-apply-cursortheme", "--size", "36", "Oxygen_White"], faux.commandes)

    def test_desactiver_remet_tout_comme_avant(self):
        faux = FauxKde({("kcminputrc", "Mouse", "cursorSize"): "32"})
        self.activer(faux)
        self.assertEqual(A.lire_marqueur(self.marqueur), {"curseur": "32"})
        reussi, message = self.desactiver(faux)
        self.assertTrue(reussi, message)
        self.assertEqual(faux.pointeur(), "32")
        self.assertNotIn(("kdeglobals", "General", "font"), faux.valeurs)
        self.assertEqual(T.pourcentage_actuel(self.texte), 100)
        self.assertFalse(os.path.exists(self.marqueur))
        self.assertFalse(self.actif())

    def test_sans_pointeur_ecrit_au_depart_on_revient_a_la_taille_de_kde(self):
        faux = FauxKde()
        self.activer(faux)
        self.desactiver(faux)
        self.assertEqual(faux.pointeur() or "24", "24")

    def test_activer_deux_fois_garde_la_taille_d_origine(self):
        faux = FauxKde({("kcminputrc", "Mouse", "cursorSize"): "32"})
        self.activer(faux)
        self.activer(faux)
        self.assertEqual(A.lire_marqueur(self.marqueur), {"curseur": "32"})
        self.desactiver(faux)
        self.assertEqual(faux.pointeur(), "32")

    def test_un_texte_regle_a_la_main_depuis_est_laisse(self):
        faux = FauxKde()
        self.activer(faux)
        T.appliquer(150, faux, self.texte)
        self.assertFalse(self.actif())                       # le texte n'est plus à 130 %
        reussi, _ = self.desactiver(faux)
        self.assertTrue(reussi)
        self.assertEqual(T.pourcentage_actuel(self.texte), 150)    # la personne l'avait voulu ainsi
        self.assertEqual(faux.pointeur() or "24", "24")

    def test_l_outil_du_pointeur_repond_reussi_sans_rien_ecrire(self):
        """Constaté dans la VM : plasma-apply-cursortheme sort avec le code 0 mais cursorSize reste vide."""
        faux = FauxKde(sans_effet={"plasma-apply-cursortheme"})
        reussi, message = self.activer(faux)
        self.assertTrue(reussi, message)
        self.assertEqual(faux.pointeur(), "36")
        self.assertIn(["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", "36"], faux.commandes)

    def test_pointeur_sans_plasma_apply_cursortheme(self):
        faux = FauxKde(absents={"plasma-apply-cursortheme"})
        reussi, _ = self.activer(faux)
        self.assertTrue(reussi)
        self.assertEqual(faux.pointeur(), "36")

    def test_le_pointeur_ne_se_regle_pas(self):
        faux = FauxKde(curseur_bloque=True)
        reussi, message = self.activer(faux)
        self.assertFalse(reussi)
        self.assertIn("pointeur", message)
        self.assertEqual(T.pourcentage_actuel(self.texte), 130)    # le texte, lui, est agrandi : on le dit

    def test_le_texte_ne_s_agrandit_pas(self):
        faux = FauxKde(panne=True)
        reussi, message = self.activer(faux)
        self.assertFalse(reussi)
        self.assertIn("ne répond pas", message)
        self.assertFalse(self.actif())

    def test_desactiver_quand_ce_n_etait_pas_active(self):
        faux = FauxKde()
        reussi, message = self.desactiver(faux)
        self.assertTrue(reussi)
        self.assertIn("n'était pas activé", message)
        self.assertEqual(faux.commandes, [])

    def test_marqueur_illisible_ou_incomplet(self):
        self.assertIsNone(A.lire_marqueur(self.marqueur))
        for contenu in ("pas du json", "[1, 2]", "{}", '{"autre": 1}'):
            with open(self.marqueur, "w", encoding="utf-8") as f:
                f.write(contenu)
            self.assertIsNone(A.lire_marqueur(self.marqueur), contenu)
        with open(self.marqueur, "w", encoding="utf-8") as f:
            json.dump({"curseur": "abc; rm -rf"}, f)
        self.assertEqual(A.lire_marqueur(self.marqueur), {"curseur": None})   # jamais autre chose qu'un nombre


class LigneDeCommande(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.marqueur = os.path.join(self.dossier, "g.json")
        self.texte = os.path.join(self.dossier, "t.json")

    def lancer(self, *argv, faux=None):
        sortie = []
        code = A.main(list(argv), run=faux or FauxKde(), sortie=sortie.append, chemin_marqueur=self.marqueur,
                      chemin_texte=self.texte)
        return code, "\n".join(sortie)

    def test_liste(self):
        code, texte = self.lancer("liste")
        self.assertEqual(code, 0)
        self.assertEqual(texte.splitlines(), ["aube\tAube", "nuit\tNuit", "contraste\tContraste élevé"])

    def test_etat_puis_appliquer(self):
        faux = FauxKde()
        self.assertEqual(self.lancer("etat", faux=faux), (0, "ambiance=aucune\ngrand-texte=non"))
        self.assertEqual(self.lancer("appliquer", "nuit", faux=faux), (0, "L'ambiance « Nuit » est en place."))
        self.assertEqual(self.lancer("etat", faux=faux), (0, "ambiance=nuit\ngrand-texte=non"))
        self.assertEqual(self.lancer("appliquer", "contraste", faux=faux)[0], 0)
        self.assertEqual(self.lancer("etat", faux=faux), (0, "ambiance=contraste\ngrand-texte=non"))

    def test_grand_texte_oui_non(self):
        faux = FauxKde()
        self.assertEqual(self.lancer("grand-texte", "oui", faux=faux)[0], 0)
        self.assertEqual(self.lancer("etat", faux=faux)[1].splitlines()[1], "grand-texte=oui")
        self.assertEqual(self.lancer("grand-texte", "non", faux=faux)[0], 0)
        self.assertEqual(self.lancer("etat", faux=faux)[1].splitlines()[1], "grand-texte=non")

    def test_les_deux_se_combinent(self):
        faux = FauxKde()
        self.lancer("appliquer", "contraste", faux=faux)
        self.lancer("grand-texte", "oui", faux=faux)
        self.assertEqual(self.lancer("etat", faux=faux), (0, "ambiance=contraste\ngrand-texte=oui"))
        self.lancer("appliquer", "aube", faux=faux)       # changer d'allure ne touche pas à la taille du texte
        self.assertEqual(self.lancer("etat", faux=faux), (0, "ambiance=aube\ngrand-texte=oui"))

    def test_echec_du_bureau(self):
        code, texte = self.lancer("appliquer", "nuit", faux=FauxKde(panne=True))
        self.assertEqual(code, 1)
        self.assertIn("ne répond pas", texte)
        self.assertEqual(self.lancer("grand-texte", "oui", faux=FauxKde(panne=True))[0], 1)

    def test_arguments_invalides(self):
        import contextlib
        import io
        for argv in (["bidule"], ["appliquer"], ["appliquer", "disco"], ["grand-texte", "peut-être"], []):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as erreur:
                A.main(argv, run=FauxKde())
            self.assertEqual(erreur.exception.code, 2, argv)


class DansParametres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PARAMETRES, encoding="utf-8") as fichier:
            cls.lignes = [ligne.rstrip("\n").split("\t") for ligne in fichier if ligne.strip() and not ligne.startswith("#")]

    def ligne(self, nom):
        return next(c for c in self.lignes if c[1] == nom)

    def test_themes_ouvre_la_page(self):
        ligne = self.ligne("Thèmes : clair ou sombre")
        self.assertEqual((ligne[5], ligne[6]), ("page", "ambiances"))
        self.assertIn("mode sombre", ligne[2])
        self.assertIn("ambiances", ligne[2])

    def test_contraste_eleve_est_dans_accessibilite(self):
        ligne = self.ligne("Contraste élevé")
        self.assertEqual((ligne[0], ligne[5], ligne[6], ligne[4]), ("Accessibilité", "page", "ambiances", "eye"))
        self.assertIn("contraste élevé", ligne[2])
        self.assertNotIn("contraste élevé", self.ligne("Accessibilité")[2])      # un seul endroit pour ce mot


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageDuCentre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import theme
        from binixx_centre.pages import ambiances as page
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.module = page

    def setUp(self):
        self.dossier = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.dossier, True)
        self.faux = FauxKde({("kdeglobals", "General", "ColorScheme"): "BinixXClair"})
        self.pages = []
        self.centre = type("Centre", (), {"show_page": lambda s, cle: self.pages.append(cle)})()
        self.anciens = (A.MARQUEUR, T.MARQUEUR, A.launch.run)
        A.MARQUEUR = os.path.join(self.dossier, "g.json")
        T.MARQUEUR = os.path.join(self.dossier, "t.json")
        A.launch.run = self.faux
        self.addCleanup(self.restaurer)

    def restaurer(self):
        A.MARQUEUR, T.MARQUEUR, A.launch.run = self.anciens

    def ouvrir(self):
        page = self.module.build(self.centre)
        page.resize(980, 900)
        page.show()
        self.app.processEvents()
        return page

    def test_la_page_depend_de_parametres_et_a_sa_couleur(self):
        self.assertFalse(self.module.MENU)
        self.assertEqual(self.module.PARENT, "parametres")
        self.assertEqual(self.module.KEY, "ambiances")

    def test_une_carte_par_allure_et_l_ambiance_en_place_est_marquee(self):
        page = self.ouvrir()
        self.assertEqual(list(page.cartes), ["aube", "nuit", "contraste"])
        self.assertEqual(page.cartes["aube"].bouton.text(), "En place")
        self.assertFalse(page.cartes["aube"].bouton.isEnabled())
        self.assertTrue(page.cartes["aube"].apercu.actif)
        for cle in ("nuit", "contraste"):
            self.assertEqual(page.cartes[cle].bouton.text(), "Choisir")
            self.assertTrue(page.cartes[cle].bouton.isEnabled())
            self.assertFalse(page.cartes[cle].apercu.actif)
        self.assertIn("Aube", page.etat.text())
        self.assertEqual(page.grand.bouton.text(), "Activer")
        page.close()

    def test_des_couleurs_personnalisees_sont_dites(self):
        self.faux.valeurs[("kdeglobals", "General", "ColorScheme")] = "MonSchema"
        page = self.ouvrir()
        self.assertIn("personnalisées", page.etat.text())
        for carte in page.cartes.values():
            self.assertEqual(carte.bouton.text(), "Choisir")
        page.close()

    def test_choisir_nuit(self):
        page = self.ouvrir()
        page.cartes["nuit"].bouton.click()
        self.assertEqual(self.faux.couleurs(), "BinixXSombre")
        self.assertEqual(page.cartes["nuit"].bouton.text(), "En place")
        self.assertEqual(page.cartes["aube"].bouton.text(), "Choisir")
        self.assertTrue(page.cartes["aube"].bouton.isEnabled())
        self.assertIn("« Nuit » est en place", page.etat.text())
        page.close()

    def test_choisir_le_contraste_eleve(self):
        page = self.ouvrir()
        page.cartes["contraste"].bouton.click()
        self.assertEqual(self.faux.couleurs(), "BinixXContraste")
        self.assertFalse(page.cartes["contraste"].bouton.isEnabled())
        page.close()

    def test_grand_texte_s_active_et_se_desactive(self):
        page = self.ouvrir()
        page.grand.bouton.click()
        self.assertEqual(T.pourcentage_actuel(), 130)
        self.assertEqual(self.faux.pointeur(), "36")
        self.assertEqual(page.grand.bouton.text(), "Désactiver")
        self.assertIn("130 %", page.etat.text())
        page.grand.bouton.click()
        self.assertEqual(T.pourcentage_actuel(), 100)
        self.assertEqual(page.grand.bouton.text(), "Activer")
        page.close()

    def test_la_page_s_ouvre_sur_ce_qui_est_deja_en_place(self):
        A.appliquer("contraste", self.faux)
        A.activer_grand_texte(self.faux)
        page = self.ouvrir()
        self.assertEqual(page.cartes["contraste"].bouton.text(), "En place")
        self.assertEqual(page.grand.bouton.text(), "Désactiver")
        self.assertIn("Grand texte", page.etat.text())
        page.close()

    def test_echec_du_bureau(self):
        page = self.ouvrir()
        self.faux.panne = True
        page.cartes["nuit"].bouton.click()
        self.assertIn("ne répond pas", page.etat.text())
        self.assertTrue(page.cartes["nuit"].bouton.isEnabled())
        self.assertTrue(page.grand.bouton.isEnabled())
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
        page.grab().save(os.path.join(CAPTURES, "ambiances.png"))
        page.close()


if __name__ == "__main__":
    unittest.main()
