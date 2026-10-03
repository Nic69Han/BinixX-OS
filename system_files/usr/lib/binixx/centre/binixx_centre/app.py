"""Fenêtre du Centre BinixX OS : barre latérale de pages à gauche, page à droite."""

import argparse
import os
import sys
import traceback

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QButtonGroup, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from . import pages, theme, widgets

PREMIER_DEMARRAGE = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                                 "binixx", "accueil-vu")


def nom_du_systeme():
    """« BinixX OS 44 » d'après /etc/os-release (PRETTY_NAME sans guillemets)."""
    try:
        with open("/etc/os-release", encoding="utf-8") as fichier:
            for ligne in fichier:
                if ligne.startswith("PRETTY_NAME="):
                    return ligne.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "BinixX OS"


class Centre(QWidget):
    def __init__(self, options=None):
        super().__init__()
        self.options = options or {}
        self.errors = []
        self.keys = []
        self.widgets = {}
        self.parents = {}
        self.setWindowTitle("Centre BinixX OS")
        self.setWindowIcon(QIcon.fromTheme("binixx"))
        self.resize(1120, 720)
        self.setMinimumSize(880, 560)

        racine = QHBoxLayout(self)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.setSpacing(0)

        barre = QWidget()
        barre.setObjectName("sidebar")
        barre.setFixedWidth(264)
        colonne = QVBoxLayout(barre)
        colonne.setContentsMargins(12, 22, 12, 16)
        colonne.setSpacing(3)
        logo = QLabel()
        logo.setPixmap(QIcon.fromTheme("binixx").pixmap(QSize(56, 56)))
        titre = QLabel("BinixX OS")
        titre.setObjectName("sidebarTitle")
        sous_titre = QLabel(nom_du_systeme())
        sous_titre.setObjectName("sidebarSubtitle")
        colonne.addWidget(logo)
        colonne.addWidget(titre)
        colonne.addWidget(sous_titre)
        colonne.addSpacing(18)

        self.pile = QStackedWidget()
        self.boutons = QButtonGroup(self)
        self.boutons.setExclusive(True)
        for module in pages.discover():
            self._ajouter_page(module, colonne)
        colonne.addStretch(1)

        racine.addWidget(barre)
        racine.addWidget(self.pile, 1)

    def _ajouter_page(self, module, colonne):
        try:
            widget = module.build(self)
        except Exception:  # une page défaillante ne doit pas empêcher d'ouvrir les autres
            self.errors.append((module.KEY, traceback.format_exc()))
            widget = QLabel(f"La page « {module.TITLE} » n'a pas pu être affichée.")
            widget.setAlignment(Qt.AlignCenter)
        index = self.pile.addWidget(widget)
        self.keys.append(module.KEY)
        self.widgets[module.KEY] = widget
        self.parents[module.KEY] = getattr(module, "PARENT", module.KEY)
        if not getattr(module, "MENU", True):  # page ouverte depuis une autre, sans bouton dans la barre latérale
            return
        bouton = QPushButton(module.TITLE)
        bouton.setObjectName("nav")
        bouton.setIcon(QIcon(widgets.pastille(getattr(module, "ICONE", "grid"),
                                              getattr(module, "ACCENT", theme.ACCENTS["bleu"]), 30, marge_droite=8)))
        bouton.setIconSize(QSize(38, 30))
        bouton.setCheckable(True)
        bouton.setCursor(Qt.PointingHandCursor)
        bouton.clicked.connect(lambda _=False, i=index: self.pile.setCurrentIndex(i))
        self.boutons.addButton(bouton, index)
        colonne.addWidget(bouton)
        if index == 0:
            bouton.setChecked(True)

    def show_page(self, key):
        """Affiche la page d'identifiant `key` ; sans effet si elle n'existe pas.

        Une page sans bouton (MENU = False) laisse allumé le bouton de sa page parente (PARENT)."""
        if key in self.keys:
            self.pile.setCurrentIndex(self.keys.index(key))
            bouton = self.boutons.button(self.keys.index(self.parents.get(key, key)))
            if bouton is not None:
                bouton.setChecked(True)
            return True
        return False


def parse(argv):
    parser = argparse.ArgumentParser(prog="binixx-centre", description="Centre BinixX OS")
    parser.add_argument("--page", default="accueil", help="page à ouvrir (accueil, catalogue, aide…)")
    parser.add_argument("--programme", metavar="FICHIER",
                        help="fichier Windows (.exe, .msi) ouvert par l'utilisateur : cherche son équivalent")
    parser.add_argument("--recherche", metavar="TEXTE", default="",
                        help="texte à mettre dans la barre de recherche de la page ouverte (catalogue, paramètres)")
    parser.add_argument("--premier-demarrage", action="store_true",
                        help="n'ouvre la fenêtre qu'à la première ouverture de session")
    parser.add_argument("--test", metavar="DOSSIER",
                        help="construit toutes les pages, en enregistre une capture dans DOSSIER, puis quitte")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)
    if args.premier_demarrage and os.path.exists(PREMIER_DEMARRAGE):
        return 0
    app = QApplication(sys.argv[:1])
    app.setApplicationName("binixx-centre")
    app.setDesktopFileName("binixx-centre")
    app.setStyleSheet(theme.STYLE)
    centre = Centre()
    if args.programme:
        args.page = "catalogue"
        centre.widgets["catalogue"].ouvrir_fichier(args.programme)
    centre.show_page(args.page)
    champ = getattr(centre.widgets.get(args.page), "recherche", None)
    if args.recherche and champ is not None:
        champ.setText(args.recherche)

    if args.test:
        os.makedirs(args.test, exist_ok=True)
        for index, key in enumerate(centre.keys):
            centre.show_page(key)
            centre.show()
            app.processEvents()
            centre.grab().save(os.path.join(args.test, f"{key}.png"))
        for key, trace in centre.errors:
            print(f"page {key} : erreur\n{trace}", file=sys.stderr)
        print(f"pages : {', '.join(centre.keys)}")
        return 1 if centre.errors else 0

    centre.show()
    if args.premier_demarrage:
        os.makedirs(os.path.dirname(PREMIER_DEMARRAGE), exist_ok=True)
        open(PREMIER_DEMARRAGE, "w", encoding="utf-8").close()
    return app.exec()
