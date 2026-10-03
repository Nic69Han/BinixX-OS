# shellcheck shell=bash
section "Aide et dépannage"
check "lanceur « Obtenir de l'aide » valide" desktop-file-validate /usr/share/applications/binixx-aide.desktop
check "rapport de diagnostic exécutable" test -x /usr/libexec/binixx/binixx-diagnostic
check "remise à zéro du bureau exécutable" test -x /usr/libexec/binixx/binixx-reinitialiser-bureau
check "remise à zéro du bureau : script de démarrage de Plasma valide" sh -n /etc/xdg/plasma-workspace/env/90-binixx-reinitialiser.sh
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_LIBEXEC=/usr/libexec/binixx QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_aide.py' 2>&1)"; then
    pass "aide : tests du rapport et de la remise à zéro (${out##*$'\n'})"
else
    fail "aide : tests du rapport et de la remise à zéro"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
