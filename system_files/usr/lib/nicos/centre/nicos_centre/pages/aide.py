"""Obtenir de l'aide : dépannage pas à pas, sans rien installer ni envoyer, et rapport pour le support."""

import json
import os
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .. import launch

ORDER = 30
KEY = "aide"
TITLE = "Obtenir de l'aide"

DIAGNOSTIC = "/usr/libexec/nicos/nicos-diagnostic"
REINITIALISER = "/usr/libexec/nicos/nicos-reinitialiser-bureau"
REPARER = "/usr/libexec/nicos/nicos-reparer-systeme"

ETATS = {"modifie": "Modifié", "supprime": "Supprimé (sera remis)", "ajoute": "Ajouté (sera retiré)"}

# (titre, que faire, libellé du bouton, nom de l'action)
PROBLEMES = [
    ("Je n'ai plus Internet",
     "Vérifiez que le Wi-Fi est activé (icône réseau, en haut à droite) et redémarrez la box. "
     "Si le problème reste, regardez la liste des réseaux.",
     "Ouvrir les réseaux", "reseau"),
    ("Mon imprimante n'imprime pas",
     "Imprimante allumée et sur le même réseau ? Essayez d'abord d'imprimer en PDF : si cela marche, "
     "le problème vient de l'imprimante, pas de l'application.",
     "Ouvrir les imprimantes", "imprimantes"),
    ("Je n'entends rien",
     "Vérifiez le volume (icône haut-parleur, en haut à droite) et la sortie choisie : haut-parleurs, "
     "casque ou écran HDMI.",
     "Ouvrir le son", "son"),
    ("L'écran n'a pas la bonne taille, ou un second écran reste noir",
     "Branchez le câble, puis réglez la résolution et la disposition des écrans.",
     "Ouvrir les écrans", "ecrans"),
    ("Le PC est lent",
     "Le moniteur système montre ce qui consomme la mémoire et le processeur. Fermer les onglets et les "
     "applications inutilisées aide aussi. Un disque presque plein ralentit tout : Filelight montre ce qui "
     "prend de la place.",
     "Ouvrir le moniteur système", "moniteur"),
    ("Depuis la dernière mise à jour, quelque chose ne marche plus",
     "NicOS garde la version précédente : on y revient en un redémarrage, sans rien perdre. "
     "Administration du PC → Mises à jour logicielles → « Revenir en arrière ».",
     "Ouvrir l'administration", "retour"),
    ("Mon bureau est cassé (barre, icônes, couleurs)",
     "Remet la barre, le thème et les raccourcis comme au premier jour. Vos fichiers, vos applications, "
     "la langue et le clavier ne changent pas ; les anciens réglages sont gardés dans un dossier.",
     "Réinitialiser le bureau", "bureau"),
    ("Un réglage du système modifié à la main pose problème",
     "Un tutoriel suivi trop vite ou un essai oublié peut dérégler l'écran de connexion, le son, le pare-feu… "
     "NicOS compare les réglages du système avec ceux d'origine et remet ceux que vous choisissez ; une copie "
     "est gardée pour pouvoir annuler. Comptes, mots de passe, réseau et disques ne sont jamais touchés.",
     "Voir les réglages modifiés", "reparer"),
]


