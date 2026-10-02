# shellcheck shell=bash
section "Modèles de documents (Créer nouveau)"
TEMPLATES=/usr/share/templates
for desktop in Document-texte Classeur Presentation; do
    check "modèle ${desktop} : lanceur valide" desktop-file-validate "${TEMPLATES}/${desktop}.desktop"
done
for model in Document.docx:word/document.xml Classeur.xlsx:xl/workbook.xml Presentation.pptx:ppt/presentation.xml; do
    file="${model%%:*}"
    part="${model##*:}"
    check "modèle ${file} : fichier Office valide (${part})" python3 -c "
import sys, zipfile
z = zipfile.ZipFile('${TEMPLATES}/.source/${file}')
assert z.testzip() is None and '${part}' in z.namelist() and '[Content_Types].xml' in z.namelist()
"
done
for desktop in Document-texte Classeur Presentation; do
    target="$(sed -n 's/^URL=//p' "${TEMPLATES}/${desktop}.desktop")"
    check "modèle ${desktop} : désigne ${target}" test -s "${TEMPLATES}/${target}"
done
