"""Éléments d'interface partagés par les pages du Centre BinixX OS : en-tête en dégradé, cartes, pastilles d'icônes.

Chaque page a sa couleur (un couple clair/foncé de theme.ACCENTS) : elle teinte l'en-tête, les titres de section et
les pastilles de ses cartes, pour qu'on sache d'un coup d'œil où l'on est.
"""

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPalette, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
                               QSizePolicy, QVBoxLayout, QWidget)

from . import icones, theme

try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:  # sans QtSvg, les pastilles gardent leur couleur mais pas leur pictogramme
    QSvgRenderer = None

_CACHE = {}


def _rendre(peintre, icone, cadre, couleur="#FFFFFF"):
    if QSvgRenderer is not None and icone in icones.ICONES:
        rendu = QSvgRenderer(QByteArray(icones.svg(icone, couleur).encode("utf-8")))
        rendu.render(peintre, cadre)


def _image(largeur, hauteur=None):
    """Une image transparente, deux fois plus fine que l'écran pour rester nette en haute densité."""
    hauteur = hauteur or largeur
    image = QPixmap(largeur * 2, hauteur * 2)
    image.fill(Qt.transparent)
    image.setDevicePixelRatio(2)
    return image


def pastille(icone, couleurs, taille, marge_droite=0):
    """Un carré arrondi en dégradé avec le pictogramme en blanc ; `marge_droite` ajoute de la place transparente."""
    cle = ("pastille", icone, couleurs, taille, marge_droite)
    if cle not in _CACHE:
        image = _image(taille + marge_droite, taille)
        peintre = QPainter(image)
        peintre.setRenderHint(QPainter.Antialiasing)
        degrade = QLinearGradient(0, 0, taille, taille)
        degrade.setColorAt(0, QColor(couleurs[0]))
        degrade.setColorAt(1, QColor(couleurs[1]))
        peintre.setBrush(QBrush(degrade))
        peintre.setPen(Qt.NoPen)
        peintre.drawRoundedRect(QRectF(0, 0, taille, taille), taille * 0.30, taille * 0.30)
        marge = taille * 0.25
        _rendre(peintre, icone, QRectF(marge, marge, taille - 2 * marge, taille - 2 * marge))
        peintre.end()
        _CACHE[cle] = image
    return _CACHE[cle]


def verre(icone, taille):
    """Une pastille de « verre » (blanc translucide) pour l'en-tête, qui a déjà son propre dégradé."""
    cle = ("verre", icone, taille)
    if cle not in _CACHE:
        image = _image(taille)
        peintre = QPainter(image)
        peintre.setRenderHint(QPainter.Antialiasing)
        peintre.setBrush(QColor(255, 255, 255, 46))
        peintre.setPen(QColor(255, 255, 255, 70))
        peintre.drawRoundedRect(QRectF(0.5, 0.5, taille - 1, taille - 1), taille * 0.30, taille * 0.30)
        marge = taille * 0.26
        _rendre(peintre, icone, QRectF(marge, marge, taille - 2 * marge, taille - 2 * marge))
        peintre.end()
        _CACHE[cle] = image
    return _CACHE[cle]


def glyphe(icone, couleur, taille):
    """Le pictogramme seul, dans une couleur (loupe de la recherche, flèche des tuiles)."""
    cle = ("glyphe", icone, couleur, taille)
    if cle not in _CACHE:
        image = _image(taille)
        peintre = QPainter(image)
        peintre.setRenderHint(QPainter.Antialiasing)
        _rendre(peintre, icone, QRectF(0, 0, taille, taille), couleur)
        peintre.end()
        _CACHE[cle] = image
    return _CACHE[cle]


def discret(texte, taille="9pt"):
    """Un texte secondaire : plus petit, en gris lisible (celui des textes d'aide du thème), sur plusieurs lignes."""
    etiquette = QLabel(texte)
    etiquette.setStyleSheet(f"font-size: {taille};")
    etiquette.setForegroundRole(QPalette.PlaceholderText)
    etiquette.setWordWrap(True)
    return etiquette


def pastille_label(icone, couleurs, taille):
    etiquette = QLabel()
    etiquette.setPixmap(pastille(icone, couleurs, taille))
    etiquette.setFixedSize(taille, taille)
    etiquette.setAttribute(Qt.WA_TransparentForMouseEvents)
    return etiquette


