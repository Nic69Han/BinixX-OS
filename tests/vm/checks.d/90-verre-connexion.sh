# shellcheck shell=bash
# Écrans de verrouillage et de connexion (docs/verre-connexion.md) : sur le système installé, l'écran de connexion lit le thème Nuit
# dans le kdeglobals de son compte, et l'écran de verrouillage a son panneau de verre. Les captures (verrouillage.png,
# verrouillage-mot-de-passe.png, connexion.png) sont prises par run-vm-test.sh.
check_verre_connexion() {
    section "Écrans de verrouillage et de connexion en verre"
    local maison fichier
    maison="$(getent passwd plasmalogin | cut -d: -f6)"
    fichier="${maison}/.config/kdeglobals"
    if [[ -n "${maison}" ]] && grep -q '^LookAndFeelPackage=org.binixx.dark.desktop$' "${fichier}" 2>/dev/null; then
        pass "écran de connexion en Nuit (${fichier})"
    else
        fail "écran de connexion : thème Nuit absent de '${fichier}' : $(head -c 300 "${fichier}" 2>&1 | tr '\n' ' ')"
    fi
    check "kdeglobals de l'écran de connexion à son compte" bash -c "[[ \$(stat -c %U '${fichier}') == plasmalogin ]]"
    check "écran de verrouillage : panneau de verre fumé" \
        grep -q 'id: binixxVerre' /usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml
}
register_check base check_verre_connexion
