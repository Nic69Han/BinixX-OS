"""Récupérer mes fichiers Windows : documents, photos, favoris… depuis l'ancien disque, une clé USB ou un dossier."""

import json
import os

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from .. import launch, theme, widgets

ORDER = 15
KEY = "migration"
TITLE = "Récupérer mes fichiers"
ICONE = "folder"
ACCENT = theme.ACCENTS["vert"]

OUTIL = "/usr/libexec/nicos/nicos-migrer"


def taille(octets):
    """« 3,2 Go », « 12 Mo », « 850 Ko »."""
    for seuil, unite in ((2 ** 30, "Go"), (2 ** 20, "Mo"), (2 ** 10, "Ko")):
        if octets >= seuil:
            valeur = octets / seuil
            return (f"{valeur:.1f}".replace(".", ",") if valeur < 10 else f"{valeur:.0f}") + f" {unite}"
    return f"{octets} octets"


def fichiers(nombre):
    return f"{nombre} fichier" + ("s" if nombre > 1 else "")


def vider(disposition):
    """Retire et détruit les widgets d'une disposition (cachés tout de suite : deleteLater est différé)."""
    while disposition.count():
        element = disposition.takeAt(0).widget()
        if element is not None:
            element.hide()
            element.deleteLater()


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.analyse = None
        self.bilan = None
        self.source = None
        self.favoris = None
        self.cases = {}
        self.processus = None
        self.tampon = ""

        contenu, page = widgets.page_de_cartes()
        page.addWidget(widgets.entete(
            "Récupérer mes fichiers Windows",
            "Vos documents, vos photos, votre musique et vos favoris peuvent venir avec vous. NicOS <b>lit</b> "
            "l'ancien disque sans jamais y écrire, et <b>ne remplace aucun fichier</b> de ce PC : un fichier de même "
            "nom mais différent est gardé à côté, avec « (depuis Windows) » dans son nom.", ICONE, ACCENT))

        page.addWidget(widgets.section("1. D'où viennent vos fichiers ?", ACCENT))
        self.liste_sources = QVBoxLayout()
        self.liste_sources.setSpacing(10)
        page.addLayout(self.liste_sources)
        ligne = QHBoxLayout()
        actualiser = QPushButton("Actualiser")
        actualiser.clicked.connect(self.actualiser)
        disques = QPushButton("Ouvrir mes disques")
        disques.clicked.connect(launch.open_devices)
        dossier = QPushButton("Choisir un dossier…")
        dossier.clicked.connect(self.choisir_un_dossier)
        for bouton in (actualiser, disques, dossier):
            bouton.setObjectName("secondaire")
            bouton.setCursor(Qt.PointingHandCursor)
            ligne.addWidget(bouton)
        ligne.addStretch(1)
        page.addLayout(ligne)
        aide = QLabel("L'ancien disque apparaît dans « Ouvrir mes disques » : un clic le monte. Windows doit être "
                      "complètement arrêté (ni veille prolongée, ni démarrage rapide). Un disque protégé par "
                      "BitLocker se déverrouille avec son mot de passe ou la clé de récupération à 48 chiffres. Vous "
                      "pouvez aussi choisir le dossier d'une clé USB ou d'une sauvegarde.")
        aide.setObjectName("bandeau")
        aide.setWordWrap(True)
        page.addWidget(aide)

        self.section_choix = widgets.section("2. Que voulez-vous récupérer ?", ACCENT)
        page.addWidget(self.section_choix)
        self.etat_analyse = QLabel("Choisissez d'abord une source.")
        page.addWidget(self.etat_analyse)
        self.cadre_cases = QFrame()  # n'apparaît qu'une fois la source analysée
        self.cadre_cases.setObjectName("card")
        self.cadre_cases.setVisible(False)
        self.zone_cases = QVBoxLayout(self.cadre_cases)
        self.zone_cases.setContentsMargins(18, 14, 18, 14)
        self.zone_cases.setSpacing(8)
        page.addWidget(self.cadre_cases)
        self.notes = QLabel()
        self.notes.setObjectName("bandeau")
        self.notes.setWordWrap(True)
        self.notes.setVisible(False)
        page.addWidget(self.notes)

        self.bouton_copier = QPushButton("Copier mes fichiers")
        self.bouton_copier.setObjectName("primary")
        self.bouton_copier.setEnabled(False)
        self.bouton_copier.setCursor(Qt.PointingHandCursor)
        self.bouton_copier.clicked.connect(self.lancer_la_copie)
        page.addWidget(self.bouton_copier, 0, Qt.AlignLeft)
        self.progression = QProgressBar()
        self.progression.setMaximumHeight(8)
        self.progression.setTextVisible(False)
        self.progression.setVisible(False)
        page.addWidget(self.progression)
        self.resultat = QLabel()
        self.resultat.setWordWrap(True)
        self.resultat.setOpenExternalLinks(False)
        page.addWidget(self.resultat)
        self.bouton_ouvrir = QPushButton("Ouvrir mes Documents")
        self.bouton_ouvrir.setObjectName("secondaire")
        self.bouton_ouvrir.setCursor(Qt.PointingHandCursor)
        self.bouton_ouvrir.setVisible(False)
        self.bouton_ouvrir.clicked.connect(lambda: launch.open_folder(os.path.join(os.path.expanduser("~"), "Documents")))
        page.addWidget(self.bouton_ouvrir, 0, Qt.AlignLeft)
        page.addStretch(1)

        widgets.remplir(self, contenu)
        self.actualiser()

    # --- 1. les sources ---------------------------------------------------------------------------------------------

    def sources(self):
        """Profils Windows trouvés sur les disques montés (liste de dictionnaires)."""
        code, sortie = launch.run([OUTIL, "sources"], timeout=60)
        try:
            return json.loads(sortie) if code == 0 else []
        except ValueError:
            return []

    def actualiser(self):
        vider(self.liste_sources)
        trouvees = self.sources()
        if not trouvees:
            self.liste_sources.addWidget(QLabel("Aucun ancien disque Windows trouvé pour l'instant."))
        for source in trouvees:
            carte = widgets.carte(f"Profil « {source['nom']} »", f"Disque {source['disque']} · {source['chemin']}",
                                  f"Récupérer les fichiers de {source['nom']}",
                                  lambda _=False, c=source["chemin"]: self.choisir_source(c),
                                  icone="hard-drive", couleurs=ACCENT)
            self.liste_sources.addWidget(carte)

    def choisir_un_dossier(self):
        dossier = QFileDialog.getExistingDirectory(self, "Choisir le dossier à récupérer", "/run/media")
        if dossier:
            self.choisir_source(dossier)

    # --- 2. l'analyse -----------------------------------------------------------------------------------------------

    def choisir_source(self, chemin):
        self.source = chemin
        self.analyse = None
        self.bilan = None
        self.resultat.setText("")
        self.bouton_ouvrir.setVisible(False)
        self.progression.setVisible(False)
        self._vider_cases()
        self.etat_analyse.setText(f"Analyse de {chemin}… (patientez : un gros disque peut prendre une minute)")
        self.bouton_copier.setEnabled(False)
        processus = QProcess(self)
        processus.setProgram(OUTIL)
        processus.setArguments(["analyser", chemin])
        processus.finished.connect(lambda code, _s, p=processus: self._analyse_terminee(p, code))
        self.processus = processus
        processus.start()

    def _vider_cases(self):
        self.cases = {}
        vider(self.zone_cases)
        self.cadre_cases.setVisible(False)
        self.notes.setVisible(False)

    def _analyse_terminee(self, processus, code):
        sortie = bytes(processus.readAllStandardOutput()).decode("utf-8", "replace")
        try:
            analyse = json.loads(sortie) if code == 0 else None
        except ValueError:
            analyse = None
        if analyse is None:
            self.etat_analyse.setText("Ce dossier n'a pas pu être lu. Vérifiez que le disque est bien monté.")
            return
        self.etat_analyse.setText("Cochez ce que vous voulez récupérer :" if analyse["profil_windows"] else
                                  "Ce dossier ne ressemble pas à un profil Windows : il sera copié en entier dans "
                                  "vos Documents.")
        for categorie in analyse["categories"]:
            case = QCheckBox(f"{categorie['titre']} ({fichiers(categorie['fichiers'])}, {taille(categorie['octets'])})")
            case.setChecked(categorie["fichiers"] > 0)
            case.setEnabled(categorie["fichiers"] > 0)
            case.toggled.connect(self.mettre_a_jour_bouton)
            self.cases[categorie["cle"]] = case
            self.zone_cases.addWidget(case)
        if analyse["navigateurs"]:
            favoris = QCheckBox("Favoris du navigateur (" + ", ".join(analyse["navigateurs"]) + ")")
            favoris.setChecked(True)
            favoris.toggled.connect(self.mettre_a_jour_bouton)
            self.cases["favoris"] = favoris
            self.zone_cases.addWidget(favoris)
        self.cadre_cases.setVisible(bool(self.cases))
        notes = []
        if analyse["onedrive"]:
            notes.append("OneDrive : vos fichiers sont déjà dans le nuage ; reconnectez-le avec « OneDrive » du menu "
                         "plutôt que de les copier.")
        if analyse["pst"]:
            notes.append("Courrier Outlook (.pst) trouvé : il est copié avec les Documents, mais pour le lire il faut "
                         "l'importer dans Thunderbird (voir le guide de migration).")
        if analyse["navigateurs"]:
            notes.append("Les mots de passe du navigateur ne sont pas copiés (Windows les chiffre pour son compte) : "
                         "exportez-les depuis Edge ou Chrome, ou activez la synchronisation Firefox.")
        self.notes.setText("<br>".join(notes))
        self.notes.setVisible(bool(notes))
        self.analyse = analyse
        self.mettre_a_jour_bouton()

    def mettre_a_jour_bouton(self, _=None):
        self.bouton_copier.setEnabled(self.analyse is not None and self.processus_libre()
                                      and any(case.isChecked() and case.isEnabled() for case in self.cases.values()))

    def processus_libre(self):
        return self.processus is None or self.processus.state() == QProcess.NotRunning

    # --- 3. la copie ------------------------------------------------------------------------------------------------

    def lancer_la_copie(self):
        dossiers = [cle for cle, case in self.cases.items() if cle != "favoris" and case.isChecked()]
        self.bilan = None
        self.favoris = None
        self.bouton_copier.setEnabled(False)
        self.resultat.setText("")
        if "favoris" in self.cases and self.cases["favoris"].isChecked():
            code, sortie = launch.run([OUTIL, "favoris", self.source], timeout=120)
            try:
                self.favoris = json.loads(sortie) if code == 0 else None
            except ValueError:
                self.favoris = None
        if not dossiers:
            self._terminer({"copies": 0, "deja_la": 0, "renommes": 0, "erreurs": 0, "octets": 0, "rapport": ""})
            return
        self.progression.setVisible(True)
        self.progression.setRange(0, 0)  # indéterminée jusqu'au premier message
        self.tampon = ""
        processus = QProcess(self)
        processus.setProgram(OUTIL)
        processus.setArguments(["copier", self.source, "--dossiers", ",".join(dossiers), "--json"])
        processus.readyReadStandardOutput.connect(lambda p=processus: self._lire(p))
        processus.finished.connect(lambda code, _s, p=processus: self._copie_terminee(p, code))
        self.processus = processus
        processus.start()

    def _lire(self, processus):
        self.tampon += bytes(processus.readAllStandardOutput()).decode("utf-8", "replace")
        while "\n" in self.tampon:
            ligne, self.tampon = self.tampon.split("\n", 1)
            try:
                evenement = json.loads(ligne)
            except ValueError:
                continue
            if evenement.get("etat") == "avance":
                self.progression.setRange(0, evenement["total"])
                self.progression.setValue(evenement["fait"])
            elif evenement.get("etat") == "debut":
                self.progression.setRange(0, max(evenement["total"], 1))
            elif evenement.get("etat") == "fin":
                self.bilan = evenement

    def _copie_terminee(self, processus, code):
        self._lire(processus)
        if self.bilan is None:  # l'outil s'est arrêté avant la fin : on explique pourquoi
            erreur = bytes(processus.readAllStandardError()).decode("utf-8", "replace").strip()
            self.progression.setVisible(False)
            self.resultat.setText("La copie n'a pas pu se faire : " + (erreur or f"code {code}") + ". Rien n'a été "
                                  "supprimé ni modifié sur l'ancien disque.")
            self.mettre_a_jour_bouton()
            return
        self._terminer(self.bilan)

    def _terminer(self, bilan):
        self.bilan = bilan
        self.progression.setRange(0, 1)
        self.progression.setValue(1)
        lignes = [f"<b>Terminé.</b> {bilan['copies']} fichier(s) copié(s) ({taille(bilan['octets'])})."]
        if bilan["deja_la"]:
            lignes.append(f"{bilan['deja_la']} déjà présent(s) et identique(s) : non recopiés.")
        if bilan["renommes"]:
            lignes.append(f"{bilan['renommes']} gardé(s) à côté d'un fichier de même nom (« (depuis Windows) »).")
        if bilan["erreurs"]:
            lignes.append(f"<b>{bilan['erreurs']} fichier(s) illisible(s)</b> : liste dans le rapport.")
        if bilan["rapport"]:
            lignes.append(f"Rapport : {bilan['rapport']}")
        if self.favoris and self.favoris.get("fichier"):
            lignes.append(f"{self.favoris['liens']} favoris exportés dans {self.favoris['fichier']} : dans Firefox, "
                          "Ctrl+Maj+O → « Importer et sauvegarde » → « Importer les favoris depuis un fichier HTML ».")
        self.resultat.setText("<br>".join(lignes))
        self.bouton_ouvrir.setVisible(True)
        self.mettre_a_jour_bouton()


def build(centre):
    return Page(centre)
