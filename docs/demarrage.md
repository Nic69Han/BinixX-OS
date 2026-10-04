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

## L'indicateur de chargement

Sous le logo, une roue tourne : elle montre que l'ordinateur travaille, pour que personne ne le croie planté.

- **Avant** : la roue du thème « spinner » de Fedora (blanche, 24 pixels de diamètre, 30 images). Le test VM l'a mesurée : elle était
  bien là (environ 90 pixels clairs sur chaque capture de l'écran de démarrage) et elle tournait (environ 200 pixels changent d'une
  capture à l'autre), à l'arrêt comme au démarrage. Mais elle est petite sur un écran moderne, et sur les quatre démarrages dont
  le journal donne les mesures, deux montraient des captures successives identiques pendant 2 à 3 secondes, au début du chargement :
  la roue semblait figée. La cause n'est pas établie ; rien n'a été mesuré sur un vrai PC.
- **Maintenant** : une roue BinixX OS de 64 pixels, aux couleurs de la gemme (un arc bleu clair qui s'efface, sur un anneau discret),
  30 images, un tour par seconde, comme celle de Fedora. Elle est calculée par `branding/roue_demarrage.py` (aucune image tierce) ;
  `branding/generer.py` l'appelle et les images sont dans `system_files/usr/share/plymouth/themes/binixx/throbber-*.png`. Le build ne
  copie plus celles de Fedora : une image de plus ou de moins dans l'animation la ferait sauter.
- **Mesuré avec la nouvelle roue** (test VM de la branche) : visible sur chaque capture de l'écran de démarrage (environ 325 pixels
  clairs, contre 90 avec celle de Fedora) et en mouvement entre toutes les paires de captures (environ 750 pixels changent d'une capture
  à l'autre, contre 200) ; dans cette série, aucun arrêt, alors que deux démarrages sur quatre en avaient avec l'ancienne roue.
  Une seule série : on ne sait pas si les arrêts d'avant viennent de la roue, de la machine virtuelle ou du hasard.
- **Vérifié** : par le test de l'image (au moins 12 images PNG de même taille, numérotées sans trou), par `tests/demarrage/test_roue.py`
  (les images du dépôt sont exactement celles que le script dessine, un tour complet revient à la première image) et par le test VM
  (étape 3b) : la roue doit être visible sur au moins la moitié des captures de l'écran de démarrage et bouger sur au moins une paire de
  captures. Le journal donne sa forme (vignette) et, pour chaque capture, le nombre de pixels qui ont changé : on y lit les arrêts.

## Voir les messages quand il le faut

- **Une fois** : Échap pendant l'écran de démarrage ; ou, au menu GRUB (Échap pendant l'attente), touche `e`, retirer `quiet splash` de
  la ligne `linux`, puis Ctrl + X.
- **Après coup** : `journalctl -b` (ce démarrage), `journalctl -b -1` (le précédent).

## Ce que le test VM a mesuré

Redémarrage d'une machine virtuelle de 2 cœurs et 4 Go, comme sur un vrai PC (messages sur l'écran, sans connexion automatique),
une capture d'écran par seconde :

| | Sans le correctif | Avec le correctif |
| --- | --- | --- |
| Texte de console à l'écran | **12 secondes** de lignes de texte sur toute la hauteur de l'écran | aucune |
| Écran de démarrage BinixX OS | n'apparaît jamais | environ 8 secondes |
| Écran noir avant la connexion | quelques secondes | environ 8 secondes (voir « Limites ») |
| Écran de connexion | oui | oui : la session `greeter` de `plasmalogin` tourne, Plymouth ne la bloque pas |
| À l'arrêt | texte | écran de démarrage |

**Essayé et abandonné** : `plymouth quit --retain-splash` (garder le logo à l'écran jusqu'à ce que la connexion affiche la sienne). Le
logo disparaît quand même, et l'écran noir dure autant (7 captures au lieu de 8) : aucun gain, une unité systemd de plus à entretenir.

## Comment c'est vérifié

- Test de l'image : fichier de paramètres valide, module `two-step` de Plymouth dans l'image de démarrage, service et script du menu GRUB.
- Tests unitaires (`tests/demarrage`, `tests/vm`) : le script du menu GRUB (jamais le `user.cfg` d'un autre, jamais `timeout=0`, syntaxe
  GRUB) et l'outil qui lit l'écran.
- **Test VM** (`tests/vm/run-vm-test.sh`, étape 3b) : la VM redémarre comme un vrai PC (messages sur l'écran, sans connexion
  automatique). `tests/vm/ecran_demarrage.py` prend une capture par seconde, la réduit à quelques mesures (part de noir, de bleu nuit du
  fond BinixX OS, de pixels clairs) et juge : l'écran de démarrage apparaît ; aucun texte de console une fois qu'il est là ; avant lui,
  jamais un écran de texte (trois captures au plus) mais deux lignes en haut à gauche sont tolérées (douze captures au plus : voir
  « Limites ») ; l'écran de connexion finit par s'afficher. Les paramètres reçus par le noyau
  et la trace `binixx_menu=cache` de GRUB sont aussi relevés.

## Limites

- Mesuré en machine virtuelle seulement ; pas encore sur du matériel réel (cartes graphiques, portables, très vieux PC).
- Deux lignes de texte restent en haut à gauche de l'écran, quelques secondes, avant l'écran de démarrage. Le test les lit (reconnaissance
  de caractères sur la capture) : c'est le **micrologiciel de la machine virtuelle** (OVMF), `BdsDxe: loading Boot0007 "BinixX OS 44" …
  \EFI\fedora\shimx64.efi`, écrit avant GRUB et le noyau. Ni BinixX OS ni Linux n'y touchent. Un vrai PC affiche le logo de son
  constructeur à la place (ce que fait aussi Windows) ; pas encore vérifié sur matériel réel.
- Si le pilote graphique n'est pas chargé tôt, l'écran de démarrage apparaît plus tard : un instant de noir, jamais de texte.
- Entre la fin de l'écran de démarrage et l'écran de connexion, l'écran reste noir environ 8 secondes **dans la machine virtuelle**, où
  Plasma dessine sans carte graphique (rendu logiciel). Sur un vrai PC ce temps sera plus court, mais il n'est pas mesuré : le test
  VM le relève à chaque version (« écran noir le plus long »).
- Le menu GRUB reste visible une seconde au premier démarrage, et après un démarrage en échec.
- **Écrans noirs sans indicateur** : avant l'écran de démarrage (micrologiciel, GRUB, chargement du noyau ; sur un vrai PC le logo du
  constructeur remplit ce moment) et entre l'écran de démarrage et la connexion (environ 8 secondes dans la VM). Aucune roue n'y
  est affichée : Plymouth n'est pas encore lancé (avant) ou déjà fermé (après).
