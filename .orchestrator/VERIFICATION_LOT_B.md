# VERIFICATION_LOT_B — audit indépendant ChatGPT (2026-10-13)

## Verdict
**LOT B livré et fondations B0–B5 acceptées en revue statique AVEC RÉSERVES.** B2 (recommandations datées) et B4 (validation des candidats) exigent des correctifs avant certification de leur exactitude. Ces correctifs sont regroupés sous **C0** au début du grand LOT C autonome, sans micro-lots et sans sauter les fonctions V1. Ne pas déclarer LOT B intégralement VERIFIED ni catalogue/règles/métagame complets.

## Vérifications directes sur GitHub
- Repo privé `Sd-tech-Sol/PokeMind`; branche `work/pm-v1-lotb-personal-deck-advisor`; Codex HEAD `571b5111ef74881985bdd8c2041c7f3dc79dc683`; base préparée `29fc9d99bd6422865d59927e4af1b741a5768d47`. **6 commits en avance, 0 retard, 31 fichiers modifiés/créés**.
- Lecture de `src/pokemind/{cards,collection,recommendations,lessons,candidates,capabilities,database,cli}.py`, de tests `test_{cards,collection,candidates,lot_b_e2e}.py`, des documents RESULT/HANDOFF/NEXT_ACTION et de la matrice d'acceptation.
- Arbre Git complet **162 entrées, truncated=false**, aucun chemin privé SQLite, deck, collection, journal, image, backup ou secret détecté. Inspection des chemins ne garantit pas absence de secret dans tout l'historique.
- **Aucun statut CI ni workflow PR** attaché au commit. Baseline 230, **256 tests réussis en 48,41 secondes**, compilation/diff check, migration/restauration synthétiques, base personnelle toujours schéma 7 et byte-identique sont **rapportés par Codex seulement**, non exécutés indépendamment sous Windows par ChatGPT. Aucun merge.

## B0 conforme au périmètre
`CatalogApiClient._reserve_get` et `_SafeRedirectHandler` débitent chaque GET initial/retry/redirect avant transmission; `_validate_public_api_url` vérifie HTTPS/hôte/port/credentials/fragment/chemin public/langue/paramètres sur URL initiale, redirect et finale. Tests synthétiques de budget 1, redirects refusés et 429. Pas de certification exhaustive de la pile HTTP réelle.

## B1 conforme comme mécanisme — données déclaratives
Import JSON daté `owner_provided`, quantités, identité locale et ambiguïtés, snapshots et rollbacks, crédits déclarés sans achat, preview lecture seule et `--apply --confirm-owner`. Schéma SQL 10 additif et tests de sauvegarde synthétiques. **Aucune vraie collection ni montant de crédits importés.** Distinction copie exacte/variante et caractère partiel du snapshot à renforcer si l'absence d'une entrée risque d'être interprétée comme absence de possession.

## B2 : DÉFAUT TEMPORALITÉ C0-1 (correctif obligatoire)
`recommend_deck(db, deck_id, as_of=DATE, ...)` utilise bien cette date pour `analyze_deck` et `battle_lessons`, **mais consulte les derniers `collection_status`, `credits_status` et `collection_missing` sans borne historique**. Exemple : captures propriétaire collection/crédits du 2026-10-13, puis demande historique `recommend deck --as-of 2026-05-01 --collection`; la réponse peut présenter des avoirs d'octobre comme connus en mai.
**C0-1** : filtrer provenance par `as_of` ET date de capture locale `recorded_at`, suivre les rollbacks, ne pas substituer un vieux snapshot sans justification; à défaut répondre `unknown/NOT_AVAILABLE_AS_OF`. Tester deux snapshots, crédits, as_of ancien, date future, rollback et absence de données. Éviter de divulguer les montants dans Git.

## B3 conforme pour les faits des journaux
`battle_lessons` compte événements réellement reconnus côté joueur avec `n_battles`, sépare hypothèses/faits et liens de version attestés, évite la causalité inventée. Notes propriétaires volontaires `--apply --confirm-owner`; tests synthétiques seulement. Un journal n'établit pas la liste complète ni les cartes possédées.

## B4 : DÉFAUTS STRUCTURELS C0-2 (correctifs obligatoires)
`_validate_candidate` rejette `REJECTED_STRUCTURE/CANDIDATE_SECTION_EMPTY` **si aucune Énergie OU aucun Dresseur**, même si les règles vérifiées imposent seulement 60 cartes, nombre/copies autorisés et au moins un Pokémon de base, **sans obligation de contenir les trois catégories**. Un deck avec 60 cartes admissibles, au moins un Basic mais zéro Énergie est faussement rejeté. Tester cas zéro Énergie et zéro Dresseur avec >4 noms différents, et conserver `unknown` si preuve manquante.
`_resolve_card` vérifie nom/code/numéro mais **ne vérifie pas systématiquement que la catégorie TCGdex correspond au `card_type` déclaré par l'utilisateur**; risque de marquer `READY_FOR_REVIEW` un candidat mettant un Pokémon dans la catégorie Dresseur. Ajouter test catégorie contradictoire, ambiguë et absence de preuve, puis interdire tout statut prêt à réviser indûment. Conserver séparation candidat / version jouée et export TXT volontaire dans `drafts` si légalité `unknown`; aucune transmission au jeu.

## B5 : mécanisme livré avec validation externe non démontrée
CLI/skill portable `deck-advisor`, `capability status` sans affichage du montant, E2E synthétiques collection/5 combats/attestation/conseil/candidat/export, export corrigé sous `data/local/test-runs`. Le validateur officiel du skill était bloqué par `PyYAML` absent : seule validation locale équivalente attestée.

## Suite sans réduction de périmètre
Conformément à la demande expresse de l'utilisateur, **pas de microbranche B-R1**. Préparer **LOT C grand lot autonome**, avec **C0 corrections B2/B4 comme premier chantier**, puis coach visuel d'entraînement avec captures volontaires éphémères, reconnaissance conservatrice, mémoire textuelle de partie et conseils tour par tour sourcés. **C0 doit être testé et corrigé avant toute séance réelle**; si échec, suspendre la fonctionnalité à risque avec PARTIAL/BLOCKED et expliquer, sans l'abandonner.
LOTS D (actualisation quotidienne et mardi/vendredi, scheduler seulement après opt-in) et E (backups, sécurité, E2E/stabilisation) restent intégralement prévus. Les données publiques incomplètes LOT A et conseils conditionnels LOT B restent au backlog, jamais faussement DONE. Pas de merge, compte Pokémon, dépenses, édition réelle de collection/deck/combats, publication privée ni installation automatique de service.
