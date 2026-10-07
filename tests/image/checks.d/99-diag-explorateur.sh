# shellcheck shell=bash
# TEMPORAIRE (à retirer avant de sortir la PR du brouillon) : ouvre Dolphin dans un écran virtuel, avant et après l'Explorateur BinixX, et
# imprime les captures en base64 dans le journal de la CI pour les relire.
section "DIAG Explorateur : captures de Dolphin (temporaire)"
diag_installer() {
    dnf5 -y install xorg-x11-server-Xvfb ImageMagick >/tmp/diag-dnf.log 2>&1 || {
        tail -n 15 /tmp/diag-dnf.log
        return 1
    }
}
diag_capture() { # diag_capture <nom> <utilisateur>
    local nom="$1" user="$2" home xdg
    home="$(getent passwd "${user}" | cut -d: -f6)"
    xdg="/tmp/xdg-${user}"
    mkdir -p "${xdg}" && chown "${user}" "${xdg}" && chmod 700 "${xdg}"
    runuser -u "${user}" -- bash -c "mkdir -p '${home}/Documents' '${home}/Downloads' '${home}/Pictures'; touch '${home}/Documents/Facture.docx' '${home}/Documents/Budget.xlsx' '${home}/Notes.txt'"
    runuser -u "${user}" -- kwriteconfig6 --file kdeglobals --group General --key ColorScheme BinixXClair
    runuser -u "${user}" -- kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle Breeze
    runuser -u "${user}" -- env DISPLAY=:99 XDG_RUNTIME_DIR="${xdg}" QT_QPA_PLATFORM=xcb QT_QPA_PLATFORMTHEME=kde \
        XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true dbus-run-session -- timeout 40 dolphin --new-window "${home}" >"/tmp/diag-dolphin-${nom}.log" 2>&1 &
    sleep 25
    import -display :99 -window root "/tmp/diag-${nom}.png" 2>>"/tmp/diag-dolphin-${nom}.log" || echo "import a échoué"
    pkill -u "${user}" dolphin || true
    sleep 3
    echo "---- rc de ${user} après le lancement (menus + barres) ----"
    if [[ -f "${home}/${RC}" ]]; then
        grep -nE '<gui |ToolBar|Menu name="(file|edit|view)"' "${home}/${RC}" | head -20
    else
        echo "(pas de fichier local)"
    fi
    echo "---- sortie de Dolphin (${nom}) ----"
    tail -n 25 "/tmp/diag-dolphin-${nom}.log"
    echo "BEGIN-PNG ${nom}"
    base64 -w 3000 "/tmp/diag-${nom}.png"
    echo "END-PNG ${nom}"
}
if diag_installer; then
    mkdir -p /tmp/skel-vide
    useradd -m -k /tmp/skel-vide diagavant
    useradd -m diagapres
    useradd -m diaginverse
    # Barres d'outils dans l'ordre inverse du nôtre : ce que donnerait une seconde fusion après une mise à jour de Dolphin
    python3 - "$(getent passwd diaginverse | cut -d: -f6)/${RC}" <<'PYEOF'
import sys, xml.dom.minidom
doc = xml.dom.minidom.parse(sys.argv[1])
racine = doc.documentElement
barres = racine.getElementsByTagName("ToolBar")
premiere, seconde = barres[0], barres[1]
racine.removeChild(seconde)
racine.insertBefore(seconde, premiere)
open(sys.argv[1], "w", encoding="utf-8").write(doc.toxml())
print("ordre des barres après inversion :", [b.getAttribute("name") for b in racine.getElementsByTagName("ToolBar")])
PYEOF
    chown -R diaginverse:diaginverse "$(getent passwd diaginverse | cut -d: -f6)"
    (Xvfb :99 -screen 0 1366x768x24 -nolisten tcp >/tmp/diag-xvfb.log 2>&1 &)
    sleep 3
    diag_capture avant diagavant
    diag_capture apres diagapres
    diag_capture apres2 diagapres
    diag_capture inverse diaginverse
    pkill Xvfb || true
fi
