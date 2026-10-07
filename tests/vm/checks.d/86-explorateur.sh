# shellcheck shell=bash
# Explorateur BinixX : Dolphin préréglé comme l'Explorateur de Windows 11.
#  - phase base : le compte de l'installation a reçu les barres d'outils et la vue « détails » de /etc/skel (c'est ce que fait
#    l'installeur à la création du compte), et les réglages communs de /etc/xdg/dolphinrc sont lus dans la session ;
#  - phase explorateur (lancée par run-vm-test.sh, qui photographie ensuite l'écran : explorateur.png) : Dolphin s'ouvre dans la vraie
#    session, et on vérifie que KDE a bien repris nos barres d'outils dans son fichier (il réécrit alors le fichier du compte avec la
#    version de Dolphin pour les menus). La fenêtre reste ouverte pour la capture.
explorateur_session() {
    local uid
    uid="$(id -u "${TEST_USER}")"
    runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"
}

check_explorateur_compte() {
    section "Explorateur BinixX (compte de l'installation)"
    local rc=.local/share/kxmlgui5/dolphin/dolphinui.rc vues=.local/share/dolphin/view_properties/global/.directory out
    check "barres d'outils de Dolphin dans le dossier personnel (copiées de /etc/skel à la création du compte)" \
        cmp "/etc/skel/${rc}" "${TEST_HOME}/${rc}"
    check "vue « détails » par défaut dans le dossier personnel" cmp "/etc/skel/${vues}" "${TEST_HOME}/${vues}"
    if [[ "$(explorateur_session kreadconfig6 --file dolphinrc --group General --key ShowStatusBar)" == 1 ]]; then
        pass "dolphinrc (/etc/xdg) lu dans la session : barre d'état sur toute la largeur"
    else
        fail "dolphinrc : ShowStatusBar='$(explorateur_session kreadconfig6 --file dolphinrc --group General --key ShowStatusBar)' (1 attendu)"
    fi
    out="$(explorateur_session /usr/libexec/binixx/binixx-explorateur etat 2>&1)"
    if [[ "${out}" == explorateur=oui ]]; then pass "binixx-explorateur etat : ${out}"; else fail "binixx-explorateur etat : ${out:0:200}"; fi
    echo "            info : $(dolphin --version 2>&1 | head -n 1)"
}
register_check base check_explorateur_compte

explorateur_fenetre_ouverte() { explorateur_session busctl --user list --no-legend | grep -q 'org\.kde\.dolphin'; }

check_explorateur_session() {
    section "Explorateur BinixX (Dolphin ouvert dans la session)"
    local uid socket rc="${TEST_HOME}/.local/share/kxmlgui5/dolphin/dolphinui.rc"
    uid="$(id -u "${TEST_USER}")"
    if ! wait_for 120 explorateur_session busctl --user status org.kde.plasmashell; then
        fail "Plasma ne répond pas sur le bus de la session : Dolphin ne peut pas s'ouvrir"
        return
    fi
    socket="$(find "/run/user/${uid}" -maxdepth 1 -name 'wayland-[0-9]*' ! -name '*.lock' -printf '%f\n' | sort | head -n 1)"
    if [[ -z "${socket}" ]]; then
        fail "aucune socket Wayland dans /run/user/${uid} : la session graphique n'est pas ouverte"
        return
    fi
    # Une copie du fichier d'origine, pour voir ce que KDE en fait
    cp -- "${rc}" /tmp/dolphinui-avant.rc
    echo "            info : environnement de la session : $(explorateur_session systemctl --user show-environment 2>&1 | grep -E '^(WAYLAND_DISPLAY|XDG_CURRENT_DESKTOP|KDE_FULL_SESSION|XDG_SESSION_TYPE)=' | tr '\n' ' ')"
    # Lancé par le gestionnaire de la session de l'utilisateur, comme une application du menu (environnement de Plasma : thème, portails…),
    # et non depuis la connexion SSH, dont l'environnement n'a ni thème KDE ni bureau ; il survit aussi à la fin de cette connexion.
    explorateur_session systemd-run --user --collect --quiet --unit=binixx-test-dolphin \
        -E WAYLAND_DISPLAY="${socket}" -E QT_QPA_PLATFORM=wayland -E XDG_CURRENT_DESKTOP=KDE -E KDE_FULL_SESSION=true \
        dolphin --new-window "${TEST_HOME}" >/tmp/dolphin-session.log 2>&1
    if wait_for 90 explorateur_fenetre_ouverte; then pass "Dolphin est ouvert dans la session (${socket})"; else
        fail "Dolphin ne s'ouvre pas : $(tail -n 5 /tmp/dolphin-session.log | tr '\n' ' ' | cut -c1-300) ; $(explorateur_session systemctl --user status binixx-test-dolphin --no-pager 2>&1 | tail -n 6 | tr '\n' ' ' | cut -c1-400)"
        return
    fi
    # La capture doit montrer le bureau normal : ambiance Aube, texte à 100 % (le contrôle des ambiances les remet après la mise à jour)
    out="$(explorateur_session /usr/libexec/binixx/binixx-ambiance etat 2>&1)"
    echo "            info : bureau au moment de la capture : ${out//$'\n'/ ; }"
    if [[ "${out}" != *"ambiance=aube"* || "${out}" != *"grand-texte=non"* ]]; then
        warn "la capture n'est pas en ambiance Aube avec le texte à 100 % : ${out//$'\n'/ ; }"
    fi
    sleep 8 # le temps d'afficher la fenêtre avant la capture d'écran
    # KDE reprend les barres du compte dans le fichier de Dolphin et réécrit le fichier du compte : version de Dolphin, menus et barres
    python3 - "${rc}" <<'PYEOF'
import sys, xml.dom.minidom
try:
    doc = xml.dom.minidom.parse(sys.argv[1]).documentElement
except Exception as erreur:  # noqa: BLE001
    print("            ÉCHEC : le fichier du compte n'est plus du XML valide :", erreur)
    sys.exit(1)
version = doc.getAttribute("version")
barres = [b.getAttribute("name") for b in doc.getElementsByTagName("ToolBar")]
menus = [m.getAttribute("name") for m in doc.getElementsByTagName("Menu")]
print("            info : dolphinui.rc après le lancement : version %s, barres %s, menus %s" % (version, barres, menus))
assert version.isdigit() and int(version) > 1, "la version devrait être celle de Dolphin, pas notre 1 (KDE n'a pas fusionné le fichier)"
assert "mainToolBar" in barres and "commandToolBar" in barres, barres
assert "file" in menus and "view" in menus, "les menus de Dolphin devraient avoir été repris du fichier d'origine : %s" % menus
PYEOF
    local code=$?
    if [[ ${code} -eq 0 ]]; then
        pass "KDE a repris nos deux barres d'outils dans le fichier de Dolphin (menus et version de Dolphin conservés)"
    else
        fail "le fichier dolphinui.rc du compte n'a pas été fusionné comme prévu (voir la ligne ci-dessus)"
    fi
    echo "            info : journal de Dolphin : $(tail -n 5 /tmp/dolphin-session.log | tr '\n' ' ' | cut -c1-400)"
}
register_check explorateur check_explorateur_session
