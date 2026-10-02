# shellcheck shell=bash
# Centre d'administration (Cockpit) : chargé par check-image.sh

section "Administration à la souris"
for pkg in cockpit cockpit-files cockpit-networkmanager cockpit-ostree cockpit-selinux cockpit-storaged \
    plasma-firewall plasma-firewall-firewalld; do
    check "${pkg} installé" rpm -q "${pkg}"
done
check "centre d'administration démarré à la demande (cockpit.socket)" test "$(systemctl is-enabled cockpit.socket 2>/dev/null)" = enabled
check "centre d'administration limité au PC lui-même" \
    grep -qx 'ListenStream=127.0.0.1:9090' /usr/lib/systemd/system/cockpit.socket.d/50-nicos-localhost.conf
check "lanceur « Administration du PC » valide" desktop-file-validate /usr/share/applications/nicos-administration.desktop
