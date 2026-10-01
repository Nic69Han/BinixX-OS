#!/usr/bin/bash
# Vérifie le contenu de l'image NicOS depuis l'intérieur d'un conteneur, sans la démarrer.
# Lancé par `just test-image` (et donc par la CI à chaque build, pull requests comprises) :
#   podman run --rm -v ./tests/image:/tests:ro -v ./flatpaks:/flatpaks:ro nicos:testing bash /tests/check-image.sh

set -uo pipefail

failures=0
pass() { printf '  ok      %s\n' "$*"; }
fail() {
    printf '  ÉCHEC   %s\n' "$*"
    failures=$((failures + 1))
}
check() { # check "description" commande...
    local desc="$1"
    shift
    if "$@" >/dev/null 2>&1; then pass "${desc}"; else fail "${desc}"; fi
}
section() { printf '\n== %s\n' "$*"; }

section "Paquets"
for pkg in google-carlito-fonts google-crosextra-caladea-fonts liberation-sans-fonts \
    liberation-serif-fonts liberation-mono-fonts cups cups-pdf hplip gutenprint-cups \
    sane-backends sane-airscan ipp-usb skanpage pipewire xdg-desktop-portal-kde mokutil \
    plasma-setup; do
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

section "Bureau Plasma"
LNF=/usr/share/plasma/look-and-feel/org.nicos.desktop
check "thème global org.nicos.desktop présent" test -f "${LNF}/metadata.json"
check "identifiant du thème global correct" grep -q '"Id": "org.nicos.desktop"' "${LNF}/metadata.json"
check "disposition du panneau présente" test -f "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"
check "écran de démarrage hérité de Breeze" test -f "${LNF}/contents/splash/Splash.qml"
check "thème clair (BreezeLight)" grep -qx 'ColorScheme=BreezeLight' "${LNF}/contents/defaults"
check "panneau sans sélecteur de bureaux virtuels" \
    bash -c "! grep -q 'org.kde.plasma.pager' '${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js'"
lnf="$(kreadconfig6 --file /etc/xdg/kdeglobals --group KDE --key LookAndFeelPackage)"
if [[ "${lnf}" == org.nicos.desktop ]]; then pass "thème global par défaut (/etc/xdg) : ${lnf}"; else fail "thème global par défaut (/etc/xdg) : '${lnf}'"; fi
KDE_SETTINGS_GLOBALS=/usr/share/kde-settings/kde-profile/default/xdg/kdeglobals
if [[ -f "${KDE_SETTINGS_GLOBALS}" ]]; then
    check "thème global par défaut (kde-settings Fedora)" grep -qx 'LookAndFeelPackage=org.nicos.desktop' "${KDE_SETTINGS_GLOBALS}"
fi
numlock="$(kreadconfig6 --file /etc/xdg/kcminputrc --group Keyboard --key NumLock)"
if [[ "${numlock}" == 0 ]]; then pass "pavé numérique activé au démarrage"; else fail "NumLock='${numlock}' (attendu : 0)"; fi
check "favoris du menu de démarrage" grep -q 'org.onlyoffice.desktopeditors.desktop' /etc/xdg/kicker-extra-favoritesrc
check "OnlyOffice associé aux .docx" \
    grep -qx 'application/vnd.openxmlformats-officedocument.wordprocessingml.document=org.onlyoffice.desktopeditors.desktop' /etc/xdg/kde-mimeapps.list

check "barre des tâches en haut de l'écran" \
    grep -q 'panel.location = "top"' "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"
check "logo NicOS sur le bouton Démarrer" \
    grep -q 'writeConfig("icon", "nicos")' "${LNF}/contents/layouts/org.kde.plasma.desktop-layout.js"

section "Identité visuelle"
# shellcheck source=/dev/null  # fichier de l'image, absent du dépôt
. /usr/lib/os-release
if [[ "${NAME}" == NicOS && "${LOGO}" == nicos ]]; then pass "os-release : ${PRETTY_NAME}"; else fail "os-release : NAME='${NAME}' LOGO='${LOGO}'"; fi
if [[ "${ID}" == fedora ]]; then pass "ID=fedora conservé"; else fail "ID='${ID}' (attendu : fedora)"; fi
check "icône NicOS installée" test -s /usr/share/icons/hicolor/scalable/apps/nicos.svg
check "logos Fedora remplacés (generic-logos)" bash -c '! rpm -q fedora-logos && rpm -q generic-logos'
check "fond d'écran NicOS (clair et sombre)" \
    test -s /usr/share/wallpapers/NicOS/contents/images/1920x1080.jpg -a -s /usr/share/wallpapers/NicOS/contents/images_dark/1920x1080.jpg
