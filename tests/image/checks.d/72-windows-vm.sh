# shellcheck shell=bash
section "Windows dans une machine virtuelle"
check "lanceur « Windows complet » valide" desktop-file-validate /usr/share/applications/binixx-windows-vm.desktop
check "Podman présent (WinBoat)" command -v podman
check "Podman Compose présent (WinBoat)" command -v podman-compose
check "FreeRDP 3 présent (WinBoat)" bash -c "xfreerdp --version 2>&1 | grep -q 'version 3\\.'"
check "Boxes proposé par le catalogue" grep -qP '\tflatpak\torg.gnome.Boxes\t' /usr/share/binixx/catalogue-windows/catalogue.tsv
# Boxes et WinBoat s'installent à la demande : ni l'un ni l'autre n'est dans la liste du premier démarrage
check "Boxes non installé d'office" bash -c "! grep -qx 'org.gnome.Boxes' /usr/share/binixx/flatpaks/system-flatpaks.list"
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_CATALOGUE=/usr/share/binixx/catalogue-windows/catalogue.tsv QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_windows.py' 2>&1)"; then
    pass "windows : tests des prérequis, de la page et du catalogue (${out##*$'\n'})"
else
    fail "windows : tests des prérequis, de la page et du catalogue"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