class Entete(QFrame):
    """L'en-tête d'une page : dégradé à la couleur de la page et facettes translucides (clin d'œil à la gemme du logo).

    `corps` est la colonne de droite : le titre et le texte y sont, on peut y ajouter une barre de recherche."""

    def __init__(self, titre, texte, icone, couleurs):
        super().__init__()
        self.couleurs = couleurs
        self.setObjectName("hero")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        ligne = QHBoxLayout(self)
        ligne.setContentsMargins(26, 22, 26, 22)
        ligne.setSpacing(18)
        if icone:
            picto = QLabel()
            picto.setPixmap(verre(icone, 64))
            picto.setFixedSize(64, 64)
            ligne.addWidget(picto, 0, Qt.AlignTop)
        self.corps = QVBoxLayout()
        self.corps.setSpacing(4)
        self.titre = QLabel(titre)
        self.titre.setObjectName("heroTitre")
        self.titre.setWordWrap(True)
        self.corps.addWidget(self.titre)
        if texte:
            self.texte = QLabel(texte)
            self.texte.setObjectName("heroTexte")
            self.texte.setWordWrap(True)
            self.texte.setTextFormat(Qt.RichText)
            self.corps.addWidget(self.texte)
        ligne.addLayout(self.corps, 1)

    def ajouter(self, widget):
        """Pose un élément (recherche, bouton) sous le texte, à l'intérieur du dégradé."""
        self.corps.addSpacing(10)
        self.corps.addWidget(widget)

    def paintEvent(self, evenement):
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.Antialiasing)
        decoupe = QPainterPath()
        decoupe.addRoundedRect(QRectF(self.rect()), 20, 20)
        peintre.setClipPath(decoupe)
        principale = QColor(self.couleurs[0])
        degrade = QLinearGradient(0, 0, self.width(), self.height())
        degrade.setColorAt(0, principale.darker(280))
        degrade.setColorAt(0.55, principale.darker(135))
        degrade.setColorAt(1, principale)
        peintre.fillRect(self.rect(), QBrush(degrade))
        largeur, hauteur = self.width(), self.height()
        for x, y, cote, opacite in ((0.90, 0.30, 1.05, 30), (0.76, 1.00, 0.75, 20), (1.00, 0.95, 0.55, 26)):
            peintre.save()
            peintre.translate(largeur * x, hauteur * y)
            peintre.rotate(45)
            peintre.setPen(Qt.NoPen)
            peintre.setBrush(QColor(255, 255, 255, opacite))
            c = hauteur * cote
            peintre.drawRoundedRect(QRectF(-c / 2, -c / 2, c, c), c * 0.16, c * 0.16)
            peintre.restore()
        peintre.end()


def entete(titre, texte, icone, couleurs=theme.ACCENTS["bleu"]):
    """L'en-tête d'une page (voir Entete)."""
    return Entete(titre, texte, icone, couleurs)


def recherche(indication, hauteur=46):
    """Une grande barre de recherche arrondie, avec une loupe, faite pour poser dans un en-tête."""
    champ = QLineEdit()
    champ.setObjectName("recherche")
    champ.setPlaceholderText(indication)
    champ.setClearButtonEnabled(True)
    champ.setMinimumHeight(hauteur)
    champ.setMaximumWidth(680)
    champ.addAction(QIcon(glyphe("search", theme.BLUE, 20)), QLineEdit.LeadingPosition)
    return champ


class Section(QLabel):
    """Un titre de section, précédé d'un liseré à la couleur de la page. C'est un QLabel : le texte reste modifiable."""

    def __init__(self, texte, couleurs):
        super().__init__(texte)
        self.setObjectName("sectionTitle")
        self.setContentsMargins(0, 10, 0, 0)
        self.liseret = QColor(couleurs[0])

    def colorer(self, couleurs):
        """Change la couleur du liseré (Paramètres : celle de la catégorie affichée)."""
        self.liseret = QColor(couleurs[0])
        self.update()

    def paintEvent(self, evenement):
        super().paintEvent(evenement)
        zone = self.contentsRect()
        haut = self.fontMetrics().height()
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.Antialiasing)
        peintre.setPen(Qt.NoPen)
        peintre.setBrush(self.liseret)
        peintre.drawRoundedRect(QRectF(0, zone.top() + (zone.height() - haut) / 2 + 1, 4, haut - 2), 2, 2)
        peintre.end()


def section(texte, couleurs=theme.ACCENTS["bleu"]):
    """Un titre de section à la couleur de la page."""
    return Section(texte, couleurs)


def defilante(contenu):
    """`contenu` dans une zone défilante (les pages longues)."""
    zone = QScrollArea()
    zone.setWidgetResizable(True)
    zone.setFrameShape(QFrame.NoFrame)
    zone.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    zone.setWidget(contenu)
    return zone


def remplir(parent, contenu):
    """Fait de `contenu`, dans une zone défilante, tout le contenu du widget `parent` ; renvoie la zone."""
    zone = defilante(contenu)
    racine = QVBoxLayout(parent)
    racine.setContentsMargins(0, 0, 0, 0)
    racine.addWidget(zone)
    return zone


