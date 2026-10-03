# Identité visuelle

Le logo de NicOS est une **gemme** : un losange aux angles doux, fendu de deux entailles
diagonales. Il reprend le losange à lames bleues et noires de l'avatar GitHub du projet,
dans un style plus moderne (dégradé, lumière venant du haut), proche de Windows 11.

## Fichiers

| Fichier | Usage |
| --- | --- |
| `branding/logo/nicos-logo-horizontal.svg` | Logo principal (fond clair) |
| `branding/logo/nicos-logo-horizontal-fond-sombre.svg` | Logo principal (fond sombre) |
| `branding/logo/nicos-logo-vertical*.svg` | Logo empilé : écran de démarrage, affiches |
| `branding/logo/nicos-symbole*.svg` | Symbole seul ; `-petit` (une entaille) sous 24 px, `-mono` en une couleur |
| `branding/logo/nicos-avatar.svg` | Avatar du projet (GitHub, réseaux) |

Dans l'image :

| Emplacement | Contenu |
| --- | --- |
| `/usr/share/icons/hicolor/scalable/apps/nicos.svg` | Icône `nicos` : bouton Démarrer, « À propos », `LOGO` de `os-release` |
| `/usr/share/wallpapers/NicOS/` | Fond d'écran « Lever de gemme » (bureau, verrouillage, connexion), version claire et sombre, en 1080p et 4K |
| `/usr/share/plymouth/themes/nicos/` | Écran de démarrage |

Sur l'ISO, `disk_config/personnaliser-iso.sh` :

- nomme le volume `NicOS-44-x86_64` (nom de la clé USB) au lieu de `Fedora-S-dvd-x86_64-44`, dans
  les menus de démarrage aussi ;
- donne à l'installeur (Anaconda) le logo et les couleurs de `branding/installeur/`, par
  `images/product.img`, qu'il applique au démarrage par-dessus les logos Fedora.

## Le fond d'écran : « Lever de gemme »

