# shellcheck shell=bash
section "Installer des applications"
check "lanceur « Installer des applications » valide" desktop-file-validate /usr/share/applications/nicos-applications.desktop
check "flatpak présent" command -v flatpak
check "licences des applications fournies" test -s /usr/share/nicos/catalogue-windows/licences.tsv
if out="$(NICOS_CENTRE=/usr/lib/nicos/centre NICOS_CATALOGUE=/usr/share/nicos/catalogue-windows/catalogue.tsv NICOS_LICENCES=/usr/share/nicos/catalogue-windows/licences.tsv NICOS_FLATPAKS=/usr/share/nicos/flatpaks/system-flatpaks.list QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_applications.py' 2>&1)"; then
    pass "applications : tests de la liste, des licences, de la commande et de la page (${out##*$'\n'})"
else
    fail "applications : tests de la liste, des licences, de la commande et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
