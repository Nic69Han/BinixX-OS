# shellcheck shell=bash
section "Souris comme sous Windows (double-clic pour ouvrir, pointeur blanc)"
LNF_CLAIR=/usr/share/plasma/look-and-feel/org.binixx.desktop/contents/defaults
LNF_SOMBRE=/usr/share/plasma/look-and-feel/org.binixx.dark.desktop/contents/defaults

# Valeurs lues comme le fait une application : /etc/xdg (et le profil kde-settings de Fedora) derrière un dossier personnel vide
pointeur_valeur_par_defaut() ( # pointeur_valeur_par_defaut fichier groupe clé
    home="$(mktemp -d)"
    trap 'rm -rf "${home}"' EXIT
    HOME="${home}" XDG_CONFIG_HOME="${home}/.config" kreadconfig6 --file "$1" --group "$2" --key "$3"
)
valeur="$(pointeur_valeur_par_defaut kdeglobals KDE SingleClick)"
if [[ "${valeur}" == false ]]; then pass "kdeglobals : SingleClick=false (un clic sélectionne, un double-clic ouvre)"; else fail "SingleClick='${valeur}' (false attendu)"; fi
valeur="$(pointeur_valeur_par_defaut kcminputrc Mouse cursorTheme)"
if [[ "${valeur}" == Breeze_Light ]]; then pass "kcminputrc : pointeur ${valeur} par défaut"; else fail "cursorTheme='${valeur}' (Breeze_Light attendu)"; fi
check "thème global BinixX OS clair : pointeur Breeze_Light" grep -qx 'cursorTheme=Breeze_Light' "${LNF_CLAIR}"
check "thème global BinixX OS sombre : pointeur Breeze_Light" grep -qx 'cursorTheme=Breeze_Light' "${LNF_SOMBRE}"
check "le pointeur de repli de « Grand texte » est Breeze_Light" python3 -c '
import sys
sys.path.insert(0, "/usr/lib/binixx/centre")
from binixx_centre import ambiances
assert ambiances.THEME_CURSEUR == "Breeze_Light", ambiances.THEME_CURSEUR
'

# La flèche est vraiment blanche (comme celle de Windows) et non noire : on lit l'image du curseur (format Xcursor, 32 pixels environ) et
# on compte ses pixels opaques clairs et sombres (le contour sombre de Breeze Light est semi-transparent : il n'y compte pas). Mesuré sur
# Fedora 44 : Breeze Light 134 pixels opaques, tous clairs ; « Breeze » (noir, contour blanc) 207 pixels dont 147 sombres et 39 clairs.
check "le pointeur Breeze_Light est une flèche blanche" python3 -c '
import struct
fichier = "/usr/share/icons/Breeze_Light/cursors/left_ptr"
d = open(fichier, "rb").read()
assert d[:4] == b"Xcur", "pas un fichier Xcursor : " + fichier
_, _, nb = struct.unpack_from("<III", d, 4)
meilleur = None
for i in range(nb):
    typ, taille, pos = struct.unpack_from("<III", d, 16 + 12 * i)
    if typ == 0xFFFD0002 and (meilleur is None or abs(taille - 32) < abs(meilleur[0] - 32)):
        meilleur = (taille, pos)
taille, pos = meilleur
_, _, _, _, larg, haut = struct.unpack_from("<IIIIII", d, pos)
pixels = struct.unpack_from("<%dI" % (larg * haut), d, pos + 36)
opaques = [p for p in pixels if p >> 24 == 255]
def lum(p):
    return (((p >> 16) & 255) * 299 + ((p >> 8) & 255) * 587 + (p & 255) * 114) / 1000
claires = sum(1 for p in opaques if lum(p) > 200)
sombres = sum(1 for p in opaques if lum(p) < 80)
print("pixels opaques :", len(opaques), "clairs :", claires, "sombres :", sombres)
assert opaques and claires > sombres * 2, "la flèche devrait être surtout blanche"
'
