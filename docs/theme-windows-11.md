# Style Windows 11 (Win11OS KDE)

Les ambiances **Aube** (clair) et **Nuit** (sombre) prennent l'allure de Windows 11 : fenêtres à angles arrondis et boutons à droite,
boutons, cases et barres de défilement plats, barre des tâches et menus de Plasma dans le style de Windows 11. Ce style vient du projet
**Win11OS KDE** de yeyushengfan258 ([GitHub](https://github.com/yeyushengfan258/Win11OS-kde), licence GNU GPL version 3), repris
**sans modification** ; BinixX OS y met ses couleurs, son fond d'écran et sa disposition.

## Ce qui est appliqué

| Élément | D'où il vient | Où il est dans l'image |
| --- | --- | --- |
| Barre de titre des fenêtres (angles arrondis, réduire, agrandir, fermer) | Win11OS KDE, thème Aurorae `Win11OS-light` / `Win11OS-dark` | `/usr/share/aurorae/themes/` |
| Boutons, cases, barres de défilement, onglets des applications | Win11OS KDE, thème Kvantum, en **variante opaque** `BinixX-Win11-light` / `BinixX-Win11-dark` | `/usr/share/Kvantum/` (paquet Fedora `kvantum`) |
| Barre des tâches, menu de démarrage, bulles, icônes de la zone de notification | Win11OS KDE, thème Plasma, en **verre adaptatif** `BinixX-Win11-light` / `BinixX-Win11-dark` (verre dépoli avec le flou, opaque sans) | `/usr/share/plasma/desktoptheme/` |
| **Dossiers jaunes** (et les dossiers Documents, Images, Musique… en jaune aussi) | BinixX OS, à partir des icônes de Breeze | thèmes d'icônes `binixx-os` et `binixx-os-dark` (`/usr/share/icons/`) |
| Couleurs (accent bleu BinixX OS, texte, sélection) | BinixX OS | `BinixXClair`, `BinixXSombre` |
| Fond d'écran « Le marcheur de l'aube », disposition du panneau, logo du bouton Démarrer | BinixX OS | inchangés |
| Pointeur blanc, double-clic | BinixX OS | inchangés |

La barre de titre est épurée comme celle de Windows 11 : l'icône de l'application à gauche, réduire, agrandir et fermer à droite, rien
d'autre. KWin met par défaut à gauche un bouton « sur tous les bureaux » (trois points dans le thème Win11OS) et à droite un bouton
« aide » ; le thème global ne pose pas ces clés (`plasma-apply-lookandfeel` les ignore) : `build_files/build.sh` les écrit dans
`/etc/xdg/kwinrc` (`ButtonsOnLeft=M`, `ButtonsOnRight=IAX`), pour toutes les ambiances.

### Ce qui n'est pas repris du projet

- **Ses fonds d'écran** : des dessins proches du fond de Windows 11. BinixX OS garde le sien.
- **Son écran de connexion** : il remplacerait celui de Plasma ; il se jugerait sur un test de connexion que l'image ne fait pas encore.
- **Ses thèmes globaux et ses couleurs** : remplacés par ceux de BinixX OS (`org.binixx.desktop`, `org.binixx.dark.desktop`, couleurs
  `BinixXClair` et `BinixXSombre`), qui posent les thèmes ci-dessus.
- **Le thème d'icônes « Win11 »** du même auteur (une cinquantaine de Mo de sources) : ses icônes imitent de près celles des applications de
  Microsoft (Explorateur de fichiers, Photos, Xbox, Visual Studio…), ce que BinixX OS préfère ne pas distribuer. Les dossiers jaunes
  sont faits autrement (voir plus bas) ; le reste des icônes est celui de Breeze.
- **Le menu Démarrer en grille** du même auteur : un autre projet, non repris pour l'instant (voir « Moderniser BinixX OS »).

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

## Verre adaptatif

Les thèmes de Win11OS KDE sont **translucides**, comme l'acrylique de Windows 11 ou le « Liquid Glass » d'Apple, et comptent sur l'effet
« flou » de KWin pour rester lisibles. Sans flou (PC sans accélération graphique, machine virtuelle, bureau à distance), on voit à
travers : le test VM a montré les fenêtres du dessous se lire **par-dessus** le menu de démarrage, texte compris.

Plasma choisit lui-même le fond de ses fenêtres (code de libplasma : `ThemePrivate::updateKSvgSelectors`, `DialogPrivate::updateTheme`, et
`Panel.qml` pour la barre des tâches) :

| Situation | Dossier du thème que Plasma lit |
| --- | --- |
| L'effet de flou de KWin est actif (PC avec accélération graphique, cas courant) | `translucent/` |
| Pas de flou (machine virtuelle, vieux PC, bureau à distance) | `dialogs/` et `widgets/` eux-mêmes |
| Un élément demande un fond plein (barre des tâches touchée par une fenêtre agrandie, certaines info-bulles) | `solid/` |

`build_files/variantes-themes.py` s'appuie sur ce choix et fabrique, à chaque construction de l'image, à partir des thèmes d'origine
laissés intacts :

- **Plasma** `BinixX-Win11-light` / `-dark` (Aube, Nuit), en **verre adaptatif** : avec le flou, le verre dépoli d'origine de Win11OS
  KDE (`translucent/`) pour la barre des tâches, le menu de démarrage, les bulles et les info-bulles ; sans flou, les fonds pleins de
  `solid/` à la place de ceux, translucides, de `dialogs/` et `widgets/` (liens fichier par fichier ; un `.svgz` d'origine qui cacherait
  un `.svg` opaque est écarté, car Plasma cherche `.svgz` d'abord). Chaque PC a donc le rendu le plus moderne qu'il sait afficher
  **lisiblement**. La section `Wallpaper` du thème d'origine, qui nomme des fonds d'écran non livrés, est retirée.
- **Kvantum** `BinixX-Win11-light` / `-dark` (fenêtres des applications) : **opaques**. Kvantum ne sait pas si le flou est là ; huit réglages
  sont coupés (`translucent_windows`, `blurring`, `popup_blurring`, `transparent_dolphin_view`, `transparent_pcmanfm_sidepane`,
  `transparent_pcmanfm_view`, `transparent_menutitle`, `blur_translucent`), le dessin est le même. Comme le « Mica » de Windows 11, les
  fenêtres de travail restent pleines : le verre est réservé à ce qui flotte au-dessus (barre, menu, bulles).
- **Plasma** `BinixX-contraste` (Contraste élevé), à partir de Breeze (`default`) : **opaque dans tous les cas**, `translucent/` menant
  lui aussi à `solid/`. Le contraste élevé sert à lire : rien ne doit transparaître derrière le texte. Avant, il prenait Breeze tel quel,
  translucide sans flou (le test VM le montrait).
- La construction **échoue** si un réglage ou un fond attendu a disparu d'un thème d'origine (au lieu de livrer en silence des fenêtres
  redevenues transparentes).
- Les thèmes d'origine **restent installés, inchangés** : `Win11OS-light` / `Win11OS-dark` dans Kvantum Manager rendent aussi les fenêtres
  des applications translucides (sur un PC qui sait flouter) ; le thème Kvantum suit alors les couleurs dans **sa** famille (voir plus bas).
- **Le test VM ne peut pas montrer le verre** : la machine virtuelle n'a pas d'accélération graphique, le flou n'y est pas actif (le
  journal du test le dit : « effet de flou de KWin chargé »). Les captures montrent donc le cas opaque ; le cas « verre » est vérifié par
  le test de l'image (les liens mènent au verre d'origine) et se voit sur un vrai PC.

## Comment ça se règle

- **Aube** et **Nuit** (Paramètres → Personnalisation → Thèmes : clair ou sombre) posent le thème global correspondant : style
  `kvantum`, décoration Aurorae, thème Plasma. Les deux thèmes globaux sont dans `usr/share/plasma/look-and-feel/org.binixx.desktop`
  et `org.binixx.dark.desktop` (fichier `contents/defaults`).
- **Contraste élevé** garde l'ancien style (Breeze) : il suit à la lettre les couleurs noir, blanc et jaune, alors que Kvantum
  dessine ses propres couleurs. Il a donc son propre thème global, `org.binixx.contraste.desktop`, avec le thème Plasma Breeze toujours
  opaque `BinixX-contraste`.
- **Le thème Kvantum suit les couleurs.** Kvantum range son thème dans un fichier à part (`~/.config/Kvantum/kvantum.kvconfig`) que
  Plasma ne connaît pas : sans précaution, des couleurs sombres sous un thème Kvantum clair rendraient le texte illisible. Trois
  mécanismes les gardent d'accord :
  1. un compte neuf reçoit le thème clair de `/etc/skel/.config/Kvantum/kvantum.kvconfig` ;
  2. `binixx-ambiance appliquer` pose le thème Kvantum de l'ambiance **avant** de changer le thème global, et le remet d'accord si le
     bureau ne répond pas ;
  3. un service de chaque session (`binixx-kvantum.path` surveille `~/.config/kdeglobals`, `binixx-kvantum.service` lance
     `binixx-ambiance kvantum`) refait la même chose chaque fois que les couleurs changent, même depuis Configuration du système,
     et à l'ouverture de session (comptes existants).
  Un thème `Win11OS-*` d'origine (translucide) choisi à la main est suivi dans sa famille, jamais remplacé par l'opaque ; un autre thème Kvantum choisi à la main (Kvantum Manager) n'est jamais remplacé, et des couleurs qui ne sont pas celles de
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
- **Transparence** : le verre dépoli n'est que sur la barre des tâches, le menu et les bulles, et seulement quand le flou de KWin est actif
  (voir « Verre adaptatif ») ; les fenêtres des applications restent opaques, sauf si l'on choisit à la main les thèmes Kvantum d'origine.
- **Dossiers** : jaunes, mais au dessin de Breeze (plats, avec un onglet plus foncé), pas celui, dégradé, de l'Explorateur de Windows 11.
  Les autres icônes (applications, fichiers) sont celles de Breeze.

## Moderniser BinixX OS

Ce qui fait l'identité de BinixX OS **ne change pas** : fenêtres aux angles arrondis, barre des tâches flottante aux coins arrondis en haut
de l'écran, gemme bleue, fond « Le marcheur de l'aube ». La modernisation s'inspire de ce que les bureaux les plus récents ont en commun
(octobre 2026) :

| Tendance | Chez qui | Dans BinixX OS |
| --- | --- | --- |
| **Verre dépoli** sur ce qui flotte (barre, menus, bulles), fond plein pour le travail | Windows 11 (acrylique et Mica), Apple « Liquid Glass » (juin 2025), Plasma (flou) | **Fait** : verre adaptatif (ci-dessus), lisible même sans flou |
| Barre de titre épurée : l'icône, le titre, trois boutons | Windows 11, macOS, GNOME | **Fait** : plus de bouton « sur tous les bureaux » ni « aide » |
| L'accessibilité comme exigence de départ | tendances 2026 ; Plasma 6.6 et 6.7 | **Fait** : contraste élevé opaque partout |
| Sélections et surlignages arrondis | Plasma 6.7 (Breeze), Windows 11 | déjà là : Kvantum Win11OS arrondit les sélections |
| Menu Démarrer : applications en grille ou par catégories | Windows 11 (refonte 2025, puis 26H2 en test) | **Fait** : « Toutes les applications » et les catégories en grille d'icônes (comptes neufs) |
| Bascule clair / sombre automatique selon l'heure | Plasma 6.5, macOS, iOS | **Fait** : « Aube le jour, Nuit le soir », activé d'office, réglable dans Ambiances ([centre-binixx.md](centre-binixx.md#ambiances--lallure-du-bureau-en-un-clic)) |

Pistes suivantes, chacune à voir en capture avant de la livrer :

- **Menu Démarrer** : la grille (choisie par le propriétaire) n'affiche que le nom des applications ; la recherche du menu, elle, montre
  toujours ce que fait chacune (« Okular — Visionneuse de documents »). Un menu plus proche de celui de Windows 11 (épinglées +
  recommandées) serait un composant tiers à maintenir. Un compte déjà créé garde sa liste : clic droit sur le bouton Démarrer →
  Configurer → « Afficher les applications : en grille ».
- **Icônes** : les icônes Fluent de Microsoft (licence MIT,
  [fluentui-system-icons](https://github.com/microsoft/fluentui-system-icons)) en thème partiel qui hérite de BinixX OS ; leurs pictogrammes
  d'interface sont libres de réutilisation, contrairement aux icônes d'applications de Microsoft.
- **Écran de connexion** du projet Win11OS, avec un test de connexion en VM.

Sources : [Liquid Glass (Wikipédia)](https://en.wikipedia.org/wiki/Liquid_Glass) ;
[Windows 11 : refonte du menu Démarrer](https://www.windowscentral.com/microsoft/windows-11/windows-11-to-bring-major-changes-to-start-menu-and-taskbar-in-2026),
[menu Démarrer redimensionnable en 26H2](https://www.digitalcitizen.life/windows-11-may-get-a-smaller-and-more-customizable-start-menu-in-26h2/) ;
[KDE Plasma 6 (Wikipédia)](https://en.wikipedia.org/wiki/KDE_Plasma_6) ;
[Plasma 6.7 : surlignages arrondis](https://linuxiac.com/kde-plasma-6-7-to-introduce-rounded-highlights/) ;
[tendances de l'interface en 2026](https://www.pixelmatters.com/insights/7-UI-design-trends-to-watch-in-2026).

## Tests

- **Image** (`tests/image/checks.d/82-theme-windows-11.sh`) : `kvantum` installé et son style Qt 6 présent ; les trois thèmes de chaque
  variante (Aurorae, Kvantum, Plasma) complets ; les variantes (huit réglages Kvantum à `false` ; thème Plasma d'Aube et de Nuit : `translucent` qui mène au verre d'origine,
  `dialogs/` et `widgets/` aux fonds de `solid`, sans `.svgz` d'origine qui les cache, pas de section Wallpaper ; `BinixX-contraste` : les
  trois chemins mènent à `solid`) ; barre de titre (`/etc/xdg/kwinrc`) et les thèmes d'origine restés translucides ; licence, auteurs et source ; fonds d'écran et écran de connexion du projet absents ;
  chaque thème global pose des noms qui existent vraiment ; Contraste élevé n'utilise ni Kvantum ni Aurorae ; thème Kvantum de
  `/etc/skel` ; service et surveillance activés ; `binixx-ambiance kvantum` suit les couleurs sans remplacer un autre thème choisi.
  Les tests Python de `tests/image/centre/test_ambiances.py` couvrent la logique (thème par couleurs, fichier réécrit sans perdre les
  réglages par application, thème choisi à la main respecté, ordre dans `appliquer`).
- Dossiers jaunes, dans les mêmes tests de l'image : thèmes `binixx-os` et `binixx-os-dark` (héritage, jaune de chaque taille de 16 à 96 pixels,
  dossiers Documents, Téléchargements, Musique, Images et Vidéos, type « dossier », liens du thème sombre, licence) ; chaque thème global
  nomme un thème d'icônes qui existe ; Contraste élevé reste sur Breeze sombre.
- **VM** (`tests/vm/checks.d/82-theme-windows-11.sh`) : le compte de l'installation a le thème clair ; la surveillance tourne ; un
  changement de couleurs dans `kdeglobals` fait changer le thème Kvantum tout seul ; pour chaque ambiance, le style, la
  décoration des fenêtres, les boutons de la barre de titre, le thème Plasma, le thème d'icônes et le thème Kvantum relus dans la session
  sont ceux annoncés ; le journal dit si le flou de KWin est chargé. Captures d'écran jointes aux journaux : `theme-aube.png`,
  `theme-nuit.png`, `theme-contraste.png` (Dolphin ouvert) et `theme-*-menu.png` (menu de démarrage ouvert).
