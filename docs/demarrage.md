# Démarrage « à la Windows »

Sur Windows, on allume le PC et l'on voit un logo, puis l'écran de connexion. Jamais de texte qui défile. Sur Linux, par défaut,
c'est l'inverse : les messages du noyau et de systemd s'affichent un par un, ce qui ressemble à une panne pour quelqu'un qui n'a
jamais vu cela. BinixX OS cache ces messages derrière son écran de démarrage, et les montre quand ils servent.

## Ce que voit l'utilisateur

| Étape | Avant | Maintenant |
| --- | --- | --- |
| Après le logo du constructeur | Menu GRUB en texte, une seconde, à chaque démarrage | Rien : le PC démarre tout droit (le menu reste visible au premier démarrage et après un échec) |
| Chargement du système | Dizaines de lignes de texte | Écran de démarrage BinixX OS : fond bleu nuit, logo, indicateur de chargement |
| Connexion | Écran de connexion | Écran de connexion |
| Un problème grave (disque introuvable, mode de secours) | Texte | Texte : l'écran de démarrage se ferme et laisse voir le message (comportement standard de dracut et de systemd, que nos tests ne reproduisent pas) |

La touche **Échap** pendant l'écran de démarrage affiche les messages. La touche **Échap** pendant la seconde d'attente de GRUB
affiche le menu, par exemple pour démarrer une ancienne version.

## Pourquoi du texte s'affichait

L'image avait déjà son écran de démarrage (le thème Plymouth `binixx`, dans l'image de démarrage). Mais Plymouth ne l'affiche que si
le noyau reçoit **`quiet` et `splash`** ; sans eux il retombe sur un thème qui n'est que du texte. Le test VM l'a mesuré sur le système
installé par l'installation automatique du test VM, qui suit le même chemin que l'ISO publique :

```
ostree=… console=ttyS0,115200 root=UUID=… vconsole.keymap=fr rootflags=subvol=root rw
```

Pas de `quiet`, pas de `splash`, pas de `rhgb` : l'installeur (Anaconda) ne les ajoute pas aux images `bootc`, et l'image n'en fournissait
pas.

## Ce que font les autres

- **Fedora, Ubuntu, Linux Mint, SteamOS** : les mêmes paramètres du noyau (`quiet splash`), Plymouth pour l'animation.
- **Fedora** cache aussi le menu GRUB quand le démarrage précédent a réussi (`menu_auto_hide`) et le montre après un échec ; **Ubuntu**
  le cache quand le PC n'a qu'un seul système. Sur une image `bootc`, la configuration de GRUB est générée par `bootupd` et ne contient
  pas ce mécanisme (plusieurs utilisateurs de Fedora Silverblue le signalent) : on le remet par le fichier prévu pour cela (`user.cfg`).
- **Windows** : logo et points qui tournent ; les erreurs graves ouvrent un écran bleu ou un menu de récupération.

## Les paramètres du noyau

`usr/lib/bootc/kargs.d/10-binixx-demarrage.toml`, appliqué par `bootc` à l'installation, et vérifié après une mise à jour :

| Paramètre | Rôle |
| --- | --- |
| `quiet`, `rhgb`, `splash` | Pas de texte du noyau ; Plymouth affiche son thème |
| `loglevel=3`, `rd.udev.log_level=3`, `udev.log_level=3` | Seules les erreurs du noyau et d'udev sont écrites |
| `systemd.show_status=auto`, `rd.systemd.show_status=auto` | systemd n'affiche son avancement que si le démarrage traîne ou échoue. Avec `quiet` seul, il se tairait **même en cas d'échec** |
| `plymouth.ignore-serial-consoles` | Un port série (support, serveurs) ne force pas le mode texte |

Volontairement absents : `vt.global_cursor_default=0` (le curseur des consoles de dépannage, `Ctrl + Alt + F3`, resterait invisible).

## Le menu GRUB discret

`/boot` est une partition à part, qui ne fait pas partie de l'image. Le service `binixx-menu-grub.service` (script
`/usr/libexec/binixx/binixx-menu-grub`) y écrit `/boot/grub2/user.cfg` à chaque démarrage. La configuration de GRUB le lit **avant**
que greenboot ne remette `boot_success` à 0 : le fichier sait donc comment le démarrage précédent s'est passé.

- Démarrage précédent réussi (`boot_success=1`) : menu caché, attente d'une seconde (Échap l'affiche), `binixx_menu=cache`.
- Premier démarrage, ou démarrage précédent en échec : menu visible une seconde, `binixx_menu=visible`. Après une mise à jour
  défectueuse, greenboot revient seul à la version précédente ; le menu reste là pour la choisir à la main.

La valeur `binixx_menu` est écrite dans l'environnement de GRUB : `sudo grub2-editenv list` dit si le menu a été caché au dernier démarrage.

Le script ne touche jamais à un `user.cfg` qui n'est pas le sien (sans la ligne de marque en tête). Pour garder le menu visible :
`sudo systemctl disable --now binixx-menu-grub.service && sudo rm /boot/grub2/user.cfg`.

## Voir les messages quand il le faut

- **Une fois** : Échap pendant l'écran de démarrage ; ou, au menu GRUB (Échap pendant l'attente), touche `e`, retirer `quiet splash` de
  la ligne `linux`, puis Ctrl + X.
- **Après coup** : `journalctl -b` (ce démarrage), `journalctl -b -1` (le précédent).

## Comment c'est vérifié

- Test de l'image : fichier de paramètres valide, module `two-step` de Plymouth dans l'image de démarrage, service et script du menu GRUB.
- Tests unitaires (`tests/demarrage`, `tests/vm`) : le script du menu GRUB (jamais le `user.cfg` d'un autre, jamais `timeout=0`, syntaxe
  GRUB) et l'outil qui lit l'écran.
- **Test VM** (`tests/vm/run-vm-test.sh`, étape 3b) : la VM redémarre comme un vrai PC (messages sur l'écran, sans connexion
  automatique). `tests/vm/ecran_demarrage.py` prend une capture par seconde, la réduit à quelques mesures (part de noir, de bleu nuit du
  fond BinixX OS, de pixels clairs) et juge : l'écran de démarrage apparaît ; aucun texte de console une fois qu'il est là (et trois
  captures au plus avant : micrologiciel et menu GRUB) ; l'écran de connexion finit par s'afficher. Les paramètres reçus par le noyau
  et la trace `binixx_menu=cache` de GRUB sont aussi relevés.

## Limites

- Mesuré en machine virtuelle seulement ; pas encore sur du matériel réel (cartes graphiques, portables, très vieux PC).
- Si le pilote graphique n'est pas chargé tôt, l'écran de démarrage apparaît plus tard : un instant de noir, jamais de texte.
- La durée de l'écran noir entre l'écran de démarrage et la connexion dépend de la machine ; le test VM la relève (« écran noir le plus
  long »).
