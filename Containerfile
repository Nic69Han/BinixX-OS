# Contexte de build : ces fichiers servent pendant le build sans être copiés tels quels dans l'image
FROM scratch AS ctx
COPY build_files /
COPY system_files /system_files
COPY flatpaks /flatpaks

# Image de base : Fedora Kinoite (KDE Plasma) préparée par Universal Blue
# (codecs, pilotes, Flathub, mises à jour automatiques déjà configurés).
# On configure cette image, on ne la forke pas.
#
# L'étiquette `latest` n'est volontairement pas épinglée par digest : le build
# quotidien récupère ainsi les correctifs de sécurité de Fedora sans intervention.
# Pour des builds reproductibles, épinglez le digest (…:latest@sha256:…) et
# installez Renovate sur le dépôt pour qu'il le mette à jour (voir .github/renovate.json5).
FROM ghcr.io/ublue-os/kinoite-main:latest

### PERSONNALISATION
## Tout se passe dans build_files/build.sh (paquets, réglages KDE, services)
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/build.sh

### VÉRIFICATION
## Contrôle que l'image finale est une image bootc valide
RUN bootc container lint
