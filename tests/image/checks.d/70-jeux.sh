# shellcheck shell=bash
section "Jeux"
check "lanceur « Jeux » valide" desktop-file-validate /usr/share/applications/binixx-jeux.desktop
# Rien n'est installé d'office : ni boutique de jeux, ni client Steam dans la liste Flatpak du premier démarrage
for app in com.valvesoftware.Steam net.lutris.Lutris com.heroicgameslauncher.hgl; do
    check "${app} non installé d'office" bash -c "! grep -qx '${app}' /usr/share/binixx/flatpaks/system-flatpaks.list"
done
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_CATALOGUE=/usr/share/binixx/catalogue-windows/catalogue.tsv QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_jeux.py' 2>&1)"; then
    pass "jeux : tests du catalogue, des cartes graphiques et de la page (${out##*$'\n'})"
else
    fail "jeux : tests du catalogue, des cartes graphiques et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
