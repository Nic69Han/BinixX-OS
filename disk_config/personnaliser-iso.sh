#!/usr/bin/bash
# Donne à l'installeur de l'ISO le logo et les couleurs de NicOS, à la place de ceux de Fedora.
#
# Usage : disk_config/personnaliser-iso.sh <install.iso>   (l'ISO est remplacée)
#
# bootc-image-builder construit l'installeur (Anaconda) avec les paquets de Fedora, dont
# fedora-logos, et n'a pas d'option de marque. Anaconda prévoit pour cela images/product.img
# sur le support d'installation : son initramfs le décompresse par-dessus le système de
# l'installeur (anaconda-lib.sh, anaconda_auto_updates), puis l'interface charge
# /run/install/product/anaconda-gtk.css après le style de Fedora, avec une priorité plus haute.
# Contenu de product.img : branding/installeur/ (généré par branding/generer.py).
#
# L'ISO est réécrite par xorriso en rejouant son démarrage à l'identique (BIOS, UEFI et Secure
# Boot, étiquette du volume), comme le fait mkksiso de Fedora ; sa somme de contrôle interne
# (entrée « Test this media » du menu) est ensuite recalculée.
# Prérequis : xorriso, cpio, gzip, implantisomd5 et checkisomd5 (paquet isomd5sum).

set -euo pipefail

ISO="${1:-}"
[[ -f "${ISO}" ]] || { echo "Usage : $0 <install.iso>" >&2 && exit 2; }
for cmd in xorriso cpio gzip implantisomd5 checkisomd5; do
    command -v "${cmd}" >/dev/null || { echo "commande manquante : ${cmd}" >&2 && exit 1; }
done
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/branding/installeur"
[[ -s "${SOURCE}/run/install/product/anaconda-gtk.css" ]] || {
    echo "${SOURCE} incomplet : lancer branding/generer.py" >&2 && exit 1
}

work="$(mktemp -d "$(dirname "${ISO}")/.personnaliser-iso.XXXXXX")"
trap 'rm -rf "${work}"' EXIT

# product.img : archive cpio compressée, fichiers à root, dans un ordre stable
(cd "${SOURCE}" && find . -mindepth 1 -print0 | LC_ALL=C sort -z |
    cpio --quiet --null --create --format=newc --owner=0:0 --reproducible) | gzip -9n >"${work}/product.img"
echo "product.img : $(stat -c %s "${work}/product.img") octets"

xorriso -indev "${ISO}" -outdev "${work}/nicos.iso" \
    -boot_image any replay \
    -map "${work}/product.img" /images/product.img

implantisomd5 --force "${work}/nicos.iso"
checkisomd5 "${work}/nicos.iso" >/dev/null || { echo "somme de contrôle de l'ISO invalide" >&2 && exit 1; }
mv -f "${work}/nicos.iso" "${ISO}"
echo "Installeur aux couleurs de NicOS : ${ISO}"
