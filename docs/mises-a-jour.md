# Mises à jour et canaux

NicOS se met à jour comme un tout : une nouvelle image système est téléchargée en arrière-plan
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
sudo bootc switch ghcr.io/nic69han/nicos:testing   # devenir testeur
sudo bootc switch ghcr.io/nic69han/nicos:stable    # revenir au canal stable
```

La version précédente est aussi proposée dans le menu de démarrage.

## Changer de version de Fedora

L'image de base est épinglée sur Fedora 44 (`kinoite-main:44` dans le `Containerfile`) : le
passage à une nouvelle version se fait par une pull request, validée comme les autres par le
test VM avant d'arriver en `stable`. À prévoir avant la fin du support de la version en cours.
