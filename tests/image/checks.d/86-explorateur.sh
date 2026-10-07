# shellcheck shell=bash
section "Explorateur BinixX (Dolphin préréglé comme l'Explorateur de Windows 11)"
RC=.local/share/kxmlgui5/dolphin/dolphinui.rc
VUES=.local/share/dolphin/view_properties/global/.directory
check "barres d'outils de Dolphin dans /etc/skel (comptes créés après l'installation)" test -s "/etc/skel/${RC}"
check "vue « détails » par défaut dans /etc/skel" test -s "/etc/skel/${VUES}"
check "commande binixx-explorateur exécutable" test -x /usr/libexec/binixx/binixx-explorateur
check "les fichiers de /etc/skel sont de vrais fichiers (pas des liens)" \
    bash -c "! test -L /etc/skel/${RC} && ! test -L /etc/skel/${VUES}"

# La première ligne ressemble à celle de l'Explorateur (navigation, adresse), la seconde est sa barre de commandes. Le fichier garde une
# version plus basse que celle de Dolphin : c'est ce qui fait que KDE y reprend les barres sans écraser les menus d'une mise à jour.
check "dolphinui.rc : XML valide, version 1, deux barres d'outils avec les actions de l'Explorateur" python3 -c '
import xml.dom.minidom
doc = xml.dom.minidom.parse("/etc/skel/.local/share/kxmlgui5/dolphin/dolphinui.rc").documentElement
assert doc.tagName == "gui" and doc.getAttribute("name") == "dolphin", "pas un fichier de Dolphin"
assert doc.getAttribute("version") == "1", "version " + doc.getAttribute("version") + " : doit rester inférieure à celle de Dolphin"
barres = {b.getAttribute("name"): b for b in doc.getElementsByTagName("ToolBar")}
assert set(barres) == {"mainToolBar", "commandToolBar"}, sorted(barres)
actions = {nom: [a.getAttribute("name") for a in b.getElementsByTagName("Action")] for nom, b in barres.items()}
for nom in ("go_back", "go_forward", "go_up", "url_navigators"):
    assert nom in actions["mainToolBar"], nom
for nom in ("new_menu", "edit_cut", "edit_copy", "edit_paste", "renamefile", "movetotrash", "sort", "view_settings"):
    assert nom in actions["commandToolBar"], nom
assert barres["commandToolBar"].getAttribute("newline") == "true", "la barre de commandes doit être sur une seconde ligne"
'

# Dolphin ignore sans bruit une action qu'il ne connaît pas : on vérifie que chaque nom est bien dans Dolphin ou dans les bibliothèques
# KDE qui fournissent les actions standard (Couper, Copier, Renommer, Corbeille, Actualiser…), en chaîne ASCII ou UTF-16 selon la façon
# dont Qt la range. Le nom doit y figurer en entier : « redisplay » se trouve dans « view_redisplay », qui est le vrai nom de l'action
# Actualiser, et le bouton n'apparaissait pas. Une faute de frappe, ou un renommage en amont, fait échouer la construction au lieu de
# faire disparaître un bouton.
check "les actions de dolphinui.rc existent dans Dolphin ou dans les actions standard de KDE (nom entier)" python3 -c '
import glob, re, xml.dom.minidom
fichiers = (["/usr/bin/dolphin"] + glob.glob("/usr/lib64/libdolphin*.so*")
            + glob.glob("/usr/lib64/libKF6ConfigWidgets.so*") + glob.glob("/usr/lib64/libKF6XmlGui.so*"))
assert len(fichiers) >= 3, fichiers
contenu = b"".join(open(f, "rb").read() for f in fichiers)
doc = xml.dom.minidom.parse("/etc/skel/.local/share/kxmlgui5/dolphin/dolphinui.rc")
noms = {a.getAttribute("name") for a in doc.getElementsByTagName("Action")}
def present(nom):
    ascii_ = re.compile(rb"(?<![A-Za-z0-9_])" + re.escape(nom.encode()) + rb"(?![A-Za-z0-9_])")
    utf16 = re.compile(rb"(?<![A-Za-z0-9_]\x00)" + re.escape(nom.encode("utf-16-le")) + rb"(?![A-Za-z0-9_]\x00)")
    return bool(ascii_.search(contenu) or utf16.search(contenu))
