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

# Variantes (build_files/variantes-themes.py), posées par défaut. Les thèmes d'origine restent installés, inchangés.
# Plasma lit les fonds (menu de démarrage, barre des tâches, bulles) dans « translucent » quand le flou de KWin est actif, dans « dialogs » et
# « widgets » sinon (machine virtuelle, vieux PC : translucides dans l'original, ils avaient laissé voir les fenêtres du dessous à travers le
# menu dans le test VM), et dans « solid » quand un élément demande un fond plein. Sans flou, les variantes doivent donc mener aux fonds de
# « solid », sans qu'un « .svgz » d'origine cache un « .svg » opaque (Plasma cherche « .svgz » d'abord) ; avec le flou, au verre d'origine
# (Aube, Nuit) ou encore à « solid » (contraste élevé).

# fond_reel <dossier d'un thème> <fond> : chemin réel (liens suivis) du seul fichier « fond.svg » ou « fond.svgz » ; échoue s'il n'y en a pas
# ou s'il y en a deux
fond_reel() {
    local f existants=()
    for f in "$1/$2.svg" "$1/$2.svgz"; do
        if [[ -e "${f}" ]]; then existants+=("${f}"); fi
    done
    [[ ${#existants[@]} -eq 1 ]] && readlink -f "${existants[0]}"
}

plasma_fonds() ( # plasma_fonds <thème d'origine> <variante> <dossier lu avec le flou : translucent ou solid>
    set -e
    racine=/usr/share/plasma/desktoptheme
    amont="${racine}/$1"
    aval="${racine}/$2"
    test "$(readlink -f "${aval}/solid")" = "${amont}/solid"
    test "$(readlink -f "${aval}/translucent")" = "${amont}/$3"
    for fond in dialogs/background widgets/background widgets/panel-background widgets/tooltip; do
        reel="$(fond_reel "${aval}" "${fond}")"
        [[ "${reel}" == "${amont}/solid/${fond}".svg* ]]
        fond_reel "${aval}/translucent" "${fond}" >/dev/null
    done
    # le reste du thème est celui d'origine
    test "$(readlink -f "${aval}/widgets/tasks.svgz")" = "${amont}/widgets/tasks.svgz"
)

for variante in light dark; do
    amont="Win11OS-${variante}"
    aval="BinixX-Win11-${variante}"
    check "${aval} : thème Kvantum sans transparence ni flou (huit réglages à false), même dessin que ${amont}" bash -c \
        "k=/usr/share/Kvantum/${aval}/${aval}.kvconfig; for c in translucent_windows blurring popup_blurring transparent_dolphin_view transparent_pcmanfm_sidepane transparent_pcmanfm_view transparent_menutitle blur_translucent; do grep -qx \"\${c}=false\" \${k} || exit 1; done; cmp /usr/share/Kvantum/${aval}/${aval}.svg /usr/share/Kvantum/${amont}/${amont}.svg"
    check "${amont} : le thème Kvantum d'origine est resté translucide (inchangé)" bash -c \
        "grep -qx 'translucent_windows=true' /usr/share/Kvantum/${amont}/${amont}.kvconfig"
    check "${aval} : thème Plasma sans la section Wallpaper du thème d'origine, nommé ${aval}" bash -c \
        "d=/usr/share/plasma/desktoptheme/${aval}; grep -qx 'Name=${aval}' \${d}/metadata.desktop && grep -qx 'X-KDE-PluginInfo-Name=${aval}' \${d}/metadata.desktop && ! grep -q 'Wallpaper' \${d}/metadata.desktop"
    check "${aval} : thème Plasma en verre adaptatif (verre dépoli de ${amont} avec le flou, fonds opaques de solid sans)" plasma_fonds "${amont}" "${aval}" translucent
done

check "BinixX-contraste : thème Plasma du contraste élevé, Breeze opaque avec ou sans flou" plasma_fonds default BinixX-contraste solid
check "BinixX-contraste : nommé BinixX-contraste, sans la section Wallpaper de Breeze" bash -c \
    "d=/usr/share/plasma/desktoptheme/BinixX-contraste; python3 -c 'import json, sys; m = json.load(open(sys.argv[1]))[\"KPlugin\"]; sys.exit(m[\"Id\"] != \"BinixX-contraste\")' \${d}/metadata.json && ! grep -q Wallpaper \${d}/plasmarc"

# Barre de titre épurée : l'icône de l'application à gauche (pas « sur tous les bureaux »), réduire, agrandir et fermer à droite (pas « aide »)
check "barre de titre : icône de l'application à gauche, réduire, agrandir et fermer à droite (/etc/xdg/kwinrc)" bash -c \
    "test \"\$(kreadconfig6 --file /etc/xdg/kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft)\" = M && test \"\$(kreadconfig6 --file /etc/xdg/kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight)\" = IAX"

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
    opaque="BinixX-Win11-$2"
    grep -qx 'widgetStyle=kvantum' "${f}"
    grep -qx "ColorScheme=$3" "${f}"
    grep -qx "name=${opaque}" "${f}"
    grep -qx "theme=__aurorae__svg__${nom}" "${f}"
    grep -qx 'library=org.kde.kwin.aurorae' "${f}"
    grep -qx 'ButtonsOnRight=IAX' "${f}"
    grep -qx "Theme=$4" "${f}"
    test -d "/usr/share/aurorae/themes/${nom}" -a -d "/usr/share/plasma/desktoptheme/${opaque}" -a -d "/usr/share/Kvantum/${opaque}"
    test -s "/usr/share/color-schemes/$3.colors"
    test -s "/usr/share/icons/$4/index.theme"
)
check "Aube : Kvantum et thème Plasma BinixX-Win11-light (opaques), fenêtres Win11OS-light, couleurs BinixXClair" style_theme_global org.binixx.desktop light BinixXClair binixx-os
check "Nuit : Kvantum et thème Plasma BinixX-Win11-dark (opaques), fenêtres Win11OS-dark, couleurs BinixXSombre" style_theme_global org.binixx.dark.desktop dark BinixXSombre binixx-os-dark
check "Contraste élevé : style Breeze, décoration Breeze, thème Plasma Breeze opaque (pas de style Windows 11)" bash -c \
    "f=${LNF}/org.binixx.contraste.desktop/contents/defaults; grep -qx 'widgetStyle=Breeze' \${f} && grep -qx 'ColorScheme=BinixXContraste' \${f} && grep -qx 'library=org.kde.breeze' \${f} && grep -qx 'name=BinixX-contraste' \${f} && ! grep -v '^#' \${f} | grep -qi 'kvantum\|aurorae\|Win11'"
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
    test -s "${f}" && [[ "$(kreadconfig6 --file "${f}" --group General --key theme)" == BinixX-Win11-light ]]
)
check "un compte neuf reçoit le thème Kvantum BinixX-Win11-light (/etc/skel/.config/Kvantum)" style_skel

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
    # sous les couleurs sombres, le thème sombre ; puis le thème clair sous les couleurs claires ; un thème translucide de Win11OS KDE choisi à la main
    # est suivi dans sa famille ; un autre thème choisi n'est pas remplacé
    printf '[General]\nColorScheme=BinixXSombre\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == BinixX-Win11-dark ]]
    printf '[General]\nColorScheme=BinixXClair\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == BinixX-Win11-light ]]
    printf '[General]\ntheme=Win11OS-light\n' >"${home}/.config/Kvantum/kvantum.kvconfig"
    printf '[General]\nColorScheme=BinixXSombre\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == Win11OS-dark ]]
    printf '[General]\ntheme=KvArc\n' >"${home}/.config/Kvantum/kvantum.kvconfig"
    printf '[General]\nColorScheme=BinixXSombre\n' >"${home}/.config/kdeglobals"
    "${outil}" kvantum >/dev/null
    [[ "$(kreadconfig6 --file "${home}/.config/Kvantum/kvantum.kvconfig" --group General --key theme)" == KvArc ]]
)
check "binixx-ambiance kvantum : le thème suit les couleurs en gardant la famille d'un thème Win11OS translucide choisi à la main, sans remplacer un autre thème" style_synchronisation
