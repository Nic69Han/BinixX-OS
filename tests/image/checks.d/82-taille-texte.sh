# shellcheck shell=bash
section "Taille du texte (un curseur de 100 % à 200 %)"
check "outil binixx-taille-texte exécutable" test -x /usr/libexec/binixx/binixx-taille-texte
check "kreadconfig6 présent" command -v kreadconfig6
check "kwriteconfig6 présent" command -v kwriteconfig6
# kwriteconfig6 sait prévenir les applications (--notify) : sans cela, le texte ne changerait qu'à la prochaine ouverture
if kwriteconfig6 --help 2>&1 | grep -q -- '--notify'; then
    pass "kwriteconfig6 accepte --notify : les applications ouvertes changent de police tout de suite"
else
    warn "kwriteconfig6 n'a pas d'option --notify : l'outil écrit quand même, mais le changement attend la réouverture des applications"
fi
check "la ligne « Taille du texte » de Paramètres ouvre la page « taille_texte »" bash -c \
    "awk -F'\t' '\$2==\"Taille du texte\" && \$6==\"page\" && \$7==\"taille_texte\" {found=1} END {exit !found}' /usr/share/binixx/parametres/parametres.tsv"
check "l'outil refuse une taille mal écrite" bash -c '! /usr/libexec/binixx/binixx-taille-texte appliquer grand >/dev/null 2>&1'
out="$(/usr/libexec/binixx/binixx-taille-texte etat 2>&1 || true)"
if [[ "${out}" == 100 ]]; then pass "l'état de départ est 100 %"; else fail "binixx-taille-texte etat : ${out:0:200}"; fi
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_taille_texte.py' 2>&1)"; then
    pass "taille du texte : tests du calcul des polices, de l'écriture, du retour à l'origine et de la page (${out##*$'\n'})"
else
    fail "taille du texte : tests du calcul des polices, de l'écriture, du retour à l'origine et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
