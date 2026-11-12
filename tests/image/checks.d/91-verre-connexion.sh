# shellcheck shell=bash
section "Écrans de verrouillage et de connexion en verre"
LOCK=/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml
check "écran de verrouillage : panneau de verre fumé" grep -q 'id: binixxVerre' "${LOCK}"
check "écran de verrouillage : heure en blanc" grep -q 'Kirigami.Theme.textColor: "#FFFFFF"' "${LOCK}"
check "écran de verrouillage : une seule modification" bash -c "[[ \$(grep -c 'id: binixxVerre' '${LOCK}') -eq 1 ]]"
TMPF=/usr/lib/tmpfiles.d/binixx-plasmalogin.conf
check "écran de connexion : thème Nuit posé à chaque démarrage" grep -q 'LookAndFeelPackage=org.binixx.dark.desktop' "${TMPF}"
check "écran de connexion : pas de bascule automatique jour / nuit" grep -q 'AutomaticLookAndFeel=false' "${TMPF}"
check "écran de connexion : thème global Nuit présent" test -f /usr/share/plasma/look-and-feel/org.binixx.dark.desktop/metadata.json
