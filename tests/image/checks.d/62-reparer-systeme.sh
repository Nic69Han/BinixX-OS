# shellcheck shell=bash
section "Réparer le système"
check "outil de réparation exécutable" test -x /usr/libexec/binixx/binixx-reparer-systeme
check "pkexec présent" command -v pkexec
check "action polkit valide et liée à l'outil" python3 - <<'PYEOF'
import os
from xml.dom import minidom
doc = minidom.parse("/usr/share/polkit-1/actions/org.binixx.reparer-systeme.policy")
action = doc.getElementsByTagName("action")[0]
assert action.getAttribute("id") == "org.binixx.reparer-systeme"
chemins = [a.firstChild.data if a.firstChild else a.getAttribute("value") for a in action.getElementsByTagName("annotate")
           if a.getAttribute("key") == "org.freedesktop.policykit.exec.path"]
assert chemins == ["/usr/libexec/binixx/binixx-reparer-systeme"], chemins
assert os.access(chemins[0], os.X_OK)
droits = {n.tagName: n.firstChild.data for n in action.getElementsByTagName("defaults")[0].childNodes if n.nodeType == 1}
assert droits == {"allow_any": "no", "allow_inactive": "no", "allow_active": "auth_admin"}, droits
PYEOF
# Les dossiers pris en charge par l'outil existent bien dans l'image : un nom mal écrit passerait inaperçu
check "dossiers de réglages pris en charge : connus de l'outil et présents dans l'image" python3 - <<'PYEOF'
import importlib.machinery, importlib.util, os
chargeur = importlib.machinery.SourceFileLoader("r", "/usr/libexec/binixx/binixx-reparer-systeme")
module = importlib.util.module_from_spec(importlib.util.spec_from_loader("r", chargeur))
chargeur.exec_module(module)
# Dossiers que l'image de base fournit toujours (sddm.conf.d n'en fait pas partie : on le crée au besoin)
for prefixe in ("xdg/", "profile.d/", "sysctl.d/", "systemd/"):
    assert os.path.isdir("/etc/" + prefixe.rstrip("/")), prefixe
for prefixe in ("sddm.conf.d/", "xdg/", "profile.d/", "sysctl.d/", "systemd/"):
    assert module.categorie(prefixe + "x") is not None, prefixe
assert module.categorie("passwd") is None and module.categorie("ssh/sshd_config") is None
PYEOF
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_LIBEXEC=/usr/libexec/binixx QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_reparer.py' 2>&1)"; then
    pass "réparation : tests de la comparaison, de la remise à l'origine, de l'annulation et de la page (${out##*$'\n'})"
else
    fail "réparation : tests de la comparaison, de la remise à l'origine, de l'annulation et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
