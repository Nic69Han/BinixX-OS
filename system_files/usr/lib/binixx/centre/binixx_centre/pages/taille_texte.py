"""Taille du texte : un curseur de 100 % à 200 %, un aperçu, « Appliquer » et « Rétablir ». Page ouverte depuis Paramètres.

La logique (polices de KDE, gardées pour pouvoir tout remettre) est dans taille_texte.py ; ici, seulement l'écran."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from .. import taille_texte, theme, widgets

ORDER = 16
KEY = "taille_texte"
TITLE = "Taille du texte"
ICONE = "type"
ACCENT = theme.ACCENTS["fuchsia"]
MENU = False          # pas de bouton dans la barre latérale : on l'ouvre depuis Paramètres
PARENT = "parametres"

EXEMPLE = ("Voici à quoi ressemblera le texte du bureau et des applications. Les menus, les fenêtres, les barres d'outils "
           "et les boutons suivent la même taille.")


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.actuel = taille_texte.pourcentage_actuel()
        contenu, page = widgets.page_de_cartes()

        retour = QPushButton("← Retour aux Paramètres")
        retour.setObjectName("secondaire")
        retour.setCursor(Qt.PointingHandCursor)
        retour.clicked.connect(lambda: centre.show_page("parametres"))
        page.addWidget(retour, 0, Qt.AlignLeft)
        page.addWidget(widgets.entete(
            "Taille du texte", "Agrandissez le texte du bureau et des applications d'un seul geste, de 100 % (taille "
                               "d'origine) à 200 %.", ICONE, ACCENT))

        page.addWidget(widgets.section("Choisir la taille", ACCENT))
        carte = QFrame()
        carte.setObjectName("card")
        colonne = QVBoxLayout(carte)
        colonne.setContentsMargins(20, 16, 20, 16)
        colonne.setSpacing(10)
        ligne = QHBoxLayout()
        petit = QLabel("Aa")
        petit.setStyleSheet("font-size: 9pt;")
        grand = QLabel("Aa")
        grand.setStyleSheet("font-size: 20pt;")
        self.curseur = QSlider(Qt.Horizontal)
        self.curseur.setRange(taille_texte.MINIMUM, taille_texte.MAXIMUM)
        self.curseur.setSingleStep(taille_texte.PAS)
        self.curseur.setPageStep(taille_texte.PAS)
        self.curseur.setTickInterval(taille_texte.PAS)
        self.curseur.setTickPosition(QSlider.TicksBelow)
        self.curseur.setValue(self.actuel)
        self.curseur.setMinimumHeight(34)
        self.curseur.valueChanged.connect(self.changer)
        self.valeur = QLabel("")
        self.valeur.setObjectName("cardTitle")
        self.valeur.setMinimumWidth(64)
        self.valeur.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        ligne.addWidget(petit)
        ligne.addWidget(self.curseur, 1)
        ligne.addWidget(grand)
        ligne.addSpacing(8)
        ligne.addWidget(self.valeur)
        colonne.addLayout(ligne)
        self.apercu = QLabel(EXEMPLE)
        self.apercu.setWordWrap(True)
        self.apercu.setMinimumHeight(110)
        self.apercu.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        colonne.addWidget(self.apercu)
        boutons = QHBoxLayout()
        self.appliquer = QPushButton("Appliquer")
        self.appliquer.setObjectName("primary")
        self.appliquer.setCursor(Qt.PointingHandCursor)
        self.appliquer.clicked.connect(self.valider)
        self.retablir = QPushButton("Rétablir la taille d'origine")
        self.retablir.setObjectName("secondaire")
        self.retablir.setCursor(Qt.PointingHandCursor)
        self.retablir.clicked.connect(self.remettre)
        boutons.addWidget(self.appliquer)
        boutons.addWidget(self.retablir)
        boutons.addStretch(1)
        colonne.addLayout(boutons)
        self.etat = QLabel("")
        self.etat.setWordWrap(True)
        colonne.addWidget(self.etat)
        page.addWidget(carte)

        page.addWidget(widgets.section("Bon à savoir", ACCENT))
        page.addWidget(widgets.carte(
            "Les pages web", "Un site garde sa propre mise en page : pour l'agrandir, Ctrl + molette de la souris (ou "
                             "Ctrl et +) dans le navigateur.", icone="globe", couleurs=ACCENT))
        page.addWidget(widgets.carte(
            "Tout le reste de l'affichage", "Pour agrandir aussi les icônes et les fenêtres, utilisez la mise à "
                                            "l'échelle de l'écran (Paramètres → Affichage).", icone="monitor",
            couleurs=ACCENT))
        page.addStretch(1)
        widgets.remplir(self, contenu)
        self.changer(self.actuel)
        self.afficher_l_etat()

    def changer(self, pourcentage):
        """Le curseur a bougé : l'aperçu prend la taille voulue, sans rien changer au bureau."""
        police = QFont(self.apercu.font())
        police.setPointSizeF(taille_texte.apercu(pourcentage) * 1.0)
        self.apercu.setFont(police)
        self.valeur.setText(f"{pourcentage} %")
        self.appliquer.setEnabled(pourcentage != self.actuel)

    def afficher_l_etat(self, message=None):
        if message is None:
            message = (f"Le texte est actuellement à {self.actuel} %." if self.actuel != 100
                       else "Le texte a sa taille d'origine.")
        self.etat.setText(message)
        self.retablir.setEnabled(self.actuel != 100)

    def valider(self):
        reussi, message = taille_texte.appliquer(self.curseur.value())
        if reussi:
            self.actuel = taille_texte.pourcentage_actuel()
            message += " Les applications déjà ouvertes s'adaptent tout de suite ; fermez et rouvrez celles qui ne le font pas."
        self.appliquer.setEnabled(self.curseur.value() != self.actuel)
        self.afficher_l_etat(message)

    def remettre(self):
        reussi, message = taille_texte.retablir()
        if reussi:
            self.actuel = taille_texte.pourcentage_actuel()
            self.curseur.setValue(self.actuel)
        self.afficher_l_etat(message)


def build(centre):
    return Page(centre)
