"""Pages du Centre BinixX OS : chaque module de ce dossier apporte une page.

Un module définit  ORDER (position dans la barre latérale), KEY (identifiant, pour --page),
TITLE (texte du bouton) et  build(centre) -> QWidget. Ajouter une page = ajouter un fichier.

Une page peut aussi donner ICONE (nom d'une icône de icones.py) et ACCENT (un couple de theme.ACCENTS) : la barre
latérale en fait la pastille du bouton, et la page reprend la même couleur pour son en-tête (widgets.entete).

Une page peut n'avoir aucun bouton dans la barre latérale (MENU = False) : on l'ouvre depuis une autre page ou avec
--page, et le bouton de sa page parente (PARENT = clé de cette page) reste allumé.
"""

import importlib
import pkgutil


def discover():
    """Modules de pages, dans l'ordre d'affichage."""
    modules = []
    for info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{info.name}")
        if all(hasattr(module, name) for name in ("ORDER", "KEY", "TITLE", "build")):
            modules.append(module)
    return sorted(modules, key=lambda module: module.ORDER)
