# Windows complet : Windows dans une machine virtuelle

Pour **le logiciel indispensable qui n'existe pas sous BinixX OS** (comptabilité, CAO, application métier) et
dont aucun équivalent ne convient. Essayer d'abord « Mon logiciel Windows » : beaucoup de logiciels ont un
équivalent, et c'est toujours plus simple et plus rapide. Page *Windows complet* du Centre BinixX OS
([centre-binixx.md](centre-binixx.md)).

> **La licence Windows reste à acquérir** (celle de l'utilisateur ou de l'entreprise) : BinixX OS n'en fournit
> pas. Les cas d'usage professionnels doivent respecter le contrat de licence de Microsoft.

## Ce PC est-il prêt ?

La page vérifie quatre choses, avec les valeurs du PC, et dit quoi faire :

| Vérification | « ok » | « juste » | « non » |
| --- | --- | --- | --- |
| Virtualisation matérielle (`/dev/kvm`) | activée | — | désactivée dans le BIOS/UEFI (VT-x, AMD-V, SVM) ou absente |
| Mémoire vue par le système | 7 Go ou plus (un PC « 8 Go ») | 3,5 Go ou plus (« 4 Go ») | moins |
| Espace libre dans le dossier personnel | 64 Go ou plus | 32 Go ou plus | moins |
| Processeur | 4 fils d'exécution ou plus | 2 ou 3 | 1 |

Les seuils sont dans `binixx_centre/virtualisation.py` et testés (`tests/image/centre/test_windows.py`).

## Trois façons de faire

| Option | Pour qui | Licence | À savoir |
| --- | --- | --- | --- |
| **Boxes** (Flatpak, à la demande) | Commencer simplement : Windows dans une fenêtre, assistant d'installation | LGPL-2.1+ | Le plus simple ; Windows s'affiche en bureau complet, pas application par application |
| **WinBoat** (à télécharger sur winboat.app) | Les programmes Windows dans **leurs propres fenêtres**, mêlées à celles de BinixX OS (FreeRDP RemoteApp) | **MIT** | **Bêta** : prévoir de dépanner. Windows tourne dans un conteneur Podman. USB non pris en charge avec Podman (d'après le projet). Pas sur Flathub (AppImage ou RPM) |
| **Windows 365** (dans le navigateur) | Aucune installation, aucune virtualisation | service de Microsoft | Abonnement nécessaire, souvent déjà fourni par l'entreprise |

BinixX OS ajoute à l'image ce dont WinBoat a besoin côté système : **Podman** (déjà dans l'image de base),
**Podman Compose** et **FreeRDP 3** (`build_files/modules.d/85-windows-vm.sh`, qui échoue si FreeRDP 3 manque).
WinBoat lui-même n'est pas embarqué : projet jeune, absent de Flathub, à télécharger par l'utilisateur
(la page indique ce qui manque, le cas échéant).

## Ce que la CI vérifie, et ce qu'elle ne vérifie pas

- **Vérifié** : les prérequis (valeurs limites, cas « BIOS »), la page et ses boutons, le catalogue (Boxes,
  Windows 365, renvois depuis les logiciels sans équivalent), la présence de Podman, Podman Compose et
  FreeRDP 3 dans l'image et dans le système installé.
- **Non vérifié** : le démarrage de Windows, l'installation de WinBoat et les fenêtres intégrées. La VM de
  test n'a pas de virtualisation imbriquée, et la CI n'a pas de licence Windows. WinBoat est à valider à la
  main sur un vrai PC avant de le recommander à des utilisateurs.

## Alternatives écartées

- **WinApps** : licence **AGPL-3.0**, hors de ce que nous embarquons ; WinBoat poursuit le même but sous MIT.
- **Bottles / Wine** : déjà proposé à la demande (« Mon logiciel Windows »), sans garantie, ce n'est pas Windows.
- **Double démarrage** : plus performant mais contraire à l'esprit « un seul système, sans risque » ; l'installeur
  de BinixX OS n'est pas fait pour partager un disque avec Windows.
- **VirtualBox / VMware** : absents de Flathub ou à licence restrictive ; Boxes (QEMU/KVM) couvre le besoin.
