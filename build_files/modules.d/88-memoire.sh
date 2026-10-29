#!/usr/bin/bash
# Mémoire vive : ce que l'image allège en plus des fichiers de system_files (zram, sysctl, Baloo, installation Flatpak). docs/memoire.md

set -ouex pipefail

# Lancés avec chaque session et inutiles au public de BinixX OS : le notificateur de Discover (les mises à jour sont automatiques et la
# page « Mises à jour » du Centre les montre) et le démon de KDE Connect (téléphone relié au PC). 25 à 40 Mo chacun. Masqués pour tous
# (Hidden=true), réactivables par compte dans Configuration du système → Démarrage automatique. Absents de la base : rien à faire.
for autostart in org.kde.discover.notifier.desktop org.kde.kdeconnect.daemon.desktop; do
    fichier="/etc/xdg/autostart/${autostart}"
    if [[ -f "${fichier}" ]]; then
        kwriteconfig6 --file "${fichier}" --group "Desktop Entry" --key Hidden --type bool true
    else
        echo "${autostart} absent de la base : rien à masquer"
    fi
done

# Firefox (paquet de la base) : moins de pages gardées en mémoire pour Précédent/Suivant, onglets déchargés quand la mémoire manque,
# pas de préchargement de pages que l'on n'ouvrira peut-être pas. Valeurs par défaut : chacun peut les changer dans about:config.
cat >/usr/lib64/firefox/browser/defaults/preferences/binixx-memoire.js <<'JSEOF'
// BinixX OS : mémoire vive (build_files/modules.d/88-memoire.sh, docs/memoire.md)
pref("browser.tabs.unloadOnLowMemory", true);
pref("browser.sessionhistory.max_total_viewers", 2);
pref("network.prefetch-next", false);
pref("network.predictor.enabled", false);
JSEOF
