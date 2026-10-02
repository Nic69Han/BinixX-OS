"""Paramètres : tous les réglages du PC au même endroit, classés et nommés comme dans Windows 11."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from .. import launch, parametres, widgets

ORDER = 11
KEY = "parametres"
TITLE = "Paramètres"

LIBELLES = {"kcm": "Ouvrir", "page": "Ouvrir", "app": "Ouvrir", "flatpak": "Ouvrir", "discover": "Ouvrir"}


def modules_installes():
    """Identifiants des modules de la Configuration du système présents sur ce PC (None : on ne sait pas)."""
    code, sortie = launch.run(["kcmshell6", "--list"], timeout=10)
    return parametres.modules_disponibles(sortie) if code == 0 else None


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.erreur = ""
        try:
            tous = parametres.charger()
        except (OSError, ValueError) as erreur:
            tous = []
            self.erreur = str(erreur)
        self.reglages = parametres.visibles(tous, modules_installes())
        self.installees = launch.installed_flatpaks()
        self.cartes = []

        racine = QVBoxLayout(self)
        racine.setContentsMargins(32, 28, 32, 20)
        racine.setSpacing(10)
        titre = QLabel("Paramètres")
        titre.setObjectName("pageTitle")
        racine.addWidget(titre)
        self.recherche = QLineEdit()
        self.recherche.setPlaceholderText("Rechercher un paramètre : Bluetooth, imprimante, fond d'écran, mot de passe…")
        self.recherche.setClearButtonEnabled(True)
        self.recherche.setMinimumHeight(34)
        self.recherche.textChanged.connect(self.afficher)
        racine.addWidget(self.recherche)

        corps = QHBoxLayout()
        corps.setSpacing(18)
        self.liste = QListWidget()
        self.liste.setFixedWidth(230)
        self.liste.setFrameShape(QFrame.NoFrame)
        self.liste.setStyleSheet("QListWidget::item { padding: 9px 8px; }")
        for categorie in parametres.categories(self.reglages):
            self.liste.addItem(categorie)
        self.liste.currentRowChanged.connect(lambda _=0: self.afficher())
        corps.addWidget(self.liste)

        self.contenu = QWidget()
        self.colonne = QVBoxLayout(self.contenu)
        self.colonne.setContentsMargins(0, 0, 8, 0)
        self.colonne.setSpacing(8)
        zone = QScrollArea()
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.NoFrame)
        zone.setWidget(self.contenu)
        corps.addWidget(zone, 1)
        racine.addLayout(corps, 1)

        bas = QHBoxLayout()
        avance = QPushButton("Tous les réglages avancés (Configuration du système)")
        avance.setCursor(Qt.PointingHandCursor)
        avance.clicked.connect(lambda _=False: launch.open_settings())
        bas.addWidget(avance)
        bas.addStretch(1)
        racine.addLayout(bas)

        if self.liste.count():
            self.liste.setCurrentRow(0)
        else:
            self.afficher()

    # --- l'affichage ------------------------------------------------------------------------------------------------

    def categorie_courante(self):
        element = self.liste.currentItem()
        return element.text() if element else ""

    def afficher(self, _=None):
        requete = self.recherche.text().strip()
        if requete:
            self.liste.blockSignals(True)
            self.liste.clearSelection()
            self.liste.setCurrentRow(-1)
            self.liste.blockSignals(False)
            trouves = parametres.chercher(self.reglages, requete)
            self._remplir(trouves, "Aucun paramètre ne correspond à « " + requete + " ». Essayez un autre mot, ou "
                          "ouvrez les réglages avancés." if not trouves else "", avec_categorie=True)
            return
        categorie = self.categorie_courante()
        if not categorie and self.liste.count():
            self.liste.blockSignals(True)
            self.liste.setCurrentRow(0)
            self.liste.blockSignals(False)
            categorie = self.categorie_courante()
        self._remplir(parametres.de_la_categorie(self.reglages, categorie),
                      self.erreur and f"Les paramètres n'ont pas pu être lus : {self.erreur}" or "")

    def _remplir(self, reglages, message, avec_categorie=False):
        while self.colonne.count():
            element = self.colonne.takeAt(0).widget()
            if element is not None:
                element.hide()
                element.deleteLater()
        self.cartes = []
        if message:
            vide = QLabel(message)
            vide.setWordWrap(True)
            self.colonne.addWidget(vide)
        for reglage in reglages:
            bouton, action = self._action(reglage)
            carte = widgets.carte(reglage.nom, reglage.explication, bouton, action,
                                  details=reglage.categorie if avec_categorie else None)
            carte.reglage = reglage
            self.cartes.append(carte)
            self.colonne.addWidget(carte)
        self.colonne.addStretch(1)

    # --- ce qu'un clic déclenche ------------------------------------------------------------------------------------

    def _action(self, reglage):
        """(libellé du bouton, fonction) ; (None, None) quand l'explication suffit."""
        if reglage.type == "info":
            return None, None
        if reglage.type == "flatpak" and reglage.cible not in self.installees:
            return "Installer", lambda _=False, c=reglage.cible: launch.open_discover(c)
        return LIBELLES.get(reglage.type, "Ouvrir"), lambda _=False, r=reglage: self.ouvrir(r)

    def ouvrir(self, reglage):
        if reglage.type == "kcm":
            return launch.open_settings(reglage.cible)
        if reglage.type == "page":
            return self.centre.show_page(reglage.cible)
        if reglage.type == "app":
            return launch.open_app(reglage.cible)
        if reglage.type == "flatpak":
            return launch.run_flatpak(reglage.cible)
        if reglage.type == "discover":
            return launch.open_discover_mode(reglage.cible)
        return None


def build(centre):
    return Page(centre)
