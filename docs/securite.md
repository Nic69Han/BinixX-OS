# Sécurité

Ce que NicOS fait pour protéger un poste de bureau, et ce qui reste à faire par l'utilisateur ou
l'administrateur. La feuille de route sécurité est dans [feuille-de-route.md](feuille-de-route.md) (lot 1).

## Protections en place

| Risque | Protection | Vérifié par |
| --- | --- | --- |
| Système modifié par un logiciel malveillant | `/usr` en lecture seule, même pour l'administrateur ; SELinux en mode strict (enforcing) | test VM |
| Démarrage piégé | Secure Boot (shim et noyau signés) | test VM |
| Mise à jour qui casse le PC | Chaque version est installée et testée en VM avant d'être publiée ; retour à la version précédente au démarrage | test VM (mise à jour puis retour arrière) |
| Failles non corrigées | Mises à jour automatiques chaque nuit du système (appliquées au redémarrage suivant, sauf connexion limitée) et des applications | test VM |
| Connexions entrantes | Pare-feu : rien n'entre, sauf la découverte du réseau local (imprimantes, partages) et KDE Connect ; pas de serveur SSH | tests image et VM |
| Publicités piégées, sites malveillants | Firefox : uBlock Origin installé d'office, mode HTTPS uniquement, télémétrie coupée | test image |
| Programme téléchargé malveillant | Les programmes Windows (`.exe`) ne s'exécutent pas ; les applications viennent de Flathub et tournent isolées | — |
| Exploitation de failles du noyau | Journaux et adresses du noyau réservés à l'administrateur, pas d'espionnage d'un programme par un autre | test VM |

**Pas encore en place** : la signature des images (les postes acceptent aujourd'hui toute image publiée
sous `ghcr.io/nic69han/nicos`, sur une connexion chiffrée) ; elle est prévue en priorité (S2).

## Pour l'utilisateur et l'administrateur

- **Chiffrer le disque** : cocher « Chiffrer mes données » à l'installation. Pour ne pas taper le mot
  de passe de chiffrement à chaque démarrage, le confier à la puce TPM du PC : `ujust setup-luks-tpm-unlock`
  (annulation : `ujust remove-luks-tpm-unlock`). Le disque reste illisible s'il est retiré du PC.
  **Pas sur un processeur AMD Ryzen des générations Zen 1 à 3** (environ 2017 à 2022) : leur puce TPM
  intégrée est vulnérable (faille « faulTPM ») ; garder alors le mot de passe, ou ajouter un code PIN
  quand le script le propose.
- **Clé de récupération du disque chiffré** : si le mot de passe de chiffrement est oublié, les fichiers sont
  perdus. Le Centre NicOS (page **Protéger mes données**) crée une clé de récupération, l'équivalent de
  celle de BitLocker : elle est affichée **une seule fois**, à imprimer ou à enregistrer sur une clé USB
  rangée à part, jamais sur ce PC. Le mot de passe actuel du disque et celui d'un administrateur sont
  demandés. Créer une seconde clé remplace la première (l'ancienne cesse de fonctionner, avec accord
  préalable). Au démarrage, la clé se saisit à la place du mot de passe. Outil : `nicos-cle-recuperation`
  (`systemd-cryptenroll --recovery-key`), testé sur un vrai volume LUKS2 : la clé déverrouille le volume,
  le mot de passe d'origine continue de fonctionner. Seuls les volumes LUKS2 sont pris en charge.
- **Sauvegarder** : Déjà Dup (« Sauvegardes »), sur un disque externe débranché après la sauvegarde ou
  un service cloud. C'est la protection contre les rançongiciels.
- **Mots de passe** : un mot de passe différent par site, dans le gestionnaire de Firefox ou Bitwarden.
- **Mises à jour** : redémarrer au moins une fois par semaine pour appliquer celles déjà téléchargées.
  `ujust update` les applique tout de suite.
- **Accès à distance** : le serveur SSH et le bureau à distance (KRdp) sont fermés par défaut. Pour les
  ouvrir sur un réseau de confiance :
  - SSH : `sudo systemctl enable --now sshd` puis `sudo firewall-cmd --permanent --add-service=ssh && sudo firewall-cmd --reload` ;
  - bureau à distance : l'activer dans Configuration du système, puis
    `sudo firewall-cmd --permanent --add-service=rdp && sudo firewall-cmd --reload`.
- **Partager un dossier** sur le réseau depuis ce PC : `sudo firewall-cmd --permanent --add-service=samba && sudo firewall-cmd --reload`.

## En entreprise

- **Domaine Active Directory** : `sudo realm join` (voir [migration-windows.md](migration-windows.md)).
  Les comptes, mots de passe et verrouillages restent gérés depuis l'annuaire.
- **Antivirus** : NicOS n'en a pas besoin pour se protéger lui-même. Si une politique interne ou un
  assureur en exige un, ClamTk (Flathub) analyse les fichiers à la demande.
- **Inventaire** : `rpm -qa` liste les paquets ; `bootc status` donne la version exacte de l'image.

## Signaler une faille

Voir [SECURITY.md](../SECURITY.md).
