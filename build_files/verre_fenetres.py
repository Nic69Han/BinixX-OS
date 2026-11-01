"""Barre de titre « verre fumé » de BinixX OS : décoration des fenêtres (Aurorae) tirée de celle de Win11OS KDE.

La décoration de Win11OS KDE (decoration.svg) dessine la barre de titre et le cadre des fenêtres avec un fond gris (#282828 en sombre,
#f2f2f2 en clair) à 65 % d'opacité, sans « masque » : KWin ne floute donc jamais ce qu'il y a derrière, et l'on voit les fenêtres du
dessous à travers la barre de titre. La variante BinixX-Verre-* :
  - reprend les couleurs du verre fumé de la barre des tâches (build_files/verre_plasma.py) à une opacité qui reste lisible sans flou
    (machine virtuelle, vieux PC, profil léger) ;
  - ajoute les éléments « mask-* » : Aurorae (aurorae.qml, supportsMask) en tire la zone que KWin floute derrière la barre de titre et
    le cadre (Decoration::updateBlur) ; l'ombre portée n'en fait pas partie.
Le reste du dessin (ombre, liseré, boutons) est celui d'origine, inchangé.

    from verre_fenetres import decoration_verre
    decoration_verre(open("Win11OS-dark/decoration.svg").read(), "dark")
"""
import re
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
# Couleur du fond de la barre de titre et du cadre dans la décoration d'origine
FOND_ORIGINE = {"dark": "#282828", "light": "#f2f2f2"}
# Verre fumé des fenêtres : les tons de la barre des tâches, un peu plus couvrants (le titre doit se lire sur n'importe quoi, même sans
# flou ; Win11OS KDE était à 65 %)
VERRE = {"dark": ("#181822", 0.82), "light": ("#ffffff", 0.84)}
MORCEAUX = ("topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright")

for prefixe, espace in (("", SVG), ("xlink", "http://www.w3.org/1999/xlink"), ("inkscape", "http://www.inkscape.org/namespaces/inkscape"),
                        ("sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"),
                        ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"), ("cc", "http://creativecommons.org/ns#"),
                        ("dc", "http://purl.org/dc/elements/1.1/")):
    ET.register_namespace(prefixe, espace)


def _style(element):
    return dict(p.split(":", 1) for p in element.get("style", "").split(";") if ":" in p)


def _poser_style(element, style):
    element.set("style", ";".join(f"{cle}:{valeur}" for cle, valeur in style.items()))


def _est_fond(element, teinte):
    style = _style(element)
    return element.tag in (f"{{{SVG}}}rect", f"{{{SVG}}}path") and style.get("fill", "").lower() == FOND_ORIGINE[teinte]


def decoration_verre(texte, teinte):
    """decoration.svg de Win11OS KDE (teinte « dark » ou « light ») en verre fumé, avec son masque de flou ; SystemExit si le dessin
    d'origine n'a plus la forme attendue."""
    racine = ET.fromstring(texte)
    couleur, opacite = VERRE[teinte]
    groupes = {element.get("id"): element for element in racine.iter() if element.get("id", "").startswith("decoration-")}
    for etat in ("decoration", "decoration-inactive"):
        for morceau in MORCEAUX:
            if f"{etat}-{morceau}" not in groupes:
                raise SystemExit(f"Win11OS-{teinte}/decoration.svg : « {etat}-{morceau} » introuvable, le thème d'origine a changé, à revoir")
    fonds = 0
    for groupe in groupes.values():
        for element in groupe.iter():
            if _est_fond(element, teinte):
                style = _style(element)
                style.pop("mix-blend-mode", None)  # « darken » en clair : le verre blanc ne doit pas assombrir
                style.update({"fill": couleur, "opacity": f"{opacite:g}", "fill-opacity": "1"})
                _poser_style(element, style)
                fonds += 1
    if fonds < len(MORCEAUX):
        raise SystemExit(f"Win11OS-{teinte}/decoration.svg : {fonds} fonds {FOND_ORIGINE[teinte]} seulement, le thème d'origine a changé")

    # Masque : copie des morceaux actifs où seul le fond compte (opaque) ; l'ombre et les liserés y sont présents mais invisibles, pour
    # que chaque morceau garde la taille de celui de la décoration
    parents = {enfant: parent for parent in racine.iter() for enfant in parent}
    for morceau in MORCEAUX:
        original = groupes[f"decoration-{morceau}"]
        copie = ET.fromstring(ET.tostring(original))
        copie.set("id", f"mask-{morceau}")
        lien = f"{{{XLINK}}}href"
        if copie.get(lien, "").startswith("#decoration-"):  # côtés droits : le côté gauche en miroir (<use>), donc son masque
            copie.set(lien, copie.get(lien).replace("#decoration-", "#mask-", 1))
        for element in copie.iter():
            if element is not copie and element.get("id"):
                element.set("id", f"mask-{morceau}-{element.get('id')}")
            if element.tag in (f"{{{SVG}}}rect", f"{{{SVG}}}path"):
                style = _style(element)
                style["opacity"] = "1" if style.get("fill", "").lower() == couleur else "0"
                _poser_style(element, style)
        parent = parents[original]
        parent.insert(list(parent).index(original) + 1, copie)

    sortie = ET.tostring(racine, encoding="unicode")
    sortie = re.sub(r"^<svg\b", "<svg", sortie)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            "<!-- BinixX OS : barre de titre « verre fumé », tirée de Win11OS KDE (GPL-3.0) par build_files/verre_fenetres.py -->\n"
            + sortie + "\n")


def rc_verre(texte, teinte):
    """Réglages Aurorae (Win11OS-*rc) de la variante : titre blanc en sombre, presque noir en clair, comme d'origine."""
    if "[General]" not in texte or "[Layout]" not in texte:
        raise SystemExit(f"Win11OS-{teinte}rc : sections [General] et [Layout] attendues, le thème d'origine a changé, à revoir")
    return texte
