# Explorateur BinixX

Dolphin, l'explorateur de fichiers de KDE, **épuré** : une seule ligne de boutons, les fichiers en grandes icônes, pas de barre d'état.
Il reste l'explorateur de fichiers de BinixX OS (Windows + E) : il sait déjà parler aux dossiers partagés Windows, aux téléphones, aux
archives et à la corbeille, et KDE le met à jour. Seule sa présentation change : l'ouverture par défaut de Dolphin était jugée trop
chargée (deux barres, une vue en liste serrée, une barre d'état).

## Ce qu'on voit à l'ouverture

| Élément | Où |
| --- | --- |
| Précédent, Suivant, Dossier parent | Les trois premiers boutons de la ligne, à icône seule (le nom s'affiche au survol) |
| Barre d'adresse | Le chemin cliquable, au milieu (cliquer dans la zone vide pour saisir un chemin) |
| Rechercher | Loupe (Ctrl + F) |
| Affichage | Bouton à flèche : taille des icônes, liste, détails, aperçus, fichiers cachés (« Configuration des affichages ») |
| Menu | Les trois traits : tout le reste (Nouvelle fenêtre, Créer nouveau, Trier par, Réglages…) |
| Fichiers | Grandes icônes (niveau de zoom 3, comme les « icônes moyennes » de Windows) |
| Volet de gauche | Panneau « Emplacements » (F9 pour l'afficher ou le masquer) |
| Information au survol d'un fichier | Fiche d'information au survol |

Les actions qu'on faisait avec des boutons restent à portée : **clic droit** (Couper, Copier, Coller, Renommer, Déplacer dans la corbeille,
Créer nouveau → dossier, document texte, classeur, présentation), ou **Ctrl + X, Ctrl + C, Ctrl + V, F2, Suppr**. Pour trier : menu →
Trier par, ou clic droit dans le dossier → Trier par. Pour remettre des boutons : clic droit sur la barre → « Configurer les barres d'outils ».

## Comment c'est fait

Dolphin range sa disposition à deux endroits que KDE ne lit que dans le **dossier personnel** de chaque compte. BinixX OS les place donc
dans `/etc/skel`, d'où `useradd` (donc Plasma Setup et l'installeur) les copie à la création d'un compte :

| Fichier (dans le dossier personnel) | Rôle |
| --- | --- |
| `.local/share/kxmlgui5/dolphin/dolphinui.rc` | La barre d'outils (sept boutons) et la priorité de chacun (icône seule) |
| `.local/share/dolphin/view_properties/global/.directory` | Vue par défaut : icônes (`ViewMode=0`, `ZoomLevel=3`) ; si on passe en vue « détails », colonnes Nom, Modifié le, Type, Taille |

Les réglages qui valent pour tous les comptes sont dans `/etc/xdg/dolphinrc` (pas de barre d'état, information au survol, lignes compactes à petites
icônes et sans flèche d'arborescence pour qui passe en vue « détails ») ; KDE les lit derrière ceux de l'utilisateur, qui reste prioritaire.

### Pourquoi une mise à jour de Dolphin n'écrase rien

`dolphinui.rc` porte volontairement la **version 1**, très inférieure à celle de Dolphin. C'est le mécanisme que KDE (kxmlgui) prévoit
pour les réglages d'un utilisateur : il garde le fichier de Dolphin, avec ses menus, et y reprend seulement la barre d'outils et les
propriétés des boutons du fichier du compte. Si Dolphin ajoute un menu ou un bouton, il apparaît ; notre barre, elle, ne bouge pas.
Un nom de bouton que Dolphin ne connaît plus est ignoré sans erreur : le test de l'image vérifie donc que chaque nom existe encore.

## Pour un compte déjà créé

Une mise à jour de BinixX OS ne change pas les comptes existants (elle ne touche pas aux dossiers personnels). Pour recevoir
l'Explorateur BinixX sur un compte existant, **fermer Dolphin** puis, dans un terminal :

```
/usr/libexec/binixx/binixx-explorateur appliquer
```

Rien n'est écrasé : si un fichier existe déjà, il est conservé et la commande le dit. `appliquer --forcer` le remplace après l'avoir
rangé dans `~/.local/share/binixx/sauvegardes/`. `binixx-explorateur retablir` remet Dolphin comme KDE le livre (mêmes sauvegardes) ;
`binixx-explorateur etat` dit si l'Explorateur BinixX est en place.

## Ce que cela ne fait pas

- **Pas de colonnes à la manière du Finder de macOS** : Dolphin les a retirées avec KDE 4.8 (le code était devenu trop difficile à maintenir) et
  la recherche n'a trouvé aucun explorateur Qt maintenu qui les propose. C'est un point de l'ambiance macOS, à étudier séparément.
- **Pas de barre d'état** : le nombre d'éléments sélectionnés et la place libre ne sont plus affichés. Pour les retrouver : menu → Configurer
  Dolphin (réglage de la barre d'état) ou, en une ligne, `ShowStatusBar=1` dans `~/.config/dolphinrc` (2 : aucune, 1 : pleine largeur).
- **Le panneau de gauche** garde les groupes de KDE (« Emplacements », « Distant », « Récent ») : on ne peut pas les renommer « Accès rapide »
  ou « Ce PC » sans traduire Dolphin.
- **Icônes de Breeze**, comme le reste du bureau, tant que le thème d'icônes n'est pas changé.

## Pourquoi pas un autre explorateur

Quatre explorateurs ont été comparés sur la même image de Fedora 44 : Dolphin (KDE), Nautilus (GNOME), COSMIC Files et Spacedrive. Nautilus et
COSMIC Files tirent chacun leur bureau, leurs réglages et leurs services ; Spacedrive est une version alpha, sous licence AGPL, sans paquet
officiel. Dolphin épuré donne l'allure la plus proche de celle des explorateurs de Windows 11 et de macOS, sans rien ajouter au système.

## Tests

- **Image** (`tests/image/checks.d/86-explorateur.sh`) : fichiers présents, XML valide, version 1, une seule barre et ses sept boutons dans l'ordre,
  chaque nom de bouton présent dans Dolphin ou dans les actions standard de KDE, clés de réglage encore connues de Dolphin, vue par défaut,
  `dolphinrc` lu sans fichier utilisateur, compte créé par `useradd`, commande `binixx-explorateur` (appliquer, conserver, remplacer avec
  sauvegarde, rétablir).
- **VM** (`tests/vm/checks.d/86-explorateur.sh`) : le compte de l'installation a reçu les fichiers de `/etc/skel` ; Dolphin s'ouvre dans la
  vraie session et KDE réécrit alors le fichier du compte avec la version de Dolphin, ses menus **et** notre barre (c'est la preuve que
  la fusion a eu lieu) ; une capture d'écran (`explorateur.png`) est jointe aux journaux du test.
