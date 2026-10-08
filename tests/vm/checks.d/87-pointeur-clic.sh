# shellcheck shell=bash
# Souris comme sous Windows : double-clic pour ouvrir et pointeur blanc, tels que la session de l'utilisateur de test les lit (le contrôle
# des ambiances, qui passe avant, a pu écrire le thème de pointeur : il doit rester Breeze_Light).
pointeur_session() {
    local uid
    uid="$(id -u "${TEST_USER}")"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"
}

check_pointeur_clic() {
    section "Souris comme sous Windows (double-clic, pointeur blanc)"
    local valeur
    valeur="$(pointeur_session kreadconfig6 --file kdeglobals --group KDE --key SingleClick)"
    if [[ "${valeur}" == false ]]; then pass "kdeglobals : SingleClick=false (double-clic pour ouvrir)"; else fail "SingleClick='${valeur}' (false attendu)"; fi
    valeur="$(pointeur_session kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme)"
    if [[ "${valeur}" == Breeze_Light ]]; then pass "kcminputrc : pointeur ${valeur} (flèche blanche)"; else fail "cursorTheme='${valeur}' (Breeze_Light attendu)"; fi
    check "le thème de pointeur Breeze_Light est installé" test -e /usr/share/icons/Breeze_Light/cursors/left_ptr
}
register_check base check_pointeur_clic

# Après la mise à jour et le redémarrage : les deux réglages sont toujours là (ils viennent de /etc/xdg, fusionné par ostree)
check_pointeur_clic_apres_mise_a_jour() {
    section "Souris comme sous Windows (après la mise à jour)"
    local valeur
    valeur="$(pointeur_session kreadconfig6 --file kdeglobals --group KDE --key SingleClick)"
    if [[ "${valeur}" == false ]]; then pass "double-clic toujours en place"; else fail "SingleClick='${valeur}' après la mise à jour (false attendu)"; fi
    valeur="$(pointeur_session kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme)"
    if [[ "${valeur}" == Breeze_Light ]]; then pass "pointeur blanc toujours en place"; else fail "cursorTheme='${valeur}' après la mise à jour (Breeze_Light attendu)"; fi
}
register_check after-update check_pointeur_clic_apres_mise_a_jour
