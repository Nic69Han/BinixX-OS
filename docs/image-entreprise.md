# Image d'entreprise : un BinixX OS aux couleurs et aux logiciels de la PME

Une PME ne veut pas régler chaque PC à la main. Elle prépare **une image** : BinixX OS + ses logiciels
+ ses réglages. Tous les postes l'installent, tous se mettent à jour ensemble, et un poste qui se
comporte mal revient à la version précédente en un redémarrage. C'est l'équivalent, en plus simple,
des « images de déploiement » Windows (MDT, Autopilot).

Le gabarit est le dossier [`entreprise/`](../entreprise/). Il est aussi fourni dans chaque poste
BinixX OS : `/usr/share/binixx/entreprise-template`.

## Ce qu'il faut

- Un dépôt Git (GitHub, par exemple) **privé** pour l'entreprise, et son registre d'images (GHCR) ;
- une demi-heure ; aucune connaissance de Linux n'est nécessaire pour les réglages courants.

## En 6 étapes

1. **Copier le gabarit** dans un nouveau dépôt privé : le dossier `entreprise/` de BinixX OS, ou depuis un
   poste BinixX OS `cp -r /usr/share/binixx/entreprise-template ~/mon-entreprise`.
2. **Régler `entreprise.conf`** : nom de l'entreprise, logiciels supplémentaires, page d'accueil de
   Firefox, serveur proxy. Les applications Flatpak de l'entreprise vont dans `flatpaks/entreprise.list`
   (elles s'ajoutent à celles de BinixX OS).
3. **Déposer ses fichiers** dans `system_files/` : ils sont copiés tels quels à la racine du système
   (fond d'écran, imprimantes, réglages KDE…).
4. **Activer la construction automatique** : copier `github-actions.yml.modele` dans
   `.github/workflows/build.yml`. L'image est reconstruite à chaque modification et chaque nuit, ce
   qui reprend les correctifs de BinixX OS sans rien faire.
5. **Installer le premier poste** avec l'ISO de BinixX OS, puis le faire suivre l'image de l'entreprise :
   `sudo bootc switch ghcr.io/<organisation>/binixx-entreprise:stable`, redémarrer. (Registre privé :
   s'identifier d'abord, `sudo podman login ghcr.io`, avec un jeton en lecture seule.)
6. **Installer les suivants** avec une ISO de l'entreprise : même principe que l'ISO de BinixX OS, avec
   `iso.toml.modele` (adresse de l'image à remplacer) ; voir « ISO d'installation » ci-dessous.

## Ce que l'on peut régler

| Besoin | Où |
| --- | --- |
| Nom de l'entreprise (« À propos », support) | `entreprise.conf` : `NOM_ENTREPRISE` |
| Logiciels supplémentaires (hors connexion, dans l'image) | `entreprise.conf` : `PAQUETS` |
| Applications Flatpak supplémentaires (installées au premier démarrage) | `flatpaks/entreprise.list` |
| Page d'accueil et proxy de Firefox | `entreprise.conf` : `PAGE_ACCUEIL`, `PROXY` |
| Fond d'écran de l'entreprise | `system_files/usr/share/wallpapers/BinixX/contents/images/…` |
| Imprimantes, partages réseau, réglages KDE | `system_files/etc/…` |
| Tout le reste (services, domaine Active Directory, VPN) | `build.sh` |

La jonction au domaine Active Directory se fait une fois par poste, avec un compte administrateur du
domaine (voir [administration.md](administration.md)) : l'image ne contient **jamais** de mot de passe.

## Mises à jour par étapes

Les postes suivent l'étiquette `stable`. Pour valider avant de déployer, publier d'abord sous
`testing` : les postes pilotes suivent `testing`
(`sudo bootc switch ghcr.io/<organisation>/binixx-entreprise:testing`), les autres attendent
que l'image soit promue en `stable` (`podman tag … :stable` puis `podman push`).
La version précédente reste toujours disponible : **Administration du PC → Mises à jour logicielles →
Revenir en arrière**.

## ISO d'installation

L'ISO de l'entreprise se fabrique comme celle de BinixX OS (`just build-iso`, voir le `Justfile` de BinixX OS),
avec `iso.toml.modele` copié en `disk_config/iso.toml`. Le script `disk_config/personnaliser-iso.sh`
de BinixX OS donne ensuite son nom au volume et son logo à l'installeur.

## Précautions

- Tout ce qui est dans l'image est lisible par les utilisateurs du poste : **aucun secret** (mot de
  passe, clé d'accès, jeton) dans `entreprise/`.
- Garder le dépôt et l'image **privés** si les réglages révèlent l'organisation du réseau.
- La signature des images (cosign) renforce la confiance ; elle est prévue pour BinixX OS (feuille de
  route, S2) et s'ajoute de la même façon à l'image de l'entreprise.

## Vérifier le gabarit

`just test-entreprise` construit le gabarit avec ses réglages d'exemple au-dessus de l'image BinixX OS
locale, puis vérifie le résultat (`tests/entreprise/check.sh`). La CI de BinixX OS le fait à chaque build.
