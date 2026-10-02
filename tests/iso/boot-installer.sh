#!/usr/bin/bash
# Démarre l'ISO d'installation publique dans une VM KVM, comme sur un vrai PC : firmware UEFI
# avec Secure Boot (clés Microsoft), puis shim, GRUB et l'installeur graphique de l'ISO.
# N'installe rien. Vérifie que l'installeur graphique démarre depuis le volume « NicOS-… », avec
# l'écran de choix de la langue et le logo NicOS (disk_config/personnaliser-iso.sh), et en fait une
# capture d'écran.
# Second démarrage, la langue demandée au lancement (inst.lang, français par défaut) : vérifie que
# l'installeur s'affiche dans cette langue et en fait une capture.
#
# Usage : tests/iso/boot-installer.sh <ISO> [--workdir DIR] [--no-secure-boot]
#                                           [--langue LOCALE | --sans-langue]
#
# L'installeur ouvre un shell root sur la console virtio hvc0 (anaconda-generator) : le script
# s'en sert pour lire son état (mode d'affichage, Secure Boot, langue, logo, nom du produit).
# Prérequis (hôte x86_64) : /dev/kvm, qemu-system-x86_64, qemu-img, OVMF (edk2), python3, xorriso.
# Résultats dans <workdir>/logs/ : installeur.png et .txt, installeur-<langue>.png et .txt,
# journaux série.
# Variables utiles : VM_CPUS, VM_RAM (Mio), INSTALLER_TIMEOUT (s), OVMF_CODE, OVMF_VARS,
# OVMF_VARS_SECURE_BOOT.

set -euo pipefail

ISO=""
WORK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_work"
SECURE_BOOT=1
LANGUE=fr_FR.UTF-8
while [[ $# -gt 0 ]]; do
    case "$1" in
    --workdir) WORK="$2" && shift 2 ;;
    --no-secure-boot) SECURE_BOOT=0 && shift ;;
    --langue) LANGUE="$2" && shift 2 ;;
    --sans-langue) LANGUE="" && shift ;;
    -h | --help) sed -n '2,21p' "${BASH_SOURCE[0]}" && exit 0 ;;
    -*) echo "Option inconnue : $1" >&2 && exit 2 ;;
    *) ISO="$1" && shift ;;
    esac
done
[[ -f "${ISO}" ]] || { echo "ISO introuvable : '${ISO}'" >&2 && exit 2; }
ISO="$(cd "$(dirname "${ISO}")" && pwd)/$(basename "${ISO}")"

mkdir -p "${WORK}"
WORK="$(cd "${WORK}" && pwd)"
LOGS="${WORK}/logs"
DISK="${WORK}/disque-vide.qcow2"
VARS="${WORK}/vars.fd"
QMP_SOCK="${WORK}/qmp.sock"
CONSOLE_SOCK="${WORK}/console.sock"
PIDFILE="${WORK}/qemu.pid"
VM_CPUS="${VM_CPUS:-4}"
VM_RAM="${VM_RAM:-4096}"
INSTALLER_TIMEOUT="${INSTALLER_TIMEOUT:-900}"
# Marque de l'installeur attendue sur l'ISO (branding/generer.py)
BRANDING="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/branding/installeur"

log() { printf '\n\033[1m[%(%H:%M:%S)T] %s\033[0m\n' -1 "$*"; }
die() {
    printf '\n\033[1;31mÉCHEC : %s\033[0m\n' "$*" >&2
    exit 1
}

for cmd in qemu-system-x86_64 qemu-img python3 xorriso; do
    command -v "${cmd}" >/dev/null || die "commande manquante : ${cmd}"
done
[[ -w /dev/kvm ]] || die "/dev/kvm indisponible : la virtualisation matérielle est nécessaire"

