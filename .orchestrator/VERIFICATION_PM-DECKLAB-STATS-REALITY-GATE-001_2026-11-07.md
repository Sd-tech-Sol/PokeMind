# Audit indépendant ChatGPT — PM-DECKLAB-STATS-REALITY-GATE-001
Date : 2026-11-07.
Commit rapport : `1a75bddfbb9bd1f72d99e38f5cde52d807f62b04`.
Code de la fonctionnalité : `3a56023e1d17d73760497813f813c263c40a743e`.
Rapport source initial : `.orchestrator/VERIFICATION_PM-DECKLAB-PUBLIC-STATS-001_2026-11-07.md`.

## Conclusion
**SOURCE_VERIFIED / REAL_SOURCE_EXECUTOR_EVIDENCE_ACCEPTED / CANDIDATE_BUILD_READY**.
La relecture GitHub confirme que le commit de clôture `1a75bdd` ne modifie aucun code applicatif, tests ni script : uniquement fichiers d'orchestration. Le rapport est cohérent avec le pipeline examiné précédemment, et les lacunes de preuve signalées (porte complète après retouche de fixture, vraie API Limitless) ont reçu des essais documentés. ChatGPT **n'a pas exécuté** lui-même les tests Windows/Python ni la collecte réseau, donc `REAL_SOURCE_EXECUTOR_EVIDENCE_ACCEPTED` ne signifie pas `INDEPENDENTLY_REPLAYED`.

## Éléments indépendamment vérifiés
- Compare GitHub `d1c06ed...1a75bdd` : un commit, fichiers d'orchestration seulement. Pas de nouveau code ni d'artefacts modifiés.
- `src/pokemind/deck_public_stats.py` lu au commit `3a56023` : collecte publique sans entrée deck, cache et limite de tentatives, ségrégation BO1/BO3, seuils, dédoublonnage par tournoi, identification locale ambiguë = taux refusé.
- Les chiffres rapportés sont arithmétiquement cohérents : 12V/8D/2N = 22 matchs, 12/22 = 54,55%, arrondi 55%, intervalle Wilson annoncé 35–73%. Une seule collecte de 5 GET demeure sous budget 8.
- Source et date sont affichées séparément de la période des tournois.

## Preuves déclarées par Claude (non ré-exécutées par ChatGPT)
- Deux portes complètes isolées `python scripts/local_gate.py`, code de sortie 0 : 121 Qt, 1634 cœur, 0 échec, 3 ignorés.
- Un essai réseau avec les vrais endpoints publics Limitless : 5 GET HTTP 200, 1 tournoi PTCGL Standard en ligne, BO1, 23 joueurs, 59 pairings dont 56 admissibles. Quota annoncé 50/5min; 2e tentative locale même jour = 0 GET.
- Projection hors ligne : archétype reconnu et ambigu, faible échantillon, inconnu; recomptage indépendant du snapshot égal au résultat PokeMind.

## Réserves restantes
- Échantillon minuscule, un seul tournoi (collecteur existant maximum un tournoi par campagne/jour); ne pas qualifier les pourcentages de statistiques « mondiales ».
- Les tournois `status=unknown` peuvent encore changer lors d'une future récupération. Les cas « Box/Control » ne sont pas reconnus, volontairement.
- Aucun EXE 0.9.5 construit, aucune réception UI réelle du propriétaire; aucune version 0.9.5 publiée.
- La 0.9.4 candidate reste non publiée et non réceptionnée séparément.
- Pas de CI GitHub, tests et HTTP exécutés seulement par Claude.

## Prochaine action unique
Préparer **un candidat Windows 0.9.5 isolé et non publié** depuis le code vérifié, avec version/notes cohérentes, installateur QA, scans et tests de fumée, sans modifier ou installer sur la machine de l'utilisateur et sans toucher au candidat conservé 0.9.4. Si une incompatibilité réelle apparaît, test de régression et correction minimale; sinon STOP et transmettre le rapport pour audit ChatGPT. Après ce candidat seulement, demander GO de réception sur Windows; un GO de publication sera toujours distinct.
