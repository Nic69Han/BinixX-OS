# Feuille de route

État au 3 octobre 2026. Une ligne = une pull request.

## Objectif

Devenir **la référence pour quitter Windows au bureau**, pour les particuliers et les PME, en France puis
en Europe. Pas « une distribution Linux de plus » : un poste de travail qui ressemble à Windows, qui
ne casse pas et dont chaque version est testée avant d'arriver chez l'utilisateur.

Pourquoi maintenant :

- **Windows 10** : plus de support depuis octobre 2025 ; les mises à jour de sécurité payantes ou
  gratuites des particuliers s'arrêtent le **12 octobre 2027**. Beaucoup de PC ne passent pas à Windows 11.
- **État et Europe** : la DINUM a annoncé en avril 2026 le passage des postes de l'État à Linux ;
  chaque ministère rend son plan à l'automne 2026. Danemark et Schleswig-Holstein font de même.
- **Précédents** : Zorin OS 18 (2 millions de téléchargements en 3 mois, aux trois quarts des
  utilisateurs Windows) et Bazzite (même base que BinixX OS, devenue connue grâce à une promesse simple).

## Règles pour chaque PR

- Une proposition par PR, avec ses tests : contenu de l'image (`check-image.sh`) et, si le système
  change, test complet en VM sur l'image de la branche (`test-vm.yml`, option `build`).
- Fusion automatique quand la construction et le test VM sont verts sur le dernier commit.
- Rien n'atteint les postes (`stable`) sans le test VM sur `main`.

## Lot 1 — Socle de sécurité

Menaces visées, pour un poste de bureau : hameçonnage et publicités piégées, rançongiciels, logiciels
malveillants téléchargés, vol ou perte du PC, réseaux Wi-Fi publics, mises à jour non appliquées,
mise à jour du système compromise à la source.

Déjà en place : Secure Boot, SELinux en mode strict (enforcing), `/usr` en lecture seule, mises à jour
automatiques testées avec retour arrière, applications isolées (Flatpak), les `.exe` ne s'exécutent pas.

| PR | Contenu | Critères d'acceptation |
| --- | --- | --- |
| **S1. Durcissement du poste** | Pare-feu : zone `binixx` par défaut (aucune connexion entrante sauf découverte du réseau local, voisinage Windows, KDE Connect), au lieu de la zone Fedora qui ouvre les ports 1025 à 65535. SSH désactivé par défaut. Réglages du noyau (journaux du noyau et adresses réservés à l'administrateur, pas de débogage d'un autre programme, pas de redirections ICMP). Firefox : uBlock Origin installé d'office, mode HTTPS uniquement, télémétrie coupée. Guide `securite.md` et politique de signalement des failles (`SECURITY.md`). | Image : zone et services du pare-feu, SSH non activé, fichier sysctl, règles Firefox valides. VM : pare-feu actif sur la zone `binixx`, valeurs du noyau appliquées, mises à jour automatiques (système et Flatpak) programmées. |
| **S2. Images signées et vérifiées** | Signature Cosign à chaque publication ; sur les postes, refus de toute image de `ghcr.io/nic69han/binixx` non signée par la clé BinixX OS (aujourd'hui : acceptée sans vérification). **Action du propriétaire** : créer la paire de clés et le secret `SIGNING_SECRET`. | Image : clé publique et règle `sigstoreSigned`. VM : mise à jour signée acceptée ; image non signée refusée. |
| **S3. Chaîne d'approvisionnement** | **Livré** : inventaire des logiciels de chaque image (SBOM CycloneDX), avis de sécurité Fedora en attente avec seuil bloquant (`Critical` par défaut, réglable), attestations de provenance et de SBOM GitHub : [securite.md](securite.md#chaîne-dapprovisionnement--ce-quil-y-a-dans-limage-doù-elle-vient). Trivy et Grype ne couvrent pas Fedora : la source est celle de Fedora (`dnf updateinfo`). | SBOM et rapport joints à chaque build ; build rouge si une vulnérabilité critique corrigeable est présente. |
| **S4. Chiffrement et PC perdu** | Chiffrement proposé à l'installation, déverrouillage par la puce TPM sans mot de passe supplémentaire (`ujust setup-luks-tpm-unlock`, déjà dans l'image), documenté pas à pas ; option antivirus (ClamTk) pour les PME qui doivent en justifier un. **Livré** : page « Protéger mes données » du Centre BinixX OS, avec création et remplacement de la **clé de récupération** du disque chiffré. | Test VM d'une installation chiffrée qui redémarre seule grâce au TPM virtuel. Test VM de la clé de récupération sur un volume LUKS2 : **fait**. |

