#!/usr/bin/bash
# Vérifie le contenu de l'image BinixX OS depuis l'intérieur d'un conteneur, sans la démarrer.
# Lancé par `just test-image` (et donc par la CI à chaque build, pull requests comprises) :
#   podman run --rm -v ./tests/image:/tests:ro -v ./flatpaks:/flatpaks:ro binixx:testing bash /tests/check-image.sh

set -uo pipefail

failures=0
pass() { printf '  ok      %s\n' "$*"; }
fail() {
    printf '  ÉCHEC   %s\n' "$*"
    failures=$((failures + 1))
}
check() { # check "description" commande...
    local desc="$1" etat
    shift
    # « set -e » compte dans la commande (une fonction qui l'active échoue dès sa première commande en échec) : bash l'ignorerait sous « if »,
    # d'où ce code de retour lu à part
    (
        set -e
        "$@"
    ) >/dev/null 2>&1
    etat=$?
    if [[ "${etat}" -eq 0 ]]; then pass "${desc}"; else fail "${desc}"; fi
}
section() { printf '\n== %s\n' "$*"; }

section "Paquets"
for pkg in google-carlito-fonts google-crosextra-caladea-fonts liberation-sans-fonts \
    liberation-serif-fonts liberation-mono-fonts cups cups-pdf hplip gutenprint-cups \
    sane-backends sane-airscan ipp-usb skanpage pipewire xdg-desktop-portal-kde mokutil \
    plasma-setup langpacks-fr hunspell-fr onedrive plasma-nm-l2tp plasma-nm-sstp plasma-nm-strongswan \
    adcli sssd-ad oddjob-mkhomedir krb5-workstation firefox; do
    check "${pkg} installé" rpm -q "${pkg}"
done

section "Polices compatibles Microsoft (fontconfig)"
expect_font() { # police demandée -> famille attendue
    local got
    got="$(fc-match -f '%{family[0]}' "$1" 2>/dev/null)"
    if [[ "${got}" == "$2" ]]; then pass "$1 -> ${got}"; else fail "$1 -> '${got}' (attendu : $2)"; fi
}
expect_font Calibri Carlito
expect_font Cambria Caladea
expect_font Arial "Liberation Sans"
expect_font "Times New Roman" "Liberation Serif"
expect_font "Courier New" "Liberation Mono"
expect_font "Segoe UI" Selawik
expect_font "Segoe UI Semibold" Selawik
check "licence de Selawik fournie avec la police" test -s /usr/share/fonts/selawik/LICENSE.txt

section "Bureau Plasma"
LNF=/usr/share/plasma/look-and-feel/org.binixx.desktop
check "thème global org.binixx.desktop présent" test -f "${LNF}/metadata.json"
check "identifiant du thème global correct" grep -q '"Id": "org.binixx.desktop"' "${LNF}/metadata.json"
check "disposition du panneau présente" test -f "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"
check "écran de démarrage hérité de Breeze" test -f "${LNF}/contents/splash/Splash.qml"
check "couleurs BinixX OS clair dans le thème BinixX OS" grep -qx 'ColorScheme=BinixXClair' "${LNF}/contents/defaults"
LNF_DARK=/usr/share/plasma/look-and-feel/org.binixx.dark.desktop
check "thème global BinixX OS sombre présent" grep -q '"Id": "org.binixx.dark.desktop"' "${LNF_DARK}/metadata.json"
check "thème BinixX OS sombre : même disposition que BinixX OS" \
    cmp "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js" "${LNF_DARK}/contents/layouts/org.kde.plasma.desktop-layout.js"
check "thème BinixX OS sombre : couleurs BinixX OS sombre" grep -qx 'ColorScheme=BinixXSombre' "${LNF_DARK}/contents/defaults"
check "thème BinixX OS sombre : aperçus hérités de Brise sombre" \
    test -f "${LNF_DARK}/contents/previews/preview.png" -a -f "${LNF_DARK}/contents/previews/fullscreenpreview.jpg"
