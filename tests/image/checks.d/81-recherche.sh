# shellcheck shell=bash
section "Recherche unique (Windows + S)"
check "outil binixx-recherche exécutable" test -x /usr/libexec/binixx/binixx-recherche
check "lanceur « Rechercher » valide" desktop-file-validate /usr/share/applications/binixx-recherche.desktop
check "touche Windows + S : raccourci fourni" grep -qx '_launch=Meta+S' /etc/xdg/kglobalshortcutsrc
check "le lanceur déclare la même touche (Meta+S)" grep -qx 'X-KDE-Shortcuts=Meta+S' /usr/share/applications/binixx-recherche.desktop
check "kioclient présent (ouvre les applications trouvées)" command -v kioclient
check "xdg-open présent (ouvre les fichiers trouvés)" command -v xdg-open
if command -v baloosearch6 >/dev/null; then
    pass "baloosearch6 présent : la recherche montre aussi les fichiers"
else
    warn "baloosearch6 absent : la recherche ne montrera pas de fichiers"
fi
# La recherche sans fenêtre, sur les vrais fichiers de l'image
out="$(/usr/libexec/binixx/binixx-recherche --texte imprimante 2>&1 || true)"
if grep -q "Imprimantes et scanners" <<<"${out}" && grep -q "kcm kcm_printer_manager" <<<"${out}" && ! grep -q Traceback <<<"${out}"; then
    pass "« imprimante » trouve le réglage des imprimantes"
else
    fail "binixx-recherche --texte imprimante : ${out:0:300}"
fi
out="$(/usr/libexec/binixx/binixx-recherche --texte word 2>&1 || true)"
if grep -q "Microsoft Word" <<<"${out}" && grep -q "centre catalogue word" <<<"${out}"; then
    pass "« word » trouve l'équivalent de Word dans le catalogue"
else
    fail "binixx-recherche --texte word : ${out:0:300}"
fi
out="$(/usr/libexec/binixx/binixx-recherche --texte dolphin --json 2>&1 || true)"
if python3 -c 'import json,sys; g=json.loads(sys.argv[1]); assert any(c["categorie"]=="Applications" for c in g)' "${out}" 2>/dev/null; then
    pass "« dolphin » trouve une application installée (réponse JSON valide)"
else
    fail "binixx-recherche --texte dolphin --json : ${out:0:300}"
fi
out="$(/usr/libexec/binixx/binixx-recherche --texte zzzzqqqqxxxx 2>&1)" && code=0 || code=$?
if [[ "${code}" -eq 1 ]] && ! grep -q Traceback <<<"${out}"; then
    pass "un texte sans réponse sort en erreur, sans trace"
else
    fail "binixx-recherche --texte zzzzqqqqxxxx : code ${code}, ${out:0:200}"
fi
# La fenêtre se construit et se peint (hors écran), avec des résultats
rm -rf /tmp/recherche-test
if out="$(QT_QPA_PLATFORM=offscreen /usr/libexec/binixx/binixx-recherche --test /tmp/recherche-test 2>&1)"; then
    pass "la fenêtre de recherche se construit et trouve des résultats (${out##*: })"
    check "capture de la fenêtre de recherche produite" test -s /tmp/recherche-test/recherche.png
else
    fail "binixx-recherche --test : ${out:0:300}"
fi
rm -rf /tmp/recherche-test
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_PARAMETRES=/usr/share/binixx/parametres/parametres.tsv BINIXX_CATALOGUE=/usr/share/binixx/catalogue-windows/catalogue.tsv QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_recherche.py' 2>&1)"; then
    pass "recherche : tests de la notation, des lanceurs, du regroupement, de l'ouverture et de la fenêtre (${out##*$'\n'})"
else
    fail "recherche : tests de la notation, des lanceurs, du regroupement, de l'ouverture et de la fenêtre"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
