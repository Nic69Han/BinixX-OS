#!/usr/bin/env python3
"""La roue de chargement de l'écran de démarrage BinixX OS.

Un arc aux couleurs de la gemme (bleu clair en tête, bleu-violet en queue, qui s'efface) tourne sur un anneau discret, sous le
logo. Elle sert à une chose : montrer que l'ordinateur travaille, pour que personne ne le croie planté. Elle remplace la roue du thème
« spinner » de Fedora (24 px de diamètre, blanche), trop petite sur un écran moderne ; le mouvement est le même : 30 images, un tour
par seconde (le rythme du thème de Fedora), dans le sens des aiguilles d'une montre.

Tout est calculé (aucune image tierce, résultat identique d'une exécution à l'autre) : chaque image est dessinée en grand puis réduite.

    pip install numpy pillow
    python3 branding/roue_demarrage.py [dossier]

branding/generer.py appelle `ecrire_roue()` pour produire les images du thème Plymouth (throbber-0001.png à throbber-0030.png)."""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

IMAGES = 30                   # nombre d'images : le thème de Fedora en a autant, Plymouth les passe au même rythme
COTE = 64                     # côté de chaque image, en pixels (la roue de Fedora : 32)
RAYON = 24.0                  # rayon de l'anneau, au milieu de son trait
TRAIT = 6.0                   # épaisseur du trait
ARC = math.radians(190)       # longueur de l'arc lumineux
SURECHANTILLONNAGE = 8        # chaque image est dessinée 8 fois plus grande, puis réduite : bords lisses
TETE = np.array([0xB8, 0xE0, 0xFF], np.float64)     # le bleu clair de la gemme (GEM_DARK dans generer.py), éclairci pour la tête
QUEUE = np.array([0x5A, 0x7D, 0xFF], np.float64)    # gemme, milieu
PISTE = 0.20                  # opacité de l'anneau sous l'arc


def dessiner(angle_de_tete, cote=COTE):
    """Une image RGBA : l'anneau et l'arc dont la tête est à `angle_de_tete` (radians, 0 = à droite, positif = sens des aiguilles)."""
    grand = cote * SURECHANTILLONNAGE
    echelle = SURECHANTILLONNAGE
    ys, xs = np.mgrid[0:grand, 0:grand].astype(np.float64)
    dx, dy = (xs + 0.5) / echelle - cote / 2, (ys + 0.5) / echelle - cote / 2
    rayon = np.hypot(dx, dy)
    angle = np.arctan2(dy, dx)  # l'axe des y va vers le bas : un angle croissant tourne dans le sens des aiguilles
    sur_l_anneau = np.abs(rayon - RAYON) <= TRAIT / 2
    # distance angulaire derrière la tête, dans le sens contraire du mouvement : 0 à la tête, ARC à la queue
    derriere = np.mod(angle_de_tete - angle, 2 * math.pi)
    dans_l_arc = sur_l_anneau & (derriere <= ARC)
    fondu = np.clip(1 - derriere / ARC, 0, 1)
    arc_opacite = np.where(dans_l_arc, fondu ** 0.55, 0.0)
    # tête arrondie : un disque de la largeur du trait au bout de l'arc
    tete_x, tete_y = RAYON * math.cos(angle_de_tete), RAYON * math.sin(angle_de_tete)
    arc_opacite = np.where(np.hypot(dx - tete_x, dy - tete_y) <= TRAIT / 2, 1.0, arc_opacite)
    piste_opacite = np.where(sur_l_anneau, PISTE, 0.0)
    opacite = 1 - (1 - arc_opacite) * (1 - piste_opacite)
    # couleur : de la tête (clair) à la queue (milieu de la gemme), l'anneau seul en clair
    melange = np.clip(derriere / ARC, 0, 1)[..., None]
    couleur_arc = TETE * (1 - melange) + QUEUE * melange
    poids_arc = (arc_opacite / np.maximum(opacite, 1e-9))[..., None]
    couleur = couleur_arc * poids_arc + TETE * (1 - poids_arc)
    # réduction en alpha prémultiplié (sinon les bords prennent la couleur du transparent)
    premultiplie = np.dstack([couleur * opacite[..., None], opacite[..., None] * 255.0])
    reduit = premultiplie.reshape(cote, echelle, cote, echelle, 4).mean(axis=(1, 3))
    alpha = reduit[..., 3] / 255.0
    rgb = np.where(alpha[..., None] > 1e-9, reduit[..., :3] / np.maximum(alpha[..., None], 1e-9), 0.0)
    return Image.fromarray(np.clip(np.dstack([rgb, reduit[..., 3]]).round(), 0, 255).astype(np.uint8), "RGBA")


def ecrire_roue(dossier, images=IMAGES):
    """Écrit throbber-0001.png à throbber-00NN.png dans `dossier` : le tour complet, une image tous les 360/NN degrés."""
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    for ancienne in dossier.glob("throbber-*.png"):
        ancienne.unlink()
    for i in range(images):
        dessiner(-math.pi / 2 + 2 * math.pi * i / images).save(dossier / f"throbber-{i + 1:04d}.png", optimize=True)
    return images


if __name__ == "__main__":
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "system_files/usr/share/plymouth/themes/binixx"
    print(f"{ecrire_roue(cible)} images écrites dans {cible}")
