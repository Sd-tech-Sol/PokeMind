# PM-V1-REST-FR-EN-COVERAGE-001 — Couverture REST publique FR/EN, campagne nouvelle bornée

**Statut : READY pour relais manuel Codex uniquement.** But : convertir le choix vérifié du REST TCGdex en progression mesurable du catalogue public EN/FR, sans ajouter d'outils, réécrire les adaptateurs, consulter le matériel privé, ni rejouer les anciennes campagnes. La totalité V1 reste obligatoire, même si ce lot n'en clôt qu'une partie.

## A — Prévol obligatoire

1. Branche `work/pm-v1-lotj-final-readiness-windows`. Contrôler `git status`, `git fetch` et `git pull --ff-only` seulement si sûr, sans reset/force-push. Lire AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, le **premier** NEXT_ACTION, HANDOFF/RESULT/DECISIONS, le présent mandat, skill exécuteur, AUTONOMY_POLICY, matrice J et preuves PUBLIC/BULK/alternatives.
2. Identifier exactement `PM-V1-REST-FR-EN-COVERAGE-001` READY, `execute_now=true`, `consumed=false`, et **CI Windows ET Ubuntu `completed/success` au SHA HEAD documentaire courant**. Si `queued` / `in_progress`, règle `WAIT_CI_NO_FUNCTIONAL_WORK` : vérifications ponctuelles espacées d'au moins30s, attente bornée25min, zéro travail fonctionnel. Si échec/annulé/absent/timeout/HEAD changé, STOP assaini.
3. Vérifier dans les éléments versionnés existants les autorisations, attribution, conditions d'utilisation et plafonds du **seul REST TCGdex**; aucune recherche externe hors du budget autorisé. En cas de conditions incertaines ou d'interdiction, STOP `BLOCKED_WITH_REASON` avant toute requête. Aucun usage du client Pokémon Live, ni pages officielles, Limitless, Trainer Hill, images ou règles sans nouvelles permissions distinctes.
4. Lire et comprendre **avant toute exécution** les fichiers `src/pokemind/public_campaign.py`, `src/pokemind/cards.py`, `src/pokemind/catalog_snapshots.py`, `src/pokemind/public_card_selection.py`, `scripts/lot_i_public_campaign.py`, tests et compteurs. Ne créer aucun nouveau programme/service/SDK/planificateur. Faire prévol/dry-run sans réseau ni base privée.

## B — Plan de collecte explicitement neuf

- **Budget propriétaire de ce seul mandat : au plus 192 HTTP GET publics TCGdex**, répartis en **huit invocations CLI maximum de 24 GET chacune**. Un appel à un endpoint compte même en échec; aucun dépassement, retry non compté ou cumul implicite d'un ancien mandat. Intervalle réseau existant au moins0,5s; timeout et arrêt sur 401/403/429/challenge; ne jamais contourner ni inventer une permission de service. Si l'endpoint ne peut pas garantir cette comptabilité, STOP.
- Créer **un nouvel espace PUBLIC isolé** via le mécanisme versionné, avec nom neuf dérivé de `PM-V1-REST-FR-EN-COVERAGE-001`; aucune inspection/copie/sélection d'une SQLite existante, personnelle ou d'une ancienne campagne. La création doit être exclusive : si un espace portant ce nom existe, STOP pour choix d'un autre nom explicitement neuf, sans remplacement.
- Répartir au plus quatre premières invocations pour **l'index EN/FR** (sets et cartes), puis au plus quatre pour **les détails EN/FR** si les index rendent des éléments éligibles. Chaque invocation avec `--tcgdex-budget 24 --meta-budget 0 --official-budget 0`, phase explicitement `index` ou `details`; initiale `--create`, toutes les actions réseau uniquement via `--execute-public-campaign` à l'intérieur de cette permission bornée. Ajuster à la baisse si aucun progrès, quota ou terminologie droits douteuse; jamais changer de source/phase vers collecte non autorisée.
- La collecte ne peut **pas** utiliser `--db` pour pointer une vraie DB, fichiers de decks, captures, logs ou backups. Les réponses fournisseur restent uniquement dans l'espace PUBLIC ignoré par Git; pas d'archive, image, binaire, script distant, téléchargement bulk ou publication du brut.

## C — Mesures, qualité et arrêt fail-closed

Produire pour chacune des invocations un résumé **assaini et agrégé** : GET tentés/réussis/refusés, index EN/FR, set/card scans `completed` ou `partial`, union d'impressions et détails présents/absents par langue, collisions, erreurs, dénominateurs réellement mesurés, stale, et statut de source. Interpréter 404 comme absence attestée par requête, pas comme absence universelle; ne jamais annoncer 100%, Standard/Live legal ou réimpressions équivalentes sans norme officielle. Préserver provenance, dates et hash local public sans publier chemins/hashes privés.
- Arrêt immédiat si erreur d'accès, compteurs incohérents, pagination dupliquée, fuite, répertoire ambigu, comportement non attendu ou source dont les droits ne sont pas validés. Aucun autre GET après blocage ni relance de campagne consommée.
- Évaluer honnêtement gain par GET et les trous restants; préparer un plan pour la suite **sans autoriser automatiquement une autre campagne**.

## D — Tests et contrôles sans réseau en CI

Réutiliser les tests existants, en ajoutant seulement si un défaut spécifique observé le requiert (quota, reprise, snapshots, provenance). Aucun code produit ne doit changer pour maquiller un résultat fournisseur; correction ordinaire seulement si la preuve et la portée la justifient. Tests synthétiques ciblés + suite complète locale Windows, compilation, hygiène Git, diffcheck, git status; aucun vrai corpus fournisseur dans fixtures/CI. Conserver la CI Ubuntu seulement pour régression, pas d'extension produit Linux.

## E — Livraison, preuve et STOP

Publier un rapport nouveau `.orchestrator/EVIDENCE_PM-V1-REST-FR-EN-COVERAGE-001.md` avec les compteurs réels mesurés, comparaison avant/après dans **la seule nouvelle campagne**, les limites et l'arrêt, et mettre à jour la matrice J sans agréger artificiellement les anciennes campagnes. Mettre `STATE/RESULT/HANDOFF/NEXT_ACTION/DECISIONS` cohérents au même ID, `AWAITING_AUDIT`, `execute_now=false`, autorisation consommée uniquement si collecte effective; documenter les éventuelles tentatives 0 en cas de STOP. Commit/push non destructifs sur la branche autorisée, vérifier CI Windows/Ubuntu au SHA final et STOP audit ChatGPT. Aucun mandat suivant préparé par Codex.

**Interdictions** : aucun contact de fournisseur autre que TCGdex dans cette tâche, aucun nouveau stockage privé, aucun achat, OCR, scheduler Windows, client Live, import de deck personnel, vrai backup/clone/restore/migration, metadata personnelle, merge, reset destructif ou force-push. Si tout se passe bien, succès de la campagne **ne vaut jamais `RELEASE_READY`**. Ancien mandat alternatives et budgets antérieurs consommés, non rejouables.
