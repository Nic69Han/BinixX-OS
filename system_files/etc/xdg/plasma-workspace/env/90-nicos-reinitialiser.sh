# Lu par startplasma avant le démarrage de Plasma : applique une remise à zéro du bureau programmée
# depuis le Centre NicOS (Aide). Ne fait rien sans demande.
if [ -e "${XDG_STATE_HOME:-$HOME/.local/state}/nicos/reinitialiser-bureau" ]; then
    /usr/libexec/nicos/nicos-reinitialiser-bureau appliquer || true
fi
