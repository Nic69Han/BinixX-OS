# shellcheck shell=bash
section "Applications GTK aux couleurs de BinixX OS"
for pkg in breeze-gtk-gtk3 breeze-gtk-gtk4 kde-gtk-config; do
    check "paquet ${pkg}" rpm -q "${pkg}"
done
check "thème Breeze GTK 3 présent" test -f /usr/share/themes/Breeze/gtk-3.0/gtk.css
check "module kded de kde-gtk-config (report des réglages KDE vers GTK)" \
    bash -c 'ls /usr/lib64/qt6/plugins/kf6/kded/gtkconfig.so >/dev/null 2>&1 || find /usr/lib64 -name "gtkconfig.so" | grep -q .'
PREFS=/usr/lib64/firefox/browser/defaults/preferences/binixx-prefs.js
check "Firefox : boîte « Ouvrir / Enregistrer » de KDE" grep -q 'widget.use-xdg-desktop-portal.file-picker", 1' "${PREFS}"
check "Firefox : fichiers téléchargés ouverts par l'application choisie dans KDE" grep -q 'widget.use-xdg-desktop-portal.mime-handler", 1' "${PREFS}"
check "Flatpak : réglages GTK lisibles par les applications (permission posée à chaque démarrage)" \
    grep -q 'flatpak override --system --filesystem=xdg-config/gtk-3.0:ro --filesystem=xdg-config/gtk-4.0:ro' /usr/libexec/binixx/binixx-flatpak-install
check "Flatpak : thème Breeze des applications GTK 3 installé au démarrage" grep -q 'org.gtk.Gtk3theme.Breeze' /usr/libexec/binixx/binixx-flatpak-install
