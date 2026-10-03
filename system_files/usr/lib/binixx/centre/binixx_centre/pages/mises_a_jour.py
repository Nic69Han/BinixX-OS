"""Mises à jour : la version installée, une mise à jour prête à appliquer, la version précédente, une recherche.

Page ouverte depuis Paramètres (« Mises à jour du système »). Les lectures (état, recherche) passent par
/usr/libexec/binixx/binixx-mises-a-jour sans mot de passe ; installer une mise à jour et revenir à la version précédente
demandent l'administrateur (pkexec). Rien ne bloque la fenêtre : chaque commande tourne dans un QProcess."""

import json

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QWidget

from .. import launch, misesajour, theme, widgets

ORDER = 14
KEY = "mises_a_jour"
TITLE = "Mises à jour"
ICONE = "refresh"
ACCENT = theme.ACCENTS["lime"]
MENU = False          # pas de bouton dans la barre latérale : on l'ouvre depuis Paramètres
PARENT = "parametres"

OUTIL = "/usr/libexec/binixx/binixx-mises-a-jour"
AUTHENTIFICATION_ANNULEE = (126, 127)  # pkexec : fenêtre fermée ou refusée

# Ce que dit la carte « Mises à jour » dans chaque situation : (message, texte du bouton ; None = pas de bouton)
SITUATIONS = {
    "inconnu": ("L'état des mises à jour n'a pas pu être lu. Ce PC ne démarre peut-être pas depuis une image BinixX OS.",
                None),
    "repos": ("BinixX OS se met à jour tout seul, en arrière-plan : la nouvelle version s'applique au redémarrage "
              "suivant. Vous pouvez aussi vérifier maintenant.", "Rechercher des mises à jour"),
    "verification": ("Recherche en cours…", None),
    "a_jour": ("Votre PC est à jour.", "Rechercher à nouveau"),
    "disponible": ("Une nouvelle version est disponible.", "Installer maintenant"),
    "installation": ("Téléchargement en cours. Vous pouvez continuer à travailler : le PC ne redémarre pas tout seul.",
                     None),
    "prete": ("Une mise à jour est prête. Redémarrez le PC pour l'appliquer.", "Redémarrer maintenant"),
    "retour": ("C'est fait : la version précédente reviendra au prochain redémarrage. Vos documents et vos réglages "
               "ne changent pas.", "Redémarrer maintenant"),
    "inconnue": ("", "Rechercher à nouveau"),   # la recherche n'a pas abouti : le message dit pourquoi
    "echec": ("", "Réessayer"),
}


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.mode = "repos"
        self.donnees = None        # l'état lu (misesajour.reponse), ou None
        self.verification = None   # la dernière recherche
        self.processus = None
        self.detail = ""
        contenu, page = widgets.page_de_cartes()

        retour = QPushButton("← Retour aux Paramètres")
        retour.setObjectName("secondaire")
        retour.setCursor(Qt.PointingHandCursor)
        retour.clicked.connect(lambda: centre.show_page("parametres"))
        page.addWidget(retour, 0, Qt.AlignLeft)
        page.addWidget(widgets.entete(
            "Mises à jour", "La version de BinixX OS installée sur ce PC, ce qui est prêt à s'appliquer, et la "
                            "possibilité de revenir en arrière.", ICONE, ACCENT))

        page.addWidget(widgets.section("Ce PC", ACCENT))
        self.version = QLabel("Lecture de l'état du système…")
        self.version.setWordWrap(True)
        self.version.setTextFormat(Qt.RichText)
        self.carte_version = widgets.carte("Version installée", "", icone="package", couleurs=ACCENT, corps=self.version)
        page.addWidget(self.carte_version)

        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.carte_etat = widgets.carte("Mises à jour du système", "", "Rechercher des mises à jour",
                                        self.action_principale, icone="refresh", couleurs=ACCENT, corps=self.message)
        self.bouton = self.carte_etat.bouton
        page.addWidget(self.carte_etat)

        self.precedente = QLabel("")
        self.precedente.setWordWrap(True)
        self.carte_precedente = widgets.carte(
            "Revenir à la version précédente", "", "Revenir en arrière", self.revenir, icone="rotate", couleurs=ACCENT,
            corps=self.precedente)
        self.bouton_retour = self.carte_precedente.bouton
        page.addWidget(self.carte_precedente)

        page.addWidget(widgets.section("Applications", ACCENT))
        page.addWidget(widgets.carte(
            "Mises à jour des applications",
            "Les applications (navigateur, bureautique, jeux…) se mettent à jour séparément, chaque jour. Discover "
            "montre celles qui attendent.", "Ouvrir Discover", lambda: launch.open_discover_mode("update"),
            icone="download", couleurs=ACCENT))
        page.addStretch(1)
        widgets.remplir(self, contenu)
        self.afficher()

    # --- affichage ---------------------------------------------------------------------------------------------

    def showEvent(self, evenement):
        super().showEvent(evenement)
        if self.donnees is None and not self.occupe():
            self.lire_l_etat()

    def occupe(self):
        return self.processus is not None and self.processus.state() != QProcess.NotRunning

    def afficher(self):
        """Met à jour les cartes d'après `self.donnees`, `self.mode` et `self.verification`."""
        donnees = self.donnees
        if donnees is None:
            self.version.setText("Version inconnue.")
        else:
            installee = donnees["installee"]
            ligne = f"<b>{installee['version'] or 'Version inconnue'}</b>"
            if installee["date"]:
                ligne += f", mise à jour du {installee['date']}"
            self.version.setText(f"{ligne}<br><span style='color: gray;'>{donnees['canal']}.</span>")
        message, bouton = SITUATIONS[self.mode]
        if self.mode == "disponible" and self.verification and self.verification.get("taille"):
            message += f" Environ {misesajour.taille_lisible(self.verification['taille'])} à télécharger."
        if self.mode == "prete" and donnees and donnees["prete"] and donnees["prete"]["version"]:
            message = f"La version {donnees['prete']['version']} est prête. Redémarrez le PC pour l'appliquer."
        if self.detail and self.mode in ("inconnue", "echec"):
            message = self.detail
        self.message.setText(message)
        self.bouton.setVisible(bouton is not None)
        if bouton is not None:
            self.bouton.setText(bouton)
        self.bouton.setEnabled(not self.occupe())
        precedente = donnees["precedente"] if donnees else None
        self.carte_precedente.setVisible(precedente is not None)
        if precedente is not None:
            quand = f" ({precedente['date']})" if precedente["date"] else ""
            self.precedente.setText(
                f"Si une mise à jour pose problème, vous pouvez remettre la version <b>{precedente['version'] or 'précédente'}"
                f"</b>{quand}. Vos documents et vos réglages ne changent pas ; il faudra redémarrer le PC.")
        self.bouton_retour.setEnabled(not self.occupe() and self.mode not in ("retour", "installation"))

    # --- commandes ---------------------------------------------------------------------------------------------

    def _lancer(self, argv, rappel):
        """Lance `argv` sans bloquer la fenêtre ; `rappel(code, sortie)` est appelé à la fin (code -1 : introuvable)."""
        processus = QProcess(self)
        processus.setProcessChannelMode(QProcess.MergedChannels)

        def fini(code, _statut):
            rappel(code, bytes(processus.readAllStandardOutput()).decode("utf-8", "replace"))

        def erreur(genre):
            if genre == QProcess.FailedToStart:
                rappel(-1, "")

        processus.finished.connect(fini)
        processus.errorOccurred.connect(erreur)
        self.processus = processus
        processus.start(argv[0], argv[1:])
        return processus

    def lire_l_etat(self):
        self._lancer([OUTIL, "etat", "--json"], self._etat_lu)

    def _etat_lu(self, code, sortie):
        self.processus = None
        try:
            self.donnees = json.loads(sortie) if code == 0 else None
        except ValueError:
            self.donnees = None
        if self.donnees is None:
            self.mode = "inconnu"
        elif self.donnees["prete"]:
            self.mode = "prete"
        elif self.mode == "inconnu":
            self.mode = "repos"
        self.afficher()

    def action_principale(self):
        """Le bouton de la carte « Mises à jour » : il change de rôle selon la situation."""
        if self.occupe():
            return
        if self.mode in ("repos", "a_jour", "inconnue", "echec"):
            self.rechercher()
        elif self.mode == "disponible":
            self.installer()
        elif self.mode in ("prete", "retour"):
            launch.reboot_prompt()

    def rechercher(self):
        self.mode = "verification"
        self.detail = ""
        self.afficher()
        self._lancer([OUTIL, "verifier", "--json"], self._recherche_finie)

    def _recherche_finie(self, code, sortie):
        self.processus = None
        try:
            reponse = json.loads(sortie) if code == 0 else None
        except ValueError:
            reponse = None
        if reponse is None:
            self.mode, self.detail = "echec", "La recherche n'a pas pu être faite. Réessayez dans un instant."
        else:
            self.donnees = reponse
            self.verification = reponse.get("verification") or {}
            disponible = self.verification.get("disponible")
            if reponse["prete"]:
                self.mode = "prete"
            elif disponible is None:
                self.mode, self.detail = "inconnue", self.verification.get("raison") or "On ne sait pas s'il y a une nouvelle version."
            else:
                self.mode = "disponible" if disponible else "a_jour"
        self.afficher()

    def installer(self):
        self.mode = "installation"
        self.afficher()
        self._lancer(["pkexec", OUTIL, "installer"], self._installation_finie)

    def _installation_finie(self, code, sortie):
        self.processus = None
        if code == 0:
            self.lire_l_etat_apres_action("prete")
            return
        if code in AUTHENTIFICATION_ANNULEE:  # l'utilisateur a fermé la fenêtre du mot de passe : rien à dire
            self.mode = "disponible"
        else:
            self.mode = "echec"
            self.detail = f"La mise à jour n'a pas pu être téléchargée (code {code}). Rien n'a changé sur ce PC."
        self.afficher()

    def revenir(self):
        precedente = self.donnees["precedente"] if self.donnees else None
        if precedente is None or self.occupe():
            return
        reponse = QMessageBox.question(
            self, "Revenir à la version précédente",
            f"Remettre la version {precedente['version'] or 'précédente'}"
            + (f" ({precedente['date']})" if precedente["date"] else "")
            + " ?\n\nVos documents et vos réglages ne changent pas. Le PC devra redémarrer pour terminer.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reponse != QMessageBox.Yes:
            return
        self.mode = "installation"
        self.afficher()
        self._lancer(["pkexec", OUTIL, "retour"], self._retour_fini)

    def _retour_fini(self, code, sortie):
        self.processus = None
        if code == 0:
            self.lire_l_etat_apres_action("retour")
            return
        self.mode = "repos"
        if code not in AUTHENTIFICATION_ANNULEE:
            self.mode = "echec"
            self.detail = f"Le retour à la version précédente n'a pas pu être fait (code {code}). Rien n'a changé."
        self.afficher()

    def lire_l_etat_apres_action(self, mode):
        """Après une installation ou un retour : relit l'état (la version préparée change), puis affiche `mode`."""
        self.mode = mode
        self.afficher()

        def lu(code, sortie):
            self.processus = None
            try:
                self.donnees = json.loads(sortie) if code == 0 else self.donnees
            except ValueError:
                pass
            self.afficher()

        self._lancer([OUTIL, "etat", "--json"], lu)


def build(centre):
    return Page(centre)
