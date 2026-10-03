# shellcheck shell=bash
# Taille du texte : on l'applique pour de vrai dans la session de l'utilisateur de test, on relit les polices dans
# kdeglobals, on regarde si une application Qt les adopte, puis on rétablit (la session de test ne doit pas rester agrandie).
# Les polices de départ peuvent exister (écrites à l'installation) ou non : on compare toujours avec ce qu'on a lu avant.
check_taille_texte() {
    section "Taille du texte (polices de KDE dans la session)"
    local uid out attendue outil=/usr/libexec/binixx/binixx-taille-texte
    local avant_interface avant_petite avant_titres
    uid="$(id -u "${TEST_USER}")"
    session() { runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"; }
    police() { session kreadconfig6 --file kdeglobals --group "$1" --key "$2"; }
    # La taille voulue à 150 % : celle de la police actuelle, ou de celle de KDE (par défaut) si rien n'est écrit
    voulue() { python3 -c 'import sys; v = float(sys.argv[1]) * 1.5; d = round(v * 2) / 2; print(int(d) if d == int(d) else d)' "${1:-$2}"; }
    taille() { cut -d, -f2 <<<"$1"; }
    avant_interface="$(police General font)"
    avant_petite="$(police General smallestReadableFont)"
    avant_titres="$(police WM activeFont)"
    if [[ "$(session "${outil}" etat 2>&1)" == 100 ]]; then pass "au départ le texte est à 100 %"; else fail "état de départ : $(session "${outil}" etat 2>&1)"; fi
    if out="$(session "${outil}" appliquer 150 2>&1)"; then pass "binixx-taille-texte appliquer 150 : ${out}"; else fail "appliquer 150 : ${out:0:300}"; fi
    attendue="$(voulue "$(taille "${avant_interface}")" 10)"
    if [[ "$(taille "$(police General font)")" == "${attendue}" ]]; then
        pass "police de l'interface : ${attendue} points (× 1,5)"
    else
        fail "police de l'interface : '$(police General font)' (${attendue} points attendus)"
    fi
    attendue="$(voulue "$(taille "${avant_petite}")" 8)"
    if [[ "$(taille "$(police General smallestReadableFont)")" == "${attendue}" ]]; then
        pass "plus petite police lisible : ${attendue} points"
    else
        fail "plus petite police lisible : '$(police General smallestReadableFont)' (${attendue} attendus)"
    fi
    attendue="$(voulue "$(taille "${avant_titres}")" 10)"
    if [[ "$(taille "$(police WM activeFont)")" == "${attendue}" ]]; then
        pass "police des titres de fenêtres : ${attendue} points"
    else
        fail "police des titres de fenêtres : '$(police WM activeFont)' (${attendue} attendus)"
    fi
    if [[ "$(session "${outil}" etat 2>&1)" == 150 ]]; then pass "l'état relu est 150 %"; else fail "état relu : $(session "${outil}" etat 2>&1)"; fi
    # Une application Qt adopte-t-elle la nouvelle police ? (le greffon de thème de Plasma lit kdeglobals) : avertissement seulement
    out="$(session env QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=kde python3 -c \
        'from PySide6.QtWidgets import QApplication; print(QApplication([]).font().pointSizeF())' 2>&1 | tail -n 1)"
    attendue="$(voulue "$(taille "${avant_interface}")" 10)"
    if [[ "${out}" == "${attendue}.0" || "${out}" == "${attendue}" ]]; then
        pass "une application Qt prend la police de ${attendue} points"
    else
        warn "une application Qt lit une police de '${out:0:120}' points (${attendue} attendus) : le greffon de thème de Plasma n'est peut-être pas chargé hors session"
    fi
    if out="$(session "${outil}" retablir 2>&1)"; then pass "binixx-taille-texte retablir : ${out}"; else fail "retablir : ${out:0:300}"; fi
    if [[ "$(police General font)" == "${avant_interface}" && "$(police General smallestReadableFont)" == "${avant_petite}" && "$(police WM activeFont)" == "${avant_titres}" ]]; then
        pass "les polices sont exactement comme avant"
    else
        fail "polices après rétablissement : '$(police General font)' / '$(police General smallestReadableFont)' / '$(police WM activeFont)'"
    fi
    if [[ "$(session "${outil}" etat 2>&1)" == 100 ]]; then pass "de nouveau à 100 %"; else fail "état après rétablissement : $(session "${outil}" etat 2>&1)"; fi
}
register_check base check_taille_texte
