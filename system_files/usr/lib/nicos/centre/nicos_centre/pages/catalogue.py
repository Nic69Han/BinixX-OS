"""Mon logiciel Windows : l'équivalent sous NicOS de ce que l'on utilisait sous Windows."""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout,
                               QWidget)

from .. import catalogue, launch

ORDER = 20
KEY = "catalogue"
TITLE = "Mon logiciel Windows"

MAX_RESULTATS = 30
BOTTLES = "com.usebottles.bottles"


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.entrees = []
        self.erreur = ""
        try:
            self.entrees = catalogue.charger()
        except (OSError, ValueError) as erreur:
            self.erreur = str(erreur)
        self.installees = launch.installed_flatpaks()
        self.fournies = catalogue.fournies()

        page = QVBoxLayout(self)
        page.setContentsMargins(32, 28, 32, 20)
        page.setSpacing(12)
        titre = QLabel("Mon logiciel Windows")
        titre.setObjectName("pageTitle")
        intro = QLabel("Tapez le nom du logiciel que vous utilisiez sous Windows (Word, Sage, Photoshop, "
                       "Teams…) : voici ce qui le remplace sous NicOS.")
        intro.setObjectName("pageLead")
        intro.setWordWrap(True)
        page.addWidget(titre)
        page.addWidget(intro)

        self.bandeau = QLabel()
        self.bandeau.setObjectName("card")
        self.bandeau.setWordWrap(True)
        self.bandeau.setMargin(12)
        self.bandeau.setVisible(False)
        page.addWidget(self.bandeau)

        self.recherche = QLineEdit()
        self.recherche.setPlaceholderText("Quel logiciel Windows utilisiez-vous ?")
        self.recherche.setClearButtonEnabled(True)
        self.recherche.setMinimumHeight(38)
        self.recherche.textChanged.connect(self.afficher)
        page.addWidget(self.recherche)

        self.liste = QVBoxLayout()
        self.liste.setSpacing(10)
        contenu = QWidget()
        contenu_layout = QVBoxLayout(contenu)
        contenu_layout.setContentsMargins(0, 0, 8, 0)
        contenu_layout.addLayout(self.liste)
        contenu_layout.addStretch(1)
        zone = QScrollArea()
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.NoFrame)
        zone.setWidget(contenu)
        page.addWidget(zone, 1)

        pied = QFrame()
        pied.setObjectName("card")
        pied_layout = QHBoxLayout(pied)
        pied_layout.setContentsMargins(16, 12, 16, 12)
        texte = QLabel("<b>Si rien ne convient</b> : cherchez une version en ligne chez l'éditeur, essayez la "
                       "compatibilité Windows (résultat non garanti), faites tourner Windows lui-même dans une "
                       "machine virtuelle, ou demandez à votre administrateur de garder un accès Windows pour "
                       "ce logiciel.")
        texte.setWordWrap(True)
        bottles = QPushButton("Essayer avec Bottles")
        bottles.setObjectName("primary")
        bottles.setCursor(Qt.PointingHandCursor)
        bottles.clicked.connect(lambda: launch.open_discover(BOTTLES))
        windows = QPushButton("Windows complet")
        windows.setObjectName("primary")
        windows.setCursor(Qt.PointingHandCursor)
        windows.clicked.connect(lambda: self.centre.show_page("windows") if self.centre else None)
        pied_layout.addWidget(texte, 1)
        pied_layout.addWidget(bottles)
        pied_layout.addWidget(windows)
        page.addWidget(pied)

        self.afficher("")

    def ouvrir_fichier(self, chemin):
        """Appelé quand on ouvre un .exe ou un .msi : explique, puis cherche d'après le nom du fichier."""
        nom = os.path.basename(chemin)
        self.bandeau.setText(f"Vous avez ouvert <b>{_echapper(nom)}</b>. Les programmes Windows (.exe, .msi) ne "
                             "s'exécutent pas directement sous NicOS : voici ce qui s'en approche.")
        self.bandeau.setVisible(True)
        requete, _ = catalogue.chercher_fichier(self.entrees, chemin)
        self.recherche.setText(requete)

    def afficher(self, texte):
        while self.liste.count():
            element = self.liste.takeAt(0)
            widget = element.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        if self.erreur:
            self.liste.addWidget(QLabel(f"Le catalogue n'a pas pu être lu : {self.erreur}"))
            return
        resultats = catalogue.chercher(self.entrees, texte)
        if not resultats:
            vide = QLabel("Aucun logiciel de ce nom dans le catalogue. Essayez un autre mot "
                          "(« tableur », « photo », « compta »…), ou voyez « Si rien ne convient » ci-dessous.")
            vide.setWordWrap(True)
            self.liste.addWidget(vide)
            return
        for entree in resultats[:MAX_RESULTATS]:
            self.liste.addWidget(self._ligne(entree))
        if len(resultats) > MAX_RESULTATS:
            self.liste.addWidget(QLabel(f"… et {len(resultats) - MAX_RESULTATS} autres : précisez la recherche."))

    def _etat(self, entree):
        """(texte du badge, libellé du bouton ou None, action)."""
        badge, bouton, action = catalogue.etat(entree, self.installees, self.fournies)
        return badge, bouton, (lambda: launch.executer(action)) if action else None

    def _ligne(self, entree):
        badge, bouton, action = self._etat(entree)
        carte = QFrame()
        carte.setObjectName("card")
        ligne = QHBoxLayout(carte)
        ligne.setContentsMargins(16, 12, 16, 12)
        texte = QVBoxLayout()
        texte.setSpacing(2)
        haut = QLabel(f"{entree.windows}  →")
        haut.setStyleSheet("font-size: 9pt;")
        haut.setEnabled(False)
        nom = QLabel(f"{entree.remplacant}   <span style='font-weight:400; font-size:9pt;'>· {badge}</span>")
        nom.setObjectName("cardTitle")
        texte.addWidget(haut)
        texte.addWidget(nom)
        if entree.remarque:
            remarque = QLabel(entree.remarque)
            remarque.setWordWrap(True)
            texte.addWidget(remarque)
        ligne.addLayout(texte, 1)
        if bouton:
            action_bouton = QPushButton(bouton)
            action_bouton.setObjectName("primary")
            action_bouton.setCursor(Qt.PointingHandCursor)
            action_bouton.clicked.connect(action)
            ligne.addWidget(action_bouton, 0, Qt.AlignVCenter)
        return carte


def _echapper(texte):
    return texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(centre):
    return Page(centre)
