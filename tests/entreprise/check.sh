#!/usr/bin/bash
# Vérifie, depuis l'intérieur d'un conteneur, qu'une image d'entreprise construite avec entreprise/
# (réglages d'exemple de entreprise.conf) est complète. Lancé par `just test-entreprise`.

set -uo pipefail

failures=0
pass() { printf '  ok      %s\n' "$*"; }
fail() {
    printf '  ÉCHEC   %s\n' "$*"
    failures=$((failures + 1))
}
check() { # check "description" commande...
    local desc="$1"
    shift
    if "$@" >/dev/null 2>&1; then pass "${desc}"; else fail "${desc}"; fi
}
section() { printf '\n== %s\n' "$*"; }

section "Image d'entreprise (exemple)"
# shellcheck source=/dev/null  # fichier de l'image, absent du dépôt
. /usr/lib/os-release
if [[ "${NAME}" == "BinixX OS" && "${VARIANT}" == "Exemple SARL" && "${VARIANT_ID}" == exemple-sarl ]]; then
    pass "os-release : BinixX OS, variante « ${VARIANT} » (${VARIANT_ID})"
else
    fail "os-release : NAME='${NAME}' VARIANT='${VARIANT:-}' VARIANT_ID='${VARIANT_ID:-}'"
fi
check "mémo pour le support (/etc/binixx/entreprise.conf)" grep -qx 'NOM_ENTREPRISE="Exemple SARL"' /etc/binixx/entreprise.conf
check "logiciel de l'entreprise installé (paquet)" rpm -q htop
check "applications Flatpak de l'entreprise listées" grep -qx 'org.keepassxc.KeePassXC' /usr/share/binixx/flatpaks/system-flatpaks.d/entreprise.list
check "applications Flatpak de BinixX OS conservées" test -s /usr/share/binixx/flatpaks/system-flatpaks.list
check "Firefox : page d'accueil de l'entreprise" python3 -c '
import json
p = json.load(open("/etc/firefox/policies/policies.json"))["policies"]
assert p["Homepage"]["URL"] == "https://intranet.exemple.fr"
'
check "Firefox : réglages de BinixX OS conservés (HTTPS, uBlock Origin)" python3 -c '
import json
p = json.load(open("/etc/firefox/policies/policies.json"))["policies"]
assert p["HttpsOnlyMode"] == "enabled" and "uBlock0@raymondhill.net" in p["ExtensionSettings"]
assert "Proxy" not in p  # PROXY est vide dans l exemple
'
check "fichiers de l'entreprise copiés (system_files)" test -f /etc/binixx/README
check "identité BinixX OS conservée (logo)" test -s /usr/share/icons/hicolor/scalable/apps/binixx.svg

printf '\n'
if [[ ${failures} -gt 0 ]]; then
    printf '%d vérification(s) en échec.\n' "${failures}"
    exit 1
fi
printf "Toutes les vérifications de l'image d'entreprise sont passées.\n"
