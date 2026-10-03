"""Fenêtre de la recherche unique (Windows + S) : une barre, une liste groupée, Entrée ouvre la première ligne.

Une petite fenêtre à part, sans le Centre : elle s'ouvre vite, se ferme avec Échap, un clic à côté ou l'ouverture d'un
résultat. Les résultats viennent de recherche.py ; les fichiers (baloosearch6) arrivent après, sans bloquer la frappe."""

import argparse
import os
import sys

from PySide6.QtCore import QEvent, QProcess, QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout,
                               QWidget)

from . import launch, recherche, theme, widgets

LARGEUR = 680
HAUTEUR_MAX = 470
DELAI_FRAPPE = 110      # millisecondes entre la dernière touche et la recherche
DELAI_ACTIVATION = 400  # avant ce délai, perdre le focus ne ferme pas la fenêtre (elle vient de s'ouvrir)

STYLE = f"""
QFrame#recherchePanneau {{ background: palette(window); border: 1px solid rgba(128,128,128,0.45); border-radius: 20px; }}
QListWidget#resultats {{ background: transparent; border: none; outline: 0; }}
QListWidget#resultats::item {{ border-radius: 12px; padding: 0; }}
QListWidget#resultats::item:hover {{ background: rgba(47,91,255,0.10); }}
QListWidget#resultats::item:selected {{ background: rgba(47,91,255,0.22); }}
QLabel#rechercheCategorie {{ font-size: 8.5pt; font-weight: 700; padding: 8px 8px 2px 8px; background: transparent; }}
QLabel#resultatTitre {{ font-size: 10.5pt; font-weight: 600; background: transparent; }}
QLabel#resultatPrecision {{ font-size: 8.5pt; background: transparent; }}
QLabel#rechercheAide {{ padding: 4px 14px 10px 14px; background: transparent; }}
"""


def icone(nom, taille=32):
    """L'icône d'un résultat : un pictogramme de BinixX OS (« :settings »), une icône du thème ou un chemin d'image."""
    if nom.startswith(":"):
        return QIcon(widgets.pastille(nom[1:], theme.ACCENTS["bleu"], taille))
    if os.path.isabs(nom):
        pixmap = QPixmap(nom)
        if not pixmap.isNull():
            return QIcon(pixmap)
    sortie = QIcon.fromTheme(nom) if nom else QIcon()
    return sortie if not sortie.isNull() else QIcon.fromTheme("application-x-executable")


