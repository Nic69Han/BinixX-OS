#!/usr/bin/bash
# Contrôle obligatoire de greenboot : l'écran de connexion doit démarrer.
# Un PC sans écran de connexion est inutilisable : si une mise à jour en est la cause, greenboot
# redémarre jusqu'à trois fois, puis revient à la version précédente de NicOS.
#
# Ne bloque jamais un PC volontairement sans bureau (cible par défaut autre que graphical.target),
# ni un PC lent : on attend jusqu'à 4 minutes que le service démarre.

[[ "$(systemctl get-default)" == graphical.target ]] || exit 0

for _ in $(seq 120); do
    systemctl is-active --quiet display-manager.service && exit 0
    # Échec certain (service masqué ou en échec) : inutile d'attendre
    [[ "$(systemctl is-enabled display-manager.service 2>/dev/null)" == masked ]] && break
    systemctl is-failed --quiet display-manager.service && break
    sleep 2
done
echo "NicOS : l'écran de connexion (display-manager.service) ne démarre pas" >&2
exit 1
