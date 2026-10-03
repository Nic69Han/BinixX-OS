"""Tests de la page « Mises à jour » : lecture de rpm-ostree, comparaison avec le registre, ligne de commande, page.

python3 -m unittest discover -s tests/image/centre -p 'test_misesajour.py'   (la partie Qt est ignorée sans PySide6)
"""

import json
import os
import sys
import time
import unittest

ICI = os.path.dirname(__file__)
RACINE = os.environ.get("BINIXX_CENTRE", os.path.join(ICI, "../../../system_files/usr/lib/binixx/centre"))
CAPTURES = os.environ.get("BINIXX_CAPTURES")
sys.path.insert(0, RACINE)

from binixx_centre import misesajour as M  # noqa: E402

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    AVEC_QT = True
except ImportError:
    AVEC_QT = False

OCTOBRE_3 = 1791028800   # 3 octobre 2026, midi UTC
OCTOBRE_1 = 1790856000   # 1er octobre 2026, midi UTC
EMPREINTE_A = "sha256:" + "a" * 64
EMPREINTE_B = "sha256:" + "b" * 64
EMPREINTE_C = "sha256:" + "c" * 64
IMAGE = "ostree-image-signed:docker://ghcr.io/nic69han/binixx:stable"


def deploiement(version="44.20261003.0", horodatage=OCTOBRE_3, booted=False, staged=False, image=IMAGE,
                empreinte=EMPREINTE_A, **autres):
    donnees = {"id": f"default-{version}.0", "version": version, "timestamp": horodatage, "booted": booted,
               "staged": staged, "container-image-reference": image,
               "container-image-reference-digest": empreinte, "osname": "default", "pinned": False}
    donnees.update(autres)
    return donnees


def statut(*deploiements):
    return json.dumps({"deployments": list(deploiements), "transaction": None})


class Faux:
    """Un `launch.run` qui répond selon la commande et se souvient de ce qu'on lui a demandé."""

    def __init__(self, status=None, publiees=None, code_status=0):
        self.status = status
        self.publiees = publiees or {}       # {adresse : réponse de skopeo inspect (dictionnaire) ou None}
        self.code_status = code_status
        self.appels = []

    def __call__(self, argv, timeout=120):
        self.appels.append((list(argv), timeout))
        if argv[0] == "rpm-ostree":
            return self.code_status, self.status or ""
        if argv[0] == "skopeo":
            reponse = self.publiees.get(argv[-1])
            return (0, json.dumps(reponse)) if reponse is not None else (1, "")
        if argv[0] in ("bootc",):
            return 0, "fait\n"
        raise AssertionError(argv)


def image_publiee(empreinte, *couches):
    return {"Digest": empreinte, "LayersData": [{"Digest": d, "Size": t} for d, t in couches]}


class Presentation(unittest.TestCase):
    def test_date_en_francais(self):
        self.assertRegex(M.date_en_francais(OCTOBRE_3), r"^[23] octobre 2026$")
        self.assertRegex(M.date_en_francais(OCTOBRE_1), r"^(30 septembre|1er octobre) 2026$")
        self.assertEqual(M.date_en_francais(None), "")
        self.assertEqual(M.date_en_francais("bientôt"), "")

    def test_premier_du_mois(self):
        self.assertTrue(M.date_en_francais(int(time.mktime((2026, 11, 1, 12, 0, 0, 0, 0, -1)))).startswith("1er novembre"))

    def test_taille_lisible(self):
        self.assertEqual(M.taille_lisible(None), "")
        self.assertEqual(M.taille_lisible(0), "0 octets")
        self.assertEqual(M.taille_lisible(512), "512 octets")
        self.assertEqual(M.taille_lisible(1500), "2 Ko")
        self.assertEqual(M.taille_lisible(480_000_000), "480 Mo")
        self.assertEqual(M.taille_lisible(1_200_000_000), "1,2 Go")
        self.assertEqual(M.taille_lisible(12_300_000), "12,3 Mo")
        self.assertEqual(M.taille_lisible(250_000_000_000), "250 Go")


