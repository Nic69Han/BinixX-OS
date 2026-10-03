# Validation du MVP (v0.1)

Le MVP est validé quand les quatre critères ci-dessous passent. Chaque critère indique ce qui est
vérifié automatiquement ([tests/](../tests/README.md)) et ce qui reste à contrôler à la main.

| # | Critère | Automatique | À la main |
| --- | --- | --- | --- |
| 1 | L'ISO démarre en VM et s'installe sans intervention | `test-vm.yml` : ISO générée, installée sur disque vierge, système démarré | Installation guidée de l'ISO publique sur un vrai PC, avec chiffrement |
| 2 | OnlyOffice ouvre et enregistre un .docx et un .xlsx sans perte de mise en forme | Présence d'OnlyOffice, associations de fichiers, polices de substitution | Protocole ci-dessous |
| 3 | Son, réseau, impression PDF et visio fonctionnent | Carte son détectée, PipeWire, accès Internet, PDF réellement produit par l'imprimante PDF, portail de partage d'écran installé | Son audible, visio réelle avec partage d'écran |
| 4 | Une mise à jour puis un retour arrière passent sans casse | `test-vm.yml` : `bootc switch` vers une nouvelle image, redémarrage, `bootc rollback`, redémarrage, avec vérifications à chaque étape | Même chose sur un vrai PC, avec des documents et des réglages utilisateur |

## Critère 2 : fidélité des documents Office

Préparer, sous Windows avec Microsoft Office, un jeu de fichiers de test à conserver dans le projet :

- **.docx** : styles de titres, table des matières, en-tête et pied de page avec numéros de page, tableau
  avec cellules fusionnées, image ancrée, notes de bas de page, suivi des modifications, commentaires,
  polices Calibri et Cambria.
- **.xlsx** : plusieurs feuilles, formules courantes (SOMME, SI, RECHERCHEV, dates), mise en forme
  conditionnelle, cellules fusionnées, graphique, tableau croisé dynamique, figer les volets.

Pour chaque fichier, sous BinixX OS :

1. Ouvrir dans OnlyOffice : comparer visuellement avec une capture faite sous Windows (même nombre de pages,
   mêmes sauts de ligne, pas de police de remplacement visible).
2. Modifier une cellule ou un paragraphe, enregistrer au format d'origine, fermer.
3. Rouvrir le fichier **sous Microsoft Office** : aucun message de réparation, mise en forme intacte.

Noter les écarts dans [compatibilite.md](compatibilite.md). Hors périmètre du MVP : macros VBA, Access, Visio.

## Critère 3 : son et visio

1. Son : lire une vidéo dans Firefox, régler le volume depuis la zone de notification, brancher un casque.
2. Visio : ouvrir la web app Teams (ou Zoom), rejoindre une réunion de test, activer caméra et micro,
   **partager l'écran** : la fenêtre de choix KDE doit apparaître et l'autre participant doit voir l'écran.
3. Impression : imprimer une page depuis OnlyOffice vers « Imprimante PDF », le fichier arrive sur le Bureau ;
   puis sur une imprimante réseau réelle.

## Critère 1 et 4 sur du vrai matériel

1. Installer depuis la clé USB, en cochant « Chiffrer mes données ». Vérifier que Secure Boot est actif :
   `mokutil --sb-state`.
2. Terminer l'assistant de premier démarrage, attendre l'installation des applications.
3. Après une mise à jour publiée, redémarrer, vérifier `bootc status`, puis `sudo bootc rollback`,
   redémarrer et vérifier que documents et réglages sont intacts.
