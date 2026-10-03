# shellcheck shell=bash
section "Barre des tâches (en haut ou en bas)"
check "outil binixx-barre exécutable" test -x /usr/libexec/binixx/binixx-barre
# Hors session de bureau (build), l'outil doit répondre par une erreur claire, jamais par une trace d'erreur Python
out="$(/usr/libexec/binixx/binixx-barre bas 2>&1 || true)"
if grep -q "le bureau ne répond pas" <<<"${out}" && ! grep -q Traceback <<<"${out}"; then
    pass "sans session de bureau : message clair, pas de plantage"
else
    fail "binixx-barre bas sans session : ${out:0:200}"
fi
check "une position inconnue est refusée" bash -c '! /usr/libexec/binixx/binixx-barre gauche >/dev/null 2>&1'
# La page « Barre des tâches » est construite avec les autres (centre --test) et ouverte depuis Paramètres
check "la ligne Barre des tâches de Paramètres ouvre la page « barre »" bash -c \
    "awk -F'\t' '\$2==\"Barre des tâches\" && \$6==\"page\" && \$7==\"barre\" {found=1} END {exit !found}' /usr/share/binixx/parametres/parametres.tsv"
check "le mode du thème place la barre en haut au départ" grep -q 'panel.location = "top"' \
    /usr/share/plasma/look-and-feel/org.binixx.desktop/contents/layouts/org.kde.plasma.desktop-layout.js