class Adresses(unittest.TestCase):
    def test_references_d_un_deploiement(self):
        for reference in (IMAGE, "ostree-unverified-registry:ghcr.io/nic69han/binixx:stable",
                          "ostree-remote-registry:binixx:ghcr.io/nic69han/binixx:stable",
                          "ostree-unverified-image:docker://ghcr.io/nic69han/binixx:stable",
                          "docker://ghcr.io/nic69han/binixx:stable", "ghcr.io/nic69han/binixx:stable"):
            self.assertEqual(M.adresse_docker(reference), "docker://ghcr.io/nic69han/binixx:stable", reference)

    def test_ce_qui_n_est_pas_un_registre(self):
        for reference in (None, "", 42, "ostree-unverified-image:oci:/var/tmp/image", "containers-storage:localhost/x:y",
                          "localhost/binixx:testing", "ostree-unverified-registry:localhost/binixx:testing",
                          "docker://ghcr.io/Majuscule/Interdit:stable", "ghcr.io/espace dans/le:nom"):
            self.assertIsNone(M.adresse_docker(reference), reference)

    def test_registre_local_avec_port(self):
        self.assertEqual(M.adresse_docker("ostree-unverified-registry:10.0.2.2:5000/binixx:update"),
                         "docker://10.0.2.2:5000/binixx:update")

    def test_depot_et_etiquette(self):
        self.assertEqual(M.depot_de("docker://ghcr.io/nic69han/binixx:stable"), "ghcr.io/nic69han/binixx")
        self.assertEqual(M.depot_de("docker://10.0.2.2:5000/binixx:update"), "10.0.2.2:5000/binixx")
        self.assertEqual(M.depot_de("docker://ghcr.io/nic69han/binixx@" + EMPREINTE_A), "ghcr.io/nic69han/binixx")
        self.assertEqual(M.etiquette(IMAGE), "stable")
        self.assertEqual(M.etiquette("ghcr.io/nic69han/binixx"), "latest")
        self.assertIsNone(M.etiquette("ghcr.io/nic69han/binixx@" + EMPREINTE_A))
        self.assertIsNone(M.etiquette("localhost/x:y"))

    def test_description_du_canal(self):
        self.assertIn("Stable", M.description_du_canal(IMAGE))
        self.assertIn("Stable", M.description_du_canal("ghcr.io/nic69han/binixx:latest"))
        self.assertIn("Test", M.description_du_canal("ghcr.io/nic69han/binixx:testing"))
        self.assertIn("figée", M.description_du_canal("ghcr.io/nic69han/binixx@" + EMPREINTE_A))
        self.assertIn("« mon-essai »", M.description_du_canal("ghcr.io/nic69han/binixx:mon-essai"))


class LectureDeLEtat(unittest.TestCase):
    def test_un_seul_deploiement(self):
        etat = M.lire_etat(statut(deploiement(booted=True)))
        self.assertEqual(etat["installee"]["version"], "44.20261003.0")
        self.assertEqual(etat["installee"]["empreinte"], EMPREINTE_A)
        self.assertEqual(etat["installee"]["image"], IMAGE)
        self.assertRegex(etat["installee"]["date"], r"octobre 2026")
        self.assertIsNone(etat["prete"])
        self.assertIsNone(etat["precedente"])

    def test_version_preparee_puis_installee_puis_precedente(self):
        etat = M.lire_etat(statut(
            deploiement("44.20261004.0", staged=True, empreinte=EMPREINTE_C),
            deploiement("44.20261003.0", booted=True),
            deploiement("44.20261001.0", OCTOBRE_1, empreinte=EMPREINTE_B)))
        self.assertEqual(etat["installee"]["version"], "44.20261003.0")
        self.assertEqual(etat["prete"]["version"], "44.20261004.0")
        self.assertEqual(etat["prete"]["empreinte"], EMPREINTE_C)
        self.assertEqual(etat["precedente"]["version"], "44.20261001.0")

    def test_apres_un_retour_arriere_la_version_precedente_est_celle_qu_on_a_quittee(self):
        # rpm-ostree range d'abord la version qui démarrera ; celle qui tourne est « installée »
        etat = M.lire_etat(statut(deploiement("44.20261001.0", OCTOBRE_1), deploiement("44.20261003.0", booted=True)))
        self.assertEqual(etat["installee"]["version"], "44.20261003.0")
        self.assertIsNone(etat["precedente"])   # aucune version plus ancienne qu'elle dans la liste

    def test_reponses_incomprises(self):
        for sortie in ("", "pas du json", "[]", "{}", json.dumps({"deployments": []}),
                       json.dumps({"deployments": "non"}), json.dumps({"deployments": [deploiement()]}),   # rien ne tourne
                       json.dumps({"deployments": ["x", 3]})):
            self.assertIsNone(M.lire_etat(sortie), sortie)

    def test_champs_manquants(self):
        etat = M.lire_etat(json.dumps({"deployments": [{"booted": True}]}))
        self.assertEqual(etat["installee"]["version"], "")
        self.assertEqual(etat["installee"]["date"], "")
        self.assertIsNone(etat["installee"]["empreinte"])
        self.assertEqual(etat["installee"]["image"], "")

    def test_etat_sans_rpm_ostree(self):
        self.assertIsNone(M.etat(Faux(code_status=1)))
        faux = Faux(statut(deploiement(booted=True)))
        self.assertIsNotNone(M.etat(faux))
        self.assertEqual(faux.appels[0][0], ["rpm-ostree", "status", "--json"])


