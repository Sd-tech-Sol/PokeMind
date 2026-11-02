# Continuité de session — PokeMind (à lire en premier)

Version courte du 2026-10-29. L'ancienne version complète est archivée dans
[archive/2026-10](archive/2026-10/SESSION_CONTINUITY_avant_2026-10-29.md); les archives ne donnent aucune permission.

## Ordre de lecture (Codex, Claude Code, ChatGPT)
1. `AGENTS.md`, puis ce fichier.
2. `STATE.json` (état machine, court) et le **premier en-tête** de `NEXT_ACTION.md` = seul mandat actif.
3. `RESULT.md` (dernier mandat seulement), `HANDOFF.md`, haut de `DECISIONS.md`.
4. Plan de travail en cours : [`docs/audits/AUDIT_CLAUDE_2026-10-29.md`](../docs/audits/AUDIT_CLAUDE_2026-10-29.md) §10.

## Règles qui ne changent pas
- GitHub est la mémoire. Données personnelles, bases, journaux, captures, chemins absolus : **jamais** dans Git.
- Opérations sur les données personnelles (backup, migration, import, déplacement de `data/local`) : ordre explicite du propriétaire, par copie, jamais de suppression.
- Une tâche technique ne commence jamais par `python -m pokemind status/search` sans `--db` (base personnelle).
- V1 `NOT_RELEASE_READY` tant que les critères de publication (audit §9) ne sont pas remplis.

## Preuve technique (depuis le 2026-10-29)
- **Avant tout push de code** : `python scripts/local_gate.py` doit afficher `PORTE LOCALE : VERTE`.
  Elle copie le dépôt sans `data/local` dans un dossier temporaire court et rejoue compilation, hygiène,
  tests Qt et suite complète, hors ligne, en `offscreen` comme la CI. Rapporter les comptes exacts.
- Une sélection de tests n'est pas une preuve de livraison; la suite complète l'est.
- GitHub Actions : les commits docs seuls ne déclenchent plus la CI; Windows tourne sur PR ou à la demande.
  Si le budget Actions bloque un run, le dire; ne jamais présenter la porte locale comme une CI.

## Fin de mandat (court)
Mettre à jour `RESULT.md` (remplacé, pas empilé), `HANDOFF.md`, `NEXT_ACTION.md`, `STATE.json`, et `DECISIONS.md`
si nouvelle décision. **Un** commit de rapport par mandat. Les historiques vont dans `archive/AAAA-MM/`.
