"""Windows dans une machine virtuelle : pour le logiciel indispensable qui n'existe pas sous NicOS."""

from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from .. import launch, virtualisation, widgets

ORDER = 25
KEY = "windows"
TITLE = "Windows complet"

BOXES = "org.gnome.Boxes"
WINBOAT = "https://www.winboat.app/"
WINDOWS365 = "https://windows365.microsoft.com/"
PICTOS = {virtualisation.OK: "✔", virtualisation.ATTENTION: "⚠", virtualisation.KO: "✖"}


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.verifications = virtualisation.verifier()
        self.outils = virtualisation.outils_winboat()
        installees = launch.installed_flatpaks()
        self.cartes = []

        contenu = QWidget()
        page = QVBoxLayout(contenu)
        page.setContentsMargins(32, 28, 32, 24)
        page.setSpacing(12)
        titre = QLabel("Windows dans une machine virtuelle")
        titre.setObjectName("pageTitle")
        intro = QLabel("Pour le logiciel indispensable qui n'existe pas sous NicOS (comptabilité, CAO, application "
                       "métier) : Windows tourne dans une fenêtre, sur ce PC. <b>Il faut une licence Windows</b> "
                       "(la vôtre, ou celle de l'entreprise) : NicOS n'en fournit pas. Essayez d'abord "
                       "« Mon logiciel Windows » : beaucoup de logiciels ont un équivalent.")
        intro.setObjectName("pageLead")
        intro.setWordWrap(True)
        page.addWidget(titre)
        page.addWidget(intro)

        section = QLabel("Ce PC est-il prêt ?")
        section.setObjectName("sectionTitle")
        page.addSpacing(6)
        page.addWidget(section)
        for verification in self.verifications:
            page.addWidget(widgets.carte(f"{PICTOS[verification.etat]}  {verification.titre}", verification.detail))

        section = QLabel("Trois façons de faire")
        section.setObjectName("sectionTitle")
        page.addSpacing(8)
        page.addWidget(section)
        if BOXES in installees:
            boxes = widgets.carte("Boxes   <span style='font-weight:400; font-size:9pt;'>· Installé</span>",
                                  "Windows dans une fenêtre, avec un assistant qui l'installe pour vous. Le plus "
                                  "simple pour commencer.", "Ouvrir", lambda: launch.run_flatpak(BOXES))
        else:
            boxes = widgets.carte("Boxes   <span style='font-weight:400; font-size:9pt;'>· À installer depuis Flathub</span>",
                                  "Windows dans une fenêtre, avec un assistant qui l'installe pour vous. Le plus "
                                  "simple pour commencer.", "Installer", lambda: launch.open_discover(BOXES))
        self.cartes.append(boxes)
        page.addWidget(boxes)

        manquants = [nom for nom, present in self.outils if not present]
        etat_winboat = ("Podman et FreeRDP sont là : il ne reste qu'à télécharger WinBoat." if not manquants
                        else "Il manque : " + ", ".join(manquants) + ".")
        winboat = widgets.carte(
            "WinBoat   <span style='font-weight:400; font-size:9pt;'>· Expérimental</span>",
            "Les programmes Windows s'ouvrent dans leurs propres fenêtres, mêlées à celles de NicOS. Projet libre "
            "(MIT), encore en version bêta : prévoyez de dépanner. " + etat_winboat,
            "Page du projet", lambda: launch.open_url(WINBOAT))
        self.cartes.append(winboat)
        page.addWidget(winboat)

        nuage = widgets.carte(
            "Windows 365   <span style='font-weight:400; font-size:9pt;'>· Dans le navigateur</span>",
            "Un PC Windows dans le nuage, sans rien installer ni virtualisation. Abonnement Microsoft nécessaire "
            "(souvent déjà fourni par l'entreprise).", "Ouvrir le site", lambda: launch.open_url(WINDOWS365))
        self.cartes.append(nuage)
        page.addWidget(nuage)

        limites = QLabel("<b>À savoir</b> : les logiciels très gourmands (3D, CAO lourde, jeux) tournent mal dans "
                         "une machine virtuelle. Pour les jeux, voir la page Jeux. Le premier démarrage de Windows "
                         "est long ; les fichiers se partagent par un dossier commun.")
        limites.setWordWrap(True)
        page.addWidget(limites)
        page.addStretch(1)

        zone = QScrollArea()
        zone.setWidgetResizable(True)
        zone.setFrameShape(QFrame.NoFrame)
        zone.setWidget(contenu)
        racine = QVBoxLayout(self)
        racine.setContentsMargins(0, 0, 0, 0)
        racine.addWidget(zone)


def build(centre):
    return Page(centre)
