"""Accueil : les premiers pas d'un utilisateur qui vient de Windows."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from .. import launch

ORDER = 10
KEY = "accueil"
TITLE = "Accueil"

# (titre, description, libellé du bouton, action)
CARTES = [
    ("Me connecter à Internet", "Wi-Fi, câble ou VPN de l'entreprise.", "Réseaux",
     lambda centre: launch.open_settings("kcm_networkmanagement")),
    ("Retrouver mes logiciels Windows", "Word, Excel, Outlook, Teams… : l'équivalent sous NicOS.", "Voir le catalogue",
     lambda centre: centre.show_page("catalogue") or launch.open_discover()),
    ("Brancher OneDrive et Microsoft 365", "Mes fichiers OneDrive dans le dossier personnel.", "OneDrive",
     lambda centre: launch.open_app("nicos-onedrive")),
    ("Installer des applications", "VLC, LibreOffice, Spotify… : on coche, NicOS installe. Discover reste là pour le reste.",
     "Choisir mes applications", lambda centre: centre.show_page("applications")),
    ("Choisir clair ou sombre", "Le thème NicOS existe en deux versions.", "Apparence",
     lambda centre: launch.open_settings("kcm_lookandfeel")),
    ("Administrer le PC", "Mises à jour, retour arrière, disques, pare-feu, domaine.", "Administration",
     lambda centre: launch.open_app("nicos-administration")),
]

# (sous Windows, sous NicOS)
EQUIVALENCES = [
    ("Menu Démarrer", "Le bouton NicOS, en haut à gauche"),
    ("Explorateur de fichiers", "Dolphin (barre en haut de l'écran)"),
    ("Paramètres, Panneau de configuration", "Paramètres (menu NicOS) ; les réglages avancés : Configuration du système"),
    ("Microsoft Store, Windows Update", "Discover"),
    ("Gestionnaire des tâches (Ctrl+Maj+Échap)", "Moniteur système (Ctrl+Échap)"),
    ("Outil Capture d'écran", "Spectacle (touche Impr. écran)"),
    ("Imprimer en PDF", "Imprimante « PDF », déjà installée"),
    ("Changer de fenêtre (Alt+Tab)", "Pareil : Alt+Tab"),
]


def _carte(centre, titre, description, bouton, action):
    carte = QFrame()
    carte.setObjectName("card")
    layout = QVBoxLayout(carte)
    layout.setContentsMargins(16, 14, 16, 14)
    haut = QLabel(titre)
    haut.setObjectName("cardTitle")
    haut.setWordWrap(True)
    texte = QLabel(description)
    texte.setWordWrap(True)
    bas = QPushButton(bouton)
    bas.setObjectName("primary")
    bas.setCursor(Qt.PointingHandCursor)
    bas.clicked.connect(lambda: action(centre))
    layout.addWidget(haut)
    layout.addWidget(texte, 1)
    layout.addWidget(bas, 0, Qt.AlignLeft)
    return carte


def build(centre):
    contenu = QWidget()
    page = QVBoxLayout(contenu)
    page.setContentsMargins(32, 28, 32, 28)
    page.setSpacing(14)

    titre = QLabel("Bienvenue dans NicOS")
    titre.setObjectName("pageTitle")
    intro = QLabel("Votre PC est prêt. Voici de quoi retrouver vos repères, "
                   "pas à pas, sans rien casser : tout ce qui est modifié peut être annulé.")
    intro.setObjectName("pageLead")
    intro.setWordWrap(True)
    page.addWidget(titre)
    page.addWidget(intro)

    section = QLabel("Pour bien démarrer")
    section.setObjectName("sectionTitle")
    page.addSpacing(6)
    page.addWidget(section)
    grille = QGridLayout()
    grille.setSpacing(14)
    for index, (titre_c, description, bouton, action) in enumerate(CARTES):
        grille.addWidget(_carte(centre, titre_c, description, bouton, action), index // 3, index % 3)
    for colonne in range(3):
        grille.setColumnStretch(colonne, 1)
    page.addLayout(grille)

    section = QLabel("Sous Windows, ici")
    section.setObjectName("sectionTitle")
    page.addSpacing(10)
    page.addWidget(section)
    tableau = QGridLayout()
    tableau.setHorizontalSpacing(24)
    tableau.setVerticalSpacing(6)
    for ligne, (windows, nicos) in enumerate(EQUIVALENCES):
        gauche = QLabel(windows)
        droite = QLabel(nicos)
        droite.setStyleSheet("font-weight: 600;")
        tableau.addWidget(gauche, ligne, 0)
        tableau.addWidget(QLabel("→"), ligne, 1)
        tableau.addWidget(droite, ligne, 2)
    tableau.setColumnStretch(3, 1)
    page.addLayout(tableau)
    page.addStretch(1)

    zone = QScrollArea()
    zone.setWidgetResizable(True)
    zone.setFrameShape(QFrame.NoFrame)
    zone.setWidget(contenu)
    return zone
