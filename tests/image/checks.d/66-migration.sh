# shellcheck shell=bash
section "Récupérer mes fichiers Windows"
check "lanceur « Récupérer mes fichiers Windows » valide" desktop-file-validate /usr/share/applications/binixx-migration.desktop
check "outil de migration exécutable" test -x /usr/libexec/binixx/binixx-migrer
check "outil de migration : aide sans erreur de syntaxe" bash -c '/usr/libexec/binixx/binixx-migrer 2>&1 | grep -q "binixx-migrer sources"'
check "BitLocker : cryptsetup présent" command -v cryptsetup
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_LIBEXEC=/usr/libexec/binixx QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_migration.py' 2>&1)"; then
    pass "migration : tests de l'outil et de la page (${out##*$'\n'})"
else
    fail "migration : tests de l'outil et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
