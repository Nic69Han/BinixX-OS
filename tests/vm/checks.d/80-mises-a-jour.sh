# shellcheck shell=bash
# Page « Mises à jour » : l'outil lit l'état du vrai système, sans mot de passe, et cet état suit la mise à jour et le
# retour arrière faits par le test (version précédente présente, image démarrée). « installer » et « retour »
# changeraient le système sous les pieds du test : on vérifie seulement qu'un utilisateur ordinaire en est écarté.
etat_mises_a_jour() { # etat_mises_a_jour <champ python> : une valeur de la réponse JSON de `etat --json`
    runuser -u "${TEST_USER}" -- /usr/libexec/binixx/binixx-mises-a-jour etat --json 2>/dev/null |
        python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"
}
check_mises_a_jour() { # check_mises_a_jour <base|after-update|after-rollback>
    section "Mises à jour (état lu par l'utilisateur, sans mot de passe)"
    local outil=/usr/libexec/binixx/binixx-mises-a-jour out image code
    if out="$(runuser -u "${TEST_USER}" -- "${outil}" etat 2>&1)"; then
        pass "binixx-mises-a-jour etat répond"
    else
        fail "binixx-mises-a-jour etat : ${out:0:300}"
    fi
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
    image="$(etat_mises_a_jour 'd["installee"]["image"]' || true)"
    if [[ "${image}" == *binixx* || "${image}" == *update-test* ]]; then pass "image installée lue : ${image}"; else
        fail "image installée illisible : '${image}'"
        rpm-ostree status --json 2>&1 | head -c 2500 | sed 's/^/            brut : /'
    fi
    if [[ -n "$(etat_mises_a_jour 'd["installee"]["version"]' || true)" ]]; then pass "version installée lue : $(etat_mises_a_jour 'd["installee"]["version"]')"; else
        warn "version installée vide dans la réponse de rpm-ostree"
    fi
    case "$1" in
    after-update)
        if [[ "${image}" == *update-test* ]]; then pass "la version installée est celle de la mise à jour"; else fail "version installée : ${image}"; fi
        if [[ "$(etat_mises_a_jour '"oui" if d["precedente"] else "non"' || true)" == oui ]]; then
            pass "la version précédente est proposée (retour arrière possible)"
        else
            fail "aucune version précédente après la mise à jour"
        fi
        ;;
    after-rollback)
        if [[ "${image}" != *update-test* ]]; then pass "la version installée est de nouveau l'ancienne"; else fail "version installée : ${image}"; fi
        if [[ "$(etat_mises_a_jour '"oui" if d["precedente"] else "non"' || true)" == oui ]]; then
            pass "la version de la mise à jour est proposée comme version précédente"
        else
            warn "aucune version précédente après le retour arrière"
        fi
        ;;
    esac
    # La recherche passe par le réseau : elle peut ne pas aboutir dans la VM, mais elle ne doit jamais planter
    out="$(runuser -u "${TEST_USER}" -- "${outil}" verifier --json 2>&1)" && code=0 || code=$?
    if [[ "${code}" -eq 0 ]] && python3 -c 'import json,sys; v=json.loads(sys.argv[1])["verification"]["disponible"]; assert v in (True, False, None)' "${out}" 2>/dev/null; then
        pass "la recherche de nouvelle version répond : $(python3 -c 'import json,sys; v=json.loads(sys.argv[1])["verification"]; print(v["disponible"], v["raison"])' "${out}")"
    else
        fail "binixx-mises-a-jour verifier : ${out:0:300}"
    fi
    out="$(runuser -u "${TEST_USER}" -- "${outil}" installer 2>&1)" && code=0 || code=$?
    if [[ "${code}" -eq 3 && "${out}" == *administrateur* ]]; then pass "installer est refusé à un utilisateur ordinaire"; else fail "installer sans administrateur : code ${code}, ${out:0:200}"; fi
    out="$(runuser -u "${TEST_USER}" -- "${outil}" retour 2>&1)" && code=0 || code=$?
    if [[ "${code}" -eq 3 && "${out}" == *administrateur* ]]; then pass "retour est refusé à un utilisateur ordinaire"; else fail "retour sans administrateur : code ${code}, ${out:0:200}"; fi
    check "règle polkit de l'installation et du retour arrière en place" test -f /usr/share/polkit-1/actions/org.binixx.mises-a-jour.policy
}
# register_check range des noms de fonctions séparés par des espaces : pas d'argument, une fonction par phase
check_mises_a_jour_base() { check_mises_a_jour base; }
check_mises_a_jour_apres_mise_a_jour() { check_mises_a_jour after-update; }
check_mises_a_jour_apres_retour() { check_mises_a_jour after-rollback; }
register_check base check_mises_a_jour_base
register_check after-update check_mises_a_jour_apres_mise_a_jour
register_check after-rollback check_mises_a_jour_apres_retour
