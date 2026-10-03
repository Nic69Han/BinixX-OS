# Centre BinixX OS : accueil, logiciels Windows, fichiers, aide, protection des données, jeux

Une seule application, `Bienvenue dans BinixX OS` dans le menu (commande `binixx-centre`), faite de pages :

| Page | Rôle |
| --- | --- |
| **Accueil** | Les premiers pas : réseau, OneDrive, applications, apparence, administration ; et « Sous Windows, ici » (Explorateur → Dolphin, Store → Discover…). S'ouvre toute seule **une fois**, à la première ouverture de session ; le menu permet de la rouvrir. |
| **Paramètres** | Tous les réglages du PC au même endroit, **classés et nommés comme dans Windows 11** (Système, Bluetooth et appareils, Réseau et Internet, Personnalisation, Applications, Comptes, Heure et langue, Accessibilité, Confidentialité et sécurité, Mises à jour et récupération), avec une recherche (« Bluetooth », « fond d'écran », « mot de passe », « Panneau de configuration »). Touche **Windows + I** : [ci-dessous](#paramètres). |
| **Mon logiciel Windows** | Une recherche (« Word », « Sage », « Photoshop », « tableur »…) renvoie l'équivalent sous BinixX OS : déjà installé (bouton *Ouvrir*), à installer (bouton *Installer*, qui ouvre Discover sur la bonne application), version en ligne, ou « pas d'équivalent direct » avec les pistes pour s'en sortir. En bas, « Essayer avec Bottles » pour la compatibilité Windows, sans garantie. |
| **Installer des applications** | Plus de vingt applications connues sous Windows (VLC, LibreOffice, Spotify, Discord, Bitwarden, GIMP, FileZilla…) : on coche, BinixX OS les installe d'un coup depuis Flathub, avec **un seul mot de passe d'administrateur**. La licence est affichée et les applications **propriétaires** sont signalées : [ci-dessous](#installer-des-applications). |
| **Windows complet** | Pour le logiciel indispensable sans équivalent : le PC est-il prêt (virtualisation, mémoire, espace, processeur) ? Boxes, WinBoat ou Windows 365 : [windows-vm.md](windows-vm.md). |
| **Récupérer mes fichiers** | Copie documents, photos, musique, vidéos et favoris depuis l'ancien disque Windows, une clé USB ou un dossier, **sans rien écraser** ni écrire sur l'ancien disque : [migration-windows.md](migration-windows.md#récupérer-ses-fichiers--récupérer-mes-fichiers-windows). |
| **Obtenir de l'aide** | Sept cas fréquents sans IA, rapport de diagnostic pour le support, remise à zéro du bureau : [aide-depannage.md](aide-depannage.md). |
| **Protéger mes données** | Clé de récupération du disque chiffré (l'équivalent de celle de BitLocker) et accès au pare-feu : [securite.md](securite.md#clé-de-récupération-du-disque-chiffré). |
| **Jeux** | Steam, Heroic (Epic, GOG), Lutris, Prism (Minecraft), ProtonUp-Qt et le jeu en streaming, **à installer à la demande** ; carte graphique détectée, manettes, lien ProtonDB : [jeux.md](jeux.md). |

D'autres pages s'y ajoutent : voir la [feuille de route](feuille-de-route.md).

## Quand on ouvre un .exe ou un .msi

BinixX OS n'exécute pas les programmes Windows directement. Un double-clic sur un `.exe` ou un `.msi`
ouvre « Mon logiciel Windows », avec une explication et une recherche déjà remplie d'après le nom du
fichier (`Setup_Sage100_v2023.exe` → « Sage »). Le fichier n'est **jamais** exécuté ni lu par le Centre :
seul son nom sert. Le lanceur est `binixx-windows-program.desktop`, associé aux types MIME
`application/vnd.microsoft.portable-executable`, `application/x-msi` et leurs variantes
(`etc/xdg/kde-mimeapps.list`).

## Paramètres

La page **Paramètres** (menu BinixX OS, favori du menu de démarrage, ou touche Windows + I) est l'équivalent de
l'application Paramètres de Windows 11. Elle ne réécrit aucun réglage : elle met devant ceux de KDE (la
Configuration du système) un classement et des noms que l'on reconnaît.

- **Un fichier de données** : `usr/share/binixx/parametres/parametres.tsv`. Une ligne par réglage : catégorie, nom, mots de
  recherche (« fond d'écran », « arrière-plan »…), explication, icône, type et cible. Les types : `kcm` (un module de la
  Configuration du système), `page` (une autre page du Centre), `app` (un lanceur de l'image), `flatpak`, `discover`
  (mises à jour, applications installées), `info` (une explication, rien à ouvrir).
- **Présentation** : un en-tête en dégradé aux couleurs de BinixX OS (avec la grande barre de recherche arrondie), un menu de
  catégories à pastilles colorées, des **tuiles** cliquables à la souris comme au clavier (Tab, Entrée, Espace), sur deux
  colonnes (une seule si la fenêtre est étroite). Chaque catégorie a sa couleur et son pictogramme ; les pictogrammes sont des
  traits fins embarqués en SVG (`binixx_centre/icones.py`, dans le style des icônes Feather, licence MIT), donc indépendants
  du thème d'icônes du PC. Une explication sans réglage à ouvrir (type `info`) a un cadre en pointillés.
- **Recherche** sans accents ni majuscules, tous les mots doivent correspondre, le nom exact d'abord : « wifi »,
  « Wi-Fi » et « WIFI » donnent la même réponse ; « mot de passe » met « Votre compte » en premier.
- **Jamais de bouton mort** : un module KDE absent de ce PC est masqué (la liste vient de `kcmshell6 --list`) ; à l'inverse, la CI
  vérifie à **chaque build** que tous les modules cités existent dans l'image, et affiche la liste complète. Un module renommé par une mise à jour de Plasma fait
  échouer le build au lieu de laisser un bouton qui n'ouvre rien.
- **Réglages avancés** : le bouton du bas ouvre la Configuration du système complète.
- **Ajouter ou corriger un réglage** : une ligne dans `parametres.tsv` ; `kcmshell6 --list` (sur un poste BinixX OS) donne les
  identifiants des modules.
- **Touche Windows + I** : `usr/share/applications/binixx-parametres.desktop` (`X-KDE-Shortcuts`) et `etc/xdg/kglobalshortcutsrc`.
  Le test VM vérifie que KDE l'a enregistrée, en simple avertissement : si KDE l'ignorait, le menu et la recherche restent là.

## Barre des tâches : en bas ou en haut

Sous Windows la barre est en bas ; BinixX OS la place **en haut** au départ (flottante, aux coins arrondis). Dans
**Paramètres → Personnalisation → Barre des tâches**, une page propose les deux positions, chacune avec une petite
maquette d'écran (celle du choix actuel est cerclée). Un clic sur « Choisir » déplace la barre tout de suite, sans fermer la
session, et Plasma garde ce choix d'une session à l'autre. Plasma met quelques secondes à appliquer le changement : la page
affiche « La barre se déplace… », puis confirme (ou dit que la barre n'a pas bougé) sans bloquer la fenêtre.

- **Comment** : `binixx_centre/barre.py` envoie à Plasma, par D-Bus (`org.kde.PlasmaShell.evaluateScript`), un petit script
  qui met les panneaux en `top` ou `bottom` ; aucun fichier de configuration n'est réécrit à la main, aucun shell n'est
  utilisé, et la position vient d'une liste fermée (`haut`, `bas`). La position actuelle se lit dans la disposition courante
  de Plasma, à défaut dans `plasma-org.kde.plasma.desktop-appletsrc`.
- **Hors session** (un terminal à distance, un build) : le message dit que le bureau ne répond pas, sans trace d'erreur.
- **Pourquoi on relit la position** : `evaluateScript` répond avant que la barre ait bougé ; le test VM l'a mesuré (plusieurs
  secondes). `barre.deplacer()` (ligne de commande) attend jusqu'à 15 secondes que Plasma confirme ; la page envoie l'ordre
  (`barre.envoyer()`) puis relit toutes les 600 ms.
- **En ligne de commande** (pour le support et les scripts d'entreprise) : `/usr/libexec/binixx/binixx-barre haut|bas|etat`.
- **Page sans bouton dans la barre latérale** : elle s'ouvre depuis Paramètres, dont le bouton reste allumé
  (`MENU = False` et `PARENT = "parametres"` dans `pages/barre.py`, voir [Sous le capot](#sous-le-capot)).
- **Pour changer la position d'origine** (un déploiement d'entreprise en bas, par exemple) : `panel.location` dans
  `usr/share/plasma/look-and-feel/org.binixx.desktop/contents/layouts/org.kde.plasma.desktop-layout.js`.
- **Tests** : `tests/image/centre/test_barre.py` (script, lecture, déplacement, page) ; la CI vérifie l'outil dans l'image ;
  le test VM déplace vraiment la barre dans la session de l'utilisateur de test, vérifie que Plasma le confirme et que le
  choix est écrit dans sa configuration, puis la remet en haut.

## Installer des applications

La page **Installer des applications** (menu, ou bouton « Choisir mes applications » de l'accueil) remplace, pour
l'essentiel, le « Microsoft Store » : on coche, un bouton installe tout.

- **La liste vient du catalogue** (`catalogue.tsv`) : une ligne par application Flatpak, avec les logiciels Windows
  qu'elle remplace (« Remplace : Adobe Photoshop » pour GIMP). N'y figurent ni ce que BinixX OS installe déjà au premier
  démarrage (OnlyOffice, Thunderbird…), ni les jeux et « Windows complet », qui ont leur page avec leurs explications.
  Ajouter une application = ajouter une ligne `flatpak` au catalogue, puis régénérer les licences (voir plus bas).
- **Installation pour tout le système** : `flatpak install --system --noninteractive --assumeyes flathub <applications>`,
  dans une seule transaction, donc **un seul mot de passe d'administrateur** pour le lot (fenêtre d'authentification
  de Plasma). Les applications apparaissent aussitôt dans le menu, pour tous les comptes. Pour un compte sans droits
  d'administration, la page l'explique. L'installation peut être annulée.
- **Licences** : chaque ligne affiche « Libre · GPL-3.0 » ou, en orange, « Propriétaire (code fermé) » (Spotify,
  Discord, AnyDesk, Dropbox, Visual Studio Code). Les licences viennent de Flathub et sont enregistrées dans
  `licences.tsv`, que `tests/centre/verifier_flathub.py --ecrire licences.tsv` régénère (le même outil, sans
  `--ecrire`, signale tout écart avec Flathub et tout identifiant disparu).
- **Rien n'est installé d'office** et rien n'est coché d'avance.
- **Ce que la CI vérifie** : la liste, les licences, la commande (aucun identifiant dangereux ne passe) et la page
  (avec un faux `flatpak`) ; dans la VM, la **commande de la page installe vraiment une application** depuis Flathub, puis
  la retire, et chaque identifiant proposé est cherché sur Flathub (un identifiant disparu est signalé en avertissement).
  **Non vérifié** : la fenêtre d'authentification elle-même (pas d'écran en CI).

## Compléter le catalogue

Le catalogue est un simple fichier : `system_files/usr/share/binixx/catalogue-windows/catalogue.tsv`
(une ligne par logiciel, colonnes décrites en tête de fichier). Après une modification :

- `python3 -m unittest discover -s tests/image/centre` (lecture et recherche) ;
- `tests/centre/verifier_flathub.py` : vérifie sur Flathub que chaque identifiant existe et affiche sa
  licence (réseau nécessaire) ;
- la CI vérifie aussi que chaque logiciel « inclus » a son lanceur dans l'image.

## Pourquoi pas le Centre de bienvenue de KDE ?

Il s'adresse à des habitués de Linux (« Découvrir Plasma », « Participer »). L'accueil de BinixX OS parle
le langage de Windows. Le Centre de bienvenue de KDE est donc désactivé à l'ouverture de session
(`/etc/xdg/plasma-welcomerc`), mais reste installé.

## Présentation commune

Toutes les pages partagent le même style moderne (retour du propriétaire : « plus moderne, c'est trop basique »).

- **Une couleur par page**, reprise partout : l'en-tête en dégradé (avec des facettes translucides, clin d'œil à la gemme du
  logo), le liseré des titres de section et les pastilles des cartes. Accueil bleu, Paramètres indigo, Mon logiciel Windows
  orange, Installer des applications violet, Windows complet cyan, Récupérer mes fichiers vert, Obtenir de l'aide rose,
  Protéger mes données sarcelle, Jeux rouge. Mode sombre compris.
- **La barre latérale** montre, devant chaque page, une pastille de sa couleur avec son pictogramme.
- **Des cartes** arrondies avec une pastille d'icône, un titre, un texte et un bouton en pilule ; sur l'accueil, des cartes
  « hautes » rangées sur trois, deux ou une colonne selon la largeur de la fenêtre (rien ne déborde).
- **Les états se voient** : sous « Windows complet », ✔/⚠/✖ sont des pastilles verte, orange et rouge ; sous « Installer des
  applications », la barre d'installation reste visible en bas, quelle que soit la longueur de la liste.
- Les pictogrammes sont des SVG embarqués (`icones.py`, style Feather, licence MIT) ; les éléments communs (en-tête, cartes,
  grille, pastilles) sont dans `widgets.py`, les couleurs et les styles dans `theme.py`. Une page n'a rien à redessiner : elle
  appelle `widgets.entete(...)`, `widgets.section(...)` et `widgets.carte(...)`.

## Sous le capot

- Python et **PySide6** (Qt 6), déjà présents dans l'image : rien de nouveau à installer.
- Code : `system_files/usr/lib/binixx/centre/binixx_centre/` ; lanceur `usr/libexec/binixx/binixx-centre`.
- **Ajouter une page** = ajouter un fichier dans `binixx_centre/pages/` qui définit `ORDER`, `KEY`,
  `TITLE` et `build(centre)` (et, pour le style, `ICONE` et `ACCENT`, voir ci-dessus) ; elle apparaît dans la barre
  latérale, sans autre modification. Une page qui n'a pas à y figurer (elle s'ouvre depuis une autre) ajoute
  `MENU = False` et `PARENT = "<clé de la page parente>"`.
- Les actions (ouvrir Discover, la Configuration du système, un lanceur) passent par `launch.py` :
  jamais de shell, jamais de texte saisi par l'utilisateur dans une commande.
- `binixx-centre --test <dossier>` construit toutes les pages hors écran et en enregistre une
  capture (une image par page) : c'est ce que fait la CI (`tests/image/checks.d/50-centre.sh`). Le test VM vérifie que
  l'accueil s'ouvre vraiment à la première session et que le Centre de bienvenue de KDE reste fermé.
