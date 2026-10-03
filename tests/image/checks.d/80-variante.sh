# shellcheck shell=bash
section "Variante de l'image"
# shellcheck source=/dev/null  # fichier de l'image, absent du dépôt
variant_id="$(. /usr/lib/os-release && echo "${VARIANT_ID:-}")"
case "${variant_id}" in
nvidia)
    pass "variante NVIDIA"
    check "pilotes NVIDIA présents" rpm -q nvidia-driver kmod-nvidia
    # shellcheck disable=SC2016  # expansion voulue dans le sous-shell
    check "BinixX OS reste BinixX OS (nom, logo)" bash -c '. /usr/lib/os-release && [[ "${NAME}" == "BinixX OS" && "${LOGO}" == binixx ]]'
    ;;
"" | kinoite) pass "variante standard (VARIANT_ID : ${variant_id:-aucun})" ;; # kinoite : valeur de la base Fedora
*) fail "variante inconnue : ${variant_id}" ;;
esac
