# shellcheck shell=bash
# « Installer des applications » : la commande que la page construit installe vraiment une application depuis Flathub
# (puis on la retire), et les identifiants proposés existent encore sur Flathub (un identifiant disparu ferait
# échouer l'installation de tout le lot : on le signale en avertissement, la CI ne doit pas dépendre d'un renommage).
check_applications() {
    section "Installer des applications (Flathub)"
    local ident absents="" cmd ok=0 liste
    wait_for 600 test -f /var/lib/nicos/flatpaks.sha256 || true
    check "action polkit d'installation de Flatpak connue" pkaction --action-id org.freedesktop.Flatpak.app-install
    check "le dépôt Flathub est configuré pour tout le système" bash -c "flatpak remotes --system --columns=name | grep -qx flathub"

    liste="$(
        python3 - <<'PYEOF'
import sys
sys.path.insert(0, "/usr/lib/nicos/centre")
from nicos_centre import applications, catalogue
for application in applications.proposees(catalogue.charger(), catalogue.fournies()):
    print(application.identifiant)
PYEOF
    )"
    if [[ "$(wc -l <<<"${liste}")" -ge 20 ]]; then pass "$(wc -l <<<"${liste}") applications proposées par la page"; else fail "liste d'applications trop courte : ${liste}"; fi
    while read -r ident; do
        [[ -n ${ident} ]] || continue
        wait_for 40 flatpak remote-info --system flathub "${ident}" || absents+="${ident} "
    done <<<"${liste}"
    if [[ -z ${absents} ]]; then pass "tous les identifiants proposés existent sur Flathub"; else warn "absents de Flathub : ${absents}"; fi

    ident=org.kde.kolourpaint
    cmd="$(
        python3 - "${ident}" <<'PYEOF'
import shlex, sys
sys.path.insert(0, "/usr/lib/nicos/centre")
from nicos_centre import applications
print(shlex.join(applications.commande([sys.argv[1]])))
PYEOF
    )"
    for _ in 1 2; do
        # shellcheck disable=SC2086  # la commande vient de applications.commande : mots séparés par des espaces
        if timeout 900 ${cmd} </dev/null >/var/tmp/nicos-test-applications.log 2>&1; then
            ok=1
            break
        fi
        sleep 20
    done
    if [[ ${ok} -eq 1 ]] && flatpak info --system "${ident}" >/dev/null 2>&1; then
        pass "la commande de la page installe ${ident} depuis Flathub"
        flatpak uninstall --system --noninteractive --assumeyes "${ident}" >/dev/null 2>&1 || warn "${ident} non retiré"
    else
        fail "la commande de la page n'a pas installé ${ident} : $(tail -3 /var/tmp/nicos-test-applications.log | tr '\n' ' ')"
    fi
    rm -f /var/tmp/nicos-test-applications.log
}
register_check base check_applications