for scheme in BinixXClair BinixXSombre; do
    colors="/usr/share/color-schemes/${scheme}.colors"
    selection="$(kreadconfig6 --file "${colors}" --group Colors:Selection --key BackgroundNormal 2>/dev/null)"
    if [[ "${selection}" == 47,91,255 || "${selection}" == 90,125,255 ]] && grep -q "^ColorScheme=${scheme}$" "${colors}"; then
        pass "couleurs ${scheme} : sélection en bleu BinixX OS (${selection})"
    else
        fail "couleurs ${scheme} : sélection '${selection}'"
    fi
done
for pair in DefaultLightLookAndFeel=org.binixx.desktop DefaultDarkLookAndFeel=org.binixx.dark.desktop; do
    value="$(kreadconfig6 --file /etc/xdg/kdeglobals --group KDE --key "${pair%=*}")"
    if [[ "${value}" == "${pair#*=}" ]]; then pass "thème ${pair%LookAndFeel=*} : ${value}"; else fail "${pair%=*}='${value}'"; fi
done
check "panneau sans sélecteur de bureaux virtuels" \
    bash -c "! grep -q 'org.kde.plasma.pager' '${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js'"
lnf="$(kreadconfig6 --file /etc/xdg/kdeglobals --group KDE --key LookAndFeelPackage)"
if [[ "${lnf}" == org.binixx.desktop ]]; then pass "thème global par défaut (/etc/xdg) : ${lnf}"; else fail "thème global par défaut (/etc/xdg) : '${lnf}'"; fi
KDE_SETTINGS_GLOBALS=/usr/share/kde-settings/kde-profile/default/xdg/kdeglobals
if [[ -f "${KDE_SETTINGS_GLOBALS}" ]]; then
    check "thème global par défaut (kde-settings Fedora)" grep -qx 'LookAndFeelPackage=org.binixx.desktop' "${KDE_SETTINGS_GLOBALS}"
fi
numlock="$(kreadconfig6 --file /etc/xdg/kcminputrc --group Keyboard --key NumLock)"
if [[ "${numlock}" == 0 ]]; then pass "pavé numérique activé au démarrage"; else fail "NumLock='${numlock}' (attendu : 0)"; fi
check "favoris du menu de démarrage" grep -q 'org.onlyoffice.desktopeditors.desktop' /etc/xdg/kicker-extra-favoritesrc
check "OnlyOffice associé aux .docx" \
    grep -qx 'application/vnd.openxmlformats-officedocument.wordprocessingml.document=org.onlyoffice.desktopeditors.desktop' /etc/xdg/kde-mimeapps.list

check "barre des tâches en haut de l'écran" \
    grep -q 'panel.location = "top"' "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"
check "barre des tâches flottante" \
    grep -q 'panel.floating = true' "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"
placement="$(kreadconfig6 --file /etc/xdg/kwinrc --group Windows --key Placement)"
if [[ "${placement}" == Centered ]]; then pass "nouvelles fenêtres centrées"; else fail "placement des fenêtres : '${placement}'"; fi
SNAP=/usr/share/kwin/scripts/kde-snap-overlay
check "dispositions de fenêtres (kde-snap-overlay) installées" grep -q '"Id": "kde-snap-overlay"' "${SNAP}/metadata.json"
check "kde-snap-overlay : licence et attribution fournies" test -s "${SNAP}/LICENSE" -a -s "${SNAP}/NOTICE"
snap="$(kreadconfig6 --file /etc/xdg/kwinrc --group Plugins --key kde-snap-overlayEnabled)"
if [[ "${snap}" == true ]]; then pass "kde-snap-overlay activé par défaut"; else fail "kde-snap-overlayEnabled='${snap}'"; fi
check "logo BinixX OS sur le bouton Démarrer" \
    grep -q 'writeConfig("icon", "binixx")' "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"
