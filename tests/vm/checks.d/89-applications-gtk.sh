# shellcheck shell=bash
# Applications GTK aux couleurs de BinixX OS (docs/applications-unifiees.md).
#  - phase base : kde-gtk-config a reporté dans les réglages GTK du compte le thème Breeze, la police Inter et les icônes de
#    BinixX OS ; les Flatpak GTK lisent ces réglages (permission globale) et ont le thème Breeze (extension de Flathub) ;
#    Firefox est réglé pour la boîte « Ouvrir / Enregistrer » de KDE ;
#  - phase applications (lancée par run-vm-test.sh, qui photographie ensuite l'écran : applications-gtk.png) : Firefox s'ouvre
#    dans la vraie session, sur ses paramètres ; la fenêtre reste ouverte pour la capture.
applications_session() {
    local uid
    uid="$(id -u "${TEST_USER}")"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"
}

reglage_gtk() { # reglage_gtk <version 3.0|4.0> <clé> : valeur dans les réglages GTK du compte
    sed -n "s/^$2=//p" "${TEST_HOME}/.config/gtk-$1/settings.ini" 2>/dev/null | head -n 1
}

reglages_gtk_synchronises() { [[ "$(reglage_gtk 3.0 gtk-theme-name)" == Breeze* ]]; }

check_applications_gtk() {
    section "Applications GTK aux couleurs de BinixX OS"
    local valeur
    if wait_for 120 reglages_gtk_synchronises; then
        pass "thème GTK 3 du compte : $(reglage_gtk 3.0 gtk-theme-name) (reporté de KDE par kde-gtk-config)"
    else
        fail "réglages GTK du compte non synchronisés : gtk-theme-name='$(reglage_gtk 3.0 gtk-theme-name)' ($(ls -la "${TEST_HOME}/.config/gtk-3.0" 2>&1 | tr '\n' ' ' | cut -c1-300))"
    fi
    valeur="$(reglage_gtk 3.0 gtk-font-name)"
    if [[ "${valeur}" == Inter* ]]; then pass "police des applications GTK : ${valeur}"; else fail "police GTK : '${valeur}' (Inter attendue)"; fi
    valeur="$(reglage_gtk 3.0 gtk-icon-theme-name)"
    if [[ "${valeur}" == binixx-os* ]]; then pass "icônes des applications GTK : ${valeur}"; else fail "icônes GTK : '${valeur}' (binixx-os attendu)"; fi
    valeur="$(reglage_gtk 3.0 gtk-cursor-theme-name)"
    if [[ "${valeur}" == binixx-curseurs ]]; then pass "pointeur des applications GTK : ${valeur}"; else warn "pointeur GTK : '${valeur}'"; fi
    echo "            info : boutons des fenêtres GTK : $(reglage_gtk 3.0 gtk-decoration-layout) ; GTK 4 : $(reglage_gtk 4.0 gtk-theme-name)"
    if grep -rqs "0C6EEE\|#0c6eee\|12, *110, *238" "${TEST_HOME}/.config/gtk-3.0/colors.css" "${TEST_HOME}/.config/gtk-4.0/colors.css"; then
        pass "couleurs GTK au bleu BinixX (colors.css)"
    else
        fail "bleu BinixX absent des couleurs GTK du compte ($(ls "${TEST_HOME}/.config/gtk-3.0" "${TEST_HOME}/.config/gtk-4.0" 2>&1 | tr '\n' ' '))"
    fi

    valeur="$(flatpak override --system --show 2>&1)"
    if grep -q 'xdg-config/gtk-3.0:ro' <<<"${valeur}" && grep -q 'xdg-config/gtk-4.0:ro' <<<"${valeur}"; then
        pass "Flatpak : réglages GTK lisibles par toutes les applications (lecture seule)"
    else
        fail "Flatpak : permission globale absente : ${valeur//$'\n'/ ; }"
    fi
    if wait_for "${FLATPAK_TIMEOUT}" flatpak info --system org.gtk.Gtk3theme.Breeze; then
        pass "Flatpak : thème Breeze pour les applications GTK 3 installé"
    else
        fail "Flatpak : org.gtk.Gtk3theme.Breeze absent"
    fi
    check "Firefox : boîte « Ouvrir / Enregistrer » de KDE" \
        grep -q 'widget.use-xdg-desktop-portal.file-picker", 1' /usr/lib64/firefox/browser/defaults/preferences/binixx-prefs.js
}
register_check base check_applications_gtk

firefox_ouvert() { pgrep -u "${TEST_USER}" -x firefox >/dev/null && sleep 1 && pgrep -u "${TEST_USER}" -x firefox >/dev/null; }

check_applications_session() {
    section "Applications GTK : Firefox ouvert dans la session"
    local uid socket
    uid="$(id -u "${TEST_USER}")"
    socket="$(find "/run/user/${uid}" -maxdepth 1 -name 'wayland-[0-9]*' ! -name '*.lock' -printf '%f\n' | sort | head -n 1)"
    if [[ -z "${socket}" ]]; then
        fail "aucune socket Wayland dans /run/user/${uid} : la session graphique n'est pas ouverte"
        return
    fi
    # Lancé par la session de l'utilisateur, comme depuis le menu (environnement de Plasma : portails, thème GTK)
    applications_session systemd-run --user --collect --quiet --unit=binixx-test-firefox \
        -E WAYLAND_DISPLAY="${socket}" -E XDG_CURRENT_DESKTOP=KDE -E KDE_FULL_SESSION=true -E MOZ_ENABLE_WAYLAND=1 \
        firefox --new-window about:preferences >/tmp/firefox-session.log 2>&1
    if wait_for 90 firefox_ouvert; then pass "Firefox est ouvert dans la session (${socket})"; else
        fail "Firefox ne s'ouvre pas : $(applications_session systemctl --user status binixx-test-firefox --no-pager 2>&1 | tail -n 6 | tr '\n' ' ' | cut -c1-400)"
        return
    fi
    sleep 15 # premier lancement : création du profil, puis affichage de la page avant la capture d'écran
}
register_check applications check_applications_session
