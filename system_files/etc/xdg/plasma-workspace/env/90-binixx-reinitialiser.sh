# Lu par startplasma avant le démarrage de Plasma : applique une remise à zéro du bureau programmée
# depuis le Centre BinixX OS (Aide). Ne fait rien sans demande.
if [ -e "${XDG_STATE_HOME:-$HOME/.local/state}/binixx/reinitialiser-bureau" ]; then
    /usr/libexec/binixx/binixx-reinitialiser-bureau appliquer || true
fi
