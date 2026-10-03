#!/usr/bin/env python3
"""« Lever de gemme » : le fond d'écran de NicOS.

Un horizon de planète vu de l'espace, un ciel étoilé en bleu NicOS, et la gemme du logo qui se lève comme un soleil,
une aube d'ambre sur l'horizon. L'idée : un fond qu'on reconnaît tout de suite et qui n'appartient qu'à NicOS, comme
« Bliss » pour Windows XP. Une photo de la NASA serait aussi belle, mais on l'attribuerait à la NASA.

Tout est calculé (bruit fractal, étoiles, lumière, gemme dessinée d'après branding/generer.py) : aucune image tierce,
donc aucune licence à citer ; le résultat est identique d'une exécution à l'autre (graine fixe).

    pip install numpy scipy pillow
    python3 branding/lever_de_gemme.py [largeur] [sortie.png] [clair|nuit]

`clair` est le fond du thème NicOS, `nuit` celui du thème NicOS sombre (ciel plus sombre, nébuleuse plus discrète).
branding/generer.py appelle `ecrire_fonds()` pour produire les fichiers de l'image.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

# Dégradé de la gemme sur fond clair : identique à GEM_LIGHT de generer.py (un test le vérifie)
GEM_LIGHT = [(0.0, "#5FB2FF"), (0.45, "#2F5BFF"), (1.0, "#1A26C9")]
GRAINE = 7
MODES = ("clair", "nuit")


def _couleur(hexa):
    return [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def _vec(*valeurs):
    return np.array(valeurs, np.float32)


def flou(champ, sigma, reduction=1):
    """Flou gaussien ; les grands flous se font sur une image réduite (même résultat, bien plus vite en 4K)."""
    if reduction <= 1:
        return gaussian_filter(champ, sigma)
    h, w = champ.shape
    petit = np.asarray(Image.fromarray(champ).resize((w // reduction, h // reduction), Image.BOX), np.float32)
    petit = gaussian_filter(petit, sigma / reduction)
    return np.asarray(Image.fromarray(petit).resize((w, h), Image.BICUBIC), np.float32)


def bruit_fractal(rng, h, w, echelles, gains, reduction=1):
    """Bruit fractal : somme de bruits blancs flous à plusieurs échelles, ramené à [0, 1]."""
    total = np.zeros((h, w), np.float32)
    for sigma, gain in zip(echelles, gains):
        gros = reduction > 1 and sigma >= 6 * reduction
        hh, ww = (h // reduction, w // reduction) if gros else (h, w)
        n = gaussian_filter(rng.standard_normal((hh, ww)).astype(np.float32), sigma / (reduction if gros else 1),
                            mode="wrap")
        n = n / (n.std() + 1e-6)
        if gros:
            n = np.asarray(Image.fromarray(n).resize((w, h), Image.BICUBIC), np.float32)
        total += gain * n
    total -= total.min()
    return total / (total.max() + 1e-6)


def melange(a, b, t):
    """a + (b - a) * t, avec t de forme (h, w) et a, b de forme (h, w, 3) ou (3,)."""
    return a + (b - a) * t[..., None]


def gemme(taille, sur_echantillonnage=3):
    """La gemme du logo (même géométrie que generer.gem) : (couleur pré-multipliée, opacité), de côté `taille` px.

    Un losange aux angles doux, fendu de deux entailles diagonales, en dégradé ciel -> bleu NicOS -> indigo, avec une
    lumière blanche venant du haut. Dessinée à partir d'une distance signée, puis réduite pour lisser les bords."""
    n = taille * sur_echantillonnage
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = xx - c, yy - c
    cote = taille * 0.96 / math.sqrt(2) * 0.98   # côté du carré avant rotation (generer.gem : size / sqrt(2) * 0.98)
    cote *= sur_echantillonnage
    rayon = cote * 0.2
    # repère de la gemme : le carré tourné de 45 degrés
    lx = (dx - dy) / math.sqrt(2)
    ly = (dx + dy) / math.sqrt(2)
    qx, qy = np.abs(lx) - (cote / 2 - rayon), np.abs(ly) - (cote / 2 - rayon)
    distance = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rayon
    dedans = distance <= 0
    # trois lames de poids 1,25 / 1 / 0,8 séparées par des entailles
    poids, entaille = (1.25, 1.0, 0.8), cote * 0.05
    unite = (cote - entaille * 2) / sum(poids)
    lames = np.zeros_like(dedans)
    y = -cote / 2
    for p in poids:
        lames |= (ly >= y) & (ly < y + p * unite)
        y += p * unite + entaille
    lames &= dedans
    # dégradé le long de la diagonale de la gemme
    t = np.clip((lx + ly + cote) / (2 * cote), 0, 1)
    couleur = np.stack([np.interp(t, [o for o, _ in GEM_LIGHT], [_couleur(h)[k] for _, h in GEM_LIGHT])
                        for k in range(3)], axis=-1).astype(np.float32)
    # lumière du haut : blanc à 26 % en haut à droite du carré, jusqu'à 0 vers le centre
    u, v = (lx + cote / 2) / cote, (ly + cote / 2) / cote
    lumiere = 0.26 * (1 - np.clip((1 - u + v) / 1.3, 0, 1)) * dedans
    a_lames = lames.astype(np.float32)
    opacite = a_lames + lumiere * (1 - a_lames)
    couleur_pm = couleur * (a_lames * (1 - lumiere))[..., None] + lumiere[..., None]
    s = sur_echantillonnage
    reduit = lambda a: a.reshape(taille, s, taille, s, *a.shape[2:]).mean(axis=(1, 3))  # noqa: E731
    return reduit(couleur_pm).astype(np.float32), reduit(opacite).astype(np.float32)