first_file() {
    local f
    for f in "$@"; do [[ -f "${f}" ]] && echo "${f}" && return 0; done
    return 1
}
# Chemins Ubuntu/Debian (paquet ovmf) puis Fedora (paquet edk2-ovmf)
OVMF_CODE="${OVMF_CODE:-$(first_file /usr/share/OVMF/OVMF_CODE_4M.secboot.fd /usr/share/edk2/ovmf/OVMF_CODE.secboot.fd || true)}"
OVMF_VARS="${OVMF_VARS:-$(first_file /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/edk2/ovmf/OVMF_VARS.fd || true)}"
OVMF_VARS_SECURE_BOOT="${OVMF_VARS_SECURE_BOOT:-$(first_file /usr/share/OVMF/OVMF_VARS_4M.ms.fd /usr/share/edk2/ovmf/OVMF_VARS.secboot.fd || true)}"
[[ -f "${OVMF_CODE}" && -f "${OVMF_VARS}" ]] || die "firmware OVMF introuvable (définir OVMF_CODE et OVMF_VARS)"
if [[ ${SECURE_BOOT} -eq 1 && ! -f "${OVMF_VARS_SECURE_BOOT}" ]]; then
    die "variables OVMF avec clés Secure Boot introuvables (OVMF_VARS_SECURE_BOOT) ; ou utiliser --no-secure-boot"
fi

rm -rf "${LOGS}" && mkdir -p "${LOGS}"

### Outils VM ------------------------------------------------------------------

vm_running() { [[ -f "${PIDFILE}" ]] && kill -0 "$(<"${PIDFILE}")" 2>/dev/null; }

qmp() { # qmp <commande> [arguments JSON]
    local arguments="${2:-}"
    [[ -n "${arguments}" ]] || arguments='{}'
    python3 - "${QMP_SOCK}" "$1" "${arguments}" <<'PYEOF'
import json, socket, sys

sock = socket.socket(socket.AF_UNIX)
sock.settimeout(60)
sock.connect(sys.argv[1])
stream = sock.makefile("rw")

def call(command, arguments=None):
    message = {"execute": command}
    if arguments:
        message["arguments"] = arguments
    stream.write(json.dumps(message) + "\n")
    stream.flush()
    while True:
        reply = json.loads(stream.readline())
        if "return" in reply or "error" in reply:
            return reply

json.loads(stream.readline())  # message d'accueil QMP
call("qmp_capabilities")
reply = call(sys.argv[2], json.loads(sys.argv[3]))
if "error" in reply:
    sys.exit(reply["error"].get("desc", "erreur QMP"))
PYEOF
}

screenshot() { # screenshot <nom> : capture de l'écran de la VM, sans jamais faire échouer le test
    vm_running || return 0
    if qmp screendump "{\"filename\": \"${LOGS}/$1.png\", \"format\": \"png\"}"; then
        echo "Capture d'écran : ${LOGS}/$1.png"
    else
        echo "Capture d'écran impossible" >&2
    fi
}

console() { # console <commande> : l'exécute dans le shell root de l'installeur (hvc0), affiche sa sortie
    python3 - "${CONSOLE_SOCK}" "$1" <<'PYEOF'
import socket, sys, time

sock = socket.socket(socket.AF_UNIX)
sock.settimeout(2)
sock.connect(sys.argv[1])
# Les guillemets coupent les marqueurs dans l'écho de la ligne tapée : seule la sortie
# de echo contient __NICOS_DEBUT__ et __NICOS_FIN__ en un seul morceau.
line = 'echo "__NICOS_""DEBUT__"; %s; echo "__NICOS_""FIN__"\n' % sys.argv[2]
sock.sendall(b"\n" + line.encode())
received = b""
deadline = time.time() + 30
while time.time() < deadline:
    try:
        chunk = sock.recv(65536)
    except socket.timeout:
        continue
    if not chunk:
        break
    received += chunk
    text = received.decode(errors="replace").replace("\r", "")
    if "__NICOS_DEBUT__\n" in text:
        output = text.split("__NICOS_DEBUT__\n", 1)[1]
        if "__NICOS_FIN__" in output:
            sys.stdout.write(output.split("__NICOS_FIN__", 1)[0])
            sys.exit(0)
sys.exit("pas de réponse du shell de l'installeur")
PYEOF
}

