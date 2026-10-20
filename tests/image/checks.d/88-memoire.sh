# shellcheck shell=bash
section "Mémoire vive (docs/memoire.md)"
check "zram : générateur installé" rpm -q zram-generator
# shellcheck disable=SC2016  # expansion voulue dans le sous-shell
check "zram : aussi grand que la mémoire vive (8 Go au plus), zstd" bash -c \
    'f=/usr/lib/systemd/zram-generator.conf.d/50-binixx.conf; grep -qx "zram-size = min(ram, 8192)" "$f" && grep -qx "compression-algorithm = zstd" "$f"'
# shellcheck disable=SC2016  # expansion voulue dans le sous-shell
check "noyau : swappiness 150 et page-cluster 0 pour le zram" bash -c \
    'f=/usr/lib/sysctl.d/61-binixx-memoire.conf; grep -qx "vm.swappiness = 150" "$f" && grep -qx "vm.page-cluster = 0" "$f"'
check "Baloo : noms de fichiers seulement, pas le contenu" grep -qx 'only basic indexing=true' /etc/xdg/baloofilerc
check "installation des applications au premier démarrage : mémoire et processeur limités" grep -qx 'MemoryHigh=512M' \
    /usr/lib/systemd/system/binixx-flatpak-install.service.d/50-binixx-memoire.conf
check "Firefox : réglages de mémoire par défaut" grep -q 'browser.tabs.unloadOnLowMemory' \
    /usr/lib64/firefox/browser/defaults/preferences/binixx-memoire.js
for autostart in org.kde.discover.notifier.desktop org.kde.kdeconnect.daemon.desktop; do
    [[ -f "/etc/xdg/autostart/${autostart}" ]] || continue
    check "${autostart} : plus lancé avec la session" grep -qx 'Hidden=true' "/etc/xdg/autostart/${autostart}"
done
