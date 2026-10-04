#!/usr/bin/bash
# Personnalisation de l'image BinixX OS, exécutée une seule fois pendant `podman build`.
# Le contexte de build (build_files/, system_files/, flatpaks/) est monté sur /ctx.

set -ouex pipefail

### 0. Correctifs de sécurité
# En premier : une mise à jour de paquet rétablit les fichiers d'origine (Firefox, thèmes « Fedora »), elle ne doit donc
# pas passer après les sections de personnalisation ci-dessous (securite.sh).
bash /ctx/securite.sh

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

# Administration à la souris : Cockpit, console web de Fedora (domaine Active Directory, mises à
# jour et retour arrière, pare-feu, disques, services, journaux), et pare-feu dans
# Configuration du système (plasma-firewall)
ADMINISTRATION=(
    cockpit
    cockpit-files
    cockpit-networkmanager
    cockpit-ostree
    cockpit-selinux
    cockpit-storaged
    plasma-firewall
    plasma-firewall-firewalld
)

# Français : correcteur orthographique, césure et synonymes pour les applications KDE
# (l'image de base n'a que l'anglais)
LANGUAGE=(
    hunspell-fr
    langpacks-fr
)

# OneDrive : client libre de synchronisation, configuré par l'assistant « OneDrive » du menu
CLOUD=(
    onedrive
)

# VPN intégrés à Windows (L2TP/IPsec, IKEv2, SSTP), réglables dans les paramètres réseau.
# OpenVPN, Cisco AnyConnect (OpenConnect) et WireGuard sont déjà dans l'image de base.
VPN=(
    plasma-nm-l2tp
    plasma-nm-sstp
    plasma-nm-strongswan
)

# PME : rejoindre un domaine Active Directory (`realm join`, realmd est dans la base) et
# ouvrir sa session avec son compte Windows ; le dossier personnel est créé à la 1re connexion
ENTERPRISE=(
    adcli
    krb5-workstation
    oddjob-mkhomedir
    sssd-ad
)

dnf5 -y install \
    "${ADMINISTRATION[@]}" \
    "${FONTS[@]}" \
    "${PRINTING[@]}" \
    "${SCANNING[@]}" \
    "${VIDEOCONF[@]}" \
    "${SECURITY[@]}" \
    "${LANGUAGE[@]}" \
    "${CLOUD[@]}" \
    "${VPN[@]}" \
    "${ENTERPRISE[@]}"

# Selawik (remplace Segoe UI, voir branding/fabriquer-selawik.sh) vient de system_files :
# cache de fontconfig régénéré pour l'inclure
fc-cache -s

### 3. Bureau Plasma
# Thème global org.binixx.desktop : copie complète de Breeze (clair), puis nos fichiers
# (system_files/…/org.binixx.desktop) par-dessus. --update=none ne remplace aucun
# fichier déjà présent, donc nos defaults et notre disposition du panneau sont conservés.
LNF_DIR=/usr/share/plasma/look-and-feel
cp -a --update=none "${LNF_DIR}/org.kde.breeze.desktop/." "${LNF_DIR}/org.binixx.desktop/"
# Thème global sombre org.binixx.dark.desktop : même disposition, reste copié de Brise sombre
cp -a "${LNF_DIR}/org.binixx.desktop/contents/layouts" "${LNF_DIR}/org.binixx.dark.desktop/contents/"
cp -a --update=none "${LNF_DIR}/org.kde.breezedark.desktop/." "${LNF_DIR}/org.binixx.dark.desktop/"

