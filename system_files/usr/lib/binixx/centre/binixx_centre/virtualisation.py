"""Ce PC peut-il faire tourner Windows dans une machine virtuelle ? Aucune dépendance à Qt : testé seul
(tests/image/centre/test_windows.py). Chaque vérification renvoie un état « ok », « attention » ou « ko »."""

import math
import os
import re
import shutil
from dataclasses import dataclass

OK, ATTENTION, KO = "ok", "attention", "ko"

# Seuils sur la mémoire que voit le système : un PC « 8 Go » en voit 7,5 ou moins (une partie sert la carte
# graphique et le micrologiciel), un PC « 4 Go » environ 3,7.
MEMOIRE_CONFORTABLE_GO = 7
MEMOIRE_MINIMALE_GO = 3.5
ESPACE_CONFORTABLE_GO = 64
ESPACE_MINIMAL_GO = 32
FILS_CONFORTABLES = 4
FILS_MINIMAUX = 2


@dataclass(frozen=True)
class Verification:
    cle: str
    etat: str
    titre: str
    detail: str


def _lire(chemin):
    try:
        with open(chemin, encoding="utf-8", errors="replace") as fichier:
            return fichier.read()
    except OSError:
        return ""


def processeur_sait_virtualiser(cpuinfo):
    """Le processeur annonce VT-x (vmx) ou AMD-V (svm)."""
    return any(re.search(r"\b(vmx|svm)\b", ligne) for ligne in cpuinfo.splitlines() if ligne.startswith("flags"))


def nombre_de_fils(cpuinfo):
    return sum(1 for ligne in cpuinfo.splitlines() if re.match(r"processor\s*:", ligne))


def memoire_go(meminfo):
    trouve = re.search(r"^MemTotal:\s+(\d+)\s+kB", meminfo, re.MULTILINE)
    return int(trouve.group(1)) / (1024 * 1024) if trouve else 0.0


def virtualisation(cpuinfo, kvm_utilisable):
    """/dev/kvm utilisable = la virtualisation matérielle est activée et accessible."""
    if kvm_utilisable:
        return Verification("virtualisation", OK, "Virtualisation matérielle activée",
                            "Le PC peut faire tourner une machine virtuelle à pleine vitesse.")
    if processeur_sait_virtualiser(cpuinfo):
        return Verification("virtualisation", KO, "Virtualisation matérielle désactivée",
                            "Le processeur sait le faire, mais l'option est coupée dans le BIOS/UEFI : cherchez "
                            "« Intel Virtualization Technology », « VT-x », « AMD-V » ou « SVM Mode » et activez-la.")
    return Verification("virtualisation", KO, "Virtualisation matérielle non détectée",
                        "Ce processeur ne l'annonce pas, ou elle est coupée dans le BIOS/UEFI. Sans elle, Windows "
                        "serait beaucoup trop lent.")


def memoire(go):
    annonce = f"{math.ceil(go - 0.01)} Go"  # 15,3 Go vus par le système = le « 16 Go » de la boîte
    if go >= MEMOIRE_CONFORTABLE_GO:
        return Verification("memoire", OK, f"Mémoire : {annonce}", "Assez pour BinixX OS et Windows en même temps.")
    if go >= MEMOIRE_MINIMALE_GO:
        return Verification("memoire", ATTENTION, f"Mémoire : {annonce}",
                            "Juste : Windows prendra la moitié de la mémoire. Fermez les autres applications.")
    return Verification("memoire", KO, f"Mémoire : {annonce}",
                        "Trop peu pour faire tourner Windows en plus de BinixX OS : 8 Go sont conseillés.")


def espace(go):
    arrondi = f"{go:.0f} Go"
    if go >= ESPACE_CONFORTABLE_GO:
        return Verification("espace", OK, f"Espace libre : {arrondi}", "Assez pour Windows et quelques logiciels.")
    if go >= ESPACE_MINIMAL_GO:
        return Verification("espace", ATTENTION, f"Espace libre : {arrondi}",
                            "Juste : Windows seul occupe une trentaine de Go. Libérez de la place si possible.")
    return Verification("espace", KO, f"Espace libre : {arrondi}",
                        "Pas assez de place : prévoyez au moins 64 Go libres.")


def fils(nombre):
    if nombre >= FILS_CONFORTABLES:
        return Verification("fils", OK, f"Processeur : {nombre} fils d'exécution", "Assez pour deux systèmes à la fois.")
    if nombre >= FILS_MINIMAUX:
        return Verification("fils", ATTENTION, f"Processeur : {nombre} fils d'exécution",
                            "Juste : Windows sera lent si BinixX OS travaille en même temps.")
    return Verification("fils", KO, "Processeur trop modeste", "Il faut au moins 2 fils d'exécution (4 conseillés).")


def kvm_accessible(chemin="/dev/kvm"):
    return os.access(chemin, os.R_OK | os.W_OK)


def verifier(cpuinfo=None, meminfo=None, kvm=None, libre_go=None, dossier=None):
    """Les quatre vérifications, avec les valeurs du PC sauf celles qu'on passe (tests)."""
    cpuinfo = _lire("/proc/cpuinfo") if cpuinfo is None else cpuinfo
    meminfo = _lire("/proc/meminfo") if meminfo is None else meminfo
    kvm = kvm_accessible() if kvm is None else kvm
    if libre_go is None:
        try:
            libre_go = shutil.disk_usage(dossier or os.path.expanduser("~")).free / 1024 ** 3
        except OSError:
            libre_go = 0.0
    return [virtualisation(cpuinfo, kvm), memoire(memoire_go(meminfo)), espace(libre_go), fils(nombre_de_fils(cpuinfo))]


def outils_winboat(chercher=shutil.which):
    """Ce dont WinBoat a besoin côté BinixX OS : (nom, présent). FreeRDP 3 s'appelle xfreerdp3 ou xfreerdp."""
    return [("Podman", bool(chercher("podman"))),
            ("Podman Compose", bool(chercher("podman-compose"))),
            ("FreeRDP", bool(chercher("xfreerdp3") or chercher("xfreerdp")))]
