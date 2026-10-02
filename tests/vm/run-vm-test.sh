#!/usr/bin/bash
# Test de bout en bout de NicOS dans une machine virtuelle KVM (critères MVP 1, 3 et 4) :
#   1. génère une ISO d'installation automatique à partir de l'image (bootc-image-builder) ;
#   2. installe NicOS sur un disque vierge, sans aucune intervention ;
#   3. démarre le système installé (UEFI + Secure Boot) et le vérifie (guest-checks.sh) ;
#   4. le met à jour depuis un registre local, redémarre et vérifie, puis revient en arrière
#      avec `bootc rollback`, redémarre et vérifie de nouveau ;
#   5. lui impose une mise à jour défectueuse (plus d'écran de connexion) : il doit revenir tout seul
#      à la version précédente après trois démarrages (greenboot, retour arrière automatique).
#
# Usage : sudo tests/vm/run-vm-test.sh --image ghcr.io/nic69han/nicos:testing
#         [--switch-ref REF] [--workdir DIR] [--no-secure-boot] [--skip-update] [--skip-auto-rollback]
#
# --image accepte une étiquette ou une empreinte (…/nicos@sha256:…), pour tester exactement
# l'image qui sera promue. --switch-ref est l'image que le système installé suivra ensuite
# pour ses mises à jour (comme le `bootc switch` de disk_config/iso.toml) ; par défaut --image.
#
# Prérequis (hôte x86_64) : /dev/kvm, podman, qemu-system-x86_64, qemu-img, OVMF (edk2),
# xorriso, ssh, python3, curl. Journaux, captures et rapports : <workdir>/logs/.
# Variables utiles : VM_CPUS, VM_RAM (Mio), SSH_PORT, BIB_IMAGE, REUSE_ISO=1,
# OVMF_CODE, OVMF_VARS, OVMF_VARS_SECURE_BOOT (chemins des firmwares si non détectés).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${REPO_ROOT}/tests/vm"

IMAGE=""
SWITCH_REF=""
WORK="${TEST_DIR}/_work"
SECURE_BOOT=1
RUN_UPDATE=1
RUN_AUTO_ROLLBACK=1
while [[ $# -gt 0 ]]; do
    case "$1" in
    --image) IMAGE="$2" && shift 2 ;;
    --switch-ref) SWITCH_REF="$2" && shift 2 ;;
    --workdir) WORK="$2" && shift 2 ;;
    --no-secure-boot) SECURE_BOOT=0 && shift ;;
    --skip-update) RUN_UPDATE=0 && shift ;;
    --skip-auto-rollback) RUN_AUTO_ROLLBACK=0 && shift ;;
    -h | --help) sed -n '2,21p' "${BASH_SOURCE[0]}" && exit 0 ;;
    *) echo "Option inconnue : $1" >&2 && exit 2 ;;
    esac
done
[[ -n "${IMAGE}" ]] || { echo "--image est obligatoire" >&2 && exit 2; }
[[ ${EUID} -eq 0 ]] || { echo "À lancer en root (bootc-image-builder et podman rootful)" >&2 && exit 2; }

# Chemin absolu : QEMU lancé avec -daemonize se place dans /
mkdir -p "${WORK}"
WORK="$(cd "${WORK}" && pwd)"

# Configuration minimale annoncée (docs/compatibilite.md) : un PC refusé par Windows 11 doit suffire
VM_CPUS="${VM_CPUS:-2}"
VM_RAM="${VM_RAM:-4096}"
SSH_PORT="${SSH_PORT:-2222}"
BIB_IMAGE="${BIB_IMAGE:-quay.io/centos-bootc/bootc-image-builder:latest}"
REGISTRY_PORT=5000
UPDATE_REF="10.0.2.2:${REGISTRY_PORT}/nicos:update-test" # 10.0.2.2 = l'hôte, vu depuis la VM
BAD_UPDATE_REF="10.0.2.2:${REGISTRY_PORT}/nicos:update-bad"
TEST_USER=testeur

