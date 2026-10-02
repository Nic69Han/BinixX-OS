"""Paramètres : tous les réglages du PC au même endroit, classés et nommés comme dans Windows 11."""

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPalette, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from .. import icones, launch, parametres, theme

try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:  # sans QtSvg, les pastilles gardent leur couleur mais pas leur pictogramme
    QSvgRenderer = None

ORDER = 11
KEY = "parametres"
TITLE = "Paramètres"

# Une couleur (dégradé) et un pictogramme par catégorie : on s'y repère d'un coup d'œil
COULEURS = {
    "Système": ("#2F5BFF", "#5FB2FF"),
    "Bluetooth et appareils": ("#7C3AED", "#A78BFA"),
    "Réseau et Internet": ("#0891B2", "#22D3EE"),
    "Personnalisation": ("#DB2777", "#F472B6"),
    "Applications": ("#EA580C", "#FB923C"),
    "Comptes": ("#059669", "#34D399"),
    "Heure et langue": ("#D97706", "#FBBF24"),
    "Jeux": ("#DC2626", "#F87171"),
    "Accessibilité": ("#4F46E5", "#818CF8"),
    "Confidentialité et sécurité": ("#0F766E", "#2DD4BF"),
    "Mises à jour et récupération": ("#1D4ED8", "#60A5FA"),
}
ICONES_CATEGORIES = {
    "Système": "monitor", "Bluetooth et appareils": "bluetooth", "Réseau et Internet": "wifi",
    "Personnalisation": "droplet", "Applications": "package", "Comptes": "user", "Heure et langue": "globe",
    "Jeux": "gamepad", "Accessibilité": "accessibility", "Confidentialité et sécurité": "shield",
    "Mises à jour et récupération": "refresh",
}
PAR_DEFAUT = ("#2F5BFF", "#5FB2FF")
_CACHE = {}


def modules_installes():
    """Identifiants des modules de la Configuration du système présents sur ce PC (None : on ne sait pas)."""
    code, sortie = launch.run(["kcmshell6", "--list"], timeout=10)
    return parametres.modules_disponibles(sortie) if code == 0 else None


def _rendre(peintre, icone, cadre, couleur="#FFFFFF"):
    if QSvgRenderer is not None and icone in icones.ICONES:
        rendu = QSvgRenderer(QByteArray(icones.svg(icone, couleur).encode("utf-8")))
        rendu.render(peintre, cadre)


def pastille(icone, couleurs, taille):
    """Un carré arrondi en dégradé avec le pictogramme en blanc, net aussi sur un écran haute densité."""
    cle = ("pastille", icone, couleurs, taille)
    if cle not in _CACHE:
        echelle = 2
        image = QPixmap(taille * echelle, taille * echelle)
        image.fill(Qt.transparent)
        image.setDevicePixelRatio(echelle)
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


def glyphe(icone, couleur, taille):
    """Le pictogramme seul, dans une couleur (loupe de la recherche, flèche des tuiles)."""
    cle = ("glyphe", icone, couleur, taille)
    if cle not in _CACHE:
        echelle = 2
        image = QPixmap(taille * echelle, taille * echelle)
        image.fill(Qt.transparent)
        image.setDevicePixelRatio(echelle)
        peintre = QPainter(image)
        peintre.setRenderHint(QPainter.Antialiasing)
        _rendre(peintre, icone, QRectF(0, 0, taille, taille), couleur)
        peintre.end()
        _CACHE[cle] = image
    return _CACHE[cle]


