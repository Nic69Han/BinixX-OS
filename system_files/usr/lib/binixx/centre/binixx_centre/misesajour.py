"""Mises à jour du système : version installée, mise à jour prête, version précédente, nouvelle version disponible.

Aucune dépendance à Qt : testé seul (tests/image/centre/test_misesajour.py) ; l'outil en ligne de commande est
/usr/libexec/binixx/binixx-mises-a-jour.

- L'état se lit avec `rpm-ostree status --json` : ce programme répond à un utilisateur ordinaire, sans mot de passe.
- « Y a-t-il une nouvelle version ? » compare l'empreinte de l'image installée avec celle que le registre publie
  aujourd'hui pour la même étiquette (`skopeo inspect`, sans identifiant) ; la taille à télécharger est celle des
  couches de la nouvelle image que l'ancienne n'a pas.
- Installer une mise à jour (`bootc upgrade`) et revenir à la version précédente (`bootc rollback`) demandent
  l'administrateur : le Centre passe par `pkexec` (usr/share/polkit-1/actions/org.binixx.mises-a-jour.policy). Rien n'est
  installé sans que l'utilisateur le demande, et aucun shell n'est utilisé.
"""

import json
import os
import re
import sys
import time

from . import launch

STATUT = ["rpm-ostree", "status", "--json"]
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
        "décembre")
# Ce qui précède l'adresse de l'image dans la référence d'un déploiement :
# « ostree-image-signed:docker://ghcr.io/… », « ostree-unverified-registry:ghcr.io/… », « ostree-remote-registry:remote:… »
PREFIXES = re.compile(r"^(ostree-image-signed:|ostree-unverified-image:|ostree-unverified-registry:|"
                      r"ostree-remote-registry:[^:]+:|ostree-remote-image:[^:]+:)")
REGISTRE = re.compile(r"^[a-z0-9][a-z0-9.-]*(:[0-9]+)?/[a-z0-9][a-z0-9._/-]*(:[A-Za-z0-9._-]+)?(@sha256:[0-9a-f]{64})?$")
EMPREINTE = re.compile(r"^sha256:[0-9a-f]{64}$")
DELAI = 60
INSTALLER = ["bootc", "upgrade"]
RETOUR = ["bootc", "rollback"]
CANAUX = {
    "stable": "Stable : chaque version a passé un test complet avant d'arriver sur ce PC",
    "latest": "Stable : chaque version a passé un test complet avant d'arriver sur ce PC",
    "testing": "Test : versions pas encore validées, pour les testeurs",
}


def date_en_francais(horodatage):
    """« 3 octobre 2026 » d'après un horodatage Unix ; chaîne vide si on ne le connaît pas."""
    try:
        instant = time.localtime(int(horodatage))
    except (TypeError, ValueError, OverflowError, OSError):
        return ""
    return f"{instant.tm_mday}{'er' if instant.tm_mday == 1 else ''} {MOIS[instant.tm_mon - 1]} {instant.tm_year}"


def taille_lisible(octets):
    """« 480 Mo », « 1,2 Go » : les unités qu'on lit sur un PC français."""
    if octets is None:
        return ""
    for unite, facteur in (("Go", 1000 ** 3), ("Mo", 1000 ** 2), ("Ko", 1000)):
        if octets >= facteur:
            valeur = octets / facteur
            texte = f"{valeur:.0f}" if valeur >= 100 or unite == "Ko" else f"{valeur:.1f}".replace(".", ",")
            return f"{texte} {unite}"
    return f"{octets} octets"


def adresse_docker(reference):
    """`docker://ghcr.io/nic69han/binixx:stable` d'après la référence d'un déploiement ; None si ce n'est pas une image
    d'un registre (disque local, essai en cours de développement…)."""
    if not isinstance(reference, str):
        return None
    adresse = PREFIXES.sub("", reference.strip())
    adresse = adresse[len("docker://"):] if adresse.startswith("docker://") else adresse
    if not REGISTRE.match(adresse) or adresse.startswith("localhost/"):
        return None
    return "docker://" + adresse


def depot_de(adresse):
    """`ghcr.io/nic69han/binixx` d'après `docker://ghcr.io/nic69han/binixx:stable` (sans étiquette ni empreinte)."""
    debut, _, nom = adresse[len("docker://"):].rpartition("/")
    return (debut + "/" if debut else "") + nom.split(":", 1)[0].split("@", 1)[0]


