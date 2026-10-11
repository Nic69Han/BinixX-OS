#!/usr/bin/bash
# Variante de l'image, selon BINIXX_VARIANT (argument de build du Containerfile) :
#   (vide)  BinixX OS standard (pilote graphique libre nouveau pour les cartes NVIDIA)
#   nvidia  BinixX OS sur la base Universal Blue « kinoite-nvidia » : pilotes NVIDIA propriétaires, déjà signés
#           pour Secure Boot par Universal Blue. docs/nvidia.md

set -ouex pipefail

case "${BINIXX_VARIANT:-}" in
"") ;;
nvidia)
    # Liste d'abord, test ensuite : `grep -q` dans un tube fait échouer rpm (SIGPIPE) sous pipefail
    nvidia_packages="$(rpm -qa | grep -i nvidia | sort || true)"
    echo "Paquets NVIDIA de la base :"
    echo "${nvidia_packages}"
    [[ -n "${nvidia_packages}" ]] || {
        echo "Aucun paquet NVIDIA dans la base : la variante n'a pas de sens" >&2
        exit 1
    }
    # Identifie la variante dans « À propos » et dans le rapport de diagnostic (os-release)
    sed -i -e '/^VARIANT=/d' -e '/^VARIANT_ID=/d' /usr/lib/os-release
    printf 'VARIANT="NVIDIA"\nVARIANT_ID=nvidia\n' >>/usr/lib/os-release
    # Services NVIDIA de la base qui ne servent qu'avec le pilote chargé. Sans lui (Secure Boot qui refuse le pilote tant que
    # la clé d'Universal Blue n'est pas enrôlée, PC sans carte NVIDIA), ils échouent en boucle au démarrage et leurs
    # « [FAILED] » s'affichent entre l'écran de démarrage et l'écran de connexion. /sys/module/nvidia n'existe que si le
    # pilote est chargé ; l'initramfs le charge bien avant ces services.
    for unite in nvidia-persistenced.service nvidia-cdi-refresh.service; do
        if [[ ! -e "/usr/lib/systemd/system/${unite}" ]]; then
            echo "${unite} absent de la base : rien à conditionner"
            continue
        fi
        mkdir -p "/usr/lib/systemd/system/${unite}.d"
        printf '%s\n' "# BinixX OS : seulement si le pilote NVIDIA est chargé (build_files/modules.d/80-variante.sh)" \
            "[Unit]" "ConditionPathExists=/sys/module/nvidia" >"/usr/lib/systemd/system/${unite}.d/50-binixx-pilote-nvidia.conf"
    done
    ;;
*)
    echo "Variante inconnue : ${BINIXX_VARIANT}" >&2
    exit 1
    ;;
esac
