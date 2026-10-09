# ArtCraft : création d'images et de vidéos par IA

[ArtCraft](https://getartcraft.com/) est un studio de création d'images et de vidéos par intelligence artificielle (composition 2D, mise en
scène 3D, choix du modèle), développé par l'équipe de storytold. BinixX OS l'ouvre comme une application du menu : **ArtCraft**, rangé avec
les applications graphiques (Graphisme).

## Ce qui est installé

Un **lanceur de web app** (`usr/share/applications/binixx-webapp-artcraft.desktop`) qui ouvre le service officiel,
<https://app.getartcraft.com/>, dans sa propre fenêtre sans barre d'adresse, comme les web apps de Teams, Zoom ou Microsoft 365
(`binixx-webapp`, moteur Chromium en Flatpak ; sans lui, le navigateur par défaut).

- **Aucun programme à mettre à jour** : c'est toujours la dernière version d'ArtCraft.
- **Compte** : à la première ouverture, ArtCraft demande de créer un compte gratuit ou de se connecter.
- **Données** : les images, les textes saisis et les vidéos sont envoyés aux serveurs d'ArtCraft et, selon le modèle choisi, à des
  fournisseurs tiers ; rien n'est généré sur le PC. Pour une entreprise : n'y mettre ni document confidentiel, ni photo de personnes sans
  leur accord, et lire d'abord les conditions d'utilisation du service (elles ne sont pas celles de la licence du code).

## Pourquoi pas l'application native

ArtCraft publie une application de bureau (Rust et Tauri) pour **Windows et macOS seulement** ; sous Linux, ses auteurs proposent de la
**compiler soi-même** ([guide de compilation](https://github.com/storytold/artcraft/blob/main/_docs/dev_setup.md)). Elle n'est pas sur Flathub.
L'embarquer dans l'image est possible techniquement, mais pas sans l'accord de ses auteurs :

- sa licence est une licence « **fair source** » écrite par ses auteurs (fichier `LICENSE.md`, « WIP » : *pas encore* un texte juridique
  complet), et non une licence libre reconnue par l'OSI ;
- elle permet de **copier, modifier, compiler et utiliser** le code « pour son usage privé et personnel » et donne les images créées à
  leurs auteurs ; elle **interdit** de vendre le logiciel, de s'en servir pour un produit concurrent, ou de retirer ses liens de soutien et ses
  services payants ;
- elle **ne prévoit pas** d'en distribuer une version compilée à d'autres personnes, ce que ferait une image système, et elle ne parle que
  d'usage « privé et personnel » (rien sur l'usage en entreprise).

Le lanceur web n'embarque aucun code d'ArtCraft : il n'y a donc rien à redistribuer. Si ses auteurs donnent leur accord écrit (ou publient
une version Linux, par exemple un Flatpak), la version native pourra remplacer le lanceur : le test de l'image vérifie aujourd'hui qu'aucun
programme ArtCraft n'est dans l'image.

Quelqu'un qui veut la version native pour **son usage personnel** peut la compiler en suivant le guide ci-dessus (Rust, Node.js et Tauri,
dans une boîte de développement type Toolbx ou Distrobox, puisque le système est en lecture seule).

## Tests

`tests/image/check-image.sh` (section « Web apps ») : le lanceur est valide, ouvre l'adresse officielle par `binixx-webapp`, est dans la catégorie
Graphics ; aucun programme ni paquet ArtCraft n'est dans l'image.
