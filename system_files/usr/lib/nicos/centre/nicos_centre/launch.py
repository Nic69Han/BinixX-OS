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


def open_webapp(url):
    """Ouvre une adresse dans une fenêtre d'application (comme les web apps de NicOS)."""
    return _start(["/usr/libexec/nicos/nicos-webapp", url])


def run(argv, timeout=120):
    """Exécute un programme de NicOS et renvoie (code de sortie, sortie standard) ; jamais de shell."""
    try:
        fini = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as erreur:
        return 1, str(erreur)
    return fini.returncode, fini.stdout


def run_input(argv, texte, timeout=300):
    """Exécute un programme en lui donnant `texte` sur l'entrée standard ; renvoie (code, sortie, erreurs).

    Pour les actions privilégiées (pkexec) : un mot de passe ne passe jamais par la ligne de commande."""
    try:
        fini = subprocess.run(argv, input=texte, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as erreur:
        return 1, "", str(erreur)
    return fini.returncode, fini.stdout, fini.stderr


def logout_prompt():
    """Propose de fermer la session (boîte de dialogue de Plasma)."""
    return _start(["busctl", "--user", "call", "org.kde.LogoutPrompt", "/LogoutPrompt", "org.kde.LogoutPrompt",
                   "promptLogout"])

def run_flatpak(app_id):
    """Lance une application Flatpak installée."""
    return _start(["flatpak", "run", app_id])


def installed_flatpaks():
    """Identifiants des applications Flatpak installées (ensemble vide si flatpak ne répond pas)."""
    try:
        sortie = subprocess.run(["flatpak", "list", "--app", "--columns=application"], capture_output=True,
                                text=True, timeout=10, check=False).stdout
    except (OSError, subprocess.TimeoutExpired):
        return set()
    return {ligne.strip() for ligne in sortie.splitlines() if ligne.strip()}
