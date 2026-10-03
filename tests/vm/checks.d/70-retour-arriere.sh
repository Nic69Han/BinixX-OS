# shellcheck shell=bash
check_retour_arriere() {
    section "Retour arrière automatique (greenboot)"
    check "contrôles de démarrage de greenboot terminés" systemctl is-active greenboot-healthcheck.service
    check "contrôle de l'écran de connexion en place" test -x /etc/greenboot/check/required.d/10-binixx-connexion.sh
    check "contrôles par défaut (DNS des dépôts) absents" bash -c '! rpm -q greenboot-default-health-checks'
    if grub2-editenv list >/dev/null 2>&1; then
        check "démarrage déclaré réussi au chargeur de démarrage (boot_success=1)" bash -c 'grub2-editenv list | grep -qx "boot_success=1"'
    else
        warn "grub2-editenv ne lit pas l'environnement du chargeur de démarrage"
    fi
}
register_check base check_retour_arriere

check_retour_automatique() {
    section "Retour arrière automatique après une mise à jour défectueuse"
    check "version précédente de nouveau démarrée (témoin de la mise à jour défectueuse absent)" \
        test ! -e /usr/share/binixx/update-bad-marker
    local image
    image="$(booted_image)"
    if [[ "${image}" != *update-bad* ]]; then pass "image démarrée : ${image}"; else fail "image démarrée : la mise à jour défectueuse (${image})"; fi
    local tries
    tries="$(wc -l </var/log/binixx-test-boots 2>/dev/null || echo 0)"
    if [[ "${tries}" -ge 2 && "${tries}" -le 5 ]]; then
        pass "greenboot a essayé ${tries} fois la mise à jour défectueuse avant de revenir en arrière"
    else
        fail "démarrages de la mise à jour défectueuse : ${tries} (attendu : 3)"
    fi
    journalctl -b -1 -u greenboot-healthcheck.service --no-pager -o cat 2>/dev/null | tail -n 12 | sed 's/^/            /' || true
}
register_check after-auto-rollback check_retour_automatique
