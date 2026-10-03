# shellcheck shell=bash
section "Image d'entreprise (gabarit)"
TEMPLATE=/usr/share/binixx/entreprise-template
for file in Containerfile entreprise.conf build.sh flatpaks/entreprise.list github-actions.yml.modele iso.toml.modele; do
    check "gabarit : ${file} fourni" test -s "${TEMPLATE}/${file}"
done
check "gabarit : build.sh exécutable" test -x "${TEMPLATE}/build.sh"
check "installation Flatpak : listes complémentaires (system-flatpaks.d) prises en compte" \
    grep -q 'system-flatpaks.d' /usr/libexec/binixx/binixx-flatpak-install
