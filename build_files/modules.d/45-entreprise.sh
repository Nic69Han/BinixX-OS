#!/usr/bin/bash
# Gabarit d'image d'entreprise : copié dans l'image pour qu'un administrateur puisse en partir depuis
# un poste NicOS (`cp -r /usr/share/nicos/entreprise-template ~/mon-entreprise`). Le même dossier est
# construit et vérifié par la CI (`just test-entreprise`). Guide : docs/image-entreprise.md

set -ouex pipefail

install -d /usr/share/nicos/entreprise-template
cp -a /ctx/entreprise/. /usr/share/nicos/entreprise-template/
