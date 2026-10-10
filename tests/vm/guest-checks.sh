#!/usr/bin/bash
# Vérifications exécutées DANS la VM, en root (sudo), par run-vm-test.sh.
# Usage : guest-checks.sh <phase> <secure-boot attendu : 1|0>
#   base            premier démarrage du système installé depuis l'ISO
#   after-update    après `bootc switch` vers l'image de mise à jour et redémarrage
#   after-rollback  après `bootc rollback` et redémarrage
#   after-auto-rollback  après une mise à jour défectueuse, retour arrière automatique de greenboot
#   theme-aube, theme-nuit, theme-contraste, theme-fin   style Windows 11 : une ambiance posée puis Dolphin ouvert pour la capture d'écran

set -uo pipefail

PHASE="${1:?phase manquante}"
EXPECT_SECURE_BOOT="${2:-1}"
TEST_USER="${SUDO_USER:-testeur}"
TEST_HOME="$(getent passwd "${TEST_USER}" | cut -d: -f6)"
UPDATE_MARKER=/usr/share/binixx/update-test-marker
FLATPAK_LIST=/usr/share/binixx/flatpaks/system-flatpaks.list
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
        local unit
        while read -r unit; do
            fail "service BinixX OS en échec : ${unit}"
            journalctl -b -u "${unit}" --no-pager -o cat 2>/dev/null | tail -n 15 | sed 's/^/            /'
        done < <(grep '^binixx-' <<<"${failed}")
        if grep -qv '^binixx-' <<<"${failed}"; then
            warn "unités en échec (hors BinixX OS) : $(grep -v '^binixx-' <<<"${failed}" | tr '\n' ' ')"
        fi
        ;;
    *) fail "état du système : '${state}'" ;;
    esac
    check "session graphique (graphical.target) atteinte" systemctl is-active graphical.target
    check "gestionnaire de connexion actif" systemctl is-active display-manager.service
    check "SELinux en mode Enforcing" test "$(getenforce)" = Enforcing
    check "/usr en lecture seule, même pour root" bash -c '! touch /usr/.binixx-rw-test'
    if [[ "${EXPECT_SECURE_BOOT}" == 1 ]]; then
        check "Secure Boot actif" bash -c 'mokutil --sb-state | grep -q "SecureBoot enabled"'
    fi
    if command -v efibootmgr >/dev/null; then
        # Noms des entrées seulement : le chemin (\EFI\fedora\shimx64.efi) garde « fedora »,
        # dossier dont dépend Secure Boot
        local labels
        labels="$(efibootmgr 2>/dev/null | grep '^Boot[0-9A-F]\{4\}' | cut -f1 | sed 's/^Boot[0-9A-F]\{4\}\*\{0,1\} //')"
        if grep -qx 'BinixX OS' <<<"${labels}" && ! grep -qi 'fedora' <<<"${labels}"; then
            pass "menu de démarrage du PC : entrée « BinixX OS », aucune entrée « Fedora »"
        else
            fail "menu de démarrage du PC : $(tr '\n' ';' <<<"${labels}")"
        fi
    else
        warn "efibootmgr absent : entrée de démarrage du PC non vérifiée"
    fi
    local image
    image="$(booted_image)"
    if [[ "${image}" == *binixx* ]]; then pass "image démarrée : ${image}"; else fail "image démarrée : '${image}'"; fi
}

