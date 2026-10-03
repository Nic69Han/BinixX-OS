"""Tests de « Récupérer mes fichiers Windows » : analyse, copie sans écrasement, favoris, page.

python3 -m unittest discover -s tests/image/centre -p 'test_migration.py'   (la partie Qt est ignorée sans PySide6)
Un faux profil Windows est fabriqué dans un dossier temporaire ; l'ancien disque et le PC ne sont jamais touchés.
"""

import importlib.machinery
import importlib.util
import json
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
LIBEXEC = os.environ.get("BINIXX_LIBEXEC", os.path.join(ICI, "../../../system_files/usr/libexec/binixx"))
OUTIL = os.path.join(LIBEXEC, "binixx-migrer")
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False


def charger_outil():
    chargeur = importlib.machinery.SourceFileLoader("migrer", OUTIL)
    spec = importlib.util.spec_from_loader("migrer", chargeur)
    module = importlib.util.module_from_spec(spec)
    chargeur.exec_module(module)
    return module


M = charger_outil()


def ecrire(racine, relatif, contenu="x", mode=0o777, mtime=None):
    chemin = os.path.join(racine, relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write(contenu)
    os.chmod(chemin, mode)  # un disque NTFS monté rend tout exécutable
    if mtime:
        os.utime(chemin, (mtime, mtime))
    return chemin


def lire(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return fichier.read()


CHROME = {"roots": {
    "bookmark_bar": {"name": "Barre de favoris", "type": "folder", "children": [
        {"name": "Impôts & taxes", "type": "url", "url": "https://www.impots.gouv.fr/?a=1&b=2"},
        {"name": "Travail", "type": "folder", "children": [
            {"name": "Intranet", "type": "url", "url": "https://intranet.exemple.fr/"}]}]},
    "other": {"name": "Autres favoris", "type": "folder", "children": []},
    "synced": {"name": "Mobile", "type": "folder", "children": []}}}


class Monde(unittest.TestCase):
    """Un disque Windows monté (D:), un PC (maison) vide, et un profil riche."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.disque = os.path.join(self.tmp.name, "media", "WINDOWS")
        self.profil = os.path.join(self.disque, "Users", "Marie")
        self.maison = os.path.join(self.tmp.name, "maison")
        os.makedirs(self.maison)
        p = self.profil
        ecrire(p, "Documents/Lettre.docx", "lettre", mtime=1_600_000_000)
        ecrire(p, "Documents/Compta/2025/Bilan.xlsx", "bilan")
        ecrire(p, "Documents/Fichier accentué été.txt", "accents")
        ecrire(p, "Documents/desktop.ini", "[.ShellClassInfo]")
        ecrire(p, "Documents/~$Lettre.docx", "verrou Word")
        ecrire(p, "Documents/brouillon.tmp", "temporaire")
        ecrire(p, "Desktop/Raccourci.txt", "bureau")
        ecrire(p, "Pictures/Vacances/photo1.jpg", "photo")
        ecrire(p, "Music/chanson.mp3", "musique")
        ecrire(p, "Videos/film.mp4", "video")
        ecrire(p, "Downloads/setup.exe", "installeur")
        ecrire(p, "AppData/Local/Microsoft/Edge/User Data/Default/Bookmarks", json.dumps(CHROME))
        ecrire(p, "AppData/Local/Google/Chrome/User Data/Profile 1/Bookmarks", json.dumps(CHROME))
        ecrire(p, "OneDrive/Fichier.txt", "dans le nuage")
        ecrire(p, "Documents/Outlook/archive.pst", "pst")
        # liens (junctions Windows : « Ma musique » dans Documents) : ne doivent ni boucler ni dupliquer
        os.symlink(os.path.join(p, "Music"), os.path.join(p, "Documents", "Ma musique"))
        os.symlink(p, os.path.join(p, "Documents", "boucle"))
        # profils système à ne pas proposer
        os.makedirs(os.path.join(self.disque, "Users", "Public", "Documents"))
        os.makedirs(os.path.join(self.disque, "Users", "Default", "Documents"))
        ecrire(self.disque, "Windows/System32/x.dll", "système")
        self.fabriquer_firefox()

    def fabriquer_firefox(self):
        dossier = os.path.join(self.profil, "AppData/Roaming/Mozilla/Firefox/Profiles/abcd.default-release")
        os.makedirs(dossier)
        base = sqlite3.connect(os.path.join(dossier, "places.sqlite"))
        base.executescript("""
            CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT);
            CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, type INTEGER, fk INTEGER, parent INTEGER,
                                        position INTEGER, title TEXT, guid TEXT);
            INSERT INTO moz_places VALUES (1, 'https://www.mozilla.org/'), (2, 'https://wiki.exemple.fr/'),
                (3, 'place:sort=8&maxResults=10');
            INSERT INTO moz_bookmarks VALUES
                (1, 2, NULL, 0, 0, '', 'root________'),
                (2, 2, NULL, 1, 0, 'menu', 'menu________'),
                (3, 2, NULL, 1, 1, 'toolbar', 'toolbar_____'),
                (4, 2, NULL, 1, 2, 'tags', 'tags________'),
                (5, 2, NULL, 1, 3, 'unfiled', 'unfiled_____'),
                (6, 2, NULL, 1, 4, 'mobile', 'mobile______'),
                (10, 1, 1, 3, 0, 'Mozilla', 'aaaaaaaaaaaa'),
                (11, 2, NULL, 2, 0, 'Wikis', 'bbbbbbbbbbbb'),
                (12, 1, 2, 11, 0, 'Wiki interne', 'cccccccccccc'),
                (13, 2, NULL, 4, 0, 'important', 'dddddddddddd'),
                (14, 1, 1, 13, 0, NULL, 'eeeeeeeeeeee'),
                (15, 1, 3, 3, 1, 'Requête', 'ffffffffffff');
        """)
        base.commit()
        base.close()

    def tearDown(self):
        self.tmp.cleanup()

    def copier(self, cles=None, **options):
        return M.copier(self.profil, cles, maison=self.maison, **options)


class Analyse(Monde):
    def test_les_profils_des_disques_montes(self):
        sources = M.trouver_sources([os.path.join(self.tmp.name, "media")])
        self.assertEqual([(s["nom"], s["disque"]) for s in sources], [("Marie", "WINDOWS")])  # ni Public ni Default

    def test_une_copie_de_profil_sur_une_cle_usb(self):
        cle = os.path.join(self.tmp.name, "usb", "SAUVEGARDE")
        ecrire(cle, "Documents/a.txt")
        ecrire(cle, "Images/b.jpg")
        sources = M.trouver_sources([os.path.join(self.tmp.name, "usb")])
        self.assertEqual([s["nom"] for s in sources], ["SAUVEGARDE"])

    def test_le_contenu_du_profil(self):
        infos = M.analyser(self.profil)
        par_cle = {c["cle"]: c for c in infos["categories"]}
        self.assertEqual(set(par_cle), {"documents", "bureau", "images", "musique", "videos", "telechargements"})
        # desktop.ini, ~$verrou, .tmp, liens ignorés ; les .pst comptent comme des fichiers du dossier Documents
        self.assertEqual(par_cle["documents"]["fichiers"], 4)
        self.assertEqual(infos["navigateurs"], ["Chrome", "Edge", "Firefox"])
        self.assertTrue(infos["onedrive"])
        self.assertEqual(infos["pst"], [os.path.join("Documents", "Outlook", "archive.pst")])
        self.assertTrue(infos["profil_windows"])

    def test_noms_francais_et_casse(self):
        fr = os.path.join(self.tmp.name, "fr")
        for nom in ("DOCUMENTS", "bureau", "Images", "Musique", "VIDÉOS", "Téléchargements"):
            ecrire(fr, f"{nom}/f.txt")
        self.assertEqual(set(M.dossiers_du_profil(fr)),
                         {"documents", "bureau", "images", "musique", "videos", "telechargements"})

    def test_un_dossier_quelconque_est_copiable_en_entier(self):
        autre = os.path.join(self.tmp.name, "Mes affaires")
        ecrire(autre, "a/b.txt")
        infos = M.analyser(autre)
        self.assertEqual([c["cle"] for c in infos["categories"]], ["tout"])
        self.assertFalse(infos["profil_windows"])

    def test_dossier_introuvable(self):
        with self.assertRaises(FileNotFoundError):
            M.analyser(os.path.join(self.tmp.name, "rien"))


class Copie(Monde):
    def test_copie_complete_dans_les_dossiers_du_pc(self):
        bilan = self.copier()
        m = self.maison
        self.assertEqual(lire(os.path.join(m, "Documents", "Lettre.docx")), "lettre")
        self.assertEqual(lire(os.path.join(m, "Documents", "Compta", "2025", "Bilan.xlsx")), "bilan")
        self.assertEqual(lire(os.path.join(m, "Documents", "Fichier accentué été.txt")), "accents")
        self.assertEqual(lire(os.path.join(m, "Desktop", "Raccourci.txt")), "bureau")
        self.assertEqual(lire(os.path.join(m, "Pictures", "Vacances", "photo1.jpg")), "photo")
        self.assertEqual(lire(os.path.join(m, "Music", "chanson.mp3")), "musique")
        self.assertEqual(lire(os.path.join(m, "Videos", "film.mp4")), "video")
        self.assertEqual(lire(os.path.join(m, "Downloads", "setup.exe")), "installeur")
        self.assertEqual(bilan["copies"], 9)  # 4 Documents + Bureau, Images, Musique, Vidéos, Téléchargements
        self.assertEqual(bilan["erreurs"], [])
        # rien de parasite ni de lien copié
        for interdit in ("desktop.ini", "~$Lettre.docx", "brouillon.tmp", "Ma musique", "boucle"):
            self.assertFalse(os.path.lexists(os.path.join(m, "Documents", interdit)), interdit)
        self.assertFalse(os.path.exists(os.path.join(m, "Documents", "Ma musique", "chanson.mp3")))

    def test_les_droits_sont_normalises_et_la_date_conservee(self):
        self.copier(["documents"])
        cible = os.path.join(self.maison, "Documents", "Lettre.docx")
        self.assertEqual(stat.S_IMODE(os.stat(cible).st_mode), 0o644)  # pas « exécutable » comme sur NTFS
        self.assertEqual(int(os.stat(cible).st_mtime), 1_600_000_000)

    def test_ce_qui_n_est_pas_choisi_n_est_pas_copie(self):
        self.copier(["images"])
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Pictures", "Vacances", "photo1.jpg")))
        self.assertFalse(os.path.exists(os.path.join(self.maison, "Documents")) and
                         os.path.exists(os.path.join(self.maison, "Documents", "Lettre.docx")))

    def test_les_dossiers_du_pc_suivent_la_langue(self):
        os.makedirs(os.path.join(self.maison, ".config"))
        ecrire(self.maison, ".config/user-dirs.dirs",
               'XDG_DOCUMENTS_DIR="$HOME/Documents"\nXDG_DESKTOP_DIR="$HOME/Bureau"\n'
               'XDG_PICTURES_DIR="$HOME/Images"\nXDG_DOWNLOAD_DIR="$HOME/Téléchargements"\n')
        env = dict(os.environ)
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.maison, ".config")
        try:
            self.copier(["bureau", "images", "telechargements"])
        finally:
            os.environ.clear()
            os.environ.update(env)
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Bureau", "Raccourci.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Images", "Vacances", "photo1.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Téléchargements", "setup.exe")))

    def test_un_fichier_du_pc_n_est_jamais_ecrase(self):
        ecrire(self.maison, "Documents/Lettre.docx", "version du PC")  # même nom, contenu différent
        bilan = self.copier(["documents"])
        self.assertEqual(lire(os.path.join(self.maison, "Documents", "Lettre.docx")), "version du PC")
        self.assertEqual(lire(os.path.join(self.maison, "Documents", "Lettre (depuis Windows).docx")), "lettre")
        self.assertEqual(bilan["renommes"], [os.path.join("Documents", "Lettre (depuis Windows).docx")])

    def test_un_fichier_identique_n_est_pas_recopie(self):
        ecrire(self.maison, "Documents/Lettre.docx", "lettre")
        bilan = self.copier(["documents"])
        self.assertEqual(bilan["deja_la"], 1)
        self.assertEqual(bilan["renommes"], [])
        self.assertFalse(os.path.exists(os.path.join(self.maison, "Documents", "Lettre (depuis Windows).docx")))

    def test_on_peut_recommencer_sans_doublon(self):
        premier = self.copier()
        second = self.copier()
        self.assertEqual(second["copies"], 0)
        self.assertEqual(second["deja_la"], premier["copies"])
        self.assertEqual(second["renommes"], [])

    def test_trois_versions_d_un_meme_nom(self):
        ecrire(self.maison, "Documents/Lettre.docx", "PC 1")
        ecrire(self.maison, "Documents/Lettre (depuis Windows).docx", "PC 2")
        self.copier(["documents"])
        self.assertEqual(lire(os.path.join(self.maison, "Documents", "Lettre (depuis Windows 2).docx")), "lettre")

    def test_la_source_n_est_jamais_modifiee(self):
        avant = sorted(os.path.join(d, f) for d, _, fs in os.walk(self.disque) for f in fs)
        mtimes = {c: os.stat(c).st_mtime_ns for c in avant}
        self.copier()
        apres = sorted(os.path.join(d, f) for d, _, fs in os.walk(self.disque) for f in fs)
        self.assertEqual(avant, apres)
        self.assertEqual(mtimes, {c: os.stat(c).st_mtime_ns for c in apres})

    def test_dossier_quelconque_range_dans_documents(self):
        autre = os.path.join(self.tmp.name, "Mes affaires")
        ecrire(autre, "a/b.txt", "contenu")
        M.copier(autre, None, maison=self.maison)
        self.assertEqual(lire(os.path.join(self.maison, "Documents", "Mes affaires", "a", "b.txt")), "contenu")

    def test_destination_choisie_un_sous_dossier_par_categorie(self):
        dest = os.path.join(self.tmp.name, "ailleurs")
        self.copier(["documents", "images"], destination=dest)
        self.assertTrue(os.path.exists(os.path.join(dest, "Documents", "Lettre.docx")))
        self.assertTrue(os.path.exists(os.path.join(dest, "Images", "Vacances", "photo1.jpg")))

    def test_pas_assez_de_place_rien_n_est_copie(self):
        ancien = M.shutil.disk_usage
        M.shutil.disk_usage = lambda chemin: type("U", (), {"free": 1024})()
        try:
            with self.assertRaises(OSError) as ctx:
                self.copier(["documents"])
        finally:
            M.shutil.disk_usage = ancien
        self.assertIn("Pas assez de place", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.maison, "Documents", "Lettre.docx")))

    def test_un_fichier_illisible_n_arrete_pas_la_copie(self):
        if os.geteuid() == 0:
            self.skipTest("root lit tout")
        os.chmod(os.path.join(self.profil, "Documents", "Lettre.docx"), 0)
        try:
            bilan = self.copier(["documents"])
        finally:
            os.chmod(os.path.join(self.profil, "Documents", "Lettre.docx"), 0o644)
        self.assertEqual(len(bilan["erreurs"]), 1)
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Documents", "Compta", "2025", "Bilan.xlsx")))

    def test_le_rapport_est_ecrit_et_les_evenements_suivent_l_avancement(self):
        evenements = []
        bilan = self.copier(["documents"], evenement=evenements.append)
        self.assertEqual(evenements[0]["etat"], "debut")
        self.assertEqual(evenements[-1]["etat"], "fin")
        self.assertEqual([e["fait"] for e in evenements if e["etat"] == "avance"], list(range(1, 5)))
        rapport = lire(bilan["rapport"])
        self.assertIn("Fichiers copiés : 4", rapport)
        self.assertIn(self.profil, rapport)

    def test_aucun_dossier_choisi(self):
        with self.assertRaises(ValueError):
            self.copier(["n-existe-pas"])


class Favoris(Monde):
    def test_export_html_des_trois_navigateurs(self):
        chemin, total = M.exporter_favoris(self.profil, maison=self.maison)
        self.assertEqual(total, 2 + 2 + 2)  # Edge, Chrome, Firefox : deux liens chacun (requête « place: » exclue)
        contenu = lire(chemin)
        self.assertTrue(contenu.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"))
        for attendu in ("Favoris Edge", "Favoris Chrome", "Favoris Firefox", "Barre de favoris", "Travail",
                        'HREF="https://www.impots.gouv.fr/?a=1&amp;b=2"', "Impôts &amp; taxes", "Wiki interne",
                        "Barre personnelle", "Menu des favoris", "https://www.mozilla.org/"):
            self.assertIn(attendu, contenu)
        self.assertNotIn("place:", contenu)  # requêtes internes de Firefox
        self.assertNotIn("important", contenu)  # étiquettes : doublons des favoris
        self.assertEqual(contenu.count("https://www.mozilla.org/"), 1)

    def test_sans_navigateur_rien_n_est_ecrit(self):
        vide = os.path.join(self.tmp.name, "vide")
        ecrire(vide, "Documents/a.txt")
        self.assertEqual(M.exporter_favoris(vide, maison=self.maison), (None, 0))

    def test_base_firefox_abimee_ou_json_invalide_n_arretent_rien(self):
        ecrire(self.profil, "AppData/Local/Microsoft/Edge/User Data/Default/Bookmarks", "pas du json")
        with open(os.path.join(self.profil, "AppData/Roaming/Mozilla/Firefox/Profiles/abcd.default-release/places.sqlite"),
                  "wb") as f:
            f.write(b"corrompu")
        chemin, total = M.exporter_favoris(self.profil, maison=self.maison)
        self.assertEqual(total, 2)  # il reste Chrome
        self.assertIn("Favoris Chrome", lire(chemin))


class Outil(Monde):
    def lancer(self, *args):
        env = {**os.environ, "HOME": self.maison, "XDG_CONFIG_HOME": os.path.join(self.maison, ".config")}
        return subprocess.run([OUTIL, *args], capture_output=True, text=True, timeout=120, env=env, check=False)

    def test_analyser_en_json(self):
        fini = self.lancer("analyser", self.profil)
        self.assertEqual(fini.returncode, 0, fini.stderr)
        self.assertEqual(json.loads(fini.stdout)["nom"], "Marie")

    def test_copier_avec_evenements_json(self):
        fini = self.lancer("copier", self.profil, "--dossiers", "documents,images", "--json")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        evenements = [json.loads(ligne) for ligne in fini.stdout.splitlines()]
        self.assertEqual(evenements[0]["etat"], "debut")
        self.assertEqual(evenements[-1]["etat"], "fin")
        self.assertEqual(evenements[-1]["copies"], 5)
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Documents", "Lettre.docx")))

    def test_copier_en_texte(self):
        fini = self.lancer("copier", self.profil, "--dossiers", "bureau")
        self.assertEqual(fini.returncode, 0)
        self.assertIn("1 fichier(s) copié(s)", fini.stdout)

    def test_favoris(self):
        fini = self.lancer("favoris", self.profil)
        self.assertEqual(fini.returncode, 0, fini.stderr)
        donnees = json.loads(fini.stdout)
        self.assertEqual(donnees["liens"], 6)
        self.assertTrue(os.path.exists(donnees["fichier"]))

    def test_sources_ne_plante_pas(self):
        fini = self.lancer("sources")
        self.assertEqual(fini.returncode, 0, fini.stderr)
        self.assertIsInstance(json.loads(fini.stdout), list)

    def test_appels_incorrects(self):
        for args in ((), ("copier",), ("analyser", os.path.join(self.tmp.name, "rien")), ("n-importe-quoi", "x"),
                     ("sources", "x")):
            with self.subTest(args=args):
                self.assertEqual(self.lancer(*args).returncode, 2)

    def test_dossier_choisi_inexistant_dans_dossiers(self):
        fini = self.lancer("copier", self.profil, "--dossiers", "n-existe-pas")
        self.assertEqual(fini.returncode, 2)


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class Page(Monde):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from binixx_centre import launch, theme
        from binixx_centre.pages import migration
        cls.launch, cls.migration = launch, migration
        cls.app.setStyleSheet(theme.STYLE)

    def setUp(self):
        super().setUp()
        self.ancien = (self.migration.OUTIL, os.environ.get("HOME"), os.environ.get("XDG_CONFIG_HOME"))
        self.migration.OUTIL = OUTIL
        os.environ["HOME"] = self.maison
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.maison, ".config")

    def tearDown(self):
        self.migration.OUTIL = self.ancien[0]
        for cle, valeur in (("HOME", self.ancien[1]), ("XDG_CONFIG_HOME", self.ancien[2])):
            if valeur is None:
                os.environ.pop(cle, None)
            else:
                os.environ[cle] = valeur
        super().tearDown()

    def attendre(self, page, condition, secondes=60):
        import time
        fin = time.time() + secondes
        while not condition() and time.time() < fin:
            self.app.processEvents()
            time.sleep(0.02)
        self.assertTrue(condition(), "délai dépassé")

    def test_choisir_un_dossier_puis_copier(self):
        page = self.migration.build(None)
        page.sources = lambda: []
        page.actualiser()
        page.choisir_source(self.profil)
        self.attendre(page, lambda: page.analyse is not None)
        self.assertEqual({c["cle"] for c in page.analyse["categories"]},
                         {"documents", "bureau", "images", "musique", "videos", "telechargements"})
        self.assertTrue(page.cases["favoris"].isEnabled())
        for cle, case in page.cases.items():
            case.setChecked(cle in ("documents", "favoris"))
        if CAPTURES:
            os.makedirs(CAPTURES, exist_ok=True)
            page.resize(1040, 900)
            page.show()
            self.app.processEvents()
            page.grab().save(os.path.join(CAPTURES, "migration.png"))
        page.lancer_la_copie()
        self.attendre(page, lambda: page.bilan is not None)
        self.assertEqual(page.bilan["copies"], 4)
        self.assertTrue(os.path.exists(os.path.join(self.maison, "Documents", "Lettre.docx")))
        self.assertFalse(os.path.exists(os.path.join(self.maison, "Pictures")))  # non coché : non copié
        self.assertTrue(any(f.startswith("Favoris-depuis-Windows") for f in os.listdir(os.path.join(self.maison, "Documents"))))
        self.assertEqual(page.progression.value(), page.progression.maximum())

    def test_rien_de_coche_le_bouton_reste_inactif(self):
        page = self.migration.build(None)
        page.choisir_source(self.profil)
        self.attendre(page, lambda: page.analyse is not None)
        for case in page.cases.values():
            case.setChecked(False)
        page.mettre_a_jour_bouton()
        self.assertFalse(page.bouton_copier.isEnabled())

    def test_sources_detectees_affichees(self):
        page = self.migration.build(None)
        page.sources = lambda: [{"chemin": self.profil, "nom": "Marie", "disque": "WINDOWS"}]
        page.actualiser()
        textes = " ".join(b.text() for b in page.findChildren(type(page.bouton_copier)))
        self.assertIn("Marie", textes)


if __name__ == "__main__":
    unittest.main()