## Lot 2 — Applications

| PR | Contenu | Critères d'acceptation |
| --- | --- | --- |
| **A1. Choix des applications** | **Livré en grande partie** : page « Installer des applications » du Centre BinixX OS, comme Ninite : cases à cocher avec les noms connus sous Windows (VLC, LibreOffice, Spotify, Discord, Bitwarden, GIMP, RustDesk…), licence affichée et applications propriétaires signalées, installation d'un coup avec un seul mot de passe ([centre-binixx.md](centre-binixx.md#installer-des-applications)). Reste : la proposer à la première ouverture de session ; sélection par fichier pour les images d'entreprise. | Test VM : la commande de la page installe une vraie application depuis Flathub : **fait**. |
| **A2. Microsoft 365 en applications** | Lanceurs Outlook, Word, Excel, PowerPoint et OneDrive en ligne, comme les web apps Teams/Zoom. | Lanceurs valides ; ouverture dans une fenêtre dédiée. |
| **A3. Programmes Windows** | **Livré en grande partie** (« Mon logiciel Windows », lot 6) : au double-clic sur un `.exe` ou un `.msi`, le Centre BinixX OS cherche l'équivalent connu ; Bottles est proposé **à la demande** (pas préinstallé : compatibilité non garantie, il ne faut pas la promettre). Reste : table des installeurs courants plus large. | Test : un installeur connu propose son équivalent ; un inconnu propose Bottles. |

## Lot 3 — Migration et matériel

| PR | Contenu | Critères d'acceptation |
| --- | --- | --- |
| **M1. Assistant de migration** | **Livré** (« Récupérer mes fichiers Windows ») : Documents, Bureau, Images, Musique, Vidéos, Téléchargements et favoris du navigateur depuis l'ancien disque Windows, une clé USB ou un dossier, sans rien écraser : [migration-windows.md](migration-windows.md#récupérer-ses-fichiers--récupérer-mes-fichiers-windows). Reste : lire une sauvegarde « Historique des fichiers », importer les mots de passe. | Test VM avec un faux profil Windows : fichiers et favoris retrouvés. |
| **M2. Vieux PC** | Cible 4 Go de mémoire : le test VM tourne avec 4 Go ; services d'arrière-plan allégés si besoin. | Test VM complet vert à 4 Go. |
| **M3. Essayer sans installer** | ISO « live » : BinixX OS démarre depuis la clé USB, sans toucher au disque, avec un bouton « Installer ». | Test de démarrage de l'ISO live jusqu'au bureau. |

## Lot 4 — Zéro terminal

Un utilisateur de Windows n'ouvre pas de terminal. Toute tâche courante d'utilisation ou d'administration
doit se faire à la souris ; la documentation donne d'abord le chemin graphique.

| PR | Contenu | Critères d'acceptation |
| --- | --- | --- |
| **U1. Centre d'administration** | Cockpit, la console d'administration web de Fedora, accessible seulement depuis le PC lui-même (lanceur « Administration du PC ») : rejoindre un domaine Active Directory, mises à jour et retour arrière, pare-feu, disques et chiffrement, services, journaux, comptes. Pare-feu aussi dans Configuration du système (plasma-firewall). Guide `administration.md` : chaque tâche, son chemin à la souris. | Image : paquets, socket limité à localhost, lanceur. VM : console joignable en local seulement, modules détectés. |
| **U2. Assistants BinixX OS sans terminal** | Page « BinixX OS » dans le centre d'administration : déverrouillage du disque par la puce TPM (avec l'avertissement AMD Zen 1 à 3), ouverture de l'accès à distance (SSH, bureau à distance) en un clic, et OneDrive avec connexion par le navigateur et fichiers à la demande (montage rclone) au lieu de l'assistant en terminal. | Test VM de chaque action sans saisie au clavier. |
| **U3. Console Active Directory** | Pour l'administrateur d'une PME : ADMC (équivalent libre des consoles Windows « Utilisateurs et ordinateurs » et « Gestion des stratégies de groupe »), à empaqueter : il n'est ni dans Fedora ni sur Flathub. | Construction reproductible ; démarrage de l'application en VM. |

