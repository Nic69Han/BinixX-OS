# shellcheck shell=bash
# Ambiances : on pose Aube, Nuit puis Contraste élevé pour de vrai dans la session de l'utilisateur de test (Plasma tourne) et on
# relit kdeglobals à chaque fois, puis « Grand texte ». Contraste élevé et Grand texte restent en place jusqu'au redémarrage de
# la phase suivante : on vérifie qu'ils ont survécu, puis on remet Aube et le texte d'origine.
ambiances_session() {
    local uid
    uid="$(id -u "${TEST_USER}")"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"
}
ambiances_reglage() { ambiances_session kreadconfig6 --file "$1" --group "$2" --key "$3"; }

# Une commande lancée dans la session, avec son code de sortie et ce qu'elle dit (une ligne dans le journal)
ambiances_diag() {
    local sortie code
    sortie="$(ambiances_session "$@" 2>&1)" && code=0 || code=$?
    printf '            diag : %s -> code %s : %s\n' "$*" "${code}" "$(tr '\n' ' ' <<<"${sortie:0:300}")"
}

# Les couleurs du schéma sont-elles vraiment copiées dans kdeglobals (et pas seulement son nom) ?
ambiances_couleurs_du_contraste() {
    [[ "$(ambiances_reglage kdeglobals "Colors:View" BackgroundNormal)" == "0,0,0" &&
        "$(ambiances_reglage kdeglobals "Colors:View" ForegroundNormal)" == "255,255,255" &&
        "$(ambiances_reglage kdeglobals "Colors:Selection" BackgroundNormal)" == "255,221,0" ]]
}

check_ambiances() {
    section "Ambiances (couleurs et Grand texte dans la session)"
    local out outil=/usr/libexec/binixx/binixx-ambiance texte=/usr/libexec/binixx/binixx-taille-texte
    if ! wait_for 120 ambiances_session busctl --user status org.kde.plasmashell; then
        fail "Plasma ne répond pas sur le bus de la session : les ambiances ne peuvent pas être posées"
        return
    fi
    out="$(ambiances_session "${outil}" etat 2>&1)"
    if [[ "${out}" == *"ambiance=aube"* ]]; then
        pass "au départ : Aube (le schéma BinixXClair vient de kdedefaults, rien n'est écrit dans kdeglobals)"
    else
        warn "ambiance de départ : ${out//$'\n'/ ; }"
    fi
    if [[ "${out}" == *"grand-texte=non"* ]]; then pass "au départ « Grand texte » est désactivé"; else fail "binixx-ambiance etat : ${out:0:200}"; fi
    # Ce que disent les outils de Plasma quand on les lance à la main dans cette session (sans écran : l'outil les lance en
    # « offscreen ») ; informatif, pour comprendre un échec sans deviner
    ambiances_diag plasma-apply-colorscheme --list-schemes
    ambiances_diag plasma-apply-colorscheme BinixXSombre
    ambiances_diag env QT_QPA_PLATFORM=offscreen plasma-apply-colorscheme BinixXSombre
    ambiances_diag plasma-apply-lookandfeel --list
    ambiances_diag env QT_QPA_PLATFORM=offscreen plasma-apply-cursortheme --help
    ambiances_diag env QT_QPA_PLATFORM=offscreen plasma-apply-lookandfeel --apply org.binixx.dark.desktop

    local cle schema
    for cle in nuit aube nuit; do
        schema=BinixXSombre
        [[ "${cle}" == aube ]] && schema=BinixXClair
        if out="$(ambiances_session "${outil}" appliquer "${cle}" 2>&1)"; then pass "binixx-ambiance appliquer ${cle} : ${out}"; else fail "appliquer ${cle} : ${out:0:300}"; fi
        if [[ "$(ambiances_reglage kdeglobals General ColorScheme)" == "${schema}" ]]; then
            pass "kdeglobals : ColorScheme=${schema}"
        else
            fail "ColorScheme relu : '$(ambiances_reglage kdeglobals General ColorScheme)' (${schema} attendu)"
        fi
    done
    # Breeze suit les couleurs (icônes sombres sur fond sombre) : le thème d'icônes écrit n'est qu'une information
    echo "            info : thème d'icônes dans kdeglobals après Nuit : '$(ambiances_reglage kdeglobals Icons Theme)'"

    if out="$(ambiances_session "${outil}" appliquer contraste 2>&1)"; then pass "binixx-ambiance appliquer contraste : ${out}"; else fail "appliquer contraste : ${out:0:300}"; fi
    if [[ "$(ambiances_reglage kdeglobals General ColorScheme)" == BinixXContraste ]]; then
        pass "kdeglobals : ColorScheme=BinixXContraste"
    else
        fail "ColorScheme relu : '$(ambiances_reglage kdeglobals General ColorScheme)' (BinixXContraste attendu)"
    fi
    if ambiances_couleurs_du_contraste; then
        pass "les couleurs du schéma sont dans kdeglobals : fond noir, texte blanc, sélection jaune"
    else
        fail "couleurs relues : fond '$(ambiances_reglage kdeglobals "Colors:View" BackgroundNormal)', texte '$(ambiances_reglage kdeglobals "Colors:View" ForegroundNormal)', sélection '$(ambiances_reglage kdeglobals "Colors:Selection" BackgroundNormal)'"
    fi
    if [[ "$(ambiances_reglage kdeglobals WM activeBackground)" == "255,221,0" ]]; then
        pass "la barre de titre de la fenêtre active est jaune"
    else
        warn "barre de titre active : '$(ambiances_reglage kdeglobals WM activeBackground)' (255,221,0 attendu)"
    fi
    # Une application Qt adopte-t-elle la palette ? (le greffon de thème de Plasma lit kdeglobals) : avertissement seulement
    out="$(ambiances_session env QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=kde python3 -c \
        'from PySide6.QtWidgets import QApplication; print(QApplication([]).palette().window().color().name())' 2>&1 | tail -n 1)"
    if [[ "${out}" == "#0c0c0c" ]]; then
        pass "une application Qt prend la palette du contraste élevé"
    else
        warn "une application Qt lit un fond de fenêtre '${out:0:80}' (#0c0c0c attendu) : le greffon de thème de Plasma n'est peut-être pas chargé hors session"
    fi
    out="$(ambiances_session "${outil}" etat 2>&1)"
    if [[ "${out}" == *"ambiance=contraste"* ]]; then pass "binixx-ambiance etat : contraste"; else fail "binixx-ambiance etat : ${out:0:200}"; fi

    # Grand texte : texte à 130 %, pointeur à 36, et il se combine avec l'ambiance en place
    if out="$(ambiances_session "${outil}" grand-texte oui 2>&1)"; then pass "binixx-ambiance grand-texte oui : ${out}"; else fail "grand-texte oui : ${out:0:300}"; fi
    if [[ "$(ambiances_session "${texte}" etat 2>&1)" == 130 ]]; then pass "le texte est à 130 %"; else fail "taille du texte : $(ambiances_session "${texte}" etat 2>&1)"; fi
    if [[ "$(ambiances_reglage kcminputrc Mouse cursorSize)" == 36 ]]; then
        pass "pointeur de souris : taille 36"
    else
        fail "taille du pointeur relue : '$(ambiances_reglage kcminputrc Mouse cursorSize)' (36 attendu)"
    fi
    out="$(ambiances_session "${outil}" etat 2>&1)"
    if [[ "${out}" == *"ambiance=contraste"* && "${out}" == *"grand-texte=oui"* ]]; then
        pass "contraste élevé et grand texte se combinent"
    else
        fail "binixx-ambiance etat : ${out:0:200}"
    fi
}
register_check base check_ambiances