def page_de_cartes(marges=(28, 24, 28, 22)):
    """(contenu, mise en page) : le fond d'une page défilante, aux marges et à l'espacement communs."""
    contenu = QWidget()
    page = QVBoxLayout(contenu)
    page.setContentsMargins(*marges)
    page.setSpacing(12)
    return contenu, page


def carte(titre, texte, bouton=None, action=None, details=None, icone=None, couleurs=theme.ACCENTS["bleu"],
          corps=None, avant=None):
    """Une carte : pastille d'icône, titre, texte, éventuellement une ligne de détail en grisé et un bouton à droite.

    La carte garde son bouton dans l'attribut `bouton` (None s'il n'y en a pas). `corps` remplace le texte par un
    widget quelconque ; `avant` est une ligne en grisé au-dessus du titre."""
    cadre = QFrame()
    cadre.setObjectName("card")
    ligne = QHBoxLayout(cadre)
    ligne.setContentsMargins(16, 14, 18, 14)
    ligne.setSpacing(14)
    if icone:
        ligne.addWidget(pastille_label(icone, couleurs, 44), 0, Qt.AlignTop)
    colonne = QVBoxLayout()
    colonne.setSpacing(3)
    if avant:
        colonne.addWidget(discret(avant))
    haut = QLabel(titre)
    haut.setObjectName("cardTitle")
    haut.setWordWrap(True)
    colonne.addWidget(haut)
    if details:
        colonne.addWidget(discret(details))
    if corps is not None:
        colonne.addWidget(corps)
    elif texte:
        contenu = QLabel(texte)
        contenu.setWordWrap(True)
        colonne.addWidget(contenu)
    ligne.addLayout(colonne, 1)
    cadre.bouton = None
    if bouton:
        cadre.bouton = QPushButton(bouton)
        cadre.bouton.setObjectName("primary")
        cadre.bouton.setCursor(Qt.PointingHandCursor)
        cadre.bouton.clicked.connect(action)
        ligne.addWidget(cadre.bouton, 0, Qt.AlignVCenter)
    return cadre


def carte_haute(titre, texte, bouton, action, icone, couleurs=theme.ACCENTS["bleu"]):
    """Une carte verticale (pastille en haut, bouton en bas), pour les grilles de l'accueil."""
    cadre = QFrame()
    cadre.setObjectName("card")
    colonne = QVBoxLayout(cadre)
    colonne.setContentsMargins(18, 18, 18, 16)
    colonne.setSpacing(6)
    colonne.addWidget(pastille_label(icone, couleurs, 48), 0, Qt.AlignLeft)
    colonne.addSpacing(6)
    haut = QLabel(titre)
    haut.setObjectName("cardTitle")
    haut.setWordWrap(True)
    corps = QLabel(texte)
    corps.setWordWrap(True)
    corps.setForegroundRole(QPalette.PlaceholderText)
    colonne.addWidget(haut)
    colonne.addWidget(corps, 1)
    colonne.addSpacing(6)
    cadre.bouton = QPushButton(bouton)
    cadre.bouton.setObjectName("primary")
    cadre.bouton.setCursor(Qt.PointingHandCursor)
    cadre.bouton.clicked.connect(action)
    colonne.addWidget(cadre.bouton, 0, Qt.AlignLeft)
    return cadre


class Grille(QWidget):
    """Des cartes rangées sur autant de colonnes que la largeur le permet (trois au plus par défaut).

    Sans cela, trois cartes côte à côte débordent d'une fenêtre étroite. `largeur_min` est la largeur minimale d'une
    carte (celle de son bouton le plus long, marges comprises)."""

    def __init__(self, elements, colonnes=3, largeur_min=250, espace=14):
        super().__init__()
        self.elements = list(elements)
        self.maximum = colonnes
        self.largeur_min = largeur_min
        self.espace = espace
        self.colonnes = 0
        self.grille = QGridLayout(self)
        self.grille.setContentsMargins(0, 0, 0, 0)
        self.grille.setSpacing(espace)
        self._ranger(colonnes)

    def minimumSizeHint(self):
        # la largeur minimale est celle d'une seule colonne : sinon la zone défilante resterait aussi large que
        # trois colonnes et déborderait
        return QSize(self.largeur_min, super().minimumSizeHint().height())

    def _ranger(self, colonnes):
        self.colonnes = colonnes
        while self.grille.count():
            self.grille.takeAt(0)
        for numero, element in enumerate(self.elements):
            self.grille.addWidget(element, numero // colonnes, numero % colonnes)
        for colonne in range(self.maximum):
            self.grille.setColumnStretch(colonne, 1 if colonne < colonnes else 0)

    def resizeEvent(self, evenement):
        super().resizeEvent(evenement)
        possibles = (self.width() + self.espace) // (self.largeur_min + self.espace)
        colonnes = max(1, min(self.maximum, possibles))
        if colonnes != self.colonnes:
            self._ranger(colonnes)
