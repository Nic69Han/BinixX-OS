# Obtenir de l'aide : dépannage et rapport pour le support

Menu → **Obtenir de l'aide** (ou page *Obtenir de l'aide* du Centre NicOS, voir
[centre-nicos.md](centre-nicos.md)). Tout se passe sur le PC : **rien n'est envoyé nulle part**.

## Les cas les plus fréquents

Pour chacun, une explication en une ou deux phrases et un bouton qui ouvre le bon réglage :
plus d'Internet, imprimante muette, pas de son, écran de la mauvaise taille, PC lent, « depuis la
dernière mise à jour quelque chose ne marche plus » (retour à la version précédente, un
redémarrage, sans rien perdre) et bureau cassé.

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

## Rapport de diagnostic

Le bouton *Créer le rapport* lance `nicos-diagnostic`, enregistre le résultat dans
`Documents/Rapport-NicOS-<date>.txt` et le copie dans le presse-papiers. Il contient : version de
NicOS et de la dernière mise à jour, services en échec, erreurs récentes du démarrage, espace
disque, mémoire, état du réseau (types et états des connexions seulement), cartes graphiques, réseau
et son, imprimantes, applications Flatpak.

Il ne contient ni mot de passe, ni contenu de fichier, ni adresse IP, ni nom de réseau Wi-Fi, et il
n'exige aucun droit particulier. L'utilisateur le relit avant de l'envoyer ; un administrateur peut aussi
le lancer lui-même : `/usr/libexec/nicos/nicos-diagnostic`.

## Tests

`tests/image/centre/test_aide.py` : rapport complet et sans adresse IP, cycle programmer / appliquer /
annuler de la remise à zéro (la langue et le clavier restent), création du rapport par la page. Le test
VM rejoue le rapport et la programmation sur le système installé.
