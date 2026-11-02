# PM-V1-OFFLINE-COMPETITIVE-ADVISOR-001 — EXÉCUTÉ / AWAITING_AUDIT

**Clôture Codex2026-10-22 :lot exécuté,autorisation consommée.**
Voir `../EVIDENCE_PM-V1-OFFLINE-COMPETITIVE-ADVISOR-001.md`,STATE etpremier NEXT_ACTION.
Prochain geste :audit indépendant ChatGPT,V1 NOT_RELEASE_READY.

## Mandat initial conservé pour audit

**Autorisation de progression PUBLIQUE ordinaire donnée par le propriétaire le 2026-10-22 (D-196).** Exécuter le **lot fonctionnel complet**, sans micro-go, dans Codex ou Claude Code démarré manuellement. **Zéro GET nouveau, zéro installation, aucune donnée personnelle.**

## Résultat utilisateur exigé
Transformer les 32 listes de deux tournois déjà récupérées en **comparateur/choix de decks réellement utilisable hors ligne** dans le CLI de PokeMind. Ne pas fabriquer un taux de victoire, ni privilégier arbitrairement un deck au seul motif d'une place de tournoi. V1 `NOT_RELEASE_READY`.

### A. Prévol/architecture
Vérifier `git status`, branche `work/pm-v1-lotj-final-readiness-windows`, fetch/pull `ff-only` **sans perte** et CI du HEAD autorisant ce mandat (deux jobs au SHA); attendre son succès si non terminé avant travail fonctionnel. Lire AGENTS.md, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, le premier NEXT_ACTION, HANDOFF, RESULT, PROJECT_SPEC et skill exécuteur. Réutiliser `competitive.py`, `decks.py`, `candidates.py`, `deck_exports.py`, modules meta et DB PUBLIC plutôt que dupliquer des moteurs. Ne pas afficher/lire la base personnelle par défaut.

### B. Outil de comparaison local PUBLIC
Ajouter une ou plusieurs commandes CLI minimales, **avec `--db` PUBLIC explicite**, pour :
- inventorier les **compositions réellement distinctes** (pas compter deux fois une URL/liste réutilisée), archétypes, éventail de placements, dates/événements, identité source et qualité de données;
- comparer deux listes 60/60 par quantités/identités de cartes sourcées (partagées, retirées, ajoutées, stratégie de construction) et exporter séparément l'une ou l'autre avec le sérialiseur déjà `FIELD_VALIDATED` historiquement;
- produire une **shortlist de 2–4 options réellement différentes**, avec Dragapult comme base et Basic Box/Hydrapple/Dhelmise comme exemples si disponibles, en marquant explicitement ce qui est une hypothèse de plan de jeu (évolutions, énergie, soutien, échange des Récompenses) et ce qui n'est **pas** connu (matchup, winrate, BO1/BO3, TCG Live, inventaire/crédits, compatibilité à date). Aucun score ou classement de force inventé; pas de « bat Dragapult X% » sans match data.
- garder une sortie lisible par humain et JSON courte, pointeurs URL/source/date, sans info personnelle.

### C. Fiabilité et validation sans nouvelle collecte
Réutiliser exclusivement les **pages PUBLIC complètes déjà cachées** et les données SQLite PUBLIC que le propriétaire a autorisées dans le mandat compétitif. **Aucun `get`, navigateur, API, web ni téléchargement** dans ce lot. Si le cache PUBLIC requis est absent, présenter `BLOCKED_WITH_REASON`, mais ne pas recommencer la campagne précédente.
- Vérifier non-mutation des commandes, absence de fallback au propriétaire, contraintes de 60 cartes, comptage dédupliqué, échantillon top16 biaisé, liens source et comportement sur données manquantes/ambiguës. Tester avec **fixtures synthétiques uniquement dans Git/CI**, jamais les listes réelles.
- Sur le PC dans Codex, lorsque le chemin du cache PUBLIC est explicitement celui du rapport antérieur, tester la vraie commande de comparaison **en lecture seule** et reporter des chiffres assainis `CODEX_LOCAL_REPORTED`. Ne modifier, migrer, fusionner ni purger ce cache. Les exports complets restent localement; aucune liste complète ou donnée propriétaire dans Git.
- Exécuter suite complète, compilation, hygiène Git, diff; corriger de façon autonome les erreurs ordinaires du lot.

### D. Livraison/STOP
Publier modifications de code, tests, documentation pratique (commande pour comparer les listes et choisir un autre deck), `.orchestrator/RESULT.md`, `HANDOFF.md`, `NEXT_ACTION.md`, `STATE.json` et décisions si nécessaire, dans **la même branche**; preuves assainies seulement. Après commit, vérifier le HEAD et les deux CI au SHA exact (si pending, dire pending), puis **`AWAITING_AUDIT` / STOP**. **Ne pas demander de nouveau « go » au milieu du lot.**

## Exclusions continues
Aucun GET/robots/réessai de fournisseur (budget de ce lot **0**), pas de cache brut dans Git, ni deck/collection/journal/SQLite personnels; aucune connexion au client Live, OCR/capture, achats/crédits, système/Windows scheduler, installation, backup, migration, restauration, purge, reset, merge ou force push. Ne pas modifier les decks joués. Une commande explicitement déclenchée par l'utilisateur dans un futur mandat personnel reste distincte. Préserver les autres exigences V1; `NOT_RELEASE_READY`.
