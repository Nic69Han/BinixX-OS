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

from PySide6.QtCore import QProcess, QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from . import catalogue, launch, moteurs, theme, virtualisation, widgets

LARGEUR = 440
FERMETURE_AUTO_MS = 4000  # choix retenu : la fenêtre se ferme seule une fois le programme lancé
# Des images qui se comprennent d'un coup d'œil, sans nom technique : un éclair (ouvrir ici, vite), les quatre carreaux
# (dans Windows) ; l'équivalent montre l'icône de l'application elle-même
ICONES = {"equivalent": "package", "wine": "zap", "windows": "grid"}
COULEURS = {"equivalent": theme.ACCENTS["vert"], "wine": theme.ACCENTS["ambre"], "windows": theme.ACCENTS["bleu"]}
TAILLE_ICONE = 36

# La boîte « Ouvrir avec » de Windows 11, que les habitués de Windows connaissent : on sélectionne une ligne (la
# recommandée l'est d'avance), puis « Juste une fois » ou « Toujours » ; un double-clic ouvre tout de suite
STYLE = f"""
QPushButton#choixLigne {{ background: transparent; border: none; border-radius: 12px; padding: 0; text-align: left; }}
QPushButton#choixLigne:hover {{ background: rgba(128,128,128,0.12); }}
QPushButton#choixLigne:focus {{ outline: none; }}
QPushButton#choixLigne:checked {{ background: rgba(173,207,251,0.45); }}
QLabel#choixTitre {{ font-size: 10.5pt; font-weight: 600; background: transparent; }}
QLabel#choixSous {{ font-size: 9pt; background: transparent; }}
QLabel#choixPastille {{ background: {theme.BLUE}; color: white; border-radius: 9px; padding: 2px 9px;
                        font-size: 8pt; font-weight: 600; }}
QLabel#aiguillageNom {{ font-size: 12pt; font-weight: 700; }}
QPushButton#lien {{ background: transparent; border: none; color: {theme.BLUE}; padding: 4px 2px; }}
QPushButton#lien:hover {{ text-decoration: underline; }}
"""


