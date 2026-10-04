# shellcheck shell=bash
# Démarrage graphique : ce que le noyau reçoit, ce que Plymouth fait, ce que GRUB affiche.
# Cette étape ne fait que relever l'état (aucun échec) : elle sert à lire dans le journal du test pourquoi du texte
# s'affiche au démarrage. Les captures d'écran du démarrage sont décrites plus haut dans le journal (« Écran pendant le démarrage »).
decrire_demarrage() {
    section "Démarrage graphique (relevé)"
    indente() { sed 's/^/            /'; }
    echo "  ligne de commande du noyau (/proc/cmdline) :"
    indente </proc/cmdline
    echo "  entrées de démarrage (options de /boot/loader/entries) :"
    grep -h '^options' /boot/loader/entries/*.conf 2>/dev/null | indente
    echo "  paramètres imposés par l'image (/usr/lib/bootc/kargs.d) :"
    { ls /usr/lib/bootc/kargs.d/ 2>/dev/null && cat /usr/lib/bootc/kargs.d/*.toml 2>/dev/null; } | indente
    echo "  partition /boot :"
    findmnt -no TARGET,FSTYPE,OPTIONS /boot 2>&1 | indente
    echo "  variables du chargeur (grub2-editenv list) :"
    grub2-editenv list 2>&1 | indente
    echo "  dossiers GRUB :"
    # shellcheck disable=SC2012
    ls -la /boot/grub2 /boot/efi/EFI/fedora /boot/efi/EFI/BOOT 2>&1 | indente
    echo "  réglages de menu dans la configuration de GRUB :"
    grep -nE 'timeout|menu_auto_hide|menu_show_once|boot_success|boot_indeterminate|custom\.cfg|user\.cfg|load_env|set default|terminal' \
        /boot/grub2/grub.cfg /boot/efi/EFI/fedora/grub.cfg 2>&1 | head -n 40 | indente
    echo "  Plymouth :"
    echo "    thème par défaut : $(plymouth-set-default-theme 2>&1)"
    systemctl list-units --all --no-legend --plain 'plymouth*' 2>&1 | indente
    journalctl -b -o short-monotonic --no-pager 2>/dev/null | grep -iE 'plymouth' | head -n 12 | indente
    echo "  Plymouth dans l'image de démarrage (initramfs) :"
    lsinitrd /usr/lib/modules/*/initramfs.img 2>/dev/null | grep -E 'plymouth/(two-step|binixx/(binixx|watermark))' | indente
    return 0
}
register_check base decrire_demarrage
register_check after-update decrire_demarrage
