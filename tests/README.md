# Tests

Deux niveaux de tests, du plus rapide au plus complet.

## 1. Contenu de l'image : `tests/image/check-image.sh`

Lancé dans un conteneur à partir de l'image construite, sans la démarrer (quelques secondes).
Il vérifie les paquets, la substitution des polices Microsoft, le thème et la disposition Plasma,
la liste Flatpak, les lanceurs de web apps et l'activation des services.

- En local : `just build && just test-image`
- En CI : à chaque build (`build.yml`), pull requests comprises, **avant** toute publication.

## 2. Système complet en VM : `tests/vm/run-vm-test.sh`

1. Génère une ISO d'installation **automatique** (`iso-unattended.toml.in`, qui efface le disque de la VM).
2. Installe NicOS sur un disque vierge, sans intervention (critère MVP n°1).
3. Démarre le système installé en UEFI **avec Secure Boot** et lance `guest-checks.sh` dans la VM :
   état des services, SELinux, `/usr` en lecture seule, son, réseau, imprimante PDF (un vrai PDF est
   produit), session Plasma et disposition du panneau, installation des Flatpak.
4. Publie une « mise à jour » (`update/Containerfile` : l'image + un fichier témoin) dans un registre local,
   fait `bootc switch`, redémarre et vérifie ; puis `bootc rollback`, redémarre et vérifie (critère n°4).

Journaux, rapports et captures d'écran (dont `bureau.png`) : `tests/vm/_work/logs/`.

- En local (hôte x86_64 avec KVM, root) : `just test-vm`, ou
  `sudo tests/vm/run-vm-test.sh --image ghcr.io/nic69han/nicos:latest`
  (options `--no-secure-boot`, `--skip-update` ; `REUSE_ISO=1` pour ne pas regénérer l'ISO).
- En CI : `test-vm.yml`, après chaque build réussi de `main` ou à la main depuis l'onglet Actions.
  Compter 1 à 2 heures ; les journaux sont joints au run (artefact `vm-test-logs`).

Ce qui n'est pas testé automatiquement (fidélité des documents OnlyOffice, son réellement audible,
partage d'écran dans une vraie réunion) est décrit dans [docs/validation-mvp.md](../docs/validation-mvp.md).
