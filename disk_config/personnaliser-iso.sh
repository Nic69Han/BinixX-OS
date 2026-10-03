#!/usr/bin/bash
# Retire Fedora de ce que l'utilisateur voit de l'ISO : nom du volume et installeur.
#
# Usage : disk_config/personnaliser-iso.sh <install.iso>   (l'ISO est remplacée)
#
# 1. Nom du volume. bootc-image-builder nomme l'ISO d'après l'ID de os-release
#    (« Fedora-S-dvd-x86_64-44 ») : c'est le nom de la clé USB affiché par l'ordinateur. Il devient
#    « BinixX-OS-44-x86_64 ». Le menu de démarrage s'en sert pour retrouver l'installeur
#    (inst.stage2=hd:LABEL=…, inst.ks=…, search -l …) : il est remplacé dans les grub.cfg de l'ISO
#    et dans celui de l'image de démarrage UEFI (efiboot.img, FAT, modifiée avec mtools), comme le
#    fait mkksiso de Fedora avec --volid. Éditeur et application de l'ISO deviennent « BinixX OS ».
# 2. Logo et couleurs de l'installeur. bootc-image-builder le construit avec fedora-logos et n'a pas
#    d'option de marque. Anaconda prévoit images/product.img sur le support : son initramfs le
#    décompresse par-dessus l'installeur (anaconda-lib.sh, anaconda_auto_updates), puis
#    l'interface charge /run/install/product/anaconda-gtk.css après le style de Fedora, avec une
#    priorité plus haute. Contenu : branding/installeur/ (généré par branding/generer.py).
#
# L'ISO est réécrite par xorriso en rejouant son démarrage (BIOS, UEFI et Secure Boot), puis sa
# somme de contrôle interne (entrée « Test this media » du menu) est recalculée. Le script relit
# l'ISO produite et échoue s'il y reste l'ancien nom ou « Fedora » dans un titre du menu.
# Prérequis : xorriso, mtools, cpio, gzip, implantisomd5 et checkisomd5 (paquet isomd5sum).

set -euo pipefail

ISO="${1:-}"
[[ -f "${ISO}" ]] || { echo "Usage : $0 <install.iso>" >&2 && exit 2; }
fail() { echo "ÉCHEC : $*" >&2 && exit 1; }
for cmd in xorriso mcopy mtype cpio gzip implantisomd5 checkisomd5; do
    command -v "${cmd}" >/dev/null || fail "commande manquante : ${cmd}"
done
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/branding/installeur"
[[ -s "${SOURCE}/run/install/product/anaconda-gtk.css" ]] || fail "${SOURCE} incomplet : lancer branding/generer.py"
export MTOOLS_SKIP_CHECK=1 # image FAT sans géométrie de disquette

work="$(mktemp -d "$(dirname "${ISO}")/.personnaliser-iso.XXXXXX")"
trap 'rm -rf "${work}"' EXIT

volume_id() { xorriso -indev "$1" -pvd_info 2>/dev/null | sed -n 's/^Volume Id *: //p'; }

# Zone de l'image de démarrage UEFI : 2e partition ajoutée à l'ISO (début et nombre de blocs de
# 512 octets), d'après le rapport de xorriso ; vide si l'ISO n'en a pas
efi_partition() {
    xorriso -indev "$1" -report_el_torito as_mkisofs 2>/dev/null |
        sed -n "s/^-append_partition 2 [^ ]* --interval:local_fs:\([0-9]*\)d-\([0-9]*\)d::.*/\1 \2/p" |
        awk '{ print $1, $2 - $1 + 1 }'
}

# Copie du fichier /<chemin> de l'ISO dans <destination> ; échoue s'il n'existe pas
extract() { xorriso -osirrox on -indev "$1" -extract "/$2" "$3" >/dev/null 2>&1 && chmod u+w "$3"; }

### 1. Nom du volume ---------------------------------------------------------------

old_label="$(volume_id "${ISO}")"
if [[ "${old_label}" =~ ^Fedora-S-dvd-(.+)-([0-9]+)$ ]]; then
    new_label="BinixX-OS-${BASH_REMATCH[2]}-${BASH_REMATCH[1]}"
elif [[ "${old_label}" == BinixX-OS-* ]]; then
    new_label="${old_label}" # ISO déjà personnalisée
else
    fail "nom de volume inattendu : '${old_label}' (bootc-image-builder a changé ?)"
fi
echo "Nom du volume : ${old_label} -> ${new_label}"

xorriso_args=(-volid "${new_label}" -volset_id "${new_label}" -publisher "BinixX OS" -application_id "BinixX OS")

# Menus GRUB de l'ISO : UEFI (EFI/BOOT) et BIOS (boot/grub2)
configs=0
for cfg in EFI/BOOT/grub.cfg boot/grub2/grub.cfg; do
    mkdir -p "${work}/iso/$(dirname "${cfg}")"
    extract "${ISO}" "${cfg}" "${work}/iso/${cfg}" || continue
    sed -i "s/${old_label}/${new_label}/g" "${work}/iso/${cfg}"
    xorriso_args+=(-update "${work}/iso/${cfg}" "/${cfg}")
    configs=$((configs + 1))
