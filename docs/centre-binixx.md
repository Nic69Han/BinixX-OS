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

## Raccourcis : l'aide-mémoire de Windows

Un utilisateur de Windows a des réflexes : Windows + E pour les fichiers, Windows + L pour verrouiller, Windows + V pour
l'historique du presse-papiers. **Paramètres → Bluetooth et appareils → Aide-mémoire des raccourcis** ouvre une page qui liste
ceux qui marchent sur BinixX OS (touches dessinées comme sur un clavier, avec une recherche : « capture », « fichiers »,
« windows e »). Le bouton « Personnaliser » ouvre les raccourcis de la Configuration du système (`kcm_keys`) pour en changer
ou en ajouter.

- **Deux sources** : `kde` = Plasma les fournit lui-même (Windows + D, Windows + L, Alt + Tab…) ; `binixx` = l'image les ajoute,
  parce que KDE n'offre pas l'équivalent : **Windows + R** (la barre de recherche de KRunner), **Ctrl + Maj + Échap** (le
  Moniteur système, comme le Gestionnaire des tâches ; Ctrl + Échap marche toujours) et **Windows + E** (Dolphin ; KDE le
  fournit normalement, la ligne le garantit). Windows + I (Paramètres) existait déjà. **Windows + Maj + S** (capturer une
  zone) est celui de Spectacle, déjà dans KDE.
- **Comment** : `etc/xdg/kglobalshortcutsrc` (`_launch=` par lanceur), et chaque lanceur ajouté déclare la même touche
  (`X-KDE-Shortcuts=`) : `binixx-executer.desktop`, `binixx-gestionnaire-taches.desktop`.
  Les réglages de l'utilisateur passent avant : s'il change une touche, la sienne reste.
- **Une touche, un seul propriétaire** : KDE ne sert qu'une action par touche. Spectacle prend déjà Windows + R (une de ses
  actions d'enregistrement d'écran) et la Configuration du système Windows + I : sans précaution, nos raccourcis ne marcheraient
  que par moments. Constaté dans le test VM : un `[services]` dans `kglobalshortcutsrc` ne retire pas la touche à ces lanceurs,
  KDE lit la déclaration `X-KDE-Shortcuts` de leur fichier `.desktop`. Au build, `build_files/modules.d/78-raccourcis.sh` lance donc
  `binixx-raccourcis surcharger` : il lit les `X-KDE-Shortcuts` des lanceurs de KDE (entrée principale ou `[Desktop Action X]`),
  retire nos touches (source `binixx`) dans le `.desktop` de ceux qui ne sont pas à nous, et note ce qu'il a retiré dans
  `/usr/share/binixx/raccourcis/touches-retirees.txt`. Il ne touche ni aux touches de source `kde`, ni à nos lanceurs `binixx-*`.
  Le build échoue s'il reste un conflit.
