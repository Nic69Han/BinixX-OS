# Feuille de route

État au 1er octobre 2026. Une ligne = une pull request, dans l'ordre de réalisation.

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
  utilisateurs Windows) et Bazzite (même base que NicOS, devenue connue grâce à une promesse simple).

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
| **S1. Durcissement du poste** | Pare-feu : zone `nicos` par défaut (aucune connexion entrante sauf découverte du réseau local, voisinage Windows, KDE Connect), au lieu de la zone Fedora qui ouvre les ports 1025 à 65535. SSH désactivé par défaut. Réglages du noyau (journaux du noyau et adresses réservés à l'administrateur, pas de débogage d'un autre programme, pas de redirections ICMP). Firefox : uBlock Origin installé d'office, mode HTTPS uniquement, télémétrie coupée. Guide `securite.md` et politique de signalement des failles (`SECURITY.md`). | Image : zone et services du pare-feu, SSH non activé, fichier sysctl, règles Firefox valides. VM : pare-feu actif sur la zone `nicos`, valeurs du noyau appliquées, mises à jour automatiques (système et Flatpak) programmées. |
| **S2. Images signées et vérifiées** | Signature Cosign à chaque publication ; sur les postes, refus de toute image de `ghcr.io/nic69han/nicos` non signée par la clé NicOS (aujourd'hui : acceptée sans vérification). **Action du propriétaire** : créer la paire de clés et le secret `SIGNING_SECRET`. | Image : clé publique et règle `sigstoreSigned`. VM : mise à jour signée acceptée ; image non signée refusée. |
| **S3. Chaîne d'approvisionnement** | Inventaire des logiciels de chaque image (SBOM), analyse des vulnérabilités connues (CVE) bloquante au-dessus d'un seuil, attestation de provenance GitHub. | SBOM et rapport joints à chaque build ; build rouge si une vulnérabilité critique corrigeable est présente. |
| **S4. Chiffrement et PC perdu** | Chiffrement proposé à l'installation, déverrouillage par la puce TPM sans mot de passe supplémentaire (`ujust setup-luks-tpm-unlock`, déjà dans l'image), documenté pas à pas ; option antivirus (ClamTk) pour les PME qui doivent en justifier un. | Test VM d'une installation chiffrée qui redémarre seule grâce au TPM virtuel. |

## Lot 2 — Applications

| PR | Contenu | Critères d'acceptation |
| --- | --- | --- |
| **A1. Choix des applications au premier démarrage** | Comme Ninite : cases à cocher avec les noms connus sous Windows (Chrome, VLC, Spotify, WhatsApp, Discord, Steam, Zoom, Bitwarden, Pinta pour paint.net, LibreOffice, RustDesk, ClamTk…). VLC remplace Haruna (nom connu). | Test VM : sélection par fichier, applications installées, lanceurs présents. |
| **A2. Microsoft 365 en applications** | Lanceurs Outlook, Word, Excel, PowerPoint et OneDrive en ligne, comme les web apps Teams/Zoom. | Lanceurs valides ; ouverture dans une fenêtre dédiée. |
| **A3. Programmes Windows** | Bottles préinstallé ; au double-clic sur un `.exe` ou `.msi`, un assistant propose l'équivalent Linux connu (table des installeurs courants) ou l'installation dans Bottles. | Test : un installeur connu propose son équivalent ; un inconnu propose Bottles. |

## Lot 3 — Migration et matériel

| PR | Contenu | Critères d'acceptation |
| --- | --- | --- |
| **M1. Assistant de migration** | Récupère Documents, Bureau, Images, Musique, Vidéos et favoris du navigateur depuis l'ancien disque Windows ou une clé USB. | Test VM avec un faux profil Windows : fichiers et favoris retrouvés. |
| **M2. Vieux PC** | Cible 4 Go de mémoire : le test VM tourne avec 4 Go ; services d'arrière-plan allégés si besoin. | Test VM complet vert à 4 Go. |
| **M3. Essayer sans installer** | ISO « live » : NicOS démarre depuis la clé USB, sans toucher au disque, avec un bouton « Installer ». | Test de démarrage de l'ISO live jusqu'au bureau. |

## Lot 4 — Se faire connaître

| PR | Contenu |
| --- | --- |
| **L1. Site et README public** | Page d'accueil (FR/EN) avec la promesse en une phrase, la vidéo de démonstration et les résultats du dernier test. **Décision du propriétaire** : publication du README. |
| **L2. Notes de version** | À chaque version `stable` : ce qui change, résultats des tests, capture du bureau. |

Hors dépôt : lancement sur LinuxFr.org, Reddit, Hacker News et DistroWatch ; campagne End of 10 et
repair cafés ; reconditionneurs de PC ; prestataires informatiques des PME.

## Décisions et actions du propriétaire

1. Créer la clé de signature (S2) : `cosign generate-key-pair`, contenu de `cosign.key` dans le secret
   `SIGNING_SECRET` du dépôt, `cosign.pub` à la racine du dépôt. Ne jamais publier `cosign.key`.
2. Activer le signalement privé des failles dans les réglages du dépôt (S1).
3. Suite bureautique par défaut : OnlyOffice (meilleure fidélité Microsoft) ou LibreOffice (choix des
   administrations européennes) ; l'autre reste proposée dans A1.
4. Publication du README et du site (L1).
