#!/usr/bin/bash
# Vérifications exécutées DANS la VM, en root (sudo), par run-vm-test.sh.
# Usage : guest-checks.sh <phase> <secure-boot attendu : 1|0>
#   base            premier démarrage du système installé depuis l'ISO
#   after-update    après `bootc switch` vers l'image de mise à jour et redémarrage
#   after-rollback  après `bootc rollback` et redémarrage

set -uo pipefail

PHASE="${1:?phase manquante}"
EXPECT_SECURE_BOOT="${2:-1}"
TEST_USER="${SUDO_USER:-testeur}"
TEST_HOME="$(getent passwd "${TEST_USER}" | cut -d: -f6)"
UPDATE_MARKER=/usr/share/nicos/update-test-marker
FLATPAK_LIST=/usr/share/nicos/flatpaks/system-flatpaks.list
FLATPAK_TIMEOUT="${FLATPAK_TIMEOUT:-2700}"

failures=0
pass() { printf '  ok        %s\n' "$*"; }
warn() { printf '  attention %s\n' "$*"; }
fail() {
    printf '  ÉCHEC     %s\n' "$*"
    failures=$((failures + 1))
}
check() { # check "description" commande...
    local desc="$1"
    shift
    if "$@" >/dev/null 2>&1; then pass "${desc}"; else fail "${desc}"; fi
}
section() { printf '\n== %s\n' "$*"; }
# wait_for <secondes> commande... : réessaie toutes les 5 s jusqu'au succès ou au délai
wait_for() {
    local deadline=$((SECONDS + $1))
    shift
    until "$@" >/dev/null 2>&1; do
        [[ ${SECONDS} -ge ${deadline} ]] && return 1
        sleep 5
    done
}

booted_image() {
    bootc status --format=json 2>/dev/null | python3 -c \
        'import json,sys; s=json.load(sys.stdin)["status"]; print(((s.get("booted") or {}).get("image") or {}).get("image",{}).get("image",""))'
}

check_system_state() {
    section "État du système"
    local state
    state="$(timeout 600 systemctl is-system-running --wait 2>/dev/null)"
    case "${state}" in
    running) pass "démarrage terminé sans unité en échec" ;;
    degraded)
        local failed
        failed="$(systemctl --failed --no-legend --plain | awk '{print $1}')"
        if grep -q '^nicos-' <<<"${failed}"; then
            fail "service NicOS en échec : $(grep '^nicos-' <<<"${failed}" | tr '\n' ' ')"
        else
            warn "unités en échec (hors NicOS) : $(tr '\n' ' ' <<<"${failed}")"
        fi
        ;;
    *) fail "état du système : '${state}'" ;;
    esac
    check "session graphique (graphical.target) atteinte" systemctl is-active graphical.target
    check "gestionnaire de connexion actif" systemctl is-active display-manager.service
    check "SELinux en mode Enforcing" test "$(getenforce)" = Enforcing
    check "/usr en lecture seule, même pour root" bash -c '! touch /usr/.nicos-rw-test'
    if [[ "${EXPECT_SECURE_BOOT}" == 1 ]]; then
        check "Secure Boot actif" bash -c 'mokutil --sb-state | grep -q "SecureBoot enabled"'
    fi
    local image
    image="$(booted_image)"
    if [[ "${image}" == *nicos* ]]; then pass "image démarrée : ${image}"; else fail "image démarrée : '${image}'"; fi
}

check_hardware_and_network() {
    section "Son, réseau, visio"
    check "carte son détectée" grep -q '[0-9]' /proc/asound/cards
    check "PipeWire et WirePlumber installés" rpm -q pipewire wireplumber
    check "portail KDE (partage d'écran Wayland) installé" rpm -q xdg-desktop-portal-kde
    check "accès Internet (HTTPS vers Flathub)" curl -fsS --max-time 30 -o /dev/null https://dl.flathub.org/repo/flathub.flatpakrepo
    check "polices : Calibri remplacée par Carlito" bash -c 'fc-match -f "%{family[0]}" Calibri | grep -qx Carlito'
}

check_printing() {
    section "Impression PDF"
    if ! wait_for 120 lpstat -p Cups-PDF; then
        fail "imprimante Cups-PDF absente ($(systemctl is-failed nicos-pdf-printer.service))"
        return
    fi
    pass "imprimante Cups-PDF créée"
    local since
    since="$(mktemp)"
    if ! runuser -u "${TEST_USER}" -- bash -c 'echo "Page de test NicOS" | lp -d Cups-PDF -t nicos-test' >/dev/null; then
        fail "envoi d'un travail d'impression"
        return
    fi
    # Le PDF arrive sur le Bureau de l'utilisateur (ou dans /var/spool/cups-pdf s'il n'en a pas)
    if wait_for 120 bash -c "find '${TEST_HOME}/' /var/spool/cups-pdf/ -name '*.pdf' -newer '${since}' 2>/dev/null | grep -q ."; then
        pass "PDF produit : $(find "${TEST_HOME}/" /var/spool/cups-pdf/ -name '*.pdf' -newer "${since}" 2>/dev/null | head -1)"
    else
        fail "aucun PDF produit en 2 minutes"
        lpstat -W completed -o 2>/dev/null | tail -3
    fi
    rm -f "${since}"
}

