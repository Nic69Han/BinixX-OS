"""Protéger mes données : clé de récupération du disque chiffré (l'équivalent de celle de BitLocker), pare-feu."""

import json
import os
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)

from .. import launch, theme, widgets

ORDER = 40
KEY = "securite"
TITLE = "Protéger mes données"
ICONE = "shield-check"
ACCENT = theme.ACCENTS["sarcelle"]

CLE_RECUPERATION = "/usr/libexec/binixx/binixx-cle-recuperation"

CONSEIL = ("Si vous oubliez le mot de passe de ce disque, vos fichiers sont perdus. La clé de récupération permet "
           "de les retrouver : imprimez-la ou notez-la, et gardez-la ailleurs que sur ce PC (tiroir fermé, coffre, "
           "clé USB rangée à part). Quiconque la possède peut lire vos fichiers.")


def texte_de_la_cle(cle, peripherique):
    """Contenu du papier ou du fichier remis à l'utilisateur."""
    return ("Clé de récupération du disque chiffré - BinixX OS\n"
            f"Disque : {peripherique}\n"
            f"Créée le : {time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Clé : {cle}\n\n"
            "À quoi elle sert : si le mot de passe du disque est oublié, saisissez cette clé à sa place au "
            "démarrage du PC pour retrouver vos fichiers.\n"
            "Gardez-la ailleurs que sur ce PC. Quiconque la possède peut lire vos fichiers.\n")


