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
| `/usr/share/wallpapers/NicOS/` | Fond d'écran (bureau, verrouillage, connexion), version claire et sombre |
| `/usr/share/plymouth/themes/nicos/` | Écran de démarrage |

Sur l'ISO, `disk_config/personnaliser-iso.sh` :

- nomme le volume `NicOS-44-x86_64` (nom de la clé USB) au lieu de `Fedora-S-dvd-x86_64-44`, dans
  les menus de démarrage aussi ;
- donne à l'installeur (Anaconda) le logo et les couleurs de `branding/installeur/`, par
  `images/product.img`, qu'il applique au démarrage par-dessus les logos Fedora.

## Couleurs

| Nom | Valeur | Usage |
| --- | --- | --- |
| Dégradé NicOS | `#5FB2FF` → `#2F5BFF` → `#1A26C9` | Gemme sur fond clair |
| Dégradé sombre | `#8CCBFF` → `#5A7DFF` → `#3A3FE0` | Gemme sur fond sombre |
| Bleu NicOS | `#2F5BFF` | Couleur unie quand le dégradé n'est pas possible |
| Encre | `#0B0F1A` | Texte, fonds sombres |

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
| Numéro du noyau `…fc44` | Changer le noyau obligerait à le recompiler et le signer nous-mêmes ; Secure Boot le refuserait |
| Dossier `EFI/fedora` sur la partition de démarrage | Les chargeurs signés pour Secure Boot (shim, GRUB) cherchent ce chemin |
| `ID=fedora`, `/etc/fedora-release`, dépôts et paquets « fedora » | Les outils de mise à jour et les logiciels s'en servent pour reconnaître la base Fedora |

La politique de marque Fedora demande de retirer ses logos d'un système dérivé et permet de dire
qu'il est « basé sur Fedora » : c'est ce que fait NicOS.

## À vérifier avant une diffusion publique

- Recherche d'antériorité sur le nom et sur la forme du logo (marques déposées).
- Le logo évoque Windows 11 sans reprendre ses quatre carreaux : garder cette distance.
