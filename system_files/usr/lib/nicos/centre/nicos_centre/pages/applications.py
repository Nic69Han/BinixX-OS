"""Installer des applications : on coche ce qu'on utilisait sous Windows, NicOS installe le tout d'un coup."""

import os

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from .. import applications, catalogue, launch

ORDER = 22
KEY = "applications"
TITLE = "Installer des applications"


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.cases = {}  # identifiant -> case à cocher
        self.etiquettes = {}  # identifiant -> étiquette d'état
        self.processus = None
        self.sortie = ""
        self.demandees = []
        self.erreur = ""
        try:
            entrees = catalogue.charger()
        except (OSError, ValueError) as erreur:
            entrees = []
            self.erreur = str(erreur)
        self.proposees = applications.proposees(entrees, catalogue.fournies())
        self.licences = applications.lire_licences()

        contenu = QWidget()
        page = QVBoxLayout(contenu)
        page.setContentsMargins(32, 28, 32, 24)
        page.setSpacing(10)
        titre = QLabel("Installer des applications")
        titre.setObjectName("pageTitle")
        intro = QLabel("Cochez les applications que vous utilisiez sous Windows, ou leur équivalent : NicOS les "
                       "installe d'un coup depuis <b>Flathub</b>. Elles tournent isolées du système et se mettent à "
                       "jour toutes seules. Le mot de passe d'un administrateur est demandé une fois. Les applications "
                       "<b>propriétaires</b> sont signalées : leur code est fermé et leurs conditions sont celles de "
                       "l'éditeur.")
        intro.setObjectName("pageLead")
        intro.setWordWrap(True)
        page.addWidget(titre)
        page.addWidget(intro)
        if self.erreur:
            page.addWidget(QLabel(f"Le catalogue n'a pas pu être lu : {self.erreur}"))

        installees = launch.installed_flatpaks()
        for categorie, groupe in applications.par_categorie(self.proposees):
            section = QLabel(categorie)
            section.setObjectName("sectionTitle")
            page.addSpacing(6)
            page.addWidget(section)
            for application in groupe:
                page.addWidget(self._ligne(application, installees))

        page.addSpacing(10)
        barre = QHBoxLayout()
        self.bouton = QPushButton("Installer la sélection")
        self.bouton.setObjectName("primary")
        self.bouton.setCursor(Qt.PointingHandCursor)
        self.bouton.clicked.connect(self.installer)
        self.annuler = QPushButton("Annuler")
        self.annuler.setVisible(False)
        self.annuler.clicked.connect(self.arreter)
        barre.addWidget(self.bouton)
        barre.addWidget(self.annuler)
        barre.addStretch(1)
        page.addLayout(barre)
        self.progression = QProgressBar()
        self.progression.setRange(0, 0)
        self.progression.setVisible(False)
        page.addWidget(self.progression)
        self.statut = QLabel()
        self.statut.setWordWrap(True)
        page.addWidget(self.statut)
        page.addStretch(1)
        self.mettre_a_jour_bouton()

        zone = QScrollArea()
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.NoFrame)
        zone.setWidget(contenu)
        racine = QVBoxLayout(self)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.addWidget(zone)

    # --- la liste ----------------------------------------------------------------------------------------------------

    def _ligne(self, application, installees):
        cadre = QFrame()
        cadre.setObjectName("card")
        ligne = QHBoxLayout(cadre)
        ligne.setContentsMargins(16, 8, 16, 8)
        case = QCheckBox(application.nom)
        case.setStyleSheet("font-weight: 600;")
        case.toggled.connect(self.mettre_a_jour_bouton)
        self.cases[application.identifiant] = case
        licence = self.licences.get(application.identifiant, "")
        morceaux = []
        remplace = applications.remplace_vraiment(application)
        if remplace:
            morceaux.append("Remplace : " + ", ".join(remplace))
        libelle = applications.libelle_licence(licence)
        if applications.est_proprietaire(licence):  # bien visible : code fermé, conditions de l'éditeur
            libelle = f"<span style='color:#b45309; font-weight:600;'>{libelle} (code fermé)</span>"
        morceaux.append(libelle)
        detail = QLabel("  ·  ".join(morceaux))
        detail.setStyleSheet("font-size: 9pt;")
        detail.setEnabled(False)
        detail.setWordWrap(True)
        colonne = QVBoxLayout()
        colonne.setSpacing(2)
        colonne.addWidget(case)
        colonne.addWidget(detail)
        if application.remarque:
            remarque = QLabel(application.remarque)
            remarque.setWordWrap(True)
            remarque.setStyleSheet("font-size: 9pt;")
            colonne.addWidget(remarque)
        ligne.addLayout(colonne, 1)
        etat = QLabel()
        self.etiquettes[application.identifiant] = etat
        ligne.addWidget(etat, 0, Qt.AlignVCenter)
        self._marquer(application.identifiant, application.identifiant in installees)
        return cadre

    def _marquer(self, identifiant, installee):
        case = self.cases[identifiant]
        if installee:
            case.setChecked(False)
        case.setEnabled(not installee)
        self.etiquettes[identifiant].setText("✓ Installée" if installee else "")

    def choisies(self):
        return [i for i, case in self.cases.items() if case.isChecked() and case.isEnabled()]

    def mettre_a_jour_bouton(self, _=None):
        nombre = len(self.choisies())
        self.bouton.setText("Installer la sélection" + (f" ({nombre})" if nombre else ""))
        self.bouton.setEnabled(nombre > 0 and not self.en_cours())

    def en_cours(self):
        return self.processus is not None and self.processus.state() != QProcess.NotRunning

    # --- l'installation ----------------------------------------------------------------------------------------------

    def installer(self):
        identifiants = self.choisies()
        try:
            argv = applications.commande(identifiants, os.environ.get("NICOS_FLATPAK", "flatpak"))
        except ValueError as erreur:
            self.statut.setText(str(erreur))
            return
        self.demandees = identifiants
        self.sortie = ""
        self.statut.setText("Installation en cours… (une fenêtre peut demander le mot de passe d'un administrateur)")
        self.progression.setVisible(True)
        self.annuler.setVisible(True)
        self.bouton.setEnabled(False)
        processus = QProcess(self)
        processus.setProcessChannelMode(QProcess.MergedChannels)
        processus.setProgram(argv[0])
        processus.setArguments(argv[1:])
        processus.readyRead.connect(lambda p=processus: self._lire(p))
        processus.finished.connect(lambda code, _s, p=processus: self._fini(p, code))
        processus.errorOccurred.connect(lambda _e, p=processus: self._introuvable(p))
        self.processus = processus
        processus.start()

    def arreter(self):
        if self.en_cours():
            self.processus.terminate()
            self.statut.setText("Annulation…")

    def _lire(self, processus):
        self.sortie += bytes(processus.readAll()).decode("utf-8", "replace")
        ligne = applications.derniere_ligne(self.sortie)
        if ligne:
            self.statut.setText(ligne)

    def _introuvable(self, processus):
        if processus.error() == QProcess.FailedToStart:
            self.progression.setVisible(False)
            self.annuler.setVisible(False)
            self.statut.setText("Flatpak n'a pas pu démarrer sur ce PC.")
            self.mettre_a_jour_bouton()

    def _fini(self, processus, code):
        self._lire(processus)
        self.progression.setVisible(False)
        self.annuler.setVisible(False)
        installees = launch.installed_flatpaks()
        for identifiant in self.cases:
            self._marquer(identifiant, identifiant in installees)
        reussies = [i for i in self.demandees if i in installees]
        if code == 0:
            self.statut.setText(f"Terminé : {len(reussies)} application(s) installée(s). Elles sont dans le menu.")
        else:
            cause = applications.explication_echec(self.sortie)
            detail = applications.derniere_ligne(self.sortie)
            debut = f"{len(reussies)} application(s) installée(s) sur {len(self.demandees)}. " if reussies else ""
            self.statut.setText(debut + "L'installation s'est arrêtée. " + (cause or detail or f"Code {code}."))
        self.mettre_a_jour_bouton()


def build(centre):
    return Page(centre)
