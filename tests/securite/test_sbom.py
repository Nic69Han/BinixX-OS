"""Tests de securite/sbom.py : lecture de `rpm -qa`, identifiants purl, licences, document CycloneDX."""

import datetime
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ICI = os.path.dirname(__file__)
OUTIL = os.path.join(ICI, "../../securite/sbom.py")


def charger():
    chargeur = importlib.machinery.SourceFileLoader("sbom", OUTIL)
    spec = importlib.util.spec_from_loader("sbom", chargeur)
    module = importlib.util.module_from_spec(spec)
    chargeur.exec_module(module)
    return module


S = charger()
OS_RELEASE = 'NAME="Fedora Linux"\nVERSION_ID=44\nID=fedora\nPRETTY_NAME="Fedora Linux 44 (Kinoite)"\n# commentaire\n'
LIGNES = [
    "bash\t0\t5.3.0\t2.fc44\tx86_64\tGPL-3.0-or-later\tbash-5.3.0-2.fc44.src.rpm\tFedora Project\n",
    "gpg-pubkey\t0\tabcd1234\t5f3e1b2c\t(none)\tpubkey\t(none)\t(none)\n",
    "perl-libs\t4\t5.42.0\t512.fc44\tx86_64\t(GPL-1.0-or-later OR Artistic-1.0-Perl) AND MIT\t(none)\t(none)\n",
    "vieux-paquet\t(none)\t1.0\t1.fc44\tnoarch\tGPLv2+ and MIT\t\t\n",
    "\n",
]


class Lecture(unittest.TestCase):
    def test_os_release(self):
        distro = S.lire_os_release(OS_RELEASE)
        self.assertEqual((distro["ID"], distro["VERSION_ID"]), ("fedora", "44"))
        self.assertEqual(distro["PRETTY_NAME"], "Fedora Linux 44 (Kinoite)")
        self.assertNotIn("# commentaire", distro)

    def test_paquets(self):
        paquets = S.lire_paquets(LIGNES)
        self.assertEqual([p["nom"] for p in paquets], ["bash", "perl-libs", "vieux-paquet"])  # gpg-pubkey ignoré
        self.assertEqual(paquets[1]["epoque"], "4")
        self.assertEqual(paquets[2]["epoque"], "0")  # « (none) » -> 0

    def test_ligne_mal_formee(self):
        with self.assertRaises(ValueError) as erreur:
            S.lire_paquets(["bash\t0\t5.3\n"])
        self.assertIn("ligne 1", str(erreur.exception))


class Spdx(unittest.TestCase):
    def test_expressions_valides(self):
        for texte in ("MIT", "GPL-2.0-or-later", "GPL-2.0-or-later AND MIT", "(MIT OR Apache-2.0) AND BSD-3-Clause",
                      "GPL-2.0-only WITH Classpath-exception-2.0", "LGPL-2.1-or-later AND (GPL-3.0+ OR MIT)",
                      "((MIT))"):
            self.assertTrue(S.est_spdx(texte), texte)

    def test_expressions_invalides(self):
        for texte in ("", "GPLv2+ and MIT", "MIT AND", "AND MIT", "(MIT", "MIT)", "MIT OR OR GPL-2.0-only", "GPL v2", "MIT, BSD",
                      "WITH MIT", "MIT WITH"):
            self.assertFalse(S.est_spdx(texte), texte)


class Composants(unittest.TestCase):
    distro = {"ID": "fedora", "VERSION_ID": "44"}

    def test_purl_sans_epoque(self):
        p = S.lire_paquets(LIGNES)[0]
        self.assertEqual(S.purl(p, self.distro), "pkg:rpm/fedora/bash@5.3.0-2.fc44?arch=x86_64&distro=fedora-44")

    def test_purl_avec_epoque(self):
        p = S.lire_paquets(LIGNES)[1]
        self.assertEqual(S.purl(p, self.distro),
                         "pkg:rpm/fedora/perl-libs@5.42.0-512.fc44?arch=x86_64&distro=fedora-44&epoch=4")

    def test_licence_spdx_est_une_expression(self):
        element = S.composant(S.lire_paquets(LIGNES)[1], self.distro)
        self.assertEqual(element["licenses"], [{"expression": "(GPL-1.0-or-later OR Artistic-1.0-Perl) AND MIT"}])

    def test_licence_ancienne_reste_un_nom(self):
        element = S.composant(S.lire_paquets(LIGNES)[2], self.distro)
        self.assertEqual(element["licenses"], [{"license": {"name": "GPLv2+ and MIT"}}])
        self.assertNotIn("supplier", element)
        self.assertNotIn("properties", element)

    def test_editeur_et_source(self):
        element = S.composant(S.lire_paquets(LIGNES)[0], self.distro)
        self.assertEqual(element["supplier"], {"name": "Fedora Project"})
        self.assertEqual(element["properties"], [{"name": "rpm:sourcerpm", "value": "bash-5.3.0-2.fc44.src.rpm"}])


