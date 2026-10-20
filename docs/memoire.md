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
