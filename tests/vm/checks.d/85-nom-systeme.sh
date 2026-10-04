# shellcheck shell=bash
# Nom du système vu par l'installeur : sur le système installé (pas seulement dans l'image), puis après une mise à jour.
# Anaconda nomme un système déjà installé d'après /etc/redhat-release ; le fichier doit survivre au déploiement ostree
# (/etc est fusionné) : avant la correction, on lisait « Fedora Linux 44 pour x86_64 » dans l'écran de partitionnement.
check_nom_systeme() {
    section "Nom du système vu par l'installeur"
    check "/etc/redhat-release est un fichier BinixX OS" bash -c '[[ ! -L /etc/redhat-release ]] && grep -q "^BinixX OS release " /etc/redhat-release'
    check "le nom que donnerait l'installeur contient BinixX OS et pas Fedora" python3 -c \
'
produit, sep, version = open("/etc/redhat-release").readline().strip().partition(" release ")
assert sep, "pas de « release » dans /etc/redhat-release"
modele = "{p} {v} for {a}" if "linux" in produit.lower() else "{p} Linux {v} for {a}"
nom = modele.format(p=produit, v=version.split()[0], a="x86_64")
print(nom)
assert "BinixX OS" in nom and "Fedora" not in nom, nom
'
}
register_check base check_nom_systeme
register_check after-update check_nom_systeme