check_flatpaks() {
    section "Applications Flatpak (installées au premier démarrage)"
    if ! wait_for "${FLATPAK_TIMEOUT}" test -f /var/lib/nicos/flatpaks.sha256; then
        fail "installation des Flatpak non terminée après ${FLATPAK_TIMEOUT} s ($(systemctl show -p ActiveState,Result --value nicos-flatpak-install.service | tr '\n' ' '))"
        return
    fi
    local installed app
    installed="$(flatpak list --system --app --columns=application)"
    while read -r app; do
        if grep -qxF "${app}" <<<"${installed}"; then pass "${app}"; else fail "${app} non installé"; fi
    done < <(sed -e 's/#.*//' -e 's/[[:space:]]//g' -e '/^$/d' "${FLATPAK_LIST}")
}

check_plasma_desktop() {
    section "Bureau Plasma (session ouverte automatiquement pour le test)"
    if ! wait_for 300 pgrep -u "${TEST_USER}" -x plasmashell; then
        fail "la session Plasma ne démarre pas"
        return
    fi
    pass "plasmashell lancé"
    local appletsrc="${TEST_HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc"
    # Plasma écrit sa configuration quelques secondes après la création du panneau
    if ! wait_for 180 grep -q 'org.kde.plasma.icontasks' "${appletsrc}"; then
        fail "disposition du panneau non écrite dans ${appletsrc}"
        return
    fi
    local report
    if report="$(
        python3 - "${appletsrc}" <<'PYEOF'
import configparser, sys

cfg = configparser.RawConfigParser(strict=False, interpolation=None)
cfg.optionxform = str
cfg.read(sys.argv[1])
panels = [s for s in cfg.sections()
          if s.count("][") == 1 and cfg.get(s, "plugin", fallback="") == "org.kde.panel"]
if len(panels) != 1:
    sys.exit(f"{len(panels)} panneau(x) au lieu d'un seul")
panel = panels[0]
if cfg.get(panel, "location", fallback="") != "4":
    sys.exit("le panneau n'est pas en bas de l'écran (location=%s)" % cfg.get(panel, "location", fallback="?"))
prefix = panel + "][Applets]["
applets = [cfg.get(s, "plugin", fallback="") for s in cfg.sections()
           if s.startswith(prefix) and s.count("][") == 3]
for wanted in ("org.kde.plasma.kickoff", "org.kde.plasma.icontasks",
               "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock",
               "org.kde.plasma.showdesktop"):
    if wanted not in applets:
        sys.exit(f"{wanted} absent du panneau ({applets})")
if "org.kde.plasma.pager" in applets:
    sys.exit("sélecteur de bureaux virtuels présent")
launchers = ""
for s in cfg.sections():
    if s.startswith(prefix) and s.endswith("][Configuration][General"):
        launchers += cfg.get(s, "launchers", fallback="")
for app in ("org.mozilla.Thunderbird.desktop", "org.onlyoffice.desktopeditors.desktop"):
    if app not in launchers:
        sys.exit(f"{app} non épinglé dans la barre des tâches")
print("panneau en bas : " + ", ".join(applets))
PYEOF
    )"; then
        pass "${report}"
    else
        fail "disposition du panneau"
    fi
    check "thème global appliqué (kdedefaults)" grep -qx 'org.nicos.desktop' "${TEST_HOME}/.config/kdedefaults/package"
    check "thème clair appliqué" grep -q '^ColorScheme=BreezeLight' "${TEST_HOME}/.config/kdedefaults/kdeglobals"
}

case "${PHASE}" in
base)
    check_system_state
    check_hardware_and_network
    check_printing
    check_plasma_desktop
    check_flatpaks
    check "pas de fichier témoin de mise à jour avant la mise à jour" test ! -e "${UPDATE_MARKER}"
    ;;
after-update)
    check_system_state
    section "Mise à jour"
    check "fichier témoin de la mise à jour présent" test -e "${UPDATE_MARKER}"
    check "image de mise à jour démarrée" bash -c "bootc status --format=json | grep -q 'update-test'"
    check "applications Flatpak conservées" flatpak info --system org.onlyoffice.desktopeditors
    check "compte et fichiers utilisateur conservés" test -d "${TEST_HOME}/.config"
    ;;
after-rollback)
    check_system_state
    section "Retour arrière"
    check "fichier témoin absent : ancienne version démarrée" test ! -e "${UPDATE_MARKER}"
    check "applications Flatpak conservées" flatpak info --system org.onlyoffice.desktopeditors
    check "compte et fichiers utilisateur conservés" test -d "${TEST_HOME}/.config"
    ;;
*)
    echo "phase inconnue : ${PHASE}" >&2
    exit 2
    ;;
esac

printf '\n'
if [[ ${failures} -gt 0 ]]; then
    printf '[%s] %d vérification(s) en échec.\n' "${PHASE}" "${failures}"
    exit 1
fi
printf '[%s] toutes les vérifications sont passées.\n' "${PHASE}"
