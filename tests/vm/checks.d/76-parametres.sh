# shellcheck shell=bash
# « Paramètres » : la touche Windows + I est bien enregistrée par KDE dans la session de l'utilisateur de test
# (avertissement, pas échec : si KDE ignorait ce fichier, le menu et la recherche restent la voie normale).
check_parametres() {
    section "Paramètres (écran unique des réglages)"
    local uid out
    uid="$(id -u "${TEST_USER}")"
    check "kcmshell6 liste les modules sans session graphique" bash -c "kcmshell6 --list | grep -q '^ *kcm_kscreen'"
    out="$(runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
        busctl --user call org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel allComponents 2>&1 || true)"
    if grep -q 'nicos-parametres' <<<"${out}" || grep -q 'nicos_parametres' <<<"${out}"; then
        pass "KDE connaît le raccourci « Paramètres » (Windows + I)"
    else
        warn "KDE n'a pas enregistré le raccourci Windows + I : ${out:0:200}"
    fi
}
register_check base check_parametres