check "menu de démarrage : « Toutes les applications » en grille, comme Windows 11 (applicationsDisplay=0)" \
    grep -q 'kickoff.writeConfig("applicationsDisplay", 0)' "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"

section "Identité visuelle"
# shellcheck source=/dev/null  # fichier de l'image, absent du dépôt
. /usr/lib/os-release
if [[ "${NAME}" == "BinixX OS" && "${LOGO}" == binixx ]]; then pass "os-release : ${PRETTY_NAME}"; else fail "os-release : NAME='${NAME}' LOGO='${LOGO}'"; fi
if [[ "${ID}" == fedora ]]; then pass "ID=fedora conservé"; else fail "ID='${ID}' (attendu : fedora)"; fi
check "icône BinixX OS installée" test -s /usr/share/icons/hicolor/scalable/apps/binixx.svg
check "logos Fedora remplacés (generic-logos)" bash -c '! rpm -q fedora-logos && rpm -q generic-logos'
check "fond d'écran BinixX OS (clair et sombre)" \
    test -s /usr/share/wallpapers/BinixX/contents/images/1920x1080.jpg -a -s /usr/share/wallpapers/BinixX/contents/images_dark/1920x1080.jpg
check "fond d'écran par défaut du bureau" grep -qx 'Image=BinixX' "${LNF}/contents/defaults"
check "fond d'écran de l'écran de verrouillage" grep -q 'wallpapers/BinixX' /etc/xdg/kscreenlockerrc
check "fond d'écran de l'écran de connexion" grep -q 'wallpapers/BinixX' /usr/lib/plasmalogin/defaults.conf
check "logo BinixX OS dans « À propos »" grep -q 'binixx.svg' /etc/xdg/kcm-about-distrorc
theme="$(plymouth-set-default-theme 2>/dev/null)"
if [[ "${theme}" == binixx ]]; then pass "écran de démarrage : thème ${theme}"; else fail "thème Plymouth : '${theme}' (attendu : binixx)"; fi
check "animation de chargement copiée dans le thème" test -s /usr/share/plymouth/themes/binixx/throbber-0001.png
check "thème de démarrage présent dans l'initramfs" \
    bash -c 'lsinitrd /usr/lib/modules/*/initramfs.img | grep -q "plymouth/themes/binixx/watermark.png"'
check "système de fichiers racine par défaut (bootc)" grep -q 'type = "btrfs"' /usr/lib/bootc/install/50-binixx.toml
check "nom du système pour le firmware (/etc/system-release)" grep -q '^BinixX OS release ' /etc/system-release
check "/etc/fedora-release conservé pour les outils" grep -q '^Fedora release ' /etc/fedora-release
boot_csv_ok=1
shopt -s nullglob
boot_csvs=(/usr/lib/efi/shim/*/EFI/*/BOOT*.CSV /usr/lib/bootupd/updates/EFI/*/BOOT*.CSV)
shopt -u nullglob
[[ ${#boot_csvs[@]} -gt 0 ]] || boot_csv_ok=0
for csv in "${boot_csvs[@]}"; do
    label="$(iconv -f UTF-16 -t UTF-8 "${csv}")"
    [[ "${label}" == *",BinixX OS,"* && "${label}" != *Fedora* ]] || boot_csv_ok=0
done
if [[ ${boot_csv_ok} -eq 1 ]]; then pass "entrée de démarrage du firmware : BinixX OS (${#boot_csvs[@]} fichier(s) BOOT*.CSV)"; else fail "entrée de démarrage du firmware : BOOT*.CSV absent ou encore « Fedora »"; fi
fedora_names="$(python3 - <<'PYEOF'
import json, pathlib
for folder in ("/usr/share/plasma/look-and-feel", "/usr/share/wallpapers"):
    for meta in pathlib.Path(folder).glob("*/metadata.json"):
        if meta.parent.is_symlink():  # Default -> F44 : seul le dossier réel compte
            continue
        name = json.loads(meta.read_text()).get("KPlugin", {}).get("Name", "")
        if "fedora" in name.lower():
            print(f"{meta.parent.name} ({name})", end=" ")
PYEOF
)"
if [[ -z "${fedora_names}" ]]; then pass "aucun thème ni fond d'écran nommé « Fedora »"; else fail "thèmes ou fonds d'écran « Fedora » : ${fedora_names}"; fi
check "fond d'écran « par défaut » de KDE : BinixX OS" test "$(readlink -f /usr/share/wallpapers/Default)" = /usr/share/wallpapers/BinixX
check "Firefox : « À propos » sans Fedora" bash -c '! grep -qi fedora /usr/lib64/firefox/distribution/distribution.ini'
check "Firefox : ni page d'accueil ni raccourci Fedora" \
    bash -c '! grep -q fedoraproject /usr/lib64/firefox/browser/defaults/preferences/firefox-redhat-default-prefs.js'
