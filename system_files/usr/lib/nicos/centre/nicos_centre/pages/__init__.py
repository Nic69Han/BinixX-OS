"""Pages du Centre NicOS : chaque module de ce dossier apporte une page.

Un module définit  ORDER (position dans la barre latérale), KEY (identifiant, pour --page),
TITLE (texte du bouton) et  build(centre) -> QWidget. Ajouter une page = ajouter un fichier.
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
