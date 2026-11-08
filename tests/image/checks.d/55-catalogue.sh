# shellcheck shell=bash
section "Mon logiciel Windows (catalogue)"
CATALOGUE=/usr/share/binixx/catalogue-windows/catalogue.tsv
check "catalogue fourni" test -s "${CATALOGUE}"
check "lanceur « Mon logiciel Windows » valide" desktop-file-validate /usr/share/applications/binixx-catalogue-windows.desktop
check "lanceur des programmes Windows valide" desktop-file-validate /usr/share/applications/binixx-windows-program.desktop
for mime in application/vnd.microsoft.portable-executable application/x-ms-dos-executable application/x-msdownload application/x-msi; do
    check "${mime} : ouvert par l'aiguillage de BinixX OS" grep -qx "${mime}=binixx-windows-program.desktop" /etc/xdg/kde-mimeapps.list
done
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_CATALOGUE="${CATALOGUE}" python3 -m unittest discover -s /tests/centre -p 'test_catalogue.py' 2>&1)"; then
    pass "catalogue : tests de recherche et de lecture (${out##*$'\n'})"
else
    fail "catalogue : tests de recherche et de lecture"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
# Chaque logiciel « inclus » du catalogue doit avoir son lanceur dans l'image
missing="$(
    python3 - "${CATALOGUE}" <<'PYEOF'
import os, sys
for ligne in open(sys.argv[1], encoding="utf-8"):
    if ligne.startswith("#") or not ligne.strip():
        continue
    champs = ligne.rstrip("\n").split("\t")
    if champs[3] == "inclus" and not os.path.exists(f"/usr/share/applications/{champs[4]}.desktop"):
        print(f"{champs[0]} ({champs[4]})", end=" ")
PYEOF
)"
if [[ -z "${missing}" ]]; then pass "catalogue : tous les logiciels « inclus » ont leur lanceur"; else fail "catalogue : lanceur absent pour ${missing}"; fi
# Les applications annoncées « fournies » par le catalogue sont bien dans la liste Flatpak
for app in org.onlyoffice.desktopeditors org.mozilla.thunderbird_esr org.kde.okular; do
    check "catalogue : ${app} dans la liste Flatpak et dans le catalogue" \
        bash -c "grep -qx '${app}' /usr/share/binixx/flatpaks/system-flatpaks.list && grep -qP '\tflatpak\t${app}\t' '${CATALOGUE}'"
done

section "Aiguillage des programmes Windows (équivalent, Wine, Windows)"
check "binixx-ouvrir-windows exécutable" test -x /usr/libexec/binixx/binixx-ouvrir-windows
check "double-clic sur un .exe : l'aiguillage" grep -qx 'Exec=/usr/libexec/binixx/binixx-ouvrir-windows %f' /usr/share/applications/binixx-windows-program.desktop
check "menu « Programme Windows » du clic droit : .exe et .msi, Wine, Windows, choix" bash -c \
    "m=/usr/share/kio/servicemenus/binixx-ouvrir-windows.desktop; grep -q 'portable-executable' \${m} && grep -q 'x-msi' \${m} && grep -q 'binixx-ouvrir-windows --moteur wine %f' \${m} && grep -q 'binixx-ouvrir-windows --moteur windows %f' \${m} && grep -q 'binixx-ouvrir-windows --choisir %f' \${m}"
check "menu « Programme Windows » exécutable (exigé par Dolphin)" test -x /usr/share/kio/servicemenus/binixx-ouvrir-windows.desktop
check "double-clic sur un exécutable : pas de boîte « Exécuter ? » de KDE avant l'aiguillage" grep -qx 'behaviourOnLaunch=open' /etc/xdg/kiorc
check "liste des programmes qui demandent Windows fournie" test -s /usr/share/binixx/catalogue-windows/windows-requis.tsv
if out="$(BINIXX_CENTRE=/usr/lib/binixx/centre BINIXX_CATALOGUE="${CATALOGUE}" BINIXX_WINDOWS_REQUIS=/usr/share/binixx/catalogue-windows/windows-requis.tsv QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s /tests/centre -p 'test_moteurs.py' 2>&1)"; then
    pass "aiguillage : conseil, choix retenu, commandes Bottles, fenêtre (${out##*$'\n'})"
else
    fail "aiguillage : tests"
    # shellcheck disable=SC2001  # indentation de chaque ligne du rapport
    sed 's/^/            /' <<<"${out}"
fi
for cas in "WordSetup.exe:equivalent" "Setup_Zorglub_Pro.exe:wine" "SolidWorks2025.msi:windows"; do
    out="$(XDG_CONFIG_HOME="$(mktemp -d)" /usr/libexec/binixx/binixx-ouvrir-windows --json "/tmp/${cas%%:*}" 2>&1)" || true
    if grep -q "\"moteur\": \"${cas##*:}\"" <<<"${out}"; then pass "aiguillage : ${cas%%:*} → ${cas##*:}"; else fail "aiguillage : ${cas%%:*} : ${out:0:300}"; fi
done
