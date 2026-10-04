"""Fenêtre « Installer une application » : installe une application Flatpak depuis Flathub, sans passer par Discover.

Les boutons « Installer » des pages Jeux, Catalogue et Paramètres ouvraient Discover sur la fiche de l'application. Si Discover n'a pas
(encore) la liste de Flathub, il répond « Aucune entrée pour net.lutris.Lutris » et on ne sait pas pourquoi. Ici on installe directement
(la commande de la page « Installer des applications », testée sur machine virtuelle), avec la progression, et si cela échoue une phrase
simple dit pourquoi (pas de réseau, pas de droits d'administrateur…). Discover reste proposé en dernier recours.

    binixx-installer-application IDENTIFIANT_FLATPAK
"""

import os
import sys

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from . import applications, catalogue, launch, theme

DEPOT = "https://dl.flathub.org/repo/flathub.flatpakrepo"


def nom_de(identifiant, entrees):
    """Le nom que l'utilisateur connaît (« Lutris »), d'après le catalogue ; à défaut l'identifiant."""
    for entree in entrees:
        if entree.type == "flatpak" and entree.cible == identifiant:
            return entree.remplacant
    return identifiant


class Fenetre(QWidget):
    def __init__(self, identifiant, nom=None):
        super().__init__()
        self.identifiant = applications.valider(identifiant)
        if nom is None:
            try:
                nom = nom_de(self.identifiant, catalogue.charger())
            except (OSError, ValueError):
                nom = self.identifiant
        self.nom = nom
        self.flatpak = os.environ.get("BINIXX_FLATPAK", "flatpak")
        self.processus = None
        self.etape = ""
        self.sortie = ""
        self.reussi = False
        self.setWindowTitle(f"Installer {self.nom}")
        self.setWindowIcon(QIcon.fromTheme("binixx"))
        self.setMinimumWidth(480)

        racine = QVBoxLayout(self)
        racine.setContentsMargins(24, 22, 24, 18)
        racine.setSpacing(12)
        self.titre = QLabel(f"Installation de {self.nom}")
        self.titre.setObjectName("pageTitle")
        self.titre.setStyleSheet("font-size: 15pt; font-weight: 600;")
        self.statut = QLabel("Préparation…")
        self.statut.setWordWrap(True)
        self.progression = QProgressBar()
        self.progression.setRange(0, 0)
        self.progression.setMaximumHeight(8)
        self.progression.setTextVisible(False)
        racine.addWidget(self.titre)
        racine.addWidget(self.statut)
        racine.addWidget(self.progression)

        boutons = QHBoxLayout()
        boutons.addStretch(1)
        self.discover = QPushButton("Essayer avec Discover")
        self.discover.setObjectName("secondaire")
        self.reessayer = QPushButton("Réessayer")
        self.ouvrir = QPushButton("Ouvrir")
        self.ouvrir.setObjectName("primary")
        self.fermer = QPushButton("Annuler")
        self.fermer.setObjectName("secondaire")
        for bouton in (self.discover, self.reessayer, self.ouvrir, self.fermer):
            bouton.setCursor(Qt.PointingHandCursor)
            boutons.addWidget(bouton)
        racine.addLayout(boutons)
        self.discover.clicked.connect(self._discover)
        self.reessayer.clicked.connect(self.demarrer)
        self.ouvrir.clicked.connect(self._ouvrir)
        self.fermer.clicked.connect(self.close)
        self._boutons(discover=False, reessayer=False, ouvrir=False)

    # --- les boutons --------------------------------------------------------------------------------------------------

    def _boutons(self, discover, reessayer, ouvrir):
        self.discover.setVisible(discover)
        self.reessayer.setVisible(reessayer)
        self.ouvrir.setVisible(ouvrir)

    def _discover(self):
        launch.open_discover(self.identifiant)
        self.close()

    def _ouvrir(self):
        launch.run_flatpak(self.identifiant)
        self.close()

    def closeEvent(self, evenement):
        if self.en_cours():
            self.processus.terminate()
            self.processus.waitForFinished(2000)
        super().closeEvent(evenement)

    # --- l'installation : source Flathub présente ? (sinon l'ajouter), puis installation ----------------------------------

    def en_cours(self):
        return self.processus is not None and self.processus.state() != QProcess.NotRunning

    def demarrer(self):
        self.sortie = ""
        self.reussi = False
        self.progression.setVisible(True)
        self.fermer.setText("Annuler")
        self._boutons(discover=False, reessayer=False, ouvrir=False)
        self.statut.setText("Préparation…")
        self._lancer("depot", [self.flatpak, "remotes", "--system", "--columns=name"])

    def _lancer(self, etape, argv):
        self.etape = etape
        processus = QProcess(self)
        processus.setProcessChannelMode(QProcess.MergedChannels)
        processus.setProgram(argv[0])
        processus.setArguments(argv[1:])
        processus.readyRead.connect(lambda p=processus: self._lire(p))
        processus.finished.connect(lambda code, _s, p=processus: self._fini(p, code))
        processus.errorOccurred.connect(lambda _e, p=processus: self._introuvable(p))
        self.processus = processus
        processus.start()

    def _lire(self, processus):
        self.sortie += bytes(processus.readAll()).decode("utf-8", "replace")
        if self.etape == "installation":
            ligne = applications.derniere_ligne(self.sortie)
            if ligne:
                self.statut.setText(ligne)

    def _introuvable(self, processus):
        if processus.error() == QProcess.FailedToStart:
            self._terminer(False, "Flatpak n'a pas pu démarrer sur ce PC.")

    def _fini(self, processus, code):
        self._lire(processus)
        if self.etape == "depot":
            if code == 0 and "flathub" in self.sortie.split():
                self._installer()
            else:
                self.sortie = ""
                self.statut.setText("Ajout de la source d'applications Flathub… "
                                    "(une fenêtre peut demander le mot de passe d'un administrateur)")
                self._lancer("ajout", [self.flatpak, "remote-add", "--system", "--if-not-exists", "flathub", DEPOT])
        elif self.etape == "ajout":
            if code == 0:
                self._installer()
            else:
                self._terminer(False, self._cause(code))
        else:
            self._terminer(code == 0, "" if code == 0 else self._cause(code))

    def _installer(self):
        self.sortie = ""
        self.statut.setText(f"Installation de {self.nom}… (une fenêtre peut demander le mot de passe d'un administrateur)")
        self._lancer("installation", applications.commande([self.identifiant], self.flatpak))

    def _cause(self, code):
        cause = applications.explication_echec(self.sortie)
        detail = applications.derniere_ligne(self.sortie)
        return "L'installation s'est arrêtée. " + (cause or detail or f"Code {code}.")

    def _terminer(self, reussi, message=""):
        self.etape = "fini"
        self.reussi = reussi
        self.progression.setVisible(False)
        self.fermer.setText("Fermer")
        if reussi:
            self.statut.setText(f"✓ {self.nom} est installé. Vous le trouverez dans le menu des applications.")
            self._boutons(discover=False, reessayer=False, ouvrir=True)
        else:
            self.statut.setText(message)
            self._boutons(discover=True, reessayer=True, ouvrir=False)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage : binixx-installer-application IDENTIFIANT_FLATPAK", file=sys.stderr)
        return 2
    try:
        applications.valider(argv[0])
    except ValueError as erreur:
        print(erreur, file=sys.stderr)
        return 2
    app = QApplication(sys.argv[:1])
    app.setApplicationName("binixx-installer-application")
    app.setDesktopFileName("binixx-centre")
    app.setStyleSheet(theme.STYLE)
    fenetre = Fenetre(argv[0])
    fenetre.show()
    fenetre.demarrer()
    return app.exec()
