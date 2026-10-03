# Sécurité

Ce que BinixX OS fait pour protéger un poste de bureau, et ce qui reste à faire par l'utilisateur ou
l'administrateur. La feuille de route sécurité est dans [feuille-de-route.md](feuille-de-route.md) (lot 1).

## Protections en place

| Risque | Protection | Vérifié par |
| --- | --- | --- |
| Système modifié par un logiciel malveillant | `/usr` en lecture seule, même pour l'administrateur ; SELinux en mode strict (enforcing) | test VM |
| Démarrage piégé | Secure Boot (shim et noyau signés) | test VM |
| Mise à jour qui casse le PC | Chaque version est installée et testée en VM avant d'être publiée ; retour à la version précédente au démarrage | test VM (mise à jour puis retour arrière) |
| Faille connue livrée dans l'image | Chaque build liste les avis de sécurité Fedora en attente et **échoue** au-dessus d'un seuil ; inventaire des logiciels (SBOM) et provenance de l'image | build (`just scan-securite`) |
| Failles non corrigées | Mises à jour automatiques chaque nuit du système (appliquées au redémarrage suivant, sauf connexion limitée) et des applications | test VM |
| Connexions entrantes | Pare-feu : rien n'entre, sauf la découverte du réseau local (imprimantes, partages) et KDE Connect ; pas de serveur SSH | tests image et VM |
| Publicités piégées, sites malveillants | Firefox : uBlock Origin installé d'office, mode HTTPS uniquement, télémétrie coupée | test image |
| Programme téléchargé malveillant | Les programmes Windows (`.exe`) ne s'exécutent pas ; les applications viennent de Flathub et tournent isolées | — |
| Exploitation de failles du noyau | Journaux et adresses du noyau réservés à l'administrateur, pas d'espionnage d'un programme par un autre | test VM |

**Pas encore en place** : la signature des images (les postes acceptent aujourd'hui toute image publiée
sous `ghcr.io/nic69han/binixx`, sur une connexion chiffrée) ; elle est prévue en priorité (S2).

## Chaîne d'approvisionnement : ce qu'il y a dans l'image, d'où elle vient

À chaque build (pull requests comprises), avant toute publication :

| Contrôle | Ce qu'il fait | Où le trouver |
| --- | --- | --- |
| **Inventaire (SBOM)** | La liste de tous les paquets de l'image (nom, version, licence, éditeur, identifiant `purl`), au format **CycloneDX 1.6**, produite par `securite/sbom.py` à partir de la base RPM de l'image. Un inventaire presque vide (moins de 500 paquets) fait échouer le build. | Artefact `sbom-binixx-<étiquette>` du build (90 jours) ; joint à l'image publiée comme attestation. |
| **Avis de sécurité Fedora en attente** | Liste les avis (`FEDORA-AAAA-…`) dont le correctif est **déjà publié** pour un paquet de l'image (`dnf updateinfo --security`) : une faille connue **et corrigeable**. **Le build échoue** si un avis atteint le seuil (**Critical** par défaut). | Résumé du build ; artefact `avis-securite.txt`. |
| **Provenance** | Attestation signée par GitHub : quel dépôt, quel workflow et quel commit ont produit **cette empreinte** d'image. Publiée dans le registre avec l'image (`gh attestation verify oci://ghcr.io/nic69han/binixx:stable --repo Nic69Han/BinixX`). | Onglet « Attestations » du dépôt. |

Le **seuil** se change sans modifier le code : variable de dépôt `CVE_THRESHOLD` (`Critical`, `Important`, `Moderate` ou `Low`).
Un avis qu'on ne peut pas corriger tout de suite (correctif attendu dans l'image de base) s'inscrit dans
`securite/avis-acceptes.txt`, **avec sa raison** (une ligne sans raison fait échouer le contrôle) ; on le retire dès que
le correctif est dans l'image. Les avis « sans gravité » (certains correctifs Fedora n'en déclarent pas) sont listés
mais ne bloquent jamais. Un **test-témoin** lit la liste complète des avis connus (`--all`) et exige d'en comprendre au moins un : sans lui, « aucun avis en attente » pourrait aussi vouloir dire « format de `dnf` non reconnu ». En local : `just sbom` et `just scan-securite`.

Limites assumées :

- **Pourquoi pas Trivy ou Grype ?** Ils ne disposent pas d'une base d'avis pour Fedora : ils annonceraient « aucune
  faille » à tort. Les avis de Fedora eux-mêmes sont la source fiable.
- **Un avis publié depuis moins de vingt-quatre heures** peut ne pas encore être dans l'image de base : avec le seuil
  `Critical`, le build du jour échoue et celui du lendemain, reconstruit sur la base à jour, passe.
- **Les applications Flatpak** (OnlyOffice, Thunderbird…) ne sont pas dans l'image : elles s'installent depuis Flathub
  au premier démarrage et se mettent à jour séparément. Elles ne figurent donc pas dans l'inventaire.
- La provenance **n'est pas la signature** : la signature Cosign des postes (S2) attend les clés du propriétaire ;
  la provenance, elle, est garantie par GitHub sans clé à gérer. Elle n'est pas créée sur un dépôt privé sans offre Enterprise.

## Pour l'utilisateur et l'administrateur

- **Chiffrer le disque** : cocher « Chiffrer mes données » à l'installation. Pour ne pas taper le mot
  de passe de chiffrement à chaque démarrage, le confier à la puce TPM du PC : `ujust setup-luks-tpm-unlock`
  (annulation : `ujust remove-luks-tpm-unlock`). Le disque reste illisible s'il est retiré du PC.
  **Pas sur un processeur AMD Ryzen des générations Zen 1 à 3** (environ 2017 à 2022) : leur puce TPM
  intégrée est vulnérable (faille « faulTPM ») ; garder alors le mot de passe, ou ajouter un code PIN
  quand le script le propose.
- **Clé de récupération du disque chiffré** : si le mot de passe de chiffrement est oublié, les fichiers sont
  perdus. Le Centre BinixX OS (page **Protéger mes données**) crée une clé de récupération, l'équivalent de
  celle de BitLocker : elle est affichée **une seule fois**, à imprimer ou à enregistrer sur une clé USB
  rangée à part, jamais sur ce PC. Le mot de passe actuel du disque et celui d'un administrateur sont
  demandés. Créer une seconde clé remplace la première (l'ancienne cesse de fonctionner, avec accord
  préalable). Au démarrage, la clé se saisit à la place du mot de passe. Outil : `binixx-cle-recuperation`
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
- **Antivirus** : BinixX OS n'en a pas besoin pour se protéger lui-même. Si une politique interne ou un
  assureur en exige un, ClamTk (Flathub) analyse les fichiers à la demande.
- **Inventaire** : le SBOM de chaque image (voir plus haut) ; `rpm -qa` liste les paquets d'un poste ; `bootc status` donne la version exacte de l'image.

## Signaler une faille

Voir [SECURITY.md](../SECURITY.md).
