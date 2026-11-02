# Audit PM-0002 — parseurs et exemples de journaux (2026-10-10)

## `kagd/pokemon-tcg-battle-replay`

- URL : <https://github.com/kagd/pokemon-tcg-battle-replay>
- Révision inspectée : `7402a50eeb840e80203105efe360fad6eeeb61f2`, dernier commit daté du 2025-04-10.
- Format : exemples anglais structurés par `Setup`, `Turn # N - Player's Turn`, actions ligne par ligne et issue explicite `... wins`.
- Code : TypeScript; le journal complet et chaque tour sont envoyés à Azure OpenAI, avec validation également confiée au modèle et température 0,7. Le dépôt signale lui-même un risque de troncature JSON.
- Dépendances : Azure Identity, Azure/OpenAI, OpenAI, TypeScript, ts-node et tslib; clé, endpoint et déploiement Azure requis. Coût, réseau et confidentialité incompatibles avec le traitement local demandé.
- Licence : `package.json` déclare `ISC`, mais aucun fichier `LICENSE`, `COPYING` ou `NOTICE` n'est présent dans la révision inspectée. Activité limitée à 11 commits, 5 étoiles, aucun test automatisé visible.
- Décision : **rejeté comme dépendance et comme code à copier**. PokeMind utilise un parseur Python déterministe sans réseau. Seules les formes textuelles factuelles observées dans les exemples publics ont servi à concevoir des fixtures synthétiques originales.

## Exemples publics et format d'export

- Les deux exemples du dépôt ci-dessus ont été lus comme contenu non fiable. Le plus long a permis un essai local non versionné : joueur de référence, adversaire, victoire, 6 tours et 85 événements reconnus. Aucun nom ou journal externe n'est ajouté au dépôt PokeMind.
- Le forum officiel Pokémon indique que l'export copie le journal dans le presse-papiers plutôt que de créer un fichier : <https://community.pokemon.com/en-us/discussion/12951/where-does-the-battle-log-export-to-on-pc-and-android> (discussion 2024, modifiée 2025; consultée le 2026-10-10).
- Les sources communautaires signalent que l'export peut omettre ou rendre ambiguës certaines informations. PokeMind ne reconstruit donc pas les mains cachées, les Récompenses face cachée, une liste complète ni une causalité.

## Décision de sécurité et de portée

Le MVP accepte fichier, stdin ou presse-papiers explicite, n'envoie rien sur le
réseau et ne conserve pas le texte brut. Les formats non reconnus restent inconnus
ou non valides. Aucun paquet externe, service, clé, navigateur, modèle incorporé ou
script du dépôt audité n'est utilisé. La compatibilité finale doit être confirmée
avec un journal réel de l'utilisateur conservé uniquement sous `data/local/`.
