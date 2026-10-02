# shellcheck shell=bash
section "Variante de l'image"
# shellcheck source=/dev/null  # fichier de l'image, absent du dépôt
variant_id="$(. /usr/lib/os-release && echo "${VARIANT_ID:-}")"
case "${variant_id}" in
nvidia)
    pass "variante NVIDIA"
    check "pilotes NVIDIA présents" bash -c 'rpm -qa | grep -qi nvidia'
    # shellcheck disable=SC2016  # expansion voulue dans le sous-shell
    check "NicOS reste NicOS (nom, logo)" bash -c '. /usr/lib/os-release && [[ "${NAME}" == NicOS && "${LOGO}" == nicos ]]'
    ;;
"") pass "variante standard" ;;
*) fail "variante inconnue : ${variant_id}" ;;
esac