check_security() {
    section "Sécurité"
    check "pare-feu actif" systemctl is-active firewalld.service
    local zone services ports
    zone="$(firewall-cmd --get-default-zone 2>/dev/null)"
    if [[ "${zone}" == binixx ]]; then pass "pare-feu : zone par défaut binixx"; else fail "pare-feu : zone par défaut '${zone}'"; fi
    # La VM de test ouvre SSH en plus (kickstart) ; rien d'autre ne doit pouvoir entrer
    services="$(firewall-cmd --zone=binixx --list-services 2>/dev/null)"
    ports="$(firewall-cmd --zone=binixx --list-ports 2>/dev/null)"
    if [[ -z "${ports}" ]] && ! tr ' ' '\n' <<<"${services}" | grep -qvxE 'dhcpv6-client|mdns|samba-client|kdeconnect|ssh|'; then
        pass "pare-feu : entrées limitées à ${services}"
    else
        fail "pare-feu : services '${services}', ports '${ports}'"
    fi
    local setting
    for setting in kernel.dmesg_restrict=1 kernel.yama.ptrace_scope=1 net.ipv4.conf.all.accept_redirects=0; do
        check "noyau : ${setting}" test "$(sysctl -n "${setting%=*}")" = "${setting#*=}"
    done
    check "mises à jour automatiques du système programmées" systemctl is-enabled rpm-ostreed-automatic.timer
    check "mises à jour automatiques des applications programmées" systemctl is-enabled flatpak-system-update.timer
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
        fail "imprimante Cups-PDF absente ($(systemctl is-failed binixx-pdf-printer.service))"
        return
    fi
    pass "imprimante Cups-PDF créée"
    local since
    since="$(mktemp)"
    if ! runuser -u "${TEST_USER}" -- bash -c 'echo "Page de test BinixX OS" | lp -d Cups-PDF -t binixx-test' >/dev/null; then
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
    if ! wait_for "${FLATPAK_TIMEOUT}" test -f /var/lib/binixx/flatpaks.sha256; then
        fail "installation des Flatpak non terminée après ${FLATPAK_TIMEOUT} s ($(systemctl show -p ActiveState,Result --value binixx-flatpak-install.service | tr '\n' ' '))"
        return
    fi
    local installed app
    installed="$(flatpak list --system --app --columns=application)"
    while read -r app; do
        if grep -qxF "${app}" <<<"${installed}"; then pass "${app}"; else fail "${app} non installé"; fi
    done < <(sed -e 's/#.*//' -e 's/[[:space:]]//g' -e '/^$/d' "${FLATPAK_LIST}")
    local remotes
    remotes="$(flatpak remotes --system --columns=name,title | tr '\t\n' '  ')"
    if grep -qi fedora <<<"${remotes}"; then fail "source d'applications Fedora : ${remotes}"; else pass "sources d'applications : ${remotes}"; fi
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
if cfg.get(panel, "location", fallback="") != "3":  # 3 = bord haut (Plasma::Types::TopEdge)
    sys.exit("le panneau n'est pas en haut de l'écran (location=%s)" % cfg.get(panel, "location", fallback="?"))
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
for app in ("org.mozilla.thunderbird_esr.desktop", "org.onlyoffice.desktopeditors.desktop"):
    if app not in launchers:
        sys.exit(f"{app} non épinglé dans la barre des tâches")
kickoff = [s for s in cfg.sections() if s.startswith(prefix) and s.count("][") == 3
           and cfg.get(s, "plugin", fallback="") == "org.kde.plasma.kickoff"]
icon = cfg.get(kickoff[0] + "][Configuration][General", "icon", fallback="")
if icon != "binixx":
    sys.exit(f"icône du bouton Démarrer : '{icon}' (attendu : binixx)")
grille = cfg.get(kickoff[0] + "][Configuration][General", "applicationsDisplay", fallback="")
if grille != "0":
    sys.exit(f"menu de démarrage : applicationsDisplay='{grille}' (attendu : 0, « Toutes les applications » en grille)")
print("panneau en haut : " + ", ".join(applets))
PYEOF
    )"; then
        pass "${report}"
    else
        fail "disposition du panneau"
    fi
    # Aube le jour, Nuit le soir (bascule automatique de Plasma) : un compte neuf a l'un ou l'autre selon l'heure à l'endroit où le
    # service de localisation place la machine (pour la VM, celui du serveur de test, pas son fuseau horaire), avec ses couleurs
    local paquet
    paquet="$(cat "${TEST_HOME}/.config/kdedefaults/package" 2>/dev/null)"
    case "${paquet}" in
    org.binixx.desktop)
        pass "thème global appliqué (kdedefaults) : Aube"
        check "couleurs BinixX OS clair appliquées" grep -q '^ColorScheme=BinixXClair' "${TEST_HOME}/.config/kdedefaults/kdeglobals"
        ;;
    org.binixx.dark.desktop)
        pass "thème global appliqué (kdedefaults) : Nuit (posé par la bascule automatique, c'est la nuit pour le service de localisation)"
        check "couleurs BinixX OS sombre appliquées" grep -q '^ColorScheme=BinixXSombre' "${TEST_HOME}/.config/kdedefaults/kdeglobals"
        ;;
    *) fail "thème global (kdedefaults/package) : '${paquet}' (org.binixx.desktop ou org.binixx.dark.desktop attendu)" ;;
    esac
    # Plasma n'écrit « floating » que s'il diffère de son réglage par défaut (flottant)
    local shellrc="${TEST_HOME}/.config/plasmashellrc"
    if [[ ! -f "${shellrc}" ]]; then
        fail "${shellrc} absent"
    elif grep -q '^floating=0' "${shellrc}"; then
        fail "barre des tâches non flottante"
    else
        pass "barre des tâches flottante"
    fi
    local uid kwin
    uid="$(id -u "${TEST_USER}")"
    kwin="$(runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" \
        busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting isScriptLoaded s kde-snap-overlay 2>&1)"
    if [[ "${kwin}" == "b true" ]]; then pass "dispositions de fenêtres (kde-snap-overlay) chargées par KWin"; else fail "kde-snap-overlay non chargé : ${kwin}"; fi
    check "nouvelles fenêtres centrées" bash -c \
        "[[ \"\$(runuser -u '${TEST_USER}' -- kreadconfig6 --file kwinrc --group Windows --key Placement)\" == Centered ]]"
}

