#!/usr/bin/bash
# Fabrique la police Selawik et la place dans l'image (system_files/usr/share/fonts/selawik/).
#
# Selawik est publiée par Microsoft sous licence libre (SIL OFL 1.1) pour remplacer Segoe UI,
# la police de l'interface de Windows, avec les mêmes largeurs de caractères. Microsoft ne
# publie les fichiers .ttf que dans les « Releases » GitHub : ce script les recompile depuis
# les sources officielles du tag 1.01 avec fontmake, sans rien changer au dessin des lettres.
#
# Usage : branding/fabriquer-selawik.sh   (git et python3 ; fontmake est installé dans un
#         environnement temporaire)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${REPO_ROOT}/system_files/usr/share/fonts/selawik"
SOURCE_URL=https://github.com/microsoft/Selawik
SOURCE_TAG=1.01 # commit b65ff9ce7c4673e75ec5c622924a6b6f61f2f876 ; sources identiques sur main
FONTMAKE_VERSION=3.12.1

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

git -c advice.detachedHead=false clone -q --depth 1 --branch "${SOURCE_TAG}" "${SOURCE_URL}" "${work}/selawik"
python3 -m venv "${work}/venv"
"${work}/venv/bin/pip" install -q "fontmake==${FONTMAKE_VERSION}" ttfautohint-py
glyphs="${work}/selawik/Source files/Glyphs/selawik.glyphs"
# Dates des polices = date des sources : deux fabrications donnent les mêmes fichiers
SOURCE_DATE_EPOCH="$(git -C "${work}/selawik" log -1 --format=%ct)"
export SOURCE_DATE_EPOCH

# Particularités des sources :
# - « TTFAutohint options » y vaut "New Value" (valeur par défaut de l'éditeur Glyphs, refusée
#   par ttfautohint) : -a applique les réglages standard de ttfautohint ;
# - le filtre GlyphsAddExtremes, propre à l'éditeur Glyphs, n'existe pas dans fontmake : il est
#   ignoré (fontmake le signale) ;
# - Light et Semilight y ont la même graisse (300) : en une seule passe, Semilight remplace
#   Light. Light est donc exportée à part, Semilight retirée de la liste des instances.
(cd "${work}" && "${work}/venv/bin/fontmake" -g "${glyphs}" -o ttf -i -a --output-dir ttf)
"${work}/venv/bin/python" - "${glyphs}" "${work}/light.glyphs" <<'PYEOF'
import sys

import glyphsLib

font = glyphsLib.GSFont(sys.argv[1])
font.instances = [instance for instance in font.instances if instance.name != "Semilight"]
font.save(sys.argv[2])
PYEOF
(cd "${work}" && "${work}/venv/bin/fontmake" -g "${work}/light.glyphs" -o ttf -i -a --output-dir ttf-light)

mkdir -p "${DEST}"
rm -f "${DEST}"/*.ttf
for weight in Semilight Regular Semibold Bold; do
    install -m 0644 "${work}/ttf/Selawik-${weight}.ttf" "${DEST}/"
done
install -m 0644 "${work}/ttf-light/Selawik-Light.ttf" "${DEST}/"
install -m 0644 "${work}/selawik/LICENSE.txt" "${DEST}/LICENSE.txt"
ls -l "${DEST}"
