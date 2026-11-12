# Applications unifiées : les applications GTK aux couleurs de BinixX OS

Les applications de KDE (Dolphin, Paramètres, le Centre…) suivent d'elles-mêmes le style Windows 11 de BinixX OS (Kvantum, couleurs
BinixX, police Inter). D'autres applications sont écrites avec GTK, la bibliothèque de GNOME : Firefox, Thunderbird, Remmina,
Déjà Dup. Sans réglage, elles garderaient le style de GNOME, avec une autre police, d'autres icônes et une autre boîte « Ouvrir ».
BinixX OS les rapproche du reste du bureau.

## Ce qui est fait

| Pour | Quoi | Où |
| --- | --- | --- |
| Applications GTK du système (Firefox) | Thème **Breeze** pour GTK 3 et 4, et **kde-gtk-config**. À chaque ouverture de session, celui-ci reporte dans `~/.config/gtk-3.0` et `gtk-4.0` les réglages de KDE : couleurs (le bleu BinixX `#0C6EEE`, Aube ou Nuit), police Inter, icônes `binixx-os` (dossiers pastel), pointeur, boutons de fenêtre à droite | paquets `breeze-gtk-gtk3`, `breeze-gtk-gtk4`, `kde-gtk-config` (`build_files/build.sh`) |
| Toutes les applications GTK, avant la première session | Réglages par défaut du système : thème Breeze, icônes `binixx-os`, pointeur, Inter 10, boutons à droite | `/etc/xdg/gtk-3.0/settings.ini`, `gtk-4.0/settings.ini` |
| Applications Flatpak en GTK 3 (Thunderbird, Remmina) | Le thème Breeze de Flathub (`org.gtk.Gtk3theme.Breeze`), et une permission globale de **lecture seule** sur ces deux dossiers de réglages : elles prennent les mêmes couleurs, la même police et les mêmes icônes | `binixx-flatpak-install`, à chaque démarrage |
| Applications GTK 4 / libadwaita (Déjà Dup) | Elles n'acceptent pas de thème, mais suivent le mode clair ou sombre, et la couleur d'accent que le portail de KDE leur donne ; avec la permission ci-dessus, elles lisent aussi les couleurs de kde-gtk-config | portail `xdg-desktop-portal-kde` |
| Firefox | La boîte « Ouvrir » / « Enregistrer sous » de KDE, la même que dans Dolphin, au lieu de celle de GTK. Les fichiers téléchargés s'ouvrent avec l'application choisie dans KDE. Pas de question « navigateur par défaut » | `/usr/lib64/firefox/browser/defaults/preferences/binixx-prefs.js` |

Un changement d'ambiance (Aube ↔ Nuit) ou de couleurs dans le Centre est reporté aux applications GTK par kde-gtk-config. Une
application déjà ouverte peut demander d'être relancée.

## Ce qui ne change pas

- **OnlyOffice** (la suite bureautique de BinixX OS, à la place de LibreOffice) dessine sa propre interface. Il suit le mode clair
  ou sombre du système, mais garde ses couleurs.
- **Chromium** garde son thème : on peut choisir « GTK » dans ses paramètres (Apparence) pour qu'il prenne les couleurs ci-dessus.
- **La barre de titre de Firefox** est dessinée par Firefox, avec les boutons Breeze, et non par KWin : c'est ce qui permet d'avoir
  les onglets dans la barre de titre, comme sous Windows.

## Sécurité

La permission Flatpak ajoutée ne permet que de **lire** `~/.config/gtk-3.0` et `~/.config/gtk-4.0` : des couleurs, une police, des
noms de thème. Les applications n'y écrivent pas et ne voient rien d'autre de plus.

## Tests

- Image (`tests/image/checks.d/90-applications-gtk.sh`) : paquets, thème Breeze GTK 3, module kded de kde-gtk-config, réglages de
  Firefox, permission et thème Flatpak dans le script de démarrage.
- VM (`tests/vm/checks.d/89-applications-gtk.sh`) :
  - les réglages GTK du compte, une fois le bureau revenu en Aube : thème Breeze, police Inter, icônes `binixx-os`, pointeur, bleu
    BinixX dans `colors.css` ;
  - la permission Flatpak et le thème Breeze installé ;
  - une capture de Firefox ouvert dans la session (`applications-gtk.png`).
