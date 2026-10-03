# shellcheck shell=bash
# Sur le système installé : ce dont WinBoat a besoin est là, et les vérifications de la page « Windows complet »
# tournent avec les vraies valeurs de la machine. Windows lui-même n'est pas lancé : la VM de test n'a pas
# de virtualisation imbriquée, et aucune licence Windows n'est disponible pour la CI.
check_windows_vm() {
    section "Windows dans une machine virtuelle"
    check "Podman présent" command -v podman
    check "Podman Compose présent" command -v podman-compose
    check "FreeRDP 3 présent" bash -c "xfreerdp --version 2>&1 | grep -q 'version 3\\.'"
    local out
    out="$(runuser -u "${TEST_USER}" -- python3 -c "
import sys
sys.path.insert(0, '/usr/lib/binixx/centre')
from binixx_centre import virtualisation as v
for r in v.verifier():
    print(r.cle, r.etat, r.titre)
" 2>&1)"
    if [[ "$(wc -l <<<"${out}")" -eq 4 ]] && grep -q '^virtualisation ' <<<"${out}"; then
        pass "les quatre vérifications des prérequis tournent sur ce système"
        # shellcheck disable=SC2001  # indentation de chaque ligne
        sed 's/^/        /' <<<"${out}"
    else
        fail "vérifications des prérequis : ${out}"
    fi
    if [[ -e /dev/kvm ]]; then
        pass "/dev/kvm présent : cette machine peut faire tourner une machine virtuelle"
    else
        warn "/dev/kvm absent de la VM de test (pas de virtualisation imbriquée) : Windows n'est pas lancé par le test"
    fi
}
register_check base check_windows_vm
