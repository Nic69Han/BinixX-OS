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
  `sudo tests/vm/run-vm-test.sh --image ghcr.io/nic69han/nicos:testing`
  (options `--switch-ref`, `--no-secure-boot`, `--skip-update` ; `REUSE_ISO=1` pour ne pas
  regénérer l'ISO). Sur Ubuntu 25.04 et suivantes, désactiver d'abord le profil AppArmor qui bloque
  bootc-image-builder, jusqu'au prochain redémarrage : `sudo apparmor_parser -R /etc/apparmor.d/bwrap-userns-restrict`.
- En CI : `test-vm.yml`, après chaque build réussi de `main` ou à la main depuis l'onglet Actions.
  Il fige l'empreinte de l'image `testing`, la teste et, **si tout passe, la promeut en `stable`**,
  le canal que suivent les postes installés (voir [docs/mises-a-jour.md](../docs/mises-a-jour.md)).
  Compter 1 à 2 heures ; les journaux sont joints au run (artefact `vm-test-logs`).
  Pour tester une pull request avant de la fusionner : lancer « Test VM » sur sa branche avec l'option
  `build` cochée. L'image est alors construite depuis la branche, et jamais promue.

## 3. ISO publique : `tests/iso/boot-installer.sh`

L'ISO de l'étape 2 installe toute seule, mais ce n'est pas celle que téléchargent les utilisateurs.
Ce script démarre l'**ISO publique** dans une VM, comme sur un vrai PC :

1. firmware UEFI avec Secure Boot, puis shim et GRUB de l'ISO ;
2. il attend l'installeur graphique et l'interroge par sa console (`hvc0`) : mode graphique,
   Secure Boot actif, nom de produit affiché ;
3. il prend une capture d'écran de l'installeur (`installeur.png`).

Rien n'est installé.

- En local : `tests/iso/boot-installer.sh chemin/vers/install.iso` (KVM et OVMF nécessaires).
- En CI : `build-iso.yml` le lance juste après avoir fabriqué l'ISO. La capture et le rapport sont
  joints au run (artefact `installer-boot`), et l'ISO est publiée même si ce test échoue.

Ce qui n'est pas testé automatiquement (fidélité des documents OnlyOffice, son réellement audible,
partage d'écran dans une vraie réunion) est décrit dans [docs/validation-mvp.md](../docs/validation-mvp.md).
