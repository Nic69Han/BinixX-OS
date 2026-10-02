#!/usr/bin/bash
# Variante de l'image, selon NICOS_VARIANT (argument de build du Containerfile) :
#   (vide)  NicOS standard (pilote graphique libre nouveau pour les cartes NVIDIA)
#   nvidia  NicOS sur la base Universal Blue « kinoite-nvidia » : pilotes NVIDIA propriétaires, déjà signés
#           pour Secure Boot par Universal Blue. docs/nvidia.md

set -ouex pipefail

case "${NICOS_VARIANT:-}" in
"") ;;
nvidia)
    echo "Paquets NVIDIA de la base :"
    rpm -qa | grep -i nvidia | sort
    rpm -qa | grep -qi nvidia || {
        echo "Aucun paquet NVIDIA dans la base : la variante n'a pas de sens" >&2
        exit 1
    }
    # Identifie la variante dans « À propos » et dans le rapport de diagnostic (os-release)
    sed -i -e '/^VARIANT=/d' -e '/^VARIANT_ID=/d' /usr/lib/os-release
    printf 'VARIANT="NVIDIA"\nVARIANT_ID=nvidia\n' >>/usr/lib/os-release
    ;;
*)
    echo "Variante inconnue : ${NICOS_VARIANT}" >&2
    exit 1
    ;;
esac
