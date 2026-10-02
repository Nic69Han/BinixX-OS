# shellcheck shell=bash
check_aide() {
    section "Aide et dépannage"
    local report
    report="$(runuser -u "${TEST_USER}" -- /usr/libexec/nicos/nicos-diagnostic 2>&1)"
    if grep -q 'Rapport de diagnostic NicOS' <<<"${report}" && grep -q 'Fin du rapport.' <<<"${report}"; then
        pass "rapport de diagnostic produit par l'utilisateur ($(wc -l <<<"${report}") lignes)"
    else
        fail "rapport de diagnostic incomplet"
    fi
    if grep -q 'NicOS' <<<"${report}" && grep -qi 'ostree' <<<"${report}"; then
        pass "rapport : nom du système et état de l'image présents"
    else
        warn "rapport : état de l'image (rpm-ostree) absent pour l'utilisateur"
    fi
    if grep -q 'inet ' <<<"${report}"; then fail "rapport : une adresse IP s'y trouve"; else pass "rapport sans adresse IP"; fi
    local state
    state="$(runuser -u "${TEST_USER}" -- bash -c '
        /usr/libexec/nicos/nicos-reinitialiser-bureau programmer >/dev/null &&
        /usr/libexec/nicos/nicos-reinitialiser-bureau etat &&
        /usr/libexec/nicos/nicos-reinitialiser-bureau annuler >/dev/null &&
        /usr/libexec/nicos/nicos-reinitialiser-bureau etat' 2>&1 | tr '\n' ' ')"
    if [[ "${state}" == "programmee aucune " ]]; then pass "remise à zéro du bureau : programmation puis annulation"; else fail "remise à zéro du bureau : '${state}'"; fi
    check "script de démarrage de Plasma en place" test -f /etc/xdg/plasma-workspace/env/90-nicos-reinitialiser.sh
}
register_check base check_aide
