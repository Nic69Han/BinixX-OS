"""Éléments d'interface partagés par les pages du Centre NicOS."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


def carte(titre, texte, bouton=None, action=None, details=None):
    """Une carte : titre, texte, éventuellement une ligne de détail en grisé et un bouton à droite.

    La carte garde son bouton dans l'attribut `bouton` (None s'il n'y en a pas)."""
    cadre = QFrame()
    cadre.setObjectName("card")
    ligne = QHBoxLayout(cadre)
    ligne.setContentsMargins(16, 12, 16, 12)
    colonne = QVBoxLayout()
    colonne.setSpacing(3)
    haut = QLabel(titre)
    haut.setObjectName("cardTitle")
    haut.setWordWrap(True)
    colonne.addWidget(haut)
    if details:
        detail = QLabel(details)
        detail.setStyleSheet("font-size: 9pt;")
        detail.setEnabled(False)
        detail.setWordWrap(True)
        colonne.addWidget(detail)
    if texte:
        corps = QLabel(texte)
        corps.setWordWrap(True)
        colonne.addWidget(corps)
    ligne.addLayout(colonne, 1)
    cadre.bouton = None
    if bouton:
        cadre.bouton = QPushButton(bouton)
        cadre.bouton.setObjectName("primary")
        cadre.bouton.setCursor(Qt.PointingHandCursor)
        cadre.bouton.clicked.connect(action)
        ligne.addWidget(cadre.bouton, 0, Qt.AlignVCenter)
    return cadre