check "fond d'écran par défaut du bureau" grep -qx 'Image=NicOS' "${LNF}/contents/defaults"
check "fond d'écran de l'écran de verrouillage" grep -q 'wallpapers/NicOS' /etc/xdg/kscreenlockerrc
check "fond d'écran de l'écran de connexion" grep -q 'wallpapers/NicOS' /usr/lib/plasmalogin/defaults.conf
check "logo NicOS dans « À propos »" grep -q 'nicos.svg' /etc/xdg/kcm-about-distrorc
theme="$(plymouth-set-default-theme 2>/dev/null)"
if [[ "${theme}" == nicos ]]; then pass "écran de démarrage : thème ${theme}"; else fail "thème Plymouth : '${theme}' (attendu : nicos)"; fi
check "animation de chargement copiée dans le thème" test -s /usr/share/plymouth/themes/nicos/throbber-0001.png
check "thème de démarrage présent dans l'initramfs" \
    bash -c 'lsinitrd /usr/lib/modules/*/initramfs.img | grep -q "plymouth/themes/nicos/watermark.png"'
check "système de fichiers racine par défaut (bootc)" grep -q 'type = "btrfs"' /usr/lib/bootc/install/50-nicos.toml
check "nom du système pour le firmware (/etc/system-release)" grep -q '^NicOS release ' /etc/system-release
check "/etc/fedora-release conservé pour les outils" grep -q '^Fedora release ' /etc/fedora-release
boot_csv_ok=1
shopt -s nullglob
boot_csvs=(/usr/lib/efi/shim/*/EFI/*/BOOT*.CSV /usr/lib/bootupd/updates/EFI/*/BOOT*.CSV)
shopt -u nullglob
[[ ${#boot_csvs[@]} -gt 0 ]] || boot_csv_ok=0
for csv in "${boot_csvs[@]}"; do
    label="$(iconv -f UTF-16 -t UTF-8 "${csv}")"
    [[ "${label}" == *",NicOS,"* && "${label}" != *Fedora* ]] || boot_csv_ok=0
done
if [[ ${boot_csv_ok} -eq 1 ]]; then pass "entrée de démarrage du firmware : NicOS (${#boot_csvs[@]} fichier(s) BOOT*.CSV)"; else fail "entrée de démarrage du firmware : BOOT*.CSV absent ou encore « Fedora »"; fi

section "Applications Flatpak"
LIST=/usr/share/nicos/flatpaks/system-flatpaks.list
check "liste Flatpak installée dans l'image" test -f "${LIST}"
if [[ -f /flatpaks/system-flatpaks.list ]]; then
    check "liste Flatpak identique à celle du dépôt" cmp -s "${LIST}" /flatpaks/system-flatpaks.list
fi
for app in org.onlyoffice.desktopeditors org.mozilla.firefox org.mozilla.Thunderbird org.kde.okular \
    com.nextcloud.desktopclient.nextcloud org.chromium.Chromium; do
    check "${app} dans la liste" grep -qx "${app}" "${LIST}"
done

section "Web apps"
for webapp in teams zoom slack; do
    check "lanceur ${webapp} valide" desktop-file-validate "/usr/share/applications/nicos-webapp-${webapp}.desktop"
done
check "lanceur de web apps exécutable" test -x /usr/libexec/nicos/nicos-webapp

section "Services"
for unit in nicos-flatpak-install.service nicos-pdf-printer.service plasma-setup.service; do
    state="$(systemctl is-enabled "${unit}" 2>/dev/null)"
    if [[ "${state}" == enabled ]]; then pass "${unit} activé"; else fail "${unit} : '${state}' (attendu : enabled)"; fi
done
check "script d'installation Flatpak exécutable" test -x /usr/libexec/nicos/nicos-flatpak-install
check "syntaxe des unités systemd NicOS" \
    systemd-analyze verify --man=no --recursive-errors=no \
    /usr/lib/systemd/system/nicos-flatpak-install.service /usr/lib/systemd/system/nicos-pdf-printer.service
check "pilote de l'imprimante PDF (PPD)" test -f /usr/share/cups/model/CUPS-PDF_noopt.ppd
check "backend CUPS de l'imprimante PDF" test -x /usr/lib/cups/backend/cups-pdf

printf '\n'
if [[ ${failures} -gt 0 ]]; then
    printf '%d vérification(s) en échec.\n' "${failures}"
    exit 1
fi
printf 'Toutes les vérifications de l'\''image sont passées.\n'