class RechercheDeNouveaute(unittest.TestCase):
    ADRESSE = "docker://ghcr.io/nic69han/binixx:stable"
    ANCIENNE = f"docker://ghcr.io/nic69han/binixx@{EMPREINTE_A}"

    def installee(self, **autres):
        donnees = M.lire_etat(statut(deploiement(booted=True, **autres)))["installee"]
        return donnees

    def test_a_jour(self):
        faux = Faux(publiees={self.ADRESSE: image_publiee(EMPREINTE_A, ("sha256:1", 100))})
        self.assertEqual(M.verifier(self.installee(), faux), {"disponible": False, "taille": 0, "raison": ""})

    def test_nouvelle_version_avec_la_taille_des_couches_nouvelles(self):
        faux = Faux(publiees={
            self.ADRESSE: image_publiee(EMPREINTE_B, ("sha256:1", 700), ("sha256:2", 300), ("sha256:3", 50)),
            self.ANCIENNE: image_publiee(EMPREINTE_A, ("sha256:1", 700), ("sha256:9", 5000)),
        })
        resultat = M.verifier(self.installee(), faux)
        self.assertTrue(resultat["disponible"])
        self.assertEqual(resultat["taille"], 350)      # les couches 2 et 3 seulement
        # commandes : sans shell, sans mot de passe
        self.assertEqual(faux.appels[0][0], ["skopeo", "inspect", "--no-tags", "--retry-times", "1", self.ADRESSE])
        self.assertEqual(faux.appels[1][0][-1], self.ANCIENNE)

    def test_taille_inconnue_si_l_ancienne_image_n_est_plus_publiee(self):
        faux = Faux(publiees={self.ADRESSE: image_publiee(EMPREINTE_B, ("sha256:2", 300))})
        resultat = M.verifier(self.installee(), faux)
        self.assertTrue(resultat["disponible"])
        self.assertIsNone(resultat["taille"])

    def test_pas_de_reseau(self):
        resultat = M.verifier(self.installee(), Faux())
        self.assertIsNone(resultat["disponible"])
        self.assertIn("Internet", resultat["raison"])

    def test_reponse_du_registre_sans_empreinte(self):
        resultat = M.verifier(self.installee(), Faux(publiees={self.ADRESSE: {"Digest": "n'importe quoi"}}))
        self.assertIsNone(resultat["disponible"])

    def test_image_qui_ne_vient_pas_d_un_registre(self):
        resultat = M.verifier(self.installee(image="ostree-unverified-image:oci:/var/tmp/x"), Faux())
        self.assertIsNone(resultat["disponible"])
        self.assertIn("registre", resultat["raison"])

    def test_version_figee_et_empreinte_inconnue(self):
        figee = self.installee(image="ostree-unverified-registry:ghcr.io/nic69han/binixx@" + EMPREINTE_A)
        self.assertIn("figée", M.verifier(figee, Faux())["raison"])
        sans = M.lire_etat(json.dumps({"deployments": [{"booted": True, "container-image-reference": IMAGE}]}))["installee"]
        self.assertIn("empreinte", M.verifier(sans, Faux())["raison"])


