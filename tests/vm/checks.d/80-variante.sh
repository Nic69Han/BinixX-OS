# shellcheck shell=bash
# Variante NVIDIA sans pilote NVIDIA chargé, comme dans la VM (pas de carte NVIDIA) ou sur un PC dont Secure Boot refuse le pilote
# tant que la clé d'Universal Blue n'est pas enrôlée : les services NVIDIA ne démarrent pas. Sans cela, ils échouaient en boucle
# et leurs « [FAILED] » s'affichaient entre l'écran de démarrage et l'écran de connexion (build_files/modules.d/80-variante.sh).
check_variante_nvidia() {
    # shellcheck source=/dev/null  # fichier du système testé
    [[ "$(. /usr/lib/os-release && echo "${VARIANT_ID:-}")" == nvidia ]] || return 0
    section "Variante NVIDIA sans pilote chargé"
    if [[ -e /sys/module/nvidia ]]; then
        warn "pilote NVIDIA chargé : services NVIDIA non vérifiés"
        return 0
    fi
    pass "pilote NVIDIA non chargé (pas de carte NVIDIA, ou pilote refusé par Secure Boot)"
    local unite
    for unite in nvidia-persistenced.service nvidia-cdi-refresh.service; do
        systemctl cat "${unite}" >/dev/null 2>&1 || continue
        # shellcheck disable=SC2016  # expansion voulue dans le sous-shell
        check "${unite} : écarté au démarrage, pas en échec" bash -c \
            '! systemctl is-failed --quiet "$1" && [[ -n "$(systemctl show -P ConditionTimestamp "$1")" && "$(systemctl show -P ConditionResult "$1")" == no ]]' \
            _ "${unite}"
    done
}
register_check base check_variante_nvidia
register_check after-update check_variante_nvidia
