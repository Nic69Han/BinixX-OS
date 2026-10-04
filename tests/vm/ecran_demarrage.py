#!/usr/bin/python3
"""Lit l'écran de la VM pendant le démarrage et le décrit en texte, pour le journal du test.

Un test ne peut pas « regarder » un écran : on le réduit à quelques chiffres (part de noir, de bleu nuit du fond BinixX OS, de
pixels clairs) qui disent s'il montre une console de texte, le menu GRUB, l'écran de démarrage ou le bureau, et à une vignette
en caractères que l'on lit dans le journal.

    ecran_demarrage.py resume FICHIER.ppm
    ecran_demarrage.py surveiller SOCKET_QMP FICHIER_LOG FICHIER_ARRET [DUREE_MAX_SECONDES]
    ecran_demarrage.py verifier FICHIER_LOG.csv [--sans-connexion]

« surveiller » prend une capture par seconde (QMP, format PPM) jusqu'à ce que FICHIER_ARRET existe ou que la durée soit écoulée,
et écrit une ligne de journal quand l'écran change de nature (avec la vignette), plus un fichier FICHIER_LOG.csv à une ligne par
capture. « verifier » lit ce fichier et dit si le démarrage ressemble à celui de Windows : l'écran de démarrage apparaît, aucun
texte de console n'est visible une fois qu'il est là (et presque aucun avant), l'indicateur de chargement (la roue qui tourne sous le
logo) est visible et bouge, l'écran de connexion finit par s'afficher."""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

COLONNES, LIGNES = 64, 18
RAMPE = " .:-=+*#%@"

# Libellés, dans l'ordre où ils sont décidés (voir classer)
NOIR = "noir"
TEXTE = "texte sur fond noir (console ou menu GRUB)"
DEMARRAGE = "écran de démarrage BinixX OS"
CLAIR = "écran clair (connexion ou bureau)"
SOMBRE = "écran sombre (connexion ou bureau)"
QUELQUES_LIGNES = "quelques lignes de texte (micrologiciel, menu GRUB)"
LOGO = "logo sur fond noir (micrologiciel, ou connexion qui démarre)"
AUTRE = "autre"


CODES = {NOIR: "NOIR", TEXTE: "TEXTE", QUELQUES_LIGNES: "LIGNES", LOGO: "LOGO", DEMARRAGE: "DEMARRAGE", CLAIR: "CLAIR", SOMBRE: "SOMBRE", AUTRE: "AUTRE"}
# Le texte d'une console est collé au bord gauche de l'écran (chaque ligne commence à la première colonne) ; un logo est au centre.
# MARGE_GAUCHE : part de la largeur de l'écran qui compte comme « le bord gauche » ; PART_TEXTE : part des pixels clairs qui doit s'y trouver
MARGE_GAUCHE = 0.12
PART_TEXTE = 0.05
# Un écran de texte (console du noyau, de systemd) couvre beaucoup d'écran : au moins cette part de pixels clairs. En dessous, ce sont
# quelques lignes seulement (le micrologiciel de la machine virtuelle, OVMF, écrit deux lignes « BdsDxe: loading … shimx64.efi » en haut à
# gauche avant même GRUB ; un vrai PC affiche à la place le logo de son constructeur).
PART_ECRAN_DE_TEXTE = 0.03
# Captures de « quelques lignes » tolérées avant l'écran de démarrage : le micrologiciel les laisse à l'écran jusqu'à ce que le noyau prenne la main, plus longtemps en machine virtuelle
LIGNES_TOLEREES_AVANT = 12
# Captures de texte de console tolérées avant l'écran de démarrage (arrêt, micrologiciel, menu GRUB : au plus quelques secondes)
TEXTE_TOLERE_AVANT = 3
# L'indicateur de chargement (roue qui tourne) est l'animation du thème Plymouth, sous le logo : on regarde un carré de pixels autour de son
# centre. INDICATEUR_X et INDICATEUR_Y sont les réglages HorizontalAlignment et VerticalAlignment de binixx.plymouth (part de l'écran).
INDICATEUR_X, INDICATEUR_Y = 0.5, 0.72
INDICATEUR_DEMI_COTE = 64
# Luminance à partir de laquelle un pixel de la zone appartient à l'indicateur (le fond de démarrage est à 20 environ)
INDICATEUR_PIXEL_CLAIR = 110
# Pixels clairs en dessous desquels l'indicateur n'est pas visible ; pixels qui changent entre deux captures pour dire qu'il bouge
INDICATEUR_MIN = 12
MOUVEMENT_MIN = 6
# Écart de luminance qui compte comme « ce pixel a changé »
ECART_DE_LUMINANCE = 40


