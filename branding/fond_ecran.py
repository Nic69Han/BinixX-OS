#!/usr/bin/env python3
"""« Le marcheur de l'aube » : le fond d'écran de BinixX OS.

Un horizon de planète vu de l'espace, un ciel étoilé en bleu BinixX OS avec la Voie lactée, et un homme seul qui marche
vers l'aube, tout petit, réduit à sa forme : une silhouette sombre, sans visage ni détail, avec une écharpe qui flotte
derrière lui comme un clin d'œil au Petit Prince. L'idée : un fond qu'on reconnaît tout de suite et qui n'appartient
qu'à BinixX OS, comme « Bliss » pour Windows XP. Une photo de la NASA serait aussi belle, mais on l'attribuerait à la NASA.

Tout est calculé (bruit fractal, étoiles, lumière, silhouette dessinée en formes simples) : aucune image tierce, donc
aucune licence à citer ; le résultat est identique d'une exécution à l'autre (graine fixe).

    pip install numpy scipy pillow
    python3 branding/fond_ecran.py [largeur] [sortie.png] [clair|nuit]

`clair` est le fond du thème BinixX OS, `nuit` celui du thème BinixX OS sombre (ciel plus sombre, nébuleuse plus discrète).
branding/generer.py appelle `ecrire_fonds()` pour produire les fichiers de l'image.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

GRAINE = 7
MODES = ("clair", "nuit")
HAUTEUR_MARCHEUR = 0.068    # taille de l'homme, en part de la hauteur de l'image (73 px en 1080p)
POSITION_MARCHEUR = 0.085   # son écart avec le soleil, en part de la largeur de l'image : il marche vers lui


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


def _arrondir(points, tours=2):
    """Adoucit les coins d'un polygone fermé (découpage de Chaikin) : une ligne brisée devient une courbe."""
    for _ in range(tours):
        nouveaux = []
        for i, (x0, y0) in enumerate(points):
            x1, y1 = points[(i + 1) % len(points)]
            nouveaux += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        points = nouveaux
    return points