def etiquette(reference):
    """L'étiquette suivie (« stable », « testing »…), ou None si l'image est figée sur une empreinte."""
    adresse = adresse_docker(reference)
    if adresse is None or "@" in adresse:
        return None
    nom = adresse.rsplit("/", 1)[-1]
    return nom.split(":", 1)[1] if ":" in nom else "latest"


def description_du_canal(reference):
    """Une phrase sur le canal suivi, d'après l'étiquette de l'image."""
    marque = etiquette(reference)
    if marque is None:
        return "Version figée sur une empreinte précise : elle ne se met pas à jour toute seule"
    return CANAUX.get(marque, f"Étiquette « {marque} »")


def _empreinte(deploiement):
    """L'empreinte de l'image d'un déploiement, d'où qu'elle vienne dans la réponse de rpm-ostree."""
    for cle, valeur in deploiement.items():
        if "digest" in cle and isinstance(valeur, str) and EMPREINTE.match(valeur):
            return valeur
    return None


def _version(deploiement):
    return {
        "version": str(deploiement.get("version") or ""),
        "date": date_en_francais(deploiement.get("timestamp")),
        "horodatage": deploiement.get("timestamp") if isinstance(deploiement.get("timestamp"), int) else None,
        "image": str(deploiement.get("container-image-reference") or deploiement.get("origin") or ""),
        "empreinte": _empreinte(deploiement),
    }


def lire_etat(sortie):
    """L'état d'après la réponse JSON de `rpm-ostree status --json`, ou None si on ne la comprend pas.

    {"installee": {version, date, image, empreinte}, "prete": {…} ou None, "precedente": {…} ou None}
    L'ordre des déploiements est celui de rpm-ostree : la version préparée d'abord, puis celle qui tourne, puis la
    précédente."""
    try:
        deploiements = json.loads(sortie).get("deployments")
    except (ValueError, AttributeError):
        return None
    if not isinstance(deploiements, list) or not deploiements:
        return None
    deploiements = [d for d in deploiements if isinstance(d, dict)]
    demarre = next((i for i, d in enumerate(deploiements) if d.get("booted")), None)
    if demarre is None:
        return None
    prete = next((d for d in deploiements[:demarre] if d.get("staged")), None)
    precedente = next((d for d in deploiements[demarre + 1:] if not d.get("staged")), None)
    return {
        "installee": _version(deploiements[demarre]),
        "prete": _version(prete) if prete else None,
        "precedente": _version(precedente) if precedente else None,
    }


def etat(run=launch.run):
    """L'état du système (voir lire_etat) ; None si rpm-ostree ne répond pas (pas un système bootc, essai en conteneur)."""
    code, sortie = run(STATUT, timeout=DELAI)
    return lire_etat(sortie) if code == 0 else None


def _inspecter(adresse, run):
    code, sortie = run(["skopeo", "inspect", "--no-tags", "--retry-times", "1", adresse], timeout=DELAI)
    if code != 0:
        return None
    try:
        donnees = json.loads(sortie)
    except ValueError:
        return None
    return donnees if isinstance(donnees, dict) else None


def _couches(donnees):
    """{empreinte de couche : taille} d'une réponse de `skopeo inspect`."""
    couches = {}
    for couche in donnees.get("LayersData") or []:
        if isinstance(couche, dict) and isinstance(couche.get("Digest"), str) and isinstance(couche.get("Size"), int):
            couches[couche["Digest"]] = couche["Size"]
    return couches


def verifier(installee, run=launch.run):
    """Une nouvelle version est-elle publiée pour l'image installée ?

    {"disponible": True | False | None, "taille": octets ou None, "raison": texte si on ne sait pas}
    None = on ne sait pas : pas de réseau, image qui ne vient pas d'un registre, empreinte inconnue."""
    adresse = adresse_docker(installee.get("image"))
    if adresse is None:
        return {"disponible": None, "taille": None, "raison": "Cette version ne vient pas d'un registre en ligne."}
    if "@" in adresse:
        return {"disponible": None, "taille": None, "raison": "Cette version est figée sur une empreinte précise."}
    if not installee.get("empreinte"):
        return {"disponible": None, "taille": None, "raison": "L'empreinte de la version installée est inconnue."}
    publiee = _inspecter(adresse, run)
    if publiee is None or not EMPREINTE.match(str(publiee.get("Digest") or "")):
        return {"disponible": None, "taille": None,
                "raison": "Le serveur de mises à jour ne répond pas : vérifiez la connexion à Internet."}
    if publiee["Digest"] == installee["empreinte"]:
        return {"disponible": False, "taille": 0, "raison": ""}
    taille = None
    ancienne = _inspecter(f"docker://{depot_de(adresse)}@{installee['empreinte']}", run)
    nouvelles, anciennes = _couches(publiee), _couches(ancienne or {})
    if nouvelles and anciennes:
        taille = sum(octets for empreinte, octets in nouvelles.items() if empreinte not in anciennes)
    return {"disponible": True, "taille": taille, "raison": ""}


