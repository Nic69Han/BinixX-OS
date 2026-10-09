# Style Windows 11 (Win11OS KDE)

Les ambiances **Aube** (clair) et **Nuit** (sombre) prennent l'allure de Windows 11 : fenêtres à angles arrondis et boutons à droite,
boutons, cases et barres de défilement plats, barre des tâches et fenêtres de Plasma translucides. Ce style vient du projet
**Win11OS KDE** de yeyushengfan258 ([GitHub](https://github.com/yeyushengfan258/Win11OS-kde), licence GNU GPL version 3), repris
**sans modification** ; BinixX OS y met ses couleurs, son fond d'écran et sa disposition.

## Ce qui est appliqué

| Élément | D'où il vient | Où il est dans l'image |
| --- | --- | --- |
| Barre de titre des fenêtres (angles arrondis, réduire, agrandir, fermer) | Win11OS KDE, thème Aurorae `Win11OS-light` / `Win11OS-dark` | `/usr/share/aurorae/themes/` |
| Boutons, cases, barres de défilement, onglets des applications | Win11OS KDE, thème Kvantum `Win11OS-light` / `Win11OS-dark` | `/usr/share/Kvantum/` (paquet Fedora `kvantum`) |
| Barre des tâches, fenêtres de Plasma, bulles, icônes de la zone de notification | Win11OS KDE, thème Plasma `Win11OS-light` / `Win11OS-dark` | `/usr/share/plasma/desktoptheme/` |
| **Dossiers jaunes** (et les dossiers Documents, Images, Musique… en jaune aussi) | BinixX OS, à partir des icônes de Breeze | thèmes d'icônes `binixx-os` et `binixx-os-dark` (`/usr/share/icons/`) |
| Couleurs (accent bleu BinixX OS, texte, sélection) | BinixX OS | `BinixXClair`, `BinixXSombre` |
| Fond d'écran « Le marcheur de l'aube », disposition du panneau, logo du bouton Démarrer | BinixX OS | inchangés |
| Pointeur blanc, double-clic | BinixX OS | inchangés |

Les boutons des fenêtres sont placés comme sous Windows : l'icône de l'application à gauche, réduire, agrandir et fermer à droite.

### Ce qui n'est pas repris du projet

- **Ses fonds d'écran** : des dessins proches du fond de Windows 11. BinixX OS garde le sien.
- **Son écran de connexion** : il remplacerait celui de Plasma ; il se jugerait sur un test de connexion que l'image ne fait pas encore.
- **Ses thèmes globaux et ses couleurs** : remplacés par ceux de BinixX OS (`org.binixx.desktop`, `org.binixx.dark.desktop`, couleurs
  `BinixXClair` et `BinixXSombre`), qui posent les thèmes ci-dessus.
- **Le thème d'icônes « Win11 »** du même auteur (une cinquantaine de Mo de sources) : ses icônes imitent de près celles des applications de
  Microsoft (Explorateur de fichiers, Photos, Xbox, Visual Studio…), ce que BinixX OS préfère ne pas distribuer. Les dossiers jaunes
  sont faits autrement (voir plus bas) ; le reste des icônes est celui de Breeze.
- **Le menu Démarrer en grille** du même auteur : un autre projet, non repris pour l'instant (voir « Et ensuite »).

## Dossiers jaunes

Dans Breeze, un dossier prend la couleur d'accentuation du bureau : bleu BinixX OS, donc des dossiers bleus. Windows a des dossiers jaunes.
`build_files/icones-dossiers-jaunes.py` fabrique, à chaque construction de l'image, deux thèmes d'icônes à partir de **Breeze tel qu'il
est dans l'image** :

- `binixx-os` (Aube) : hérite de Breeze ; **près de 200 dossiers** copiés avec une seule modification, la couleur du corps du dossier (jaune
  `#f2cb40` de Breeze, `#fdbc4b` aux tailles 16, 22 et 24 pixels), plus les liens qui y mènent (le type « dossier », les dossiers de
  l'application…). Documents, Téléchargements, Musique, Images, Vidéos… gardent leur pictogramme, sur fond jaune.
- `binixx-os-dark` (Nuit) : hérite de Breeze sombre ; ses dossiers sont ceux de `binixx-os` (liens), le reste vient de Breeze sombre.
- Les pictogrammes dans les dossiers gardent leur couleur sombre dans les deux thèmes (l'identifiant de la feuille de style du dessin
  est retiré pour que le bureau ne les recolore pas : en blanc sur du jaune, ils disparaîtraient).
- Si Breeze change le dessin de ses dossiers, la construction **échoue** (aucun dossier à la couleur d'accent trouvé) au lieu de livrer
  des dossiers redevenus bleus sans le dire. Les licences de Breeze (LGPL-3.0 ou plus, CC-BY-SA-4.0) sont copiées dans le thème avec une note
  disant ce qui a été modifié.
- **Contraste élevé** garde les icônes de Breeze sombre : son contraste se vérifie sur ses couleurs noir, blanc et jaune.
- Pour revenir aux dossiers bleus : Configuration du système → Apparence et comportement → Icônes → Breeze.

## Comment ça se règle

- **Aube** et **Nuit** (Paramètres → Personnalisation → Thèmes : clair ou sombre) posent le thème global correspondant : style
  `kvantum`, décoration Aurorae, thème Plasma. Les deux thèmes globaux sont dans `usr/share/plasma/look-and-feel/org.binixx.desktop`
  et `org.binixx.dark.desktop` (fichier `contents/defaults`).
- **Contraste élevé** garde l'ancien style (Breeze) : il suit à la lettre les couleurs noir, blanc et jaune, alors que Kvantum
  dessine ses propres couleurs. Il a donc son propre thème global, `org.binixx.contraste.desktop`.
- **Le thème Kvantum suit les couleurs.** Kvantum range son thème dans un fichier à part (`~/.config/Kvantum/kvantum.kvconfig`) que
  Plasma ne connaît pas : sans précaution, des couleurs sombres sous un thème Kvantum clair rendraient le texte illisible. Trois
  mécanismes les gardent d'accord :
  1. un compte neuf reçoit le thème clair de `/etc/skel/.config/Kvantum/kvantum.kvconfig` ;
  2. `binixx-ambiance appliquer` pose le thème Kvantum de l'ambiance **avant** de changer le thème global, et le remet d'accord si le
     bureau ne répond pas ;
  3. un service de chaque session (`binixx-kvantum.path` surveille `~/.config/kdeglobals`, `binixx-kvantum.service` lance
     `binixx-ambiance kvantum`) refait la même chose chaque fois que les couleurs changent, même depuis Configuration du système,
     et à l'ouverture de session (comptes existants).
  Un autre thème Kvantum choisi à la main (Kvantum Manager) n'est jamais remplacé, et des couleurs qui ne sont pas celles de
  BinixX OS (Contraste élevé, couleurs de KDE) ne touchent à rien.

## Pour un compte déjà créé

Une mise à jour ne change pas le bureau d'un compte existant (ses réglages sont dans son dossier personnel). Pour recevoir le style :
**Paramètres → Personnalisation → Thèmes : clair ou sombre → Aube** (ou Nuit). Pour revenir à l'ancien style : Configuration du système →
Apparence et comportement → Thème global → **Breeze**.

## Licences

Les fichiers de Win11OS KDE (`aurorae`, `Kvantum`, `plasma/desktoptheme`) sont sous **GNU GPL version 3** : leur texte, la liste des
auteurs et l'adresse exacte de la source (version et empreinte du commit) sont fournis dans l'image, dans
`/usr/share/licenses/binixx-win11os-kde/` (`COPYING`, `AUTHORS`, `SOURCE.txt`). Ces fichiers sont des **copies sans modification** (les dossiers jaunes, eux, sont dérivés de Breeze : voir plus haut) ;
le code et les réglages propres à BinixX OS restent sous licence Apache 2.0. Le test de l'image vérifie la présence de la licence,
des auteurs et de la source, et l'absence des fonds d'écran du projet.

## Limites connues

- **Kvantum est fragile par nature** : c'est un style tiers pour Qt, qui doit suivre les versions de Qt et de Plasma. L'image fige
  les versions, et le test VM pose Aube, Nuit et Contraste élevé dans une vraie session et photographie le résultat à chaque
  version ; si une mise à jour de Fedora casse le style, le test le dit avant que `stable` ne bouge.
- **Applications GTK** (Firefox, Thunderbird, applications Flatpak GTK…) : elles gardent leur propre dessin ; le style de Kvantum
  ne s'applique qu'aux applications Qt.
- **Transparence** : le style rend les fenêtres translucides et demande à KWin de flouter le fond (effet « flou » activé par défaut dans
  Plasma). Sur un PC sans accélération graphique, la translucidité est moins nette.
- **Dossiers** : jaunes, mais au dessin de Breeze (plats, avec un onglet plus foncé), pas celui, dégradé, de l'Explorateur de Windows 11.
  Les autres icônes (applications, fichiers) sont celles de Breeze.

## Et ensuite

- Des icônes plus proches de celles de Windows 11 : les icônes Fluent de Microsoft (licence MIT,
  [fluentui-system-icons](https://github.com/microsoft/fluentui-system-icons)) en thème partiel qui hérite de BinixX OS ; leurs pictogrammes d'interface sont
  libres de réutilisation, contrairement aux icônes d'applications de Microsoft.
- Un menu Démarrer en grille d'applications épinglées.
- L'écran de connexion du projet, avec un test de connexion en VM.

## Tests

- **Image** (`tests/image/checks.d/82-theme-windows-11.sh`) : `kvantum` installé et son style Qt 6 présent ; les trois thèmes de chaque
  variante (Aurorae, Kvantum, Plasma) complets ; licence, auteurs et source ; fonds d'écran et écran de connexion du projet absents ;
  chaque thème global pose des noms qui existent vraiment ; Contraste élevé n'utilise ni Kvantum ni Aurorae ; thème Kvantum de
  `/etc/skel` ; service et surveillance activés ; `binixx-ambiance kvantum` suit les couleurs sans remplacer un autre thème choisi.
  Les tests Python de `tests/image/centre/test_ambiances.py` couvrent la logique (thème par couleurs, fichier réécrit sans perdre les
  réglages par application, thème choisi à la main respecté, ordre dans `appliquer`).
- Dossiers jaunes, dans les mêmes tests de l'image : thèmes `binixx-os` et `binixx-os-dark` (héritage, jaune de chaque taille de 16 à 96 pixels,
  dossiers Documents, Téléchargements, Musique, Images et Vidéos, type « dossier », liens du thème sombre, licence) ; chaque thème global
  nomme un thème d'icônes qui existe ; Contraste élevé reste sur Breeze sombre.
- **VM** (`tests/vm/checks.d/82-theme-windows-11.sh`) : le compte de l'installation a le thème clair ; la surveillance tourne ; un
  changement de couleurs dans `kdeglobals` fait changer le thème Kvantum tout seul ; pour chaque ambiance, le style, la
  décoration des fenêtres, le thème Plasma, le thème d'icônes et le thème Kvantum relus dans la session sont ceux annoncés. Captures d'écran jointes aux journaux : `theme-aube.png`,
  `theme-nuit.png`, `theme-contraste.png` (Dolphin ouvert) et `theme-*-menu.png` (menu de démarrage ouvert).