LOGS="${WORK}/logs"
ISO="${WORK}/bib-output/bootiso/install.iso"
DISK="${WORK}/disk.qcow2"
KEY="${WORK}/id_ed25519"
QMP_SOCK="${WORK}/qmp.sock"
PIDFILE="${WORK}/qemu.pid"

log() { printf '\n\033[1m[%(%H:%M:%S)T] %s\033[0m\n' -1 "$*"; }
die() {
    printf '\n\033[1;31mÉCHEC : %s\033[0m\n' "$*" >&2
    exit 1
}

for cmd in podman qemu-system-x86_64 qemu-img xorriso ssh ssh-keygen python3 curl; do
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

mkdir -p "${LOGS}"

### Outils VM ------------------------------------------------------------------

vm_running() { [[ -f "${PIDFILE}" ]] && kill -0 "$(<"${PIDFILE}")" 2>/dev/null; }

ssh_vm() {
    ssh -i "${KEY}" -p "${SSH_PORT}" -o BatchMode=yes -o ConnectTimeout=5 -o LogLevel=ERROR \
        -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${TEST_USER}@127.0.0.1" "$@"
}

wait_ssh() { # wait_ssh <secondes>
    local deadline=$((SECONDS + $1))
    until ssh_vm true 2>/dev/null; do
        vm_running || die "la VM s'est arrêtée (voir ${LOGS}/boot-serial.log)"
        [[ ${SECONDS} -lt ${deadline} ]] || die "pas de connexion SSH après $1 s (voir ${LOGS}/boot-serial.log)"
        sleep 5
    done
}

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

start_vm() { # démarre le système installé, en arrière-plan
    local vars="${WORK}/vars-boot.fd"
    if [[ ${SECURE_BOOT} -eq 1 ]]; then
        # Variables neuves avec les clés Microsoft : aucune entrée de démarrage,
        # le firmware passe par le chemin de secours EFI/BOOT/BOOTX64.EFI (shim signé)
        [[ -f "${vars}" ]] || cp "${OVMF_VARS_SECURE_BOOT}" "${vars}"
    else
        vars="${WORK}/vars-install.fd"
    fi
    rm -f "${QMP_SOCK}"
    qemu-system-x86_64 \
        -name nicos-test \
        -machine q35,accel=kvm,smm=on -global driver=cfi.pflash01,property=secure,value=on \
        -cpu host -smp "${VM_CPUS}" -m "${VM_RAM}" \
        -drive "if=pflash,format=raw,unit=0,file=${OVMF_CODE},readonly=on" \
        -drive "if=pflash,format=raw,unit=1,file=${vars}" \
        -drive "file=${DISK},if=virtio,format=qcow2" \
        -netdev "user,id=net0,hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22" -device virtio-net-pci,netdev=net0 \
        -audiodev none,id=snd0 -device intel-hda -device hda-duplex,audiodev=snd0 \
        -device virtio-vga -device virtio-rng-pci \
        -display none \
        -serial "file:${LOGS}/boot-serial.log" \
        -qmp "unix:${QMP_SOCK},server=on,wait=off" \
        -daemonize -pidfile "${PIDFILE}"
}

stop_vm() {
    vm_running || return 0
    qmp system_powerdown >/dev/null 2>&1 || true
    local deadline=$((SECONDS + 120))
    while vm_running && [[ ${SECONDS} -lt ${deadline} ]]; do sleep 2; done
    vm_running && kill "$(<"${PIDFILE}")" 2>/dev/null
    rm -f "${PIDFILE}"
}

reboot_vm() {
    local old_boot new_boot=""
    old_boot="$(ssh_vm cat /proc/sys/kernel/random/boot_id)"
    ssh_vm sudo systemctl reboot || true
    local deadline=$((SECONDS + 900))
    while [[ -z "${new_boot}" || "${new_boot}" == "${old_boot}" ]]; do
        vm_running || die "la VM s'est arrêtée pendant le redémarrage"
        [[ ${SECONDS} -lt ${deadline} ]] || die "la VM n'a pas redémarré en 15 minutes"
        sleep 5
        new_boot="$(ssh_vm cat /proc/sys/kernel/random/boot_id 2>/dev/null || true)"
    done
}

