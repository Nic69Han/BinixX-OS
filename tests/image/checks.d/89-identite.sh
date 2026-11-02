# shellcheck shell=bash
section "Identité BinixX (bleu pastel, logo, pointeur, police Inter ; docs/identite-visuelle.md)"
# Le bleu BinixX : pastel #ADCFFB et sa nuance forte #0C6EEE ; plus de bleu vif #2F5BFF
check "logo et icône système au bleu BinixX (dégradé pastel → fort)" bash -c \
    "grep -qi '#ADCFFB' /usr/share/icons/hicolor/scalable/apps/binixx.svg && grep -qi '#0C6EEE' /usr/share/icons/hicolor/scalable/apps/binixx.svg && ! grep -qi '#2F5BFF' /usr/share/icons/hicolor/scalable/apps/binixx.svg"
check "écran de démarrage : barre de progression au bleu BinixX pastel" \
    grep -qx 'ProgressBarForegroundColor=0xadcffb' /usr/share/plymouth/themes/binixx/binixx.plymouth
check "Centre BinixX : nuance forte et pastel du bleu BinixX" python3 -c '
import sys
sys.path.insert(0, "/usr/lib/binixx/centre")
from binixx_centre import theme
assert (theme.BLUE, theme.SKY) == ("#0C6EEE", "#ADCFFB"), (theme.BLUE, theme.SKY)
assert "2F5BFF" not in theme.feuille(False).upper() and "47,91,255" not in theme.feuille(True)
'
# Police Inter installée et posée pour l'interface ; « Taille du texte » part d'elle
check "police Inter installée" bash -c "fc-list : family | grep -qx 'Inter'"
police_par_defaut() ( # police_par_defaut groupe clé : la valeur lue comme une application, dossier personnel vide
    home="$(mktemp -d)"
    trap 'rm -rf "${home}"' EXIT
    HOME="${home}" XDG_CONFIG_HOME="${home}/.config" kreadconfig6 --file kdeglobals --group "$1" --key "$2"
)
for cle in General/font General/menuFont General/toolBarFont General/smallestReadableFont WM/activeFont; do
    valeur="$(police_par_defaut "${cle%/*}" "${cle#*/}")"
    if [[ "${valeur}" == Inter,* ]]; then pass "kdeglobals ${cle} : ${valeur%%,-1*}"; else fail "kdeglobals ${cle} : '${valeur}' (Inter attendu)"; fi
done
check "« Taille du texte » part de la police Inter" python3 -c '
import sys
sys.path.insert(0, "/usr/lib/binixx/centre")
from binixx_centre import taille_texte
assert taille_texte.DEFAUTS[("General", "font")].startswith("Inter,10,")
'
