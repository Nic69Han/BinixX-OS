# Mises à jour et canaux

BinixX OS se met à jour comme un tout : une nouvelle image système est téléchargée en arrière-plan
et s'applique au redémarrage suivant. La version précédente reste disponible pour revenir en
arrière. Les applications Flatpak se mettent à jour séparément, chaque jour.

## Deux canaux

| Canal | Contenu | Qui le suit |
| --- | --- | --- |
| `testing` | Chaque build de `main` : modifications fusionnées et build quotidien avec les correctifs de Fedora 44 | Testeurs volontaires |
| `stable` | Une image `testing` qui a passé le test VM complet (installation, démarrage, mise à jour, retour arrière) | Tous les postes installés depuis l'ISO |

`latest` est un alias de `stable`, gardé pour les commandes déjà publiées.

## Chemin d'une mise à jour

1. `build.yml` construit l'image, vérifie son contenu et la publie en `testing`.
2. `test-vm.yml` démarre aussitôt : il fige l'empreinte (`sha256:…`) de cette image et la teste
   dans une machine virtuelle.
3. Si toutes les vérifications passent, **la même empreinte** reçoit les étiquettes `stable` et
   `latest`. Une image qui échoue au test n'atteint jamais les postes.
4. Les postes la téléchargent lors de leur vérification automatique et l'appliquent au
   redémarrage suivant.

Au tout premier lancement du projet, `stable` n'existe qu'après le premier test VM réussi.
D'ici là, le workflow de l'ISO (qui embarque `stable`) ne peut pas aboutir.

## Sur un poste

```bash
rpm-ostree status                          # version en cours et version précédente
sudo bootc rollback                        # revenir à la version précédente (puis redémarrer)
sudo bootc switch ghcr.io/nic69han/binixx:testing   # devenir testeur
sudo bootc switch ghcr.io/nic69han/binixx:stable    # revenir au canal stable
```

La version précédente est aussi proposée dans le menu de démarrage.

## Postes installés sous l'ancien nom (NicOS)

Le projet s'appelait NicOS jusqu'au 3 octobre 2026 ; l'image se publie maintenant sous `ghcr.io/nic69han/binixx`
(variante NVIDIA : `binixx-nvidia`). Un poste installé avant ce changement suit encore l'ancienne adresse
(`ghcr.io/nic69han/nicos`), qui ne reçoit plus de mises à jour. Pour le faire passer au nouveau nom, une seule fois :

```bash
sudo bootc switch ghcr.io/nic69han/binixx:stable      # (ou binixx-nvidia:stable)
systemctl reboot
```

Les documents et les réglages de l'utilisateur ne bougent pas. Seuls les noms internes changent : les sauvegardes
faites avant le changement par « Réparer le système » ou « Réinitialiser le bureau » restent sur le disque
(`/var/lib/nicos`, `~/.local/share/nicos`) mais ne sont plus proposées dans la liste ; l'écran d'accueil peut
s'afficher une fois de plus.

## Retour arrière automatique

Si une mise à jour empêche l'écran de connexion de démarrer, le PC **revient tout seul à la version
précédente** : l'utilisateur voit le PC redémarrer deux ou trois fois, puis retrouve son bureau, sans
rien faire. C'est [greenboot](https://github.com/fedora-iot/greenboot-rs) (licence BSD-3-Clause, conçu
pour bootc) :

1. après une mise à jour, le chargeur de démarrage compte les essais (trois au plus) ;
2. à chaque démarrage, greenboot lance les contrôles de `/etc/greenboot/check/required.d/` ; le seul
   contrôle de BinixX OS est `10-binixx-connexion.sh` : le service de l'écran de connexion
   (`display-manager.service`) doit démarrer ;
3. contrôle réussi : le démarrage est déclaré bon, la mise à jour est adoptée ; contrôle en échec : le PC
   redémarre ; au troisième échec, il démarre la version précédente.

Choix de prudence :

- **un seul contrôle, celui qui rend le PC inutilisable.** Pas de test du réseau : un portable qui démarre
  hors connexion ne doit jamais revenir en arrière à tort. Les contrôles « par défaut » de greenboot
  (résolution DNS des dépôts) ne sont donc pas installés ;
- un PC volontairement sans bureau (cible par défaut autre que `graphical.target`) n'est pas contrôlé ;
- on attend jusqu'à 4 minutes que l'écran de connexion démarre, pour ne pas pénaliser un vieux PC ;
- une panne qui n'empêche pas l'écran de connexion de démarrer ne déclenche pas le retour arrière :
  le retour manuel reste possible (`sudo bootc rollback`, ou Administration du PC).

Le test en VM le vérifie de bout en bout : une « mise à jour défectueuse » (sans écran de connexion) est
publiée dans un registre local, la VM doit redémarrer trois fois puis revenir seule à la version
précédente (`tests/vm/update-bad/`, phase `after-auto-rollback`).

## Changer de version de Fedora

L'image de base est épinglée sur Fedora 44 (`kinoite-main:44` dans le `Containerfile`) : le
passage à une nouvelle version se fait par une pull request, validée comme les autres par le
test VM avant d'arriver en `stable`. À prévoir avant la fin du support de la version en cours.
