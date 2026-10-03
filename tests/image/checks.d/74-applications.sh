# shellcheck shell=bash
section "Installer des applications"
check "lanceur « Installer des applications » valide" desktop-file-validate /usr/share/applications/binixx-applications.desktop
check "flatpak présent" command -v flatpak
check "licences des applications fournies" test -s /usr/share/binixx/catalogue-windows/licences.tsv
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_CATALOGUE=/usr/share/binixx/catalogue-windows/catalogue.tsv BINIXX_LICENCES=/usr/share/binixx/catalogue-windows/licences.tsv BINIXX_FLATPAKS=/usr/share/binixx/flatpaks/system-flatpaks.list QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_applications.py' 2>&1)"; then
    pass "applications : tests de la liste, des licences, de la commande et de la page (${out##*$'\n'})"
else
    fail "applications : tests de la liste, des licences, de la commande et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
