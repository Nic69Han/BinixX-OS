# Centre NicOS : accueil, logiciels Windows, fichiers, aide, protection des données, jeux

Une seule application, `Bienvenue dans NicOS` dans le menu (commande `nicos-centre`), faite de pages :

| Page | Rôle |
| --- | --- |
| **Accueil** | Les premiers pas : réseau, OneDrive, applications, apparence, administration ; et « Sous Windows, ici » (Explorateur → Dolphin, Store → Discover…). S'ouvre toute seule **une fois**, à la première ouverture de session ; le menu permet de la rouvrir. |
| **Mon logiciel Windows** | Une recherche (« Word », « Sage », « Photoshop », « tableur »…) renvoie l'équivalent sous NicOS : déjà installé (bouton *Ouvrir*), à installer (bouton *Installer*, qui ouvre Discover sur la bonne application), version en ligne, ou « pas d'équivalent direct » avec les pistes pour s'en sortir. En bas, « Essayer avec Bottles » pour la compatibilité Windows, sans garantie. |
| **Installer des applications** | Plus de vingt applications connues sous Windows (VLC, LibreOffice, Spotify, Discord, Bitwarden, GIMP, FileZilla…) : on coche, NicOS les installe d'un coup depuis Flathub, avec **un seul mot de passe d'administrateur**. La licence est affichée et les applications **propriétaires** sont signalées : [ci-dessous](#installer-des-applications). |
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

## Installer des applications

La page **Installer des applications** (menu, ou bouton « Choisir mes applications » de l'accueil) remplace, pour
l'essentiel, le « Microsoft Store » : on coche, un bouton installe tout.

- **La liste vient du catalogue** (`catalogue.tsv`) : une ligne par application Flatpak, avec les logiciels Windows
  qu'elle remplace (« Remplace : Adobe Photoshop » pour GIMP). N'y figurent ni ce que NicOS installe déjà au premier
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
