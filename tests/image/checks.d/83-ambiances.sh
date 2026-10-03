# shellcheck shell=bash
section "Ambiances (Aube, Nuit, Contraste élevé, Grand texte)"
check "outil binixx-ambiance exécutable" test -x /usr/libexec/binixx/binixx-ambiance
check "schéma de couleurs « contraste élevé » installé" test -s /usr/share/color-schemes/BinixXContraste.colors
check "le schéma se déclare BinixXContraste" grep -qx 'ColorScheme=BinixXContraste' /usr/share/color-schemes/BinixXContraste.colors
for theme in org.binixx.desktop org.binixx.dark.desktop; do
    check "thème global ${theme} présent (Aube et Nuit s'appuient dessus)" test -s "/usr/share/plasma/look-and-feel/${theme}/metadata.json"
done
for schema in BinixXClair BinixXSombre; do
    check "schéma de couleurs ${schema} présent" test -s "/usr/share/color-schemes/${schema}.colors"
done
check "kreadconfig6 présent" command -v kreadconfig6
# Outils de Plasma qui changent le bureau tout de suite : l'outil en essaie plusieurs et vérifie le résultat dans kdeglobals
check "un outil pour poser un thème global (plasma-apply-lookandfeel ou lookandfeeltool)" bash -c \
    'command -v plasma-apply-lookandfeel || command -v lookandfeeltool'
if command -v plasma-apply-colorscheme >/dev/null; then
    pass "plasma-apply-colorscheme présent : les couleurs changent dans les applications ouvertes"
else
    warn "plasma-apply-colorscheme absent : les couleurs sont écrites dans kdeglobals, appliquées à la prochaine ouverture de session"
fi
if command -v plasma-apply-cursortheme >/dev/null && plasma-apply-cursortheme --help 2>&1 | grep -q -- '--size'; then
    pass "plasma-apply-cursortheme --size présent : le pointeur grossit tout de suite"
else
    warn "plasma-apply-cursortheme sans --size : « Grand texte » grossit le pointeur à la prochaine ouverture de session seulement"
fi
check "les lignes « Thèmes : clair ou sombre » et « Contraste élevé » de Paramètres ouvrent la page « ambiances »" bash -c \
    "awk -F'\t' '(\$2==\"Thèmes : clair ou sombre\" || \$2==\"Contraste élevé\") && \$6==\"page\" && \$7==\"ambiances\" {n++} END {exit n != 2}' /usr/share/binixx/parametres/parametres.tsv"
check "l'outil refuse une ambiance inconnue" bash -c '! /usr/libexec/binixx/binixx-ambiance appliquer disco >/dev/null 2>&1'
out="$(/usr/libexec/binixx/binixx-ambiance liste 2>&1 || true)"
if [[ "$(wc -l <<<"${out}")" == 3 && "${out}" == *"contraste"* ]]; then pass "binixx-ambiance liste : trois ambiances"; else fail "binixx-ambiance liste : ${out:0:200}"; fi
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_SCHEMA_CONTRASTE=/usr/share/color-schemes/BinixXContraste.colors BINIXX_LNF=/usr/share/plasma/look-and-feel BINIXX_PARAMETRES=/usr/share/binixx/parametres/parametres.tsv QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_ambiances.py' 2>&1)"; then
    pass "ambiances : tests du contraste du schéma, des outils de Plasma, de « Grand texte » et de la page (${out##*$'\n'})"
else
    fail "ambiances : tests du contraste du schéma, des outils de Plasma, de « Grand texte » et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
