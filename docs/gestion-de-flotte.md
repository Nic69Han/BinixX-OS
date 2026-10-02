# Gérer un parc de postes NicOS

Pour une PME de 5 à 50 postes. Le principe : **une image, une source de vérité**. On ne règle pas chaque
PC ; on règle l'image, et tous les postes la suivent.

## Ce qui est déjà là

| Besoin | Solution | Où |
| --- | --- | --- |
| Tous les postes identiques | Image d'entreprise : NicOS + logiciels + réglages de la PME | [image-entreprise.md](image-entreprise.md) |
| Déployer sans casser | Canaux `testing` (postes pilotes) puis `stable`, mises à jour testées | [mises-a-jour.md](mises-a-jour.md) |
| Un poste en panne après une mise à jour | Retour arrière **automatique**, ou manuel en un clic | [mises-a-jour.md](mises-a-jour.md) |
| Administrer un poste à la souris | Cockpit (« Administration du PC ») | [administration.md](administration.md) |
| Domaine Active Directory | Jonction par poste, comptes Windows | [administration.md](administration.md) |
| Savoir ce qui ne va pas sur un poste | Rapport de diagnostic (page Aide), à joindre à la demande | [aide-depannage.md](aide-depannage.md) |

## Ce qui manque, et les options

Aucune de ces options n'est installée par défaut : ce sont des **serveurs** de l'entreprise, à choisir
selon la taille du parc. Licences relevées le 2 octobre 2026 ([solutions-mit.md](solutions-mit.md)).

| Besoin | Option | Licence | Quand |
| --- | --- | --- | --- |
| Inventaire du parc (versions, logiciels, état des disques), requêtes sur tous les postes | **Fleet** (osquery) | MIT pour le cœur ; options payantes sous licence commerciale | À partir de 20 postes, ou dès qu'un audit l'exige |
| Assistance à distance par le support (bureau, terminal, fichiers) | **MeshCentral**, auto-hébergé | Apache-2.0 | Support informatique externe ou interne |
| Assistance ponctuelle, sans serveur | RustDesk ou AnyDesk (Flathub, voir « Mon logiciel Windows ») | AGPL-3.0 / propriétaire | 1 à 10 postes |
| Plusieurs postes dans une seule console | Cockpit : ajouter les autres postes (connexion SSH, à activer à la demande) | LGPL | Parc modeste, administrateur unique |

## Règles de prudence

- Les postes ne reçoivent **que** ce que l'image contient : pas de commande poussée à la main sur les postes.
- Un agent (Fleet, MeshCentral) est une porte d'entrée de plus : n'installer que ce dont on a besoin, le
  mettre dans l'image de l'entreprise (donc versionné et testé) et ouvrir le moins de ports possible.
- Aucun secret (mot de passe, jeton d'enrôlement) dans l'image : un jeton d'enrôlement se saisit une fois
  par poste, ou se dépose par un canal séparé.
- Garder au moins un poste pilote sur `testing`.
