# shellcheck shell=bash
section "Paramètres (écran unique des réglages)"
check "lanceur « Paramètres » valide" desktop-file-validate /usr/share/applications/nicos-parametres.desktop
check "touche Windows + I : raccourci fourni" grep -qx '_launch=Meta+I' /etc/xdg/kglobalshortcutsrc
check "« Paramètres » est dans les favoris du menu" grep -q 'nicos-parametres.desktop' /etc/xdg/kicker-extra-favoritesrc
check "kcmshell6 présent" command -v kcmshell6
# Les modules KDE cités par la page doivent exister dans l'image : la liste vient de kcmshell6 lui-même
# (un module renommé par une mise à jour de Plasma fait échouer le build, au lieu de laisser un bouton mort)
# kcmshell6 a besoin d'une plate-forme Qt : sans session graphique (build), on prend « offscreen ». S'il ne liste
# toujours rien, on se rabat sur les greffons de modules installés (un fichier ou un dossier kcm_xxx par module).
modules="$(QT_QPA_PLATFORM=offscreen kcmshell6 --list 2>&1 || true)"
source_modules="kcmshell6 --list"
if ! grep -q '^ *kcm_' <<<"${modules}"; then
    modules="$(find /usr/lib64/qt6/plugins /usr/share/kpackage/kcms -maxdepth 5 -name 'kcm_*' -printf '%f\n' 2>/dev/null |
        sed 's/\.so$//' | sort -u || true)"
    source_modules="greffons installés"
fi
if grep -q '^ *kcm_' <<<"${modules}"; then
    pass "$(grep -c '^ *kcm_' <<<"${modules}") modules KDE (${source_modules})"
    # Sortie complète du build, pour ajuster les identifiants si Plasma change
    printf '%s\n' "${modules}" | sed 's/^/            /' | head -150
    missing="$(
        python3 - "${modules}" <<'PYEOF'
import re, sys
disponibles = {m.split()[0] for m in sys.argv[1].splitlines() if m.strip() and re.match(r"^kcm_", m.strip())}
manquants = []
for ligne in open("/usr/share/nicos/parametres/parametres.tsv", encoding="utf-8"):
    champs = ligne.rstrip("\n").split("\t")
    if not ligne.startswith("#") and len(champs) >= 6 and champs[4] == "kcm" and champs[5] not in disponibles:
        manquants.append(f"{champs[1]} ({champs[5]})")
print(", ".join(manquants))
PYEOF
    )"
    if [[ -z "${missing}" ]]; then pass "tous les modules KDE cités par la page Paramètres existent"; else fail "modules KDE absents : ${missing}"; fi
else
    fail "aucun module KDE trouvé (kcmshell6 --list : ${modules:-rien})"
fi
# Les lanceurs cités existent dans l'image
missing="$(
    python3 - <<'PYEOF'
import os
manquants = []
for ligne in open("/usr/share/nicos/parametres/parametres.tsv", encoding="utf-8"):
    champs = ligne.rstrip("\n").split("\t")
    if not ligne.startswith("#") and len(champs) >= 6 and champs[4] == "app" and not os.path.exists(f"/usr/share/applications/{champs[5]}.desktop"):
        manquants.append(champs[5])
print(" ".join(manquants))
PYEOF
)"
if [[ -z "${missing}" ]]; then pass "tous les lanceurs cités par la page Paramètres existent"; else fail "lanceurs absents : ${missing}"; fi
if out="$(NICOS_CENTRE=/usr/lib/nicos/centre NICOS_PARAMETRES=/usr/share/nicos/parametres/parametres.tsv NICOS_LANCEURS=/usr/share/applications NICOS_CATALOGUE=/usr/share/nicos/catalogue-windows/catalogue.tsv NICOS_FLATPAKS=/usr/share/nicos/flatpaks/system-flatpaks.list QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_parametres.py' 2>&1)"; then
    pass "paramètres : tests du fichier, de la recherche et de la page (${out##*$'\n'})"
else
    fail "paramètres : tests du fichier, de la recherche et de la page"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