# Après le redémarrage de la mise à jour : les deux sont-ils toujours là ? Puis on remet le bureau comme au départ.
check_ambiances_apres_mise_a_jour() {
    section "Ambiances (après la mise à jour et le redémarrage)"
    local out outil=/usr/libexec/binixx/binixx-ambiance texte=/usr/libexec/binixx/binixx-taille-texte
    if ! wait_for 120 ambiances_session busctl --user status org.kde.plasmashell; then
        fail "Plasma ne répond pas sur le bus de la session après le redémarrage"
        return
    fi
    out="$(ambiances_session "${outil}" etat 2>&1)"
    if [[ "${out}" == *"ambiance=contraste"* ]]; then pass "Contraste élevé a survécu à la mise à jour et au redémarrage"; else fail "binixx-ambiance etat : ${out:0:200}"; fi
    if [[ "${out}" == *"grand-texte=oui"* ]]; then pass "« Grand texte » a survécu à la mise à jour et au redémarrage"; else fail "binixx-ambiance etat : ${out:0:200}"; fi
    if ambiances_couleurs_du_contraste; then pass "les couleurs du contraste élevé sont toujours dans kdeglobals"; else fail "couleurs du contraste élevé perdues après le redémarrage"; fi
    if [[ "$(ambiances_reglage kcminputrc Mouse cursorSize)" == 36 ]]; then pass "le pointeur est toujours à 36"; else fail "pointeur après redémarrage : '$(ambiances_reglage kcminputrc Mouse cursorSize)'"; fi

    if out="$(ambiances_session "${outil}" grand-texte non 2>&1)"; then pass "binixx-ambiance grand-texte non : ${out}"; else fail "grand-texte non : ${out:0:300}"; fi
    if [[ "$(ambiances_session "${texte}" etat 2>&1)" == 100 ]]; then pass "le texte est revenu à 100 %"; else fail "taille du texte : $(ambiances_session "${texte}" etat 2>&1)"; fi
    if [[ "$(ambiances_reglage kcminputrc Mouse cursorSize || true)" =~ ^(|24)$ ]]; then
        pass "le pointeur est revenu à sa taille d'origine"
    else
        fail "pointeur après « grand-texte non » : '$(ambiances_reglage kcminputrc Mouse cursorSize)'"
    fi
    if out="$(ambiances_session "${outil}" appliquer aube 2>&1)"; then pass "binixx-ambiance appliquer aube : ${out}"; else fail "appliquer aube : ${out:0:300}"; fi
    if [[ "$(ambiances_reglage kdeglobals General ColorScheme)" == BinixXClair ]]; then pass "le bureau est revenu à Aube"; else fail "ColorScheme : '$(ambiances_reglage kdeglobals General ColorScheme)'"; fi
}
register_check after-update check_ambiances_apres_mise_a_jour
