#!/usr/bin/env python3
"""Télécharge une image d'un registre quay.io au format « OCI image layout », avec reprise.

Un téléchargement interrompu (connexion coupée par le CDN) reprend à l'octet où il s'est arrêté, au lieu
de tout recommencer ; chaque couche est vérifiée par son empreinte SHA-256.

Usage : fetch-oci.py quay.io/organisation/image:étiquette dossier-de-sortie
"""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MANIFEST_TYPES = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])
INDEX_TYPES = ("application/vnd.oci.image.index.v1+json", "application/vnd.docker.distribution.manifest.list.v2+json")
MAX_ATTEMPTS = 80


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Renvoie la redirection au lieu de la suivre : l'adresse du CDN se demande sans nos identifiants."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def request(url, headers=None, timeout=60):
    return OPENER.open(urllib.request.Request(url, headers=headers or {}), timeout=timeout)


def json_get(url, headers):
    with request(url, headers) as reponse:
        return json.loads(reponse.read()), reponse.headers.get("Content-Type", "").split(";")[0]


def parse(reference):
    registre, _, reste = reference.partition("/")
    if registre != "quay.io":
        sys.exit(f"seul quay.io est géré par ce téléchargement de secours, pas {registre}")
    depot, _, etiquette = reste.partition(":")
    return registre, depot, etiquette or "latest"


def token(registre, depot):
    adresse = f"https://{registre}/v2/auth?" + urllib.parse.urlencode({"service": registre, "scope": f"repository:{depot}:pull"})
    return json.loads(request(adresse).read())["token"]


def manifeste(registre, depot, reference, auth):
    """(octets, type) du manifeste d'une plateforme amd64 ; descend d'un index si besoin."""
    adresse = f"https://{registre}/v2/{depot}/manifests/{reference}"
    with request(adresse, {"Authorization": f"Bearer {auth}", "Accept": MANIFEST_TYPES}) as reponse:
        octets = reponse.read()
        type_ = reponse.headers.get("Content-Type", "").split(";")[0]
    contenu = json.loads(octets)
    type_ = contenu.get("mediaType", type_)
    if type_ in INDEX_TYPES:
        for entree in contenu["manifests"]:
            plateforme = entree.get("platform", {})
            if plateforme.get("architecture") == "amd64" and plateforme.get("os") == "linux":
                return manifeste(registre, depot, entree["digest"], auth)
        sys.exit("pas de manifeste linux/amd64")
    return octets, type_


def adresse_du_blob(registre, depot, empreinte, auth):
    """Adresse signée du CDN (valable quelques minutes), obtenue par la redirection du registre."""
    try:
        request(f"https://{registre}/v2/{depot}/blobs/{empreinte}", {"Authorization": f"Bearer {auth}"}).close()
    except urllib.error.HTTPError as erreur:
        if erreur.code in (301, 302, 303, 307, 308):
            return erreur.headers["Location"]
        raise
    return f"https://{registre}/v2/{depot}/blobs/{empreinte}"


def sha256_fichier(chemin):
    resume = hashlib.sha256()
    with open(chemin, "rb") as fichier:
        for bloc in iter(lambda: fichier.read(1 << 20), b""):
            resume.update(bloc)
    return resume.hexdigest()


def telecharger(registre, depot, auth, empreinte, taille, destination):
    attendu = empreinte.split(":", 1)[1]
    essais = 0
    while True:
        deja = os.path.getsize(destination) if os.path.exists(destination) else 0
        if deja == taille:
            if sha256_fichier(destination) == attendu:
                return
            print(f"  empreinte incorrecte pour {empreinte[:19]}, on recommence", flush=True)
            os.remove(destination)
            deja = 0
        essais += 1
        if essais > MAX_ATTEMPTS:
            sys.exit(f"abandon : {empreinte} n'a pas pu être téléchargée en {MAX_ATTEMPTS} essais")
        try:
            adresse = adresse_du_blob(registre, depot, empreinte, auth)
            entetes = {"Range": f"bytes={deja}-"} if deja else {}
            with request(adresse, entetes) as reponse:
                if deja and reponse.status != 206:  # le serveur ignore la reprise : on repart de zéro
                    deja = 0
                with open(destination, "ab" if deja else "wb") as sortie:
                    while True:
                        bloc = reponse.read(1 << 20)
                        if not bloc:
                            break
                        sortie.write(bloc)
        except Exception as erreur:  # coupure, délai dépassé, erreur du CDN : on reprend
            reste = taille - (os.path.getsize(destination) if os.path.exists(destination) else 0)
            print(f"  {empreinte[:19]} : {type(erreur).__name__} ({erreur}), reste {reste} octets, essai {essais}", flush=True)
            time.sleep(min(2 * essais, 20))


def main(reference, dossier):
    registre, depot, etiquette = parse(reference)
    auth = token(registre, depot)
    octets, type_ = manifeste(registre, depot, etiquette, auth)
    contenu = json.loads(octets)
    blobs_dir = os.path.join(dossier, "blobs", "sha256")
    os.makedirs(blobs_dir, exist_ok=True)

    empreinte_manifeste = hashlib.sha256(octets).hexdigest()
    with open(os.path.join(blobs_dir, empreinte_manifeste), "wb") as fichier:
        fichier.write(octets)
    for couche in [contenu["config"], *contenu["layers"]]:
        hexa = couche["digest"].split(":", 1)[1]
        print(f"{couche['digest'][:19]}… {couche['size'] / 1e6:.1f} Mo", flush=True)
        telecharger(registre, depot, auth, couche["digest"], couche["size"], os.path.join(blobs_dir, hexa))

    with open(os.path.join(dossier, "oci-layout"), "w", encoding="utf-8") as fichier:
        json.dump({"imageLayoutVersion": "1.0.0"}, fichier)
    index = {"schemaVersion": 2, "manifests": [{
        "mediaType": type_, "digest": f"sha256:{empreinte_manifeste}", "size": len(octets),
        "annotations": {"org.opencontainers.image.ref.name": "latest"},
    }]}
    with open(os.path.join(dossier, "index.json"), "w", encoding="utf-8") as fichier:
        json.dump(index, fichier)
    print("image OCI prête dans", dossier, flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
