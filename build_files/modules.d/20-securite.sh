#!/usr/bin/bash
# Mises à jour de sécurité : applique au build les correctifs que Fedora a déjà publiés, au lieu d'attendre que l'image de
# base soit reconstruite (elle l'est chaque jour, mais un avis publié depuis moins de 24 h n'y est pas encore). Le contrôle
# « Pending security advisories » (just scan-securite) vérifie ensuite ce qui reste et bloque la publication s'il le faut.
#
# Exclus : le noyau et ses modules (kernel*, kmod-*, akmod-*). Universal Blue compile ceux de la variante NVIDIA pour UN
# noyau précis : changer le noyau sans recompiler ces modules casserait le pilote. Un avis sur le noyau reste donc visible
# dans le contrôle et attend la reconstruction de la base.

set -ouex pipefail

dnf5 -y upgrade --security --exclude='kernel*,kmod-*,akmod-*'

# Dans le journal du build : les avis qui restent (le contrôle de sécurité en tire la décision)
dnf5 updateinfo list --security || true
