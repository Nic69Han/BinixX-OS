#!/usr/bin/bash
# Raccourcis clavier : une touche que BinixX OS annonce (usr/share/binixx/raccourcis/raccourcis.tsv, source « binixx »)
# n'a qu'un propriétaire. Un lanceur de KDE (Spectacle, Configuration du système…) qui déclare la même touche dans son
# fichier .desktop la perdrait au profit de BinixX OS : sinon KDE donne la touche à l'un des deux, au hasard de l'ordre de
# démarrage, et « Windows + R » ouvrirait parfois autre chose. Le résultat s'écrit en bas de /etc/xdg/kglobalshortcutsrc.

set -ouex pipefail

/usr/libexec/binixx/binixx-raccourcis surcharger
# Plus aucun conflit ne doit rester : sinon le build échoue
/usr/libexec/binixx/binixx-raccourcis surcharger --verifier