guest_checks() { # guest_checks <phase> : lance guest-checks.sh (et checks.d/) dans la VM, garde journal et rapport
    tar -C "${TEST_DIR}" -cf - guest-checks.sh checks.d |
        ssh_vm 'rm -rf /tmp/nicos-tests && mkdir /tmp/nicos-tests && tar -C /tmp/nicos-tests -xf -'
    local status=0
    ssh_vm sudo bash /tmp/nicos-tests/guest-checks.sh "$1" "${SECURE_BOOT}" </dev/null 2>&1 | tee "${LOGS}/checks-$1.log" || status=$?
    ssh_vm sudo journalctl -b --no-pager >"${LOGS}/journal-$1.log" 2>&1 || true
    ssh_vm sudo bootc status >"${LOGS}/bootc-status-$1.txt" 2>&1 || true
    return "${status}"
}

cleanup() {
    local status=$?
    if vm_running; then
        [[ ${status} -ne 0 ]] && screenshot echec
        stop_vm
    fi
    podman rm -f nicos-test-registry >/dev/null 2>&1 || true
    # Journaux rendus à l'utilisateur qui a lancé sudo (lisibles sans root, et par la CI)
    if [[ -n "${SUDO_UID:-}" && -d "${LOGS}" ]]; then
        chown -R "${SUDO_UID}:${SUDO_GID:-${SUDO_UID}}" "${LOGS}" || true
    fi
    exit "${status}"
}
trap cleanup EXIT

### 1. ISO d'installation automatique -------------------------------------------