screen_colors() { # nombre de couleurs différentes à l'écran (0 si capture impossible)
    qmp screendump "{\"filename\": \"${WORK}/ecran.ppm\", \"format\": \"ppm\"}" >/dev/null 2>&1 || {
        echo 0
        return
    }
    python3 - "${WORK}/ecran.ppm" <<'PYEOF'
import re, sys

data = open(sys.argv[1], "rb").read()
header = re.match(rb"P6\s+(\d+)\s+(\d+)\s+(\d+)\s", data)
pixels = data[header.end():] if header else b""
print(len({pixels[i:i + 3] for i in range(0, len(pixels) - 2, 3)}))
PYEOF
}

cleanup() {
    local status=$?
    if vm_running; then
        [[ ${status} -ne 0 ]] && screenshot echec
        qmp quit >/dev/null 2>&1 || kill "$(<"${PIDFILE}")" 2>/dev/null || true
    fi
    rm -rf "${PIDFILE}" "${DISK}" "${WORK}/ecran.ppm" "${WORK}/iso-boot"
    # Résultats rendus à l'utilisateur qui a lancé sudo, le cas échéant
    if [[ -n "${SUDO_UID:-}" && -d "${LOGS}" ]]; then
        chown -R "${SUDO_UID}:${SUDO_GID:-${SUDO_UID}}" "${LOGS}" || true
    fi
    exit "${status}"
}
trap cleanup EXIT

### Démarrage de l'ISO ---------------------------------------------------------

start_vm() { # start_vm <journal série> [paramètres du noyau] : démarre l'ISO, disque vierge
    local serial="$1" append="${2:-}"
    local boot=(-drive "file=${ISO},if=none,id=cd0,media=cdrom,readonly=on" -device "ide-cd,drive=cd0,bootindex=0")
    if [[ -n "${append}" ]]; then
        # Noyau de l'ISO démarré directement, avec d'autres paramètres : sans Secure Boot, qui
        # ne vérifierait pas ce noyau (shim et GRUB sont testés par le démarrage normal)
        cp "${OVMF_VARS}" "${VARS}"
        boot+=(-kernel "${WORK}/iso-boot/vmlinuz" -initrd "${WORK}/iso-boot/initrd.img" -append "${append}")
    elif [[ ${SECURE_BOOT} -eq 1 ]]; then
        cp "${OVMF_VARS_SECURE_BOOT}" "${VARS}"
    else
        cp "${OVMF_VARS}" "${VARS}"
    fi
    # Disque vierge : l'installeur doit trouver une destination, comme sur un vrai PC
    rm -f "${DISK}" "${QMP_SOCK}" "${CONSOLE_SOCK}"
    qemu-img create -q -f qcow2 "${DISK}" 64G
    qemu-system-x86_64 \
        -name nicos-iso \
        -machine q35,accel=kvm,smm=on -global driver=cfi.pflash01,property=secure,value=on \
        -cpu host -smp "${VM_CPUS}" -m "${VM_RAM}" \
        -drive "if=pflash,format=raw,unit=0,file=${OVMF_CODE},readonly=on" \
        -drive "if=pflash,format=raw,unit=1,file=${VARS}" \
        -drive "file=${DISK},if=virtio,format=qcow2" \
        "${boot[@]}" \
        -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
        -device virtio-vga -device virtio-rng-pci \
        -device virtio-serial-pci \
        -chardev "socket,id=console0,path=${CONSOLE_SOCK},server=on,wait=off" -device virtconsole,chardev=console0 \
        -display none \
        -serial "file:${LOGS}/${serial}" \
        -qmp "unix:${QMP_SOCK},server=on,wait=off" \
        -daemonize -pidfile "${PIDFILE}"
}

