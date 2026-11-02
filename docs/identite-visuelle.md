# Identité visuelle

Le logo de BinixX OS est une **gemme** : un losange aux angles doux, fendu de deux entailles
diagonales. Il reprend le losange à lames bleues et noires de l'avatar GitHub du projet,
dans un style plus moderne (dégradé, lumière venant du haut), proche de Windows 11.

## Fichiers

| Fichier | Usage |
| --- | --- |
| `branding/logo/binixx-logo-horizontal.svg` | Logo principal (fond clair) |
| `branding/logo/binixx-logo-horizontal-fond-sombre.svg` | Logo principal (fond sombre) |
| `branding/logo/binixx-logo-vertical*.svg` | Logo empilé : écran de démarrage, affiches |
| `branding/logo/binixx-symbole*.svg` | Symbole seul ; `-petit` (une entaille) sous 24 px, `-mono` en une couleur |
| `branding/logo/binixx-avatar.svg` | Avatar du projet (GitHub, réseaux) |

Dans l'image :

| Emplacement | Contenu |
| --- | --- |
| `/usr/share/icons/hicolor/scalable/apps/binixx.svg` | Icône `binixx` : bouton Démarrer, « À propos », `LOGO` de `os-release` |
| `/usr/share/wallpapers/BinixX/` | Fond d'écran « Le marcheur de l'aube » (bureau, verrouillage, connexion), version claire et sombre, en 1080p et 4K |
| `/usr/share/plymouth/themes/binixx/` | Écran de démarrage : logo et roue de chargement (`branding/roue_demarrage.py`) |

Sur l'ISO, `disk_config/personnaliser-iso.sh` :

- nomme le volume `BinixX-OS-44-x86_64` (nom de la clé USB) au lieu de `Fedora-S-dvd-x86_64-44`, dans
  les menus de démarrage aussi ;
- donne à l'installeur (Anaconda) le logo et les couleurs de `branding/installeur/`, par
  `images/product.img`, qu'il applique au démarrage par-dessus les logos Fedora.

## Le fond d'écran

