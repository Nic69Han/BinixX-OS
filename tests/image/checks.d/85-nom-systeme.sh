# shellcheck shell=bash
section "Nom du système vu par l'installeur (réinstallation sur un disque qui contient déjà BinixX OS)"
# Anaconda (pyanaconda/modules/storage/devicetree/root.py) nomme un système déjà installé d'après /etc/redhat-release (avant os-release),
# puis ajoute « Linux » au nom s'il ne le contient pas. On reproduit son calcul : « Fedora Linux 44 pour x86_64 » ne doit plus apparaître.
check "/etc/redhat-release est un fichier BinixX OS, pas un lien vers fedora-release" \
    bash -c '[[ ! -L /etc/redhat-release ]] && grep -q "^BinixX OS release " /etc/redhat-release'
check "le nom que donnerait l'installeur contient BinixX OS et pas Fedora" python3 -c \
'
import sys
version_id = [l.split("=", 1)[1].strip().strip(chr(34)) for l in open("/usr/lib/os-release") if l.startswith("VERSION_ID=")][0]
produit, sep, version = open("/etc/redhat-release").readline().strip().partition(" release ")
assert sep, "pas de « release » dans /etc/redhat-release"
version = version.split()[0]
modele = "{p} {v} for {a}" if "linux" in produit.lower() else "{p} Linux {v} for {a}"
nom = modele.format(p=produit, v=version, a="x86_64")
print(nom)
assert "BinixX OS" in nom and "Fedora" not in nom, nom
assert version == version_id, (version, version_id)
'