stop_vm() {
    vm_running || return 0
    qmp quit >/dev/null 2>&1 || kill "$(<"${PIDFILE}")" 2>/dev/null || true
    local deadline=$((SECONDS + 30))
    while vm_running && [[ ${SECONDS} -lt ${deadline} ]]; do sleep 1; done
    rm -f "${PIDFILE}"
}

wait_installer() { # attend l'interface graphique de l'installeur, puis son affichage complet
    log "Attente de l'installeur (au plus ${INSTALLER_TIMEOUT} s)"
    local deadline=$((SECONDS + INSTALLER_TIMEOUT)) state=""
    until [[ "${state}" == *graphique* ]]; do
        vm_running || die "la VM s'est arrêtée (voir les journaux série dans ${LOGS})"
        if [[ ${SECONDS} -ge ${deadline} ]]; then
            die "installeur graphique non démarré après ${INSTALLER_TIMEOUT} s (dernier état : ${state:-aucune réponse du shell de l installeur})"
        fi
        sleep 10
        state="$(console 'grep -q "graphical mode" /tmp/anaconda.log 2>/dev/null && echo graphique; grep -qi "wayland startup failed" /tmp/anaconda.log 2>/dev/null && echo wayland-en-echec' 2>/dev/null || true)"
        [[ "${state}" == *wayland-en-echec* ]] && die "l'interface graphique de l'installeur n'a pas démarré (Wayland)"
    done

    # Écran noir ou console texte : quelques couleurs ; interface graphique : des centaines
    log "Installeur en mode graphique : attente de son affichage"
    local colors=0
    deadline=$((SECONDS + 300))
    while [[ ${colors} -lt 256 ]]; do
        [[ ${SECONDS} -lt ${deadline} ]] || die "l'écran reste vide ou en mode texte (${colors} couleurs)"
        sleep 10
        colors="$(screen_colors)"
    done
    sleep 20 # fin des animations d'ouverture
}

installer_report() { # état de l'installeur, lu par son shell root
    # Une seule ligne : l'écho des lignes suivantes se mêlerait sinon à la sortie.
    # L'installeur n'a pas pgrep : on compte les processus dans /proc ([b] évite de compter grep
    # lui-même). La langue est la dernière choisie par Anaconda (journal).
    # shellcheck disable=SC2016  # les $(…) s'évaluent dans l'installeur, pas ici
    console 'echo "Secure Boot : $(od -An -tu1 /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c | tr -s " " "\n" | tail -n 1)"; echo "Processus anaconda : $(grep -las "[b]in/anaconda" /proc/[0-9]*/cmdline | wc -l)"; echo "Module de langue : $(grep -las "[p]yanaconda.modules.localization" /proc/[0-9]*/cmdline | wc -l)"; echo "Langue : $(grep -o "setting locale to: .*" /tmp/anaconda.log | tail -n 1 | cut -d " " -f 4)"; echo "Logo : $(md5sum </usr/share/anaconda/pixmaps/nicos/sidebar-logo.png | cut -c 1-32)"; echo "Style : $(test -s /run/install/product/anaconda-gtk.css && echo NicOS)"; echo "Volume : $(sed -n "s/.*inst.stage2=hd:LABEL=\([^ ]*\).*/\1/p" /proc/cmdline)"; echo "--- Nom du produit"; grep -iE "^(product|version|name|pretty_name) *=" /.buildstamp /etc/os-release 2>&1; echo "--- /tmp/anaconda.log (mode d affichage, langue, erreurs)"; grep -iE "display mode|wayland|setting locale|setlocale failed|traceback" /tmp/anaconda.log | tail -n 20' || true
}

failures=0
expect() { # expect <description> <motif grep -E d'une ligne entière> <rapport>
    if grep -qxE "$2" <<<"$3"; then
        echo "ok        $1"
    else
        echo "ÉCHEC     $1" && failures=$((failures + 1))
    fi
}

