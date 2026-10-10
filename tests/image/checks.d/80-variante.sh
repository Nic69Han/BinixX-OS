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
    # Sans pilote chargé, ces services échoueraient en boucle et s'afficheraient au démarrage (build_files/modules.d/80-variante.sh)
    for unite in nvidia-persistenced.service nvidia-cdi-refresh.service; do
        [[ -e "/usr/lib/systemd/system/${unite}" ]] || continue
        check "${unite} : seulement avec le pilote NVIDIA chargé" \
            grep -qx 'ConditionPathExists=/sys/module/nvidia' "/usr/lib/systemd/system/${unite}.d/50-binixx-pilote-nvidia.conf"
    done
    ;;
"" | kinoite) pass "variante standard (VARIANT_ID : ${variant_id:-aucun})" ;; # kinoite : valeur de la base Fedora
*) fail "variante inconnue : ${variant_id}" ;;
esac
