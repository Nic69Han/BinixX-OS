# Jeux

Beaucoup d'utilisateurs de Windows jouent. BinixX OS ne préinstalle **aucune** boutique (image plus légère,
choix de l'utilisateur, licences des éditeurs) mais, dans le Centre BinixX OS, la page **Jeux** (et la
recherche « Mon logiciel Windows ») propose chaque boutique au nom qu'on lui connaît sous Windows.

| Sous Windows | Sous BinixX OS | Licence | Remarque |
| --- | --- | --- | --- |
| Steam | Steam (Flatpak) | propriétaire | Proton, intégré à Steam, fait tourner des milliers de jeux Windows. À activer dans les réglages de Steam si un jeu ne démarre pas. |
| Epic Games Store, GOG Galaxy | Heroic Games Launcher | GPL-3.0 | Aussi Amazon Games ; les jeux Windows passent par Proton. |
| Battle.net, EA app (Origin), Ubisoft Connect | Lutris | GPL-3.0 | Scripts d'installation par boutique ; **résultat variable selon les jeux, sans garantie**. |
| Minecraft Launcher | Prism Launcher | GPL-3.0 | Plusieurs installations de Minecraft Java ; un compte acheté reste nécessaire. |
| (jeu qui refuse de démarrer) | ProtonUp-Qt | GPL-3.0 | Installe d'autres versions de Proton (GE-Proton). |
| Xbox Game Pass, GeForce NOW | Dans le navigateur | — | Jeu en streaming, sans installation ; abonnement nécessaire. |

Tout s'installe à la demande depuis Flathub, par Discover. Les identifiants sont vérifiés par
`tests/centre/verifier_flathub.py` (licences affichées).

## Matériel

- **Carte graphique** : la page indique la ou les cartes détectées. Sur un portable à deux cartes,
  `switcheroo-control` permet de lancer un jeu avec la carte la plus puissante (clic droit sur l'icône →
  « Lancer avec la carte graphique dédiée »). Cartes NVIDIA : les pilotes libres (`nouveau`) suffisent à la
  bureautique ; pour les jeux 3D exigeants, l'administrateur peut passer à la variante `binixx-nvidia`
  (pilotes officiels, **expérimentale** : voir [nvidia.md](nvidia.md)).
- **Manettes** : accès direct à leur réglage et à leur test dans la Configuration du système.
- **Un jeu ne démarre pas** : lien vers ProtonDB, qui recense jeu par jeu ce qui fonctionne.

## Ce qu'il ne faut pas promettre

- Les jeux protégés par un anti-triche qui n'a pas de version pour Linux (certains jeux en ligne) **ne
  fonctionneront pas**. ProtonDB et la page du jeu sur la boutique le disent.
- Les performances dépendent de la carte graphique et de ses pilotes ; sur un vieux PC, préférer les jeux
  légers ou le jeu en streaming.
- Aucun jeu n'est testé par la CI : elle vérifie que la page, le catalogue et les actions fonctionnent.

## Alternatives écartées

- **Préinstaller Steam** : image alourdie pour tout le monde, licence propriétaire, mises à jour de
  l'éditeur indépendantes de celles de BinixX OS.
- **Image dédiée aux jeux** (comme Bazzite, qui partage la même base) : doublerait la maintenance ; BinixX OS
  vise le bureau, et Bazzite reste le bon choix pour une console de salon.
- **MangoHud, GameMode, Gamescope** : disponibles en extensions Flatpak ; à ajouter à la page si la demande
  existe.
