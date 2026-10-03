# Vérifications de l'image par fonctionnalité

Chaque `NN-nom.sh` est chargé (`source`) par `../check-image.sh`, dans l'ordre alphabétique, avant le
bilan. Il dispose de `section`, `pass`, `fail` et `check`. Exemple :

```bash
section "Ma fonctionnalité"
check "paquet installé" rpm -q mon-paquet
check "lanceur valide" desktop-file-validate /usr/share/applications/binixx-ma-fonction.desktop
```
