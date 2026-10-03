# shellcheck shell=bash
# « Récupérer mes fichiers Windows » : un faux profil Windows (créé en tant qu'utilisateur) est analysé puis copié
# dans un dossier de destination ; un second passage avec un fichier modifié ne doit rien écraser.
check_migration() {
    section "Récupérer mes fichiers Windows"
    local outil=/usr/libexec/binixx/binixx-migrer base=/var/tmp/binixx-test-migration profil dest out code
    profil="${base}/Users/Alice" dest="${base}/copie"
    rm -rf "${base}"
    install -d -o "${TEST_USER}" "${base}"
    runuser -u "${TEST_USER}" -- bash -c "
        mkdir -p '${profil}/Documents' '${profil}/Pictures' '${profil}/AppData/Local/Google/Chrome/User Data/Default'
        printf 'contrat v1' >'${profil}/Documents/contrat.txt'
        printf 'photo' >'${profil}/Pictures/photo.jpg'
        printf 'ini' >'${profil}/Documents/desktop.ini'
        printf '%s' '{\"roots\":{\"bookmark_bar\":{\"type\":\"folder\",\"name\":\"Barre\",\"children\":[{\"type\":\"url\",\"name\":\"BinixX OS\",\"url\":\"https://example.org/\"}]}}}' \\
            >'${profil}/AppData/Local/Google/Chrome/User Data/Default/Bookmarks'
    "

    check "le pilote NTFS est disponible (disque Windows lisible)" bash -c 'grep -qw ntfs3 /proc/filesystems || modprobe ntfs3'
    check "la liste des sources (sans droits) est du JSON valide" runuser -u "${TEST_USER}" -- bash -c "'${outil}' sources | python3 -c 'import json,sys; json.load(sys.stdin)'"
    out="$(runuser -u "${TEST_USER}" -- "${outil}" analyser "${profil}" 2>&1)"
    if grep -q '"profil_windows": true' <<<"${out}" && grep -q '"documents"' <<<"${out}"; then pass "le profil de test est reconnu"; else fail "profil non reconnu : ${out}"; fi

    out="$(runuser -u "${TEST_USER}" -- "${outil}" copier "${profil}" --dossiers documents,images --destination "${dest}" --json 2>&1)"
    code=$?
    if [[ ${code} -eq 0 ]]; then pass "copie terminée (code 0)"; else fail "copie : code ${code} : ${out}"; fi
    if [[ "$(cat "${dest}/Documents/contrat.txt" 2>/dev/null)" == "contrat v1" ]]; then pass "le document est copié"; else fail "document absent ou différent"; fi
    if [[ -f "${dest}/Images/photo.jpg" ]]; then pass "la photo est copiée"; else fail "photo absente"; fi
    if [[ ! -e "${dest}/Documents/desktop.ini" ]]; then pass "desktop.ini (créé par Windows) n'est pas copié"; else fail "desktop.ini copié"; fi
    if [[ "$(stat -c %a "${dest}/Documents/contrat.txt" 2>/dev/null)" == 644 ]]; then pass "droits normalisés (644)"; else fail "droits : $(stat -c %a "${dest}/Documents/contrat.txt" 2>&1)"; fi

    printf 'contrat v2' >"${profil}/Documents/contrat.txt"
    printf 'autre contenu' >"${dest}/Documents/contrat.txt"
    chown "${TEST_USER}" "${dest}/Documents/contrat.txt"
    runuser -u "${TEST_USER}" -- "${outil}" copier "${profil}" --dossiers documents --destination "${dest}" >/dev/null 2>&1
    if [[ "$(cat "${dest}/Documents/contrat.txt")" == "autre contenu" ]]; then pass "un fichier du PC n'est jamais écrasé"; else fail "fichier du PC écrasé"; fi
    if [[ "$(cat "${dest}/Documents/contrat (depuis Windows).txt" 2>/dev/null)" == "contrat v2" ]]; then pass "la version de Windows est gardée à côté"; else fail "copie « (depuis Windows) » absente"; fi

    out="$(runuser -u "${TEST_USER}" -- "${outil}" favoris "${profil}" --destination "${dest}" 2>&1)"
    if grep -q '"liens": 1' <<<"${out}" && grep -rqs 'https://example.org/' "${dest}"/*.html; then pass "les favoris sont exportés en HTML"; else fail "favoris : ${out}"; fi
    rm -rf "${base}"
}
register_check base check_migration
