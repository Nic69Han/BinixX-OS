# Passer de Windows à NicOS

Ce guide s'adresse à la personne qui migre un poste (ou à celle qui l'accompagne).

## Avant de changer de système

- **Sauvegarder les fichiers** (Documents, Bureau, Images, Téléchargements) sur un disque externe ou un
  cloud. L'installation de NicOS efface le disque.
- **Courriel** : noter les paramètres des comptes (serveurs IMAP/SMTP ou compte Microsoft 365 / Gmail).
  Thunderbird configure seul la plupart des comptes à partir de l'adresse et du mot de passe.
  Avec Outlook en POP et des fichiers `.pst`, importer d'abord le courrier dans Thunderbird **sous Windows**.
- **Mots de passe du navigateur** : les exporter depuis Edge ou Chrome (fichier CSV), puis les importer dans
  Firefox. Plus simple : activer la synchronisation Firefox avant la migration.
- **Logiciels métiers** : vérifier chacun dans [compatibilite.md](compatibilite.md). Un logiciel Windows
  (`.exe`) ne s'installe pas sur NicOS.
- **Licences** : noter la clé Windows si le PC doit pouvoir revenir en arrière.

## Où retrouver ses habitudes

> Pour un logiciel précis (Word, Sage, Photoshop…), l'application **« Mon logiciel Windows »** (menu, ou
> double-clic sur un `.exe` ou un `.msi`) donne l'équivalent sous NicOS : voir [centre-nicos.md](centre-nicos.md).

| Sous Windows | Sous NicOS |
| --- | --- |
| Menu Démarrer, touche Windows | Logo NicOS en haut à gauche, touche Windows (même comportement, recherche comprise) |
| Barre des tâches, épingler une application | Même principe, mais la barre est **en haut** de l'écran : clic droit sur l'icône → « Épingler au gestionnaire de tâches ». Elle se déplace en bas par clic droit → « Modifier le tableau de bord » |
| Explorateur de fichiers | Dolphin (Windows + E) |
| Word, Excel, PowerPoint | OnlyOffice (ouvre et enregistre directement les .docx, .xlsx, .pptx). Avec un abonnement Microsoft 365 : « Word (web) », « Excel (web) », « PowerPoint (web) » dans le menu |
| Clic droit → Nouveau → Document Word, Classeur Excel, Présentation PowerPoint | Clic droit dans un dossier → **Créer nouveau** → « Document texte », « Classeur », « Présentation » : un fichier .docx, .xlsx ou .pptx vierge (A4, Calibri 11, français), qui s'ouvre dans OnlyOffice |
| Outlook (nouvel Outlook), OneDrive en ligne | « Outlook (web) » et « Microsoft 365 (web) » dans le menu, ou Thunderbird pour le courriel |
| Outlook | Thunderbird (courriel, agenda, contacts) |
| Edge, Chrome | Firefox |
| Teams, Zoom, Slack | Web apps du même nom dans le menu (fenêtre dédiée, partage d'écran possible) |
| Lecteur PDF | Okular |
| OneDrive | « OneDrive » dans le menu : connecte le compte Microsoft et synchronise les fichiers dans le dossier OneDrive (tous les fichiers sont téléchargés : pas de « fichiers à la demande ») |
| Bloc-notes | KWrite |
| Outil Capture d'écran | Spectacle (touche Impr. écran) |
| Photos | Gwenview |
| Lecteur multimédia, Films et TV | Haruna (ouvre les .mp4, .avi, .wmv…) |
| Connexion Bureau à distance (mstsc) | Remmina |
| Historique des fichiers, Sauvegarde | Déjà Dup (« Sauvegardes ») : sur un disque externe ou un service cloud |
| Calculatrice | KCalc |
| Paramètres, Panneau de configuration | Configuration du système |
| Gestion de l'ordinateur, Observateur d'événements, Gestion des disques | « Administration du PC » (voir [administration.md](administration.md)) |
| Windows Update | Automatique ; suivi dans Discover (« Mises à jour ») |
| Microsoft Store | Discover |
| Imprimer en PDF | Imprimante « Imprimante PDF » (fichier enregistré sur le Bureau), ou « Imprimer dans un fichier » |
| Gestionnaire des tâches (Ctrl + Maj + Échap) | Moniteur système (Ctrl + Échap) |
| VPN (Paramètres → Réseau → VPN) | Configuration du système → Connexions → « + » : L2TP/IPsec, IKEv2, SSTP, OpenVPN, Cisco AnyConnect, WireGuard |

Raccourcis identiques : Alt + Tab, Ctrl + C / V / X / Z, Windows + L (verrouiller), Windows + D (bureau),
Alt + F4 (fermer), Windows + flèches (ancrer une fenêtre à gauche ou à droite).

Dispositions de fenêtres, comme les « Snap Layouts » de Windows 11 : faire glisser une fenêtre
vers le haut de l'écran fait apparaître trois dispositions (deux colonnes, deux lignes, quatre
quarts) ; la lâcher sur une case l'y range. La lâcher tout en haut l'agrandit, comme sous
Windows.

## Les premiers jours

- **Applications au premier démarrage** : OnlyOffice, Thunderbird, Remmina… se téléchargent pendant les
  premières minutes, PC connecté à Internet (Firefox est déjà là). Si le menu semble incomplet, patienter puis se reconnecter.
- **Polices** : les documents en Calibri, Cambria, Arial, Times New Roman ou Segoe UI s'affichent avec des
  polices de même largeur, donc même mise en page. Seul le dessin des lettres change légèrement.
- **Mises à jour** : elles s'installent en arrière-plan et s'appliquent au redémarrage. En cas de problème
  après une mise à jour, choisir la version précédente dans le menu de démarrage, ou
  `sudo bootc rollback` puis redémarrer.
- **Installer une application** : Discover, comme un magasin d'applications. Les applications viennent de
  Flathub et fonctionnent isolées du système, qui reste intact.

## En entreprise : domaine Active Directory

Un PC NicOS peut rejoindre le domaine Windows de l'entreprise : chacun ouvre alors sa session avec son
compte habituel (`prenom.nom@entreprise.local` sur l'écran de connexion) et son dossier personnel est créé
à la première connexion. Une fois, par l'administrateur, avec un compte autorisé à joindre des PC :

```
sudo realm join --user=administrateur entreprise.local
```

`realm list` vérifie la jonction ; `sudo realm leave` l'annule.

## Obtenir de l'aide

Ouvrir une *issue* sur le dépôt GitHub du projet en précisant le modèle du PC, ce qui était attendu et ce
qui s'est produit.
