# shellcheck shell=bash
# Discover : les boutons « Installer » des pages Jeux et Catalogue ouvrent « plasma-discover --application <identifiant> ». Discover ne
# trouve l'application (sinon : « Aucune entrée pour net.lutris.Lutris ») que si le dépôt Flathub est configuré ET si ses fiches
# d'applications (AppStream) sont téléchargées. Le relevé dit ce qu'il en est sur le système installé ; les vérifications échouent
# si les fiches manquent alors que le réseau et le dépôt sont là.
APPLICATIONS_A_LA_DEMANDE=(net.lutris.Lutris com.valvesoftware.Steam com.heroicgameslauncher.hgl)

fiches_flathub() {
    # le fichier que Discover (moteur Flatpak) lit pour le dépôt « flathub » du système
    echo "/var/lib/flatpak/appstream/flathub/$(uname -m)/active/appstream.xml.gz"
}

decrire_discover() {
    section "Discover et les fiches de Flathub (relevé)"
    indente() { sed 's/^/            /'; }
    local fiches ident
    fiches="$(fiches_flathub)"
    wait_for 900 test -f /var/lib/binixx/flatpaks.sha256 || echo "  (installation des Flatpak par défaut non terminée)"
    echo "  paquets :"
    rpm -q plasma-discover plasma-discover-flatpak plasma-discover-rpm-ostree 2>&1 | indente
    echo "  dépôts Flatpak du système :"
    flatpak remotes --system --columns=name,url,options,filter 2>&1 | indente
    echo "  fiches AppStream de Flathub (${fiches}) :"
    # shellcheck disable=SC2012
    ls -la "$(dirname "${fiches}")/" 2>&1 | indente
    if [[ -s ${fiches} ]]; then
        echo "    taille décompressée : $(zcat "${fiches}" | wc -c) octets, $(zcat "${fiches}" | grep -c '<component') fiches"
        for ident in "${APPLICATIONS_A_LA_DEMANDE[@]}"; do
            echo "    ${ident} : $(zcat "${fiches}" | grep -c "<id>${ident}") entrée(s)"
        done
    fi
    echo "  moteurs de Discover :"
    QT_QPA_PLATFORM=offscreen timeout 60 plasma-discover --listbackends 2>&1 | head -n 20 | indente || true
    echo "  service d'installation des Flatpak par défaut :"
    systemctl show -p ActiveState,SubState,Result,NRestarts binixx-flatpak-install.service | indente
    journalctl -u binixx-flatpak-install.service -b --no-pager 2>/dev/null | tail -n 12 | indente
    return 0
}
register_check base decrire_discover

verifier_discover() {
    section "Discover trouve les applications à la demande"
    local fiches ident
    fiches="$(fiches_flathub)"
    check "le dépôt Flathub est configuré pour tout le système" bash -c 'flatpak remotes --system --columns=name | grep -qx flathub'
    check "les fiches AppStream de Flathub sont téléchargées (Discover les lit)" test -s "${fiches}"
    for ident in "${APPLICATIONS_A_LA_DEMANDE[@]}"; do
        # shellcheck disable=SC2016  # le $1 et le $2 sont ceux du bash -c
        check "les fiches de Flathub décrivent ${ident}" bash -c 'zcat "$1" | grep -q "<id>$2"' _ "${fiches}" "${ident}"
    done
}
register_check base verifier_discover
