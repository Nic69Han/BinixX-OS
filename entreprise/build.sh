#!/usr/bin/bash
# Personnalisation de l'entreprise, exécutée une seule fois pendant `podman build` (voir Containerfile).
# Le contexte de build est monté sur /ctx. Les réglages sont dans entreprise.conf.

set -ouex pipefail

# shellcheck source=/dev/null  # entreprise.conf est monté sur /ctx pendant le build
. /ctx/entreprise.conf

### 1. Fichiers de l'entreprise
cp -avf /ctx/system_files/. /

### 2. Logiciels
if [[ ${#PAQUETS[@]} -gt 0 ]]; then
    dnf5 -y install "${PAQUETS[@]}"
fi
# Applications Flatpak : ajoutées à celles de NicOS (liste complémentaire lue au premier démarrage)
install -Dm0644 /ctx/flatpaks/entreprise.list /usr/share/nicos/flatpaks/system-flatpaks.d/entreprise.list

### 3. Identité : NicOS reste le système, l'entreprise est la « variante » (os-release)
sed -i -e '/^VARIANT=/d' -e '/^VARIANT_ID=/d' /usr/lib/os-release
variant_id="$(tr '[:upper:]' '[:lower:]' <<<"${NOM_ENTREPRISE}" | tr -cs 'a-z0-9' '-' | sed 's/^-*//; s/-*$//')"
{
    printf 'VARIANT="%s"\n' "${NOM_ENTREPRISE//\"/}"
    printf 'VARIANT_ID=%s\n' "${variant_id:-entreprise}"
} >>/usr/lib/os-release

# Mémo pour le support : /etc/nicos/entreprise.conf (lisible par tous, aucun secret)
install -d /etc/nicos
{
    printf 'NOM_ENTREPRISE="%s"\n' "${NOM_ENTREPRISE//\"/}"
    printf 'DOMAINE_AD="%s"\n' "${DOMAINE_AD}"
} >/etc/nicos/entreprise.conf

### 4. Firefox : page d'accueil et proxy imposés (politiques d'entreprise de Firefox)
POLICIES=/etc/firefox/policies/policies.json
PAGE_ACCUEIL="${PAGE_ACCUEIL}" PROXY="${PROXY}" POLICIES="${POLICIES}" python3 - <<'PYEOF'
import json, os

path = os.environ["POLICIES"]
data = json.load(open(path))
policies = data["policies"]
if os.environ["PAGE_ACCUEIL"]:
    policies["Homepage"] = {"URL": os.environ["PAGE_ACCUEIL"], "StartPage": "homepage"}
if os.environ["PROXY"]:
    policies["Proxy"] = {
        "Mode": "manual",
        "HTTPProxy": os.environ["PROXY"],
        "UseHTTPProxyForAllProtocols": True,
    }
with open(path, "w") as out:
    json.dump(data, out, indent=2)
    out.write("\n")
PYEOF
