"""Accueil : les premiers pas d'un utilisateur qui vient de Windows."""

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel

from .. import launch, theme, widgets

ORDER = 10
KEY = "accueil"
TITLE = "Accueil"
ICONE = "home"
ACCENT = theme.ACCENTS["bleu"]

# (titre, description, libellé du bouton, action, icône, couleur)
CARTES = [
    ("Me connecter à Internet", "Wi-Fi, câble ou VPN de l'entreprise.", "Réseaux",
     lambda centre: launch.open_settings("kcm_networkmanagement"), "wifi", theme.ACCENTS["cyan"]),
    ("Retrouver mes logiciels Windows", "Word, Excel, Outlook, Teams… : l'équivalent sous BinixX OS.", "Voir le catalogue",
     lambda centre: centre.show_page("catalogue") or launch.open_discover(), "search", theme.ACCENTS["orange"]),
    ("Brancher OneDrive et Microsoft 365", "Mes fichiers OneDrive dans le dossier personnel.", "OneDrive",
     lambda centre: launch.open_app("binixx-onedrive"), "cloud", theme.ACCENTS["bleu"]),
    ("Installer des applications", "VLC, LibreOffice, Spotify… : on coche, BinixX OS installe. Discover reste là pour le reste.",
     "Choisir mes applications", lambda centre: centre.show_page("applications"), "download", theme.ACCENTS["violet"]),
    ("Choisir clair ou sombre", "Le thème BinixX OS existe en deux versions.", "Apparence",
     lambda centre: launch.open_settings("kcm_lookandfeel"), "sun", theme.ACCENTS["ambre"]),
    ("Administrer le PC", "Mises à jour, retour arrière, disques, pare-feu, domaine.", "Administration",
     lambda centre: launch.open_app("binixx-administration"), "settings", theme.ACCENTS["sarcelle"]),
]

# (sous Windows, sous BinixX OS)
EQUIVALENCES = [
    ("Menu Démarrer", "Le bouton BinixX OS, en haut à gauche"),
    ("Explorateur de fichiers", "Dolphin (barre en haut de l'écran)"),
    ("Paramètres, Panneau de configuration", "Paramètres (menu BinixX OS) ; les réglages avancés : Configuration du système"),
    ("Microsoft Store, Windows Update", "Discover"),
    ("Gestionnaire des tâches (Ctrl+Maj+Échap)", "Moniteur système (Ctrl+Échap)"),
    ("Outil Capture d'écran", "Spectacle (touche Impr. écran)"),
    ("Imprimer en PDF", "Imprimante « PDF », déjà installée"),
    ("Changer de fenêtre (Alt+Tab)", "Pareil : Alt+Tab"),
]


def build(centre):
    contenu, page = widgets.page_de_cartes()
    page.setSpacing(14)
    page.addWidget(widgets.entete(
        "Bienvenue dans BinixX OS",
        "Votre PC est prêt. Voici de quoi retrouver vos repères, pas à pas, sans rien casser : tout ce qui est "
        "modifié peut être annulé.", "home", ACCENT))

    page.addWidget(widgets.section("Pour bien démarrer", ACCENT))
    cartes = [widgets.carte_haute(titre, description, bouton, lambda _=False, a=action: a(centre), icone, couleurs)
              for titre, description, bouton, action, icone, couleurs in CARTES]
    page.addWidget(widgets.Grille(cartes))

    page.addWidget(widgets.section("Sous Windows, ici", ACCENT))
    tableau = QFrame()
    tableau.setObjectName("card")
    lignes = QGridLayout(tableau)
    lignes.setContentsMargins(20, 14, 20, 14)
    lignes.setHorizontalSpacing(14)
    lignes.setVerticalSpacing(9)
    for ligne, (windows, binixx) in enumerate(EQUIVALENCES):
        gauche = QLabel(windows)
        droite = QLabel(binixx)
        droite.setStyleSheet("font-weight: 600;")
        for texte in (gauche, droite):
            texte.setWordWrap(True)
        fleche = QLabel()
        fleche.setPixmap(widgets.glyphe("chevron", theme.BLUE, 16))
        fleche.setFixedSize(16, 16)
        lignes.addWidget(gauche, ligne, 0)
        lignes.addWidget(fleche, ligne, 1)
        lignes.addWidget(droite, ligne, 2)
    lignes.setColumnStretch(0, 4)
    lignes.setColumnStretch(2, 5)
    page.addWidget(tableau)
    page.addStretch(1)

    return widgets.defilante(contenu)