# Vérifications par fonctionnalité : un fichier par chantier dans checks.d/ (ordre alphabétique).
# Il définit une fonction et l'inscrit à une phase : register_check <base|after-update|after-rollback> <fonction>
declare -A PHASE_CHECKS=()
register_check() { PHASE_CHECKS[$1]+=" $2"; }
run_module_checks() { # run_module_checks <phase>
    local fn
    for fn in ${PHASE_CHECKS[$1]:-}; do "${fn}"; done
}
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
shopt -s nullglob
for module in "${HERE}"/checks.d/*.sh; do
    # shellcheck source=/dev/null
    . "${module}"
done
shopt -u nullglob

case "${PHASE}" in
base)
    check_system_state
    check_security
    check_hardware_and_network
    check_printing
    check_plasma_desktop
    check_flatpaks
    run_module_checks base
    check "pas de fichier témoin de mise à jour avant la mise à jour" test ! -e "${UPDATE_MARKER}"
    ;;
after-update)
    check_system_state
    section "Mise à jour"
    check "fichier témoin de la mise à jour présent" test -e "${UPDATE_MARKER}"
    check "image de mise à jour démarrée" bash -c "bootc status --format=json | grep -q 'update-test'"
    check "applications Flatpak conservées" flatpak info --system org.onlyoffice.desktopeditors
    check "compte et fichiers utilisateur conservés" test -d "${TEST_HOME}/.config"
    run_module_checks after-update
    ;;
after-rollback)
    check_system_state
    section "Retour arrière"
    check "fichier témoin absent : ancienne version démarrée" test ! -e "${UPDATE_MARKER}"
    check "applications Flatpak conservées" flatpak info --system org.onlyoffice.desktopeditors
    check "compte et fichiers utilisateur conservés" test -d "${TEST_HOME}/.config"
    run_module_checks after-rollback
    ;;
after-auto-rollback)
    check_system_state
    run_module_checks after-auto-rollback
    ;;
theme-aube | theme-nuit | theme-contraste | theme-fin)
    # Captures du style Windows 11 : une phase par ambiance, lancées par run-vm-test.sh (checks.d/82-theme-windows-11.sh)
    run_module_checks "${PHASE}"
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
