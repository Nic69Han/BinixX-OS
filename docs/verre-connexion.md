# Écrans de verrouillage et de connexion en verre

## Écran de verrouillage (Windows + L, mise en veille)

- **Au repos**, l'heure et la date s'affichent sur le fond d'écran BinixX, **toujours en blanc**. Avant, elles prenaient la couleur de
  texte du style des applications, et sortaient gris foncé sur le ciel sombre du fond d'écran.
- **Dès qu'on touche une touche ou la souris**, KDE floute et assombrit le fond. L'avatar et le mot de passe apparaissent alors sur un
  **panneau de verre fumé** aux coins arrondis, avec un liseré clair d'un pixel : le même verre que la barre des tâches et les menus
  en Nuit (`build_files/verre_plasma.py`).

L'écran de verrouillage est un fichier QML de KDE (`/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml`).
`build_files/verre_verrouillage.py` le modifie à la construction de l'image, à deux endroits repérés par leur texte : l'horloge et la
pile qui affiche le mot de passe. Si une version de KDE change ces repères, **la construction échoue** : il faut alors revoir le
fichier, au lieu de publier un écran de verrouillage cassé. En cas d'erreur de QML, l'écran de verrouillage de secours de KDE prend
le relais : le PC reste toujours déverrouillable.

## Écran de connexion (Plasma Login Manager)

Le dessin de l'écran de connexion est **compilé dans le programme de KDE** : on ne peut pas y ajouter de panneau sans recompiler
Plasma Login Manager. BinixX OS lui donne en revanche son **ambiance Nuit**, quelle que soit l'heure :
- textes clairs, heure lisible sur le ciel ;
- champs et boutons sombres, en verre fumé, comme le reste de BinixX en Nuit.

Avant, il prenait le thème clair, et l'heure sortait gris foncé sur le ciel sombre.

L'écran de connexion lit son thème global dans le `kdeglobals` de son compte système (`plasmalogin`). `tmpfiles.d`
(`/usr/lib/tmpfiles.d/binixx-plasmalogin.conf`, écrit à la construction d'après la déclaration du compte dans `sysusers.d`) le
réécrit à chaque démarrage :

```
[KDE]
LookAndFeelPackage=org.binixx.dark.desktop
AutomaticLookAndFeel=false
```

Le fond d'écran reste celui de BinixX (`/usr/lib/plasmalogin/defaults.conf`).

## Tests

- Image (`tests/image/checks.d/91-verre-connexion.sh`) : le panneau et l'horloge blanche dans le QML de KDE, le réglage `tmpfiles.d`.
- Test des repères (`tests/themes/test_verre_verrouillage.py`) : sur un extrait du fichier de KDE ; la construction échoue si un repère
  manque.
- VM (`tests/vm/checks.d/90-verre-connexion.sh`) : le `kdeglobals` de l'écran de connexion sur le système installé. Trois captures :
  - `verrouillage.png` : écran verrouillé par logind ;
  - `verrouillage-mot-de-passe.png` : après une touche ;
  - `connexion.png` : écran de connexion après un redémarrage.
