# Contexte de build : ces fichiers servent pendant le build sans être copiés tels quels dans l'image
FROM scratch AS ctx
COPY build_files /
COPY system_files /system_files
COPY flatpaks /flatpaks
COPY entreprise /entreprise

# Image de base : Fedora Kinoite (KDE Plasma) préparée par Universal Blue
# (codecs, pilotes, Flathub, mises à jour automatiques déjà configurés).
# On configure cette image, on ne la forke pas.
#
# Version de Fedora épinglée : l'étiquette `44` suit uniquement Fedora 44. Le build
# quotidien récupère donc les correctifs de sécurité sans intervention, mais le passage
# à la version suivante ne se fait jamais tout seul.
# Changer de version = modifier ce numéro dans une pull request et la valider,
# test en VM compris : `sudo just build` puis
# `sudo tests/vm/run-vm-test.sh --image localhost/nicos:testing` (voir tests/README.md).
# À faire avant la fin du support de Fedora 44 (environ un mois après la sortie de Fedora 46).
FROM ghcr.io/ublue-os/kinoite-main:44

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