done
[[ ${configs} -gt 0 ]] || fail "aucun menu GRUB dans l'ISO"

# Image de démarrage UEFI (FAT) : sa propre copie du menu
read -r efi_start efi_count <<<"$(efi_partition "${ISO}")" || true
[[ -n "${efi_start:-}" ]] || fail "image de démarrage UEFI introuvable (2e partition de l'ISO)"
dd if="${ISO}" of="${work}/efiboot.img" bs=512 skip="${efi_start}" count="${efi_count}" status=none
mkdir -p "${work}/efi"
mcopy -s -n -i "${work}/efiboot.img" ::/ "${work}/efi/"
while IFS= read -r -d '' file; do
    case "${file}" in
    *.cfg | *.conf) ;;
    *) fail "ancien nom dans un fichier binaire de l'image UEFI : ${file#"${work}"/efi/}" ;;
    esac
    sed -i "s/${old_label}/${new_label}/g" "${file}"
    mcopy -o -i "${work}/efiboot.img" "${file}" "::/${file#"${work}"/efi/}"
done < <(grep -rlZF -- "${old_label}" "${work}/efi" || true)
# Même partition EFI au même emplacement (type ESP), et copie éventuelle dans l'arborescence
xorriso_args+=(-append_partition 2 C12A7328-F81F-11D2-BA4B-00A0C93EC93B "${work}/efiboot.img")
if extract "${ISO}" images/efiboot.img "${work}/efiboot-arbre.img"; then
    xorriso_args+=(-update "${work}/efiboot.img" /images/efiboot.img)
fi

### 2. Logo et couleurs de l'installeur ------------------------------------------------

# product.img : archive cpio compressée, fichiers à root, dans un ordre stable
(cd "${SOURCE}" && find . -mindepth 1 -print0 | LC_ALL=C sort -z |
    cpio --quiet --null --create --format=newc --owner=0:0 --reproducible) | gzip -9n >"${work}/product.img"
echo "product.img : $(stat -c %s "${work}/product.img") octets"
xorriso_args+=(-map "${work}/product.img" /images/product.img)

### 3. Nouvelle ISO, vérifiée ----------------------------------------------------------

xorriso -indev "${ISO}" -outdev "${work}/binixx.iso" -boot_image any replay "${xorriso_args[@]}"
implantisomd5 --force "${work}/binixx.iso" >/dev/null
checkisomd5 "${work}/binixx.iso" >/dev/null || fail "somme de contrôle de la nouvelle ISO invalide"

[[ "$(volume_id "${work}/binixx.iso")" == "${new_label}" ]] || fail "nom de volume non appliqué"
if xorriso -indev "${work}/binixx.iso" -pvd_info 2>/dev/null | grep -i fedora; then
    fail "« Fedora » reste dans l'identité de l'ISO (ci-dessus)"
fi
mkdir -p "${work}/verif"
for cfg in EFI/BOOT/grub.cfg boot/grub2/grub.cfg; do
    extract "${work}/binixx.iso" "${cfg}" "${work}/verif/${cfg//\//_}" || continue
done
read -r efi_start efi_count <<<"$(efi_partition "${work}/binixx.iso")" || true
[[ -n "${efi_start:-}" ]] || fail "image de démarrage UEFI absente de la nouvelle ISO"
dd if="${work}/binixx.iso" of="${work}/verif/efiboot.img" bs=512 skip="${efi_start}" count="${efi_count}" status=none
mtype -i "${work}/verif/efiboot.img" ::/EFI/BOOT/grub.cfg >"${work}/verif/efiboot_grub.cfg"
if grep -F -- "${old_label}" "${work}"/verif/*.cfg; then
    fail "l'ancien nom de volume reste dans le menu de démarrage (ci-dessus)"
fi
grep -qF "hd:LABEL=${new_label}" "${work}/verif/efiboot_grub.cfg" ||
    fail "le menu UEFI ne désigne pas le nouveau volume"
# Titres affichés du menu (menuentry, submenu) ; « --class fedora » n'est qu'une icône de thème
if grep -hE "^[[:space:]]*(menuentry|submenu)" "${work}"/verif/*.cfg | sed 's/--class [^ ]*//g' | grep -i fedora; then
    fail "« Fedora » dans un titre du menu de démarrage (ci-dessus)"
fi
xorriso -indev "${work}/binixx.iso" -find /images/product.img 2>/dev/null | grep -q product.img ||
    fail "product.img absent de la nouvelle ISO"

mv -f "${work}/binixx.iso" "${ISO}"
echo "ISO personnalisée : volume ${new_label}, installeur aux couleurs de BinixX OS : ${ISO}"