log "Image testée : ${IMAGE}"
if [[ "${IMAGE}" == localhost/* ]]; then
    podman image exists "${IMAGE}" || die "image locale introuvable dans le stockage root : ${IMAGE}"
    switch_cmd="bootc switch --mutate-in-place --transport containers-storage ${IMAGE}"
else
    podman pull "${IMAGE}"
    switch_cmd="bootc switch --mutate-in-place --transport registry ${IMAGE}"
fi
if [[ -n "${SWITCH_REF}" ]]; then
    switch_cmd="bootc switch --mutate-in-place --transport registry ${SWITCH_REF}"
fi
# Nom local fixe pour l'ISO et la mise à jour de test, même si --image est une empreinte
CANDIDATE=localhost/nicos-vm-test:candidate
podman tag "${IMAGE}" "${CANDIDATE}"

[[ -f "${KEY}" ]] || ssh-keygen -q -t ed25519 -N '' -C nicos-vm-test -f "${KEY}"
config="$(<"${TEST_DIR}/iso-unattended.toml.in")"
config="${config//@SSH_PUBKEY@/$(<"${KEY}.pub")}"
config="${config//@SWITCH_CMD@/${switch_cmd}}"
printf '%s\n' "${config}" >"${WORK}/iso-unattended.toml"

if [[ "${REUSE_ISO:-0}" == 1 && -f "${ISO}" ]]; then
    log "Réutilisation de l'ISO existante (REUSE_ISO=1)"
else
    # Ubuntu 25.04+ : le profil AppArmor bwrap-userns-restrict retire tous les droits aux
    # programmes lancés par bwrap, même root dans un conteneur privilégié. osbuild (dans
    # bootc-image-builder) passe par bwrap à chaque étape et échouerait au premier montage.
    if grep -qs '^unpriv_bwrap ' /sys/kernel/security/apparmor/profiles; then
        die "le profil AppArmor bwrap-userns-restrict bloque bootc-image-builder.
Désactivez-le jusqu'au prochain redémarrage : apparmor_parser -R /etc/apparmor.d/bwrap-userns-restrict"
    fi
    log "Génération de l'ISO d'installation automatique"
    # quay.io coupe parfois les connexions en cours de route : téléchargement avec reprise (fetch-bib.sh)
    "${TEST_DIR}/fetch-bib.sh" "${BIB_IMAGE}"
    rm -rf "${WORK}/bib-output" && mkdir -p "${WORK}/bib-output"
    podman run --rm --privileged --pull=never \
        --security-opt label=type:unconfined_t \
        -v "${WORK}/iso-unattended.toml:/config.toml:ro" \
        -v "${WORK}/bib-output:/output" \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        "${BIB_IMAGE}" \
        --type anaconda-iso --use-librepo=True \
        "${CANDIDATE}"
fi
[[ -f "${ISO}" ]] || die "ISO introuvable : ${ISO}"

### 2. Installation sans intervention ---------------------------------------------

log "Installation de NicOS sur un disque vierge (console : ${LOGS}/install-serial.log)"
# Démarrage direct du noyau de l'ISO, pour lire l'installeur sur la console série.
# Les paramètres (emplacement de l'installeur et du kickstart) viennent du menu GRUB de l'ISO.
rm -rf "${WORK}/iso-boot" && mkdir -p "${WORK}/iso-boot"
xorriso -osirrox on -indev "${ISO}" \
    -extract /images/pxeboot/vmlinuz "${WORK}/iso-boot/vmlinuz" \
    -extract /images/pxeboot/initrd.img "${WORK}/iso-boot/initrd.img" \
    -extract /EFI/BOOT/grub.cfg "${WORK}/iso-boot/grub.cfg"
kernel_args="$(awk '$1 ~ /^linux(efi)?$/ && $2 ~ /vmlinuz/ { $1 = ""; $2 = ""; print; exit }' "${WORK}/iso-boot/grub.cfg")"
[[ "${kernel_args}" == *inst.stage2=* ]] || die "paramètres d'installation introuvables dans le grub.cfg de l'ISO"
# Sans vérification du support (lente) ni écran de démarrage graphique, avec la console série
read -ra grub_words <<<"${kernel_args}"
boot_words=()
for word in "${grub_words[@]}"; do
    case "${word}" in
    rd.live.check | quiet | rhgb) ;;
    *) boot_words+=("${word}") ;;
    esac
done
kernel_args="${boot_words[*]} console=ttyS0,115200 inst.text"
echo "Paramètres du noyau : ${kernel_args}"

rm -f "${DISK}" "${WORK}/vars-boot.fd"
qemu-img create -q -f qcow2 "${DISK}" 64G
# Installation en UEFI sans clés Secure Boot (le noyau démarré directement n'est pas vérifié)
cp "${OVMF_VARS}" "${WORK}/vars-install.fd"
install_status=0
timeout 90m qemu-system-x86_64 \
    -name nicos-install \
    -machine q35,accel=kvm,smm=on -global driver=cfi.pflash01,property=secure,value=on \
    -cpu host -smp "${VM_CPUS}" -m "${VM_RAM}" \
    -drive "if=pflash,format=raw,unit=0,file=${OVMF_CODE},readonly=on" \
    -drive "if=pflash,format=raw,unit=1,file=${WORK}/vars-install.fd" \
    -drive "file=${DISK},if=virtio,format=qcow2" \
    -cdrom "${ISO}" \
    -kernel "${WORK}/iso-boot/vmlinuz" -initrd "${WORK}/iso-boot/initrd.img" -append "${kernel_args}" \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
    -device virtio-rng-pci \
    -display none -serial "file:${LOGS}/install-serial.log" -no-reboot || install_status=$?
[[ ${install_status} -ne 124 ]] || die "installation non terminée en 90 minutes (l'installeur attend peut-être une réponse)"
grep -q NICOS-INSTALL-OK "${LOGS}/install-serial.log" ||
    die "l'installation n'a pas abouti (voir ${LOGS}/install-serial.log)"
log "Installation terminée sans intervention"

### 3. Premier démarrage ------------------------------------------------------------

log "Démarrage du système installé (Secure Boot : ${SECURE_BOOT})"
start_vm
wait_ssh 900
log "Vérifications du système installé"
base_status=0
guest_checks base || base_status=$?
screenshot bureau
[[ ${base_status} -eq 0 ]] || die "vérifications du premier démarrage"

### 4. Mise à jour puis retour arrière ----------------------------------------------

if [[ ${RUN_UPDATE} -eq 1 ]]; then
    log "Préparation d'une mise à jour dans un registre local"
    podman build --pull=never --build-arg "BASE_IMAGE=${CANDIDATE}" \
        -t localhost/nicos-update-test:latest "${TEST_DIR}/update"
    podman rm -f nicos-test-registry >/dev/null 2>&1 || true
    podman run -d --rm --name nicos-test-registry -p "${REGISTRY_PORT}:5000" docker.io/library/registry:2
    podman push --tls-verify=false localhost/nicos-update-test:latest "localhost:${REGISTRY_PORT}/nicos:update-test"

    log "Mise à jour de la VM vers ${UPDATE_REF}"
    ssh_vm "sudo tee /etc/containers/registries.conf.d/90-nicos-test.conf >/dev/null" <<EOF
[[registry]]
location = "10.0.2.2:${REGISTRY_PORT}"
insecure = true
EOF
    ssh_vm sudo bootc switch "${UPDATE_REF}" </dev/null 2>&1 | tee "${LOGS}/bootc-switch.log" ||
        die "bootc switch vers la mise à jour"
    reboot_vm
    guest_checks after-update || die "vérifications après la mise à jour"

    log "Retour arrière vers la version précédente"
    ssh_vm sudo bootc rollback </dev/null 2>&1 | tee "${LOGS}/bootc-rollback.log" ||
        die "bootc rollback"
    reboot_vm
    guest_checks after-rollback || die "vérifications après le retour arrière"

    ### 5. Mise à jour défectueuse : retour arrière automatique (greenboot) ---------------

    if [[ ${RUN_AUTO_ROLLBACK} -eq 1 ]]; then
        log "Mise à jour défectueuse : l'écran de connexion ne démarre plus"
        podman build --pull=never --build-arg "BASE_IMAGE=${CANDIDATE}" \
            -t localhost/nicos-update-bad:latest "${TEST_DIR}/update-bad"
        podman push --tls-verify=false localhost/nicos-update-bad:latest "localhost:${REGISTRY_PORT}/nicos:update-bad"
        ssh_vm sudo bootc switch "${BAD_UPDATE_REF}" </dev/null 2>&1 | tee "${LOGS}/bootc-switch-bad.log" ||
            die "bootc switch vers la mise à jour défectueuse"
        ssh_vm sudo systemctl reboot || true
        # Trois démarrages en échec (compteur de greenboot), puis retour à la version précédente.
        # Chaque démarrage défectueux ne dure qu'une vingtaine de secondes : on ne compte pas sur le fait de
        # l'attraper par SSH. Le contrôle de la mise à jour défectueuse écrit une ligne par démarrage dans
        # /var/log/nicos-test-boots (partagé avec la version précédente) : « version d'origine de nouveau
        # démarrée et fichier non vide » prouve qu'elle a démarré, échoué, puis qu'on est revenu en arrière.
        deadline=$((SECONDS + 1800))
        rolled_back=0
        while [[ ${rolled_back} -eq 0 ]]; do
            vm_running || die "la VM s'est arrêtée pendant le retour arrière automatique"
            [[ ${SECONDS} -lt ${deadline} ]] || die "pas de retour arrière automatique en 30 minutes (voir ${LOGS}/boot-serial.log)"
            sleep 10
            state="$(ssh_vm 'if test -e /usr/share/nicos/update-bad-marker; then echo bad; elif test -s /var/log/nicos-test-boots; then echo rolled-back; else echo good; fi' 2>/dev/null || true)"
            [[ ${state} == "rolled-back" ]] && rolled_back=1
        done
        log "Retour arrière automatique effectué"
        guest_checks after-auto-rollback || die "vérifications après le retour arrière automatique"
    fi
fi

log "Test VM réussi : installation, démarrage$([[ ${RUN_UPDATE} -eq 1 ]] && echo ', mise à jour et retour arrière') validés"