def lire_ppm(donnees):
    """(largeur, hauteur, octets RGB) d'une image PPM binaire (P6), comme l'écrit QEMU."""
    if not donnees.startswith(b"P6"):
        raise ValueError("pas une image PPM binaire (P6)")
    mots, position = [], 2
    while len(mots) < 3:
        while donnees[position:position + 1].isspace():
            position += 1
        if donnees[position:position + 1] == b"#":  # commentaire jusqu'à la fin de la ligne
            while donnees[position:position + 1] not in (b"\n", b""):
                position += 1
            continue
        debut = position
        while not donnees[position:position + 1].isspace() and position < len(donnees):
            position += 1
        mots.append(int(donnees[debut:position]))
    largeur, hauteur, maximum = mots
    if maximum != 255:
        raise ValueError("seules les images à 8 bits par couleur sont lues")
    pixels = donnees[position + 1:]
    if len(pixels) < largeur * hauteur * 3:
        raise ValueError("image tronquée")
    return largeur, hauteur, pixels


def fond_demarrage(rouge, vert, bleu):
    """Le dégradé bleu nuit du thème Plymouth (0b0f1a vers 10163a), et ce qui en est proche."""
    return 5 <= rouge <= 30 and 8 <= vert <= 40 and 20 <= bleu <= 75 and bleu >= rouge + 10 and bleu >= vert + 8


def luminance(rouge, vert, bleu):
    return (2126 * rouge + 7152 * vert + 722 * bleu) // 10000


def analyser(largeur, hauteur, pixels, pas=3):
    """Les mesures d'une image : parts (de 0 à 1) de noir, de fond de démarrage, de pixels clairs ; luminance moyenne."""
    total = noirs = fonds = clairs = clairs_a_gauche = somme = 0
    limite = int(largeur * MARGE_GAUCHE)
    for y in range(0, hauteur, pas):
        ligne = y * largeur * 3
        for x in range(0, largeur, pas):
            i = ligne + x * 3
            r, v, b = pixels[i], pixels[i + 1], pixels[i + 2]
            lum = luminance(r, v, b)
            total += 1
            somme += lum
            if r <= 10 and v <= 10 and b <= 10:
                noirs += 1
            elif fond_demarrage(r, v, b):
                fonds += 1
            if lum >= 150:
                clairs += 1
                if x < limite:
                    clairs_a_gauche += 1
    total = max(total, 1)
    return {"noir": noirs / total, "fond": fonds / total, "clair": clairs / total, "luminance": somme / total,
            "gauche": clairs_a_gauche / clairs if clairs else 0.0}


def classer(mesures):
    """Ce que montre l'écran : de quoi distinguer, sans le voir, la console de texte de l'écran de démarrage."""
    if mesures["noir"] >= 0.995:
        return NOIR
    if mesures["fond"] >= 0.5:
        return DEMARRAGE
    if mesures["noir"] >= 0.7 and mesures["clair"] > 0:
        if mesures["gauche"] < PART_TEXTE:
            return LOGO
        return TEXTE if mesures["clair"] >= PART_ECRAN_DE_TEXTE else QUELQUES_LIGNES
    if mesures["noir"] >= 0.97:
        return NOIR
    if mesures["luminance"] >= 90:
        return CLAIR
    if mesures["luminance"] >= 12:
        return SOMBRE
    return AUTRE


