# shellcheck shell=bash
section "Clé de récupération du disque chiffré"
check "lanceur « Protéger mes données » valide" desktop-file-validate /usr/share/applications/binixx-securite.desktop
check "outil de la clé de récupération exécutable" test -x /usr/libexec/binixx/binixx-cle-recuperation
check "systemd-cryptenroll présent" command -v systemd-cryptenroll
check "cryptsetup présent" command -v cryptsetup
check "pkexec présent" command -v pkexec
check "action polkit valide et liée à l'outil" python3 - <<'PYEOF'
import os, sys
from xml.dom import minidom
doc = minidom.parse("/usr/share/polkit-1/actions/org.binixx.cle-recuperation.policy")
action = doc.getElementsByTagName("action")[0]
assert action.getAttribute("id") == "org.binixx.cle-recuperation"
chemins = [a.getAttribute("org.freedesktop.policykit.exec.path") or a.firstChild.data
           for a in action.getElementsByTagName("annotate")
           if a.getAttribute("key") == "org.freedesktop.policykit.exec.path"]
assert chemins == ["/usr/libexec/binixx/binixx-cle-recuperation"], chemins
assert os.access(chemins[0], os.X_OK)
droits = {n.tagName: n.firstChild.data for n in action.getElementsByTagName("defaults")[0].childNodes if n.nodeType == 1}
assert droits == {"allow_any": "no", "allow_inactive": "no", "allow_active": "auth_admin"}, droits
PYEOF
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_LIBEXEC=/usr/libexec/binixx QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_cle.py' 2>&1)"; then
    pass "clé de récupération : tests de l'outil et de la page (${out##*$'\n'})"
else
    fail "clé de récupération : tests de l'outil et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
