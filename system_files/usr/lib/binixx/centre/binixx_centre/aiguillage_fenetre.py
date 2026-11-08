"""Fenêtre « Ouvrir un programme Windows » : l'aiguillage d'un .exe ou d'un .msi (voir moteurs.py).

Elle montre les trois chemins (équivalent, Wine, Windows), le conseillé en premier et marqué, puis fait le travail :
  - Wine : installe Bottles s'il manque (fenêtre d'installation de BinixX OS), prépare la bouteille BinixX la première
    fois, ouvre le programme ; si rien ne s'affiche, un bouton propose Windows ;
  - Windows : ouvre WinBoat s'il est installé et que le PC peut faire tourner Windows, avec la marche à suivre ; sinon la
    page « Windows complet » du Centre, qui dit ce qui manque ;
  - équivalent : l'ouvre, ou l'installe.
Ouverte avec un moteur déjà choisi (choix retenu, menu du clic droit), elle passe directement au travail."""

import os
import sys

from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout,
                               QWidget)

from . import catalogue, launch, moteurs, theme, virtualisation, widgets

LARGEUR = 640
FERMETURE_AUTO_MS = 4000  # choix retenu : la fenêtre se ferme seule une fois le programme lancé
ICONES = {"equivalent": "package", "wine": "layers", "windows": "monitor"}
COULEURS = {"equivalent": theme.ACCENTS["vert"], "wine": theme.ACCENTS["bleu"], "windows": theme.ACCENTS["indigo"]}