state="$(systemctl is-enabled flatpak-add-fedora-repos.service 2>/dev/null || true)"
if [[ -z "${state}" || "${state}" == masked ]]; then
    pass "pas de source d'applications Fedora ajoutée au démarrage (${state:-service absent})"
else
    fail "flatpak-add-fedora-repos.service : '${state}' (attendu : masked ou absent)"
fi

section "Applications Flatpak"
LIST=/usr/share/binixx/flatpaks/system-flatpaks.list
check "liste Flatpak installée dans l'image" test -f "${LIST}"
if [[ -f /flatpaks/system-flatpaks.list ]]; then
    check "liste Flatpak identique à celle du dépôt" cmp -s "${LIST}" /flatpaks/system-flatpaks.list
fi
for app in org.onlyoffice.desktopeditors org.mozilla.thunderbird_esr org.kde.okular \
    com.nextcloud.desktopclient.nextcloud org.chromium.Chromium org.remmina.Remmina org.gnome.DejaDup \
    org.kde.haruna; do
    check "${app} dans la liste" grep -qx "${app}" "${LIST}"
done
# Firefox vient de l'image (navigateur par défaut de Fedora) : pas de second Firefox en Flatpak
check "pas de Firefox en double dans la liste Flatpak" bash -c "! grep -qx org.mozilla.firefox '${LIST}'"

section "Web apps"
for webapp in teams zoom slack outlook word excel powerpoint microsoft365 artcraft; do
    check "lanceur ${webapp} valide" desktop-file-validate "/usr/share/applications/binixx-webapp-${webapp}.desktop"
done
# ArtCraft (images et vidéos par IA) : le service web officiel, dans une fenêtre dédiée, rangé avec les applications graphiques. Aucune version
# native dans l'image : ses auteurs ne publient que Windows et macOS, et leur licence ne prévoit pas la redistribution (docs/artcraft.md)
check "lanceur ArtCraft : ouvre app.getartcraft.com par binixx-webapp, dans la catégorie Graphics" bash -c \
    "grep -qx 'Exec=/usr/libexec/binixx/binixx-webapp https://app.getartcraft.com/' /usr/share/applications/binixx-webapp-artcraft.desktop && grep -qx 'Categories=Graphics;2DGraphics;' /usr/share/applications/binixx-webapp-artcraft.desktop"
check "ArtCraft : pas de programme natif ni de paquet dans l'image" bash -c \
    "! command -v artcraft && ! rpm -q artcraft && ! ls /usr/bin/*artcraft* /opt/*rtcraft* /usr/lib/*rtcraft* 2>/dev/null | grep -q ."
check "lanceur de web apps exécutable" test -x /usr/libexec/binixx/binixx-webapp

