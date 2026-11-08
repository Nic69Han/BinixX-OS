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

# Aiguillage des programmes Windows sur le vrai système, pour l'utilisateur de test : binixx-ouvrir-windows (ouvert par le
# double-clic sur un .exe, voir 55-catalogue.sh dans l'image) conseille un équivalent, Wine ou Windows. Wine lui-même n'est pas lancé (Bottles et son
# moteur Wine se téléchargent : plusieurs centaines de Mo) ; la fenêtre et ses étapes sont testées dans l'image.
check_aiguillage_windows() {
    section "Aiguillage des programmes Windows"
    local out cas
    out="$(runuser -u "${TEST_USER}" -- kreadconfig6 --file kiorc --group 'Executable scripts' --key behaviourOnLaunch 2>&1)" || true
    if [[ "${out}" == "open" ]]; then
        pass "double-clic sur un .exe : une seule fenêtre (pas de « Exécuter ? » de KDE avant l'aiguillage)"
    else
        fail "kiorc behaviourOnLaunch pour l'utilisateur : '${out}' (attendu : open)"
    fi
    for cas in "WordSetup.exe:equivalent" "Setup_Zorglub_Pro.exe:wine" "SolidWorks2025.msi:windows"; do
        out="$(runuser -u "${TEST_USER}" -- /usr/libexec/binixx/binixx-ouvrir-windows --json "/tmp/${cas%%:*}" 2>&1)" || true
        if grep -q "\"moteur\": \"${cas##*:}\"" <<<"${out}"; then
            pass "aiguillage : ${cas%%:*} → ${cas##*:}"
        else
            fail "aiguillage : ${cas%%:*} : ${out:0:300}"
        fi
    done
}
register_check base check_aiguillage_windows
