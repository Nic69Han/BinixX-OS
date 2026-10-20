# shellcheck shell=bash
# Mémoire vive d'une session au repos, juste après la connexion (VM de 4 Go, comme un vieux PC) : chiffre de référence pour alléger
# BinixX OS (docs/memoire.md). Phase « memoire », lancée par run-vm-test.sh après un redémarrage, avant toute autre fenêtre.
# Le relevé s'imprime toujours : réglages de la mémoire, services et applications de session avec leur mémoire, puis le résumé
# « RELEVÉ MÉMOIRE ». Le budget n'avertit que tant qu'il n'est pas calibré sur plusieurs passages ; l'échec ne vient qu'au-delà de
# MEMOIRE_ECHEC_MO (session manifestement cassée ou fuite).
MEMOIRE_BUDGET_MO="${MEMOIRE_BUDGET_MO:-1500}"
MEMOIRE_ECHEC_MO="${MEMOIRE_ECHEC_MO:-3000}"

memoire_indente() { sed 's/^/            /'; }

# Mémoire de chaque service en cours (cgroup : MemoryCurrent), du plus gros au plus petit. memoire_services [--user]
memoire_services() {
    local unite octets
    systemctl "$@" list-units --type=service --state=running --no-legend --plain | awk '{print $1}' | while read -r unite; do
        octets="$(systemctl "$@" show -P MemoryCurrent "${unite}" 2>/dev/null)"
        [[ "${octets}" =~ ^[0-9]+$ ]] && awk -v o="${octets}" -v u="${unite}" 'BEGIN{printf "%8.1f Mo  %s\n", o / 1048576, u}'
    done | sort -rn | head -n 25
}

releve_reglages_memoire() {
    section "Mémoire : réglages en place (relevé)"
    echo "  mémoire d'échange (zram) :"
    {
        zramctl 2>&1
        swapon --show 2>&1
    } | memoire_indente
    echo "  configuration du zram (zram-generator) :"
    systemd-analyze cat-config systemd/zram-generator.conf 2>&1 | grep -v '^#' | grep . | memoire_indente
    echo "  noyau :"
    sysctl vm.swappiness vm.page-cluster vm.vfs_cache_pressure vm.dirty_ratio vm.dirty_background_ratio vm.watermark_scale_factor \
        2>&1 | memoire_indente
    printf 'transparent_hugepage=%s ; lru_gen=%s min_ttl_ms=%s ; ksm=%s\n' \
        "$(cat /sys/kernel/mm/transparent_hugepage/enabled 2>&1)" "$(cat /sys/kernel/mm/lru_gen/enabled 2>&1)" \
        "$(cat /sys/kernel/mm/lru_gen/min_ttl_ms 2>&1)" "$(cat /sys/kernel/mm/ksm/run 2>&1)" | memoire_indente
    echo "  systemd-oomd : $(systemctl is-active systemd-oomd 2>&1) ; configuration :"
    systemd-analyze cat-config systemd/oomd.conf 2>&1 | grep -v '^#' | grep . | memoire_indente
    oomctl 2>&1 | grep -E 'Path:|Limit|Pressure' | head -n 12 | memoire_indente
    echo "  /tmp : $(findmnt -no FSTYPE,OPTIONS /tmp 2>&1)"
    echo "  journal en mémoire (/run/log/journal) : $(du -sh /run/log/journal 2>/dev/null | cut -f1)"
    echo "  paquets présents (candidats à l'allègement) :"
    rpm -q abrt mcelog smartmontools ModemManager cups-browsed tuned tuned-ppd power-profiles-daemon PackageKit sssd \
        kdeconnectd baloo-file akonadi-server plasma-discover-notifier kwalletmanager 2>&1 | memoire_indente
    echo "  lancés avec chaque session (autostart, sans Hidden=true) :"
    grep -L -i '^Hidden=true' /etc/xdg/autostart/*.desktop 2>/dev/null | xargs -r -n1 basename | memoire_indente
    echo "  indexation des fichiers (Baloo) :"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/$(id -u "${TEST_USER}")" balooctl6 status 2>&1 | head -n 6 |
        memoire_indente
}

mesurer_memoire() {
    local uid
    uid="$(id -u "${TEST_USER}")"
    section "Mémoire de la session au repos"
    if ! wait_for 300 pgrep -u "${TEST_USER}" -x plasmashell; then
        fail "session Plasma de ${TEST_USER} absente : pas de mesure"
        return
    fi
    # Repos : charge sur une minute sous 0,5 (4 minutes au plus), puis 30 s de plus pour les démarrages différés de la session
    wait_for 240 bash -c "awk '{exit !(\$1 < 0.5)}' /proc/loadavg" || warn "charge pas retombée : $(cut -d' ' -f1-3 /proc/loadavg)"
    sleep 30
    releve_reglages_memoire
    section "Mémoire de la session au repos (mesure)"
    echo "  services du système, par mémoire :"
    memoire_services --system | memoire_indente
    echo "  services de la session de ${TEST_USER}, par mémoire :"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" bash -c "$(declare -f memoire_services); memoire_services --user" |
        memoire_indente
    echo "  applications (PSS, processus du même nom réunis) :"
    /usr/libexec/binixx/binixx-memoire --top 25 | memoire_indente
    local valeurs utilise disponible echange
    valeurs="$(/usr/libexec/binixx/binixx-memoire --valeurs)"
    utilise="$(sed -n 's/^utilise=//p' <<<"${valeurs}")"
    disponible="$(sed -n 's/^disponible=//p' <<<"${valeurs}")"
    echange="$(sed -n 's/^echange_utilise=//p' <<<"${valeurs}")"
    printf '  RELEVÉ MÉMOIRE utilise=%s disponible=%s echange=%s (Mo)\n' "${utilise}" "${disponible}" "${echange}"
    if [[ -z "${utilise}" ]]; then
        fail "relevé de mémoire illisible : ${valeurs}"
    elif ((utilise > MEMOIRE_ECHEC_MO)); then
        fail "session au repos : ${utilise} Mo utilisés (au-delà de ${MEMOIRE_ECHEC_MO} Mo)"
    elif ((utilise > MEMOIRE_BUDGET_MO)); then
        warn "session au repos : ${utilise} Mo utilisés (objectif ${MEMOIRE_BUDGET_MO} Mo)"
    else
        pass "session au repos : ${utilise} Mo utilisés (objectif ${MEMOIRE_BUDGET_MO} Mo)"
    fi
}
register_check memoire mesurer_memoire
