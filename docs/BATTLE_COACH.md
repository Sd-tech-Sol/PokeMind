# Tes conseils de combats en une commande

Depuis la racine de PokeMind :

```powershell
python -m pokemind battle coach
```

PokeMind affiche le bilan réel conservé, les familles adverses qui ont causé le
plus de défaites, les événements visibles et les pistes à tester. Il reprend les
rapports et le Learning Loop existants. Les cartes observées restent des indices;
elles ne prouvent ni une liste adverse complète ni la cause d'une défaite.

Après avoir ajouté des journaux `.txt` ou `.log` dans `data/local/battle_logs` :

```powershell
python -m pokemind battle coach --update
```

Cette actualisation est **locale et hors ligne** : elle intègre les nouvelles
parties, recalcule les statistiques et réutilise les connaissances PUBLIC déjà
disponibles. Elle ne télécharge aucune carte, règle ou liste sur Internet.
Les doublons sont exclus par les moteurs existants; une reprise identique à date
égale conserve le même instantané. Aucun service ni surveillance n'est installé.

Le joueur est mémorisé uniquement dans
`data/local/battle-intelligence/coach-settings.json`. Sur une nouvelle installation,
si aucun joueur n'est configuré et qu'une analyse est nécessaire, le premier appel
est `python -m pokemind battle coach --player VOTRE_JOUEUR`. Le choix est conservé
pour les appels suivants; `POKEMIND_PLAYER_NAME` est aussi accepté. Un joueur
différent d'un choix déjà enregistré est refusé pour éviter une réattribution.
Un rapport existant reste consultable sans joueur ni accès aux journaux.

Les dossiers applicatifs manquants sont créés dans PokeMind. Sans rapport, la
présence de journaux admissibles déclenche une seule analyse locale avec
sauvegarde. Sans journaux, la commande nomme le dossier où les déposer et retourne
un statut d'absence, sans inventer de résultats. Des journaux tous invalides
produisent un diagnostic local et un statut distinct. Une actualisation sans
journaux conserve et affiche le rapport existant.

`--json` donne les résultats structurés privés; `--as-of YYYY-MM-DD` fixe la date
d'évaluation (aujourd'hui par défaut). Une actualisation antérieure à la date du
rapport courant est refusée. Codes de sortie : `0` rapport affiché, `1` absence
de données exploitables, `2` blocage avec code neutre. Ne pas publier cette sortie
personnelle dans GitHub.

## Mémoire et reprise

Les instantanés `analysis-<empreinte>.json` restent immuables. La découverte est
directe dans `data/local/battle-intelligence`, sans parcourir de sous-dossier :
au plus 5 000 entrées et 256 Mio de candidats, 32 Mio par rapport. Chaque candidat
est contrôlé par `legacy_bridge.saved_report` : empreinte canonique, version,
date, cohérence matchs/W-L/groupes, exports60 et contenu. Les alias par date ne
déterminent jamais le dernier résultat. La sélection privilégie la date `as_of`,
puis la version du modèle (v4 devant v3 le même jour), puis la date de modification
et le nom canonique pour départager de façon stable.

`latest.json` pointe sur cet instantané exact. Cet index est mutable, local et
écrit par remplacement atomique contrôlé. La découverte validée le récupère s'il
est absent, corrompu ou périmé; un index identique n'est pas réécrit. Aucun chemin
d'index n'est suivi aveuglément. Les liens, reparse points, hardlinks et sorties
de portée sont refusés. Une panne de publication conserve les anciens rapports
et l'index antérieur; un fichier temporaire peut rester pour inspection.

Le Learning Loop de la même paire canonique est validé et réutilisé. S'il est
absent ou invalide, son état est indiqué et le rapport valide demeure consultable;
ce problème ne déclenche aucune nouvelle analyse.

La consultation d'un rapport n'ouvre pas SQLite ou les journaux. Une analyse
utilise seulement le chemin fixe `data/local/pokemind.sqlite3` selon le prévol et
les références déjà pris en charge par `battle_batch`. Le schéma 7 bloque l'import
SQL mais permet les conseils et la mémoire dérivée locale; aucune migration
7→13 ni sauvegarde n'est exécutée. Une DB absente n'est pas créée. Une DB13
compatible utilise l'import idempotent existant, sans inventer la version jouée.

Les données personnelles restent sous `data/local`, exclu de Git. La CI utilise
des données inventées; elle ne certifie pas les données du PC. **V1
NOT_RELEASE_READY**, livraison soumise à l'audit indépendant.
