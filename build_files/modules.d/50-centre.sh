#!/usr/bin/bash
# Centre NicOS (accueil, catalogue des logiciels Windows, aide) : application Python (PySide6, déjà
# dans l'image de base), copiée par la section 1 de build.sh. Le bytecode est préparé ici : /usr est
# en lecture seule sur un poste installé, Python ne pourrait pas l'écrire au premier lancement.

set -ouex pipefail

rpm -q python3-pyside6
python3 -m compileall -q /usr/lib/nicos/centre