manquantes = sorted(n for n in noms if not present(n))
assert not manquantes, "introuvables dans " + ", ".join(fichiers) + " : " + ", ".join(manquantes)
'

explorateur_vue_par_defaut() {
    local f="/etc/skel/${VUES}"
    [[ "$(kreadconfig6 --file "${f}" --group Dolphin --key ViewMode)" == 1 ]] &&
        [[ "$(kreadconfig6 --file "${f}" --group Dolphin --key Version)" == 4 ]] &&
        [[ "$(kreadconfig6 --file "${f}" --group Dolphin --key VisibleRoles)" == "Details_text,Details_modificationtime,Details_type,Details_size" ]]
}
check "vue par défaut : détails (ViewMode=1), colonnes Nom, Modifié le, Type, Taille" explorateur_vue_par_defaut

# Réglages valables pour tous les comptes : /etc/xdg/dolphinrc, lu par KDE derrière le dossier personnel (cascade)
explorateur_dolphinrc() (
    home="$(mktemp -d)"
    trap 'rm -rf "${home}"' EXIT
    lire() { HOME="${home}" XDG_CONFIG_HOME="${home}/.config" kreadconfig6 --file dolphinrc --group General --key "$1"; }
    [[ "$(lire ShowStatusBar)" == 1 && "$(lire ShowToolTips)" == true && "$(lire ShowZoomSlider)" == true ]]
)
check "dolphinrc : barre d'état sur toute la largeur, infobulle au survol, curseur de taille (lus sans fichier utilisateur)" explorateur_dolphinrc

# Un compte créé par useradd reçoit les deux fichiers (c'est ce que font Plasma Setup et l'installeur)
explorateur_compte_neuf() (
    set -e
    useradd -m binixx-test-explorateur
    trap 'userdel -r binixx-test-explorateur >/dev/null 2>&1' EXIT
    cmp "/etc/skel/${RC}" "/home/binixx-test-explorateur/${RC}"
    cmp "/etc/skel/${VUES}" "/home/binixx-test-explorateur/${VUES}"
)
check "un compte neuf reçoit les barres d'outils et la vue « détails » de /etc/skel" explorateur_compte_neuf

# La commande donne la même disposition à un compte existant, sans rien écraser sans --forcer, range ce qu'elle remplace, et la retire
explorateur_commande() (
    set -e
    home="$(mktemp -d)"
    trap 'rm -rf "${home}"' EXIT
    export HOME="${home}"
    local outil=/usr/libexec/binixx/binixx-explorateur
    [[ "$("${outil}" etat)" == explorateur=non ]]
    "${outil}" appliquer >/dev/null
    [[ "$("${outil}" etat)" == explorateur=oui ]]
    cmp "/etc/skel/${VUES}" "${home}/${VUES}"
    echo "# réglage de l'utilisateur" >>"${home}/${VUES}"
    "${outil}" appliquer >/dev/null
    grep -q "réglage de l'utilisateur" "${home}/${VUES}"
    "${outil}" appliquer --forcer >/dev/null
    if grep -q "réglage de l'utilisateur" "${home}/${VUES}"; then return 1; fi
    grep -rq "réglage de l'utilisateur" "${home}/.local/share/binixx/sauvegardes"
    "${outil}" retablir >/dev/null
    [[ "$("${outil}" etat)" == explorateur=non ]]
    [[ ! -e "${home}/${VUES}" ]]
    if "${outil}" commande-inconnue 2>/dev/null; then return 1; fi
)
check "binixx-explorateur : appliquer, conserver, remplacer avec sauvegarde, rétablir" explorateur_commande