- **La liste** : `usr/share/binixx/raccourcis/raccourcis.tsv` (catégorie, touches à la KDE, action, précision, source).
  Ajouter un raccourci = ajouter une ligne ; si sa source est `binixx`, ajouter aussi son `_launch` dans
  `kglobalshortcutsrc` (un test l'exige, et un test refuse l'inverse : une touche posée par l'image sans être annoncée).
- **Une promesse vérifiée** : `binixx_centre/raccourcis.py` interroge le service de raccourcis de KDE
  (`org.kde.kglobalaccel`, par `busctl`, sans shell) et compare les codes de touches de Qt avec ceux du fichier. Le test VM
  lance `binixx-raccourcis verifier` dans la vraie session : **un raccourci annoncé que KDE n'a pas enregistré (MANQUE), ou qu'il
  donne à plusieurs actions (CONFLIT), fait échouer le test**, et le journal contient tout ce que KDE a enregistré (composant / action) pour corriger la liste.
- **En ligne de commande** (support, scripts d'entreprise) : `/usr/libexec/binixx/binixx-raccourcis liste|verifier|registre|surcharger`.
- **Page sans bouton dans la barre latérale** : comme la barre des tâches, elle s'ouvre depuis Paramètres.
- **Tests** : `tests/image/centre/test_raccourcis.py` (fichier, codes de touches, lecture de la réponse de KDE, cohérence
  avec les lanceurs, page) ; la CI vérifie les lanceurs et les programmes ouverts (`78-raccourcis.sh`).

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

## Mises à jour : une page, comme Windows Update

**Paramètres → Mises à jour et récupération → Mises à jour du système** ouvre une page qui répond aux questions qu'on se pose
devant Windows Update, sans terminal :

- **Quelle version ai-je ?** La version installée (`44.20261003.0`), sa date, et le **canal** suivi : « Stable » (chaque version a
  passé un test complet avant d'arriver sur le PC) ou « Test » (voir [mises-a-jour.md](mises-a-jour.md#deux-canaux)).
- **Y en a-t-il une nouvelle ?** Le bouton « Rechercher des mises à jour » compare l'**empreinte** de l'image installée avec celle
  que le registre publie aujourd'hui pour la même étiquette (`skopeo inspect`, sans identifiant ni mot de passe) et annonce la
  **taille à télécharger** : les couches de la nouvelle image que l'ancienne n'a pas. Sans réseau, la page le dit et ne devine rien.
- **Installer maintenant** (administrateur, une authentification) : `bootc upgrade` télécharge et prépare la version, sans
  redémarrer. Le PC se met aussi à jour tout seul, en arrière-plan : ce bouton ne fait que devancer le moment.
- **Redémarrer maintenant** quand une version est prête : la boîte de dialogue de Plasma, qui laisse aux applications
  ouvertes le temps d'enregistrer.
- **Revenir à la version précédente** (administrateur, avec une confirmation) : `bootc rollback`, quand une version
  précédente existe. Les documents et les réglages ne changent pas ; le retour prend effet au redémarrage.
- Les applications (Flatpak) restent dans Discover : un bouton les ouvre.

- **Comment** : `binixx_centre/misesajour.py` lit `rpm-ostree status --json` (réponse à un utilisateur ordinaire : version qui
  tourne, version préparée, version précédente). Les deux actions d'administrateur passent par `pkexec` et la règle polkit
  `org.binixx.mises-a-jour` (`auth_admin`), liée à `/usr/libexec/binixx/binixx-mises-a-jour`, qui n'accepte que `installer` et
  `retour`, jamais un texte venu de l'utilisateur. Chaque commande de la page tourne dans un `QProcess` : la fenêtre ne se fige pas.
- **En ligne de commande** (support, scripts d'entreprise) : `binixx-mises-a-jour etat|verifier [--json]`.
- **Pas de « date du test »** : la promotion en `stable` rebaptise l'image sans la modifier, elle ne porte donc pas la date de son
  test. La page affiche la date de la version et son canal.
- **Page sans bouton dans la barre latérale** : comme la barre des tâches, elle s'ouvre depuis Paramètres.
- **Tests** : `tests/image/centre/test_misesajour.py` (lecture de `rpm-ostree`, empreintes, taille, ligne de commande, page) ;
  la CI vérifie l'outil, la règle polkit et les programmes (`79-mises-a-jour.sh`) ; le test VM lit l'état du vrai système
  **avant la mise à jour, après la mise à jour (la version précédente est proposée) et après le retour arrière**, et vérifie
  qu'un utilisateur ordinaire ne peut ni installer ni revenir en arrière (`80-mises-a-jour.sh`).

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

## Taille du texte : un curseur de 100 % à 200 %

**Paramètres → Accessibilité → Taille du texte** : comme dans Windows, un seul curseur (100 % à 200 %, par pas de 10) agrandit
le texte du bureau et des applications. L'aperçu change en direct ; « Appliquer » écrit le réglage, « Rétablir la taille
d'origine » remet tout.

- **Comment** : KDE range ses polices dans `kdeglobals` (« Noto Sans,10,… » : famille, taille en points). L'outil multiplie la taille
  de six polices (interface, chasse fixe, plus petite lisible, barres d'outils, menus, titres de fenêtres) avec
  `kwriteconfig6 --notify` : les applications Qt et le bureau changent de police **tout de suite**, et le module GTK de KDE
  recopie la police dans les applications GTK. Rien d'autre ne bouge : ni les familles, ni les icônes, ni la mise à l'échelle de
  l'écran (qui reste dans Paramètres → Affichage).
- **Rien n'est perdu** : la première fois, les polices d'origine (ou leur absence : KDE reprend alors les siennes) sont gardées dans
  `~/.config/binixx/taille-du-texte.json`. Changer de taille repart toujours de ces polices (pas de cumul : 150 % puis 120 %
  donne 120 %, pas 180 %) ; « rétablir » les remet, **sauf celles que l'utilisateur a changées entre-temps** dans les réglages de
  KDE, qui deviennent la nouvelle référence.
- **Les pages web** gardent leur mise en page : Ctrl + molette dans le navigateur, comme d'habitude (la page le dit).
- **En ligne de commande** : `binixx-taille-texte etat | appliquer 100..200 | retablir`.
- **Page sans bouton dans la barre latérale** : elle s'ouvre depuis Paramètres, comme la barre des tâches.
- **Tests** : `tests/image/centre/test_taille_texte.py` (calcul, écriture, retour à l'origine, page) ; la CI vérifie les outils de
  KDE (`82-taille-texte.sh`) ; le test VM applique 150 % dans la vraie session, relit les polices dans `kdeglobals`, regarde si une
  application Qt les adopte, puis rétablit et vérifie que tout est **exactement comme avant**.

## Ambiances : l'allure du bureau en un clic

**Paramètres → Personnalisation → Thèmes : clair ou sombre** (ou **Accessibilité → Contraste élevé**) ouvre la page « Ambiances » :

| Ambiance | Ce qui change |
|---|---|
| **Aube** | Le thème clair de BinixX OS (couleurs `BinixXClair`). |
| **Nuit** | Le thème sombre de BinixX OS (couleurs `BinixXSombre`). Les icônes de Breeze s'assombrissent ou s'éclaircissent tout seules avec les couleurs. |
| **Contraste élevé** | Noir, blanc et jaune (couleurs `BinixXContraste`, `usr/share/color-schemes/`) : texte blanc sur fond noir, sélection et focus en jaune, barre de titre jaune pour la fenêtre active. |

« **Grand texte** » est un interrupteur à part, qui se combine avec n'importe quelle allure : texte à 130 % (la logique de « Taille du
texte », ci-dessus) et pointeur de souris plus gros (36 au lieu de 24).

- **Comment** : l'allure se pose avec les outils de Plasma (`plasma-apply-lookandfeel` pour le thème global, puis
  `plasma-apply-colorscheme` pour le schéma de couleurs ; `lookandfeeltool` si le premier manque) :
  les couleurs, les icônes et les fenêtres changent tout de suite, y compris dans les applications ouvertes. Le fond d'écran a une
  version claire et une version sombre que Plasma choisit tout seul selon les couleurs.
- **Sans écran** (ssh, test VM) : les outils `plasma-apply-*` démarrent une application Qt et s'arrêtent sans écran ; l'outil
  leur donne alors la plateforme `offscreen` (ils écrivent les réglages et préviennent les applications par D-Bus). Avec un
  écran, rien ne change.
- **Aube au départ** : tant qu'on n'a rien choisi, le schéma de couleurs n'est pas dans `kdeglobals` mais dans
  `~/.config/kdedefaults/kdeglobals` (le thème global de BinixX OS) : la page le lit aussi, et annonce donc « Aube » sur une
  installation neuve.
- **On vérifie** : après chaque pose, `kdeglobals` est relu. L'outil ne dit « c'est en place » que si le schéma voulu y est vraiment ;
  un outil qui répond « réussi » sans rien écrire (constaté pour `plasma-apply-cursortheme --size`) ne suffit pas : pour le pointeur,
  l'écriture directe de `cursorSize` dans `kcminputrc` prend alors le relais (effet à la prochaine ouverture de session). Pour les
  couleurs il n'y a pas de repli par écriture du nom : sans les couleurs que l'outil copie, il ne changerait rien à l'écran.
  L'ambiance en cours se reconnaît à son schéma de couleurs ; des couleurs choisies à la main ailleurs sont signalées comme
  « personnalisées » et remplacées au prochain clic.
- **Contraste vérifié par les tests** : `BinixXContraste.colors` est analysé par `test_ambiances.py` ; texte normal d'au moins **7:1**
  (niveau AAA de la norme WCAG) sur le fond et le fond alterné, autres textes (liens, erreurs, grisés…) d'au moins 4,5:1, focus et
  survol d'au moins 7:1, sélection nettement détachée du contenu.
- **Contraste élevé retire une couleur d'accentuation choisie à la main** (`AccentColor` de `kdeglobals`) : elle écraserait le
  jaune. Aube et Nuit n'y touchent pas.
- **Grand texte** garde les tailles d'avant (`~/.config/binixx/grand-texte.json` pour le pointeur, `taille-du-texte.json` pour le
  texte). « Désactiver » les remet ; si le texte a été réglé à la main sur une autre taille entre-temps (« Taille du texte »), il est
  laissé tel quel et seul le pointeur est remis.
- **Pas de réglage fin des couleurs ici** : la page renvoie vers Configuration du système (« Couleurs, icônes et pointeur »).
- **En ligne de commande** : `binixx-ambiance liste | etat | appliquer aube|nuit|contraste | grand-texte oui|non`.
- **Tests** : `tests/image/centre/test_ambiances.py` (schéma, outils de Plasma et leurs secours, Grand texte, ligne de commande, page) ;
  la CI vérifie les outils (`83-ambiances.sh`) ; le test VM pose les trois ambiances dans la vraie session, relit `kdeglobals`
  (nom du schéma **et** couleurs copiées), active Grand texte, puis vérifie après le redémarrage de la mise à jour que Contraste
  élevé et Grand texte ont survécu avant de tout remettre.

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
