# Administrer NicOS à la souris

Tout se fait sans terminal, depuis trois endroits :

- **Configuration du système** : l'équivalent des Paramètres et du Panneau de configuration de Windows ;
- **Administration du PC** (menu → Système) : le centre d'administration, l'équivalent de « Gestion de
  l'ordinateur ». C'est Cockpit, la console d'administration de Fedora, ouverte dans sa propre fenêtre.
  Connexion avec son nom d'utilisateur et son mot de passe ; les actions sensibles demandent
  « Accès administrateur » (bouton en haut à droite) ;
- **Discover** : l'équivalent du Microsoft Store et de Windows Update.

## Où faire quoi

| Tâche | Où | Sous Windows |
| --- | --- | --- |
| Installer ou supprimer une application | Discover | Microsoft Store, « Ajouter ou supprimer des programmes » |
| Mettre à jour maintenant | Discover → Mises à jour | Windows Update |
| Revenir à la version précédente du système | Administration du PC → Mises à jour logicielles → « Revenir en arrière », puis redémarrer ; ou choisir l'ancienne version dans le menu de démarrage | Restauration du système |
| Rejoindre le domaine de l'entreprise (Active Directory) | Administration du PC → Présentation → Domaine → « Rejoindre un domaine » : nom du domaine, compte et mot de passe d'un administrateur du domaine | Paramètres → Comptes → Accès Professionnel ou Scolaire |
| Pare-feu : autoriser une application ou un service | Configuration du système → Pare-feu ; ou Administration du PC → Réseau → Pare-feu | Pare-feu Windows Defender |
| Réseau, Wi-Fi, VPN | Configuration du système → Connexions | Paramètres → Réseau et Internet |
| Comptes des utilisateurs | Configuration du système → Utilisateurs ; ou Administration du PC → Comptes | Paramètres → Comptes |
| Disques, partitions, chiffrement | Administration du PC → Stockage | Gestion des disques, BitLocker |
| Démarrer ou arrêter un service (SSH…) | Administration du PC → Services | Services (services.msc) |
| Comprendre une panne | Administration du PC → Journaux | Observateur d'événements |
| Imprimantes et scanners | Configuration du système → Imprimantes ; Skanpage pour numériser | Périphériques et imprimantes |
| Bureau à distance (être aidé à distance) | Configuration du système → Bureau à distance, puis Pare-feu → autoriser « rdp » | Paramètres → Bureau à distance |
| Sauvegarde | Déjà Dup (« Sauvegardes ») | Historique des fichiers |

## Ce qui demande encore le terminal

À remplacer par des assistants (feuille de route, U2) :

- confier la clé du disque chiffré à la puce TPM (`ujust setup-luks-tpm-unlock`, voir [securite.md](securite.md)) ;
- la connexion à OneDrive se fait dans une fenêtre de terminal guidée (lanceur « OneDrive »).

## Sécurité du centre d'administration

Il n'écoute que sur le PC lui-même (adresses `127.0.0.1` et `::1`) : personne ne peut s'y connecter
depuis le réseau. Pour administrer un poste à distance, l'administrateur ouvre explicitement le
service « cockpit » dans le pare-feu et change les adresses d'écoute (voir le commentaire de
`/usr/lib/systemd/system/cockpit.socket.d/50-nicos-localhost.conf`).
