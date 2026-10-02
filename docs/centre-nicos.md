# Centre NicOS : accueil, logiciels Windows, aide, jeux

Une seule application, `Bienvenue dans NicOS` dans le menu (commande `nicos-centre`), faite de pages :

| Page | Rôle |
| --- | --- |
| **Accueil** | Les premiers pas : réseau, OneDrive, applications, apparence, administration ; et « Sous Windows, ici » (Explorateur → Dolphin, Store → Discover…). S'ouvre toute seule **une fois**, à la première ouverture de session ; le menu permet de la rouvrir. |
| **Mon logiciel Windows** | Une recherche (« Word », « Sage », « Photoshop », « tableur »…) renvoie l'équivalent sous NicOS : déjà installé (bouton *Ouvrir*), à installer (bouton *Installer*, qui ouvre Discover sur la bonne application), version en ligne, ou « pas d'équivalent direct » avec les pistes pour s'en sortir. En bas, « Essayer avec Bottles » pour la compatibilité Windows, sans garantie. |
| **Jeux** | Steam, Heroic (Epic, GOG), Lutris, Prism (Minecraft), ProtonUp-Qt et le jeu en streaming, **à installer à la demande** ; carte graphique détectée, manettes, lien ProtonDB : [jeux.md](jeux.md). |

D'autres pages s'y ajoutent : voir la [feuille de route](feuille-de-route.md).

## Quand on ouvre un .exe ou un .msi

NicOS n'exécute pas les programmes Windows directement. Un double-clic sur un `.exe` ou un `.msi`
ouvre « Mon logiciel Windows », avec une explication et une recherche déjà remplie d'après le nom du
fichier (`Setup_Sage100_v2023.exe` → « Sage »). Le fichier n'est **jamais** exécuté ni lu par le Centre :
seul son nom sert. Le lanceur est `nicos-windows-program.desktop`, associé aux types MIME
`application/vnd.microsoft.portable-executable`, `application/x-msi` et leurs variantes
(`etc/xdg/kde-mimeapps.list`).

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
