# shellcheck shell=bash
# Raccourcis clavier : chaque touche que la page « Raccourcis » annonce doit être enregistrée par KDE dans la session de
# l'utilisateur de test (service org.kde.kglobalaccel), et par UNE SEULE action : si deux actions se disputent une touche, KDE
# n'en sert qu'une (MANQUE = aucune ; CONFLIT = plusieurs). On écrit aussi dans le journal tout ce que KDE a enregistré
# (composant / action), pour corriger la liste sans deviner si un raccourci de KDE change d'une version à l'autre.
check_raccourcis() {
    section "Raccourcis clavier (enregistrés par KDE dans la session)"
    local uid out code outil=/usr/libexec/binixx/binixx-raccourcis
    uid="$(id -u "${TEST_USER}")"
    session() { runuser -u "${TEST_USER}" -- env XDG_RUNTIME_DIR="/run/user/${uid}" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" "$@"; }
    if ! wait_for 120 session busctl --user status org.kde.plasmashell; then
        fail "Plasma ne répond pas sur le bus de la session : les raccourcis ne peuvent pas être vérifiés"
        return
    fi
    # KDE enregistre les raccourcis au fil du démarrage de la session : on attend qu'ils soient tous là
    if wait_for 120 session "${outil}" verifier; then
        pass "KDE répond, tous les raccourcis annoncés sont enregistrés et chacun par une seule action"
    else
        fail "au moins un raccourci annoncé n'est pas enregistré par KDE, ou est pris par plusieurs actions"
    fi
    out="$(session "${outil}" verifier 2>&1)" && code=0 || code=$?
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
    while IFS= read -r ligne; do
        if [[ "${ligne}" == MANQUE* || "${ligne}" == CONFLIT* ]]; then fail "${ligne}"; fi
    done <<<"${out}"
    if [[ "${code}" -ne 0 ]] && ! grep -q '^\(MANQUE\|CONFLIT\)' <<<"${out}"; then
        # le registre est illisible : on garde les réponses brutes de KDE pour comprendre pourquoi
        fail "lecture du registre des raccourcis impossible : ${out:0:300}"
        session busctl --user --json=short call org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel allComponents 2>&1 | head -c 1500 | sed 's/^/            brut : /'
        session busctl --user --json=short call org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component allShortcutInfos 2>&1 | head -c 1500 | sed 's/^/            brut : /'
    fi
    echo "  -- tout ce que KDE a enregistré dans la session (composant / action) :"
    session "${outil}" registre 2>&1 | sed 's/^/            /' | head -400
}
register_check base check_raccourcis
