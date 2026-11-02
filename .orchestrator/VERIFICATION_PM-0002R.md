# Vérification indépendante — PM-0002R (2026-10-10)

## Décision
**Code de correction PM-0002R accepté après inspection GitHub; validation terrain utilisateur encore ouverte.** Cette décision n'affirme pas que la compatibilité avec les vrais journaux Pokémon TCG Live est démontrée. L'état V1 demeure inachevé.

## Preuves indépendamment consultées
- Dépôt privé : `Sd-tech-Sol/PokeMind`.
- Branche vérifiée : `work/pm-0002r`, HEAD `f05e0e5229ff272537cb4985030d457e194d18dd`.
- Commit de code/test : `310f6dd884a1ed1e332b522cd9b10a7056e6c9d2`; clôture `42fa1b209493b967861482bcada6339559b99d10`, confirmation `f05e0e5`.
- Comparaison avec la base d'orchestration `44455c78d3a7d782a9d326beef590cd425023106` : 3 commits en avance, 0 en retard; code/tests/docs dans 10 fichiers.
- Lecture directe de `src/pokemind/battle_logs.py`, `cli.py`, tests, README, `RESULT.md`, `HANDOFF.md`; aucune intégration de service externe, images ou journaux réels dans les fichiers modifiés.
- Statuts GitHub : aucun check ni workflow d'exécution visible. `40 passed in 4.44s`, compilation, rollback, smoke Windows, cinq parties fictives sont **déclarés par Codex**, non exécutés de manière indépendante dans l'environnement Windows de l'utilisateur.

## Constats de lecture du code
1. `parse_battle_log` normalise les noms Unicode et casse (`NFKC/casefold`), refuse plusieurs identités contradictoires et laisse `outcome=inconnue` sans référence/adversaire/gagnant concordants. Les tests incluent le gagnant tiers, conflit et victoire/défaite explicites.
2. L'ancienne heuristique « plus de cartes piochées = utilisateur » a disparu. Les cartes vues ne sont attribuées à `self` qu'avec référence reconnue.
3. La forme française « a utilisé X » enregistre l'action sans inscrire `X` comme carte observée. Tests présents.
4. `--reparse` conserve le même SHA/ID/deck, remplace les événements dans une transaction, interdit le changement de deck. Tests de doublon et de rollback présents.
5. Le presse-papiers PowerShell force l'encodage UTF-8; le smoke réel sur Windows est uniquement attesté par Codex.

## Limites et décisions
- Aucun vrai journal de combat utilisateur n'est encore vérifié. La robustesse aux variations réelles de format reste **inconnue**; ne pas marquer le parcours « importer le combat réel -> bilan fiable » VERIFIED.
- Le journal brut n'est pas conservé; pour réanalyser plus tard, l'utilisateur doit disposer à nouveau de la source.
- Un export de combat ne donne ni deck complet de 60 cartes, ni inventaire de collection. Cinq parties donnent un bilan **exploratoire**, pas une certitude ni preuve causale.
- Pas de nouvelle correction de code recommandée à l'aveugle. **Une seule prochaine tâche** : PM-0002T, test terrain volontaire avec 1 victoire et 1 défaite (dès que disponibles), import local, contrôle des événements et W/L, puis correction ponctuelle uniquement si erreur réelle reproduite.
- Ne jamais publier de vrais pseudos, textes de journaux, captures ou base SQLite sur GitHub, y compris dans tests, issues, rapports ou artefacts.
