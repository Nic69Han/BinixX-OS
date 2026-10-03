# shellcheck shell=bash
# Recherche unique : sur le vrai système, les réglages, le catalogue et les applications installées (dont les Flatpak,
# dont les lanceurs sont ailleurs que dans /usr/share/applications) sont trouvés par l'utilisateur de test.
# La touche Windows + S est vérifiée avec les autres raccourcis (79-raccourcis.sh).
check_recherche() {
    section "Recherche unique (Windows + S)"
    local outil=/usr/libexec/binixx/binixx-recherche out
    out="$(runuser -u "${TEST_USER}" -- "${outil}" --texte imprimante 2>&1)" || true
    if grep -q "kcm kcm_printer_manager" <<<"${out}" && ! grep -q Traceback <<<"${out}"; then
        pass "« imprimante » ouvre le réglage des imprimantes"
    else
        fail "recherche « imprimante » : ${out:0:400}"
    fi
    out="$(runuser -u "${TEST_USER}" -- "${outil}" --texte word 2>&1)" || true
    if grep -q "centre catalogue word" <<<"${out}"; then pass "« word » trouve l'équivalent de Word"; else fail "recherche « word » : ${out:0:400}"; fi
    out="$(runuser -u "${TEST_USER}" -- "${outil}" --texte onlyoffice --json 2>&1)" || true
    if python3 -c 'import json,sys
g = json.loads(sys.argv[1])
apps = [r for c in g if c["categorie"] == "Applications" for r in c["resultats"]]
assert apps and apps[0]["action"][0] == "lanceur" and apps[0]["action"][1].endswith(".desktop"), apps' "${out}" 2>/dev/null; then
        pass "« onlyoffice » trouve l'application installée en Flatpak : $(python3 -c 'import json,sys; print([r["action"][1] for c in json.loads(sys.argv[1]) for r in c["resultats"] if c["categorie"]=="Applications"][0])' "${out}")"
    else
        fail "recherche « onlyoffice » : ${out:0:500}"
    fi
    out="$(runuser -u "${TEST_USER}" -- "${outil}" --texte firefox --json 2>&1)" || true
    if python3 -c 'import json,sys; g=json.loads(sys.argv[1]); assert any(c["categorie"]=="Applications" for c in g)' "${out}" 2>/dev/null; then
        pass "« firefox » trouve une application"
    else
        fail "recherche « firefox » : ${out:0:400}"
    fi
}
register_check base check_recherche