# Couleurs BinixX OS clair et sombre : celles de Brise, avec le bleu BinixX OS comme couleur d'accent
# (sélection, survol, focus, liens), comme les couleurs d'accent de Zorin OS 18. Générées
# depuis les fichiers de Brise de l'image, pour suivre ses mises à jour.
python3 - <<'PYEOF'
SCHEMES = {
    # Brise : (fichier BinixX OS, nom affiché, couleurs remplacées)
    "BreezeLight": ("BinixXClair", "BinixX OS clair",
                    {"61,174,233": "47,91,255", "41,128,185": "34,72,224", "29,153,243": "90,125,255"}),
    "BreezeDark": ("BinixXSombre", "BinixX OS sombre",
                   {"61,174,233": "90,125,255", "29,153,243": "140,170,255"}),
}
for source, (scheme, name, colors) in SCHEMES.items():
    lines, replaced = [], 0
    with open(f"/usr/share/color-schemes/{source}.colors", encoding="utf-8") as f:
        for line in f:
            key, sep, value = line.rstrip("\n").partition("=")
            if key.startswith("Name["):  # noms traduits de Brise
                continue
            if sep and value in colors:
                line, replaced = f"{key}={colors[value]}\n", replaced + 1
            elif key == "Name":
                line = f"Name={name}\n"
            elif key == "ColorScheme":
                line = f"ColorScheme={scheme}\n"
            lines.append(line)
    if replaced < 20:  # Brise a changé de couleurs : à revoir
        raise SystemExit(f"{source}.colors : {replaced} couleurs d'accent remplacées seulement")
    with open(f"/usr/share/color-schemes/{scheme}.colors", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"{scheme}.colors : {replaced} couleurs d'accent BinixX OS")
PYEOF

# Thème global par défaut pour tous les utilisateurs.
# Fedora le définit dans kde-settings (priorité plus basse que /etc/xdg) : on corrige les deux.
kwriteconfig6 --file /etc/xdg/kdeglobals --group KDE --key LookAndFeelPackage org.binixx.desktop
KDE_SETTINGS_GLOBALS=/usr/share/kde-settings/kde-profile/default/xdg/kdeglobals
if [[ -f "${KDE_SETTINGS_GLOBALS}" ]]; then
    sed -i 's/^LookAndFeelPackage=.*/LookAndFeelPackage=org.binixx.desktop/' "${KDE_SETTINGS_GLOBALS}"
fi
# Paire clair / sombre proposée par Configuration du système → Thème global (bascule
# automatique selon l'heure possible)
kwriteconfig6 --file /etc/xdg/kdeglobals --group KDE --key DefaultLightLookAndFeel org.binixx.desktop
kwriteconfig6 --file /etc/xdg/kdeglobals --group KDE --key DefaultDarkLookAndFeel org.binixx.dark.desktop

# Fenêtres, comme Zorin OS 18 :
# - les nouvelles fenêtres s'ouvrent au centre de l'écran ;
# - glisser une fenêtre vers le haut de l'écran propose des dispositions (deux colonnes, deux
#   lignes, quatre quarts), comme les « Snap Layouts » de Windows 11 : script KWin
#   kde-snap-overlay (usr/share/kwin/scripts/), qui s'appuie sur l'ancrage natif de KWin.
kwriteconfig6 --file /etc/xdg/kwinrc --group Windows --key Placement Centered
kwriteconfig6 --file /etc/xdg/kwinrc --group Plugins --key kde-snap-overlayEnabled true

# Pavé numérique activé à l'ouverture de session, comme sous Windows (0 = activé)
kwriteconfig6 --file /etc/xdg/kcminputrc --group Keyboard --key NumLock 0

### 4. Identité visuelle BinixX OS
# Logo, icône, fond d'écran et écran de démarrage viennent de system_files/
# (générés par branding/generer.py).

# Logos Fedora remplacés par des logos génériques, comme le demande la politique de
# marque Fedora pour un système dérivé.
dnf5 -y swap fedora-logos generic-logos

# Nom du système (« À propos », menu de démarrage GRUB, accueil). ID=fedora est conservé :
# les outils s'en servent pour reconnaître la base Fedora.
sed -i \
    -e 's/^NAME=.*/NAME="BinixX OS"/' \
    -e "s/^PRETTY_NAME=.*/PRETTY_NAME=\"BinixX OS $(rpm -E %fedora)\"/" \
    -e 's/^LOGO=.*/LOGO=binixx/' \
    -e 's|^HOME_URL=.*|HOME_URL="https://github.com/Nic69Han/BinixX-OS"|' \
    -e 's|^DOCUMENTATION_URL=.*|DOCUMENTATION_URL="https://github.com/Nic69Han/BinixX-OS/tree/main/docs"|' \
    -e 's|^SUPPORT_URL=.*|SUPPORT_URL="https://github.com/Nic69Han/BinixX-OS/issues"|' \
    -e 's|^BUG_REPORT_URL=.*|BUG_REPORT_URL="https://github.com/Nic69Han/BinixX-OS/issues"|' \
    -e 's/^DEFAULT_HOSTNAME=.*/DEFAULT_HOSTNAME="binixx"/' \
    /usr/lib/os-release