class LigneDeCommande(unittest.TestCase):
    STATUT = statut(deploiement("44.20261003.0", booted=True), deploiement("44.20261001.0", OCTOBRE_1))

    def lancer(self, *argv, run=None):
        sortie = []
        code = M.main(list(argv), run=run or Faux(self.STATUT), sortie=sortie.append)
        return code, "\n".join(sortie)

    def test_etat_en_texte(self):
        code, texte = self.lancer("etat")
        self.assertEqual(code, 0)
        self.assertIn("Version installée : 44.20261003.0", texte)
        self.assertIn("Image : ostree-image-signed:docker://ghcr.io/nic69han/binixx:stable", texte)
        self.assertIn("Canal : Stable", texte)
        self.assertIn("Mise à jour prête : non", texte)
        self.assertIn("Version précédente : 44.20261001.0", texte)
        self.assertNotIn("Nouvelle version", texte)     # « etat » ne touche pas au réseau

    def test_etat_en_json(self):
        faux = Faux(self.STATUT)
        code, texte = self.lancer("etat", "--json", run=faux)
        donnees = json.loads(texte)
        self.assertEqual(donnees["installee"]["version"], "44.20261003.0")
        self.assertEqual(donnees["etiquette"], "stable")
        self.assertIn("Stable", donnees["canal"])
        self.assertNotIn("verification", donnees)
        self.assertEqual([a[0][0] for a in faux.appels], ["rpm-ostree"])

    def test_verifier_ajoute_la_recherche(self):
        faux = Faux(self.STATUT, publiees={"docker://ghcr.io/nic69han/binixx:stable":
                                           image_publiee(EMPREINTE_B, ("sha256:2", 480_000_000))})
        code, texte = self.lancer("verifier", "--json", run=faux)
        donnees = json.loads(texte)
        self.assertTrue(donnees["verification"]["disponible"])
        code, texte = self.lancer("verifier", run=faux)
        self.assertIn("Nouvelle version : disponible", texte)

    def test_verifier_a_jour_et_sans_reseau(self):
        faux = Faux(self.STATUT, publiees={"docker://ghcr.io/nic69han/binixx:stable": image_publiee(EMPREINTE_A)})
        self.assertIn("le PC est à jour", self.lancer("verifier", run=faux)[1])
        self.assertIn("Nouvelle version : inconnue", self.lancer("verifier", run=Faux(self.STATUT))[1])

    def test_une_mise_a_jour_prete_est_dite(self):
        faux = Faux(statut(deploiement("44.20261004.0", staged=True), deploiement(booted=True)))
        code, texte = self.lancer("etat", run=faux)
        self.assertIn("Mise à jour prête : oui, version 44.20261004.0", texte)
        self.assertIn("Version précédente : aucune", texte)

    def test_sans_rpm_ostree_message_clair(self):
        code, texte = self.lancer("etat", run=Faux(code_status=1))
        self.assertEqual(code, 1)
        self.assertIn("Impossible de lire l'état du système", texte)
        self.assertNotIn("Traceback", texte)

    def test_installer_et_retour_sont_reserves_a_l_administrateur(self):
        if os.geteuid() == 0:
            self.skipTest("lancé en administrateur")
        faux = Faux(self.STATUT)
        for action in ("installer", "retour"):
            code, texte = self.lancer(action, run=faux)
            self.assertEqual(code, 3)
            self.assertIn("administrateur", texte)
        self.assertEqual(faux.appels, [])      # rien n'a été lancé

    def test_installer_et_retour_lancent_bootc(self):
        faux = Faux(self.STATUT)
        ancien = os.geteuid
        os.geteuid = lambda: 0
        self.addCleanup(setattr, os, "geteuid", ancien)
        self.assertEqual(self.lancer("installer", run=faux)[0], 0)
        self.assertEqual(self.lancer("retour", run=faux)[0], 0)
        self.assertEqual([a[0] for a in faux.appels], [["bootc", "upgrade"], ["bootc", "rollback"]])

    def test_action_inconnue(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            M.main(["bidule"])


@unittest.skipUnless(AVEC_QT, "PySide6 absent")
class PageDuCentre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from binixx_centre import theme
        from binixx_centre.pages import mises_a_jour as page
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(theme.STYLE)
        cls.module = page

    def setUp(self):
        from binixx_centre import launch
        self.commandes = []        # ce que la page a lancé
        self.reponses = []         # (code, sortie) à rendre, dans l'ordre
        self.demarrages = []
        self.pages = []
        self.centre = type("Centre", (), {"show_page": lambda s, cle: self.pages.append(cle)})()
        for nom, effet in (("reboot_prompt", lambda: self.demarrages.append("redémarrage") or True),
                           ("open_discover_mode", lambda mode: self.demarrages.append(("discover", mode)) or True)):
            ancien = getattr(launch, nom)
            setattr(launch, nom, effet)
            self.addCleanup(setattr, launch, nom, ancien)
        self.questions = []
        from PySide6.QtWidgets import QMessageBox
        ancien = QMessageBox.question
        QMessageBox.question = lambda *a, **k: self.questions.append(a[1]) or self.rep_question
        self.rep_question = QMessageBox.Yes
        self.addCleanup(setattr, QMessageBox, "question", ancien)

    def ouvrir(self, etat=None, code=0):
        page = self.module.build(self.centre)

        def lancer(argv, rappel):
            self.commandes.append(argv)
            code_rendu, sortie = self.reponses.pop(0) if self.reponses else (1, "")
            page.processus = None
            rappel(code_rendu, sortie)

        page._lancer = lancer
        self.reponses.insert(0, (code, json.dumps(etat) if etat is not None else ""))
        page.show()
        self.app.processEvents()
        return page

    def etat(self, prete=False, precedente=True):
        courant = M.lire_etat(statut(
            *([deploiement("44.20261004.0", staged=True, empreinte=EMPREINTE_C)] if prete else []),
            deploiement(booted=True),
            *([deploiement("44.20261001.0", OCTOBRE_1, empreinte=EMPREINTE_B)] if precedente else [])))
        courant["canal"] = M.description_du_canal(IMAGE)
        courant["etiquette"] = "stable"
        return courant

    def test_la_page_depend_de_parametres_et_a_sa_couleur(self):
        self.assertFalse(self.module.MENU)
        self.assertEqual(self.module.PARENT, "parametres")
        self.assertEqual(self.module.KEY, "mises_a_jour")

    def test_au_depart_on_lit_l_etat_sans_mot_de_passe(self):
        page = self.ouvrir(self.etat())
        self.assertEqual(self.commandes[0], ["/usr/libexec/binixx/binixx-mises-a-jour", "etat", "--json"])
        self.assertIn("44.20261003.0", page.version.text())
        self.assertIn("Stable", page.version.text())
        self.assertEqual(page.mode, "repos")
        self.assertEqual(page.bouton.text(), "Rechercher des mises à jour")
        self.assertTrue(page.carte_precedente.isVisible())
        self.assertIn("44.20261001.0", page.precedente.text())
        page.close()

    def test_etat_illisible(self):
        page = self.ouvrir(None, code=1)
        self.assertEqual(page.mode, "inconnu")
        self.assertFalse(page.bouton.isVisible())
        self.assertIn("n'a pas pu être lu", page.message.text())
        self.assertFalse(page.carte_precedente.isVisible())
        page.close()

    def test_sans_version_precedente_pas_de_carte_de_retour(self):
        page = self.ouvrir(self.etat(precedente=False))
        self.assertFalse(page.carte_precedente.isVisible())
        page.close()

    def test_une_mise_a_jour_prete_propose_de_redemarrer(self):
        page = self.ouvrir(self.etat(prete=True))
        self.assertEqual(page.mode, "prete")
        self.assertIn("44.20261004.0", page.message.text())
        self.assertEqual(page.bouton.text(), "Redémarrer maintenant")
        page.bouton.click()
        self.assertEqual(self.demarrages, ["redémarrage"])
        page.close()

    def test_rechercher_puis_installer(self):
        page = self.ouvrir(self.etat())
        verification = self.etat()
        verification["verification"] = {"disponible": True, "taille": 480_000_000, "raison": ""}
        self.reponses.append((0, json.dumps(verification)))
        page.bouton.click()
        self.assertEqual(self.commandes[-1], ["/usr/libexec/binixx/binixx-mises-a-jour", "verifier", "--json"])
        self.assertEqual(page.mode, "disponible")
        self.assertIn("480 Mo", page.message.text())
        self.assertEqual(page.bouton.text(), "Installer maintenant")
        # installer : pkexec, puis l'état est relu et la page propose de redémarrer
        pret = self.etat(prete=True)
        self.reponses.extend([(0, "fait"), (0, json.dumps(pret))])
        page.bouton.click()
        self.assertEqual(self.commandes[-2], ["pkexec", "/usr/libexec/binixx/binixx-mises-a-jour", "installer"])
        self.assertEqual(self.commandes[-1], ["/usr/libexec/binixx/binixx-mises-a-jour", "etat", "--json"])
        self.assertEqual(page.mode, "prete")
        self.assertEqual(page.bouton.text(), "Redémarrer maintenant")
        page.close()

    def test_a_jour(self):
        page = self.ouvrir(self.etat())
        reponse = self.etat()
        reponse["verification"] = {"disponible": False, "taille": 0, "raison": ""}
        self.reponses.append((0, json.dumps(reponse)))
        page.bouton.click()
        self.assertEqual(page.mode, "a_jour")
        self.assertEqual(page.message.text(), "Votre PC est à jour.")
        self.assertEqual(page.bouton.text(), "Rechercher à nouveau")
        page.close()

    def test_recherche_sans_reseau_dit_pourquoi(self):
        page = self.ouvrir(self.etat())
        reponse = self.etat()
        reponse["verification"] = {"disponible": None, "taille": None, "raison": "Le serveur ne répond pas : Internet ?"}
        self.reponses.append((0, json.dumps(reponse)))
        page.bouton.click()
        self.assertEqual(page.mode, "inconnue")
        self.assertIn("Internet", page.message.text())
        self.assertEqual(page.bouton.text(), "Rechercher à nouveau")
        page.close()

    def test_recherche_en_echec(self):
        page = self.ouvrir(self.etat())
        self.reponses.append((1, ""))
        page.bouton.click()
        self.assertEqual(page.mode, "echec")
        self.assertIn("n'a pas pu être faite", page.message.text())
        page.close()

    def test_mot_de_passe_refuse_rien_ne_change(self):
        page = self.ouvrir(self.etat())
        page.mode = "disponible"
        self.reponses.append((126, ""))
        page.installer()
        self.assertEqual(page.mode, "disponible")
        page.close()

    def test_installation_en_echec(self):
        page = self.ouvrir(self.etat())
        page.mode = "disponible"
        self.reponses.append((5, "erreur"))
        page.installer()
        self.assertEqual(page.mode, "echec")
        self.assertIn("code 5", page.message.text())
        self.assertIn("Rien n'a changé", page.message.text())
        page.close()

    def test_revenir_en_arriere_demande_confirmation(self):
        page = self.ouvrir(self.etat())
        self.rep_question = __import__("PySide6.QtWidgets", fromlist=["QMessageBox"]).QMessageBox.No
        page.bouton_retour.click()
        self.assertEqual(self.questions, ["Revenir à la version précédente"])
        self.assertEqual(len(self.commandes), 1)      # seule la lecture de l'état : rien n'a été lancé avec pkexec
        page.close()

    def test_revenir_en_arriere(self):
        page = self.ouvrir(self.etat())
        self.reponses.extend([(0, "fait"), (0, json.dumps(self.etat()))])
        page.bouton_retour.click()
        self.assertEqual(self.commandes[-2], ["pkexec", "/usr/libexec/binixx/binixx-mises-a-jour", "retour"])
        self.assertEqual(page.mode, "retour")
        self.assertIn("version précédente reviendra", page.message.text())
        self.assertEqual(page.bouton.text(), "Redémarrer maintenant")
        self.assertFalse(page.bouton_retour.isEnabled())
        page.bouton.click()
        self.assertEqual(self.demarrages, ["redémarrage"])
        page.close()

    def test_retour_refuse_ou_en_echec(self):
        page = self.ouvrir(self.etat())
        self.reponses.append((126, ""))
        page.revenir()
        self.assertEqual(page.mode, "repos")
        self.reponses.append((4, ""))
        page.revenir()
        self.assertEqual(page.mode, "echec")
        self.assertIn("code 4", page.message.text())
        page.close()

    def test_discover_pour_les_applications(self):
        page = self.ouvrir(self.etat())
        from PySide6.QtWidgets import QPushButton
        bouton = next(b for b in page.findChildren(QPushButton) if b.text() == "Ouvrir Discover")
        bouton.click()
        self.assertEqual(self.demarrages, [("discover", "update")])
        page.close()

    def test_retour_aux_parametres(self):
        page = self.ouvrir(self.etat())
        from PySide6.QtWidgets import QPushButton
        next(b for b in page.findChildren(QPushButton) if b.text().startswith("←")).click()
        self.assertEqual(self.pages, ["parametres"])
        page.close()

    def test_capture(self):
        if not CAPTURES:
            self.skipTest("BINIXX_CAPTURES non défini")
        os.makedirs(CAPTURES, exist_ok=True)
        page = self.ouvrir(self.etat())
        page.resize(980, 700)
        self.app.processEvents()
        page.grab().save(os.path.join(CAPTURES, "mises_a_jour.png"))
        page.close()


if __name__ == "__main__":
    unittest.main()
