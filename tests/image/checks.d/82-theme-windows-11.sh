# shellcheck shell=bash
section "Style Windows 11 (Win11OS KDE, GPL-3.0) : fenêtres, Plasma, Kvantum"
LICENCES=/usr/share/licenses/binixx-win11os-kde
LNF=/usr/share/plasma/look-and-feel
check "kvantum installé" rpm -q kvantum
check "le style Kvantum de Qt 6 est présent" test -s /usr/lib64/qt6/plugins/styles/libkvantum.so

for variante in light dark; do
    nom="Win11OS-${variante}"
    check "${nom} : décoration des fenêtres (Aurorae) complète" bash -c \
        "cd /usr/share/aurorae/themes/${nom} && test -s metadata.desktop && test -s ${nom}rc && test -s decoration.svg && test -s close.svg && test -s maximize.svg && test -s minimize.svg"
    check "${nom} : thème Kvantum complet (réglages et dessin)" bash -c \
        "test -s /usr/share/Kvantum/${nom}/${nom}.kvconfig && test -s /usr/share/Kvantum/${nom}/${nom}.svg"
    check "${nom} : thème Plasma complet (barre des tâches, fenêtres, bulles)" bash -c \
        "cd /usr/share/plasma/desktoptheme/${nom} && test -s metadata.desktop && test -s widgets/panel-background.svg && test -s widgets/tasks.svgz && test -s dialogs/background.svgz && test -s translucent/widgets/panel-background.svg"
done

# Licence : ces fichiers sont du projet Win11OS KDE, sous GNU GPL v3, copiés sans modification ; le texte de la licence, les auteurs et
# la source (adresse et version exacte) accompagnent l'image.
check "licence GPL v3, auteurs et source du thème fournis avec l'image" bash -c \
    "head -n 3 ${LICENCES}/COPYING | grep -q 'GNU GENERAL PUBLIC LICENSE' && grep -q 'Version 3' ${LICENCES}/COPYING && test -s ${LICENCES}/AUTHORS && grep -q 'github.com/yeyushengfan258/Win11OS-kde' ${LICENCES}/SOURCE.txt && grep -Eq 'commit [0-9a-f]{40}' ${LICENCES}/SOURCE.txt"
# Rien d'autre du projet : ses fonds d'écran (dessins proches du fond de Windows 11) et son écran de connexion ne sont pas dans l'image
check "les fonds d'écran et l'écran de connexion du projet ne sont pas dans l'image" bash -c \
    '! ls -d /usr/share/wallpapers/Win11OS* /usr/share/sddm/themes/Win11OS* /usr/share/plasma/look-and-feel/com.github.yeyushengfan258.* /usr/share/color-schemes/Win11OS* 2>/dev/null | grep -q .'

# Les thèmes globaux de BinixX OS posent ces thèmes, avec des noms qui existent vraiment
style_theme_global() ( # style_theme_global thème variante couleurs icônes
    set -e
    f="${LNF}/$1/contents/defaults"
    nom="Win11OS-$2"
    grep -qx 'widgetStyle=kvantum' "${f}"
    grep -qx "ColorScheme=$3" "${f}"
    grep -qx "name=${nom}" "${f}"
    grep -qx "theme=__aurorae__svg__${nom}" "${f}"
    grep -qx 'library=org.kde.kwin.aurorae' "${f}"
    grep -qx 'ButtonsOnRight=IAX' "${f}"
    grep -qx "Theme=$4" "${f}"
    test -d "/usr/share/aurorae/themes/${nom}" -a -d "/usr/share/plasma/desktoptheme/${nom}" -a -d "/usr/share/Kvantum/${nom}"
    test -s "/usr/share/color-schemes/$3.colors"
    test -s "/usr/share/icons/$4/index.theme"
)
check "Aube : Kvantum, fenêtres et thème Plasma Win11OS-light, couleurs BinixXClair" style_theme_global org.binixx.desktop light BinixXClair binixx-os
check "Nuit : Kvantum, fenêtres et thème Plasma Win11OS-dark, couleurs BinixXSombre" style_theme_global org.binixx.dark.desktop dark BinixXSombre binixx-os-dark
check "Contraste élevé : style Breeze, décoration Breeze, thème Plasma d'origine (pas de style Windows 11)" bash -c \
    "f=${LNF}/org.binixx.contraste.desktop/contents/defaults; grep -qx 'widgetStyle=Breeze' \${f} && grep -qx 'ColorScheme=BinixXContraste' \${f} && grep -qx 'library=org.kde.breeze' \${f} && grep -qx 'name=default' \${f} && ! grep -v '^#' \${f} | grep -qi 'kvantum\|aurorae\|Win11OS'"
# Dossiers jaunes : les icônes de BinixX OS sont celles de Breeze, avec le corps des dossiers en jaune au lieu de la couleur d'accent (bleue).
# Générées à la construction depuis Breeze (build_files/icones-dossiers-jaunes.py).
check "icônes BinixX OS (clair) : hérite de Breeze, dossiers de 32 à 96 pixels en jaune, couleurs du bureau figées (plus d'identifiant « current-color-scheme »)" bash -c \
    "grep -qx 'Inherits=breeze' /usr/share/icons/binixx-os/index.theme && for t in 32 48 64 96; do grep -q 'fill:#f2cb40' /usr/share/icons/binixx-os/places/\${t}/folder.svg && grep -q 'id=\"couleurs-fixes-binixx\"' /usr/share/icons/binixx-os/places/\${t}/folder.svg && ! grep -q 'id=\"current-color-scheme\"' /usr/share/icons/binixx-os/places/\${t}/folder.svg || exit 1; done"
