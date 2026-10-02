# Centre NicOS : accueil, logiciels Windows, fichiers, aide, protection des données, jeux

Une seule application, `Bienvenue dans NicOS` dans le menu (commande `nicos-centre`), faite de pages :

| Page | Rôle |
| --- | --- |
| **Accueil** | Les premiers pas : réseau, OneDrive, applications, apparence, administration ; et « Sous Windows, ici » (Explorateur → Dolphin, Store → Discover…). S'ouvre toute seule **une fois**, à la première ouverture de session ; le menu permet de la rouvrir. |
| **Paramètres** | Tous les réglages du PC au même endroit, **classés et nommés comme dans Windows 11** (Système, Bluetooth et appareils, Réseau et Internet, Personnalisation, Applications, Comptes, Heure et langue, Accessibilité, Confidentialité et sécurité, Mises à jour et récupération), avec une recherche (« Bluetooth », « fond d'écran », « mot de passe », « Panneau de configuration »). Touche **Windows + I** : [ci-dessous](#paramètres). |
| **Mon logiciel Windows** | Une recherche (« Word », « Sage », « Photoshop », « tableur »…) renvoie l'équivalent sous NicOS : déjà installé (bouton *Ouvrir*), à installer (bouton *Installer*, qui ouvre Discover sur la bonne application), version en ligne, ou « pas d'équivalent direct » avec les pistes pour s'en sortir. En bas, « Essayer avec Bottles » pour la compatibilité Windows, sans garantie. |
| **Windows complet** | Pour le logiciel indispensable sans équivalent : le PC est-il prêt (virtualisation, mémoire, espace, processeur) ? Boxes, WinBoat ou Windows 365 : [windows-vm.md](windows-vm.md). |
| **Récupérer mes fichiers** | Copie documents, photos, musique, vidéos et favoris depuis l'ancien disque Windows, une clé USB ou un dossier, **sans rien écraser** ni écrire sur l'ancien disque : [migration-windows.md](migration-windows.md#récupérer-ses-fichiers--récupérer-mes-fichiers-windows). |
| **Obtenir de l'aide** | Sept cas fréquents sans IA, rapport de diagnostic pour le support, remise à zéro du bureau : [aide-depannage.md](aide-depannage.md). |
| **Protéger mes données** | Clé de récupération du disque chiffré (l'équivalent de celle de BitLocker) et accès au pare-feu : [securite.md](securite.md#clé-de-récupération-du-disque-chiffré). |
| **Jeux** | Steam, Heroic (Epic, GOG), Lutris, Prism (Minecraft), ProtonUp-Qt et le jeu en streaming, **à installer à la demande** ; carte graphique détectée, manettes, lien ProtonDB : [jeux.md](jeux.md). |

D'autres pages s'y ajoutent : voir la [feuille de route](feuille-de-route.md).

## Quand on ouvre un .exe ou un .msi

NicOS n'exécute pas les programmes Windows directement. Un double-clic sur un `.exe` ou un `.msi`
ouvre « Mon logiciel Windows », avec une explication et une recherche déjà remplie d'après le nom du
fichier (`Setup_Sage100_v2023.exe` → « Sage »). Le fichier n'est **jamais** exécuté ni lu par le Centre :
seul son nom sert. Le lanceur est `nicos-windows-program.desktop`, associé aux types MIME
`application/vnd.microsoft.portable-executable`, `application/x-msi` et leurs variantes
(`etc/xdg/kde-mimeapps.list`).

## Paramètres

La page **Paramètres** (menu NicOS, favori du menu de démarrage, ou touche Windows + I) est l'équivalent de
l'application Paramètres de Windows 11. Elle ne réécrit aucun réglage : elle met devant ceux de KDE (la
Configuration du système) un classement et des noms que l'on reconnaît.

- **Un fichier de données** : `usr/share/nicos/parametres/parametres.tsv`. Une ligne par réglage : catégorie, nom, mots de
  recherche (« fond d'écran », « arrière-plan »…), explication, icône, type et cible. Les types : `kcm` (un module de la
  Configuration du système), `page` (une autre page du Centre), `app` (un lanceur de l'image), `flatpak`, `discover`
  (mises à jour, applications installées), `info` (une explication, rien à ouvrir : « Barre des tâches »).
- **Présentation** : un en-tête en dégradé aux couleurs de NicOS (avec la grande barre de recherche arrondie), un menu de
  catégories à pastilles colorées, des **tuiles** cliquables à la souris comme au clavier (Tab, Entrée, Espace), sur deux
  colonnes (une seule si la fenêtre est étroite). Chaque catégorie a sa couleur et son pictogramme ; les pictogrammes sont des
  traits fins embarqués en SVG (`nicos_centre/icones.py`, dans le style des icônes Feather, licence MIT), donc indépendants
  du thème d'icônes du PC. Une explication sans réglage à ouvrir (« Barre des tâches ») a un cadre en pointillés.
- **Recherche** sans accents ni majuscules, tous les mots doivent correspondre, le nom exact d'abord : « wifi »,
  « Wi-Fi » et « WIFI » donnent la même réponse ; « mot de passe » met « Votre compte » en premier.
- **Jamais de bouton mort** : un module KDE absent de ce PC est masqué (la liste vient de `kcmshell6 --list`) ; à l'inverse, la CI
  vérifie à **chaque build** que tous les modules cités existent dans l'image, et affiche la liste complète. Un module renommé par une mise à jour de Plasma fait
  échouer le build au lieu de laisser un bouton qui n'ouvre rien.
- **Réglages avancés** : le bouton du bas ouvre la Configuration du système complète.
- **Ajouter ou corriger un réglage** : une ligne dans `parametres.tsv` ; `kcmshell6 --list` (sur un poste NicOS) donne les
  identifiants des modules.
- **Touche Windows + I** : `usr/share/applications/nicos-parametres.desktop` (`X-KDE-Shortcuts`) et `etc/xdg/kglobalshortcutsrc`.
  Le test VM vérifie que KDE l'a enregistrée, en simple avertissement : si KDE l'ignorait, le menu et la recherche restent là.

## Compléter le catalogue

Le catalogue est un simple fichier : `system_files/usr/share/nicos/catalogue-windows/catalogue.tsv`
(une ligne par logiciel, colonnes décrites en tête de fichier). Après une modification :

- `python3 -m unittest discover -s tests/image/centre` (lecture et recherche) ;
- `tests/centre/verifier_flathub.py` : vérifie sur Flathub que chaque identifiant existe et affiche sa
  licence (réseau nécessaire) ;
- la CI vérifie aussi que chaque logiciel « inclus » a son lanceur dans l'image.

## Pourquoi pas le Centre de bienvenue de KDE ?

Il s'adresse à des habitués de Linux (« Découvrir Plasma », « Participer »). L'accueil de NicOS parle
le langage de Windows. Le Centre de bienvenue de KDE est donc désactivé à l'ouverture de session
(`/etc/xdg/plasma-welcomerc`), mais reste installé.

## Sous le capot

- Python et **PySide6** (Qt 6), déjà présents dans l'image : rien de nouveau à installer.
- Code : `system_files/usr/lib/nicos/centre/nicos_centre/` ; lanceur `usr/libexec/nicos/nicos-centre`.
- **Ajouter une page** = ajouter un fichier dans `nicos_centre/pages/` qui définit `ORDER`, `KEY`,
  `TITLE` et `build(centre)` ; elle apparaît dans la barre latérale, sans autre modification.
- Les actions (ouvrir Discover, la Configuration du système, un lanceur) passent par `launch.py` :
  jamais de shell, jamais de texte saisi par l'utilisateur dans une commande.
- `nicos-centre --test <dossier>` construit toutes les pages hors écran et en enregistre une
  capture : c'est ce que fait la CI (`tests/image/checks.d/50-centre.sh`). Le test VM vérifie que
  l'accueil s'ouvre vraiment à la première session et que le Centre de bienvenue de KDE reste fermé.
