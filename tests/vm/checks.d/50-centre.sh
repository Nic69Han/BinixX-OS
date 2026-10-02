# shellcheck shell=bash
check_centre() {
    section "Centre NicOS (accueil à la première session)"
    if wait_for 180 pgrep -u "${TEST_USER}" -f /usr/libexec/nicos/nicos-centre; then
        pass "l'accueil NicOS s'est ouvert tout seul"
    else
        fail "l'accueil NicOS n'est pas lancé"
    fi
    check "première ouverture mémorisée (l'accueil ne reviendra pas)" test -f "${TEST_HOME}/.config/nicos/accueil-vu"
    check "centre de bienvenue de KDE non lancé" bash -c "! pgrep -u '${TEST_USER}' -x plasma-welcome"
}
register_check base check_centre
