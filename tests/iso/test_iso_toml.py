"""Garde-fou sur la configuration de l'installeur (disk_config/iso.toml).

Anaconda n'est pas prévu pour tourner sans certains de ses modules : valider la langue sur l'écran « Bienvenue » appelle le
module Timezone sans vérifier qu'il existe (« AttributeError: 'NoneType' object has no attribute 'SetTimezoneWithPriority' »,
l'installeur plante), et l'écran « Date et heure » interroge le module Network. Ces deux modules restent donc actifs ; la VM
et le test d'ISO (tests/iso/boot-installer.sh, qui clique sur « Continuer ») le vérifient pour de bon."""

import os
import tomllib
import unittest

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
PREFIXE = "org.fedoraproject.Anaconda.Modules."


def modules():
    with open(os.path.join(RACINE, "disk_config", "iso.toml"), "rb") as fichier:
        config = tomllib.load(fichier)["customizations"]["installer"]["modules"]
    return {m.removeprefix(PREFIXE) for m in config["enable"]}, {m.removeprefix(PREFIXE) for m in config["disable"]}


class ModulesDeLInstalleurTest(unittest.TestCase):
    def test_les_modules_dont_anaconda_a_besoin_restent_actifs(self):
        actifs, inactifs = modules()
        for module in ("Localization", "Storage", "Runtime", "Timezone", "Network"):
            self.assertIn(module, actifs, f"{module} doit être activé")
            self.assertNotIn(module, inactifs, f"{module} ne doit pas être désactivé (l'installeur planterait)")

    def test_le_fuseau_horaire_n_est_jamais_desactive(self):
        _, inactifs = modules()
        self.assertNotIn("Timezone", inactifs)

    def test_un_module_n_est_pas_a_la_fois_actif_et_inactif(self):
        actifs, inactifs = modules()
        self.assertEqual(actifs & inactifs, set())

    def test_le_compte_est_cree_au_premier_demarrage(self):
        # Activer Users ferait créer le compte deux fois (installeur, puis Plasma Setup)
        _, inactifs = modules()
        self.assertIn("Users", inactifs)

    def test_noms_de_modules_connus(self):
        connus = {"Localization", "Storage", "Runtime", "Timezone", "Network", "Security", "Services", "Users", "Subscription",
                  "Payloads", "Boss"}
        actifs, inactifs = modules()
        self.assertLessEqual(actifs | inactifs, connus)


if __name__ == "__main__":
    unittest.main()