# 1. Démarrage normal : menu GRUB de l'ISO (shim et GRUB signés), entrée par défaut
log "Démarrage de l'ISO $(basename "${ISO}") (Secure Boot : ${SECURE_BOOT})"
start_vm iso-serial.log
wait_installer
report="$(installer_report)"
printf '%s\n' "${report}" | tee "${LOGS}/installeur.txt"
screenshot installeur
logo_md5="$(md5sum <"${BRANDING}/usr/share/anaconda/pixmaps/nicos/sidebar-logo.png" | cut -c 1-32)"
expect "installeur en marche" 'Processus anaconda : [1-9][0-9]*' "${report}"
if [[ ${SECURE_BOOT} -eq 1 ]]; then
    expect "Secure Boot actif" 'Secure Boot : 1' "${report}"
fi
expect "écran « Bienvenue » : choix de la langue (module Localization)" 'Module de langue : [1-9][0-9]*' "${report}"
expect "logo NicOS (product.img) à la place de celui de Fedora" "Logo : ${logo_md5}" "${report}"
expect "couleurs NicOS (anaconda-gtk.css)" 'Style : NicOS' "${report}"
expect "installeur trouvé sur le volume NicOS (nom de la clé USB)" 'Volume : NicOS-[^ ]+' "${report}"
if grep -qi 'wayland startup failed' <<<"${report}"; then
    echo "ÉCHEC     l'installeur est passé en mode texte" && failures=$((failures + 1))
fi
stop_vm

# 2. Langue demandée au lancement : l'installeur doit s'afficher dans cette langue
if [[ -n "${LANGUE}" ]]; then
    name="installeur-${LANGUE%%_*}"
    log "Second démarrage : installeur en ${LANGUE} (inst.lang)"
    # Paramètres de l'entrée par défaut du menu GRUB de l'ISO, sans la vérification du support
    rm -rf "${WORK}/iso-boot" && mkdir -p "${WORK}/iso-boot"
    xorriso -osirrox on -indev "${ISO}" \
        -extract /images/pxeboot/vmlinuz "${WORK}/iso-boot/vmlinuz" \
        -extract /images/pxeboot/initrd.img "${WORK}/iso-boot/initrd.img" \
        -extract /EFI/BOOT/grub.cfg "${WORK}/iso-boot/grub.cfg" 2>/dev/null
    kernel_args="$(awk '$1 ~ /^linux(efi)?$/ && $2 ~ /vmlinuz/ { $1 = ""; $2 = ""; print; exit }' "${WORK}/iso-boot/grub.cfg")"
    [[ "${kernel_args}" == *inst.stage2=* ]] || die "paramètres de l'installeur introuvables dans le grub.cfg de l'ISO"
    kernel_args="${kernel_args// rd.live.check/} inst.lang=${LANGUE}"
    echo "Paramètres du noyau :${kernel_args}"
    start_vm "${name}-serial.log" "${kernel_args}"
    wait_installer
    report="$(installer_report)"
    printf '%s\n' "${report}" | tee "${LOGS}/${name}.txt"
    screenshot "${name}"
    expect "installeur en marche" 'Processus anaconda : [1-9][0-9]*' "${report}"
    expect "installeur affiché en ${LANGUE}" "Langue : ${LANGUE//./\\.}" "${report}"
    if grep -q 'setlocale failed' <<<"${report}"; then
        echo "ÉCHEC     langue ${LANGUE} indisponible dans l'installeur" && failures=$((failures + 1))
    fi
    stop_vm
fi

[[ ${failures} -eq 0 ]] || die "${failures} vérification(s) de l'installeur en échec"
log "ISO validée : l'installeur graphique démarre$([[ ${SECURE_BOOT} -eq 1 ]] && echo " avec Secure Boot"), aux couleurs de NicOS, avec le choix de la langue$([[ -n "${LANGUE}" ]] && echo " ; testé en ${LANGUE}") (captures : ${LOGS})"
