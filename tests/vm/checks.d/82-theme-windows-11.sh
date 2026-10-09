# shellcheck shell=bash
# Style Windows 11 (Win11OS KDE) : Aube, Nuit et Contraste élevé posés pour de vrai dans la session de l'utilisateur de test.
#  - phase base : un compte neuf a reçu le thème Kvantum clair de /etc/skel, la surveillance de kdeglobals tourne, et le thème Kvantum
#    suit un changement de couleurs sans que rien d'autre ne le demande ;
#  - phases theme-aube, theme-nuit et theme-contraste (lancées par run-vm-test.sh après la mise à jour, qui photographie l'écran
#    pendant que Dolphin est ouvert, puis avec le menu de démarrage ouvert) : l'ambiance est posée, on relit chaque réglage que
#    le thème global devait écrire (style, fenêtres, thème Plasma, thème Kvantum), puis Dolphin s'ouvre ;
#  - phase theme-fin : retour à Aube.
theme_session() {
    local uid
    uid="$(id -u "${TEST_USER}")"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"
}
# Valeur d'un réglage : celle de l'utilisateur ; tant qu'il n'a rien choisi, celle que le thème global a posée dans kdedefaults
theme_reglage() {
    local valeur
    valeur="$(theme_session kreadconfig6 --file "$1" --group "$2" --key "$3")"
    if [[ -z "${valeur}" ]]; then valeur="$(theme_session kreadconfig6 --file "${TEST_HOME}/.config/kdedefaults/$1" --group "$2" --key "$3")"; fi
    printf '%s' "${valeur}"
}
theme_kvantum() { theme_session kreadconfig6 --file "${TEST_HOME}/.config/Kvantum/kvantum.kvconfig" --group General --key theme; }

check_theme_base() {
    section "Style Windows 11 (compte neuf, thème Kvantum qui suit les couleurs)"
    local theme
    check "thème Kvantum du compte de l'installation (copié de /etc/skel) : Win11OS-light" test "$(theme_kvantum)" = Win11OS-light
    check "le style Qt 6 « kvantum » est installé" test -s /usr/lib64/qt6/plugins/styles/libkvantum.so
    check "kdedefaults : style des applications kvantum (posé par le thème global)" grep -qx 'widgetStyle=kvantum' "${TEST_HOME}/.config/kdedefaults/kdeglobals"
    for fichier in plasmarc kwinrc; do
        echo "            info : kdedefaults/${fichier} : $(tr '\n' ' ' <"${TEST_HOME}/.config/kdedefaults/${fichier}" 2>/dev/null | cut -c1-200)"
    done
    local unite
    for unite in binixx-kvantum.path binixx-kvantum.service; do
        echo "            info : ${unite} : actif=$(theme_session systemctl --user is-active "${unite}" 2>&1 | head -n 1), activé=$(theme_session systemctl --user is-enabled "${unite}" 2>&1 | head -n 1)"
    done
    if [[ "$(theme_session systemctl --user is-active binixx-kvantum.path 2>&1)" == active ]]; then
        pass "la surveillance de kdeglobals (binixx-kvantum.path) tourne dans la session"
    else
        fail "binixx-kvantum.path n'est pas actif : $(theme_session systemctl --user status binixx-kvantum.path --no-pager 2>&1 | tail -n 5 | tr '\n' ' ' | cut -c1-300)"
    fi

    # Le thème Kvantum doit suivre un changement de couleurs sans que personne ne le demande (Configuration du système, thème automatique…) :
    # on change seulement le nom du schéma dans kdeglobals et on attend ; puis on remet ce qui y était
    local avant
    avant="$(theme_reglage kdeglobals General ColorScheme)"
    theme_session kwriteconfig6 --file kdeglobals --group General --key ColorScheme BinixXSombre
    if wait_for 30 test "$(theme_kvantum)" = Win11OS-dark; then
        pass "couleurs sombres écrites dans kdeglobals : le thème Kvantum est passé à Win11OS-dark tout seul"
    else
        fail "le thème Kvantum n'a pas suivi les couleurs sombres : '$(theme_kvantum)' ; $(theme_session systemctl --user status binixx-kvantum.service --no-pager 2>&1 | tail -n 4 | tr '\n' ' ' | cut -c1-300)"
    fi
    theme_session kwriteconfig6 --file kdeglobals --group General --key ColorScheme BinixXClair
    if wait_for 30 test "$(theme_kvantum)" = Win11OS-light; then
        pass "couleurs claires écrites dans kdeglobals : le thème Kvantum est revenu à Win11OS-light tout seul"
    else
        fail "le thème Kvantum n'a pas suivi les couleurs claires : '$(theme_kvantum)'"
    fi
    if [[ -n "${avant}" ]]; then
        theme_session kwriteconfig6 --file kdeglobals --group General --key ColorScheme "${avant}"
    else
        theme_session kwriteconfig6 --file kdeglobals --group General --key ColorScheme --delete
    fi
    theme=Win11OS-light
    [[ "${avant}" == BinixXSombre ]] && theme=Win11OS-dark
    wait_for 30 test "$(theme_kvantum)" = "${theme}" || true
    echo "            info : couleurs remises à '${avant:-(rien dans kdeglobals)}', thème Kvantum : $(theme_kvantum)"
}
register_check base check_theme_base

