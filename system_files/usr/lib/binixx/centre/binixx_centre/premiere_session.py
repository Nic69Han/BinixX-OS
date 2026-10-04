"""Faut-il ouvrir l'accueil ? Pas dans la session de l'assistant de premier démarrage (Plasma Setup).

Plasma Setup ouvre, avant l'écran de connexion, une vraie session Plasma pour un utilisateur spécial, « plasma-setup », dont le dossier
personnel est /run/plasma-setup (créé à chaque démarrage). Tout ce qui est dans /etc/xdg/autostart s'y lance aussi : l'accueil de
BinixX OS s'ouvrait donc une première fois pendant la configuration, puis une seconde fois à la première ouverture de session du vrai
utilisateur (le repère « accueil déjà vu » de plasma-setup est dans /run, il disparaît au redémarrage, et n'est de toute façon pas celui
du vrai utilisateur). Aucune dépendance à Qt : testé seul (tests/image/centre/test_premiere_session.py)."""

import getpass
import os

UTILISATEUR_ASSISTANT = "plasma-setup"
DOSSIER_ASSISTANT = "/run/plasma-setup"


def session_de_l_assistant(utilisateur=None, maison=None):
    """True si la session en cours est celle de l'assistant de premier démarrage (par défaut : celle du processus)."""
    if utilisateur is None:
        try:
            utilisateur = getpass.getuser()
        except (KeyError, OSError):
            utilisateur = ""
    if maison is None:
        maison = os.path.expanduser("~")
    maison = os.path.normpath(maison)
    return (utilisateur == UTILISATEUR_ASSISTANT
            or maison == DOSSIER_ASSISTANT or maison.startswith(DOSSIER_ASSISTANT + os.sep))