section "OneDrive, vidéo, entreprise"
check "lanceur OneDrive valide" desktop-file-validate /usr/share/applications/binixx-onedrive.desktop
check "assistant OneDrive exécutable" test -x /usr/libexec/binixx/binixx-onedrive-setup
check "service de synchronisation OneDrive (utilisateur)" test -f /usr/lib/systemd/user/onedrive.service
check "Haruna lit les vidéos par défaut" grep -qx 'video/mp4=org.kde.haruna.desktop' /etc/xdg/kde-mimeapps.list
check "jonction à un domaine Active Directory (realm)" bash -c 'command -v realm'

section "Sécurité"
zone="$(firewall-offline-cmd --get-default-zone 2>/dev/null)"
if [[ "${zone}" == binixx ]]; then pass "pare-feu : zone par défaut binixx"; else fail "pare-feu : zone par défaut '${zone}' (attendu : binixx)"; fi
services="$(firewall-offline-cmd --zone=binixx --list-services 2>/dev/null | tr ' ' '\n' | sort | tr '\n' ' ')"
if [[ "${services}" == "dhcpv6-client kdeconnect mdns samba-client " ]]; then
    pass "pare-feu : seuls le réseau local et KDE Connect peuvent entrer"
else
    fail "pare-feu : services ouverts '${services}'"
fi
check "pare-feu : aucun port ouvert en plus" test -z "$(firewall-offline-cmd --zone=binixx --list-ports 2>/dev/null)"
state="$(systemctl is-enabled sshd.service 2>/dev/null)"
if [[ "${state}" != enabled ]]; then pass "serveur SSH désactivé par défaut (${state})"; else fail "serveur SSH activé par défaut"; fi
for setting in 'kernel.dmesg_restrict = 1' 'kernel.yama.ptrace_scope = 1' 'net.ipv4.conf.all.accept_redirects = 0'; do
    check "noyau : ${setting}" grep -qx "${setting}" /usr/lib/sysctl.d/60-binixx-durcissement.conf
done
check "Firefox : uBlock Origin installé d'office, mode HTTPS uniquement" python3 -c '
import json
p = json.load(open("/etc/firefox/policies/policies.json"))["policies"]
assert p["HttpsOnlyMode"] == "enabled" and p["DisableTelemetry"] is True
assert p["ExtensionSettings"]["uBlock0@raymondhill.net"]["installation_mode"] == "normal_installed"
'

section "Services"
for unit in binixx-flatpak-install.service binixx-pdf-printer.service plasma-setup.service; do
    state="$(systemctl is-enabled "${unit}" 2>/dev/null)"
    if [[ "${state}" == enabled ]]; then pass "${unit} activé"; else fail "${unit} : '${state}' (attendu : enabled)"; fi
done
check "script d'installation Flatpak exécutable" test -x /usr/libexec/binixx/binixx-flatpak-install
check "script de création de l'imprimante PDF exécutable" test -x /usr/libexec/binixx/binixx-pdf-printer
check "syntaxe des unités systemd BinixX OS" \
    systemd-analyze verify --man=no --recursive-errors=no \
    /usr/lib/systemd/system/binixx-flatpak-install.service /usr/lib/systemd/system/binixx-pdf-printer.service
check "pilote de l'imprimante PDF (PPD)" test -f /usr/share/cups/model/CUPS-PDF_noopt.ppd
check "backend CUPS de l'imprimante PDF" test -x /usr/lib/cups/backend/cups-pdf

# Vérifications par fonctionnalité : un fichier par chantier dans checks.d/ (ordre alphabétique),
# avec les fonctions pass, fail, check et section ci-dessus. Aucune ligne à ajouter ici.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
shopt -s nullglob
for module in "${HERE}"/checks.d/*.sh; do
    # shellcheck source=/dev/null
    . "${module}"
done
shopt -u nullglob

printf '\n'
if [[ ${failures} -gt 0 ]]; then
    printf '%d vérification(s) en échec.\n' "${failures}"
    exit 1
fi
printf 'Toutes les vérifications de l'\''image sont passées.\n'