class CleDialog(QDialog):
    """Montre la clé une seule fois ; on ne ferme qu'après avoir confirmé l'avoir conservée."""

    def __init__(self, parent, cle, peripherique):
        super().__init__(parent)
        self.cle = cle
        self.peripherique = peripherique
        self.setWindowTitle("Votre clé de récupération")
        self.setMinimumWidth(620)
        disposition = QVBoxLayout(self)
        disposition.setContentsMargins(24, 20, 24, 20)
        disposition.setSpacing(12)
        explication = QLabel("Voici la clé de récupération. <b>Elle ne sera plus affichée.</b> Imprimez-la ou "
                             "enregistrez-la sur une clé USB que vous rangerez à part.")
        explication.setWordWrap(True)
        self.valeur = QLabel(cle)
        self.valeur.setObjectName("cleRecuperation")
        police = QFont("monospace")
        police.setStyleHint(QFont.Monospace)
        police.setPointSize(14)
        self.valeur.setFont(police)
        self.valeur.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.valeur.setWordWrap(True)
        self.valeur.setAlignment(Qt.AlignCenter)
        disposition.addWidget(explication)
        disposition.addWidget(self.valeur)

        ligne = QHBoxLayout()
        self.imprimer = QPushButton("Imprimer")
        self.enregistrer = QPushButton("Enregistrer dans un fichier…")
        self.imprimer.clicked.connect(self.imprimer_la_cle)
        self.enregistrer.clicked.connect(self.enregistrer_la_cle)
        ligne.addWidget(self.imprimer)
        ligne.addWidget(self.enregistrer)
        ligne.addStretch(1)
        disposition.addLayout(ligne)

        self.confirmation = QCheckBox("J'ai imprimé ou enregistré cette clé, et je l'ai rangée en lieu sûr.")
        self.fermer = QPushButton("Fermer")
        self.fermer.setObjectName("primary")
        self.fermer.setEnabled(False)
        self.confirmation.toggled.connect(self.fermer.setEnabled)
        self.fermer.clicked.connect(self.accept)
        disposition.addWidget(self.confirmation)
        disposition.addWidget(self.fermer, 0, Qt.AlignRight)

    def reject(self):
        """Échap ou la croix ne ferment pas : la clé ne se réaffiche pas, mieux vaut ne pas la perdre par mégarde."""
        if self.confirmation.isChecked():
            super().reject()

    def imprimer_la_cle(self):
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        imprimante = QPrinter()
        if QPrintDialog(imprimante, self).exec() == QDialog.Accepted:
            document = QTextDocument()
            document.setPlainText(texte_de_la_cle(self.cle, self.peripherique))
            document.print_(imprimante)

    def enregistrer_la_cle(self):
        usb = os.path.join("/run/media", os.environ.get("USER", ""))
        dossier = usb if os.path.isdir(usb) and os.listdir(usb) else os.path.join(os.path.expanduser("~"), "Documents")
        chemin, _ = QFileDialog.getSaveFileName(self, "Enregistrer la clé de récupération",
                                                os.path.join(dossier, "Cle-de-recuperation-BinixX-OS.txt"),
                                                "Texte (*.txt)")
        if not chemin:
            return
        # lisible par son seul propriétaire, et jamais écrasé sans qu'on l'ait choisi dans la boîte de dialogue
        descripteur = os.open(chemin, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descripteur, "w", encoding="utf-8") as fichier:
            fichier.write(texte_de_la_cle(self.cle, self.peripherique))


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        contenu, page = widgets.page_de_cartes()
        page.addWidget(widgets.entete(
            "Protéger mes données", "Si votre PC est perdu ou volé, vos fichiers doivent rester illisibles pour les "
                                    "autres, et vous devez pouvoir les retrouver si vous oubliez un mot de passe.",
            ICONE, ACCENT))

        page.addWidget(widgets.section("Chiffrement du disque", ACCENT))
        self.volumes = QVBoxLayout()
        self.volumes.setSpacing(12)
        page.addLayout(self.volumes)

        page.addWidget(widgets.section("Connexions", ACCENT))
        page.addWidget(self._carte(
            "Pare-feu", "Aucune connexion entrante n'est acceptée, sauf la découverte du réseau local "
                        "(imprimantes, voisinage Windows). Vous pouvez ouvrir un service précis si besoin.",
            "Ouvrir le pare-feu", lambda: launch.open_settings("kcm_firewall"), "shield"))
        page.addStretch(1)
        widgets.remplir(self, contenu)
        self.actualiser()

    # --- affichage -------------------------------------------------------------------------------------------

    def _carte(self, titre, texte, bouton, action, icone="lock"):
        return widgets.carte(titre, texte, bouton, action, icone=icone, couleurs=ACCENT)

    def liste_des_volumes(self):
        """Volumes chiffrés du PC (liste de dictionnaires) ; liste vide si on ne peut pas les lire."""
        code, sortie = launch.run([CLE_RECUPERATION, "volumes"], timeout=30)
        if code != 0:
            return []
        try:
            return json.loads(sortie)
        except ValueError:
            return []

    def actualiser(self):
        while self.volumes.count():
            element = self.volumes.takeAt(0).widget()
            if element is not None:
                element.deleteLater()
        self.cartes = []
        liste = self.liste_des_volumes()
        if not liste:
            self.volumes.addWidget(self._carte(
                "Le disque de ce PC n'est pas chiffré",
                "Si le PC est perdu ou volé, quelqu'un peut lire vos fichiers en retirant le disque. Le chiffrement "
                "se choisit à l'installation de BinixX OS (« Chiffrer mes données ») ; on ne peut pas l'ajouter après "
                "coup sans réinstaller. Les clés USB et les autres disques se chiffrent depuis l'administration.",
                "Administration des disques", lambda: launch.open_webapp("http://localhost:9090/storage")))
            return
        for volume in liste:
            nom = "Disque du système" if volume.get("systeme") else "Volume chiffré"
            detail = volume["chemin"] + (f" · {volume['taille']}" if volume.get("taille") else "")
            carte = self._carte(f"{nom} ({detail})", CONSEIL, "Créer une clé de récupération",
                                lambda _=False, v=volume: self.creer_cle(v))
            self.cartes.append(carte)
            self.volumes.addWidget(carte)

    # --- création de la clé (méthodes remplacées dans les tests : pas de boîte de dialogue) -------------------------

    def demander_mot_de_passe(self, volume):
        mot, valide = QInputDialog.getText(
            self, "Mot de passe du disque",
            f"Saisissez le mot de passe actuel du disque ({volume['chemin']}).\nC'est celui que vous tapez au "
            "démarrage du PC pour le déverrouiller.", QLineEdit.Password)
        return mot if valide and mot else None

    def confirmer_remplacement(self):
        reponse = QMessageBox.question(
            self, "Une clé existe déjà",
            "Ce disque a déjà une clé de récupération. En créer une nouvelle remplace l'ancienne : "
            "l'ancienne clé ne fonctionnera plus.\n\nRemplacer la clé ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reponse == QMessageBox.Yes

    def afficher_cle(self, cle, volume):
        CleDialog(self, cle, volume["chemin"]).exec()

    def afficher_erreur(self, message):
        QMessageBox.warning(self, "Clé de récupération", message)

    def executer(self, peripherique, mot_de_passe, remplacer):
        """Lance l'outil privilégié ; renvoie (code, clé ou message d'erreur). Jamais de mot de passe en argument."""
        commande = ["pkexec", CLE_RECUPERATION, "creer", peripherique] + (["--remplacer"] if remplacer else [])
        code, sortie, erreurs = launch.run_input(commande, mot_de_passe + "\n")
        if code == 0:
            for ligne in sortie.splitlines():
                if ligne.startswith("CLE="):
                    return 0, ligne[4:]
            return 5, "La clé n'a pas pu être lue."
        if code == 126:  # pkexec : l'utilisateur a fermé la fenêtre d'authentification
            return code, ""
        if code == 127:  # pkexec : droits insuffisants ou mot de passe d'administrateur refusé
            return code, ("L'autorisation d'administrateur n'a pas été accordée : seul un administrateur du PC "
                          "peut créer cette clé.")
        return code, erreurs.strip() or "La création de la clé a échoué."

    def creer_cle(self, volume):
        mot_de_passe = self.demander_mot_de_passe(volume)
        if not mot_de_passe:
            return
        code, resultat = self.executer(volume["chemin"], mot_de_passe, False)
        if code == 3:
            if not self.confirmer_remplacement():
                return
            code, resultat = self.executer(volume["chemin"], mot_de_passe, True)
        if code == 0:
            self.afficher_cle(resultat, volume)
        elif code != 126:  # 126 : l'utilisateur a renoncé, rien à dire
            self.afficher_erreur(resultat)


def build(centre):
    return Page(centre)
