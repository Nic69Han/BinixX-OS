# shellcheck shell=bash
# Barre des tâches : on la déplace pour de vrai dans la session de l'utilisateur de test (Plasma tourne), on vérifie
# qu'elle change, que le choix est écrit dans la configuration du bureau, puis on la remet en haut (disposition d'origine).
check_barre() {
    section "Barre des tâches (déplacement réel dans la session)"
    local uid out outil=/usr/libexec/binixx/binixx-barre config="${TEST_HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc"
    uid="$(id -u "${TEST_USER}")"
    session() { runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"; }
    position_est() { [[ "$(session "${outil}" etat 2>/dev/null)" == "$1" ]]; }
    enregistree_est() { # la position écrite dans la configuration du bureau
        [[ "$(python3 -c "import sys; sys.path.insert(0, '/usr/lib/binixx/centre'); from binixx_centre import barre; print(barre.position_dans_configuration(sys.argv[1]))" "${config}" 2>/dev/null)" == "$1" ]]
    }
    if ! wait_for 120 session busctl --user status org.kde.plasmashell; then
        fail "Plasma ne répond pas sur le bus de la session : la barre ne peut pas être déplacée"
        return
    fi
    if wait_for 30 position_est haut; then pass "au départ la barre est en haut"; else fail "position de départ : $(session "${outil}" etat 2>&1)"; fi

    out="$(session "${outil}" bas 2>&1)" && pass "binixx-barre bas : ${out}" || fail "binixx-barre bas : ${out}"
    if wait_for 30 position_est bas; then pass "Plasma confirme : la barre est en bas"; else fail "la barre n'est pas passée en bas : $(session "${outil}" etat 2>&1)"; fi
    if wait_for 120 enregistree_est bas; then
        pass "le choix est écrit dans la configuration du bureau (il survivra à la session)"
    else
        warn "position non encore écrite dans ${config##*/} après 2 minutes"
    fi

    out="$(session "${outil}" haut 2>&1)" && pass "binixx-barre haut : ${out}" || fail "binixx-barre haut : ${out}"
    if wait_for 30 position_est haut; then pass "la barre est revenue en haut"; else fail "la barre est restée : $(session "${outil}" etat 2>&1)"; fi
    wait_for 120 enregistree_est haut || warn "retour en haut non encore écrit dans la configuration"
}
register_check base check_barre
