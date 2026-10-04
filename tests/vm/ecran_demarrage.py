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
texte de console n'est visible une fois qu'il est là (et presque aucun avant), l'écran de connexion finit par s'afficher."""

import json
import os
import socket
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
AUTRE = "autre"


CODES = {NOIR: "NOIR", TEXTE: "TEXTE", DEMARRAGE: "DEMARRAGE", CLAIR: "CLAIR", SOMBRE: "SOMBRE", AUTRE: "AUTRE"}
# Captures de texte tolérées avant l'écran de démarrage : le micrologiciel (UEFI) et le menu GRUB, une seconde chacun
TEXTE_TOLERE_AVANT = 3


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
    total = noirs = fonds = clairs = somme = 0
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
    total = max(total, 1)
    return {"noir": noirs / total, "fond": fonds / total, "clair": clairs / total, "luminance": somme / total}


def classer(mesures):
    """Ce que montre l'écran : de quoi distinguer, sans le voir, la console de texte de l'écran de démarrage."""
    if mesures["noir"] >= 0.995:
        return NOIR
    if mesures["fond"] >= 0.5:
        return DEMARRAGE
    if mesures["noir"] >= 0.7 and mesures["clair"] > 0:
        return TEXTE
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


def examiner(donnees_ppm):
    """(largeur, hauteur, octets, mesures, nature) d'une capture."""
    largeur, hauteur, pixels = lire_ppm(donnees_ppm)
    mesures = analyser(largeur, hauteur, pixels)
    return largeur, hauteur, pixels, mesures, classer(mesures)


def decrire(largeur, hauteur, pixels, mesures, nature, seconde=None, avec_vignette=False):
    """Les lignes de journal d'une capture : un résumé, et la vignette si demandée."""
    quand = "" if seconde is None else f"t={seconde:>3} s  "
    lignes = [f"{quand}{largeur}x{hauteur}  {nature}  (noir {mesures['noir']:.0%}, fond bleu nuit {mesures['fond']:.0%}, "
              f"pixels clairs {mesures['clair']:.1%}, luminance {mesures['luminance']:.0f})"]
    if avec_vignette:
        lignes += ["    |" + ligne for ligne in vignette(largeur, hauteur, pixels)]
    return lignes


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
    derniere, vignettes = None, 0
    temporaire = os.path.join(tempfile.gettempdir(), f"ecran-demarrage-{os.getpid()}.ppm")
    with open(fichier_log, "w", encoding="utf-8") as log, open(fichier_log + ".csv", "w", encoding="utf-8") as tableau:
        tableau.write("seconde;nature;noir;fond;clair;luminance\n")
        while not os.path.exists(fichier_arret) and time.monotonic() - debut < duree_max:
            if capture_qmp(socket_qmp, temporaire):
                try:
                    with open(temporaire, "rb") as image:
                        donnees = image.read()
                    seconde = int(time.monotonic() - debut)
                    largeur, hauteur, pixels, mesures, nature = examiner(donnees)
                    tableau.write(f"{seconde};{CODES[nature]};{mesures['noir']:.3f};{mesures['fond']:.3f};"
                                  f"{mesures['clair']:.3f};{mesures['luminance']:.0f}\n")
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
    """[(seconde, code de nature)] d'un fichier .csv écrit par « surveiller »."""
    with open(chemin, encoding="utf-8") as fichier:
        lignes = fichier.read().splitlines()[1:]
    return [(int(ligne.split(";")[0]), ligne.split(";")[1]) for ligne in lignes if ligne.count(";") >= 5]


def verifier(captures, exiger_connexion=True):
    """(erreurs, informations) : le démarrage ressemble-t-il à celui de Windows ?"""
    erreurs, infos = [], []
    codes = [code for _, code in captures]
    if not codes:
        return ["aucune capture d'écran pendant le démarrage"], infos
    if "DEMARRAGE" not in codes:
        erreurs.append("l'écran de démarrage BinixX OS n'est jamais apparu")
        avant, apres = codes, []
    else:
        premiere = codes.index("DEMARRAGE")
        avant, apres = codes[:premiere], codes[premiere:]
        duree = apres.count("DEMARRAGE")
        infos.append(f"écran de démarrage BinixX OS visible sur {duree} capture(s), à partir de la capture {premiere + 1}")
        if duree < 3:
            erreurs.append(f"l'écran de démarrage n'est resté que {duree} capture(s)")
        texte_apres = apres.count("TEXTE")
        if texte_apres:
            erreurs.append(f"du texte de console est réapparu après le début de l'écran de démarrage ({texte_apres} capture(s))")
        noir, plus_long = 0, 0
        for code in apres[apres.index("DEMARRAGE"):]:
            noir = noir + 1 if code == "NOIR" else 0
            plus_long = max(plus_long, noir)
        infos.append(f"écran noir le plus long après l'écran de démarrage : {plus_long} capture(s)")
    texte_avant = avant.count("TEXTE")
    infos.append(f"captures de texte avant l'écran de démarrage : {texte_avant} (toléré : {TEXTE_TOLERE_AVANT}, micrologiciel et menu GRUB)")
    if texte_avant > TEXTE_TOLERE_AVANT:
        erreurs.append(f"du texte de console s'est affiché sur {texte_avant} captures avant l'écran de démarrage "
                       f"(toléré : {TEXTE_TOLERE_AVANT})")
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