## Lot 5 — Se faire connaître

| PR | Contenu |
| --- | --- |
| **L1. Site et README public** | Page d'accueil (FR/EN) avec la promesse en une phrase, la vidéo de démonstration et les résultats du dernier test. **Décision du propriétaire** : publication du README. |
| **L2. Notes de version** | À chaque version `stable` : ce qui change, résultats des tests, capture du bureau. |

Hors dépôt : lancement sur LinuxFr.org, Reddit, Hacker News et DistroWatch ; campagne End of 10 et
repair cafés ; reconditionneurs de PC ; prestataires informatiques des PME.

## Lot 6 — Accueil, aide et entreprise

Proposés le 2 octobre 2026 à partir des idées inspirées d'autres distributions (Zorin, Bazzite, Ubuntu
Pro, Windows Autopilot). Chaque ligne est une pull request, empilée sur le socle `modules.d` / `checks.d`.

| PR | Contenu | État |
| --- | --- | --- |
| **C1. Centre BinixX OS : Accueil** (#18) | Application PySide6 à pages ; accueil en français pour qui vient de Windows, ouvert une fois à la première session ; Centre de bienvenue de KDE désactivé. | Livré |
| **C2. Mon logiciel Windows** (#19) | Catalogue de 64 équivalents (Word, Excel, Sage, Photoshop…), recherche sans accents, ouverture des `.exe` / `.msi` ; Bottles à la demande. | Livré |
| **C3. Obtenir de l'aide** (#20) | Sept cas fréquents sans IA, rapport de diagnostic sans secret, bureau réinitialisable. | Livré |
| **E1. Image d'entreprise** (#17) | Gabarit `entreprise/` (nom, paquets, Flatpak, page d'accueil, proxy), modèles de CI et d'ISO, guide en six étapes. | Livré |
| **R1. Retour arrière automatique** (#21) | greenboot : trois démarrages en échec, retour à la version précédente ; test VM de bout en bout. | Livré |
| **G1. Variante NVIDIA** (#22) | Image `binixx-nvidia` construite et testée comme `binixx`. Fusionnée comme **expérimentale** ; validation sur matériel réel attendue. | Livré (expérimental) |
| **D1. Créer nouveau** (#23) | Document texte, Classeur, Présentation vierges (.docx, .xlsx, .pptx) dans Dolphin. | Livré |

## Lot 7 — Études (aucun code livré)

| Étude | Document | Décision attendue |
| --- | --- | --- |
| Solutions libres à intégrer (MIT ou permissives) | [solutions-mit.md](solutions-mit.md) | Lesquelles entrent dans le catalogue ou l'image |
| Copilote IA (expliquer, agir avec confirmation, administrer) | [ia-copilote.md](ia-copilote.md) | Moteur par défaut, niveau de départ |
| Gestion d'un parc de PC | [gestion-de-flotte.md](gestion-de-flotte.md) | Besoin réel des PME visées |
| Traité | Clé de récupération du disque chiffré, pack jeux, remise à zéro du système, Windows en machine virtuelle | Voir le lot 8 : la « réinstallation complète » a été remplacée par « Réparer le système », jugée plus sûre |

## Lot 8 — Autour du Centre BinixX OS (2 octobre 2026)

Ce que les études du lot 7 sont devenues. Chaque ligne est une pull request ; « Livré » = fusionnée après construction et test VM verts.

| PR | Contenu | État |
| --- | --- | --- |
| **K1. Clé de récupération du disque chiffré** (#26) | Page « Protéger mes données » : création et remplacement de la clé (équivalent de celle de BitLocker), testée sur un vrai volume LUKS2. | Livré |
| **J1. Jeux à la demande** (#27) | Steam, Heroic, Lutris, Prism, ProtonUp-Qt, jeu en streaming : rien d'installé d'office, carte graphique et manettes détectées. | Livré |
| **R2. Réparer le système** (#28) | Remet **un réglage** de `/etc` comme dans l'image, avec sauvegarde et annulation ; remplace le « Réinitialiser BinixX OS » complet, qui aurait effacé comptes et réseaux. | Livré |
| **W1. Windows complet** (#29) | Le PC est-il prêt (virtualisation, mémoire, espace) ? Boxes, WinBoat (expérimental) ou Windows 365 ; Podman Compose et FreeRDP 3 dans l'image. **WinBoat reste à valider à la main sur un vrai PC.** | Livré |
| **T1. Test VM : retour arrière** (#30) | Le test n'exige plus d'attraper par SSH la mise à jour défectueuse (créneau de quelques secondes) : il lit un compteur de démarrages. Avait fait échouer `main` et la variante NVIDIA. | Livré |
| **M1. Récupérer mes fichiers Windows** (#31) | Documents, photos, musique, favoris depuis l'ancien disque, une clé USB ou un dossier, sans rien écraser. | Livré |
| **S3. Chaîne d'approvisionnement** (#32) | SBOM CycloneDX, avis de sécurité Fedora avec seuil bloquant, attestations de provenance. | Livré |
| **G1. Variante NVIDIA** (#22) | Fusionnée comme **expérimentale** (image séparée `binixx-nvidia`) ; tests VM des deux images verts. | Livré (expérimental) |

Reste à faire, sans décision du propriétaire : choix des applications au premier démarrage (A1), notes de version (L2), console
Active Directory (U3), assistants sans terminal (U2).

## Lot 9 — Idées prises à Zorin OS et à Deepin (2 octobre 2026)

Choisies avec le propriétaire après comparaison ; chaque ligne est une pull request.

| PR | Contenu | Inspiré de | État |
| --- | --- | --- | --- |
| **P1. Paramètres** | Un seul écran, catégories et noms de Windows 11, recherche, touche Windows + I : [centre-binixx.md](centre-binixx.md#paramètres). | Centre de contrôle de Deepin | Livré |
| **Style commun** | Le style moderne de Paramètres (en-tête en dégradé, cartes à pastille, pictogrammes) appliqué à toutes les pages, une couleur par page : [centre-binixx.md](centre-binixx.md#présentation-commune). | Retour du propriétaire | Livré |
| **Fond d'écran signature** | « Le marcheur de l'aube » : un homme seul, simple silhouette sombre, marche vers le soleil qui se lève sur une planète, ciel étoilé (clin d'œil au Petit Prince) ; clair et sombre, 1080p et 4K, calculé par `branding/fond_ecran.py` : [identite-visuelle.md](identite-visuelle.md#le-fond-décran). | Le fond « Bliss » de Windows XP | En test |
| **P2. Disposition de la barre** | Barre en bas (comme Windows) ou en haut, en un clic : page ouverte depuis Paramètres, maquette de chaque choix, déplacement immédiat dans la session : [centre-binixx.md](centre-binixx.md#barre-des-tâches--en-bas-ou-en-haut). | Zorin Appearance | En test |
| **P3. Créer une application web** | Transformer n'importe quel site (intranet, logiciel de gestion en ligne) en application du menu. | Outil « Web Apps » de Zorin OS 18 | À faire |
| **P4. Clé USB bootable** | « Rufus / Etcher » dans le catalogue, vers l'outil KDE d'écriture d'ISO : installer BinixX OS sur le PC suivant. | Deepin Boot Maker | À faire |
| **P5. Poste partagé** | Option de l'image d'entreprise : la session repart propre à chaque redémarrage (réception, borne, salle de formation). | « Restauration sans souci » de Deepin 25 | À faire |

Écartés pour l'instant : synchronisation des réglages dans le nuage (serveur nécessaire), IA intégrée (en attente),
édition « Lite » (seconde image à maintenir), partitions système et données séparées et instantanés des fichiers Btrfs
(à voir à la refonte de l'ISO).

## Lot 10 — Idées prises à Omarchy et aux distributions en vogue (3 octobre 2026)

Veille du 3 octobre 2026. Rien n'est lancé : **le propriétaire choisit** dans la première table (« Proposé »). Critères de tri :
servir un particulier ou une PME qui quitte Windows, tenir dans Plasma et dans l'image `bootc`, se tester en VM. Omarchy vise des
développeurs au clavier (Hyprland, mosaïque de fenêtres) : on lui prend le principe « tout est déjà choisi et cohérent », pas son
bureau.

| PR | Contenu | Inspiré de | Preuve attendue | État |
| --- | --- | --- | --- | --- |
| **O1. Recherche unique** | Une petite fenêtre (Windows + S) ouvre une seule recherche : applications, réglages (l'index de Paramètres), fichiers, catalogue « Mon logiciel Windows », aide. | Palette de commandes d'Omarchy 4 (une touche, lanceur et menu réunis) | VM : « imprimante » ouvre le réglage d'impression, « word » son équivalent, « onlyoffice » un Flatpak ([détails](centre-binixx.md#recherche-unique--windows--s)) | En test |
| **O2. Aide-mémoire des raccourcis** | Page « Raccourcis » : les combinaisons de Windows que l'on a dans les doigts (Windows + E, D, L, V, point pour les émojis, flèches, Maj + S pour la capture) et qui marchent. Avant, l'image n'en fournissait qu'un (Windows + I) ; s'y ajoutent Windows + R, Ctrl + Maj + Échap et Windows + Maj + S, et Windows + E est garanti ([détails](centre-binixx.md#raccourcis--laide-mémoire-de-windows)). | Aide-mémoire d'Omarchy (Super + K) | VM : chaque raccourci annoncé est enregistré dans la session | En test |
| **O3. Ambiances** | Un clic change d'un coup thème clair ou sombre, couleur d'accent, fond d'écran, icônes et pointeur : *Aube* (clair), *Nuit* (sombre), *Contraste élevé*, *Grand texte*. Prolonge « Thèmes : clair ou sombre ». | Thèmes cohérents d'Omarchy (terminal, éditeur, notifications, verrouillage) | Image : chaque ambiance pose les réglages attendus. VM : elle survit au redémarrage | Proposé |
| **O4. Taille du texte, un seul curseur** | Un réglage agrandit le texte partout (bureau, applications Qt et GTK, Firefox), comme « Taille du texte » de Windows > Accessibilité ; aujourd'hui il faut passer par Polices et Affichage. Fait : Paramètres → Accessibilité → Taille du texte, 100 % à 200 %, les polices d'origine sont gardées pour tout remettre ([détails](centre-binixx.md#taille-du-texte--un-curseur-de-100--à-200-)). | Réglage unique d'échelle du texte d'Omarchy 4 | VM : valeurs relues dans la session | En test |
| **O5. Un clic pour le rapport d'erreurs** | Quand une application plante, proposer d'ouvrir le rapport de diagnostic sans secret (C3) et de l'enregistrer ou de l'envoyer à l'informaticien. *Idée de synthèse, pas une fonction d'Omarchy.* | Esprit « le système aide » ; Rapport d'erreurs Windows | VM : plantage provoqué, rapport créé sans mot de passe | Proposé |
| **O6. Canaux de mise à jour** | Choix « Stable » (par défaut) ou « En avance » ; en entreprise, un poste pilote reçoit la version avant le parc (anneaux, comme Windows Update). **L'étiquette `testing` n'a pas encore passé le test VM** : réservée aux testeurs. | Canaux stable, RC, edge et dev d'Omarchy | VM : passage à `testing` et retour à `stable`, retour arrière compris | Proposé |
| **O7. Page « Mises à jour » complète** | Avant : Paramètres renvoyait à Discover. Maintenant une page à part : version installée et canal, recherche avec taille du téléchargement, « Installer maintenant », « Redémarrer pour appliquer », « Revenir à la version précédente » ([détails](centre-binixx.md#mises-à-jour--une-page-comme-windows-update)). Pas de « date du test » : la promotion en stable ne la garde pas. | Update Manager de Linux Mint ; retour arrière visible de KDE Linux | VM : état lu dans `bootc status`, retour arrière (R1) | En test |
| **O8. Poste préconfiguré** | L'image d'entreprise prépare le PC (compte, domaine Active Directory, Wi-Fi, applications) avant la livraison ; l'utilisateur n'a plus qu'à ouvrir sa session. À étudier avec E1 (gabarit d'entreprise). | Mise en service différée d'Omarchy 4 ; Windows Autopilot | VM : un fichier de réglages pose le compte et le domaine | À étudier |
| **O9. Fonctionnalités facultatives** | Une page comme « Activer ou désactiver des fonctionnalités Windows » : Windows en machine virtuelle (W1), jeux (J1), conteneurs de développement, accès à distance, imprimantes… réunis, avec leur état. | AnduinOS : composants à la carte (boutique d'applications, outils pro, conteneurs, WSL) | VM : chaque interrupteur testé | Proposé |
| **O10. Capture et texte d'une image** | Windows + Maj + S pour capturer, enregistrer l'écran, copier le texte d'une image (OCR), pipette à couleur. **À vérifier d'abord : ce que Spectacle (déjà présent) sait faire.** | Raccourcis capture, enregistrement, OCR et pipette d'Omarchy | Image : outil et raccourcis présents | À étudier |

**À garder pour la refonte de l'ISO** (voir la décision 7) :

- **Installer à côté de Windows** : double démarrage guidé, sans effacer Windows (Omarchy 4 vient de l'ajouter ; c'est l'étape intermédiaire de beaucoup de nouveaux venus).
- **ISO plus légère et installation plus rapide** : Omarchy 4 a retiré plus d'un gigaoctet et gagné 30 %. Notre ISO pèse environ 5 Go.
- **Instantanés des fichiers (Btrfs)** : CachyOS (Snapper) et Omarchy en proposent. BinixX OS protège le *système* (`bootc`, greenboot) mais l'historique des *fichiers* repose sur Déjà Dup. À trancher avec le choix du système de fichiers à l'installation.
- **Démarrage discret, menu de secours après un échec** (KDE Linux) : à comparer avec ce que greenboot et GRUB font déjà.
- **Clé USB persistante** (MX Linux), à rapprocher de M3 (essayer sans installer).

**Déjà couvert, aucune nouvelle PR** : retour arrière des mises à jour (R1), « réinitialiser l'ordinateur » d'Omarchy (remplacé volontairement par R2, plus sûr : il n'efface pas les comptes), applications web préconfigurées (A2 et P3), mosaïque et dispositions de fenêtres (PR #15, inspirée de Zorin).

**Ordre proposé** si le propriétaire valide : O2, puis O7 (voir que les mises à jour et le retour arrière existent rassure), O1, O4, O3 ; le reste ensuite.

### Ce que font les distributions en vogue

Classement DistroWatch cité par la presse en juin et juillet 2026 : il mesure les **visites de pages par jour**, pas le nombre
d'utilisateurs. Tendances communes : **spécialisation** plutôt que distribution généraliste, systèmes **immuables** de plus en plus
courants, **jeux** devenus grand public, **passage depuis Windows** simplifié (Windows 10 : fin des mises à jour fin 2025, prolongée
pour les particuliers jusqu'au 12 octobre 2027).

| Distribution | Pourquoi on en parle | Ce qu'on en retient pour BinixX OS |
| --- | --- | --- |
| **CachyOS** (1re, depuis plus de 18 mois) | Noyau et paquets optimisés pour les processeurs récents, KDE Plasma, Btrfs et Snapper (retour arrière), ISO pour consoles portables, outils graphiques malgré la base Arch | Instantanés de fichiers (ISO). Recompiler pour chaque processeur : hors de portée sur une base Fedora |
| **Linux Mint** (2e) | La porte d'entrée classique : Cinnamon proche de Windows, stabilité, aucune surprise | O7 : un gestionnaire de mises à jour clair ; « rien ne change sans prévenir » |
| **MX Linux** (3e) | Vieux PC, MX Tools (réglages et instantanés à la souris), clé USB persistante | M2 est déjà là ; O9 ; clé persistante à étudier |
| **Pop!_OS 24.04 et COSMIC 1.0** (5e) | Bureau écrit en Rust, mosaïque de fenêtres par espace de travail, fenêtres empilées en onglets, bon support NVIDIA | Rien à ajouter : nos dispositions de fenêtres (PR #15) couvrent le besoin d'un utilisateur de Windows |
| **Zorin OS 18** (6e) | Plus de 2 millions de téléchargements en 3 mois, trois quarts depuis Windows | Notre référence directe : lot 9 |
| **Fedora 44** (7e) | GNOME 50, NTSYNC pour les jeux | Hérité gratuitement de la base |
| **AnduinOS** (9e) | Windows 11 sur Ubuntu 26.04 et GNOME 50, composants à la carte, version ARM64, **IA locale facultative** (2.0.1, juillet 2026) | O9. Argument de plus pour l'étude du copilote IA (en attente) : facultative, jamais d'office. ARM64 impossible : notre base n'existe qu'en x86_64 |
| **Bazzite** (10e) | Immuable et jeux, mode console, **même base que BinixX OS** | J1 est déjà livré ; prouve que l'immuable passe auprès du grand public |
| **KDE Linux** (alpha depuis septembre 2025) | Distribution officielle de KDE, immuable ; mises à jour par différences (de 7 Go à 1 ou 2 Go) ; menu de démarrage caché sauf après un échec | **À surveiller** : concurrent direct sur « KDE immuable ». Notre différence : le passage depuis Windows, un test de chaque version, les PME |
| **Omarchy** (DHH, 37signals) | Tout est choisi d'avance, clavier, thèmes cohérents, canaux de mise à jour, retour arrière par instantanés | Voir O1 à O10 |

Sources consultées le 3 octobre 2026 : [Omarchy 4.0](https://newreleases.io/project/github/omacom/omarchy/release/v4.0.0),
[manuel d'Omarchy](https://learn.omacom.io/2/the-omarchy-manual.md),
[top 10 de juin et juillet 2026](https://linux.how2shout.com/top-10-most-popular-linux-distributions-in-june-july-2026/),
[CachyOS, Mint et MX Linux comparés](https://www.howtogeek.com/most-popular-linux-distros-april-2026-ranked/),
[Zorin OS et la fin de Windows 10](https://www.windowscentral.com/microsoft/windows-10/windows-10-retirement-pushes-780-000-users-to-linux-as-zorin-os-hits-1m-downloads),
[AnduinOS](https://www.neowin.net/news/windows-11-like-anduinos-14-and-15-lts-plans-revealed/),
[KDE Linux](https://news.itsfoss.com/kde-linux-alpha),
[COSMIC 1.0](https://linuxiac.com/pop_os-24-04-lts-launches-with-cosmic-desktop-1-0-stable/),
[Bazzite](https://en.wikipedia.org/wiki/Bazzite_(operating_system)),
[prolongation de Windows 10 à octobre 2027](https://office-watch.com/2026/windows-10-extended-security-updates-2027/).

## Décisions et actions du propriétaire

1. Créer la clé de signature (S2) : `cosign generate-key-pair`, contenu de `cosign.key` dans le secret
   `SIGNING_SECRET` du dépôt, `cosign.pub` à la racine du dépôt. Ne jamais publier `cosign.key`.
2. Activer le signalement privé des failles dans les réglages du dépôt (S1).
3. ~~Suite bureautique par défaut~~ **Décidé** : OnlyOffice (meilleure fidélité Microsoft) ; LibreOffice reste proposée dans A1.
4. Publication du README et du site (L1).
5. ~~Variante NVIDIA (G1)~~ **Décidé** : fusion comme variante expérimentale. À faire : un essai sur une vraie carte, puis
   décision sur l'assistant de passage à `binixx-nvidia`.
6. **En attente** (le propriétaire a demandé de patienter) : copilote IA (moteur par défaut, « aucun » recommandé ; niveau de
   départ) et Coucou (réécriture pour Plasma ou idée seulement). Rien n'est lancé tant que ce n'est pas tranché.
7. **ISO publique : refaite en dernier**, une fois `stable` à jour avec tous les chantiers ci-dessus.
8. Essais sur matériel réel avant de promettre : WinBoat (W1), disque Windows NTFS et BitLocker (M1), carte NVIDIA (G1).
9. Choisir dans le lot 10 (O1 à O10) ce qui est lancé, et dans quel ordre ; ordre proposé : O2, O7, O1, O4, O3.
