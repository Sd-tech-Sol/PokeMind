# PM-V1-PUBLIC-DECK-FIELD-QA-001 — READY

**Mandat PUBLIC ordinaire autorisé par D-196.** Objectif : vérifier les listes et fiches tactiques existantes sur des caches compétitifs PUBLICS locaux, corriger uniquement les défauts constatés et produire un parcours réellement utilisable « liste sourcée → plan de jeu → export60 ». Pas de second moteur/dependance, V1 NOT_RELEASE_READY.

## Prévol
Synchroniser `work/pm-v1-lotj-final-readiness-windows` par `fetch/pull --ff-only` sans perte; lire AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, **premier NEXT_ACTION**, HANDOFF/RESULT/DECISIONS, skill exécuteur, audit `VERIFICATION_PM_V1_OWNER_SELECTED_MATCH_REVIEW_UX_001.md`, issue #1, matrice V1 et **tout le présent mandat**. Confirmer les deux CI du HEAD READY avant travail.

**Seuls caches PUBLICS consultables en lecture seule, s'ils sont présents exactement (docs/DECK_INTELLIGENCE.md) :**
- `data/local/public-campaigns/lot-i-competitive-20261022/public.sqlite3`
- `data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3`

Ne pas scanner `data/local`, chercher d'autres caches/DB, deviner des chemins ou ouvrir tout autre contenu. Si un fichier manque, documenter le blocage terrain puis ne travailler que sur fixtures synthétiques.

**Zéro GET fournisseur, zéro réseau Pokémon ou jeu.** Aucun vrai deck joué/collection/crédit/journal/base personnelle/image, sauvegarde, OCR, compte, presse-papiers, planificateur, installation, restauration, migration, purge, merge, reset destructif ou force-push. Parties tests inventées uniquement.

## Résultat concret
1. Inventorier les compositions/placements réellement présents en cache PUBLIC (32 listes/28 compositions sont des anciens chiffres rapportés par Codex, **à revérifier**). Pour chaque liste, provenance/événement/date, export 60/60 reparsé, inconnu/ambiguïté et liens d'identité. Ne pas inventer les sept correspondances d'Énergie MEE encore inconnues.
2. Valider `competitive_export`, `deck_library`, `deck_knowledge`, `public_deck_preflight`, `counter_deck` sur au moins quatre archétypes distincts disponibles (Dragapult, Basic Box, Hydrapple, Dhelmise si présents) puis le reste des listes avec vérifications automatisées read-only.
3. Pour un deck choisi, le rapport doit expliquer clairement **comment le jouer** : setup/ouverture, pioche et recherche, évolution et Énergie, attaques/conditions, plan de K.O./Récompenses et contre-jeu conditionnel. Ancrer les suggestions au texte natif daté et source PUBLIC; `unknown` pour effets/règles/Live/présentiel/BO non démontrés. Aucune promesse de matchup, winrate ou combo garanti.
4. Améliorer seulement les défauts produits observés; ne pas construire nouveau service, stockage, crawler, ML ou automatisation. Vérifier CLI humaine et JSON sous Windows (Unicode/CP1252), export60 copiable **manuellement**. Toute intégration avec `battle review-selected` doit utiliser une DB et des journaux **fictifs**.
5. Produire `docs/PUBLIC_DECK_FIELD_QA.md`, un exemple joueur reproductible et preuves assainies avec vrais dénominateurs PUBLIC, erreurs, unknowns, source/temps, contrôle non-mutation des deux caches, 0GET et absence de tout contenu personnel versionné. Observation PC = `CODEX_LOCAL_REPORTED`.
6. Full tests + ciblés, hygiène/compilation/diffcheck, CI Windows et Ubuntu au **SHA final**; tenir à jour STATE/NEXT_ACTION/NEXT_PROMPT/HANDOFF/RESULT/DECISIONS et documents V1. Commit/push assainis sur branche active, puis `AWAITING_AUDIT`, `execute_now=false`, `consumed=true`, STOP ChatGPT. Pas de tâche suivante créée par Codex.
