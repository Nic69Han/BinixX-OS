#!/usr/bin/bash
# Windows dans une machine virtuelle (page « Windows complet » du Centre BinixX OS).
# - Boxes (Flatpak, installé à la demande) n'a besoin de rien de plus dans l'image.
# - WinBoat (projet libre MIT, en bêta, que l'utilisateur télécharge lui-même : il n'est pas sur Flathub) pilote
#   Windows dans un conteneur Podman et affiche ses fenêtres avec FreeRDP 3 : Podman est dans l'image de base,
#   on ajoute Podman Compose et FreeRDP. Aucun Windows n'est fourni : la licence reste à acquérir.

set -ouex pipefail

dnf5 -y install freerdp podman-compose
rpm -q freerdp podman-compose
command -v podman
command -v podman-compose
# FreeRDP 3 est exigé par WinBoat (xfreerdp3 ou xfreerdp) ; on relit la version plutôt que de la supposer
version="$(xfreerdp --version 2>&1 || true)"
echo "${version}"
if ! grep -q 'version 3\.' <<<"${version}"; then
    echo "FreeRDP 3 attendu pour WinBoat" >&2
    exit 1
fi