Le fond de Windows XP (« Bliss ») se reconnaît au premier regard parce qu'il n'appartient qu'à Windows. BinixX OS a le sien,
« Le marcheur de l'aube » : un horizon de planète vu de l'espace, un ciel étoilé en bleu BinixX OS avec la Voie lactée, et **un homme seul qui marche
vers l'aube**, tout petit, réduit à sa forme : une silhouette sombre, sans visage ni détail, sur la courbure de la
planète, devant un soleil qui se lève. Une écharpe flotte derrière lui, un clin d'œil au Petit Prince de
Saint-Exupéry : l'esprit y est (un voyageur minuscule dans l'immensité), mais le dessin est le nôtre. L'ambre de
l'aube est la seule touche chaude de l'identité (voir [Couleurs](#couleurs)).

- **Original** : tout est calculé par `branding/fond_ecran.py` (bruit fractal, étoiles, lumière, silhouette dessinée
  en formes simples), sans image tierce : **aucune licence à citer**, mêmes droits que le logo. Le résultat est
  identique à chaque exécution (graine fixe) ; chaque fond est calculé en 4K puis réduit, donc toutes les tailles
  montrent le même ciel.
- **Une silhouette, pas un portrait** : de profil, de la tête (avec le nez et le menton) aux pieds, en pleine
  enjambée, bras qui se balancent. Elle fait 6,8 % de la hauteur de l'écran (73 px en 1080p) : assez grande pour qu'on
  la voie dès l'ouverture de la session, assez petite pour rester « au loin » et donner une échelle au ciel.
- **Deux versions** : `images/` pour le thème BinixX OS (clair), `images_dark/` pour BinixX OS sombre (ciel plus sombre,
  nébuleuse plus discrète). Le bureau, l'écran de verrouillage et l'écran de connexion utilisent le même dossier.
- **Pas de logo dans le fond** : la gemme reste sur la barre, l'écran de démarrage et l'installeur ; le fond mise sur
  une image qu'on retient sans elle.
- **Écartés** : des photos de la NASA, libres de droits avec crédit (« Falaises cosmiques » du télescope James Webb, lever
  de Terre d'Artemis II). Spectaculaires, mais on les attribuerait à la NASA, pas à BinixX OS. Elles restent possibles
  comme fonds d'écran optionnels, avec leur crédit (NASA, ESA, CSA, STScI) et sans laisser croire que la NASA cautionne
  BinixX OS.
- **Régénérer** : `python3 branding/fond_ecran.py 3840 fond.png clair` pour un essai (`nuit` pour le thème
  sombre) ; `branding/generer.py` écrit les fichiers de l'image. Dépendances : `pip install numpy scipy pillow`.
  Les tests (`tests/branding`) vérifient le déterminisme, la silhouette (une seule forme, proportions humaines, deux
  jambes en enjambée, pieds posés sur l'horizon) et les fichiers produits.

## Couleurs

Le **bleu BinixX** a été choisi en novembre 2026, sur maquette, entre un bleu ciel et un azur doux : un **pastel** et sa
**nuance forte**. Le pastel seul ne permet pas d'écrire en blanc dessus : la nuance forte, même teinte en plus foncé, porte les
boutons, les liens et la sélection (texte blanc lisible à 4,7:1) ; le pastel porte le reste (texte foncé lisible à 10,6:1).

| Nom | Valeur | Usage |
| --- | --- | --- |
| Bleu BinixX pastel | `#ADCFFB` | Survols, focus, barres de progression, contour du pointeur, liens sur fond sombre |
| Bleu BinixX fort | `#0C6EEE` | Boutons, liens sur fond clair, sélection (Aube et Nuit), accent de Kvantum, page ouverte du Centre |
| Dégradé de la gemme | `#BBD7FC` → `#ADCFFB` → `#0C6EEE` | Logo sur fond clair, icône du système |
| Dégradé sombre | `#D6E7FE` → `#ADCFFB` → `#3C8CF2` | Logo sur fond sombre (écran de démarrage, installeur) |
| Encre | `#0B0F1A` | Texte, fonds sombres |
| Accent clair | `#0C6EEE` (liens visités `#0A5CC8`, focus `#5D9AF4`) | Couleurs « BinixX OS clair » |
| Accent sombre | `#0C6EEE` (liens et focus `#ADCFFB`) | Couleurs « BinixX OS sombre » |

Le bleu vif `#2F5BFF` des premières versions n'est plus utilisé.

**Pointeur** : `binixx-curseurs`, blanc, plat et fin, contour au bleu pastel et ombre douce, fabriqué par
`branding/curseurs.py` (22 formes, attente animée, tailles 24 à 96 ; les formes manquantes viennent de Breeze). Le contraste
élevé garde Breeze Light, à contour sombre, le plus visible.

**Icônes d'applications** : chaque application est posée sur la même plaque **squircle** (la forme des icônes de téléphone). Si son
logo a son propre fond (carré ou rond plein : Signal, Zoom, Spotify…), la plaque prend ce fond, façon One UI ; sinon (Firefox, VLC,
GIMP…), c'est une plaque en verre teinté de la couleur principale du logo. En Nuit, les plaques sont un peu plus profondes. Le logo
est celui que l'application installe, jamais redessiné. `binixx_centre/plaques.py` les fabrique à la construction de l'image pour les
applications fournies (thèmes `binixx-os` et `binixx-os-dark`, répertoire `apps/scalable`), et le service utilisateur
`binixx-plaques` fait de même pour les applications installées ensuite (Flatpak), dans `~/.local/share/icons`, à l'ouverture de
session et à chaque installation. Les dossiers ont leur propre identité (pastel par contenu, voir
[theme-windows-11.md](theme-windows-11.md#dossiers-pastel)).

**Police de l'interface** : **Inter** (libre, OFL, paquet Fedora `rsms-inter-fonts`), nette aux petites tailles, posée dans
`/etc/xdg/kdeglobals` ; la chasse fixe reste celle du système. Le logotype garde Outfit.

Deux thèmes globaux, appariés dans Configuration du système → Thème global (bascule automatique
selon l'heure possible) : **BinixX OS** (clair, par défaut) et **BinixX OS sombre**. Même disposition :
barre des tâches flottante en haut de l'écran, aux coins arrondis, comme Zorin OS 18. Les couleurs
sont celles de Brise, avec le bleu BinixX OS comme couleur d'accent ; `build_files/build.sh` les
régénère depuis les fichiers de Brise à chaque construction de l'image.

L'**ambre** (`#FFD08A` → `#FF7A45`) n'apparaît qu'en touche, pour l'instant dans l'aube du fond d'écran. Il ne remplace
jamais le bleu.

Le nom s'écrit **BinixX OS** (B, X final et OS en majuscules), en Outfit SemiBold. Le point de chacun des deux « i » est
une petite gemme.

## Modifier le logo

Tout est généré par `branding/generer.py` : couleurs, proportions, logotype, icône, fond
d'écran et écran de démarrage. Après une modification :

```bash
pip install fonttools uharfbuzz pillow numpy scipy
python3 branding/generer.py   # Chromium ou Chrome nécessaire pour les images PNG et JPG
```

`--installeur-seulement` ne régénère que les images de l'installeur : les fonds d'écran ont un
grain aléatoire et changeraient à chaque fois.

Le pointeur se régénère à part (il ne dépend que de ses dessins et du bleu pastel) :

```bash
pip install pyside6-essentials numpy
python3 branding/curseurs.py
```

La police Outfit est fournie sous licence SIL Open Font License (`branding/police/OFL.txt`).
Le texte des logos est converti en tracés : aucune police n'est nécessaire pour les afficher.

## Où le nom « Fedora » apparaît encore

BinixX OS remplace le nom et les logos Fedora partout où l'utilisateur les voit : clé USB et
installeur, écran de démarrage, menu de démarrage du PC (entrée « BinixX OS »), menu GRUB, connexion,
bureau, « À propos ».

Restent, visibles seulement en ligne de commande ou dans les détails techniques :

| Trace | Pourquoi elle reste |
| --- | --- |
| Numéro du noyau `…fc44`, aussi dans Configuration du système → À propos (« Version du noyau ») | Changer le noyau obligerait à le recompiler et le signer nous-mêmes ; Secure Boot le refuserait |
| Dossier `EFI/fedora` sur la partition de démarrage | Les chargeurs signés pour Secure Boot (shim, GRUB) cherchent ce chemin |
| `ID=fedora`, `/etc/fedora-release`, dépôts et paquets « fedora » | Les outils de mise à jour et les logiciels s'en servent pour reconnaître la base Fedora |

Nom du système vu par l'installeur : quand on réinstalle sur un disque qui contient déjà BinixX OS, Anaconda (écran de
partitionnement) nomme le système trouvé d'après `/etc/redhat-release`, puis `os-release`. `/etc/redhat-release` était un lien vers
`fedora-release` : l'installeur affichait « Fedora Linux 44 pour x86_64 ». C'est maintenant un fichier à nous (« BinixX OS release 44 »,
comme `/etc/system-release`) ; `/etc/fedora-release` reste intact. Anaconda ajoute « Linux » au nom quand il n'en contient pas :
l'écran affiche « BinixX OS Linux 44 pour x86_64 ». Contrôlé par `tests/image` et `tests/vm` (le calcul d'Anaconda y est reproduit).

La politique de marque Fedora demande de retirer ses logos d'un système dérivé et permet de dire
qu'il est « basé sur Fedora » : c'est ce que fait BinixX OS.

Retirés du bureau par `build_files/build.sh` (et vérifiés par `tests/image/check-image.sh`) :

- les thèmes globaux « Fedora », « Fedora Dark » et « Fedora Light » ; le fond d'écran « Fedora
  Forty-Four » (le fond « par défaut » de KDE devient celui de BinixX OS) ;
- dans Firefox (paquet de Fedora) : la page d'accueil et le raccourci « Fedora Project - Start
  Page », et « Mozilla Firefox for Fedora » dans « À propos » (« pour BinixX OS ») ;
- une source d'applications « Fedora » dans Discover : seule Flathub reste.

## À vérifier avant une diffusion publique

- Recherche d'antériorité sur le nom et sur la forme du logo (marques déposées).
- Le logo évoque Windows 11 sans reprendre ses quatre carreaux : garder cette distance.