def etoile(canevas, x, y, luminosite, teinte, aiguilles, echelle=1.0):
    """Pose une étoile : un cœur gaussien et, pour les plus brillantes, des aiguilles de diffraction (style Webb).
    `echelle` suit la taille de l'image : une étoile occupe la même part de l'écran en 1080p et en 4K."""
    h, w, _ = canevas.shape
    r = int((18 + luminosite * 110) * echelle) if aiguilles else int(6 * echelle)
    x0, x1, y0, y1 = max(int(x) - r, 0), min(int(x) + r + 1, w), max(int(y) - r, 0), min(int(y) + r + 1, h)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - x, yy - y
    valeur = np.exp(-(dx * dx + dy * dy) / (2 * ((0.9 + luminosite * 1.6) * echelle) ** 2)) * luminosite
    if aiguilles:
        longueur = (6 + luminosite * 42) * echelle
        for angle, poids in ((0, 1.0), (math.pi / 2, 1.0), (math.pi / 4, 0.45), (-math.pi / 4, 0.45)):
            c, s = math.cos(angle), math.sin(angle)
            valeur = valeur + poids * luminosite * 0.55 * np.exp(-((-dx * s + dy * c) ** 2) / (0.9 * echelle * echelle)) \
                * np.exp(-np.abs(dx * c + dy * s) / longueur)
    canevas[y0:y1, x0:x1] += valeur[..., None] * teinte