# Fond d'écran BinixX OS sur l'écran de verrouillage et l'écran de connexion
# (le bureau le prend dans le thème global org.binixx.desktop)
BINIXX_WALLPAPER=file:///usr/share/wallpapers/BinixX/
kwriteconfig6 --file /etc/xdg/kscreenlockerrc --group Greeter --key WallpaperPlugin org.kde.image
for key in Image PreviewImage; do
    kwriteconfig6 --file /etc/xdg/kscreenlockerrc \
        --group Greeter --group Wallpaper --group org.kde.image --group General --key "${key}" "${BINIXX_WALLPAPER}"
    kwriteconfig6 --file /usr/lib/plasmalogin/defaults.conf \
        --group Greeter --group Wallpaper --group org.kde.image --group General --key "${key}" "${BINIXX_WALLPAPER}"
done

# Écran de démarrage : thème Plymouth BinixX OS. Le logo (watermark.png) et la roue de chargement (throbber-*.png, branding/roue_demarrage.py)
# sont à nous ; les autres images (champ de mot de passe, cadenas, clavier…) viennent du thème « spinner » de Fedora. Les images de la roue
# de Fedora ne sont pas copiées : une image de plus ou de moins dans l'animation la ferait sauter.
find /usr/share/plymouth/themes/spinner -maxdepth 1 -type f ! -name 'throbber-*' ! -name spinner.plymouth \
    -exec cp -a --update=none -t /usr/share/plymouth/themes/binixx/ {} +
plymouth-set-default-theme binixx

