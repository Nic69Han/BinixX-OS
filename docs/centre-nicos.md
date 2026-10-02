# Centre NicOS : accueil, logiciels Windows, aide

Une seule application, `Bienvenue dans NicOS` dans le menu (commande `nicos-centre`), faite de pages :

| Page | Rôle |
| --- | --- |
| **Accueil** | Les premiers pas : réseau, OneDrive, applications, apparence, administration ; et « Sous Windows, ici » (Explorateur → Dolphin, Store → Discover…). S'ouvre toute seule **une fois**, à la première ouverture de session ; le menu permet de la rouvrir. |

D'autres pages s'y ajoutent (catalogue « Mon logiciel Windows », aide) : voir la feuille de route.

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
