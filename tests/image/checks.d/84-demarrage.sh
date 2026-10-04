# shellcheck shell=bash
section "Démarrage graphique (écran de démarrage, paramètres du noyau)"
kargs=/usr/lib/bootc/kargs.d/10-binixx-demarrage.toml
check "paramètres de démarrage silencieux fournis à bootc (kargs.d)" test -s "${kargs}"
check "le fichier est du TOML valide : une liste « kargs » de textes" python3 -c '
import sys, tomllib
d = tomllib.load(open(sys.argv[1], "rb"))
assert d["kargs"] and all(isinstance(k, str) and k and " " not in k for k in d["kargs"]), d
' "${kargs}"
# quiet ET splash : sans l'un des deux, Plymouth retombe sur le thème « details », qui n'est que du texte
for karg in quiet splash rhgb loglevel=3 systemd.show_status=auto rd.systemd.show_status=auto; do
    check "paramètre du noyau : ${karg}" grep -qF "\"${karg}\"" "${kargs}"
done
# shellcheck disable=SC2016  # le $1 est celui du bash -c
check "aucun paramètre ne coupe l'écran de démarrage (plymouth.enable=0, rd.plymouth=0, nosplash)" \
    bash -c '! grep -qE "plymouth\.enable=0|rd\.plymouth=0|nosplash" "$1"' _ "${kargs}"
check "le thème BinixX OS utilise le module two-step" grep -qx 'ModuleName=two-step' /usr/share/plymouth/themes/binixx/binixx.plymouth
check "module two-step présent dans l'initramfs (sinon pas d'animation)" \
    bash -c 'lsinitrd /usr/lib/modules/*/initramfs.img | grep -q "plymouth/two-step.so"'
check "Plymouth n'est pas masqué" bash -c '! systemctl is-enabled plymouth-start.service 2>&1 | grep -q masked'
# La roue de chargement : sans elle (ou avec une animation à trous), on croit l'ordinateur figé. Images à nous (branding/roue_demarrage.py),
# numérotées sans trou de 0001 à NNNN, toutes de la même taille, aucune image de la roue de Fedora en plus.
check "la roue de chargement : au moins 12 images PNG de même taille, numérotées sans trou à partir de 0001" python3 -c '
import glob, os, struct, sys
dossier = sys.argv[1]
noms = sorted(os.path.basename(f) for f in glob.glob(dossier + "/throbber-*.png"))
attendus = ["throbber-%04d.png" % (i + 1) for i in range(len(noms))]
assert len(noms) >= 12 and noms == attendus, noms
tailles = set()
for nom in noms:
    entete = open(os.path.join(dossier, nom), "rb").read(24)
    assert entete[:8] == b"\x89PNG\r\n\x1a\n" and entete[12:16] == b"IHDR", nom
    tailles.add(struct.unpack(">II", entete[16:24]))
assert len(tailles) == 1, tailles
' /usr/share/plymouth/themes/binixx

section "Menu de démarrage discret (GRUB)"
check "script du menu GRUB discret exécutable" test -x /usr/libexec/binixx/binixx-menu-grub
check "service du menu GRUB discret activé" systemctl is-enabled binixx-menu-grub.service
menu_dir="$(mktemp -d)"
BINIXX_GRUB_DIR="${menu_dir}" /usr/libexec/binixx/binixx-menu-grub >/dev/null
# shellcheck disable=SC2016  # le $1 est celui du bash -c
check "le script écrit un user.cfg qui cache le menu après un démarrage réussi" bash -c \
    'grep -q "timeout_style=hidden" "$1/user.cfg" && grep -q "boot_success" "$1/user.cfg"' _ "${menu_dir}"
if command -v grub2-script-check >/dev/null; then
    check "user.cfg : syntaxe GRUB valide" grub2-script-check "${menu_dir}/user.cfg"
fi
rm -rf "${menu_dir}"
