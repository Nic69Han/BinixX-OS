# Cartes graphiques NVIDIA

BinixX OS existe en deux images, construites à partir des mêmes sources et testées de la même façon
(installation, démarrage, mise à jour, retour arrière, retour arrière automatique) :

| Image | Pilote NVIDIA | Pour qui |
| --- | --- | --- |
| `binixx` | **nouveau** (libre, dans le noyau) | Bureautique, vidéo, visioconférence : suffit à la grande majorité des postes, y compris avec une carte NVIDIA. Aucune manipulation. |
| `binixx-nvidia` | **pilotes NVIDIA** officiels, déjà préparés et signés par [Universal Blue](https://universal-blue.org/) | Jeux, 3D, calcul (CUDA), écrans multiples exigeants, ou un affichage défaillant avec `nouveau`. |

Le reste est identique : mêmes logiciels, même bureau, mêmes mises à jour. La seconde image est
reconnaissable à « NVIDIA » dans *À propos* et dans le rapport de diagnostic.

## Faut-il la variante NVIDIA ?

Dans le doute, **non** : commencer avec `binixx`. Elle suffit si l'écran s'affiche bien, que la vidéo est
fluide et que l'on ne joue pas. Le passage à la variante se fait à tout moment, sans perdre ses fichiers
ni ses réglages, et se défait de la même façon.

## Passer à la variante NVIDIA

1. **Secure Boot activé ?** (`mokutil --sb-state`). Si oui, la clé de signature d'Universal Blue doit
   d'abord être **enrôlée** (MOK) : sans elle, le noyau refuse les pilotes et l'affichage retombe sur
   `nouveau`. Procédure et clé : documentation d'Universal Blue (paquet `ublue-os-akmods-addons`) ; au
   redémarrage, l'écran bleu « MOK Manager » demande de confirmer l'enrôlement avec le mot de passe choisi.
2. Passer à l'image : `sudo bootc switch ghcr.io/nic69han/binixx-nvidia:stable`, puis redémarrer.
3. Vérifier : `nvidia-smi` affiche la carte.

Retour à l'image standard : `sudo bootc switch ghcr.io/nic69han/binixx:stable`, puis redémarrer. Si le
bureau ne démarre pas après une mise à jour, le retour arrière automatique
([mises-a-jour.md](mises-a-jour.md)) ramène le PC à la version qui marchait.

## Ce qui est testé, et ce qui ne l'est pas

La CI construit et teste les deux images en machine virtuelle : l'image NVIDIA s'installe, démarre, se
met à jour et revient en arrière comme l'autre. Elle ne peut **pas** tester l'affichage avec une vraie
carte NVIDIA ni l'enrôlement Secure Boot : cela demande du matériel. Tant qu'aucun poste réel ne l'a
validé, la variante est à considérer comme **expérimentale** ; les retours (carte, résultat) sont
bienvenus.

## Pour les mainteneurs

- `Containerfile` : `ARG BASE_IMAGE` (défaut `ghcr.io/ublue-os/kinoite-main:44`) et `ARG BINIXX_VARIANT`.
  La variante NVIDIA utilise `ghcr.io/ublue-os/kinoite-nvidia:44` (pilote propriétaire ; Universal Blue
  publie aussi `kinoite-nvidia-open`, pour les cartes récentes seulement).
- `build.yml` construit les deux images (matrice) ; une pull request ne construit que l'image standard.
  Un échec de la variante NVIDIA ne bloque pas l'image standard.
- `test-vm.yml` teste et promeut chaque image séparément ; à la main, l'entrée `variant` choisit l'image.
- `build_files/modules.d/80-variante.sh` : vérifie la présence des pilotes et marque l'image. Il fait aussi
  dépendre `nvidia-persistenced` et `nvidia-cdi-refresh` du pilote chargé (`ConditionPathExists=/sys/module/nvidia`) :
  sans pilote (clé Secure Boot pas encore enrôlée, pas de carte NVIDIA), ils échouaient en boucle et leurs
  « [FAILED] » s'affichaient entre l'écran de démarrage et l'écran de connexion. Le test VM, où le pilote ne se charge
  pas, vérifie qu'ils sont écartés sans échec.
- Pas d'ISO NVIDIA : on installe BinixX OS, puis `bootc switch` (voir ci-dessus).
