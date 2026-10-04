# shellcheck shell=bash
section "Centre BinixX OS (accueil)"
check "python3-pyside6 installé" rpm -q python3-pyside6
check "lanceur « Bienvenue dans BinixX OS » valide" desktop-file-validate /usr/share/applications/binixx-centre.desktop
check "ouverture automatique à la première session" desktop-file-validate /etc/xdg/autostart/binixx-accueil.desktop
check "centre de bienvenue de KDE : pas d'ouverture automatique" grep -qx 'LastSeenVersion=99.0.0' /etc/xdg/plasma-welcomerc
check "bytecode Python préparé dans l'image" bash -c 'compgen -G "/usr/lib/binixx/centre/binixx_centre/__pycache__/*.pyc"'
rm -rf /tmp/centre-test
if out="$(QT_QPA_PLATFORM=offscreen /usr/libexec/binixx/binixx-centre --test /tmp/centre-test 2>&1)"; then
    pass "toutes les pages du Centre se construisent (${out##*: })"
    # chaque page a sa capture : l'en-tête en dégradé, les cartes et la barre latérale se peignent sans erreur
    for page in $(tr -d ',' <<<"${out##*: }"); do
        check "capture de la page « ${page} » produite" test -s "/tmp/centre-test/${page}.png"
    done
else
    fail "Centre BinixX OS (--test) : ${out}"
fi
rm -rf /tmp/centre-test
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_widgets.py' 2>&1)"; then
    pass "style commun : tests des cartes, de la grille et des pages (${out##*$'\n'})"
else
    fail "style commun : tests des cartes, de la grille et des pages"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_AUTOSTART=/etc/xdg/autostart/binixx-accueil.desktop QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_premiere_session.py' 2>&1)"; then
    pass "accueil de premier démarrage : jamais dans la session de Plasma Setup, une seule fois pour l'utilisateur (${out##*$'\n'})"
else
    fail "accueil de premier démarrage : tests de la session de Plasma Setup"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
