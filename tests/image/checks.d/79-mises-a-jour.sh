# shellcheck shell=bash
section "Mises à jour (page « Mises à jour »)"
check "outil binixx-mises-a-jour exécutable" test -x /usr/libexec/binixx/binixx-mises-a-jour
check "pkexec présent" command -v pkexec
check "rpm-ostree présent (lecture de l'état)" command -v rpm-ostree
check "bootc présent (installer, revenir en arrière)" command -v bootc
check "skopeo présent (y a-t-il une nouvelle version ?)" command -v skopeo
check "action polkit valide et liée à l'outil" python3 - <<'PYEOF'
import os
from xml.dom import minidom
doc = minidom.parse("/usr/share/polkit-1/actions/org.binixx.mises-a-jour.policy")
action = doc.getElementsByTagName("action")[0]
assert action.getAttribute("id") == "org.binixx.mises-a-jour"
chemins = [a.firstChild.data if a.firstChild else a.getAttribute("value") for a in action.getElementsByTagName("annotate")
           if a.getAttribute("key") == "org.freedesktop.policykit.exec.path"]
assert chemins == ["/usr/libexec/binixx/binixx-mises-a-jour"], chemins
assert os.access(chemins[0], os.X_OK)
droits = {n.tagName: n.firstChild.data for n in action.getElementsByTagName("defaults")[0].childNodes if n.nodeType == 1}
assert droits == {"allow_any": "no", "allow_inactive": "no", "allow_active": "auth_admin"}, droits
PYEOF
# Hors d'un système démarré depuis une image (build), l'outil répond par un message clair, jamais par une trace Python
out="$(/usr/libexec/binixx/binixx-mises-a-jour etat 2>&1 || true)"
if grep -q "Impossible de lire l'état du système" <<<"${out}" && ! grep -q Traceback <<<"${out}"; then
    pass "hors d'un système bootc : message clair, pas de plantage"
else
    fail "binixx-mises-a-jour etat hors système bootc : ${out:0:200}"
fi
check "une action inconnue est refusée" bash -c '! /usr/libexec/binixx/binixx-mises-a-jour bidule >/dev/null 2>&1'
check "la ligne « Mises à jour du système » de Paramètres ouvre la page « mises_a_jour »" bash -c \
    "awk -F'\t' '\$2==\"Mises à jour du système\" && \$6==\"page\" && \$7==\"mises_a_jour\" {found=1} END {exit !found}' /usr/share/binixx/parametres/parametres.tsv"
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_misesajour.py' 2>&1)"; then
    pass "mises à jour : tests de la lecture de rpm-ostree, de la recherche, de la ligne de commande et de la page (${out##*$'\n'})"
else
    fail "mises à jour : tests de la lecture de rpm-ostree, de la recherche, de la ligne de commande et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
