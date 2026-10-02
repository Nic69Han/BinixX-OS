"""Jeux : boutiques et outils à la demande, carte graphique, manettes. Rien n'est installé d'office."""

from PySide6.QtWidgets import QLabel, QWidget

from .. import catalogue, launch, materiel, theme, widgets

ORDER = 50
KEY = "jeux"
TITLE = "Jeux"
ICONE = "gamepad"
ACCENT = theme.ACCENTS["rouge"]

CATEGORIE = "Jeux"
PROTONDB = "https://www.protondb.com/"


def texte_cartes(cartes, via_switcheroo, variante=""):
    """Phrase qui décrit les cartes graphiques du PC et dit comment choisir celle d'un jeu."""
    if not cartes:
        return "La carte graphique de ce PC n'a pas pu être identifiée."
    noms = [carte["nom"] for carte in cartes]
    if len(cartes) == 1:
        texte = f"Carte graphique : {noms[0]}."
    else:
        defaut = next((c["nom"] for c in cartes if c["defaut"]), None)
        texte = "Ce PC a plusieurs cartes graphiques : " + " ; ".join(noms) + "."
        if defaut:
            texte += f" Par défaut, {defaut} est utilisée (elle économise la batterie)."
        if via_switcheroo:
            texte += (" Pour lancer un jeu avec la carte la plus puissante : clic droit sur son icône, puis "
                      "« Lancer avec la carte graphique dédiée ».")
    if any("nvidia" in nom.lower() for nom in noms) and variante != "nvidia":
        texte += (" Les pilotes libres suffisent à la bureautique et à beaucoup de jeux ; pour les jeux 3D "
                  "exigeants, un administrateur peut choisir la variante NVIDIA de NicOS (pilotes officiels, "
                  "encore expérimentale).")
    return texte


def variante():
    """VARIANT_ID de /etc/os-release (« nvidia » pour l'image nicos-nvidia), sinon chaîne vide."""
    try:
        with open("/etc/os-release", encoding="utf-8") as fichier:
            for ligne in fichier:
                if ligne.startswith("VARIANT_ID="):
                    return ligne.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


class Page(QWidget):
    def __init__(self, centre):
        super().__init__()
        self.centre = centre
        self.cartes = []
        self.erreur = ""
        try:
            entrees = catalogue.charger()
        except (OSError, ValueError) as erreur:
            entrees = []
            self.erreur = str(erreur)
        installees = launch.installed_flatpaks()
        fournies = catalogue.fournies()

        contenu, page = widgets.page_de_cartes()
        page.addWidget(widgets.entete(
            "Jeux", "NicOS fait tourner beaucoup de jeux Windows grâce à Proton, intégré à Steam. Rien n'est "
                    "installé d'office : choisissez la boutique que vous utilisiez.", ICONE, ACCENT))

        page.addWidget(widgets.section("Mes boutiques et mes outils", ACCENT))
        if self.erreur:
            page.addWidget(QLabel(f"Le catalogue n'a pas pu être lu : {self.erreur}"))
        for remplacant in catalogue.remplacants(entrees, CATEGORIE):
            badge, bouton, action = catalogue.etat(remplacant.entree, installees, fournies)
            carte = widgets.carte(
                f"{remplacant.nom}   <span style='font-weight:400; font-size:9pt;'>· {badge}</span>",
                remplacant.entree.remarque, bouton, (lambda _=False, a=action: launch.executer(a)) if action else None,
                details="Remplace : " + ", ".join(remplacant.remplace), icone=ICONE, couleurs=ACCENT)
            self.cartes.append(carte)
            page.addWidget(carte)

        page.addWidget(widgets.section("Mon matériel", ACCENT))
        cartes, via_switcheroo = materiel.cartes_graphiques()
        page.addWidget(widgets.carte("Carte graphique", texte_cartes(cartes, via_switcheroo, variante()),
                                     "Écrans", lambda: launch.open_settings("kcm_kscreen"),
                                     icone="monitor", couleurs=theme.ACCENTS["indigo"]))
        page.addWidget(widgets.carte("Manettes", "Branchez la manette, puis testez ses boutons et réglez-la.",
                                     "Ouvrir les manettes", lambda: launch.open_settings("kcm_gamecontroller"),
                                     icone="gamepad", couleurs=theme.ACCENTS["violet"]))
        page.addWidget(widgets.carte("Un jeu ne démarre pas ?",
                                     "ProtonDB recense, jeu par jeu, ce qui marche sous Linux et les réglages à "
                                     "essayer. Les retours viennent de joueurs, sans garantie.",
                                     "Ouvrir ProtonDB", lambda: launch.open_url(PROTONDB),
                                     icone="life-buoy", couleurs=theme.ACCENTS["orange"]))
        page.addStretch(1)
        widgets.remplir(self, contenu)


def build(centre):
    return Page(centre)
