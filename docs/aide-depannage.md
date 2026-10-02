# Obtenir de l'aide : dépannage et rapport pour le support

Menu → **Obtenir de l'aide** (ou page *Obtenir de l'aide* du Centre NicOS, voir
[centre-nicos.md](centre-nicos.md)). Tout se passe sur le PC : **rien n'est envoyé nulle part**.

## Les cas les plus fréquents

Pour chacun, une explication en une ou deux phrases et un bouton qui ouvre le bon réglage :
plus d'Internet, imprimante muette, pas de son, écran de la mauvaise taille, PC lent, « depuis la
dernière mise à jour quelque chose ne marche plus » (retour à la version précédente, un
redémarrage, sans rien perdre), bureau cassé et « un réglage du système modifié à la main pose problème ».

## « Mon bureau est cassé » : réinitialiser le bureau

Remet la barre, le thème, les raccourcis et le comportement des fenêtres comme au premier jour.

- **Ne change pas** : les fichiers, les applications, la langue, le clavier, les écrans, les mots de
  passe enregistrés, les profils de Firefox et de Thunderbird.
- **Rien n'est supprimé** : les anciens réglages sont rangés dans
  `~/.local/share/nicos/sauvegardes/bureau-<date>/`, avec un `LISEZMOI.txt` qui explique comment en
  retrouver un.
- **Pourquoi à la prochaine ouverture de session ?** Plasma réécrit ses réglages quand la session se
  ferme : les déplacer pendant qu'elle tourne ne servirait à rien. Le bouton programme la remise à
  zéro (`nicos-reinitialiser-bureau programmer`), propose de fermer la session, et le script
  `etc/xdg/plasma-workspace/env/90-nicos-reinitialiser.sh` l'applique à l'ouverture suivante, avant que
  Plasma ne démarre. `nicos-reinitialiser-bureau annuler` la retire.

## « Un réglage du système modifié à la main pose problème » : réparer le système

Un tutoriel suivi trop vite ou un essai oublié peut dérégler l'écran de connexion, le son, le pare-feu…
Sur NicOS, l'image porte les réglages d'origine (`/usr/etc`) et `/etc` contient ce qui a été changé depuis.
Le bouton *Voir les réglages modifiés* compare les deux et liste ce qui diffère :

- **Modifié** : remis comme dans l'image ; **supprimé** : recréé ; **ajouté** : retiré (c'est un réglage qui
  n'existe pas dans l'image).
- **Rien n'est coché d'avance** : l'utilisateur choisit. Une seule authentification d'administrateur (`pkexec`).
- **Sauvegarde et annulation** : la version remplacée est copiée dans
  `/var/lib/nicos/sauvegardes-etc/<date>/` (réservé à l'administrateur, 20 réparations gardées) ;
  *Annuler la dernière réparation* rend à chaque fichier sa version d'avant.
- **Périmètre volontairement étroit** : seuls les dossiers de réglages courants sont concernés (écran de
  connexion, valeurs par défaut du bureau, variables d'environnement, noyau, pilotes, règles des
  périphériques, services, son, pare-feu, options réseau, polices…). **Jamais touchés** : comptes et mots de
  passe, clés SSH, connexions réseau et Wi-Fi, disques (`fstab`, `crypttab`), imprimantes, domaine Active
  Directory, identité de la machine ; ni les services activés ou désactivés (liens `*.wants`).
- Sans `/usr/etc` (conteneur, poste de développement), l'outil refuse de travailler : sans l'image de
  référence, tout aurait l'air « ajouté ».
- Le rapport de diagnostic liste aussi ces fichiers (noms seulement) : le support voit d'un coup d'œil ce
  qui a été touché.

Ligne de commande (administrateur) : `nicos-reparer-systeme liste | restaurer CHEMIN… | annuler [DATE] | sauvegardes`.

### Pourquoi pas un « Réinitialiser NicOS » complet ?

Remettre tout `/etc` à l'origine effacerait aussi les comptes, les mots de passe, les réseaux Wi-Fi, le
domaine et les clés : l'utilisateur ne pourrait plus ouvrir sa session. La réparation ciblée, avec
sauvegarde et annulation, couvre le besoin réel (un réglage touché à la main) sans ce risque. Les deux
autres filets existent déjà : le **retour à la version précédente** du système (Administration du PC →
Mises à jour logicielles) et le **retour arrière automatique** si l'écran de connexion ne démarre plus
([mises-a-jour.md](mises-a-jour.md)). Et en dernier recours, réinstaller NicOS en gardant sa partition
personnelle (`/home`) ne touche pas aux fichiers de l'utilisateur.

## Rapport de diagnostic

Le bouton *Créer le rapport* lance `nicos-diagnostic`, enregistre le résultat dans
`Documents/Rapport-NicOS-<date>.txt` et le copie dans le presse-papiers. Il contient : version de
NicOS et de la dernière mise à jour, services en échec, erreurs récentes du démarrage, espace
disque, mémoire, état du réseau (types et états des connexions seulement), cartes graphiques, réseau
et son, imprimantes, applications Flatpak, noms des réglages du système modifiés.

Il ne contient ni mot de passe, ni contenu de fichier, ni adresse IP, ni nom de réseau Wi-Fi, et il
n'exige aucun droit particulier. L'utilisateur le relit avant de l'envoyer ; un administrateur peut aussi
le lancer lui-même : `/usr/libexec/nicos/nicos-diagnostic`.

## Tests

`tests/image/centre/test_aide.py` : rapport complet et sans adresse IP, cycle programmer / appliquer /
annuler de la remise à zéro (la langue et le clavier restent), création du rapport par la page. Le test
VM rejoue le rapport et la programmation sur le système installé.

`tests/image/centre/test_reparer.py` (25 tests) : comparaison de deux arborescences fabriquées (modifié,
supprimé, ajouté, droits changés, liens), jamais proposés (comptes, clés, réseau, services), refus des
chemins qui sortent de `/etc` (y compris par un lien), remise à l'origine, sauvegarde, annulation,
élagage, page. Le test VM le fait **sur le système installé** : il modifie, supprime et ajoute un réglage,
vérifie que l'outil les voit, les remet à l'identique de l'image (contenu, droits, contexte SELinux),
annule, puis laisse le système comme il l'a trouvé.