def vignette(largeur, hauteur, pixels):
    """L'image en COLONNES x LIGNES caractères : plus le caractère est chargé, plus la zone est lumineuse."""
    sortie = []
    for ligne in range(LIGNES):
        texte = ""
        y0, y1 = ligne * hauteur // LIGNES, max((ligne + 1) * hauteur // LIGNES, ligne * hauteur // LIGNES + 1)
        for colonne in range(COLONNES):
            x0, x1 = colonne * largeur // COLONNES, max((colonne + 1) * largeur // COLONNES, colonne * largeur // COLONNES + 1)
            maximum = 0
            for y in range(y0, y1, max((y1 - y0) // 3, 1)):
                for x in range(x0, x1, max((x1 - x0) // 3, 1)):
                    i = (y * largeur + x) * 3
                    maximum = max(maximum, luminance(pixels[i], pixels[i + 1], pixels[i + 2]))
            texte += RAMPE[min(maximum * len(RAMPE) // 256, len(RAMPE) - 1)]
        sortie.append(texte.rstrip())
    return sortie


def zone_indicateur(largeur, hauteur, demi_cote=INDICATEUR_DEMI_COTE):
    """(x0, y0, x1, y1) du carré autour du centre de l'indicateur de chargement, borné à l'image."""
    cx, cy = int(largeur * INDICATEUR_X), int(hauteur * INDICATEUR_Y)
    return max(cx - demi_cote, 0), max(cy - demi_cote, 0), min(cx + demi_cote, largeur), min(cy + demi_cote, hauteur)


def luminances_de_la_zone(largeur, hauteur, pixels, demi_cote=INDICATEUR_DEMI_COTE):
    """(largeur de la zone, octets de luminance, ligne par ligne) du carré de l'indicateur."""
    x0, y0, x1, y1 = zone_indicateur(largeur, hauteur, demi_cote)
    zone = bytearray()
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y * largeur + x) * 3
            zone.append(luminance(pixels[i], pixels[i + 1], pixels[i + 2]))
    return x1 - x0, bytes(zone)


def pixels_clairs(zone):
    """Combien de pixels de la zone sont assez clairs pour être l'indicateur."""
    return sum(1 for lum in zone if lum >= INDICATEUR_PIXEL_CLAIR)


def pixels_changes(zone, precedente):
    """Combien de pixels ont changé de luminance entre deux captures de la même zone ; -1 si on ne peut pas comparer."""
    if precedente is None or len(precedente) != len(zone):
        return -1
    return sum(1 for a, b in zip(zone, precedente) if abs(a - b) >= ECART_DE_LUMINANCE)


def vignette_de_la_zone(largeur_zone, zone, pas_x=2, pas_y=4):
    """La zone de l'indicateur en caractères (un caractère = pas_x x pas_y pixels) : on y voit la forme de la roue."""
    hauteur_zone = len(zone) // largeur_zone if largeur_zone else 0
    lignes = []
    for y in range(0, hauteur_zone, pas_y):
        texte = ""
        for x in range(0, largeur_zone, pas_x):
            maximum = max(zone[yy * largeur_zone + xx] for yy in range(y, min(y + pas_y, hauteur_zone))
                          for xx in range(x, min(x + pas_x, largeur_zone)))
            texte += RAMPE[min(maximum * len(RAMPE) // 256, len(RAMPE) - 1)]
        lignes.append(texte.rstrip())
    return lignes


def examiner(donnees_ppm):
    """(largeur, hauteur, octets, mesures, nature) d'une capture."""
    largeur, hauteur, pixels = lire_ppm(donnees_ppm)
    mesures = analyser(largeur, hauteur, pixels)
    return largeur, hauteur, pixels, mesures, classer(mesures)


def decrire(largeur, hauteur, pixels, mesures, nature, seconde=None, avec_vignette=False):
    """Les lignes de journal d'une capture : un résumé, et la vignette si demandée."""
    quand = "" if seconde is None else f"t={seconde:>3} s  "
    lignes = [f"{quand}{largeur}x{hauteur}  {nature}  (noir {mesures['noir']:.0%}, fond bleu nuit {mesures['fond']:.0%}, "
              f"pixels clairs {mesures['clair']:.1%} dont {mesures['gauche']:.0%} au bord gauche, luminance {mesures['luminance']:.0f})"]
    if avec_vignette:
        lignes += ["    |" + ligne for ligne in vignette(largeur, hauteur, pixels)]
    return lignes


def lire_le_texte(donnees_ppm, hauteur_lue=160, agrandissement=3):
    """Le texte écrit en haut de l'écran, lu par tesseract s'il est installé (sinon chaîne vide). Sert à savoir ce que sont ces lignes."""
    outil = shutil.which("tesseract")
    if outil is None:
        return ""
    largeur, hauteur, pixels = lire_ppm(donnees_ppm)
    hauteur_lue = min(hauteur_lue, hauteur)
    inverse = bytes(range(255, -1, -1))  # tesseract lit du texte foncé sur fond clair : on inverse
    lignes = []
    for y in range(hauteur_lue):
        ligne = pixels[y * largeur * 3:(y + 1) * largeur * 3].translate(inverse)
        agrandie = b"".join(ligne[i:i + 3] * agrandissement for i in range(0, len(ligne), 3))
        lignes += [agrandie] * agrandissement
    entete = b"P6\n%d %d\n255\n" % (largeur * agrandissement, hauteur_lue * agrandissement)
    with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as fichier:
        fichier.write(entete + b"".join(lignes))
    try:
        resultat = subprocess.run([outil, fichier.name, "stdout", "--psm", "6"], capture_output=True, text=True, timeout=60, check=False)
        return " | ".join(ligne.strip() for ligne in resultat.stdout.splitlines() if ligne.strip())
    except (OSError, subprocess.SubprocessError):
        return ""
    finally:
        os.remove(fichier.name)


def capture_qmp(socket_qmp, fichier):
    """Demande une capture PPM à QEMU. Renvoie False si l'écran n'est pas (encore) disponible."""
    prise = socket.socket(socket.AF_UNIX)
    prise.settimeout(20)
    try:
        prise.connect(socket_qmp)
        flux = prise.makefile("rw")

        def appeler(commande, arguments=None):
            message = {"execute": commande}
            if arguments:
                message["arguments"] = arguments
            flux.write(json.dumps(message) + "\n")
            flux.flush()
            while True:
                reponse = json.loads(flux.readline())
                if "return" in reponse or "error" in reponse:
                    return reponse

        json.loads(flux.readline())  # message d'accueil
        appeler("qmp_capabilities")
        return "error" not in appeler("screendump", {"filename": fichier, "format": "ppm"})
    except (OSError, ValueError):
        return False
    finally:
        prise.close()


def surveiller(socket_qmp, fichier_log, fichier_arret, duree_max=1800):
    """Une capture par seconde jusqu'à l'arrêt demandé ; la vignette à chaque changement de nature, au plus 25 fois."""
    debut = time.monotonic()
    derniere, vignettes, lectures, derniere_lecture = None, 0, 0, -1
    zone_precedente, vues_de_l_indicateur = None, 0
    temporaire = os.path.join(tempfile.gettempdir(), f"ecran-demarrage-{os.getpid()}.ppm")
    with open(fichier_log, "w", encoding="utf-8") as log, open(fichier_log + ".csv", "w", encoding="utf-8") as tableau:
        tableau.write("seconde;nature;noir;fond;clair;luminance;indicateur;mouvement\n")
        while not os.path.exists(fichier_arret) and time.monotonic() - debut < duree_max:
            if capture_qmp(socket_qmp, temporaire):
                try:
                    with open(temporaire, "rb") as image:
                        donnees = image.read()
                    seconde = int(time.monotonic() - debut)
                    largeur, hauteur, pixels, mesures, nature = examiner(donnees)
                    if nature in (QUELQUES_LIGNES, TEXTE) and lectures < 4 and seconde != derniere_lecture:
                        texte = lire_le_texte(donnees)
                        lectures, derniere_lecture = lectures + 1, seconde
                        if texte:
                            log.write(f"t={seconde:>3} s  texte lu en haut de l'écran : {texte[:300]}\n")
                            log.flush()
                    clairs, mouvement = 0, -1
                    if nature == DEMARRAGE:
                        largeur_zone, zone = luminances_de_la_zone(largeur, hauteur, pixels)
                        clairs = pixels_clairs(zone)
                        mouvement = pixels_changes(zone, zone_precedente if derniere == DEMARRAGE else None)
                        zone_precedente = zone
                        if vues_de_l_indicateur < 3:
                            vues_de_l_indicateur += 1
                            log.write(f"t={seconde:>3} s  indicateur de chargement : {clairs} pixel(s) clair(s), "
                                      f"{mouvement if mouvement >= 0 else 'pas de capture précédente'} pixel(s) changé(s)\n")
                            log.write("\n".join("    |" + ligne for ligne in vignette_de_la_zone(largeur_zone, zone)) + "\n")
                    tableau.write(f"{seconde};{CODES[nature]};{mesures['noir']:.3f};{mesures['fond']:.3f};"
                                  f"{mesures['clair']:.3f};{mesures['luminance']:.0f};{clairs};{mouvement}\n")
                    tableau.flush()
                    montrer = nature != derniere and vignettes < 25
                    if montrer or seconde % 20 == 0:
                        lignes = decrire(largeur, hauteur, pixels, mesures, nature, seconde, montrer)
                        log.write("\n".join(lignes) + "\n")
                        log.flush()
                    derniere, vignettes = nature, vignettes + (1 if montrer else 0)
                except (OSError, ValueError):
                    pass
            time.sleep(1)
    if os.path.exists(temporaire):
        os.remove(temporaire)


def lire_tableau(chemin):
    """[(seconde, code de nature, pixels clairs de l'indicateur, pixels qui ont changé)] d'un fichier .csv écrit par « surveiller »
    (les deux derniers manquent dans un fichier plus ancien)."""
    with open(chemin, encoding="utf-8") as fichier:
        lignes = fichier.read().splitlines()[1:]
    resultat = []
    for ligne in lignes:
        champs = ligne.split(";")
        if len(champs) < 6:
            continue
        resultat.append((int(champs[0]), champs[1]) + ((int(champs[6]), int(champs[7])) if len(champs) >= 8 else ()))
    return resultat


def derniere_serie(codes, code):
    """(début, fin exclue) de la dernière suite ininterrompue de `code`, ou None."""
    fin = None
    for i in range(len(codes) - 1, -1, -1):
        if codes[i] == code and fin is None:
            fin = i + 1
        if fin is not None and (codes[i] != code):
            return i + 1, fin
    return (0, fin) if fin is not None else None


def verifier(captures, exiger_connexion=True):
    """(erreurs, informations) : le démarrage ressemble-t-il à celui de Windows ?

    La surveillance commence avant l'arrêt : l'écran de démarrage de l'arrêt vient donc d'abord. Celui du démarrage est la dernière série
    de captures « écran de démarrage » ; avant elle (arrêt, micrologiciel, noyau) on tolère très peu de texte, après elle aucun."""
    erreurs, infos = [], []
    codes = [capture[1] for capture in captures]
    if not codes:
        return ["aucune capture d'écran pendant le démarrage"], infos
    serie = derniere_serie(codes, "DEMARRAGE")
    if serie is None:
        erreurs.append("l'écran de démarrage BinixX OS n'est jamais apparu")
        avant, apres = codes, []
    else:
        debut, fin = serie
        avant, apres = codes[:debut], codes[debut:]
        duree = fin - debut
        infos.append(f"écran de démarrage BinixX OS visible sur {duree} capture(s), à partir de la capture {debut + 1}")
        if duree < 3:
            erreurs.append(f"l'écran de démarrage n'est resté que {duree} capture(s)")
        texte_apres = apres.count("TEXTE") + apres.count("LIGNES")
        if texte_apres:
            erreurs.append(f"du texte de console est réapparu après l'écran de démarrage ({texte_apres} capture(s))")
        noir, plus_long = 0, 0
        for code in apres[duree:]:
            noir = noir + 1 if code == "NOIR" else 0
            plus_long = max(plus_long, noir)
        infos.append(f"écran noir le plus long après l'écran de démarrage : {plus_long} capture(s)")
        mesures_indicateur = [capture[2:] for capture in captures[debut:fin]]
        if mesures_indicateur and all(len(mesure) == 2 for mesure in mesures_indicateur):
            visibles = sum(1 for clairs, _ in mesures_indicateur if clairs >= INDICATEUR_MIN)
            comparees = [mouvement for _, mouvement in mesures_indicateur if mouvement >= 0]
            bougent = sum(1 for mouvement in comparees if mouvement >= MOUVEMENT_MIN)
            infos.append(f"indicateur de chargement : visible sur {visibles} capture(s) sur {duree}, en mouvement entre "
                         f"{bougent} paire(s) de captures sur {len(comparees)}")
            if duree >= 3 and visibles * 2 < duree:
                erreurs.append(f"l'écran de démarrage n'a pas d'indicateur de chargement visible (visible sur {visibles} capture(s) "
                               f"sur {duree}) : on peut croire que l'ordinateur est figé")
            elif len(comparees) >= 3 and bougent == 0:
                erreurs.append(f"l'indicateur de chargement ne bouge pas ({len(comparees)} paires de captures comparées) : "
                               f"on peut croire que l'ordinateur est figé")
    texte_avant = avant.count("TEXTE")
    lignes_avant = avant.count("LIGNES")
    infos.append(f"captures d'un écran de texte avant l'écran de démarrage : {texte_avant} (toléré : {TEXTE_TOLERE_AVANT})")
    infos.append(f"captures de quelques lignes de texte avant l'écran de démarrage : {lignes_avant} (toléré : {LIGNES_TOLEREES_AVANT})")
    if texte_avant > TEXTE_TOLERE_AVANT:
        erreurs.append(f"un écran de texte de console s'est affiché sur {texte_avant} captures avant l'écran de démarrage "
                       f"(toléré : {TEXTE_TOLERE_AVANT})")
    if lignes_avant > LIGNES_TOLEREES_AVANT:
        erreurs.append(f"quelques lignes de texte sont restées {lignes_avant} captures avant l'écran de démarrage "
                       f"(toléré : {LIGNES_TOLEREES_AVANT})")
    if exiger_connexion:
        derniere = codes[-1]
        infos.append(f"dernière capture : {derniere}")
        if derniere not in ("CLAIR", "SOMBRE"):
            erreurs.append(f"à la fin du démarrage l'écran n'est pas celui de la connexion ou du bureau ({derniere})")
    return erreurs, infos


def main(argv):
    if len(argv) >= 3 and argv[1] == "resume":
        with open(argv[2], "rb") as image:
            largeur, hauteur, pixels, mesures, nature = examiner(image.read())
        print("\n".join(decrire(largeur, hauteur, pixels, mesures, nature, avec_vignette=True)))
        return 0
    if len(argv) >= 5 and argv[1] == "surveiller":
        surveiller(argv[2], argv[3], argv[4], int(argv[5]) if len(argv) > 5 else 1800)
        return 0
    if len(argv) >= 3 and argv[1] == "verifier":
        erreurs, infos = verifier(lire_tableau(argv[2]), "--sans-connexion" not in argv)
        for info in infos:
            print(f"  info      {info}")
        for erreur in erreurs:
            print(f"  ÉCHEC     {erreur}")
        if not erreurs:
            print("  ok        le démarrage ressemble à celui de Windows : écran de démarrage, pas de texte, écran de connexion")
        return 1 if erreurs else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
