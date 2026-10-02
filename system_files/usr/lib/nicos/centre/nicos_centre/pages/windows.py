"""Windows dans une machine virtuelle : pour le logiciel indispensable qui n'existe pas sous NicOS."""

from PySide6.QtWidgets import QLabel, QWidget

from .. import launch, theme, virtualisation, widgets

ORDER = 25
KEY = "windows"
TITLE = "Windows complet"
ICONE = "monitor"
ACCENT = theme.ACCENTS["cyan"]

BOXES = "org.gnome.Boxes"
WINBOAT = "https://www.winboat.app/"
WINDOWS365 = "https://windows365.microsoft.com/"
# pictogramme et couleur de chaque résultat de vérification : vert, orange, rouge
ETATS = {
    virtualisation.OK: ("check", theme.ACCENTS["vert"]),
    virtualisation.ATTENTION: ("alert", theme.ACCENTS["ambre"]),
    virtualisation.KO: ("x", theme.ACCENTS["rouge"]),
}


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.verifications = virtualisation.verifier()
        self.outils = virtualisation.outils_winboat()
        installees = launch.installed_flatpaks()
        self.cartes = []

        contenu, page = widgets.page_de_cartes()
        page.addWidget(widgets.entete(
            "Windows dans une machine virtuelle",
            "Pour le logiciel indispensable qui n'existe pas sous NicOS (comptabilité, CAO, application métier) : "
            "Windows tourne dans une fenêtre, sur ce PC. <b>Il faut une licence Windows</b> (la vôtre, ou celle de "
            "l'entreprise) : NicOS n'en fournit pas. Essayez d'abord « Mon logiciel Windows » : beaucoup de "
            "logiciels ont un équivalent.", ICONE, ACCENT))

        page.addWidget(widgets.section("Ce PC est-il prêt ?", ACCENT))
        self.verifs = []
        for verification in self.verifications:
            icone, couleurs = ETATS[verification.etat]
            carte = widgets.carte(verification.titre, verification.detail, icone=icone, couleurs=couleurs)
            carte.etat = verification.etat
            self.verifs.append(carte)
            page.addWidget(carte)

        page.addWidget(widgets.section("Trois façons de faire", ACCENT))
        if BOXES in installees:
            boxes = widgets.carte("Boxes   <span style='font-weight:400; font-size:9pt;'>· Installé</span>",
                                  "Windows dans une fenêtre, avec un assistant qui l'installe pour vous. Le plus "
                                  "simple pour commencer.", "Ouvrir", lambda: launch.run_flatpak(BOXES),
                                  icone="monitor", couleurs=ACCENT)
        else:
            boxes = widgets.carte("Boxes   <span style='font-weight:400; font-size:9pt;'>· À installer depuis Flathub</span>",
                                  "Windows dans une fenêtre, avec un assistant qui l'installe pour vous. Le plus "
                                  "simple pour commencer.", "Installer", lambda: launch.open_discover(BOXES),
                                  icone="monitor", couleurs=ACCENT)
        self.cartes.append(boxes)
        page.addWidget(boxes)

        manquants = [nom for nom, present in self.outils if not present]
        etat_winboat = ("Podman et FreeRDP sont là : il ne reste qu'à télécharger WinBoat." if not manquants
                        else "Il manque : " + ", ".join(manquants) + ".")
        winboat = widgets.carte(
            "WinBoat   <span style='font-weight:400; font-size:9pt;'>· Expérimental</span>",
            "Les programmes Windows s'ouvrent dans leurs propres fenêtres, mêlées à celles de NicOS. Projet libre "
            "(MIT), encore en version bêta : prévoyez de dépanner. " + etat_winboat,
            "Page du projet", lambda: launch.open_url(WINBOAT), icone="layers", couleurs=theme.ACCENTS["indigo"])
        self.cartes.append(winboat)
        page.addWidget(winboat)

        nuage = widgets.carte(
            "Windows 365   <span style='font-weight:400; font-size:9pt;'>· Dans le navigateur</span>",
            "Un PC Windows dans le nuage, sans rien installer ni virtualisation. Abonnement Microsoft nécessaire "
            "(souvent déjà fourni par l'entreprise).", "Ouvrir le site", lambda: launch.open_url(WINDOWS365),
            icone="cloud", couleurs=theme.ACCENTS["bleu"])
        self.cartes.append(nuage)
        page.addWidget(nuage)

        limites = QLabel("<b>À savoir</b> : les logiciels très gourmands (3D, CAO lourde, jeux) tournent mal dans "
                         "une machine virtuelle. Pour les jeux, voir la page Jeux. Le premier démarrage de Windows "
                         "est long ; les fichiers se partagent par un dossier commun.")
        limites.setObjectName("bandeau")
        limites.setWordWrap(True)
        page.addWidget(limites)
        page.addStretch(1)
        widgets.remplir(self, contenu)


def build(centre):
    return Page(centre)
