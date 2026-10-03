#!/usr/bin/bash
# Gabarit d'image d'entreprise : copié dans l'image pour qu'un administrateur puisse en partir depuis
# un poste BinixX OS (`cp -r /usr/share/binixx/entreprise-template ~/mon-entreprise`). Le même dossier est
# construit et vérifié par la CI (`just test-entreprise`). Guide : docs/image-entreprise.md

set -ouex pipefail

install -d /usr/share/binixx/entreprise-template
cp -a /ctx/entreprise/. /usr/share/binixx/entreprise-template/
