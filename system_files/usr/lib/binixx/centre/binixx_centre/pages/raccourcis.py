"""Aide-mémoire des raccourcis : les combinaisons de Windows que l'on a dans les doigts et qui marchent ici.

Page ouverte depuis Paramètres (« Raccourcis clavier »). La liste vient de usr/share/binixx/raccourcis/raccourcis.tsv,
dont chaque touche est vérifiée dans une vraie session par le test VM."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPalette, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .. import launch, raccourcis, theme, widgets

ORDER = 13
KEY = "raccourcis"
TITLE = "Raccourcis"
ICONE = "command"
ACCENT = theme.ACCENTS["ambre"]
MENU = False          # pas de bouton dans la barre latérale : on l'ouvre depuis Paramètres
PARENT = "parametres"

LARGEUR_TOUCHES = 230


class Touches(QWidget):
    """Les touches d'un raccourci dessinées comme des touches de clavier, séparées par « + »."""

    HAUTEUR = 34
    ECART = 14

    def __init__(self, libelles):
        super().__init__()
        self.libelles = list(libelles)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _largeurs(self):
        police = self.font()
        police.setBold(True)
        mesure = QFontMetrics(police)
        return [max(32, mesure.horizontalAdvance(texte) + 22) for texte in self.libelles], police

    def sizeHint(self):
        largeurs, _ = self._largeurs()
        return QSize(sum(largeurs) + self.ECART * (len(largeurs) - 1) + 2, self.HAUTEUR + 3)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, evenement):
        largeurs, police = self._largeurs()
        palette = self.palette()
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.Antialiasing)
        x = 1.0
        for numero, (texte, largeur) in enumerate(zip(self.libelles, largeurs)):
            if numero:
                peintre.setPen(palette.color(QPalette.PlaceholderText))
                peintre.setFont(self.font())
                peintre.drawText(QRectF(x, 0, self.ECART, self.HAUTEUR), Qt.AlignCenter, "+")
                x += self.ECART
            # une touche : un fond clair, un trait plus épais dessous pour lui donner du relief
            relief = QColor(128, 128, 128, 120)
            peintre.setPen(Qt.NoPen)
            peintre.setBrush(relief)
            peintre.drawRoundedRect(QRectF(x, 2, largeur, self.HAUTEUR), 8, 8)
            peintre.setBrush(palette.color(QPalette.Base))
            peintre.setPen(QPen(relief, 1))
            peintre.drawRoundedRect(QRectF(x + 0.5, 0.5, largeur - 1, self.HAUTEUR - 1), 8, 8)
            peintre.setFont(police)
            peintre.setPen(palette.color(QPalette.Text))
            peintre.drawText(QRectF(x, 0, largeur, self.HAUTEUR), Qt.AlignCenter, texte)
            x += largeur
        peintre.end()


def ligne(element):
    """Une ligne de l'aide-mémoire : les touches à gauche, ce qu'elles font à droite."""
    cadre = QFrame()
    cadre.setObjectName("card")
    corps = QHBoxLayout(cadre)
    corps.setContentsMargins(16, 10, 18, 10)
    corps.setSpacing(16)
    zone = QWidget()
    zone.setFixedWidth(LARGEUR_TOUCHES)
    dans_zone = QHBoxLayout(zone)
    dans_zone.setContentsMargins(0, 0, 0, 0)
    cadre.touches = Touches(raccourcis.affichage(element.touches))
    dans_zone.addWidget(cadre.touches, 0, Qt.AlignLeft | Qt.AlignVCenter)
    dans_zone.addStretch(1)
    corps.addWidget(zone)
    colonne = QVBoxLayout()
    colonne.setSpacing(2)
    action = QLabel(element.action)
    action.setObjectName("cardTitle")
    action.setWordWrap(True)
    colonne.addWidget(action)
    if element.precision:
        colonne.addWidget(widgets.discret(element.precision))
    corps.addLayout(colonne, 1)
    cadre.element = element
    return cadre


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        try:
            self.elements = raccourcis.charger()
        except (OSError, ValueError):
            self.elements = []
        self.lignes = []
        self.sections = {}
        contenu, page = widgets.page_de_cartes()

        retour = QPushButton("← Retour aux Paramètres")
        retour.setObjectName("secondaire")
        retour.setCursor(Qt.PointingHandCursor)
        retour.clicked.connect(lambda: centre.show_page("parametres"))
        page.addWidget(retour, 0, Qt.AlignLeft)

        tete = widgets.entete(
            "Raccourcis clavier",
            "Les combinaisons de Windows que vous avez dans les doigts marchent aussi ici. La touche Windows est celle "
            "du menu Démarrer.", ICONE, ACCENT)
        self.recherche = widgets.recherche("Chercher un raccourci : « fichiers », « capture », « verrouiller »…")
        self.recherche.textChanged.connect(self.filtrer)
        tete.ajouter(self.recherche)
        page.addWidget(tete)

        for categorie in raccourcis.categories(self.elements):
            titre = widgets.section(categorie, ACCENT)
            self.sections[categorie] = titre
            page.addWidget(titre)
            for element in (e for e in self.elements if e.categorie == categorie):
                rangee = ligne(element)
                self.lignes.append(rangee)
                page.addWidget(rangee)

        self.vide = QLabel("Aucun raccourci ne correspond. Essayez un autre mot.")
        self.vide.setAlignment(Qt.AlignCenter)
        self.vide.setContentsMargins(0, 20, 0, 20)
        self.vide.hide()
        page.addWidget(self.vide)

        self.pied = QWidget()
        pied = QVBoxLayout(self.pied)
        pied.setContentsMargins(0, 0, 0, 0)
        pied.setSpacing(12)
        pied.addWidget(widgets.section("Les mêmes qu'ailleurs", ACCENT))
        pied.addWidget(widgets.carte(
            "Copier, couper, coller, annuler",
            "Ctrl + C, Ctrl + X, Ctrl + V et Ctrl + Z marchent dans toutes les applications, comme Ctrl + F pour "
            "chercher, Ctrl + S pour enregistrer et Ctrl + A pour tout sélectionner.", icone="edit", couleurs=ACCENT))
        self.personnaliser = widgets.carte(
            "Changer ou ajouter un raccourci",
            "Dans la Configuration du système, on peut modifier chaque raccourci ou en créer de nouveaux.",
            "Personnaliser", lambda: launch.open_settings("kcm_keys"), icone="keyboard", couleurs=ACCENT)
        pied.addWidget(self.personnaliser)
        page.addWidget(self.pied)
        page.addStretch(1)
        widgets.remplir(self, contenu)

    def filtrer(self, texte=""):
        """N'affiche que les raccourcis qui répondent à la recherche (tous, si elle est vide)."""
        gardes = set(raccourcis.chercher(self.elements, texte))
        presentes = set()
        for rangee in self.lignes:
            visible = rangee.element in gardes
            rangee.setVisible(visible)
            if visible:
                presentes.add(rangee.element.categorie)
        for categorie, titre in self.sections.items():
            titre.setVisible(categorie in presentes)
        self.vide.setVisible(bool(self.elements) and not presentes)
        self.pied.setVisible(not texte.strip())


def build(centre):
    return Page(centre)