# theme_egal <ce qu'on contrôle> <valeur lue> <valeur attendue>
theme_egal() {
    if [[ "$2" == "$3" ]]; then pass "$1 : $3"; else fail "$1 : '$2' ($3 attendu)"; fi
}

theme_fenetre_ouverte() { theme_session busctl --user list --no-legend | grep -q 'org\.kde\.dolphin'; }

# Pose une ambiance, relit chaque réglage du thème global, puis ouvre Dolphin pour la capture d'écran
# theme_scene <ambiance> <couleurs> <style> <décoration des fenêtres> <thème Plasma> <thème Kvantum ou rien>
theme_scene() {
    local ambiance="$1" couleurs="$2" style="$3" decoration="$4" plasma="$5" kvantum="$6" out uid socket lu
    section "Style Windows 11 : ${ambiance}"
    if ! wait_for 120 theme_session busctl --user status org.kde.plasmashell; then
        fail "Plasma ne répond pas sur le bus de la session : ${ambiance} ne peut pas être posé"
        return
    fi
    if out="$(theme_session /usr/libexec/binixx/binixx-ambiance appliquer "${ambiance}" 2>&1)"; then pass "binixx-ambiance appliquer ${ambiance} : ${out}"; else fail "appliquer ${ambiance} : ${out:0:300}"; fi
    sleep 3
    theme_egal "couleurs" "$(theme_reglage kdeglobals General ColorScheme)" "${couleurs}"
    theme_egal "style des applications" "$(theme_reglage kdeglobals KDE widgetStyle)" "${style}"
    theme_egal "décoration des fenêtres" "$(theme_reglage kwinrc org.kde.kdecoration2 theme)" "${decoration}"
    lu="$(theme_reglage plasmarc Theme name)"
    theme_egal "thème Plasma" "${lu:-default}" "${plasma}"
    echo "            info : boutons des fenêtres : gauche '$(theme_reglage kwinrc org.kde.kdecoration2 ButtonsOnLeft)', droite '$(theme_reglage kwinrc org.kde.kdecoration2 ButtonsOnRight)'"
    if [[ -n "${kvantum}" ]]; then theme_egal "thème Kvantum" "$(theme_kvantum)" "${kvantum}"; fi
    uid="$(id -u "${TEST_USER}")"
    socket="$(find "/run/user/${uid}" -maxdepth 1 -name 'wayland-[0-9]*' ! -name '*.lock' -printf '%f\n' | sort | head -n 1)"
    if [[ -z "${socket}" ]]; then
        fail "aucune socket Wayland dans /run/user/${uid} : la session graphique n'est pas ouverte"
        return
    fi
    # Comme une application du menu (environnement de Plasma) : voir 86-explorateur.sh
    theme_session systemd-run --user --collect --quiet --unit="binixx-test-dolphin-${ambiance}" \
        -E WAYLAND_DISPLAY="${socket}" -E QT_QPA_PLATFORM=wayland -E XDG_CURRENT_DESKTOP=KDE -E KDE_FULL_SESSION=true \
        dolphin --new-window "${TEST_HOME}" >"/tmp/dolphin-${ambiance}.log" 2>&1
    if wait_for 90 theme_fenetre_ouverte; then pass "Dolphin est ouvert (capture d'écran)"; else
        fail "Dolphin ne s'ouvre pas : $(tail -n 5 "/tmp/dolphin-${ambiance}.log" | tr '\n' ' ' | cut -c1-300)"
        return
    fi
    sleep 10 # le temps d'afficher la fenêtre avant la capture d'écran
}
check_theme_aube() { theme_scene aube BinixXClair kvantum __aurorae__svg__Win11OS-light Win11OS-light Win11OS-light; }
check_theme_nuit() { theme_scene nuit BinixXSombre kvantum __aurorae__svg__Win11OS-dark Win11OS-dark Win11OS-dark; }
check_theme_contraste() { theme_scene contraste BinixXContraste Breeze Breeze default ""; }
register_check theme-aube check_theme_aube
register_check theme-nuit check_theme_nuit
register_check theme-contraste check_theme_contraste

check_theme_fin() {
    section "Style Windows 11 : retour à Aube"
    local out
    if out="$(theme_session /usr/libexec/binixx/binixx-ambiance appliquer aube 2>&1)"; then pass "binixx-ambiance appliquer aube : ${out}"; else fail "appliquer aube : ${out:0:300}"; fi
    theme_egal "le bureau est revenu à Aube, couleurs" "$(theme_reglage kdeglobals General ColorScheme)" BinixXClair
    wait_for 30 test "$(theme_kvantum)" = Win11OS-light || true
    theme_egal "thème Kvantum" "$(theme_kvantum)" Win11OS-light
}
register_check theme-fin check_theme_fin
