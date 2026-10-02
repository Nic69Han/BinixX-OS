# Solutions libres à intégrer dans NicOS : recherche du 2 octobre 2026

Question posée : quelles solutions **sous licence MIT** (ou proche) peut-on introduire dans NicOS pour le
rendre plus moderne et plus utile, en s'inspirant de Coucou ? Coucou n'est **pas** livré pour
l'instant (décision du propriétaire).

**Méthode.** Chaque licence et chaque chiffre ci-dessous a été relevé sur la page du dépôt ou de
Flathub le 2 octobre 2026. Légende : **MIT** = ce qui était demandé ; **permissive** = Apache-2.0 ou
BSD, mêmes libertés pour NicOS (mention de l'auteur à conserver) ; **⚠** = licence qui n'est pas MIT
(GPL, AGPL…) : on peut proposer l'application telle quelle à l'utilisateur, mais on ne copie jamais son
code dans NicOS sans analyse. Étoiles = popularité, pas qualité.

## À retenir

| Besoin | Choix recommandé | Licence | Pourquoi | Alternative |
| --- | --- | --- | --- | --- |
| IA locale (moteur) | **RamaLama** | MIT | Fedora l'installe d'un `dnf install` ; fait tourner les modèles dans des conteneurs Podman, détecte la carte graphique ; rien à installer sur le système de base | Ollama (MIT), llama.cpp (MIT) |
| IA locale (fenêtre de discussion, prête à l'emploi) | **Jan** (Flathub) | permissive (Apache-2.0) | « ChatGPT » 100 % hors ligne, modèles locaux, API locale, compatible MCP ; déjà un Flatpak vérifié | AnythingLLM (MIT, application de bureau, plus lourde) |
| Dictée vocale | **Whis** (Flathub) | MIT | Raccourci → on parle → texte dans le presse-papiers ; mode **local** sans Internet ; fonctionne sous Wayland sans injection de touches | Handy (MIT, 32 600 étoiles, mais absent de Flathub et Wayland « limité » : il demande wtype ou dotool) |
| Diagnostic par IA (lecture seule) | **linux-mcp-server** | permissive (Apache-2.0) | Outils MCP **strictement en lecture seule** (système, services, journaux, réseau, disques) | linux-mcp de Mohabdo21 (MIT, 1 étoile : trop jeune) |
| Agir avec confirmation | **systemd-mcp** (openSUSE) | MIT | Gère les services via polkit : l'autorisation est demandée à l'utilisateur ; jeune (10 étoiles) | Écrire nos propres actions (liste blanche) |
| Programme Windows indispensable | **WinBoat** | MIT | Windows dans une VM, ses fenêtres dans le bureau NicOS (FreeRDP) ; 23 100 étoiles ; Windows lui-même reste à acquérir (licence) | Bottles (⚠ GPL-3.0, déjà proposé à la demande) ; WinApps (⚠ **AGPL-3.0**) |
| Gestion d'un parc | **Cockpit** (déjà là) + **Fleet** | MIT (cœur) | Inventaire et requêtes sur Linux, Windows, macOS ; le cœur est MIT, les options payantes sont dans un dossier `ee/` à licence commerciale | MeshCentral (permissive, Apache-2.0) pour l'assistance à distance |
| Retour arrière automatique | **greenboot** | permissive (BSD-3-Clause) | Fait pour bootc ; adopté dans la PR « Retour arrière automatique » | — |
| Fichiers à la demande (OneDrive, Drive) | **rclone** | MIT | 60 100 étoiles ; `rclone mount` avec OneDrive, Google Drive, Dropbox ; prévu en U2 de la feuille de route | Client OneDrive actuel (⚠ GPL) |
| Envoyer des fichiers entre PC et téléphone | **LocalSend** (Flathub) | permissive (Apache-2.0) | Comme AirDrop, sans compte ; **demande d'ouvrir le port 53317** : à proposer, pas à activer d'office | KDE Connect (déjà là, ⚠ GPL) |
| Menus circulaires, accès rapide | **Kando** (Flathub) | MIT | Menu en cercle déclenché par un raccourci ; « la plupart des bureaux » sont pris en charge, KDE à régler | — |

## IA et assistant : le détail

| Solution | Licence | Constat | Décision |
| --- | --- | --- | --- |
| Coucou (Louis Raillé) | **code MIT** ; nom, personnage « Mochi », icônes, sons et images **réservés** | macOS (barre d'encoche) et Windows (Tauri) ; pas de Linux. Un compagnon d'écran qui montre l'état des agents IA et relaie leurs demandes d'autorisation | Pas livré. On peut reprendre **l'idée** (une fenêtre qui demande « autoriser cette action ? ») ; le code MIT serait réutilisable avec sa mention, jamais le nom ni le personnage |
| RamaLama | MIT, 3 100 étoiles | Dans Fedora | **Retenu** comme moteur local |
| Ollama | MIT, 182 000 étoiles | Installation par script ou conteneur ; pas de Flatpak ni de RPM Fedora | Alternative |
| llama.cpp | MIT | Moteur de base d'Ollama et de RamaLama | Indirectement |
| whisper.cpp | MIT, 54 100 étoiles | Reconnaissance vocale, tourne sans carte graphique | Indirectement : moteur de la famille des outils de dictée locale (Handy utilise des modèles Whisper) |
| Jan | Apache-2.0 | Flatpak vérifié ; hors ligne ; MCP | **Retenu** (fenêtre de discussion) |
| AnythingLLM | MIT, 66 700 étoiles | Application de bureau Linux ; modèles locaux ; MCP ; documents de l'entreprise | À étudier pour « interroger ses documents » |
| Goose (Block) | Apache-2.0, 54 900 étoiles | Agent avec extensions MCP, application de bureau et ligne de commande ; Ollama pris en charge | À étudier pour le niveau « agir » |
| mcphost | MIT | **Archivé** en avril 2026 | Écarté |
| Newelle | ⚠ GPL-3.0 | Discussion IA pour GNOME | Écarté (licence) |
| PlasmaLLM, Pipsqueak, K-Ollama, Vocalinux | ⚠ GPL-2.0+, GPL-3.0, LGPL-2, AGPL-3.0 | Relevés lors de la première recherche | Écartés (licence) |

## Ce que cela change pour la feuille de route

- **Aucune de ces solutions n'est ajoutée à l'image** dans cette étape : chacune a son chantier,
  avec ses tests, décrit dans [ia-copilote.md](ia-copilote.md) et [gestion-de-flotte.md](gestion-de-flotte.md).
- Whis, Jan, LocalSend et Kando peuvent entrer **dès maintenant** dans le catalogue « Mon logiciel
  Windows » comme applications à installer à la demande (aucun risque pour l'image).
- À vérifier avant tout ajout : maintenance récente, présence sur Flathub, comportement sous Wayland/KDE,
  ports réseau ouverts (LocalSend), données qui quittent le PC (modes « cloud » de Whis et de Jan).
