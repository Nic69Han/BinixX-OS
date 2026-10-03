# shellcheck shell=bash
section "Raccourcis clavier (aide-mémoire des raccourcis de Windows)"
check "outil binixx-raccourcis exécutable" test -x /usr/libexec/binixx/binixx-raccourcis
check "fichier des raccourcis présent" test -s /usr/share/binixx/raccourcis/raccourcis.tsv
for lanceur in binixx-executer binixx-gestionnaire-taches; do
    check "lanceur ${lanceur} valide" desktop-file-validate "/usr/share/applications/${lanceur}.desktop"
done
# Les programmes que ces raccourcis ouvrent existent dans l'image
check "Windows + E : Dolphin présent (org.kde.dolphin.desktop)" test -f /usr/share/applications/org.kde.dolphin.desktop
check "Windows + R : KRunner présent" bash -c 'command -v krunner || compgen -G "/usr/share/dbus-1/services/org.kde.krunner.service"'
check "Windows + R : busctl présent" command -v busctl
check "Ctrl + Maj + Échap : Moniteur système présent" test -f /usr/share/applications/org.kde.plasma-systemmonitor.desktop
check "Ctrl + Maj + Échap : kioclient présent (ouvre le lanceur du Moniteur système)" command -v kioclient
check "Windows + Maj + S : Spectacle présent" command -v spectacle
check "les raccourcis annoncés par la page sont listés" bash -c '/usr/libexec/binixx/binixx-raccourcis liste | grep -q "Windows + E"'
# Hors session de bureau (build), l'outil doit répondre par une erreur claire, jamais par une trace d'erreur Python
out="$(/usr/libexec/binixx/binixx-raccourcis verifier 2>&1 || true)"
if grep -q "impossible de lire" <<<"${out}" && ! grep -q Traceback <<<"${out}"; then
    pass "sans session de bureau : message clair, pas de plantage"
else
    fail "binixx-raccourcis verifier sans session : ${out:0:200}"
fi
check "une action inconnue est refusée" bash -c '! /usr/libexec/binixx/binixx-raccourcis bidule >/dev/null 2>&1'
# La page « Aide-mémoire des raccourcis » est ouverte depuis Paramètres, et l'image fournit les touches annoncées
check "la ligne « Aide-mémoire des raccourcis » de Paramètres ouvre la page « raccourcis »" bash -c \
    "awk -F'\t' '\$2==\"Aide-mémoire des raccourcis\" && \$6==\"page\" && \$7==\"raccourcis\" {found=1} END {exit !found}' /usr/share/binixx/parametres/parametres.tsv"
for touches in 'Meta+I' 'Meta+E' 'Meta+R' 'Ctrl+Shift+Esc'; do
    check "touche ${touches} fournie par l'image" grep -q "^_launch=${touches}\$" /etc/xdg/kglobalshortcutsrc
done
# Une touche annoncée n'a qu'un propriétaire : les lanceurs de KDE qui la déclarent aussi (Spectacle, Configuration du système…) la
# perdent au build (module 78-raccourcis.sh, qui réécrit leur X-KDE-Shortcuts) ; on liste ce qui a été retiré, et il ne doit
# rester aucun conflit
check "journal des touches retirées présent" test -f /usr/share/binixx/raccourcis/touches-retirees.txt
sed 's/^/            /' /usr/share/binixx/raccourcis/touches-retirees.txt
out="$(/usr/libexec/binixx/binixx-raccourcis surcharger --verifier 2>&1 || true)"
if /usr/libexec/binixx/binixx-raccourcis surcharger --verifier >/dev/null 2>&1; then
    pass "aucun lanceur de KDE ne dispute une touche de BinixX OS (${out##*$'\n'})"
else
    fail "des lanceurs de KDE gardent une touche de BinixX OS : ${out:0:400}"
fi
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_RACCOURCIS=/usr/share/binixx/raccourcis/raccourcis.tsv BINIXX_XDG_RACCOURCIS=/etc/xdg/kglobalshortcutsrc BINIXX_LANCEURS=/usr/share/applications QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_raccourcis.py' 2>&1)"; then
    pass "raccourcis : tests du fichier, des codes de touches, de la lecture de KDE et de la page (${out##*$'\n'})"
else
    fail "raccourcis : tests du fichier, des codes de touches, de la lecture de KDE et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
