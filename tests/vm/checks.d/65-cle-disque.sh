# shellcheck shell=bash
# Un vrai volume LUKS2 (fichier monté en périphérique de boucle) : l'outil appelé par la page « Protéger mes
# données » crée une clé de récupération qui déverrouille réellement le volume, et la remplace sur demande.
# pkexec lui-même (fenêtre d'authentification) ne se teste pas sans écran ; ici on lance l'outil en root, comme pkexec.
check_cle_disque() {
    section "Clé de récupération du disque chiffré"
    local outil=/usr/libexec/binixx/binixx-cle-recuperation
    local image=/var/tmp/binixx-test-luks.img mdp='mot de passe de test' disque out code cle nouvelle
    check "action polkit connue de polkitd" pkaction --action-id org.binixx.cle-recuperation
    rm -f "${image}"
    truncate -s 64M "${image}"
    if ! printf '%s' "${mdp}" | cryptsetup luksFormat --batch-mode --type luks2 --pbkdf pbkdf2 --pbkdf-force-iterations 1000 --key-file=- "${image}"; then
        fail "volume LUKS2 de test non créé"
        rm -f "${image}"
        return
    fi
    disque="$(losetup --show -f "${image}")"
    udevadm settle --timeout=30 || true
    # shellcheck disable=SC2064  # ${disque} est évalué ici exactement pour le nettoyage
    trap "losetup -d '${disque}' 2>/dev/null; rm -f '${image}'; trap - RETURN" RETURN

    if wait_for 60 bash -c "lsblk -J -p -o PATH,FSTYPE '${disque}' | grep -q crypto_LUKS"; then
        pass "le volume chiffré est reconnu par lsblk (${disque})"
    else
        fail "le volume chiffré n'est pas reconnu comme crypto_LUKS (${disque})"
        return
    fi
    out="$(runuser -u "${TEST_USER}" -- "${outil}" volumes 2>&1)"
    if grep -q "\"${disque}\"" <<<"${out}"; then pass "la liste des volumes (sans droits) contient le volume de test"; else fail "volume absent de la liste : ${out}"; fi

    printf '%s\n' "mauvais" | "${outil}" creer "${disque}" >/dev/null 2>&1
    code=$?
    if [[ ${code} -eq 4 ]]; then pass "mauvais mot de passe refusé (code 4)"; else fail "mauvais mot de passe : code ${code} au lieu de 4"; fi

    out="$(printf '%s\n' "${mdp}" | "${outil}" creer "${disque}" 2>&1)"
    cle="$(sed -n 's/^CLE=//p' <<<"${out}")"
    if [[ -n "${cle}" ]]; then pass "clé de récupération créée"; else
        fail "clé non créée : ${out}"
        return
    fi
    if printf '%s' "${cle}" | cryptsetup open --test-passphrase --key-file=- "${disque}"; then
        pass "la clé de récupération déverrouille le volume"
    else
        fail "la clé de récupération ne déverrouille pas le volume"
    fi
    if printf '%s' "${mdp}" | cryptsetup open --test-passphrase --key-file=- "${disque}"; then
        pass "le mot de passe d'origine fonctionne toujours"
    else
        fail "le mot de passe d'origine ne fonctionne plus"
    fi

    printf '%s\n' "${mdp}" | "${outil}" creer "${disque}" >/dev/null 2>&1
    code=$?
    if [[ ${code} -eq 3 ]]; then pass "seconde demande : refusée sans « remplacer » (code 3)"; else fail "seconde demande : code ${code} au lieu de 3"; fi

    nouvelle="$(printf '%s\n' "${mdp}" | "${outil}" creer "${disque}" --remplacer 2>/dev/null | sed -n 's/^CLE=//p')"
    if [[ -n "${nouvelle}" && "${nouvelle}" != "${cle}" ]]; then pass "clé remplacée"; else
        fail "clé non remplacée"
        return
    fi
    if printf '%s' "${nouvelle}" | cryptsetup open --test-passphrase --key-file=- "${disque}"; then pass "la nouvelle clé fonctionne"; else fail "la nouvelle clé ne fonctionne pas"; fi
    if printf '%s' "${cle}" | cryptsetup open --test-passphrase --key-file=- "${disque}" 2>/dev/null; then
        fail "l'ancienne clé fonctionne encore"
    else
        pass "l'ancienne clé ne fonctionne plus"
    fi
    out="$(systemd-cryptenroll "${disque}" </dev/null 2>&1 | grep -c recovery)"
    if [[ "${out}" == 1 ]]; then pass "une seule clé de récupération enregistrée"; else fail "${out} clés de récupération enregistrées"; fi

    out="$("${outil}" creer /etc/hostname <<<"${mdp}" 2>&1)"
    code=$?
    if [[ ${code} -eq 2 ]]; then pass "un fichier qui n'est pas un volume chiffré est refusé (code 2)"; else fail "fichier quelconque : code ${code} au lieu de 2"; fi
}
register_check base check_cle_disque
