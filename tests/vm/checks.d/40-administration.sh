# shellcheck shell=bash
# Centre d'administration (Cockpit) : chargé par guest-checks.sh

check_administration() {
    section "Centre d'administration (Cockpit)"
    check "console joignable depuis le PC" curl -fsS -o /dev/null --max-time 30 http://127.0.0.1:9090/
    local listen
    listen="$(ss -Hltn 'sport = :9090' | awk '{print $4}' | sort | tr '\n' ' ')"
    if [[ "${listen}" == "127.0.0.1:9090 [::1]:9090 " ]]; then
        pass "console fermée au réseau (écoute : ${listen})"
    else
        fail "console : adresses d'écoute '${listen}' (attendu : 127.0.0.1 et ::1)"
    fi
    local modules
    modules="$(runuser -u "${TEST_USER}" -- cockpit-bridge --packages 2>/dev/null | awk '{print $1}' | sort | tr '\n' ' ')"
    # Noms déclarés dans les manifest.json : updates = cockpit-ostree, network = cockpit-networkmanager,
    # storage = cockpit-storaged
    local module
    for module in updates network storage selinux files; do
        if grep -qw "${module}" <<<"${modules}"; then pass "module « ${module} » chargé"; else fail "module « ${module} » absent (${modules})"; fi
    done
}

register_check base check_administration