def marcheur(hauteur, sur_echantillonnage=6):
    """Silhouette d'un homme qui marche, de profil, tourné vers la droite : (opacité, pied_x, pied_y).

    Rien que la forme, comme un personnage vu de très loin : tête avec nez et menton, cou, épaules, dos, jambes en pleine
    enjambée (l'une tendue, le talon en avant ; l'autre qui pousse sur la pointe du pied), bras qui se balancent, et une
    écharpe qui flotte derrière lui. `hauteur` est la taille de l'homme en pixels, pieds compris. Le résultat est un
    masque (h, l) en niveaux de 0 à 1 ; (pied_x, pied_y) est le point du masque où il pose le pied, au sol.
    Dessiné à 6 fois la taille puis réduit, pour des contours nets sans escalier."""
    s = sur_echantillonnage
    u = hauteur * s                          # une unité = la hauteur de l'homme
    largeur, haut = int(1.10 * u), int(1.06 * u)
    ox, oy = 0.66 * u, 1.04 * u              # le pied dans le masque (y = 0 au sol, le haut du corps est négatif)
    masque = Image.new("L", (largeur, haut), 0)
    d = ImageDraw.Draw(masque)

    def p(x, y):
        # un très léger penché vers l'avant : le haut du corps avance, les pieds restent au sol
        return (ox + (x + 0.025 * -y) * u, oy + y * u)

    def membre(points):
        """Un membre : une ligne brisée de (x, y, épaisseur) dont l'épaisseur varie, arrondie aux deux bouts."""
        pts = [(p(x, y), e * u / 2) for x, y, e in points]
        gauche, droite = [], []
        for i, ((x, y), r) in enumerate(pts):
            ax, ay = pts[max(i - 1, 0)][0]
            bx, by = pts[min(i + 1, len(pts) - 1)][0]
            n = math.hypot(bx - ax, by - ay) or 1
            nx, ny = -(by - ay) / n, (bx - ax) / n
            gauche.append((x + nx * r, y + ny * r))
            droite.append((x - nx * r, y - ny * r))
        d.polygon(_arrondir(gauche + droite[::-1], 1), fill=255)
        for (x, y), r in (pts[0], pts[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)

    def forme(points, tours=2):
        d.polygon(_arrondir([p(*q) for q in points], tours), fill=255)

    hanche = (0.0, -0.49)
    # jambe avant : presque tendue, le talon attaque le sol
    membre([(*hanche, 0.115), (0.050, -0.375, 0.098), (0.095, -0.265, 0.074), (0.125, -0.185, 0.070),
            (0.158, -0.090, 0.048), (0.172, -0.052, 0.044)])
    forme([(0.150, -0.070), (0.200, -0.066), (0.285, -0.022), (0.285, 0.0), (0.168, 0.0), (0.150, -0.030)], 1)
    # jambe arrière : genou plié, talon levé, appui sur la pointe du pied
    membre([(*hanche, 0.115), (-0.040, -0.375, 0.098), (-0.078, -0.268, 0.074), (-0.125, -0.205, 0.072),
            (-0.190, -0.125, 0.048), (-0.212, -0.098, 0.043)])
    forme([(-0.232, -0.118), (-0.190, -0.100), (-0.108, -0.028), (-0.108, 0.0), (-0.145, 0.0), (-0.214, -0.062)], 1)

    # tronc, de profil : épaules, dos, creux des reins, fesses, ventre plat, poitrine
    forme([(-0.040, -0.835), (-0.070, -0.800), (-0.078, -0.730), (-0.066, -0.640), (-0.058, -0.585),
           (-0.085, -0.525), (-0.088, -0.480), (-0.040, -0.452), (0.045, -0.452), (0.058, -0.500),
           (0.052, -0.580), (0.062, -0.660), (0.070, -0.740), (0.058, -0.800), (0.030, -0.838)])

    # bras, qui se balancent à l'opposé des jambes : épaule, coude, poignet, main
    epaule = (0.002, -0.772)
    membre([(*epaule, 0.060), (-0.040, -0.690, 0.052), (-0.076, -0.612, 0.046), (-0.112, -0.545, 0.040),
            (-0.138, -0.492, 0.036), (-0.150, -0.462, 0.030)])
    membre([(*epaule, 0.060), (0.045, -0.695, 0.052), (0.085, -0.620, 0.046), (0.118, -0.552, 0.040),
            (0.142, -0.503, 0.036), (0.152, -0.470, 0.030)])

    # cou et tête, un peu avancée, avec le nez et le menton
    membre([(0.000, -0.830, 0.056), (0.010, -0.862, 0.050)])
    x, y = p(0.028, -0.930)
    rx, ry = 0.056 * u, 0.072 * u
    d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=255)
    forme([(0.066, -0.945), (0.100, -0.918), (0.072, -0.900)], 0)

    # l'écharpe : une bande ondulante qui s'affine en flottant derrière lui
    haut_e, bas_e = [], []
    for i in range(41):
        t = i / 40
        ex = -0.60 * t
        ey = -0.835 + 0.060 * math.sin(2 * math.pi * 1.2 * t) - 0.085 * t
        e = (0.056 * (1 - t) ** 0.8 + 0.016) / 2
        haut_e.append(p(ex, ey - e))
        bas_e.append(p(ex, ey + e))
    d.polygon(haut_e + bas_e[::-1], fill=255)

    petit = masque.resize((largeur // s, haut // s), Image.LANCZOS)
    return np.asarray(petit, np.float32) / 255.0, int(ox / s), int(oy / s)


def geometrie(largeur, hauteur_image):
    """Où tout se trouve, en pixels : le soleil, l'horizon, la planète (centre et rayon) et les pieds du marcheur."""
    w, h = largeur, hauteur_image
    sx, horizon = w * 0.62, h * 0.745
    sy = horizon - 0.116 * h                  # le soleil est juste derrière l'horizon
    rayon = 2.2 * w                           # la planète est un cercle immense : on n'en voit que le haut
    cx, cy = sx, horizon + rayon
    taille = max(8, int(HAUTEUR_MARCHEUR * h))
    xf = sx - POSITION_MARCHEUR * w
    yf = cy - math.sqrt(rayon ** 2 - (xf - cx) ** 2) + 1.5 * (w / 1920)   # les pieds s'enfoncent un peu dans le sol
    return {"soleil": (sx, sy), "horizon": horizon, "planete": (cx, cy, rayon), "pieds": (xf, yf), "taille": taille}


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

    # --- le soleil se lève derrière l'horizon d'une planète
    lieux = geometrie(w, h)
    (sx, sy), horizon = lieux["soleil"], lieux["horizon"]
    cx, cy, rayon = lieux["planete"]
    sd = rayon - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)   # > 0 dans la planète, < 0 dans le ciel
    ciel = sd < 0

    # --- ciel : de l'encre au bleu BinixX OS
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
        if (x - sx) ** 2 + (y - sy) ** 2 < (0.45 * h) ** 2:
            continue   # pas d'étoile à aiguilles dans la lumière du soleil
        etoile(etoiles, x, y, rng.uniform(0.35, 0.85) * (0.55 if mode == "nuit" else 0.85), _vec(0.85, 0.92, 1.0), True, echelle)
    img = img + etoiles * ciel[..., None]

    # --- la lumière du soleil : un halo chaud, puis bleu, et un cœur très lumineux juste derrière l'horizon
    r = np.sqrt((xx - sx) ** 2 + ((yy - sy) * 1.15) ** 2)
    chaud_halo = np.exp(-r / (0.16 * h)) * 0.95 + np.exp(-r / (0.42 * h)) * 0.35
    img = img + (chaud_halo * ciel)[..., None] * _vec(1.0, 0.62, 0.30)
    img = img + (np.exp(-r / (0.75 * h)) * 0.55 * ciel)[..., None] * _vec(0.25, 0.45, 1.0)
    c = np.sqrt((xx - sx) ** 2 + ((yy - (horizon - 0.015 * h)) * 1.35) ** 2)
    img = img + ((np.exp(-c / (0.050 * h)) * 1.9 + np.exp(-c / (0.14 * h)) * 0.95) * ciel)[..., None] * _vec(1.0, 0.72, 0.40)
    img = img / (1 + 0.55 * img)   # la lumière entre dans la plage d'affichage
    img = img ** (1 / 1.12)

    # --- lueur d'aube : l'ambre qui court sur l'horizon de part et d'autre du soleil
    aube = np.exp(-np.clip(-sd, 0, None) / (0.045 * h)) * np.exp(-((xx - sx) ** 2) / (2 * (0.22 * w) ** 2)) * ciel
    img = img + aube[..., None] * _vec(1.0, 0.42, 0.10) * 1.30

    # --- la planète : bleu nuit profond, éclairée seulement près du soleil ; un filet d'atmosphère sur la courbure
    surface = bruit_fractal(rng, h, w, [90 * echelle, 30 * echelle, 9 * echelle, 3 * echelle], [1.0, 0.8, 0.5, 0.3],
                            reduction)
    eclairage = np.exp(-((xx - sx) ** 2) / (2 * (0.30 * w) ** 2))
    profondeur = np.clip(sd / (0.30 * h), 0, 1)
    lueur = _vec(0.55, 0.26, 0.12) * (eclairage * np.exp(-sd / (0.045 * h)) * 0.55)[..., None]
    lueur = lueur + _vec(0.10, 0.26, 0.85) * (eclairage * np.exp(-sd / (0.16 * h)) * 0.30)[..., None]
    planete = _vec(0.006, 0.012, 0.050) + (0.010 + 0.022 * surface[..., None]) * _vec(0.5, 0.7, 1.0) \
        * (1 - profondeur[..., None] * 0.8)
    planete = planete + lueur * (0.45 + 0.8 * surface[..., None])
    corps = np.clip(sd / (1.2 * echelle) + 0.5, 0, 1)
    img = img * (1 - corps[..., None]) + planete * corps[..., None]
    filet = np.exp(-np.abs(sd) / (2.6 * echelle)) * 0.9 + np.exp(-np.clip(-sd, 0, None) / (14 * echelle)) * 0.45 * ciel
    chaleur = np.exp(-((xx - sx) ** 2) / (2 * (0.20 * w) ** 2))
    teinte_filet = melange(np.broadcast_to(_vec(0.35, 0.65, 1.0), (h, w, 3)), np.broadcast_to(_vec(1.0, 0.62, 0.30), (h, w, 3)),
                           chaleur)
    img = img + teinte_filet * filet[..., None] * (0.55 + 0.45 * chaleur[..., None])
    voile = np.exp(-np.clip(-sd, 0, None) / (0.050 * h)) * ciel
    img = img + voile[..., None] * melange(np.broadcast_to(_vec(0.05, 0.16, 0.55), (h, w, 3)),
                                           np.broadcast_to(_vec(0.60, 0.32, 0.20), (h, w, 3)), chaleur) * 0.55

    # --- l'homme qui marche vers l'aube, tout petit sur la courbure de la planète : une forme sombre, sans détail
    opac, pied_x, pied_y = marcheur(lieux["taille"])
    xf, yf = lieux["pieds"]
    x0, y0 = int(xf - pied_x), int(yf - pied_y)
    zone = (slice(max(y0, 0), min(y0 + opac.shape[0], h)), slice(max(x0, 0), min(x0 + opac.shape[1], w)))
    masque = np.zeros((h, w), np.float32)
    masque[zone] = opac[zone[0].start - y0: zone[0].stop - y0, zone[1].start - x0: zone[1].stop - x0]
    img = img * (1 - masque[..., None]) + _vec(0.004, 0.007, 0.024) * masque[..., None]

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
    sortie = Path(sys.argv[2] if len(sys.argv) > 2 else "fond-ecran.png")
    rendre(largeur, sys.argv[3] if len(sys.argv) > 3 else "clair").save(sortie)
    print("ok", sortie)
