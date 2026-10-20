# Mémoire vive

BinixX OS doit rester confortable sur un vieux PC de 4 Go. Cette page dit comment la mémoire est mesurée, et ce qui est fait pour
en prendre le moins possible.

## Mesurer

- **Sur un PC** : `/usr/libexec/binixx/binixx-memoire` affiche la mémoire utilisée et disponible, la mémoire d'échange (zram) et
  les applications qui en prennent le plus (processus du même nom réunis, mémoire comptée en PSS : une bibliothèque partagée
  n'est comptée qu'une fois). `--processus` détaille par processus, `--valeurs` donne le résumé en clé=valeur. Le même relevé
  figure dans le rapport de diagnostic (Centre BinixX → Aide), section « Mémoire et processeur ».
- **Dans le test VM** (`tests/vm/checks.d/88-memoire.sh`, phase `memoire`) : après un redémarrage, sur la VM de 4 Go, session
  ouverte et au repos, avant toute autre fenêtre. Le journal du test montre les réglages en place (zram, noyau, systemd-oomd,
  paquets candidats à l'allègement, applications lancées avec la session, Baloo), la mémoire de chaque service, les applications
  les plus lourdes, puis une ligne `RELEVÉ MÉMOIRE utilise=… disponible=… echange=…` (Mo).
- **Budget** : `MEMOIRE_BUDGET_MO` (1500 Mo) n'est qu'un avertissement tant que la valeur n'est pas calibrée sur plusieurs
  passages ; le test échoue au-delà de `MEMOIRE_ECHEC_MO` (3000 Mo), signe d'une session cassée ou d'une fuite.

## Ce qui est fait

| Réglage | Fichier | Pourquoi |
| --- | --- | --- |
| zram aussi grand que la mémoire vive (8 Go au plus), zstd | `usr/lib/systemd/zram-generator.conf.d/50-binixx.conf` | Mémoire d'échange compressée en mémoire : un PC de 4 Go tient comme s'il en avait 6 à 7 avant de ralentir. |
| `vm.swappiness = 150`, `vm.page-cluster = 0`, `vm.watermark_boost_factor = 0` | `usr/lib/sysctl.d/61-binixx-memoire.conf` | Réglages du noyau pour le zram (Documentation/admin-guide/sysctl/vm.rst) : ranger les pages peu utilisées plutôt que vider le cache des fichiers. |
| Baloo : noms de fichiers seulement | `etc/xdg/baloofilerc` (`only basic indexing=true`) | L'indexation du contenu prend de la mémoire et du disque. La recherche du Centre et de KRunner trouve toujours les fichiers par leur nom. Chacun peut réactiver le contenu dans Configuration du système → Recherche. |
| Notificateur de Discover et KDE Connect plus lancés avec la session | `build_files/modules.d/88-memoire.sh` (Hidden=true) | 25 à 40 Mo chacun ; les mises à jour sont automatiques et visibles dans le Centre. Réactivables par compte (Démarrage automatique). |
| Accueil déjà vu : le Centre ne se charge plus à chaque connexion | `usr/libexec/binixx/binixx-centre` | Une seconde et une centaine de Mo en moins à chaque ouverture de session. |
| Installation des applications au premier démarrage : `MemoryHigh=512M`, `CPUWeight=20` | `binixx-flatpak-install.service.d/50-binixx-memoire.conf` | Le bureau garde la priorité pendant les téléchargements. |
| Firefox : onglets déchargés quand la mémoire manque, 2 pages gardées pour Précédent, pas de préchargement | `build_files/modules.d/88-memoire.sh` | Valeurs par défaut, modifiables dans about:config. |

À ne pas faire, et pourquoi : earlyoom (fait double emploi avec systemd-oomd de Fedora), zswap en plus du zram (double compression),
KSM (canal entre machines virtuelles), `mitigations=off` (sécurité), un noyau plus récent que celui de Fedora (pilotes NVIDIA signés
pour le noyau de Fedora).
