# Vérification indépendante ChatGPT — PM-0002 (2026-10-10)

## Décision : corrections ciblées obligatoires avant VERIFIED

**Publication confirmée, mais PM-0002 n'est pas encore VERIFIED fonctionnellement.** Une correction des inférences d'identité et d'issue est nécessaire avant d'utiliser les statistiques pour conseiller un deck.

### Preuves vérifiées directement sur GitHub
- Branche : `work/pm-0002`, HEAD : `e142e528954a26bb8e8b01b7ded064d360b6fe19`.
- Code : `c715687858f00dba82f7afcbec08da28831b7feb`; clôture : `e142e528`.
- Diff de `work/pm-0001` à `work/pm-0002` : 11 commits en avance, zéro en retard; nouveaux `battle_logs.py`, `profiles.py`, tests et fixtures; migration SQLite 1 vers 2; CLI ajoutée.
- `RESULT.md` rapporte **30 tests réussis**, compilation, installation sans réseau, migration et démo fictive 5 parties. Ce sont des **preuves déclarées par Codex**, pas des tests indépendamment exécutés sur Windows par ChatGPT.
- Aucun statut CI ni workflow associé au HEAD via GitHub; les tests automatisés ne sont pas indépendamment confirmés.
- Revue du parseur, schéma, profils, CLI, fixtures et tests : la portée annoncée est implémentée, le stockage reste local, `data/local/` ignoré et aucun journal réel ni DB privée dans l'arbre Git.

### Anomalies concrètes de lecture de code
1. Dans `parse_battle_log`, si `winner` et `reference_player` sont présents mais différents, le résultat devient **L** même si `winner` n'a jamais été corroboré comme adversaire/participant. Un texte final trompeur pourrait produire une fausse défaite. Ajouter test adversarial et validation du gagnant.
2. `_reference_from_named_draws` identifie le joueur de référence uniquement par *la fréquence de pioches nommées* lorsque aucune identité explicite/fiable n'est disponible. Cette heuristique n'est pas une preuve du joueur. Peut inverser self/opponent, W/L, cartes observées et statistiques. Interdire les conclusions de haute confiance issues de cette supposition.
3. La branche française `a utilisé ...` est classée `use` avec le segment capturé comme `card_name`; sans contexte, ce segment peut désigner le **nom d'une attaque/talent plutôt que le nom d'une carte**. Éviter de compter des noms d'attaques comme cartes possédées/jouées.
4. La lecture du presse-papiers Windows utilise une sortie PowerShell décodée `utf-8`; le test fourni simule la commande mais ne prouve pas la conservation des accents sur la machine Windows réelle. Prévoir validation réelle, gestion explicite d'encodage ou repli clair.
5. Les données structurées sont conservées mais pas les journaux bruts (choix voulu); **une correction du parseur ne répare pas automatiquement les importations déjà effectuées**. Prévoir réimport explicite du même SHA sous nouvelle version sans doubler les parties, ou documenter une procédure sûre de réparation à partir des exports conservés par l'utilisateur.

### Portée de correction
`work/pm-0002r` reçoit une tâche **PM-0002R** seulement : tests de régression, fiabilisation des faits et procédure de relecture. Pas de nouvelles fonctions de catalogue, deck 60 cartes, méta, coach, planificateur, ou inventaire. L'objectif du futur agent reste conservé dans `PROJECT_SPEC.md` et `ROADMAP.md`. Ne pas consommer ni publier de véritables journaux privés.