def rendre(largeur=1920, mode="clair", graine=GRAINE):
    """Le fond d'écran, en 16:9, sous forme d'image Pillow."""
    if mode not in MODES:
        raise ValueError(f"mode inconnu : {mode} (attendu : {', '.join(MODES)})")
    w = largeur
    h = round(largeur * 9 / 16)
    echelle = w / 1920
    reduction = max(1, int(echelle * 2))
    rng = np.random.default_rng(graine)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h

    # --- la gemme se lève derrière l'horizon d'une planète : presque entière, seule sa pointe basse est cachée
    taille = int(0.58 * h)
    gx, horizon = w * 0.62, h * 0.745
    gy = horizon - 0.20 * taille
    rayon = 2.2 * w
    cx, cy = gx, horizon + rayon
    sd = rayon - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)   # > 0 dans la planète, < 0 dans le ciel
    ciel = sd < 0

    # --- ciel : de l'encre au bleu NicOS
    haut, milieu, bas = _vec(0.012, 0.020, 0.075), _vec(0.030, 0.060, 0.300), _vec(0.090, 0.250, 0.800)
    t = np.clip(yy / max(horizon, 1), 0, 1) ** 1.6
    img = melange(np.broadcast_to(haut, (h, w, 3)), np.broadcast_to(milieu, (h, w, 3)), np.clip(t * 1.8, 0, 1))
    img = melange(img, np.broadcast_to(bas, (h, w, 3)), np.clip((t - 0.45) * 1.9, 0, 1))
    if mode == "nuit":
        img = img * 0.55

    # --- Voie lactée : une bande diagonale de nébuleuse, bleu et violet, avec une pointe de chaud
    diagonale = ((u - 0.15) * 0.62 - (v - 0.10)) * 2.3
    bande = np.exp(-(diagonale ** 2) / 0.050)
    brume = bruit_fractal(rng, h, w, [60 * echelle, 22 * echelle, 8 * echelle, 3 * echelle], [1.0, 0.7, 0.45, 0.25],
                          reduction)
    nuage = np.clip(bande * (0.25 + 1.3 * brume ** 1.6), 0, 1)
    teinte = melange(np.broadcast_to(_vec(0.20, 0.25, 0.95), (h, w, 3)), np.broadcast_to(_vec(0.50, 0.32, 0.95), (h, w, 3)),
                     brume)
    chaud = np.clip((brume - 0.62) * 3.2, 0, 1) * bande
    teinte = melange(teinte, np.broadcast_to(_vec(1.0, 0.62, 0.35), (h, w, 3)), chaud)
    img = img + teinte * (nuage ** 1.1)[..., None] * (0.50 if mode == "clair" else 0.34)

    # --- étoiles : une poussière fine, plus dense le long de la Voie lactée, et quelques brillantes à aiguilles
    etoiles = np.zeros((h, w, 3), np.float32)
    nombre = int(3300 * echelle * echelle)
    px, py = rng.uniform(0, w, nombre), rng.uniform(0, h * 0.78, nombre)
    lum = np.clip(rng.pareto(2.6, nombre) * 0.085 + 0.035, 0, 0.50)
    chaudes = rng.random(nombre) < 0.14
    for x, y, b, c in zip(px, py, lum, chaudes):
        etoile(etoiles, x, y, b, _vec(1.0, 0.86, 0.70) if c else _vec(0.80, 0.88, 1.0), False, echelle)
    for _ in range(int(1500 * echelle * echelle)):
        x, y = rng.uniform(0, w), rng.uniform(0, h * 0.75)
        if rng.random() < np.exp(-((((x / w - 0.15) * 0.62 - (y / h - 0.10)) * 2.3) ** 2) / 0.11):
            etoile(etoiles, x, y, rng.uniform(0.03, 0.24), _vec(0.85, 0.90, 1.0), False, echelle)
    for _ in range(11):
        x, y = rng.uniform(0.03 * w, 0.97 * w), rng.uniform(0.03 * h, 0.55 * h)
        if (x - gx) ** 2 + (y - gy) ** 2 < (0.45 * h) ** 2:
            continue
        etoile(etoiles, x, y, rng.uniform(0.35, 0.85) * (0.55 if mode == "nuit" else 0.85), _vec(0.85, 0.92, 1.0), True, echelle)
    img = img + etoiles * ciel[..., None]

    # --- la lumière du soleil-gemme : un halo chaud, puis bleu
    r = np.sqrt((xx - gx) ** 2 + ((yy - gy) * 1.15) ** 2)
    chaud_halo = np.exp(-r / (0.16 * h)) * 0.95 + np.exp(-r / (0.42 * h)) * 0.35
    img = img + (chaud_halo * ciel)[..., None] * _vec(1.0, 0.62, 0.30)
    img = img + (np.exp(-r / (0.75 * h)) * 0.55 * ciel)[..., None] * _vec(0.25, 0.45, 1.0)
    img = img / (1 + 0.55 * img)   # le ciel entre dans la plage d'affichage avant de poser la gemme
    img = img ** (1 / 1.12)

    # --- la gemme, avec son éclat ; elle garde ses vraies couleurs
    couleur_gemme, opacite = gemme(taille)
    x0, y0 = int(gx - taille / 2), int(gy - taille / 2)
    fond_gemme = np.zeros((h, w, 3), np.float32)
    alpha = np.zeros((h, w), np.float32)
    fond_gemme[y0:y0 + taille, x0:x0 + taille] = couleur_gemme
    alpha[y0:y0 + taille, x0:x0 + taille] = opacite
    reflet = np.clip((yy - (gy + taille * 0.05)) / (taille * 0.40), 0, 1) ** 1.5   # reflet chaud côté horizon
    fond_gemme = fond_gemme * (1 - 0.30 * reflet[..., None]) + (0.30 * reflet * alpha)[..., None] * _vec(1.0, 0.70, 0.42)
    img = img * (1 - alpha[..., None]) + fond_gemme
    eclat = flou(alpha, 46 * echelle, reduction * 2) * 1.0 + flou(alpha, 14 * echelle, reduction) * 0.45
    hors_gemme = (1 - alpha) ** 2
    img = img + (eclat * hors_gemme)[..., None] * _vec(0.22, 0.45, 1.0) * 0.80
    # lueur d'aube : l'ambre qui court sur l'horizon de part et d'autre de la gemme
    aube = np.exp(-np.clip(-sd, 0, None) / (0.045 * h)) * np.exp(-((xx - gx) ** 2) / (2 * (0.22 * w) ** 2)) * ciel
    img = img + (aube * hors_gemme)[..., None] * _vec(1.0, 0.42, 0.10) * 1.30

    # --- la planète : bleu nuit profond, éclairée seulement près de la gemme ; un filet d'atmosphère sur la courbure
    surface = bruit_fractal(rng, h, w, [90 * echelle, 30 * echelle, 9 * echelle, 3 * echelle], [1.0, 0.8, 0.5, 0.3],
                            reduction)
    eclairage = np.exp(-((xx - gx) ** 2) / (2 * (0.30 * w) ** 2))
    profondeur = np.clip(sd / (0.30 * h), 0, 1)
    lueur = _vec(0.55, 0.26, 0.12) * (eclairage * np.exp(-sd / (0.045 * h)) * 0.55)[..., None]
    lueur = lueur + _vec(0.10, 0.26, 0.85) * (eclairage * np.exp(-sd / (0.16 * h)) * 0.30)[..., None]
    planete = _vec(0.006, 0.012, 0.050) + (0.010 + 0.022 * surface[..., None]) * _vec(0.5, 0.7, 1.0) \
        * (1 - profondeur[..., None] * 0.8)
    planete = planete + lueur * (0.45 + 0.8 * surface[..., None])
    corps = np.clip(sd / (1.2 * echelle) + 0.5, 0, 1)
    img = img * (1 - corps[..., None]) + planete * corps[..., None]
    filet = np.exp(-np.abs(sd) / (2.6 * echelle)) * 0.9 + np.exp(-np.clip(-sd, 0, None) / (14 * echelle)) * 0.45 * ciel
    chaleur = np.exp(-((xx - gx) ** 2) / (2 * (0.20 * w) ** 2))
    teinte_filet = melange(np.broadcast_to(_vec(0.35, 0.65, 1.0), (h, w, 3)), np.broadcast_to(_vec(1.0, 0.62, 0.30), (h, w, 3)),
                           chaleur)
    img = img + teinte_filet * filet[..., None] * (0.55 + 0.45 * chaleur[..., None])
    voile = np.exp(-np.clip(-sd, 0, None) / (0.050 * h)) * ciel
    img = img + voile[..., None] * melange(np.broadcast_to(_vec(0.05, 0.16, 0.55), (h, w, 3)),
                                           np.broadcast_to(_vec(0.60, 0.32, 0.20), (h, w, 3)), chaleur) * 0.55

    # --- vignettage doux, puis un grain très fin contre les bandes des dégradés
    img = img * (1 - 0.28 * np.clip(((u - 0.55) ** 2 * 1.5 + (v - 0.45) ** 2 * 1.2) * 1.6, 0, 1))[..., None]
    img = img + rng.normal(0, 0.006, img.shape).astype(np.float32)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