def _echapper(texte):
    return texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Ligne(QPushButton):
    """Une ligne à sélectionner : icône, titre, une ligne de précision, et « Recommandé » à droite. Double-clic : ouvrir."""

    def __init__(self, titre, sous_titre, icone, couleurs, conseille=False, explication="", image=None):
        super().__init__()
        self.setObjectName("choixLigne")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.double_clic = None
        self.setToolTip(explication)
        self.setAccessibleName(f"{titre} : {sous_titre}")
        ligne = QHBoxLayout(self)
        ligne.setContentsMargins(10, 8, 12, 8)
        ligne.setSpacing(12)
        if image is not None:  # l'icône de l'application elle-même
            etiquette = QLabel()
            etiquette.setPixmap(image)
            etiquette.setFixedSize(TAILLE_ICONE, TAILLE_ICONE)
            ligne.addWidget(etiquette)
        else:
            ligne.addWidget(widgets.pastille_label(icone, couleurs, TAILLE_ICONE))
        colonne = QVBoxLayout()
        colonne.setSpacing(0)
        haut = QLabel(titre)
        haut.setObjectName("choixTitre")
        haut.setTextFormat(Qt.PlainText)
        bas = QLabel(sous_titre)
        bas.setObjectName("choixSous")
        bas.setTextFormat(Qt.PlainText)
        bas.setEnabled(False)  # gris discret du thème
        colonne.addWidget(haut)
        colonne.addWidget(bas)
        ligne.addLayout(colonne, 1)
        if conseille:
            marque = QLabel("Recommandé")
            marque.setObjectName("choixPastille")
            ligne.addWidget(marque, 0, Qt.AlignVCenter)
        for enfant in self.findChildren(QLabel):
            enfant.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setMinimumHeight(56)

    def mouseDoubleClickEvent(self, evenement):
        if self.double_clic is not None:
            self.double_clic()
        else:
            super().mouseDoubleClickEvent(evenement)


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

        self.setWindowTitle("Ouvrir avec")
        self.setStyleSheet(STYLE)
        self.setFixedWidth(LARGEUR)
        page = QVBoxLayout(self)
        page.setContentsMargins(18, 16, 18, 14)
        page.setSpacing(10)

        # --- le fichier : son nom, et ce que c'est
        tete = QHBoxLayout()
        tete.setSpacing(12)
        icone_fichier = QIcon.fromTheme("application-x-ms-dos-executable")
        if icone_fichier.isNull():
            tete.addWidget(widgets.pastille_label("file", theme.ACCENTS["bleu"], 40))
        else:
            fichier = QLabel()
            fichier.setPixmap(icone_fichier.pixmap(QSize(40, 40)))
            fichier.setFixedSize(40, 40)
            tete.addWidget(fichier)
        noms = QVBoxLayout()
        noms.setSpacing(0)
        question = QLabel("Comment voulez-vous ouvrir ce fichier ?")  # la question de Windows
        question.setObjectName("aiguillageNom")
        precision = QLabel(self.nom)
        precision.setTextFormat(Qt.PlainText)  # le nom du fichier tel quel, jamais lu comme du HTML
        precision.setToolTip(self.programme)
        precision.setEnabled(False)
        noms.addWidget(question)
        noms.addWidget(precision)
        tete.addLayout(noms, 1)
        page.addLayout(tete)

        self.bandeau = QLabel()
        self.bandeau.setObjectName("bandeau")
        self.bandeau.setWordWrap(True)
        self.bandeau.setVisible(False)
        page.addWidget(self.bandeau)

        # --- écran de choix : une ligne par chemin, le conseillé en premier
        self.choix = QWidget()
        colonne = QVBoxLayout(self.choix)
        colonne.setContentsMargins(0, 0, 0, 0)
        colonne.setSpacing(2)
        self.cartes = {}
        self.groupe = QButtonGroup(self)
        self.groupe.setExclusive(True)
        for moteur_ in self._ordre():
            ligne = self._ligne(moteur_)
            if ligne is not None:
                ligne.double_clic = lambda m=moteur_: self.choisir(m)
                self.groupe.addButton(ligne)
                self.cartes[moteur_] = ligne
                colonne.addWidget(ligne)
        if self.cartes:
            self.cartes[self.conseil.moteur if self.conseil.moteur in self.cartes else next(iter(self.cartes))].setChecked(True)
        self.autres = QPushButton("Plus d'options")
        self.autres.setObjectName("lien")
        self.autres.setCursor(Qt.PointingHandCursor)
        self.autres.clicked.connect(self._autres_solutions)
        colonne.addWidget(self.autres, 0, Qt.AlignLeft)
        bas = QHBoxLayout()
        bas.setContentsMargins(0, 6, 0, 0)
        bas.addStretch(1)
        self.toujours = QPushButton("Toujours")
        self.toujours.setCursor(Qt.PointingHandCursor)
        self.toujours.clicked.connect(lambda: self.choisir(self.selection(), toujours=True))
        self.une_fois = QPushButton("Juste une fois")
        self.une_fois.setObjectName("primary")
        self.une_fois.setCursor(Qt.PointingHandCursor)
        self.une_fois.setDefault(True)  # Entrée
        self.une_fois.clicked.connect(lambda: self.choisir(self.selection()))
        bas.addWidget(self.toujours)
        bas.addWidget(self.une_fois)
        colonne.addLayout(bas)
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
        self.progression.setFixedHeight(6)
        self.progression.setVisible(False)
        page.addWidget(self.progression)

        self.boutons = QWidget()
        boutons = QHBoxLayout(self.boutons)
        boutons.setContentsMargins(0, 4, 0, 0)
        self.essayer_windows = QPushButton("Ouvrir dans Windows")
        self.essayer_windows.setObjectName("primary")
        self.essayer_windows.setCursor(Qt.PointingHandCursor)
        self.essayer_windows.clicked.connect(lambda: self.choisir("windows"))
        self.essayer_windows.setVisible(False)
        self.fermer = QPushButton("Fermer")
        self.fermer.setCursor(Qt.PointingHandCursor)
        self.fermer.clicked.connect(self.close)
        autres = QPushButton("Plus d'options")
        autres.setObjectName("lien")
        autres.setCursor(Qt.PointingHandCursor)
        autres.clicked.connect(self._autres_solutions)
        boutons.addWidget(autres)
        boutons.addStretch(1)
        boutons.addWidget(self.essayer_windows)
        boutons.addWidget(self.fermer)
        self.boutons.setVisible(False)  # l'écran de choix se ferme avec la croix de la fenêtre ou Échap
        page.addWidget(self.boutons)

        if moteur is not None:
            QTimer.singleShot(0, lambda: self.choisir(moteur))

    # --- écran de choix ----------------------------------------------------------------------------------------------------

    def _ordre(self):
        """Le conseillé d'abord, puis les autres du plus léger au plus lourd ; Wine en dernier s'il est connu pour échouer."""
        suite = ("equivalent", "windows", "wine") if self.raison_windows else moteurs.MOTEURS
        return [self.conseil.moteur] + [m for m in suite if m != self.conseil.moteur]

    def selection(self):
        """Le chemin de la ligne sélectionnée."""
        for moteur, ligne in self.cartes.items():
            if ligne.isChecked():
                return moteur
        return self.conseil.moteur

    def _ligne(self, moteur):
        conseille = moteur == self.conseil.moteur
        verbe = "Installer" if moteurs.est_installateur(self.programme) else "Lancer"
        if moteur == "equivalent":
            if self.equivalent is None:
                return None
            _, bouton, _ = self.equivalent
            entree = self.conseil.equivalent
            etat = {"Ouvrir": "déjà installé", "Ouvrir le site": "en ligne"}.get(bouton, "à installer")
            # le nom du logiciel Windows qu'on connaît : « Remplace Microsoft Word »
            return Ligne(entree.remplacant, f"Remplace {entree.windows} · {etat}", catalogue.icone_de(entree.categorie),
                         COULEURS[moteur], conseille, entree.remarque, image=self._icone_application(entree))
        if moteur == "wine":
            sous_titre = "Déconseillé pour ce programme" if self.raison_windows else "Rapide · pas avec tous les programmes"
            return Ligne(f"{verbe} le programme", sous_titre, ICONES[moteur], COULEURS[moteur], conseille,
                         self.raison_windows or "Le programme s'ouvre directement sur BinixX OS, sans Windows. Beaucoup "
                         "de programmes marchent ainsi, pas tous.")
        return Ligne(f"{verbe} dans Windows", "Marche presque toujours · plus lent à démarrer", ICONES[moteur],
                     COULEURS[moteur], conseille, "Windows tourne en arrière-plan et le programme s'affiche dans sa "
                     "propre fenêtre. Il faut une licence Windows, et un PC assez puissant.")

    @staticmethod
    def _icone_application(entree):
        """L'icône de l'équivalent (son identifiant Flatpak ou son lanceur), ou None : on garde alors la pastille."""
        if entree.type not in ("inclus", "flatpak"):
            return None
        icone = QIcon.fromTheme(entree.cible)
        return None if icone.isNull() else icone.pixmap(QSize(TAILLE_ICONE, TAILLE_ICONE))

    def keyPressEvent(self, evenement):
        if evenement.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(evenement)

    def _ajuster(self):
        """Les textes sur plusieurs lignes : la fenêtre prend la hauteur qu'il leur faut à sa largeur."""
        self.setMinimumHeight(self.layout().totalHeightForWidth(self.width()))

    def showEvent(self, evenement):
        super().showEvent(evenement)
        QTimer.singleShot(0, self._ajuster)
        if not self.auto:
            self.une_fois.setFocus()  # Entrée : « Juste une fois » sur la ligne recommandée

    def choisir(self, moteur, toujours=False):
        """Ouvre par ce chemin ; `toujours` : le retenir pour ce programme (bouton « Toujours »)."""
        if toujours:
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
        self.boutons.setVisible(True)
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
                f"<b>Windows démarre.</b> Dans la fenêtre qui s'ouvre, choisissez « Apps » puis « Add custom », et prenez "
                f"<b>{_echapper(self.nom)}</b> dans <i>{_echapper(os.path.dirname(self.programme))}</i> : vos dossiers "
                "sont partagés avec Windows. Le programme aura ensuite sa propre fenêtre.",
                en_cours=False)
            return
        # WinBoat absent ou PC pas prêt : la page du Centre dit quoi faire (virtualisation, mémoire, installation)
        launch.open_centre("windows")
        self.close()

    # --- Wine (Bottles) ----------------------------------------------------------------------------------------------------

    def _wine(self):
        self._travail("Préparation…")
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
            self._echec("Le programme ne peut pas s'ouvrir ici sur ce PC.")

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
                self.statut.setText("Installation de ce qu'il faut pour ouvrir les programmes Windows… (une fenêtre "
                                    "suit l'installation, une seule fois)")
                self._lancer("installation", [self.installateur, moteurs.BOTTLES])
            else:
                self._echec("L'installation n'a pas abouti ou a été annulée : le programme ne peut pas s'ouvrir ici.")
        elif etape == "installation":
            self._lancer("installee", moteurs.commande_installee(self.flatpak))
        elif etape == "lister":
            if code == 0 and moteurs.bouteille_existe(self.sortie):
                self._ouvrir()
            else:
                self.statut.setText("Première fois : préparation, quelques minutes, une seule fois…")
                self._lancer("creer", moteurs.commande_creer(self.flatpak))
        elif etape == "creer":
            if code == 0:
                self._ouvrir()
            else:
                self._echec("La préparation n'a pas abouti. " + self._derniere_ligne())
        elif etape == "lancer":
            self.etape = "fini"
            if code == 0:
                self._reussi()
            else:
                self._echec("Ce programme n'a pas pu s'ouvrir ici. " + self._derniere_ligne())

    def _ouvrir(self):
        self.statut.setText(f"Ouverture de <b>{_echapper(self.nom)}</b>…")
        self._lancer("lancer", moteurs.commande_lancer(self.programme, self.flatpak))

    def _derniere_ligne(self):
        lignes = [ligne.strip() for ligne in self.sortie.splitlines() if ligne.strip()]
        return _echapper(lignes[-1][:200]) if lignes else ""

    def _reussi(self):
        self._travail("✓ Le programme s'ouvre. Rien ne s'affiche d'ici une minute ? Ouvrez-le dans Windows.",
                      en_cours=False)
        self.essayer_windows.setVisible(True)
        if self.auto:
            QTimer.singleShot(FERMETURE_AUTO_MS, self.close)

    def _echec(self, message):
        self.etape = "fini"
        self._travail(message, en_cours=False)
        self.bandeau.setText("Ça n'a pas marché ici : ouvrez-le dans Windows, ou voyez les autres solutions.")
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
