"""Barre des tâches : en bas (comme Windows) ou en haut de l'écran, en un clic. Page ouverte depuis Paramètres."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from .. import barre, theme, widgets

ORDER = 12
KEY = "barre"
TITLE = "Barre des tâches"
ICONE = "taskbar"
ACCENT = theme.ACCENTS["bleu-fonce"]
MENU = False          # pas de bouton dans la barre latérale : on l'ouvre depuis Paramètres
PARENT = "parametres"

CHOIX = (
    ("bas", "En bas, comme sous Windows", "Le menu Démarrer en bas à gauche, l'heure en bas à droite : la disposition "
                                          "que vous connaissez."),
    ("haut", "En haut, comme au départ", "La disposition d'origine de BinixX OS : la barre au bord supérieur, "
                                         "le bas de l'écran reste libre pour vos fenêtres."),
)


class Apercu(QWidget):
    """Une petite maquette d'écran qui montre où serait la barre ; cerclée de la couleur de la page si c'est le choix actuel."""

    def __init__(self, position, parent=None):
        super().__init__(parent)
        self.position = position
        self.actif = False
        self.setFixedSize(QSize(200, 118))

    def paintEvent(self, evenement):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        ecran = QRectF(2, 2, self.width() - 4, self.height() - 4)
        fond = QLinearGradient(ecran.topLeft(), ecran.bottomRight())
        fond.setColorAt(0, QColor("#10163A"))
        fond.setColorAt(1, QColor("#2F5BFF"))
        chemin = QPainterPath()
        chemin.addRoundedRect(ecran, 10, 10)
        p.fillPath(chemin, QBrush(fond))
        # une fenêtre ouverte, pour que la maquette ressemble à un bureau
        fenetre = QRectF(ecran.left() + 40, ecran.top() + 30, ecran.width() - 80, ecran.height() - 60)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 215))
        p.drawRoundedRect(fenetre, 5, 5)
        # la barre, flottante comme celle de BinixX OS
        barre_h = 16
        haut = ecran.top() + 7 if self.position == "haut" else ecran.bottom() - 7 - barre_h
        cadre = QRectF(ecran.left() + 12, haut, ecran.width() - 24, barre_h)
        p.setBrush(QColor(255, 255, 255, 235))
        p.drawRoundedRect(cadre, 6, 6)
        p.setBrush(QColor(ACCENT[0]))
        p.drawRoundedRect(QRectF(cadre.left() + 5, cadre.top() + 4, 8, 8), 2.5, 2.5)
        p.setBrush(QColor("#9AA3B8"))
        for numero in range(3):
            p.drawRoundedRect(QRectF(cadre.left() + 20 + numero * 12, cadre.top() + 5, 7, 6), 2, 2)
        p.drawRoundedRect(QRectF(cadre.right() - 26, cadre.top() + 6, 20, 4), 2, 2)
        stylo = QPen(QColor(ACCENT[0]) if self.actif else QColor(128, 128, 128, 90), 3 if self.actif else 1)
        p.setPen(stylo)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(ecran, 10, 10)


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.actuelle = None
        self.cartes = {}
        contenu, page = widgets.page_de_cartes()

        retour = QPushButton("← Retour aux Paramètres")
        retour.setObjectName("secondaire")
        retour.setCursor(Qt.PointingHandCursor)
        retour.clicked.connect(lambda: centre.show_page("parametres"))
        page.addWidget(retour, 0, Qt.AlignLeft)
        page.addWidget(widgets.entete(
            "Barre des tâches", "Choisissez où se trouve la barre : le changement est immédiat et se garde d'une "
                                "ouverture de session à l'autre.", ICONE, ACCENT))

        page.addWidget(widgets.section("Où placer la barre ?", ACCENT))
        self.etat = QLabel("")
        self.etat.setWordWrap(True)
        self.etat.setObjectName("etatBarre")
        page.addWidget(self.etat)
        for position, titre, texte in CHOIX:
            apercu = Apercu(position)
            corps = QWidget()
            colonne = QVBoxLayout(corps)
            colonne.setContentsMargins(0, 0, 0, 0)
            colonne.setSpacing(8)
            description = QLabel(texte)
            description.setWordWrap(True)
            colonne.addWidget(description)
            colonne.addWidget(apercu, 0, Qt.AlignLeft)
            carte = widgets.carte(titre, "", "Choisir", lambda _=False, c=position: self.choisir(c),
                                  icone=ICONE, couleurs=ACCENT, corps=corps)
            carte.apercu = apercu
            self.cartes[position] = carte
            page.addWidget(carte)

        page.addWidget(widgets.section("Aller plus loin", ACCENT))
        page.addWidget(widgets.carte(
            "Taille, applications épinglées, largeur",
            "Clic droit sur une partie vide de la barre, puis « Modifier le mode d'édition ». Pour épingler une "
            "application : clic droit sur son icône, puis « Épingler à la barre des tâches ».",
            icone="sliders", couleurs=theme.ACCENTS["indigo"]))
        page.addStretch(1)
        widgets.remplir(self, contenu)
        self.actualiser()

    def showEvent(self, evenement):
        super().showEvent(evenement)
        self.actuelle = barre.position_actuelle()
        self.actualiser()

    def choisir(self, position):
        reussi, message = barre.deplacer(position)
        if reussi:
            self.actuelle = position
        self.actualiser(message)

    def actualiser(self, message=None):
        if message is None:
            if self.actuelle:
                message = f"La barre est actuellement {barre.NOMS[self.actuelle]}."
            else:
                message = ("La position de la barre n'a pas pu être lue : ouvrez le Centre depuis une session du "
                           "bureau pour la changer.")
        self.etat.setText(message)
        for position, carte in self.cartes.items():
            actif = position == self.actuelle
            carte.apercu.actif = actif
            carte.apercu.update()
            carte.bouton.setText("Position actuelle" if actif else "Choisir")
            carte.bouton.setEnabled(not actif)


def build(centre):
    return Page(centre)
