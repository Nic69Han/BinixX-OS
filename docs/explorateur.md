# Explorateur BinixX

Dolphin, l'explorateur de fichiers de KDE, préréglé pour ressembler à l'**Explorateur de fichiers de Windows 11** : mêmes boutons
aux mêmes endroits, même vue « détails ». On garde Dolphin plutôt que d'écrire ou d'installer un autre explorateur : il sait déjà
parler aux dossiers partagés Windows, aux téléphones, aux archives et à la corbeille, et KDE le met à jour.

## Ce qu'on voit à l'ouverture

| Dans l'Explorateur de Windows 11 | Dans BinixX OS |
| --- | --- |
| Précédent, Suivant, Dossier parent, Actualiser | Les quatre premiers boutons de la première ligne |
| Barre d'adresse (chemin cliquable), Rechercher | Barre d'adresse de Dolphin (cliquer dans la zone vide pour saisir un chemin), bouton de recherche (Ctrl + F) |
| **Nouveau ▾** | **Créer nouveau** : dossier, document texte, classeur, présentation (vierges, au format Microsoft Office : voir [migration-windows.md](migration-windows.md)) |
| Couper, Copier, Coller, Renommer, Supprimer | Cinq boutons à icône seule (le nom s'affiche au survol) ; « Supprimer » envoie à la corbeille |
| **Trier ▾**, **Afficher ▾** | **Trier par**, **Configuration des affichages** (taille des icônes, liste, détails, aperçus, fichiers cachés) |
| Colonnes Nom, Modifié le, Type, Taille | Mêmes colonnes, dans le même ordre |
| Volet de navigation | Panneau « Emplacements » à gauche (F9 pour l'afficher ou le masquer) |
| Barre d'état « 12 éléments » | Barre d'état sur toute la largeur, avec le curseur de taille |
| Information au survol d'un fichier | Fiche d'information au survol |

La **première ligne** porte la navigation et l'adresse ; la **seconde**, appelée barre de commandes comme sous Windows, porte les
actions sur les fichiers. Un clic droit sur une barre → « Configurer les barres d'outils » permet de changer les boutons.

## Comment c'est fait

Dolphin range sa disposition à deux endroits que KDE ne lit que dans le **dossier personnel** de chaque compte. BinixX OS les place donc
dans `/etc/skel`, d'où `useradd` (donc Plasma Setup et l'installeur) les copie à la création d'un compte :

| Fichier (dans le dossier personnel) | Rôle |
| --- | --- |
| `.local/share/kxmlgui5/dolphin/dolphinui.rc` | Les deux barres d'outils et la priorité de chaque bouton (icône seule ou icône et texte) |
| `.local/share/dolphin/view_properties/global/.directory` | Vue « détails » par défaut, colonnes Nom, Modifié le, Type, Taille |

Les réglages qui valent pour tous les comptes sont dans `/etc/xdg/dolphinrc` (barre d'état pleine largeur, information au survol, curseur
de taille, lignes compactes à petites icônes et sans flèche d'arborescence dans la vue « détails ») ; KDE les lit derrière ceux de l'utilisateur, qui reste prioritaire.

### Pourquoi une mise à jour de Dolphin n'écrase rien

`dolphinui.rc` porte volontairement la **version 1**, très inférieure à celle de Dolphin. C'est le mécanisme que KDE (kxmlgui) prévoit
pour les réglages d'un utilisateur : il garde le fichier de Dolphin, avec ses menus, et y reprend seulement les barres d'outils et les
propriétés des boutons du fichier du compte. Si Dolphin ajoute un menu ou un bouton, il apparaît ; nos barres, elles, ne bougent pas.
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
- **Icônes de Breeze**, comme le reste du bureau. Des icônes dans le style de Windows 11 (les Fluent UI System Icons de Microsoft, sous
  licence MIT) viendront dans une étape suivante.
- **Un seul clic ouvre un fichier**, comme partout dans KDE ; Windows demande un double-clic. Réglage : Configuration du système → Comportement de
  l'espace de travail → Comportement général. Non modifié ici : il touche aussi le bureau et toutes les applications KDE.
- Les titres des groupes du panneau de gauche (« Emplacements », « Appareils »…) sont ceux de KDE : on ne peut pas les renommer
  « Accès rapide » ou « Ce PC » sans traduire Dolphin.

## Tests

- **Image** (`tests/image/checks.d/86-explorateur.sh`) : fichiers présents, XML valide, version 1, les deux barres et leurs boutons, chaque
  nom de bouton présent dans Dolphin ou dans les actions standard de KDE, vue par défaut, `dolphinrc` lu sans fichier utilisateur, compte
  créé par `useradd`, commande `binixx-explorateur` (appliquer, conserver, remplacer avec sauvegarde, rétablir).
- **VM** (`tests/vm/checks.d/86-explorateur.sh`) : le compte de l'installation a reçu les fichiers de `/etc/skel` ; Dolphin s'ouvre dans la
  vraie session et KDE réécrit alors le fichier du compte avec la version de Dolphin, ses menus **et** nos deux barres (c'est la preuve que
  la fusion a eu lieu) ; une capture d'écran (`explorateur.png`) est jointe aux journaux du test.