class Tuile(QFrame):
    """Une tuile cliquable (souris, ou Entrée et Espace au clavier) : pictogramme coloré, nom, explication."""

    clicked = Signal()

    def __init__(self, reglage, action=None, etiquette=None, avec_categorie=False):
        super().__init__()
        self.reglage = reglage
        self.action = action
        self.libelle = etiquette
        self.actionnable = action is not None
        couleurs = COULEURS.get(reglage.categorie, PAR_DEFAUT)
        self.setObjectName("tuile")
        self.setMinimumHeight(88)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        if self.actionnable:
            self.setCursor(Qt.PointingHandCursor)
            self.setFocusPolicy(Qt.StrongFocus)
            self.clicked.connect(action)
        else:
            self.setProperty("info", True)  # une explication : cadre en pointillés, rien à ouvrir

        ligne = QHBoxLayout(self)
        ligne.setContentsMargins(16, 14, 16, 14)
        ligne.setSpacing(14)
        icone = QLabel()
        icone.setPixmap(pastille(reglage.icone, couleurs, 46))
        icone.setFixedSize(46, 46)
        ligne.addWidget(icone, 0, Qt.AlignTop)

        colonne = QVBoxLayout()
        colonne.setSpacing(2)
        if avec_categorie:
            categorie = QLabel(reglage.categorie.upper())
            categorie.setObjectName("tuileCategorie")
            categorie.setStyleSheet(f"color: {couleurs[0]};")
            colonne.addWidget(categorie)
        titre = QLabel(reglage.nom)
        titre.setObjectName("tuileTitre")
        titre.setWordWrap(True)
        texte = QLabel(reglage.explication)
        texte.setObjectName("tuileTexte")
        texte.setWordWrap(True)
        texte.setForegroundRole(QPalette.PlaceholderText)
        colonne.addWidget(titre)
        colonne.addWidget(texte)
        colonne.addStretch(1)
        ligne.addLayout(colonne, 1)

        if self.actionnable:
            if etiquette == "Installer":
                badge = QLabel(etiquette)
                badge.setObjectName("etiquette")
                ligne.addWidget(badge, 0, Qt.AlignVCenter)
            else:
                fleche = QLabel()
                fleche.setPixmap(glyphe("chevron", "#8A93B2", 20))
                fleche.setFixedSize(20, 20)
                ligne.addWidget(fleche, 0, Qt.AlignVCenter)
        for enfant in self.findChildren(QLabel):
            enfant.setAttribute(Qt.WA_TransparentForMouseEvents)

    def click(self):
        if self.actionnable:
            self.clicked.emit()

    def _appuye(self, oui):
        self.setProperty("appuye", oui)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, evenement):
        if self.actionnable and evenement.button() == Qt.LeftButton:
            self._appuye(True)
        super().mousePressEvent(evenement)

    def mouseReleaseEvent(self, evenement):
        if self.actionnable and evenement.button() == Qt.LeftButton:
            self._appuye(False)
            if self.rect().contains(evenement.position().toPoint()):
                self.clicked.emit()
        super().mouseReleaseEvent(evenement)

    def keyPressEvent(self, evenement):
        if self.actionnable and evenement.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
            return
        super().keyPressEvent(evenement)


class Entete(QFrame):
    """L'en-tête en dégradé, avec quelques facettes translucides : un clin d'œil à la gemme du logo NicOS."""

    def paintEvent(self, evenement):
        super().paintEvent(evenement)
        peintre = QPainter(self)
        peintre.setRenderHint(QPainter.Antialiasing)
        decoupe = QPainterPath()
        decoupe.addRoundedRect(QRectF(self.rect()), 20, 20)
        peintre.setClipPath(decoupe)
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


class Zone(QScrollArea):
    """Zone défilante qui prévient quand sa largeur change (pour passer de deux colonnes à une)."""

    redimensionnee = Signal()

    def resizeEvent(self, evenement):
        super().resizeEvent(evenement)
        self.redimensionnee.emit()