class ReparationDialog(QDialog):
    """Réglages du système différents de l'image : l'utilisateur coche ceux qu'il veut remettre à l'origine."""

    def __init__(self, parent, changements, peut_annuler=False):
        super().__init__(parent)
        self.action = None
        self.setWindowTitle("Réparer le système")
        self.setMinimumSize(640, 420)
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(24, 20, 24, 20)
        disposition.setSpacing(12)
        texte = QLabel("Réglages du système différents de ceux d'origine. Cochez ceux à remettre comme au premier "
                       "jour : la version actuelle est gardée, vous pourrez annuler.")
        texte.setWordWrap(True)
        disposition.addWidget(texte)
        self.liste = QListWidget()
        for changement in changements:
            item = QListWidgetItem(f"{ETATS.get(changement['etat'], changement['etat'])} : {changement['chemin']}"
                                   f"   ({changement['categorie']})")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, changement["chemin"])
            self.liste.addItem(item)
        self.liste.itemChanged.connect(self._mettre_a_jour)
        disposition.addWidget(self.liste, 1)
        if not changements:
            vide = QLabel("Aucun réglage du système n'est différent de celui d'origine.")
            disposition.addWidget(vide)
        ligne = QHBoxLayout()
        self.annuler_dernier = QPushButton("Annuler la dernière réparation")
        self.annuler_dernier.setVisible(peut_annuler)
        self.annuler_dernier.clicked.connect(lambda: self._terminer("annuler"))
        self.reparer = QPushButton("Remettre à l'origine les éléments cochés")
        self.reparer.setObjectName("primary")
        self.reparer.setEnabled(False)
        self.reparer.clicked.connect(lambda: self._terminer("restaurer"))
        fermer = QPushButton("Fermer")
        fermer.clicked.connect(self.reject)
        ligne.addWidget(self.annuler_dernier)
        ligne.addStretch(1)
        ligne.addWidget(fermer)
        ligne.addWidget(self.reparer)
        disposition.addLayout(ligne)

    def selection(self):
        """Chemins (relatifs à /etc) des éléments cochés."""
        return [self.liste.item(i).data(Qt.UserRole) for i in range(self.liste.count())
                if self.liste.item(i).checkState() == Qt.Checked]

    def _mettre_a_jour(self, _item=None):
        self.reparer.setEnabled(bool(self.selection()))

    def _terminer(self, action):
        self.action = action
        self.accept()


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.actions = {
            "reseau": lambda: launch.open_settings("kcm_networkmanagement"),
            "imprimantes": lambda: launch.open_settings("kcm_printer_manager"),
            "son": lambda: launch.open_settings("kcm_pulseaudio"),
            "ecrans": lambda: launch.open_settings("kcm_kscreen"),
            "moniteur": lambda: launch.open_app("org.kde.plasma-systemmonitor"),
            "retour": lambda: launch.open_webapp("http://localhost:9090/updates"),
            "bureau": self.reinitialiser_bureau,
            "reparer": self.reparer_systeme,
        }

        contenu = QWidget()
        page = QVBoxLayout(contenu)
        page.setContentsMargins(32, 28, 32, 24)
        page.setSpacing(12)
        titre = QLabel("Obtenir de l'aide")
        titre.setObjectName("pageTitle")
        intro = QLabel("Un souci ? Voici les cas les plus fréquents. Rien n'est envoyé nulle part : "
                       "tout reste sur ce PC.")
        intro.setObjectName("pageLead")
        intro.setWordWrap(True)
        page.addWidget(titre)
        page.addWidget(intro)

        for titre_p, texte, bouton, action in PROBLEMES:
            page.addWidget(self._carte(titre_p, texte, bouton, self.actions[action]))

        page.addSpacing(8)
        section = QLabel("Et si rien ne règle le problème ?")
        section.setObjectName("sectionTitle")
        page.addWidget(section)
        self.rapport_texte = QLabel("Le rapport de diagnostic décrit l'état du PC (mises à jour, services en échec, "
                                    "erreurs récentes, disques, matériel). Il ne contient ni mot de passe, ni "
                                    "fichier, ni adresse réseau. Relisez-le, puis joignez-le à votre demande à "
                                    "l'administrateur ou au support.")
        self.rapport_texte.setWordWrap(True)
        self.rapport_carte = self._carte("Créer un rapport pour le support", "", "Créer le rapport",
                                         self.creer_rapport, corps=self.rapport_texte)
        page.addWidget(self.rapport_carte)
        page.addStretch(1)

        zone = QScrollArea()
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.NoFrame)
        zone.setWidget(contenu)
        racine = QVBoxLayout(self)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.addWidget(zone)

    def _carte(self, titre, texte, bouton, action, corps=None):
        carte = QFrame()
        carte.setObjectName("card")
        ligne = QHBoxLayout(carte)
        ligne.setContentsMargins(16, 12, 16, 12)
        colonne = QVBoxLayout()
        colonne.setSpacing(3)
        haut = QLabel(titre)
        haut.setObjectName("cardTitle")
        haut.setWordWrap(True)
        colonne.addWidget(haut)
        if corps is None:
            corps = QLabel(texte)
            corps.setWordWrap(True)
        colonne.addWidget(corps)
        ligne.addLayout(colonne, 1)
        action_bouton = QPushButton(bouton)
        action_bouton.setObjectName("primary")
        action_bouton.setCursor(Qt.PointingHandCursor)
        action_bouton.clicked.connect(action)
        ligne.addWidget(action_bouton, 0, Qt.AlignVCenter)
        return carte

    def reinitialiser_bureau(self):
        reponse = QMessageBox.question(
            self, "Réinitialiser le bureau",
            "La barre, le thème et les raccourcis reviendront comme au premier jour à la prochaine ouverture de "
            "session. Vos fichiers, vos applications, la langue et le clavier ne changent pas ; les anciens "
            "réglages sont gardés dans un dossier.\n\nFermer la session maintenant ?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
        if reponse == QMessageBox.Cancel:
            return
        launch.run([REINITIALISER, "programmer"])
        if reponse == QMessageBox.Yes:
            launch.logout_prompt()

    # --- réparer le système (méthodes remplacées dans les tests : pas de boîte de dialogue) ----------------------

    def informer(self, titre, texte):
        QMessageBox.information(self, titre, texte)

    def choisir_reparations(self, changements, peut_annuler=False):
        """Liste de chemins à remettre à l'origine, ou « annuler » pour défaire la dernière réparation."""
        dialogue = ReparationDialog(self, changements, peut_annuler)
        if dialogue.exec() != QDialog.Accepted:
            return []
        return "annuler" if dialogue.action == "annuler" else dialogue.selection()

    def _json(self, argument):
        code, sortie = launch.run([REPARER, argument], timeout=60)
        if code != 0:
            return None
        try:
            return json.loads(sortie)
        except ValueError:
            return None

    def reparer_systeme(self):
        changements = self._json("liste")
        sauvegardes = self._json("sauvegardes")
        if changements is None or sauvegardes is None:
            self.informer("Réparer le système", "Impossible de lire la liste des réglages du système.")
            return
        peut_annuler = any(not s.get("annulee") for s in sauvegardes)
        if not changements and not peut_annuler:
            self.informer("Réparer le système",
                          "Aucun réglage du système n'a été modifié depuis l'installation : il n'y a rien à "
                          "réparer ici. Si le problème persiste, créez un rapport pour le support.")
            return
        choix = self.choisir_reparations(changements, peut_annuler)
        if not choix:
            return
        commande = ["annuler"] if choix == "annuler" else ["restaurer", *choix]
        code, _ = launch.run(["pkexec", REPARER, *commande], timeout=300)
        if code == 0:
            self.informer("Réparer le système",
                          "C'est fait. Redémarrez le PC pour que tout soit pris en compte. La version précédente "
                          "de chaque fichier est gardée : vous pouvez annuler depuis cette même page.")
        elif code != 126:  # 126 : fenêtre d'authentification fermée, rien à dire
            self.informer("Réparer le système", f"La réparation n'a pas pu être faite (code {code}). "
                                                "Aucun fichier n'a été modifié.")

    def creer_rapport(self):
        code, sortie = launch.run([DIAGNOSTIC], timeout=120)
        dossier = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(dossier, exist_ok=True)
        chemin = os.path.join(dossier, "Rapport-NicOS-" + time.strftime("%Y%m%d-%H%M%S") + ".txt")
        with open(chemin, "w", encoding="utf-8") as fichier:
            fichier.write(sortie)
        QGuiApplication.clipboard().setText(sortie)
        self.rapport_texte.setText(f"Rapport enregistré : <b>{chemin}</b><br>Il est aussi copié : vous pouvez le "
                                   "coller dans un message. Relisez-le avant de l'envoyer.")
        launch.open_app("org.kde.dolphin")
        return chemin


def build(centre):
    return Page(centre)