class Fenetre(QWidget):
    def __init__(self, index=None, ouvrir=None):
        super().__init__()
        self.index = index if index is not None else recherche.Index(aide=self._sujets_d_aide())
        self.ouvrir = ouvrir or recherche.ouvrir
        self.groupes = []
        self.fichiers = []
        self.processus = None
        self.prete = False
        self.setObjectName("rechercheFenetre")
        self.setWindowTitle("Rechercher")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.setFixedWidth(LARGEUR)

        racine = QVBoxLayout(self)
        racine.setContentsMargins(0, 0, 0, 0)
        self.panneau = QFrame()
        self.panneau.setObjectName("recherchePanneau")
        racine.addWidget(self.panneau)
        colonne = QVBoxLayout(self.panneau)
        colonne.setContentsMargins(14, 14, 14, 12)
        colonne.setSpacing(8)
        self.champ = widgets.recherche("Applications, réglages, logiciels Windows, fichiers…", hauteur=52)
        self.champ.setMaximumWidth(16777215)
        self.champ.textChanged.connect(self._frappe)
        self.champ.installEventFilter(self)
        colonne.addWidget(self.champ)
        self.aide = QLabel("Tapez le nom d'une application, d'un réglage (« wifi », « imprimante »), d'un logiciel que "
                           "vous utilisiez sous Windows (« Word », « Photoshop ») ou d'un fichier.")
        self.aide.setObjectName("rechercheAide")
        self.aide.setWordWrap(True)
        self.aide.setForegroundRole(QPalette.PlaceholderText)
        colonne.addWidget(self.aide)
        self.liste = QListWidget()
        self.liste.setObjectName("resultats")
        self.liste.setIconSize(QSize(32, 32))
        self.liste.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.liste.setFocusPolicy(Qt.NoFocus)
        self.liste.setMouseTracking(True)
        self.liste.itemClicked.connect(lambda element: self._ouvrir_element(element))
        self.liste.hide()
        colonne.addWidget(self.liste)

        self.minuteur = QTimer(self)
        self.minuteur.setSingleShot(True)
        self.minuteur.setInterval(DELAI_FRAPPE)
        self.minuteur.timeout.connect(self.chercher)
        self.adapter_la_taille()

    @staticmethod
    def _sujets_d_aide():
        """Les cas d'aide du Centre (titre, explication), pour qu'on les trouve en cherchant « imprimante » ou « lent »."""
        try:
            from .pages import aide
            return [(titre, texte) for titre, texte, _bouton, _action in aide.PROBLEMES]
        except Exception:  # sans la page d'aide, la recherche marche quand même
            return []

    # --- affichage ---------------------------------------------------------------------------------------------

    def showEvent(self, evenement):
        super().showEvent(evenement)
        self.champ.setFocus()
        QTimer.singleShot(DELAI_ACTIVATION, lambda: setattr(self, "prete", True))

    def changeEvent(self, evenement):
        super().changeEvent(evenement)
        if evenement.type() == QEvent.ActivationChange and self.prete and not self.isActiveWindow():
            self.close()   # un clic ailleurs ferme la recherche, comme dans Windows

    def adapter_la_taille(self):
        total = sum(self.liste.sizeHintForRow(i) for i in range(self.liste.count()))
        self.liste.setVisible(self.liste.count() > 0)
        self.liste.setFixedHeight(min(total + 6, HAUTEUR_MAX - 90) if self.liste.count() else 0)
        self.aide.setVisible(self.liste.count() == 0 and not self.champ.text().strip())
        self.adjustSize()

    def afficher(self, groupes):
        """Remplit la liste : un titre par catégorie, puis ses résultats ; le premier est sélectionné."""
        self.groupes = groupes
        self.liste.clear()
        premier = None
        for categorie, resultats in groupes:
            titre = QListWidgetItem()
            titre.setFlags(Qt.NoItemFlags)
            etiquette = QLabel(categorie.upper())
            etiquette.setObjectName("rechercheCategorie")
            etiquette.setForegroundRole(QPalette.PlaceholderText)
            titre.setSizeHint(QSize(LARGEUR - 60, 30))
            self.liste.addItem(titre)
            self.liste.setItemWidget(titre, etiquette)
            for resultat in resultats:
                element = QListWidgetItem()
                element.setData(Qt.UserRole, resultat)
                element.setSizeHint(QSize(LARGEUR - 60, 54))
                self.liste.addItem(element)
                self.liste.setItemWidget(element, self._ligne(resultat))
                premier = premier or element
        if premier is not None:
            self.liste.setCurrentItem(premier)
        self.adapter_la_taille()

    def _ligne(self, resultat):
        ligne = QWidget()
        corps = QHBoxLayout(ligne)
        corps.setContentsMargins(10, 4, 10, 4)
        corps.setSpacing(12)
        pastille = QLabel()
        pastille.setPixmap(icone(resultat.icone).pixmap(QSize(32, 32)))
        pastille.setFixedSize(32, 32)
        corps.addWidget(pastille)
        texte = QVBoxLayout()
        texte.setSpacing(0)
        titre = QLabel(resultat.titre)
        titre.setObjectName("resultatTitre")
        texte.addWidget(titre)
        if resultat.precision:
            precision = QLabel(self.liste.fontMetrics().elidedText(resultat.precision, Qt.ElideRight, LARGEUR - 170))
            precision.setObjectName("resultatPrecision")
            precision.setForegroundRole(QPalette.PlaceholderText)
            texte.addWidget(precision)
        corps.addLayout(texte, 1)
        ligne.setAttribute(Qt.WA_TransparentForMouseEvents)
        return ligne

    def elements(self):
        """Les lignes de résultat (sans les titres de catégorie), dans l'ordre."""
        return [self.liste.item(i) for i in range(self.liste.count())
                if self.liste.item(i).data(Qt.UserRole) is not None]

    # --- recherche ---------------------------------------------------------------------------------------------

    def _frappe(self, _texte=""):
        self._arreter_les_fichiers()
        self.fichiers = []
        if not self.champ.text().strip():
            self.minuteur.stop()
            self.afficher([])
            return
        self.minuteur.start()

    def chercher(self):
        texte = self.champ.text()
        self.afficher(self.index.chercher(texte))
        commande = recherche.commande_fichiers(texte)
        if commande:
            self._lancer_les_fichiers(commande)

    def _arreter_les_fichiers(self):
        if self.processus is not None:
            self.processus.blockSignals(True)
            if self.processus.state() != QProcess.NotRunning:
                self.processus.kill()
            self.processus = None

    def _lancer_les_fichiers(self, argv):
        """Cherche les fichiers sans bloquer la frappe ; la catégorie « Fichiers » s'ajoute à la fin quand elle arrive."""
        processus = QProcess(self)
        processus.setProcessChannelMode(QProcess.SeparateChannels)
        texte_cherche = self.champ.text()

        def fini(code, _statut):
            if self.processus is not processus or self.champ.text() != texte_cherche:
                return   # une frappe plus récente a déjà remplacé cette recherche
            if code == 0:
                self.fichiers = recherche.lire_fichiers(bytes(processus.readAllStandardOutput()).decode("utf-8", "replace"))
                if self.fichiers:
                    courant = self.liste.currentRow()
                    self.afficher(recherche.ajouter_fichiers(self.groupes, self.fichiers))
                    if courant >= 0:
                        self.liste.setCurrentRow(courant)

        processus.finished.connect(fini)
        self.processus = processus
        QTimer.singleShot(recherche.DELAI_FICHIERS * 1000, lambda: processus.kill() if processus.state() != QProcess.NotRunning else None)
        processus.start(argv[0], argv[1:])
        return processus

    # --- clavier et ouverture ----------------------------------------------------------------------------------

    def eventFilter(self, objet, evenement):
        if objet is self.champ and evenement.type() == QEvent.KeyPress:
            touche = evenement.key()
            if touche in (Qt.Key_Down, Qt.Key_Up):
                self.deplacer(1 if touche == Qt.Key_Down else -1)
                return True
            if touche in (Qt.Key_Return, Qt.Key_Enter):
                self.ouvrir_courant()
                return True
            if touche == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(objet, evenement)

    def deplacer(self, sens):
        """Passe au résultat suivant (sens = 1) ou précédent (sens = -1), sans s'arrêter sur un titre de catégorie."""
        elements = self.elements()
        if not elements:
            return
        courant = self.liste.currentItem()
        position = elements.index(courant) if courant in elements else -1
        self.liste.setCurrentItem(elements[(position + sens) % len(elements)])

    def ouvrir_courant(self):
        elements = self.elements()
        if self.minuteur.isActive():     # Entrée pressée juste après la frappe : on cherche d'abord
            self.minuteur.stop()
            self.chercher()
            elements = self.elements()
        courant = self.liste.currentItem()
        if courant is not None and courant.data(Qt.UserRole) is not None:
            self._ouvrir_element(courant)
        elif elements:
            self._ouvrir_element(elements[0])

    def _ouvrir_element(self, element):
        resultat = element.data(Qt.UserRole)
        if resultat is not None and self.ouvrir(resultat):
            self.close()

    def closeEvent(self, evenement):
        self._arreter_les_fichiers()
        super().closeEvent(evenement)


def parse(argv):
    parser = argparse.ArgumentParser(prog="binixx-recherche", description="Recherche unique de BinixX OS (Windows + S).")
    parser.add_argument("--test", metavar="DOSSIER",
                        help="ouvre la fenêtre hors écran, cherche « imprimante », en enregistre une capture, puis quitte")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("binixx-recherche")
    app.setDesktopFileName("binixx-recherche")
    app.setStyleSheet(theme.STYLE)
    fenetre = Fenetre()
    if args.test:
        os.makedirs(args.test, exist_ok=True)
        fenetre.show()
        fenetre.champ.setText("imprimante")
        fenetre.chercher()
        app.processEvents()
        fenetre.grab().save(os.path.join(args.test, "recherche.png"))
        print(f"résultats : {len(fenetre.elements())}")
        return 0 if fenetre.elements() else 1
    fenetre.show()
    return app.exec()
