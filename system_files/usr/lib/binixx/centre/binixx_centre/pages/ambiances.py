"""Ambiances : Aube, Nuit, Contraste élevé en un clic, et l'interrupteur « Grand texte ». Page ouverte depuis Paramètres.

La logique (outils de Plasma, vérification dans kdeglobals) est dans ambiances.py ; ici, seulement l'écran."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from .. import ambiances, theme, widgets

ORDER = 17
KEY = "ambiances"
TITLE = "Ambiances"
ICONE = "sun"
ACCENT = theme.ACCENTS["ardoise"]
MENU = False          # pas de bouton dans la barre latérale : on l'ouvre depuis Paramètres
PARENT = "parametres"

ICONES = {"aube": "sun", "nuit": "moon", "contraste": "eye"}


class Apercu(QWidget):
    """Une petite maquette de bureau aux couleurs de l'ambiance ; cerclée de la couleur de la page si elle est en place."""

    def __init__(self, ambiance, parent=None):
        super().__init__(parent)
        self.ambiance = ambiance
        self.actif = False
        self.setFixedSize(QSize(200, 118))

    def paintEvent(self, evenement):
        fond, texte, accent, barre = (QColor(c) for c in self.ambiance.apercu)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        ecran = QRectF(2, 2, self.width() - 4, self.height() - 4)
        chemin = QPainterPath()
        chemin.addRoundedRect(ecran, 10, 10)
        p.fillPath(chemin, fond.darker(135) if fond.lightness() > 128 else fond.lighter(150))
        fenetre = QRectF(ecran.left() + 22, ecran.top() + 16, ecran.width() - 44, ecran.height() - 32)
        p.setPen(QPen(texte, 1))
        p.setBrush(fond)
        p.drawRoundedRect(fenetre, 5, 5)
        # barre de titre
        p.setPen(Qt.NoPen)
        p.setBrush(barre)
        titre = QRectF(fenetre.left() + 1, fenetre.top() + 1, fenetre.width() - 2, 14)
        p.drawRoundedRect(titre, 4, 4)
        p.setBrush(QColor(0, 0, 0) if barre.lightness() > 128 else texte)
        p.drawRoundedRect(QRectF(titre.left() + 8, titre.top() + 5, 34, 4), 2, 2)
        # du texte, une ligne sélectionnée, un bouton
        p.setBrush(texte)
        for numero, largeur in enumerate((84, 62)):
            p.drawRoundedRect(QRectF(fenetre.left() + 10, fenetre.top() + 24 + numero * 11, largeur, 4), 2, 2)
        p.setBrush(accent)
        p.drawRoundedRect(QRectF(fenetre.left() + 10, fenetre.top() + 46, 96, 9), 3, 3)
        p.setBrush(QColor(0, 0, 0) if accent.lightness() > 128 else QColor(255, 255, 255))
        p.drawRoundedRect(QRectF(fenetre.left() + 14, fenetre.top() + 49, 48, 3), 1.5, 1.5)
        p.setBrush(accent)
        p.drawRoundedRect(QRectF(fenetre.right() - 40, fenetre.bottom() - 17, 30, 10), 4, 4)
        contour = QPen(QColor(ACCENT[0]) if self.actif else QColor(128, 128, 128, 90), 3 if self.actif else 1)
        p.setPen(contour)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(ecran, 10, 10)


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.cartes = {}
        contenu, page = widgets.page_de_cartes()

        retour = QPushButton("← Retour aux Paramètres")
        retour.setObjectName("secondaire")
        retour.setCursor(Qt.PointingHandCursor)
        retour.clicked.connect(lambda: centre.show_page("parametres"))
        page.addWidget(retour, 0, Qt.AlignLeft)
        page.addWidget(widgets.entete(
            "Ambiances", "Changez l'allure de tout le bureau en un clic : couleurs, icônes, fenêtres et fond d'écran. "
                         "Un autre clic suffit pour changer d'avis.", ICONE, ACCENT))

        page.addWidget(widgets.section("Choisir une allure", ACCENT))
        self.etat = QLabel("")
        self.etat.setWordWrap(True)
        self.etat.setObjectName("etatAmbiance")
        page.addWidget(self.etat)
        for ambiance in ambiances.AMBIANCES:
            apercu = Apercu(ambiance)
            corps = QWidget()
            colonne = QVBoxLayout(corps)
            colonne.setContentsMargins(0, 0, 0, 0)
            colonne.setSpacing(8)
            description = QLabel(ambiance.texte)
            description.setWordWrap(True)
            colonne.addWidget(description)
            colonne.addWidget(apercu, 0, Qt.AlignLeft)
            carte = widgets.carte(ambiance.titre, "", "Choisir", lambda _=False, c=ambiance.cle: self.choisir(c),
                                  icone=ICONES[ambiance.cle], couleurs=ACCENT, corps=corps)
            carte.apercu = apercu
            self.cartes[ambiance.cle] = carte
            page.addWidget(carte)
        page.addWidget(widgets.discret(
            "Le fond d'écran suit : clair avec Aube, sombre avec Nuit et Contraste élevé."))

        page.addWidget(widgets.section("Plus grand", ACCENT))
        self.grand = widgets.carte(
            "Grand texte", "Le texte du bureau et des applications à 130 % et un pointeur de souris plus gros. Se combine "
                           "avec n'importe quelle allure ; pour une autre taille de texte, voir « Taille du texte ».",
            "Activer", self.basculer_grand_texte, icone="type", couleurs=ACCENT)
        page.addWidget(self.grand)

        page.addWidget(widgets.section("Aller plus loin", ACCENT))
        page.addWidget(widgets.carte(
            "Couleurs, icônes et pointeur", "Choisir un schéma de couleurs, une couleur d'accentuation, un autre thème "
                                            "d'icônes ou de pointeur.", "Ouvrir", lambda: self.ouvrir("kcm_colors"),
            icone="sliders", couleurs=theme.ACCENTS["indigo"]))
        page.addStretch(1)
        widgets.remplir(self, contenu)
        self.actualiser()

    def ouvrir(self, module):
        from .. import launch
        launch.open_settings(module)

    def occupe(self, message):
        """Un instant : message affiché et boutons grisés pendant que Plasma change le bureau."""
        self.etat.setText(message)
        for carte in list(self.cartes.values()) + [self.grand]:
            carte.bouton.setEnabled(False)
        QApplication.processEvents()

    def actualiser(self, message=None):
        courante = ambiances.ambiance_actuelle()
        for cle, carte in self.cartes.items():
            actif = courante is not None and courante.cle == cle
            carte.bouton.setText("En place" if actif else "Choisir")
            carte.bouton.setEnabled(not actif)
            carte.apercu.actif = actif
            carte.apercu.update()
        grand = ambiances.grand_texte_actif()
        self.grand.bouton.setText("Désactiver" if grand else "Activer")
        self.grand.bouton.setEnabled(True)
        if message is None:
            message = (f"Ambiance en place : {courante.titre}." if courante is not None
                       else "Le bureau utilise des couleurs personnalisées : choisissez une ambiance pour les remplacer.")
            if grand:
                message += " « Grand texte » est activé."
        self.etat.setText(message)

    def choisir(self, cle):
        self.occupe("Un instant, l'ambiance se met en place…")
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            _, message = ambiances.appliquer(cle)
        finally:
            QGuiApplication.restoreOverrideCursor()
        self.actualiser(message)

    def basculer_grand_texte(self):
        activer = not ambiances.grand_texte_actif()
        self.occupe("Un instant…")
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            action = ambiances.activer_grand_texte if activer else ambiances.desactiver_grand_texte
            _, message = action()
        finally:
            QGuiApplication.restoreOverrideCursor()
        self.actualiser(message)


def build(centre):
    return Page(centre)
