#!/usr/bin/bash
# Personnalisation de l'image NicOS, exécutée une seule fois pendant `podman build`.
# Le contexte de build (build_files/, system_files/, flatpaks/) est monté sur /ctx.

set -ouex pipefail

### 1. Fichiers système
# Configs KDE, services systemd, lanceurs de web apps (voir system_files/)
cp -avf /ctx/system_files/. /

### 2. Paquets RPM
# kinoite-main fournit déjà CUPS, hplip, gutenprint, PipeWire et le portail KDE ;
# on les liste quand même pour que le build échoue si l'un d'eux disparaît de la base.

# Polices compatibles en métrique avec les polices Microsoft (même largeur de caractères,
# donc même mise en page) : Carlito = Calibri, Caladea = Cambria,
# Liberation = Arial / Times New Roman / Courier New.
# fontconfig fait déjà la substitution (30-metric-aliases.conf).
FONTS=(
    google-carlito-fonts
    google-crosextra-caladea-fonts
    liberation-mono-fonts
    liberation-sans-fonts
    liberation-serif-fonts
)

# Impression : impression sans pilote (IPP Everywhere) + pilotes courants
# + imprimante virtuelle PDF (Cups-PDF, créée au premier démarrage)
PRINTING=(
    c2esp
    cups
    cups-browsed
    cups-filters
    cups-pdf
    foo2zjs
    foomatic-db-ppds
    gutenprint-cups
    hplip
    plasma-print-manager
    printer-driver-brlaser
    ptouch-driver
    splix
    system-config-printer-udev
)

# Numérisation : SANE, scanners réseau (eSCL/WSD) et USB modernes (ipp-usb),
# scanners HP, et Skanpage comme application de numérisation
SCANNING=(
    ipp-usb
    libsane-hpaio
    sane-airscan
    sane-backends
    sane-backends-drivers-scanners
    skanpage
)

# Visioconférence sous Wayland : partage d'écran via PipeWire et le portail KDE
VIDEOCONF=(
    pipewire
    wireplumber
    xdg-desktop-portal
    xdg-desktop-portal-kde
)

# Sécurité : état Secure Boot et enrôlement de clés MOK
SECURITY=(
    mokutil
)

dnf5 -y install \
    "${FONTS[@]}" \
    "${PRINTING[@]}" \
    "${SCANNING[@]}" \
    "${VIDEOCONF[@]}" \
    "${SECURITY[@]}"

### 3. Bureau Plasma façon Windows
# Thème global org.nicos.desktop : copie complète de Breeze (clair), puis nos fichiers
# (system_files/…/org.nicos.desktop) par-dessus. --update=none ne remplace aucun
# fichier déjà présent, donc nos defaults et notre disposition du panneau sont conservés.
LNF_DIR=/usr/share/plasma/look-and-feel
cp -a --update=none "${LNF_DIR}/org.kde.breeze.desktop/." "${LNF_DIR}/org.nicos.desktop/"

# Thème global par défaut pour tous les utilisateurs.
# Fedora le définit dans kde-settings (priorité plus basse que /etc/xdg) : on corrige les deux.
kwriteconfig6 --file /etc/xdg/kdeglobals --group KDE --key LookAndFeelPackage org.nicos.desktop
KDE_SETTINGS_GLOBALS=/usr/share/kde-settings/kde-profile/default/xdg/kdeglobals
if [[ -f "${KDE_SETTINGS_GLOBALS}" ]]; then
    sed -i 's/^LookAndFeelPackage=.*/LookAndFeelPackage=org.nicos.desktop/' "${KDE_SETTINGS_GLOBALS}"
fi

# Pavé numérique activé à l'ouverture de session, comme sous Windows (0 = activé)
kwriteconfig6 --file /etc/xdg/kcminputrc --group Keyboard --key NumLock 0

### 4. Applications Flatpak
# La liste est installée au premier démarrage par nicos-flatpak-install.service
# (les Flatpak vivent dans /var, ils ne peuvent pas être intégrés à l'image).
install -Dm0644 /ctx/flatpaks/system-flatpaks.list /usr/share/nicos/flatpaks/system-flatpaks.list

### 5. Services
systemctl enable nicos-flatpak-install.service
systemctl enable nicos-pdf-printer.service
# Assistant de premier démarrage (langue, clavier, réseau, fuseau horaire, compte) :
# l'ISO ne crée pas de compte, c'est lui qui s'en charge.
systemctl enable plasma-setup.service
