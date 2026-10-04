# shellcheck shell=bash
# Démarrage graphique : ce que le noyau reçoit, ce que Plymouth fait, ce que GRUB affiche.
# Le relevé n'échoue jamais : il sert à lire dans le journal du test pourquoi du texte s'affiche au démarrage. Les captures d'écran
# du démarrage sont décrites plus haut dans le journal (« Écran pendant le démarrage »). Les vérifications, elles, échouent :
# le noyau doit avoir reçu les paramètres du démarrage silencieux (image/usr/lib/bootc/kargs.d), au premier démarrage comme
# après une mise à jour.
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
    echo "  /boot/grub2/user.cfg (menu discret) :"
    cat /boot/grub2/user.cfg 2>&1 | indente
    echo "  réglages de menu dans la configuration de GRUB :"
    grep -nE 'timeout|menu_auto_hide|menu_show_once|boot_success|boot_indeterminate|custom\.cfg|user\.cfg|load_env|set default|terminal' \
        /boot/grub2/grub.cfg /boot/efi/EFI/fedora/grub.cfg 2>&1 | head -n 40 | indente
    echo "  Plymouth :"
    echo "    thème par défaut : $(plymouth-set-default-theme 2>&1)"
    systemctl list-units --all --no-legend --plain 'plymouth*' 2>&1 | indente
    journalctl -b -o short-monotonic --no-pager 2>/dev/null | grep -iE 'plymouth' | head -n 12 | indente
    echo "  sessions et gestionnaire de connexion :"
    # shellcheck disable=SC2009
    { loginctl list-sessions --no-legend; ps -eo user,comm | grep -iE 'plasmalogin|greeter' | sort | uniq -c; } 2>&1 | indente
    echo "  Plymouth dans l'image de démarrage (initramfs) :"
    lsinitrd /usr/lib/modules/*/initramfs.img 2>/dev/null | grep -E 'plymouth/(two-step|binixx/(binixx|watermark))' | indente
    return 0
}
register_check base decrire_demarrage
register_check after-update decrire_demarrage

verifier_demarrage() {
    section "Démarrage graphique (vérifications)"
    local cmdline karg
    cmdline=" $(</proc/cmdline) "
    for karg in quiet splash rhgb loglevel=3 systemd.show_status=auto rd.systemd.show_status=auto; do
        if [[ "${cmdline}" == *" ${karg} "* ]]; then
            pass "le noyau a reçu « ${karg} »"
        else
            fail "le noyau n'a pas reçu « ${karg} » (ligne de commande :${cmdline})"
        fi
    done
    # (pas de « journalctl | grep -q » : grep -q ferme le tube avant la fin et pipefail y voit un échec)
    check "Plymouth s'est lancé pendant ce démarrage (plymouth-start.service)" systemctl is-active plymouth-start.service
    check "Plymouth a rendu la main à la connexion (plymouth-quit.service)" systemctl is-active plymouth-quit.service
    # shellcheck disable=SC2016  # le $(…) s'évalue dans le bash -c
    check "le thème de démarrage est celui de BinixX OS" bash -c '[[ "$(plymouth-set-default-theme)" == binixx ]]'
}
register_check base verifier_demarrage
register_check after-update verifier_demarrage

verifier_menu_grub() {
    section "Menu de démarrage discret (GRUB)"
    check "user.cfg écrit par BinixX OS (menu caché après un démarrage réussi)" \
        bash -c 'head -n 1 /boot/grub2/user.cfg | grep -q "^# BinixX OS : menu de démarrage discret"'
    # shellcheck disable=SC2016  # le $(…) s'évalue dans le bash -c
    check "service binixx-menu-grub terminé sans erreur" bash -c '[[ "$(systemctl show -p Result --value binixx-menu-grub.service)" == success ]]'
    if command -v grub2-script-check >/dev/null; then
        check "user.cfg : syntaxe GRUB valide" grub2-script-check /boot/grub2/user.cfg
    else
        warn "grub2-script-check absent : syntaxe de user.cfg non vérifiée ici"
    fi
}
register_check base verifier_menu_grub

verifier_menu_cache() {
    # Après un démarrage réussi, GRUB a lu user.cfg au démarrage suivant et a caché son menu : il l'écrit dans son environnement
    local etat
    etat="$(grub2-editenv list 2>&1 | grep '^binixx_menu=' || true)"
    if [[ "${etat}" == binixx_menu=cache ]]; then
        pass "GRUB a caché son menu à ce démarrage (le précédent avait réussi)"
    else
        fail "GRUB n'a pas caché son menu à ce démarrage : « ${etat:-binixx_menu absent} »"
    fi
}
register_check after-update verifier_menu_cache