class Page(QWidget):
    LARGEUR_DEUX_COLONNES = 640

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
        self.tuiles = []
        self.colonnes = 2
        self._message = ""
        self._avec_categorie = False

        racine = QVBoxLayout(self)
        racine.setContentsMargins(28, 24, 28, 18)
        racine.setSpacing(16)

        # En-tête : un dégradé aux couleurs de NicOS et une grande barre de recherche arrondie
        hero = Entete()
        hero.setObjectName("hero")
        cadre = QVBoxLayout(hero)
        cadre.setContentsMargins(30, 24, 30, 26)
        cadre.setSpacing(4)
        titre = QLabel("Paramètres")
        titre.setObjectName("heroTitre")
        sous_titre = QLabel("Tous les réglages de ce PC, classés comme dans Windows.")
        sous_titre.setObjectName("heroTexte")
        cadre.addWidget(titre)
        cadre.addWidget(sous_titre)
        cadre.addSpacing(12)
        self.recherche = QLineEdit()
        self.recherche.setObjectName("recherche")
        self.recherche.setPlaceholderText("Rechercher un paramètre : Bluetooth, imprimante, fond d'écran, mot de passe…")
        self.recherche.setClearButtonEnabled(True)
        self.recherche.setMinimumHeight(46)
        self.recherche.setMaximumWidth(680)
        self.recherche.addAction(QIcon(glyphe("search", theme.BLUE, 20)), QLineEdit.LeadingPosition)
        self.recherche.textChanged.connect(self.afficher)
        cadre.addWidget(self.recherche)
        racine.addWidget(hero)

        corps = QHBoxLayout()
        corps.setSpacing(22)
        self.liste = QListWidget()
        self.liste.setObjectName("categories")
        self.liste.setFixedWidth(256)
        self.liste.setIconSize(QSize(32, 32))
        self.liste.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for categorie in parametres.categories(self.reglages):
            image = pastille(ICONES_CATEGORIES.get(categorie, "sliders"), COULEURS.get(categorie, PAR_DEFAUT), 32)
            icone = QIcon()
            for mode in (QIcon.Normal, QIcon.Active, QIcon.Selected):  # la pastille garde ses couleurs une fois choisie
                icone.addPixmap(image, mode)
            element = QListWidgetItem(icone, categorie)
            element.setSizeHint(QSize(0, 46))
            self.liste.addItem(element)
        self.liste.currentRowChanged.connect(lambda _=0: self.afficher())
        corps.addWidget(self.liste)

        droite = QVBoxLayout()
        droite.setSpacing(8)
        self.entete = QLabel()
        self.entete.setObjectName("sectionTitle")
        self.entete.setStyleSheet("font-size: 16pt;")
        self.compte = QLabel()
        self.compte.setForegroundRole(QPalette.PlaceholderText)
        droite.addWidget(self.entete)
        droite.addWidget(self.compte)
        self.contenu = QWidget()
        self.grille = QGridLayout(self.contenu)
        self.grille.setContentsMargins(0, 8, 8, 8)
        self.grille.setSpacing(12)
        self.zone = Zone()
        self.zone.setWidgetResizable(True)
        self.zone.setFrameShape(QFrame.NoFrame)
        self.zone.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.zone.setWidget(self.contenu)
        self.zone.redimensionnee.connect(self._regrouper)
        droite.addWidget(self.zone, 1)
        corps.addLayout(droite, 1)
        racine.addLayout(corps, 1)

        bas = QHBoxLayout()
        avance = QPushButton("Tous les réglages avancés (Configuration du système)   ›")
        avance.setObjectName("lien")
        avance.setCursor(Qt.PointingHandCursor)
        avance.clicked.connect(lambda _=False: launch.open_settings())
        bas.addStretch(1)
        bas.addWidget(avance)
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
            self.entete.setText("Résultats")
            self.compte.setText(f"{len(trouves)} résultat(s) pour « {requete} »" if trouves else "")
            self._remplir(trouves, "" if trouves else
                          "Aucun paramètre ne correspond à « " + requete + " ». Essayez un autre mot, ou ouvrez les "
                          "réglages avancés en bas de la page.", avec_categorie=True)
            return
        categorie = self.categorie_courante()
        if not categorie and self.liste.count():
            self.liste.blockSignals(True)
            self.liste.setCurrentRow(0)
            self.liste.blockSignals(False)
            categorie = self.categorie_courante()
        du_groupe = parametres.de_la_categorie(self.reglages, categorie)
        self.entete.setText(categorie)
        self.compte.setText(f"{len(du_groupe)} réglage(s)" if du_groupe else "")
        self._remplir(du_groupe, f"Les paramètres n'ont pas pu être lus : {self.erreur}" if self.erreur else "")

    def _remplir(self, reglages, message, avec_categorie=False):
        self._message = message
        self._avec_categorie = avec_categorie
        while self.grille.count():
            element = self.grille.takeAt(0).widget()
            if element is not None:
                element.hide()
                element.deleteLater()
        self.tuiles = []
        for reglage in reglages:
            etiquette, action = self._action(reglage)
            self.tuiles.append(Tuile(reglage, action, etiquette, avec_categorie))
        self._disposer()

    def _disposer(self):
        """Place les tuiles sur une ou deux colonnes selon la largeur disponible."""
        while self.grille.count():
            element = self.grille.takeAt(0)
            if element.widget() is not None and element.widget() not in self.tuiles:
                element.widget().hide()
                element.widget().deleteLater()
        ligne = 0
        if self._message:
            vide = QLabel(self._message)
            vide.setWordWrap(True)
            vide.setForegroundRole(QPalette.PlaceholderText)
            self.grille.addWidget(vide, 0, 0, 1, 2)
            ligne = 1
        for numero, tuile in enumerate(self.tuiles):
            tuile.show()
            self.grille.addWidget(tuile, ligne + numero // self.colonnes, numero % self.colonnes)
        for colonne in range(2):
            self.grille.setColumnStretch(colonne, 1 if colonne < self.colonnes else 0)
        self.grille.setRowStretch(ligne + (len(self.tuiles) + self.colonnes - 1) // self.colonnes, 1)

    def _regrouper(self):
        colonnes = 2 if self.zone.viewport().width() >= self.LARGEUR_DEUX_COLONNES else 1
        if colonnes != self.colonnes:
            self.colonnes = colonnes
            self._disposer()

    # --- ce qu'un clic déclenche ------------------------------------------------------------------------------------

    def _action(self, reglage):
        """(étiquette, fonction) ; (None, None) quand l'explication suffit."""
        if reglage.type == "info":
            return None, None
        if reglage.type == "flatpak" and reglage.cible not in self.installees:
            return "Installer", lambda c=reglage.cible: launch.open_discover(c)
        return "Ouvrir", lambda r=reglage: self.ouvrir(r)

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
