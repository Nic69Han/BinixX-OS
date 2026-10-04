#!/usr/bin/bash
# Démarrage « à la Windows » (docs/demarrage.md) : l'écran de démarrage vient des paramètres du noyau
# (system_files/usr/lib/bootc/kargs.d) ; ici, le service qui rend le menu GRUB discret après un démarrage réussi.

set -ouex pipefail

bash -n /usr/libexec/binixx/binixx-menu-grub
test -x /usr/libexec/binixx/binixx-menu-grub
systemctl enable binixx-menu-grub.service
