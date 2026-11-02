# PM-0005B-R1 — audit d'intégrité de synchronisation

**Date :** 2026-10-12
**Portée :** correctif synthétique, sans requête Limitless réelle ni migration SQLite.

## Diagnostic corrigé

1. La découverte reprenait toujours page 1 et traitait les premiers IDs, même déjà
   importés. Deux exécutions bornées pouvaient donc rafraîchir le même tournoi sans
   progresser.
2. `standings` et `pairings` étaient demandés avant de vérifier les détails publics,
   le jeu, le format, la plateforme, `isOnline` et l'annulation.
3. Une redirection vers un chemin protégé du même hôte n'était pas soumise à la même
   allowlist que l'URL initiale. Un reste de quota nul annoncé après une réponse 200
   n'empêchait pas le GET suivant.

## Choix R1

- `meta sync --mode discover` relit la tête, ignore durablement les snapshots sains et
  exclusions terminales, puis pagine vers les IDs inconnus. L'ensemble des IDs est la
  reprise durable; aucun numéro de page seul n'est considéré fiable.
- La pagination fournisseur n'est pas atomique. De nouveaux événements en tête peuvent
  déplacer les pages; la réanalyse de la tête et la déduplication inter-sessions
  réduisent ce risque, mais ne constituent pas une photo exhaustive du fournisseur.
- `--max-tournaments` borne les imports en découverte. Les candidats privés,
  incompatibles ou annulés consomment seulement `details` et laissent examiner les
  suivants tant que le budget de GET le permet.
- `meta sync --mode refresh` revalide explicitement les snapshots les plus anciens.
  Un événement devenu privé/incompatible passe à `snapshot_status=partial`; son
  historique reste local, mais toutes les agrégations courantes l'excluent.
- `details` est validé avant tout classement ou appariement. Les données participant,
  pseudos, pays, handles et decklists ne sont ni journalisées ni persistées.
- Une fonction unique valide URL initiale, redirection et URL finale. Seuls les GET
  publics minimaux sont acceptés; `/api/games/{id}/decks` reste interdit. Chaque GET
  suivi par redirection est débité du budget avant sa transmission; budget ou quota
  fournisseur épuisé bloque donc la destination.
- `RateLimit` et `X-RateLimit-Remaining` parsables sont respectés. Un reste zéro donne
  `rate_limited` avant transmission d'un autre GET; un en-tête absent ou malformé ne
  crée pas de quota inventé.

## Preuves reproductibles

Les fixtures utilisent uniquement des IDs et participants synthétiques. Les tests
R1 couvrent : deux sessions sur une première page de six IDs; insertion d'un nouvel
événement en tête puis reprise page 2; refresh d'une correction; ancien snapshot
devenu privé; candidat privé suivi d'un candidat public; quota 200 restant zéro;
redirection même hôte vers endpoint protégé et redirection hors hôte; URL finale
protégée; GET de redirection compté et bloqué avant transmission si budget/quota
épuisé; mauvais jeu ou mode online; timeout/503/retries bornés; taille et JSON;
en-têtes quota malformés; repli offline; absence de données privées persistées.

Commandes de vérification :

```powershell
python -m pytest -q
python -m compileall -q src tests
git diff --check
python -m pokemind status --json
python -m pokemind meta status --json
```

Résultat Codex local : **157 tests réussis**. Le schéma reste 7; aucune migration R1,
aucune requête HTTP réelle et aucune modification du cache privé n'étaient nécessaires.
Cette livraison attend l'audit indépendant ChatGPT et ne se déclare pas `VERIFIED`.
