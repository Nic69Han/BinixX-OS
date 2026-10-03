# Modules de l'image

Un fichier `NN-nom.sh` par fonctionnalité. `build.sh` les exécute dans l'ordre alphabétique,
chacun dans son propre `bash`, après les sections 1 à 7 et avant la régénération de l'initramfs.

- Le contexte de build est monté sur `/ctx` : `/ctx/system_files` (copié sur `/` en section 1 de
  `build.sh`, donc déjà en place), `/ctx/flatpaks`.
- Commencer par `set -ouex pipefail`, comme `build.sh`.
- Installer ses propres paquets avec `dnf5 -y install …` et faire échouer le build si quelque chose
  manque (`rpm -q …`) : mieux vaut un build rouge qu'une image incomplète.
- Ajouter ses vérifications dans `tests/image/checks.d/NN-nom.sh` et `tests/vm/checks.d/NN-nom.sh`
  (voir `tests/README.md`).

Numéros utilisés : 40 administration (vérifications seulement, ses paquets sont dans `build.sh`).
Les mises à jour de sécurité ne sont pas un module : `build_files/securite.sh`, lancé par `build.sh` avant toute personnalisation (une mise à jour de paquet remettrait par-dessus les fichiers d'origine de Firefox, par exemple).
Les nouveaux modules prennent le numéro de leur chantier pour éviter les doublons.