def ecrire_fonds(dossier, tailles=((1920, 1080), (3840, 2160)), qualite=92):
    """Écrit les fonds de l'image dans `dossier` (le « contents » d'un thème de fond d'écran KDE) :
    images/ pour le thème clair, images_dark/ pour le sombre, et une vignette d'aperçu.

    Chaque fond est calculé une seule fois à la plus grande taille, puis réduit : toutes les tailles montrent
    exactement le même ciel (le hasard du bruit et des étoiles dépend de la taille de l'image)."""
    dossier = Path(dossier)
    grande = max(largeur for largeur, _ in tailles)
    for sous_dossier, mode in (("images", "clair"), ("images_dark", "nuit")):
        (dossier / sous_dossier).mkdir(parents=True, exist_ok=True)
        maitre = rendre(grande, mode)
        for largeur, hauteur in tailles:
            fond = maitre if maitre.width == largeur else maitre.resize((largeur, hauteur), Image.LANCZOS)
            assert fond.size == (largeur, hauteur), fond.size
            fond.save(dossier / sous_dossier / f"{largeur}x{hauteur}.jpg", "JPEG", quality=qualite, optimize=True,
                      progressive=True)
        if mode == "clair":
            maitre.resize((640, 360), Image.LANCZOS).save(dossier / "screenshot.jpg", "JPEG", quality=85, optimize=True)


if __name__ == "__main__":
    largeur = int(sys.argv[1]) if len(sys.argv) > 1 else 1920
    sortie = Path(sys.argv[2] if len(sys.argv) > 2 else "lever-de-gemme.png")
    rendre(largeur, sys.argv[3] if len(sys.argv) > 3 else "clair").save(sortie)
    print("ok", sortie)
