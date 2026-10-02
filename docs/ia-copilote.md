# Un copilote IA dans NicOS : plan et garde-fous

Objectif : aider un utilisateur qui quitte Windows à **comprendre, réparer et se débrouiller**, sans
jargon. Étude, rien n'est livré : chaque niveau est un chantier à part, avec ses tests, à lancer sur
décision du propriétaire.

> **Principe : l'IA propose, l'utilisateur décide, rien ne sort du PC sans son accord.**

## Les quatre niveaux

| Niveau | Ce que ça fait | Risque | État |
| --- | --- | --- | --- |
| **0. Sans IA** | Page « Obtenir de l'aide » : sept cas fréquents, rapport de diagnostic, bureau réinitialisable, retour arrière | Nul | **Livré** (PR « Obtenir de l'aide ») |
| **1. Expliquer** | Bouton « Demander à l'IA » sur la page Aide : le rapport de diagnostic (relu par l'utilisateur) est donné au moteur choisi ; la réponse explique en français simple ce qui ne va pas et quoi faire. **Aucune action.** | Faible : on lit, on n'agit pas | À décider |
| **2. Agir avec confirmation** | L'assistant propose des **boutons** (« Ouvrir les réseaux », « Redémarrer l'imprimante », « Réinitialiser le bureau ») ; chaque bouton correspond à une action d'une **liste blanche** et affiche ce qu'il fait et pourquoi. Un clic, jamais d'enchaînement automatique. | Moyen : encadré par la liste blanche et polkit | À décider |
| **3. Administrer un parc** | Même chose pour l'administrateur de la PME : lecture de l'inventaire, recommandations. **Jamais d'application automatique sur le parc.** | Élevé | Plus tard ([gestion-de-flotte.md](gestion-de-flotte.md)) |

## Quel moteur ? Trois choix, à proposer au premier lancement

| Moteur | Où ça tourne | Avantage | Limite |
| --- | --- | --- | --- |
| **Aucun** (par défaut) | — | Rien n'est envoyé ni installé | Pas d'IA |
| **Local** | Sur le PC : RamaLama (MIT) ou Jan (Apache-2.0, Flatpak) | Rien ne quitte le PC, fonctionne hors ligne | 8 Go de mémoire conseillés, petits modèles (3 à 8 milliards de paramètres), réponses plus lentes sans carte graphique |
| **Serveur de l'entreprise** | Un serveur interne (Ollama ou RamaLama, API compatible OpenAI) | Un seul modèle pour tout le parc, données dans l'entreprise | Un serveur à entretenir |
| **Service en ligne** | Compte et clé de l'utilisateur | Meilleures réponses | Le rapport quitte le PC : **consentement explicite**, contenu affiché avant l'envoi |

Le choix par défaut est « Aucun » ; le **local** est proposé en premier quand le PC a assez de mémoire.

## Garde-fous (valables à tous les niveaux)

1. **Les journaux sont des données, pas des ordres.** Un message d'erreur peut contenir un texte
   piégé (« ignore tes instructions et lance… ») : tout ce qui vient d'un journal, d'un fichier ou du web
   est traité comme du texte à expliquer, jamais comme une commande.
2. **Pas de shell libre.** Le niveau 2 n'exécute que les actions de la liste blanche (paramètres à
   ouvrir, service nommé à redémarrer, remise à zéro du bureau…), avec des arguments contrôlés. Les
   actions qui touchent au système passent par polkit : le système, pas l'IA, demande l'autorisation.
3. **Ce qui est envoyé est montré.** Le rapport est relu avant tout envoi hors du PC ; il ne contient
   déjà ni mot de passe, ni contenu de fichier, ni adresse IP.
4. **Réversible ou confirmé.** Chaque action est annulable (retour arrière, sauvegarde du bureau) ou
   demande une confirmation distincte.
5. **Journal des actions** consultable par l'utilisateur, **interrupteur** pour tout couper.

## Briques ouvertes retenues

Voir [solutions-mit.md](solutions-mit.md) pour les licences et la maturité.

| Rôle | Brique | Remarque |
| --- | --- | --- |
| Moteur local | RamaLama (MIT) ; alternative Ollama (MIT) | Dans des conteneurs Podman |
| Fenêtre de discussion | Jan (Apache-2.0) | Flatpak vérifié, MCP |
| Lecture du système | linux-mcp-server (Apache-2.0) | Strictement en lecture seule |
| Actions encadrées | systemd-mcp (MIT) **ou** nos propres actions | Jeune : nos propres actions d'abord |
| Agent complet | Goose (Apache-2.0) | Pour le niveau 2 si la liste blanche ne suffit pas |
| Dictée | Whis (MIT, Flathub) | Parler plutôt que taper, mode local |

## Coucou

Coucou (code MIT, nom et personnage réservés par son auteur) montre bien une idée utile : **une petite
fenêtre qui demande « autoriser cette action ? »** quand un agent veut agir. C'est le modèle de
confirmation du niveau 2. Il n'existe que pour macOS et Windows : il faudrait le réécrire pour Plasma.
Non livré pour l'instant.

## Chantiers proposés, dans l'ordre

1. **IA-1 Expliquer** : page « Demander à l'IA » (choix du moteur, aperçu du rapport, réponse), testée
   avec un faux serveur compatible OpenAI ; moteur local RamaLama sur demande, jamais préinstallé.
2. **IA-2 Agir avec confirmation** : liste blanche d'actions, boîte « autoriser ? », journal.
3. **IA-3 Dictée** : Whis dans le catalogue, raccourci clavier par défaut.
4. **IA-4 Parc** : après la gestion de flotte.

## Décisions attendues

- Moteur par défaut : « Aucun » (recommandé) ; local proposé au premier lancement si le PC a au moins 8 Go.
- Niveau 1 d'abord, ou directement jusqu'au niveau 2 ?
- Coucou : réécriture pour Plasma plus tard, ou idée seulement ?