def _echapper(texte):
    return texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Fenetre(QWidget):
    def __init__(self, programme, entrees, regles, moteur=None, flatpak="flatpak", installateur=launch.INSTALLATEUR,
                 verifier=virtualisation.verifier, winboat=moteurs.trouver_winboat, installees=None):
        super().__init__()
        self.programme = os.path.abspath(programme)
        self.nom = os.path.basename(self.programme)
        self.flatpak = flatpak
        self.installateur = installateur
        self.verifier = verifier
        self.winboat = winboat
        self.auto = moteur is not None  # choix retenu ou menu du clic droit : pas d'écran de choix
        self.processus = None
        self.etape = None
        self.sortie = ""
        self.installation_tentee = False
        self.conseil = moteurs.conseiller(self.programme, entrees, regles)
        self.raison_windows = moteurs.windows_requis(regles, self.programme)  # connu pour ne pas marcher avec Wine
        installees = launch.installed_flatpaks() if installees is None else installees
        self.equivalent = None
        if self.conseil.equivalent is not None:
            self.equivalent = catalogue.etat(self.conseil.equivalent, installees, catalogue.fournies())

        self.setWindowTitle(f"Ouvrir {self.nom}")
        self.setFixedWidth(LARGEUR)
        page = QVBoxLayout(self)
        page.setContentsMargins(24, 22, 24, 18)
        page.setSpacing(12)
        entete = widgets.entete(
            "Ouvrir un programme Windows",
            f"« {self.nom} » est fait pour Windows. BinixX OS peut l'ouvrir de plusieurs façons : la plus adaptée est "
            "en premier.", "layers")
        entete.texte.setTextFormat(Qt.PlainText)  # le nom du fichier tel quel, jamais lu comme du HTML
        page.addWidget(entete)

        self.bandeau = QLabel()
        self.bandeau.setObjectName("bandeau")
        self.bandeau.setWordWrap(True)
        self.bandeau.setVisible(False)
        page.addWidget(self.bandeau)

        # --- écran de choix
        self.choix = QWidget()
        colonne = QVBoxLayout(self.choix)
        colonne.setContentsMargins(0, 0, 0, 0)
        colonne.setSpacing(10)
        self.cartes = {}
        for moteur_ in self._ordre():
            carte = self._carte(moteur_)
            if carte is not None:
                self.cartes[moteur_] = carte
                colonne.addWidget(carte)
        self.retenir = QCheckBox("Retenir ce choix pour ce programme")
        colonne.addWidget(self.retenir)
        page.addWidget(self.choix)

        # --- écran de travail
        self.statut = QLabel()
        self.statut.setWordWrap(True)
        self.statut.setTextFormat(Qt.RichText)
        self.statut.setVisible(False)
        page.addWidget(self.statut)
        self.progression = QProgressBar()
        self.progression.setRange(0, 0)
        self.progression.setTextVisible(False)
        self.progression.setFixedHeight(8)
        self.progression.setVisible(False)
        page.addWidget(self.progression)

        boutons = QHBoxLayout()
        self.autres = QPushButton("Autres solutions")
        self.autres.setCursor(Qt.PointingHandCursor)
        self.autres.clicked.connect(self._autres_solutions)
        self.essayer_windows = QPushButton("Ouvrir dans Windows")
        self.essayer_windows.setObjectName("primary")
        self.essayer_windows.setCursor(Qt.PointingHandCursor)
        self.essayer_windows.clicked.connect(lambda: self.choisir("windows"))
        self.essayer_windows.setVisible(False)
        self.fermer = QPushButton("Fermer")
        self.fermer.setCursor(Qt.PointingHandCursor)
        self.fermer.clicked.connect(self.close)
        boutons.addWidget(self.autres)
        boutons.addStretch(1)
        boutons.addWidget(self.essayer_windows)
        boutons.addWidget(self.fermer)
        page.addLayout(boutons)

        if moteur is not None:
            QTimer.singleShot(0, lambda: self.choisir(moteur))

    # --- écran de choix ----------------------------------------------------------------------------------------------------

    def _ordre(self):
        """Le conseillé d'abord, puis les autres du plus léger au plus lourd ; Wine en dernier s'il est connu pour échouer."""
        suite = ("equivalent", "windows", "wine") if self.raison_windows else moteurs.MOTEURS
        return [self.conseil.moteur] + [m for m in suite if m != self.conseil.moteur]

    def _carte(self, moteur):
        conseille = moteur == self.conseil.moteur
        marque = "   <span style='font-weight:400; font-size:9pt;'>· Conseillé</span>" if conseille else ""
        details = self.conseil.raison if conseille and not self.conseil.retenu else None
        if moteur == "equivalent":
            if self.equivalent is None:
                return None
            badge, bouton, _ = self.equivalent
            entree = self.conseil.equivalent
            return widgets.carte(f"{_echapper(entree.remplacant)}{marque}", entree.remarque, bouton or "Voir",
                                 lambda: self.choisir("equivalent"), avant=f"Équivalent sous BinixX OS · {badge}",
                                 icone=catalogue.icone_de(entree.categorie), couleurs=COULEURS[moteur])
        if moteur == "wine":
            if self.raison_windows:
                details = "Déconseillé : " + self.raison_windows
            return widgets.carte(f"Avec Wine{marque}", "Sans Windows, directement : rapide ; marche avec beaucoup de "
                                 "logiciels, pas tous.", "Ouvrir avec Wine", lambda: self.choisir("wine"),
                                 details=details, avant="Compatibilité Windows", icone=ICONES[moteur],
                                 couleurs=COULEURS[moteur])
        return widgets.carte(f"Dans Windows{marque}", "Le vrai Windows en arrière-plan (WinBoat), le programme dans sa "
                             "propre fenêtre : le plus compatible ; demande une licence Windows et de la mémoire.",
                             "Ouvrir dans Windows", lambda: self.choisir("windows"), details=details,
                             avant="Windows complet", icone=ICONES[moteur], couleurs=COULEURS[moteur])

    def _ajuster(self):
        """Les textes sur plusieurs lignes : la fenêtre prend la hauteur qu'il leur faut à sa largeur."""
        self.setMinimumHeight(self.layout().totalHeightForWidth(self.width()))

    def showEvent(self, evenement):
        super().showEvent(evenement)
        QTimer.singleShot(0, self._ajuster)

    def choisir(self, moteur):
        if not self.auto and self.retenir.isChecked():
            try:
                moteurs.retenir(self.programme, moteur)
            except OSError:
                pass
        if moteur == "equivalent":
            self._equivalent()
        elif moteur == "windows":
            self._windows()
        else:
            self._wine()

    def _travail(self, texte, en_cours=True):
        self.choix.setVisible(False)
        self.statut.setText(texte)
        self.statut.setVisible(True)
        self.progression.setVisible(en_cours)
        self.essayer_windows.setVisible(False)
        self.fermer.setText("Annuler" if en_cours else "Fermer")
        self.setMinimumHeight(0)
        QTimer.singleShot(0, self._ajuster)
        QTimer.singleShot(0, lambda: self.resize(self.width(), self.minimumHeight()))

    def _autres_solutions(self):
        launch.open_centre("catalogue", catalogue.deviner_programme(self.programme))
        self.close()

    # --- équivalent --------------------------------------------------------------------------------------------------------

    def _equivalent(self):
        if self.equivalent is None or self.equivalent[2] is None:
            self._autres_solutions()
            return
        launch.executer(self.equivalent[2])
        self.close()

    # --- Windows (WinBoat) -------------------------------------------------------------------------------------------------

    def _windows(self):
        lanceur = self.winboat()
        if lanceur and moteurs.windows_possible(self.verifier()):
            launch.open_desktop_file(lanceur)
            self._travail(
                f"<b>WinBoat s'ouvre.</b> Votre dossier personnel y est partagé avec Windows : dans WinBoat, choisissez "
                f"« Apps », puis « Add custom » (ajouter), et prenez <b>{_echapper(self.nom)}</b> dans le dossier "
                f"<i>{_echapper(os.path.dirname(self.programme))}</i>. Le programme aura ensuite sa propre fenêtre.",
                en_cours=False)
            return
        # WinBoat absent ou PC pas prêt : la page du Centre dit quoi faire (virtualisation, mémoire, installation)
        launch.open_centre("windows")
        self.close()

    # --- Wine (Bottles) ----------------------------------------------------------------------------------------------------

    def _wine(self):
        self._travail("Vérification de Wine (Bottles)…")
        self._lancer("installee", moteurs.commande_installee(self.flatpak))

    def _lancer(self, etape, argv):
        self.etape = etape
        self.sortie = ""
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

    def _introuvable(self, processus):
        if processus.error() == QProcess.FailedToStart and processus is self.processus:
            self.etape = "fini"
            self._echec("Flatpak n'a pas pu démarrer sur ce PC.")

    def _fini(self, processus, code):
        if processus is not self.processus or self.etape == "fini":
            return
        self._lire(processus)
        etape = self.etape
        if etape == "installee":
            if code == 0:
                self._lancer("lister", moteurs.commande_lister(self.flatpak))
            elif not self.installation_tentee:
                self.installation_tentee = True
                self.statut.setText("Installation de Bottles, qui fait tourner les programmes Windows avec Wine… "
                                    "(une fenêtre suit l'installation)")
                self._lancer("installation", [self.installateur, moteurs.BOTTLES])
            else:
                self._echec("Bottles n'est pas installé : l'installation n'a pas abouti ou a été annulée.")
        elif etape == "installation":
            self._lancer("installee", moteurs.commande_installee(self.flatpak))
        elif etape == "lister":
            if code == 0 and moteurs.bouteille_existe(self.sortie):
                self._ouvrir()
            else:
                self.statut.setText("Préparation de Wine pour la première fois : cela prend quelques minutes, une seule "
                                    "fois…")
                self._lancer("creer", moteurs.commande_creer(self.flatpak))
        elif etape == "creer":
            if code == 0:
                self._ouvrir()
            else:
                self._echec("La bouteille Wine de BinixX OS n'a pas pu être préparée. " + self._derniere_ligne())
        elif etape == "lancer":
            self.etape = "fini"
            if code == 0:
                self._reussi()
            else:
                self._echec("Wine n'a pas pu ouvrir ce programme. " + self._derniere_ligne())

    def _ouvrir(self):
        self.statut.setText(f"Ouverture de <b>{_echapper(self.nom)}</b> avec Wine…")
        self._lancer("lancer", moteurs.commande_lancer(self.programme, self.flatpak))

    def _derniere_ligne(self):
        lignes = [ligne.strip() for ligne in self.sortie.splitlines() if ligne.strip()]
        return _echapper(lignes[-1][:200]) if lignes else ""

    def _reussi(self):
        self._travail(f"✓ <b>{_echapper(self.nom)}</b> démarre avec Wine. Rien ne s'affiche d'ici une minute ? Ce "
                      "programme a peut-être besoin du vrai Windows.", en_cours=False)
        self.essayer_windows.setVisible(True)
        if self.auto:
            QTimer.singleShot(FERMETURE_AUTO_MS, self.close)

    def _echec(self, message):
        self.etape = "fini"
        self._travail(message, en_cours=False)
        self.bandeau.setText("Wine n'a pas réussi : essayez Windows lui-même, ou un équivalent (« Autres solutions »).")
        self.bandeau.setVisible(True)
        self.essayer_windows.setVisible(True)

    def closeEvent(self, evenement):
        # le programme lancé par Wine continue ; on n'arrête qu'une préparation en cours
        if self.processus is not None and self.processus.state() != QProcess.NotRunning and self.etape != "lancer":
            self.processus.terminate()
            self.processus.waitForFinished(2000)
        super().closeEvent(evenement)


def main(programme, entrees, regles, moteur=None):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("binixx-ouvrir-windows")
    app.setDesktopFileName("binixx-centre")
    app.setStyleSheet(theme.feuille(theme.est_sombre(app.palette())))
    fenetre = Fenetre(programme, entrees, regles, moteur=moteur)
    fenetre.show()
    return app.exec()
