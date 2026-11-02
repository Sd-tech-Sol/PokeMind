# VERIFICATION_PM-0004B-R1 — Audit indépendant ChatGPT (2026-10-11)

## Verdict
**ACCEPTÉE en revue statique indépendante pour la correction ciblée.** Un état TCGdex `absent` après HTTP 404 survit au rafraîchissement de l'index; aucun détail absent n'est recontacté sans `--recheck-absent`. Cette revue n'est **pas** une exécution indépendante de pytest sur Windows ni une preuve de catalogue complet.

## GitHub vérifié
- Branche `work/pm-0004b-r1-absent-status`, SHA livré `2641e4d5e7805796832d8e616b94aac892ff73af`; parent `9e8d0ca00eb52c984ba92485675e8940ad523980` : **un commit, sept fichiers changés**, code modifié uniquement dans `src/pokemind/cards.py`.
- `_upsert_card_brief` garde les états `present` **et** `absent`, avec `last_error`; un changement de nom bref n'efface plus la preuve d'une 404.
- `_pending_card` exclut `t.status='absent'` malgré `detail_stale=1`, sauf avec `recheck_absent=True`; `_pending_set` fait de même pour les extensions.
- Les transitions 404→404, puis 404→200 et le rafraîchissement d'un détail `present` périmé restent opérationnels selon le code.
- Nouveau test `test_refresh_preserves_verified_absence_until_explicit_recheck` paramétré EN/FR × cartes/sets : **4 scénarios**, brief inchangé/changé, zéro GET implicite, recheck demandé, couverture, stale, retour à `present`.
- Arbre Git complet **105 entrées**, `truncated=false`, aucun fichier SQLite, backup, deck, journal, capture ou contenu privé sous `data/local/` trouvé.
- GitHub : **aucun statut CI / workflow PR** retourné pour ce commit. `89 passed` avant et **`93 passed` après** sont **rapportés par Codex**, pas exécutés par ChatGPT. Compilations, diff, intégrité SQLite et absence de modification de la base privée sont rapportés, non directement vérifiables.

## Limites
Le cache est très partiel (223 sets, 602 impressions, 973 traductions, **quatre détails par langue** selon Codex). La complétude globale et la légalité TCG Live ne sont pas établies; pas d'automatisation quotidienne. Les deux anciens journaux sans original restent non réanalysés. Aucun merge ni PM-0005 n'a été lancé.

**Remarque de structure vérifiée :** la branche GitHub par défaut est `work/pm-0001`. La branche `main` n'existe pas selon l'API à la date de cet audit. Toute future procédure d'intégration doit tenir compte de ce fait; ne pas prétendre avoir comparé ou fusionné avec `main`.

## Suite
PM-0004B-R1 est **clôturable**. Aucune nouvelle tâche Codex n'est autorisée par cet audit seul. Suite à décider explicitement : approfondissement du catalogue et de sa couverture, puis règles officielles/légalité et données compétitives par étapes; ajouter une CI si souhaité.
