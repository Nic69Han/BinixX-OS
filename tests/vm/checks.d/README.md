# Vérifications dans la VM par fonctionnalité

Chaque `NN-nom.sh` est chargé par `../guest-checks.sh` (dans la VM, en root). Il définit une fonction
et l'inscrit à une ou plusieurs phases : `base` (premier démarrage), `after-update` ou `after-rollback`.
Il dispose de `section`, `pass`, `warn`, `fail`, `check`, `wait_for`, `TEST_USER` et `TEST_HOME`.

```bash
check_ma_fonction() {
    section "Ma fonctionnalité"
    check "service actif" systemctl is-active mon-service.service
}
register_check base check_ma_fonction
```

`run-vm-test.sh` envoie `guest-checks.sh` et ce dossier dans la VM.