class Document(unittest.TestCase):
    distro = {"ID": "fedora", "VERSION_ID": "44", "PRETTY_NAME": "Fedora Linux 44 (Kinoite)"}

    def fabriquer(self, lignes=LIGNES):
        return S.fabriquer(S.lire_paquets(lignes), "binixx", "testing", self.distro,
                           maintenant=datetime.datetime(2026, 10, 2, 12, 0, tzinfo=datetime.timezone.utc),
                           numero="00000000-0000-0000-0000-000000000001")

    def test_structure_cyclonedx(self):
        d = self.fabriquer()
        self.assertEqual((d["bomFormat"], d["specVersion"], d["version"]), ("CycloneDX", "1.6", 1))
        self.assertEqual(d["serialNumber"], "urn:uuid:00000000-0000-0000-0000-000000000001")
        self.assertEqual(d["metadata"]["timestamp"], "2026-10-02T12:00:00Z")
        self.assertEqual(d["metadata"]["component"]["type"], "container")
        self.assertEqual(d["metadata"]["component"]["purl"], "pkg:oci/binixx?tag=testing")
        self.assertEqual(len(d["components"]), 3)

    def test_ordre_stable_et_references_uniques(self):
        d = self.fabriquer()
        refs = [c["bom-ref"] for c in d["components"]]
        self.assertEqual(refs, sorted(refs))
        self.assertEqual(len(set(refs)), len(refs))
        self.assertEqual(json.dumps(d, sort_keys=True), json.dumps(self.fabriquer(list(reversed(LIGNES))), sort_keys=True))

    def test_resume(self):
        texte = S.resume(self.fabriquer())
        self.assertIn("3 paquets, 3 licences distinctes, 0 sans licence", texte)


class LigneDeCommande(unittest.TestCase):
    def lancer(self, entree, *args):
        return subprocess.run([sys.executable, OUTIL, *args], input=entree, capture_output=True, text=True, check=False)

    def fichier_os_release(self):
        fichier = tempfile.NamedTemporaryFile("w", suffix="-os-release", delete=False)
        self.addCleanup(os.unlink, fichier.name)
        fichier.write(OS_RELEASE)
        fichier.close()
        return fichier.name

    def test_format_rpm_est_celui_que_lit_l_outil(self):
        sortie = self.lancer("", "--format-rpm").stdout
        self.assertEqual(sortie.count("\\t"), 7)
        self.assertTrue(sortie.endswith("\\n"))

    def test_de_bout_en_bout(self):
        entree = "".join(f"paquet{i}\t0\t1.0\t1.fc44\tx86_64\tMIT\t\t\n" for i in range(600))
        r = self.lancer(entree, "--os-release", self.fichier_os_release(), "--version", "stable")
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(len(d["components"]), 600)
        self.assertEqual(d["metadata"]["component"]["version"], "stable")
        self.assertIn("600 paquets", r.stderr)

    def test_inventaire_presque_vide_refuse(self):
        r = self.lancer("bash\t0\t5.3\t1.fc44\tx86_64\tGPL-3.0-or-later\t\t\n", "--os-release", self.fichier_os_release())
        self.assertEqual(r.returncode, 2)
        self.assertIn("incomplet", r.stderr)

    def test_entree_illisible_refusee(self):
        r = self.lancer("n'importe quoi\n", "--os-release", self.fichier_os_release(), "--minimum", "0")
        self.assertEqual(r.returncode, 2)

    def test_os_release_obligatoire(self):
        self.assertNotEqual(self.lancer("", "--minimum", "0").returncode, 0)


if __name__ == "__main__":
    unittest.main()
