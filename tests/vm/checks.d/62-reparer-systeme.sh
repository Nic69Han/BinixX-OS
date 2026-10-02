# shellcheck shell=bash
# Sur le système installé : on modifie, supprime et ajoute des réglages, l'outil les voit, les remet comme dans
# l'image (avec sauvegarde), puis l'annulation les rend. pkexec (fenêtre d'authentification) ne se teste pas sans
# écran : l'outil est lancé en root, comme le fait pkexec. Le système est laissé comme on l'a trouvé.
check_reparer_systeme() {
    section "Réparer le système"
    local outil=/usr/libexec/nicos/nicos-reparer-systeme
    local modifie=/etc/xdg/plasma-welcomerc supprime=/etc/xdg/kicker-extra-favoritesrc ajoute=/etc/sysctl.d/99-nicos-test.conf
    local sum_m sum_s ctx_m out code
    check "action polkit connue de polkitd" pkaction --action-id org.nicos.reparer-systeme
    check "image de référence /usr/etc présente" test -d /usr/etc
    check "fichiers de test présents dans l'image" test -f "${modifie}" -a -f "${supprime}"
    [[ -f ${modifie} && -f ${supprime} ]] || return
    sum_m="$(sha256sum "${modifie}" | cut -d' ' -f1)"
    sum_s="$(sha256sum "${supprime}" | cut -d' ' -f1)"
    ctx_m="$(stat -c %C "${modifie}")"

    out="$(runuser -u "${TEST_USER}" -- "${outil}" liste --texte 2>&1)"
    code=$?
    if [[ ${code} -eq 0 ]]; then pass "liste des réglages modifiés produite sans droits particuliers ($(grep -c . <<<"${out}") ligne(s) avant l'essai)"; else
        fail "liste impossible (code ${code}) : ${out}"
        return
    fi
    # Constaté sur un poste neuf : le système écrit lui-même ces fichiers ; les proposer serait dangereux
    # (retirer default.target ferait démarrer sans bureau, retirer 00-keyboard.conf change le clavier)
    for danger in default.target 00-keyboard.conf system.control tuned.conf; do
        if grep -q "${danger}" <<<"${out}"; then fail "${danger} proposé à la réparation (écrit par le système)"; else pass "${danger} jamais proposé"; fi
    done
    echo "${out}" | sed 's/^/        avant l essai : /' | head -30
    for interdit in passwd shadow group hostname machine-id; do
        if grep -qE " ${interdit}( |$)" <<<"${out}"; then fail "${interdit} proposé à la réparation"; else pass "${interdit} jamais proposé"; fi
    done

    printf '[General]\nLastSeenVersion=0.0.1\n' >"${modifie}"
    rm -f "${supprime}"
    printf 'vm.swappiness=60\n' >"${ajoute}"
    out="$("${outil}" liste --texte 2>&1)"
    for attendu in "modifie .*xdg/plasma-welcomerc" "supprime .*xdg/kicker-extra-favoritesrc" "ajoute .*sysctl.d/99-nicos-test.conf"; do
        if grep -qE "${attendu}" <<<"${out}"; then pass "vu : ${attendu%% *} ${attendu##*.\*}"; else fail "changement non vu : ${attendu}"; fi
    done

    # refus : un compte, un chemin qui sort de /etc
    for intrus in passwd ../etc/passwd /etc/passwd; do
        "${outil}" restaurer "${intrus}" >/dev/null 2>&1
        code=$?
        if [[ ${code} -eq 2 ]]; then pass "« ${intrus} » refusé (code 2)"; else fail "« ${intrus} » : code ${code} au lieu de 2"; fi
    done

    out="$("${outil}" restaurer xdg/plasma-welcomerc xdg/kicker-extra-favoritesrc sysctl.d/99-nicos-test.conf 2>&1)"
    code=$?
    if [[ ${code} -eq 0 ]]; then pass "réparation faite"; else fail "réparation : code ${code} : ${out}"; fi
    if [[ "$(sha256sum "${modifie}" | cut -d' ' -f1)" == "${sum_m}" ]]; then pass "fichier modifié : remis à l'identique de l'image"; else fail "fichier modifié : contenu différent de l'image"; fi
    if [[ -f ${supprime} && "$(sha256sum "${supprime}" | cut -d' ' -f1)" == "${sum_s}" ]]; then pass "fichier supprimé : recréé à l'identique"; else fail "fichier supprimé : non recréé"; fi
    if [[ ! -e ${ajoute} ]]; then pass "fichier ajouté : retiré"; else fail "fichier ajouté : toujours là"; fi
    if [[ "$(stat -c %C "${modifie}")" == "${ctx_m}" ]]; then pass "contexte SELinux conservé (${ctx_m})"; else fail "contexte SELinux changé : ${ctx_m} -> $(stat -c %C "${modifie}")"; fi
    out="$("${outil}" liste --texte 2>&1)"
    if grep -qE "plasma-welcomerc|kicker-extra-favoritesrc|99-nicos-test" <<<"${out}"; then fail "les fichiers réparés sont encore listés"; else pass "plus rien à réparer parmi les fichiers de l'essai"; fi
    check "sauvegarde gardée (copie de la version remplacée)" bash -c "ls /var/lib/nicos/sauvegardes-etc/*/etc/sysctl.d/99-nicos-test.conf"
    check "dossier des sauvegardes réservé à l'administrateur" bash -c "[ \"\$(stat -c %a /var/lib/nicos/sauvegardes-etc)\" = 700 ]"

    "${outil}" annuler >/dev/null 2>&1
    code=$?
    if [[ ${code} -eq 0 ]]; then pass "annulation faite"; else fail "annulation : code ${code}"; fi
    if [[ "$(cat "${modifie}")" == $'[General]\nLastSeenVersion=0.0.1' && ! -e ${supprime} && -f ${ajoute} ]]; then
        pass "annulation : les trois fichiers retrouvent leur état d'avant"
    else
        fail "annulation : état inattendu"
    fi

    # retour à l'état d'origine pour la suite du test
    "${outil}" restaurer xdg/plasma-welcomerc xdg/kicker-extra-favoritesrc sysctl.d/99-nicos-test.conf >/dev/null 2>&1
    if [[ "$(sha256sum "${modifie}" | cut -d' ' -f1)" == "${sum_m}" && "$(sha256sum "${supprime}" | cut -d' ' -f1)" == "${sum_s}" && ! -e ${ajoute} ]]; then
        pass "système remis comme avant l'essai"
    else
        fail "le système n'a pas été remis comme avant l'essai"
    fi
}
register_check base check_reparer_systeme