check "icônes BinixX OS : petits dossiers (16, 22 et 24 pixels) en jaune aussi, ouverts comme fermés" bash -c \
    "for t in 16 22 24; do for f in folder folder-open; do grep -q 'fill:#fdbc4b' /usr/share/icons/binixx-os/places/\${t}/\${f}.svg || exit 1; done; done"
check "icônes BinixX OS : les dossiers des répertoires usuels (Documents, Téléchargements, Musique, Images, Vidéos) sont jaunes aussi" bash -c \
    "for f in folder-documents folder-download folder-music folder-pictures folder-videos; do grep -q 'fill:#f2cb40' /usr/share/icons/binixx-os/places/64/\${f}.svg || exit 1; done"
check "icônes BinixX OS : le type « dossier » (inode-directory) mène au dossier jaune" bash -c \
    "test \"\$(readlink -f /usr/share/icons/binixx-os/mimetypes/64/inode-directory.svg)\" = /usr/share/icons/binixx-os/places/64/folder.svg"
check "icônes BinixX OS sombres : Breeze sombre pour le reste, mêmes dossiers jaunes (liens vers le thème clair)" bash -c \
    "grep -qx 'Inherits=breeze-dark' /usr/share/icons/binixx-os-dark/index.theme && test \"\$(readlink -f /usr/share/icons/binixx-os-dark/places/64/folder.svg)\" = /usr/share/icons/binixx-os/places/64/folder.svg"
check "icônes BinixX OS : licence de Breeze et note sur la modification fournies" bash -c \
    "test -s /usr/share/icons/binixx-os/LISEZMOI.txt && ls /usr/share/icons/binixx-os | grep -qi 'COPYING\|LICENSE'"
check "Contraste élevé garde les icônes de Breeze sombre (pas de dossiers jaunes : le contraste se vérifie sur les couleurs)" bash -c \
    "grep -qx 'Theme=breeze-dark' ${LNF}/org.binixx.contraste.desktop/contents/defaults"
check "contraste élevé : thème global complet (métadonnées, disposition du panneau, aperçus hérités de Brise sombre)" bash -c \
    "grep -q '\"Id\": \"org.binixx.contraste.desktop\"' ${LNF}/org.binixx.contraste.desktop/metadata.json && cmp ${LNF}/org.binixx.desktop/contents/layouts/org.kde.plasma.desktop-layout.js ${LNF}/org.binixx.contraste.desktop/contents/layouts/org.kde.plasma.desktop-layout.js && test -f ${LNF}/org.binixx.contraste.desktop/contents/previews/preview.png && test -f ${LNF}/org.binixx.contraste.desktop/contents/previews/fullscreenpreview.jpg"

# Kvantum ne lit le thème que dans le dossier de l'utilisateur : un compte neuf reçoit le thème clair (celui d'Aube) de /etc/skel
style_skel() (
    f=/etc/skel/.config/Kvantum/kvantum.kvconfig
    test -s "${f}" && [[ "$(kreadconfig6 --file "${f}" --group General --key theme)" == Win11OS-light ]]
)
check "un compte neuf reçoit le thème Kvantum Win11OS-light (/etc/skel/.config/Kvantum)" style_skel

# Le thème Kvantum suit les couleurs : service et surveillance de ~/.config/kdeglobals dans chaque session, et la commande qui les relie
check "service utilisateur binixx-kvantum : une commande, pas de limite de démarrages" bash -c \
    "grep -qx 'ExecStart=/usr/libexec/binixx/binixx-ambiance kvantum' /usr/lib/systemd/user/binixx-kvantum.service && grep -qx 'StartLimitIntervalSec=0' /usr/lib/systemd/user/binixx-kvantum.service"
check "surveillance de kdeglobals (binixx-kvantum.path) qui lance ce service" bash -c \
    "grep -qx 'PathChanged=%h/.config/kdeglobals' /usr/lib/systemd/user/binixx-kvantum.path && grep -qx 'Unit=binixx-kvantum.service' /usr/lib/systemd/user/binixx-kvantum.path"
check "service et surveillance activés pour tous les utilisateurs" bash -c \
    "test -L /etc/systemd/user/default.target.wants/binixx-kvantum.service && test -L /etc/systemd/user/default.target.wants/binixx-kvantum.path"

style_synchronisation() (
    set -e
    home="$(mktemp -d)"
    trap 'rm -rf "${home}"' EXIT
    export HOME="${home}" XDG_CONFIG_HOME="${home}/.config"
    mkdir -p "${home}/.config"
    outil=/usr/libexec/binixx/binixx-ambiance
    # sous les couleurs sombres, le thème sombre ; puis le thème clair sous les couleurs claires ; un autre thème choisi n'est pas remplacé
    printf '[General]\nColorScheme=BinixXSombre\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == Win11OS-dark ]]
    printf '[General]\nColorScheme=BinixXClair\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == Win11OS-light ]]
    printf '[General]\ntheme=KvArc\n' >"${home}/.config/Kvantum/kvantum.kvconfig"
    printf '[General]\nColorScheme=BinixXSombre\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == KvArc ]]
)
check "binixx-ambiance kvantum : le thème suit les couleurs sans remplacer un autre thème choisi" style_synchronisation