def reponse(run=launch.run, avec_verification=False):
    """Tout ce que la page affiche, en un dictionnaire (et en JSON pour `binixx-mises-a-jour etat --json`)."""
    courant = etat(run)
    if courant is None:
        return None
    courant["canal"] = description_du_canal(courant["installee"]["image"])
    courant["etiquette"] = etiquette(courant["installee"]["image"])
    if avec_verification:
        courant["verification"] = verifier(courant["installee"], run)
    return courant


def texte(courant):
    """L'état en quelques lignes lisibles (pour le support : `binixx-mises-a-jour etat`)."""
    lignes = []
    installee = courant["installee"]
    lignes.append(f"Version installée : {installee['version'] or 'inconnue'}"
                  + (f" ({installee['date']})" if installee["date"] else ""))
    lignes.append(f"Image : {installee['image'] or 'inconnue'}")
    lignes.append(f"Canal : {courant['canal']}")
    prete = courant["prete"]
    lignes.append("Mise à jour prête : " + (f"oui, version {prete['version']} (redémarrer pour l'appliquer)" if prete
                                           else "non"))
    precedente = courant["precedente"]
    lignes.append("Version précédente : " + (f"{precedente['version'] or 'inconnue'}"
                                             + (f" ({precedente['date']})" if precedente["date"] else "")
                                             if precedente else "aucune"))
    verification = courant.get("verification")
    if verification is not None:
        if verification["disponible"] is None:
            lignes.append(f"Nouvelle version : inconnue. {verification['raison']}")
        elif verification["disponible"]:
            lignes.append("Nouvelle version : disponible"
                          + (f", environ {taille_lisible(verification['taille'])} à télécharger"
                             if verification["taille"] else ""))
        else:
            lignes.append("Nouvelle version : aucune, le PC est à jour")
    return "\n".join(lignes)


def installer(run=launch.run):
    """(administrateur) Télécharge la nouvelle version et la prépare pour le prochain redémarrage."""
    return run(INSTALLER, timeout=3600)


def revenir(run=launch.run):
    """(administrateur) Remet la version précédente au prochain redémarrage."""
    return run(RETOUR, timeout=300)


def main(argv=None, run=launch.run, sortie=print):
    """binixx-mises-a-jour etat | verifier [--json] ; installer | retour (administrateur, via pkexec)."""
    import argparse

    parser = argparse.ArgumentParser(prog="binixx-mises-a-jour", description="Mises à jour de BinixX OS.")
    parser.add_argument("action", choices=("etat", "verifier", "installer", "retour"),
                        help="etat : version installée, mise à jour prête, version précédente ; verifier : y a-t-il "
                             "une nouvelle version ? ; installer et retour : réservés à l'administrateur")
    parser.add_argument("--json", action="store_true", help="réponse lisible par un programme")
    args = parser.parse_args(argv)
    if args.action in ("installer", "retour"):
        if os.geteuid() != 0:
            sortie("Cette action est réservée à l'administrateur : le Centre la demande avec pkexec.")
            return 3
        code, texte_sortie = (installer if args.action == "installer" else revenir)(run)
        if texte_sortie:
            sortie(texte_sortie.rstrip())
        return code
    courant = reponse(run, avec_verification=args.action == "verifier")
    if courant is None:
        sortie("Impossible de lire l'état du système : ce PC n'est pas démarré depuis une image BinixX OS.")
        return 1
    sortie(json.dumps(courant, ensure_ascii=False, indent=2) if args.json else texte(courant))
    return 0


if __name__ == "__main__":
    sys.exit(main())