Le fond de Windows XP (« Bliss ») se reconnaît au premier regard parce qu'il n'appartient qu'à Windows. NicOS a le sien :
un horizon de planète vu de l'espace, un ciel étoilé en bleu NicOS avec la Voie lactée, et **la gemme du logo qui se
lève comme un soleil**, une aube d'ambre qui court sur l'horizon. L'ambre est la seule touche chaude de l'identité
(voir [Couleurs](#couleurs)).

- **Original** : tout est calculé par `branding/lever_de_gemme.py` (bruit fractal, étoiles, lumière, gemme dessinée
  d'après `generer.py`), sans image tierce : **aucune licence à citer**, mêmes droits que le logo. Le résultat est
  identique à chaque exécution (graine fixe) ; chaque fond est calculé en 4K puis réduit, donc toutes les tailles
  montrent le même ciel.
- **Deux versions** : `images/` pour le thème NicOS (clair), `images_dark/` pour NicOS sombre (ciel plus sombre,
  nébuleuse plus discrète). Le bureau, l'écran de verrouillage et l'écran de connexion utilisent le même dossier.
- **Écartés** : des photos de la NASA, libres de droits avec crédit (« Falaises cosmiques » du télescope James Webb, lever
  de Terre d'Artemis II). Spectaculaires, mais on les attribuerait à la NASA, pas à NicOS. Elles restent possibles
  comme fonds d'écran optionnels, avec leur crédit (NASA, ESA, CSA, STScI) et sans laisser croire que la NASA cautionne
  NicOS.
- **Régénérer** : `python3 branding/lever_de_gemme.py 3840 fond.png clair` pour un essai (`nuit` pour le thème
  sombre) ; `branding/generer.py` écrit les fichiers de l'image. Dépendances : `pip install numpy scipy pillow`.
  Les tests (`tests/branding`) vérifient le déterminisme, la gemme et les fichiers produits.

## Couleurs

| Nom | Valeur | Usage |
| --- | --- | --- |
| Dégradé NicOS | `#5FB2FF` → `#2F5BFF` → `#1A26C9` | Gemme sur fond clair |
| Dégradé sombre | `#8CCBFF` → `#5A7DFF` → `#3A3FE0` | Gemme sur fond sombre |
| Bleu NicOS | `#2F5BFF` | Couleur unie quand le dégradé n'est pas possible |
| Encre | `#0B0F1A` | Texte, fonds sombres |
| Accent clair | `#2F5BFF` (liens `#2248E0`) | Sélection, survol, focus, dans les couleurs « NicOS clair » |
| Accent sombre | `#5A7DFF` (liens `#8CAAFF`) | Même rôle dans « NicOS sombre » |

Deux thèmes globaux, appariés dans Configuration du système → Thème global (bascule automatique
selon l'heure possible) : **NicOS** (clair, par défaut) et **NicOS sombre**. Même disposition :
barre des tâches flottante en haut de l'écran, aux coins arrondis, comme Zorin OS 18. Les couleurs
sont celles de Brise, avec le bleu NicOS comme couleur d'accent ; `build_files/build.sh` les
régénère depuis les fichiers de Brise à chaque construction de l'image.

L'**ambre** (`#FFD08A` → `#FF7A45`) n'apparaît qu'en touche, pour l'instant dans l'aube du fond d'écran. Il ne remplace
jamais le bleu.

Le nom s'écrit **NicOS** (N et OS en majuscules), en Outfit SemiBold. Le point du « i » est
une petite gemme.

## Modifier le logo

Tout est généré par `branding/generer.py` : couleurs, proportions, logotype, icône, fond
d'écran et écran de démarrage. Après une modification :

```bash
pip install fonttools uharfbuzz pillow
python3 branding/generer.py   # Chromium ou Chrome nécessaire pour les images PNG et JPG
```

`--installeur-seulement` ne régénère que les images de l'installeur : les fonds d'écran ont un
grain aléatoire et changeraient à chaque fois.

La police Outfit est fournie sous licence SIL Open Font License (`branding/police/OFL.txt`).
Le texte des logos est converti en tracés : aucune police n'est nécessaire pour les afficher.

## Où le nom « Fedora » apparaît encore

NicOS remplace le nom et les logos Fedora partout où l'utilisateur les voit : clé USB et
installeur, écran de démarrage, menu de démarrage du PC (entrée « NicOS »), menu GRUB, connexion,
bureau, « À propos ».

Restent, visibles seulement en ligne de commande ou dans les détails techniques :

| Trace | Pourquoi elle reste |
| --- | --- |
| Numéro du noyau `…fc44`, aussi dans Configuration du système → À propos (« Version du noyau ») | Changer le noyau obligerait à le recompiler et le signer nous-mêmes ; Secure Boot le refuserait |
| Dossier `EFI/fedora` sur la partition de démarrage | Les chargeurs signés pour Secure Boot (shim, GRUB) cherchent ce chemin |
| `ID=fedora`, `/etc/fedora-release`, dépôts et paquets « fedora » | Les outils de mise à jour et les logiciels s'en servent pour reconnaître la base Fedora |

La politique de marque Fedora demande de retirer ses logos d'un système dérivé et permet de dire
qu'il est « basé sur Fedora » : c'est ce que fait NicOS.

Retirés du bureau par `build_files/build.sh` (et vérifiés par `tests/image/check-image.sh`) :

- les thèmes globaux « Fedora », « Fedora Dark » et « Fedora Light » ; le fond d'écran « Fedora
  Forty-Four » (le fond « par défaut » de KDE devient celui de NicOS) ;
- dans Firefox (paquet de Fedora) : la page d'accueil et le raccourci « Fedora Project - Start
  Page », et « Mozilla Firefox for Fedora » dans « À propos » (« pour NicOS ») ;
- une source d'applications « Fedora » dans Discover : seule Flathub reste.

## À vérifier avant une diffusion publique

- Recherche d'antériorité sur le nom et sur la forme du logo (marques déposées).
- Le logo évoque Windows 11 sans reprendre ses quatre carreaux : garder cette distance.