# Nom de l'entrée de démarrage dans le firmware du PC (menu F12 / Échap) : « BinixX OS ».
# - À l'installation, bootupd crée l'entrée avec le nom lu dans /etc/system-release
#   (Anaconda le lance dans le système installé) ;
# - si l'entrée disparaît, le firmware la recrée d'après BOOTX64.CSV.
# Les binaires signés (shim, GRUB) et le dossier EFI/fedora ne changent pas : Secure Boot
# en dépend. /etc/fedora-release et ID=fedora restent pour les outils.
system_release="$(sed 's/^Fedora/BinixX OS/' /etc/fedora-release)"
rm -f /etc/system-release
printf '%s\n' "${system_release}" >/etc/system-release
shopt -s nullglob
boot_csvs=(/usr/lib/efi/shim/*/EFI/*/BOOT*.CSV /usr/lib/bootupd/updates/EFI/*/BOOT*.CSV)
shopt -u nullglob
if [[ ${#boot_csvs[@]} -eq 0 ]]; then
    echo "BOOT*.CSV introuvable : impossible de renommer l'entrée de démarrage" >&2
    exit 1
fi
for csv in "${boot_csvs[@]}"; do
    # Fichier UTF-16 avec BOM, comme l'original ; cat garde les droits du fichier
    iconv -f UTF-16 -t UTF-8 "${csv}" | sed 's/Fedora/BinixX OS/g' | iconv -f UTF-8 -t UTF-16 >/tmp/boot.csv
    cat /tmp/boot.csv >"${csv}"
    rm -f /tmp/boot.csv
done

# Plus de « Fedora » visible dans le bureau. plasma-workspace et plasma-setup imposent ces
# paquets : on retire seulement ce qui s'affiche.
# - Thèmes globaux « Fedora », « Fedora Dark », « Fedora Light » (Configuration du système) et
#   fond d'écran « Fedora Forty-Four » (choix du fond d'écran) : repérés par leur nom affiché.
# - Le fond d'écran « par défaut » de KDE (lien Default) devient celui de BinixX OS.
python3 - <<'PYEOF'
import json, pathlib, shutil
for folder in ("/usr/share/plasma/look-and-feel", "/usr/share/wallpapers"):
    for meta in sorted(pathlib.Path(folder).glob("*/metadata.json")):
        if meta.parent.is_symlink():  # Default -> F44 : seul le dossier réel compte
            continue
        name = json.loads(meta.read_text()).get("KPlugin", {}).get("Name", "")
        if "fedora" in name.lower():
            print(f"Retiré : {meta.parent} ({name})")
            shutil.rmtree(meta.parent)
PYEOF
ln -sfn BinixX /usr/share/wallpapers/Default

# Firefox (paquet de Fedora) : page d'accueil et raccourci épinglé « Fedora Project - Start
# Page », « Mozilla Firefox for Fedora » dans « À propos ». Page d'accueil de Firefox, et BinixX OS.
FIREFOX_DIR=/usr/lib64/firefox
sed -i '/start\.fedoraproject\.org/d' "${FIREFOX_DIR}/browser/defaults/preferences/firefox-redhat-default-prefs.js"
cat >"${FIREFOX_DIR}/distribution/distribution.ini" <<'INIEOF'
[Global]
id=binixx
version=1.0
about=Mozilla Firefox pour BinixX OS

[Preferences]
app.distributor=binixx
app.distributor.channel=binixx
INIEOF

# Discover ne propose que Flathub : pas de source d'applications « Fedora »
# (binixx-flatpak-install retire aussi une source déjà ajoutée)
if [[ -f /usr/lib/systemd/system/flatpak-add-fedora-repos.service ]]; then
    systemctl mask flatpak-add-fedora-repos.service
fi

### 5. Applications Flatpak
# La liste est installée au premier démarrage par binixx-flatpak-install.service
# (les Flatpak vivent dans /var, ils ne peuvent pas être intégrés à l'image).
install -Dm0644 /ctx/flatpaks/system-flatpaks.list /usr/share/binixx/flatpaks/system-flatpaks.list

### 6. Services
systemctl enable binixx-flatpak-install.service
systemctl enable binixx-pdf-printer.service
# Assistant de premier démarrage (langue, clavier, réseau, fuseau horaire, compte) :
# l'ISO ne crée pas de compte, c'est lui qui s'en charge.
systemctl enable plasma-setup.service
# Centre d'administration (Cockpit), joignable seulement depuis le PC lui-même
# (usr/lib/systemd/system/cockpit.socket.d/50-binixx-localhost.conf)
systemctl enable cockpit.socket

### 7. Sécurité
# Pare-feu : zone binixx par défaut (usr/lib/firewalld/zones/binixx.xml) au lieu de
# FedoraWorkstation, qui accepte les connexions entrantes sur les ports 1025 à 65535.
# --check-config fait échouer le build si la zone ou un de ses services est invalide.
firewall-offline-cmd --set-default-zone=binixx
firewall-offline-cmd --check-config
# Pas de serveur SSH par défaut : l'administrateur l'active au besoin (docs/securite.md)
systemctl disable sshd.service
# Noyau : usr/lib/sysctl.d/60-binixx-durcissement.conf ; Firefox : etc/firefox/policies/

### 8. Modules
# Un fichier build_files/modules.d/NN-nom.sh par fonctionnalité, exécuté dans l'ordre (voir
# modules.d/README.md). Les chantiers s'y ajoutent sans toucher aux sections ci-dessus.
for module in /ctx/modules.d/*.sh; do
    [[ -e "${module}" ]] || continue
    echo "::group::module ${module##*/}"
    bash "${module}"
    echo "::endgroup::"
done

### 9. Initramfs
# Le thème de démarrage est chargé depuis l'initramfs : on le régénère en dernier,
# avec la même commande que l'image de base Universal Blue.
KERNEL_VERSION="$(rpm -q --queryformat='%{evr}.%{arch}' kernel-core)"
export DRACUT_NO_XATTR=1
dracut --no-hostonly --kver "${KERNEL_VERSION}" --reproducible --add ostree \
    -f "/usr/lib/modules/${KERNEL_VERSION}/initramfs.img"
chmod 0600 "/usr/lib/modules/${KERNEL_VERSION}/initramfs.img"
