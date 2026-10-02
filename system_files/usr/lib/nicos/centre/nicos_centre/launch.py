"""Lancement d'actions : jamais de shell, jamais de texte venant de l'utilisateur dans une commande."""

import os
import subprocess

APPLICATIONS = "/usr/share/applications"


def _start(argv):
    """Lance un programme sans attendre ; False s'il est introuvable."""
    try:
        subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except OSError:
        return False


def open_app(desktop_id):
    """Ouvre une application d'après son lanceur (« nicos-onedrive » ou « org.kde.dolphin »)."""
    path = os.path.join(APPLICATIONS, desktop_id + ".desktop")
    return _start(["kioclient", "exec", path])


def open_settings(module=""):
    """Ouvre la Configuration du système, éventuellement sur un module (« kcm_lookandfeel »)."""
    return _start(["systemsettings", module] if module else ["systemsettings"])


def open_discover(appstream_id=""):
    """Ouvre Discover, sur la page d'une application (identifiant AppStream) si on la connaît."""
    return _start(["plasma-discover", "--application", appstream_id] if appstream_id else ["plasma-discover"])


def open_url(url):
    """Ouvre une adresse web dans le navigateur par défaut (http et https seulement)."""
    if not url.startswith(("https://", "http://")):
        return False
    return _start(["xdg-open", url])
