#!/usr/bin/bash
# Télécharge l'image bootc-image-builder (qui fabrique l'ISO du test VM) dans le stockage de podman.
#
# 1. podman pull, trois essais ;
# 2. si quay.io coupe la connexion en cours de route (« unexpected EOF » sur le CDN, constaté le
#    2 octobre 2026 pendant plus d'une demi-heure, toujours sur la même couche), téléchargement par
#    blocs avec reprise là où la coupure a eu lieu, contrôle de l'empreinte de chaque couche, puis
#    import du résultat (format OCI) dans podman.
#
# Usage : tests/vm/fetch-bib.sh [image]   (défaut : quay.io/centos-bootc/bootc-image-builder:latest)
# Doit tourner avec le même utilisateur que run-vm-test.sh (root).

set -euo pipefail

IMAGE="${1:-quay.io/centos-bootc/bootc-image-builder:latest}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if podman image exists "${IMAGE}"; then
    echo "${IMAGE} déjà présente"
    exit 0
fi

for attempt in 1 2 3; do
    if podman pull "${IMAGE}"; then exit 0; fi
    echo "podman pull interrompu (essai ${attempt}/3)"
    sleep $((attempt * 10))
done

echo "Téléchargement par blocs avec reprise"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT
python3 "${HERE}/fetch-oci.py" "${IMAGE}" "${work}/oci"
image_id="$(podman pull --quiet "oci:${work}/oci:latest")"
podman tag "${image_id}" "${IMAGE}"
echo "${IMAGE} importée (${image_id})"
