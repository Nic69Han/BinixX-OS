#!/usr/bin/bash
# Retour arrière automatique : si une mise à jour empêche l'écran de connexion de démarrer, le PC revient
# tout seul à la version précédente après trois tentatives (greenboot, licence BSD-3-Clause, conçu pour bootc).
# Les contrôles de BinixX OS sont dans system_files/etc/greenboot/check/required.d/ ; docs/mises-a-jour.md.

set -ouex pipefail

dnf5 -y install greenboot
rpm -q greenboot
# Les contrôles « par défaut » vérifient que les dépôts de mises à jour répondent au DNS : un PC qui démarre
# hors connexion (portable, panne de box) reviendrait à tort à l'ancienne version. On ne les installe pas.
if rpm -q greenboot-default-health-checks; then
    echo "greenboot-default-health-checks ne doit pas être installé" >&2
    exit 1
fi
systemctl enable greenboot-healthcheck.service
