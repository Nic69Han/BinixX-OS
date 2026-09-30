# NicOS

**Un poste de travail Linux prêt pour le bureau, pensé pour les personnes qui quittent Windows.**
On l'installe, on retrouve une barre des tâches, un menu Démarrer, une suite bureautique qui ouvre les
fichiers Word et Excel, et le système se met à jour tout seul, avec retour arrière possible.

> [!WARNING]
> **Statut : alpha (v0.1).** L'image se construit automatiquement, mais elle n'a encore été validée ni sur
> du vrai matériel ni par de vrais utilisateurs. Ne l'installez pas sur un poste de production.
> La liste de ce qui ne marche pas encore est plus bas, lisez-la avant d'essayer.

NicOS n'est pas une nouvelle distribution : c'est une configuration de
[Fedora Kinoite](https://fedoraproject.org/atomic-desktops/kinoite/) (Fedora + KDE Plasma), construite sur
l'image [`kinoite-main` de Universal Blue](https://github.com/ublue-os/main). On configure, on ne forke pas.

## Ce que contient l'image

| Domaine | Contenu |
| --- | --- |
| Bureautique | OnlyOffice (Word, Excel, PowerPoint), Thunderbird, Firefox, Okular (PDF), client Nextcloud |
| Polices | Carlito, Caladea et Liberation : mêmes largeurs que Calibri, Cambria, Arial, Times New Roman et Courier New, donc même mise en page. Les polices Microsoft d'origine ne sont pas incluses (licence). |
| Visioconférence | Teams, Zoom et Slack en web apps (fenêtres dédiées, via Chromium) ; partage d'écran sous Wayland par PipeWire et le portail KDE |
| Bureau | KDE Plasma avec barre des tâches fixe en bas, menu de démarrage à gauche, thème clair, pavé numérique activé |
| Impression et scan | CUPS avec impression sans pilote, pilotes HP, Brother, Samsung, Epson (Gutenprint)… ; imprimante virtuelle « Imprimante PDF » ; SANE, scanners réseau et USB, Skanpage |
| Sécurité | Secure Boot (noyau signé Fedora), chiffrement du disque proposé à l'installation, SELinux actif, système en lecture seule |
| Mises à jour | Atomiques et automatiques (image système + applications Flatpak), avec retour arrière à la version précédente |

Les applications (OnlyOffice, Firefox…) sont des Flatpak : elles s'installent depuis Flathub **au premier
démarrage, connecté à Internet**. Comptez quelques minutes avant qu'elles apparaissent dans le menu.

## Ce qui ne marche pas encore

- **Rien n'est validé sur du vrai matériel.** Les tests automatiques tournent en machine virtuelle.
- **Applications absentes au tout premier démarrage** tant que le téléchargement Flatpak n'est pas fini
  (aucune notification ne le signale pour l'instant).
- **Chiffrement du disque proposé, pas imposé** : il faut cocher « Chiffrer mes données » dans l'installeur.
- **Signature de l'image non vérifiée par les postes** : l'image est signée avec Cosign dans la CI (une fois
  la clé configurée), mais les postes installés ne refusent pas encore une image non signée.
- **Nom, logo et identité visuelle provisoires** : l'image affiche encore les logos Fedora.
- **Pas de pilote NVIDIA propriétaire** (l'image de base utilise les pilotes libres).
- **Pas d'applications Windows** (.exe) ni de macros VBA dans OnlyOffice.

Le détail par logiciel et par matériel est dans [docs/compatibilite.md](docs/compatibilite.md).

## Essayer NicOS

### Depuis l'ISO

1. Dans l'onglet **Actions** du dépôt, lancez le workflow **Build installer ISO**.
2. Téléchargez l'artefact `nicos-installer-iso` et copiez `install.iso` sur une clé USB
   (Fedora Media Writer, balenaEtcher ou `dd`).
3. Démarrez sur la clé. L'installeur ne demande que le disque : **cochez « Chiffrer mes données »**.
4. Au premier démarrage, l'assistant KDE demande la langue, le clavier, le Wi-Fi, le fuseau horaire et crée
   votre compte.

### Depuis une Fedora Atomic existante (Kinoite, Silverblue, Bazzite, Aurora…)

```bash
sudo bootc switch ghcr.io/nic69han/nicos:latest
systemctl reboot
```

### Mises à jour et retour arrière

Les mises à jour se téléchargent en arrière-plan et s'appliquent au redémarrage suivant. Si une mise à jour
pose problème, on revient à la version précédente :

```bash
sudo bootc rollback      # puis redémarrer
```

La version précédente reste aussi proposée dans le menu de démarrage.

## Organisation du dépôt

| Chemin | Rôle |
| --- | --- |
| `Containerfile` | Image de base (`kinoite-main`) + appel de `build_files/build.sh` |
| `build_files/build.sh` | Paquets RPM, réglages KDE, services |
| `system_files/` | Fichiers copiés tels quels dans l'image : thème et disposition Plasma, services systemd, lanceurs des web apps |
| `flatpaks/system-flatpaks.list` | Applications Flatpak installées au premier démarrage |
| `disk_config/` | Configuration de l'ISO d'installation (`iso.toml`) et des images disque (`disk.toml`) |
| `.github/workflows/build.yml` | Construction, test, signature Cosign et publication de l'image sur GHCR |
| `.github/workflows/build-iso.yml` | Génération de l'ISO d'installation |
| `.github/workflows/test-vm.yml` | Installation, démarrage, mise à jour et retour arrière dans une VM |
| `tests/` | Vérifications de l'image et test en VM ([tests/README.md](tests/README.md)) |
| `docs/` | [Guide de migration](docs/migration-windows.md), [compatibilité](docs/compatibilite.md), [validation du MVP](docs/validation-mvp.md) |
| `nicos.env`, `Justfile` | Paramètres et commandes de build locales |

## Développer

Il faut [`just`](https://just.systems) et `podman` (déjà présents sur les images Universal Blue).

```bash
just build          # construit l'image localhost/nicos:latest
just test-image     # vérifie son contenu (paquets, polices, réglages KDE, services)
just build-qcow2    # disque de VM ; `just run-vm-qcow2` pour le démarrer
just test-vm        # test complet en VM (KVM et root nécessaires, compter 1 à 2 h)
just lint           # shellcheck
```

Pour tester une image locale sur votre poste Fedora Atomic :
`sudo bootc switch --transport containers-storage localhost/nicos:latest`.

## Mise en route du dépôt (une seule fois)

1. **Actions** : *Settings → Actions → General → Workflow permissions → Read and write permissions*.
2. **Clé de signature** : la CI publie l'image même sans clé, mais non signée (avec un avertissement).
   ```bash
   COSIGN_PASSWORD="" cosign generate-key-pair
   gh secret set SIGNING_SECRET < cosign.key
   git add cosign.pub && git commit -m "Ajoute la clé publique Cosign" && git push
   ```
   Ne commitez **jamais** `cosign.key` (il est dans `.gitignore`).
3. **Visibilité de l'image** : après le premier build, rendez le paquet `nicos` public
   (*Profil → Packages → nicos → Package settings → Change visibility*), sinon personne ne pourra l'installer.

## Avant de rendre le projet public, à décider

- **Nom et logo** : vérifier que « NicOS » est libre (GitHub, nom de domaine, marques déposées), puis
  remplacer les logos Fedora, comme le demande la politique de marque de Fedora pour les dérivés.
- **Licence** : le dépôt est pour l'instant sous **Apache-2.0**, héritée du modèle Universal Blue. Choisir
  GPL-3.0 à la place empêcherait qu'un tiers en fasse une version fermée. La décision doit être prise avant
  les premières contributions extérieures.
- **Signature** : faire vérifier la signature Cosign par les postes installés (politique `containers-policy`).

## Remerciements

NicOS repose sur le travail de [Fedora](https://fedoraproject.org), [KDE](https://kde.org),
[Universal Blue](https://universal-blue.org) (modèle [`image-template`](https://github.com/ublue-os/image-template)
et images de base) et [Flathub](https://flathub.org).
