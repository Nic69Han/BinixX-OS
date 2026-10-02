# shellcheck shell=bash
section "Centre NicOS (accueil)"
check "python3-pyside6 installé" rpm -q python3-pyside6
check "lanceur « Bienvenue dans NicOS » valide" desktop-file-validate /usr/share/applications/nicos-centre.desktop
check "ouverture automatique à la première session" desktop-file-validate /etc/xdg/autostart/nicos-accueil.desktop
check "centre de bienvenue de KDE : pas d'ouverture automatique" grep -qx 'LastSeenVersion=99.0.0' /etc/xdg/plasma-welcomerc
check "bytecode Python préparé dans l'image" bash -c 'compgen -G "/usr/lib/nicos/centre/nicos_centre/__pycache__/*.pyc"'
rm -rf /tmp/centre-test
if out="$(QT_QPA_PLATFORM=offscreen /usr/libexec/nicos/nicos-centre --test /tmp/centre-test 2>&1)"; then
    pass "toutes les pages du Centre se construisent (${out##*: })"
else
    fail "Centre NicOS (--test) : ${out}"
fi
check "capture de la page d'accueil produite" test -s /tmp/centre-test/accueil.png
