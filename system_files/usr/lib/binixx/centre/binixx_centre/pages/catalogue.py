"""Mon logiciel Windows : l'équivalent sous BinixX OS de ce que l'on utilisait sous Windows."""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import catalogue, launch, theme, widgets

ORDER = 20
KEY = "catalogue"
TITLE = "Mon logiciel Windows"
ICONE = "search"
ACCENT = theme.ACCENTS["orange"]

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
        page.setContentsMargins(28, 24, 28, 18)
        page.setSpacing(12)
        hero = widgets.entete("Mon logiciel Windows",
                              "Tapez le nom du logiciel que vous utilisiez sous Windows (Word, Sage, Photoshop, "
                              "Teams…) : voici ce qui le remplace sous BinixX OS.", ICONE, ACCENT)
        self.recherche = widgets.recherche("Quel logiciel Windows utilisiez-vous ?")
        self.recherche.textChanged.connect(self.afficher)
        hero.ajouter(self.recherche)
        page.addWidget(hero)

        self.bandeau = QLabel()
        self.bandeau.setObjectName("bandeau")
        self.bandeau.setWordWrap(True)
        self.bandeau.setVisible(False)
        page.addWidget(self.bandeau)

        self.liste = QVBoxLayout()
        self.liste.setSpacing(10)
        contenu = QWidget()
        contenu_layout = QVBoxLayout(contenu)
        contenu_layout.setContentsMargins(0, 2, 8, 2)
        contenu_layout.addLayout(self.liste)
        contenu_layout.addStretch(1)
        page.addWidget(widgets.defilante(contenu), 1)

        pied = QFrame()
        pied.setObjectName("card")
        pied_layout = QHBoxLayout(pied)
        pied_layout.setContentsMargins(18, 14, 18, 14)
        pied_layout.setSpacing(12)
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
                             "s'exécutent pas directement sous BinixX OS : voici ce qui s'en approche.")
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
        titre = f"{entree.remplacant}   <span style='font-weight:400; font-size:9pt;'>· {badge}</span>"
        return widgets.carte(titre, entree.remarque, bouton, action, avant=f"{entree.windows}  →",
                             icone=catalogue.icone_de(entree.categorie), couleurs=ACCENT)


def _echapper(texte):
    return texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(centre):
    return Page(centre)
