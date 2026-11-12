"""Écran de verrouillage BinixX OS : un panneau de verre fumé derrière l'avatar et le mot de passe, et l'heure toujours en blanc.

L'écran de verrouillage de Plasma est un fichier QML du paquet de bureau de KDE (plasma-desktop) :
/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml. On le modifie à la construction de l'image,
à deux endroits repérés par leur texte ; si KDE les change, la construction échoue (on voit tout de suite qu'il faut revoir ce
fichier, au lieu d'un écran de verrouillage cassé) :
  - l'écran entier (« Kirigami.Theme.colorSet: Kirigami.Theme.Complementary » de l'élément racine) et l'horloge (« Clock { id:
    clock ») : textes en blanc, quelle que soit l'ambiance. Ils prenaient la couleur de texte du style des applications et sortaient
    gris foncé sur le ciel sombre du fond d'écran (heure, nom de l'utilisateur, « Mettre en veille »…) ; les champs de saisie
    gardent leurs propres couleurs ;
  - juste avant la pile qui affiche l'avatar et le mot de passe (« StackView { id: mainStack ») : un rectangle arrondi translucide,
    du même verre fumé que la barre des tâches (verre_plasma.py), qui apparaît avec eux, sur le fond déjà flouté par KDE.

    python3 verre_verrouillage.py [LockScreenUi.qml]
"""
import re
import sys

ECRAN = "/usr/share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen/LockScreenUi.qml"
MARQUE = "BinixX OS : verre fumé"  # présent une fois l'écran modifié : une deuxième passe ne fait rien

# Couleurs du verre fumé de la barre des tâches en Nuit (verre_plasma.MATIERES["dark"]["verre"]), un peu plus transparent : le fond
# est déjà flouté et assombri par KDE quand le mot de passe s'affiche
VERRE = "Qt.rgba(0.094, 0.094, 0.133, 0.48)"  # #181822 à 48 %
LISERE = "Qt.rgba(1, 1, 1, 0.14)"

HORLOGE = re.compile(r"(?P<indent>[ \t]*)Clock \{\n(?P<corps>[ \t]*)id: clock\n")
# Le réglage de couleurs de tout l'écran (le premier : celui de l'élément racine)
RACINE = re.compile(r"(?P<indent>[ \t]*)Kirigami\.Theme\.colorSet: Kirigami\.Theme\.Complementary\n")
PILE = re.compile(r"(?P<indent>[ \t]*)StackView \{\n[ \t]*id: mainStack\n")


def panneau(indent):
    """Le rectangle de verre, au niveau de la pile (même parent), dessiné avant elle donc derrière."""
    i, j = indent, indent + "    "
    return (f"{i}// {MARQUE} derrière l'avatar et le mot de passe (build_files/verre_verrouillage.py)\n"
            f"{i}Rectangle {{\n"
            f"{j}id: binixxVerre\n"
            f"{j}width: Math.min(parent.width - Kirigami.Units.gridUnit * 2, Kirigami.Units.gridUnit * 24)\n"
            f"{j}height: Kirigami.Units.gridUnit * 18\n"
            f"{j}anchors.horizontalCenter: parent.horizontalCenter\n"
            f"{j}y: mainStack.y + mainStack.height / 2 - Kirigami.Units.gridUnit * 11\n"
            f"{j}radius: Kirigami.Units.gridUnit * 1.4\n"
            f"{j}color: {VERRE}\n"
            f"{j}border.width: 1\n"
            f"{j}border.color: {LISERE}\n"
            f"{j}opacity: mainStack.opacity\n"
            f"{j}visible: opacity > 0\n"
            f"{i}}}\n\n")


def modifier(texte):
    """Le QML de l'écran de verrouillage avec le verre et l'horloge blanche ; ValueError si un repère manque."""
    if MARQUE in texte:
        return texte
    racine = RACINE.search(texte)
    if racine is None:
        raise ValueError("couleurs de l'écran (« Kirigami.Theme.colorSet: Kirigami.Theme.Complementary ») introuvables : "
                         "LockScreenUi.qml de KDE a changé")
    texte = (texte[:racine.end()]
             + f"{racine.group('indent')}// BinixX OS : textes en blanc sur le fond d'écran (nom, boutons, messages)\n"
             f"{racine.group('indent')}Kirigami.Theme.textColor: \"#FFFFFF\"\n"
             + texte[racine.end():])
    horloge = HORLOGE.search(texte)
    if horloge is None:
        raise ValueError("horloge (« Clock { id: clock ») introuvable : LockScreenUi.qml de KDE a changé")
    corps = horloge.group("corps")
    texte = (texte[:horloge.end()]
             + f"{corps}// BinixX OS : l'heure en blanc, quel que soit le style des applications\n"
             f"{corps}Kirigami.Theme.inherit: false\n"
             f"{corps}Kirigami.Theme.textColor: \"#FFFFFF\"\n"
             + texte[horloge.end():])
    pile = PILE.search(texte)
    if pile is None:
        raise ValueError("pile du mot de passe (« StackView { id: mainStack ») introuvable : LockScreenUi.qml de KDE a changé")
    return texte[:pile.start()] + panneau(pile.group("indent")) + texte[pile.start():]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    chemin = argv[0] if argv else ECRAN
    with open(chemin, encoding="utf-8") as fichier:
        texte = fichier.read()
    nouveau = modifier(texte)
    if nouveau != texte:
        with open(chemin, "w", encoding="utf-8") as fichier:
            fichier.write(nouveau)
    print(f"{chemin} : verre fumé et horloge blanche")
    return 0


if __name__ == "__main__":
    sys.exit(main())
