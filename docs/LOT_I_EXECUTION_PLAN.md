# LOT I — plan de complétion utilisable sous Windows (préparé par ChatGPT après audit H)

## Objet
Acheminer la V1 PokeMind vers une **utilisation réelle depuis Codex sur Windows 11**, sans réduire le périmètre original et **sans afficher RELEASE_READY sans preuves intégrales**. Il ne s'agit pas d'ajouter une interface GUI ou un service. Le résultat mesurable immédiat est un parcours de bout en bout démontré sur **environnement jetable/synthétique Windows**, et les workflows publics FR/EN plus complets. Les décisions impliquant les vraies données personnelles ou des installations demeurent séparées.

## Critères et sous-lots
| Phase | Développement et QA attendus | Sortie vérifiable | Si permission/sources manquent |
|---|---|---|---|
| I0 | Prévol et audit H du SHA exact; fermer régressions visibles à l'usage et nommer les gates existantes | baseline tests et matrice I, pas de reprise zéro | préserver toutes preuves A–H |
| I1 | Parcours **Windows+Codex** depuis dossier projet, `AGENTS.md`, recherche/lexique/deck/combats/coach annotations/mises à jour; commandes FR et erreurs remédiables sans fuites | smoke test intégral dans DB jetable + guide de début/retour après `/clear`; pas de GUI | aucune vraie importation privée implicite |
| I2 | Compléter le flux de découverte/détails historiques FR/EN sur TCGdex : pagination reprise, sets+cartes, couverture dénominateurs fiables, variantes/reprints; normes officielles datées et tri-state; Limitless sampling sourcé | campagnes bornées, rapports x/y selon preuves, backoff/retry et idempotence, fixtures de dérive; aucune règle fabriquée | documents officiels/Trainer Hill indisponibles → BLOCKED et piste vérifiable |
| I3 | OCR local : sélection et audit des binaires/langues libres possibles, installation `opt-in`, calibration/test reproductible sur corpus FR/EN authentiquement rasterisé; pas de lecture réelle sans consentement | commande de prévol, benchmarks mesurables seulement si moteur déjà présent, faux positifs/abstention/latence + refus de promotion | sans moteur : refus honnête; mise en place future guidée, pas de fake accuracy |
| I4 | Decks, journaux et coach : E2E réaliste **anonymisé synthétique**, version 60 cartes, >=3 logs distincts en fixtures, corrections/idempotence, mémoire 3 tours, statut d'incertitude et citations | transcript de démo Codex offline, retour de session, tests de non-inférence collection/crédits/carte cachée | pas de parties/screenshots personnels avant ordre distinct |
| I5 | Récupération SQLite et mise en service : outils `owner-plan` et dry-run, guides Windows pour backup vérifié, nouveau clone, migration sûre, inventaire résidus; examiner option de protocole offline séparé **sans écrasement** | tests crash/race/Windows; aucune restauration sur existant ni purge tant qu'exclusion durable/retention atomique non prouvées | BLOQUÉ sécurité plutôt que supprimer backups |
| I6 | Cadence Windows quotidienne + mardi/vendredi Toronto : installation seulement préparée, diagnostic et uninstall en dry-run, report de statut/alertes, DST | preuves simulateur et tests Windows; scheduler inactif | vrai scheduler exige opt-in/heure |
| I7 | Mise à jour README/docs, matrice V1 A–I, release gate, UX Codex, sécurité, CI au dernier SHA, contrôle confidentialité et handoff | rapport honnête, documentation d'utilisation Windows, backlog J+ s'il reste blocages | pas de déclaration RELEASE_READY sans vrais essais |

## Portée de plateformes
**Windows 11 est l'unique plateforme produit prioritaire.** Les tests GitHub Actions Linux déjà existants peuvent être conservés comme contrôle de non-régression sans élargir la compatibilité, ajouter des fonctionnalités Linux, du packaging Linux ou des tâches dédiées sans demande explicite du propriétaire. Ne pas réécrire cette portée en 'application multiplateforme'. Aucune nouvelle GUI, EXE, serveur, tâche résidente ou intégration exclusive Claude Code.

## Données/sources/sécurité
Fixtures synthétiques en Git. SQLite/journaux/captures/decks personnels dans `data/local/` hors Git; jamais à l'API publique ou à CI. TCGdex, Pokémon officiels, Limitless uniquement endpoints autorisés, quotas plafonnés par commande, respect conditions, dates et provenances; aucune prédiction ni règle certain sans texte vérifié. Trainer Hill seulement si accès automatisé primaire autorisé. Toute action réelle `backup/create/restore/migration/import/retention`, lecture de captures, installation d'OCR, installation de tâche planifiée, achats et changement branche principale requiert un ordre distinct. S'il manque un accord, avancer les parties indépendantes et conserver `BLOCKED_WITH_REASON`.

## Clôture
Codex exécute I0–I7 en un **grand lot autonome** sur sa branche, fait commits/tests/auto-correctifs, pousse, arrête. ChatGPT inspecte le dernier SHA et décide J+ si nécessaire. Tous objectifs V1 restent suivis. Le présent plan et la préparation du prompt ne constituent PAS une mise en service.
