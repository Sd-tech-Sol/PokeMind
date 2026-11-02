# PM-V1-PUBLIC-DECK-LEGALITY-PREFLIGHT-001 — preuves assainies

Exécution manuelle du propriétaire le 22 octobre 2026 Québec, sans micro-go.
Les mesures sur les caches PUBLIC existants sont **CODEX_LOCAL_REPORTED**,
jamais une vérification indépendante du PC. V1 **NOT_RELEASE_READY**.

## Prévol et portée

- Branche `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre.
  Synchronisation fetch/pull ff-only sans perte de b51d08f à
  `d115596bb69130a971a42aa93988e1fb96ea5943`.
- STATE/NEXT_ACTION/mandat READY concordants, D-196 et ordre manuel courant.
  [CI39882736624](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39882736624)
  au SHA d115596 : **Windows805passed/2skipped** job120184007504,
  **Ubuntu804passed/3skipped** job120184007471, deux jobs completed/success.
  Les logs portent le SHA exact et les marqueurs `ci_evidence`,
  `competitive_advisor_evidence`, `competitive_pages_evidence`,
  `rules_registry_evidence`, lus avant toute opération fonctionnelle.
- `preflight --json` : RUNTIME_READY, Python3.13.15, SQLite3.50.4, FTS5 prêt,
  aucune base propriétaire ouverte, aucune écriture ni réseau par la commande.
- Deux bases PUBLIC déjà désignées par les rapports antérieurs : cache
  compétitif et catalogue-snapshot du 22 octobre. Chemins explicites,
  namespace/marqueurs/alias et tables propriétaires vides contrôlés par le
  mécanisme existant. Aucune fusion, copie ou migration des données.

## Livraison et réutilisation

| Exigence | Résultat et limite |
|---|---|
| Commande explicite | `meta competitive-preflight`, `--db`, `--reference-db`, `--as-of`, `--format standard`, `--platform in_person\|live`; sélection répétable ou shortlist2–4 |
| Réutilisation | Snapshot/sélecteurs/sources/shortlist de `competitive.py`, identités de catalogue et `check_card` de `rules.py`; extraction du contrôle de structure existant vers `check_deck_entries`, sans import de deck |
| Preuves par impression | Nom/set/numéro, identité résolue/ambiguë/inconnue, marque, quantités, verdict et raisons, textes de catalogue sourcés, assertions/errata/réimpression avec dates d'effet |
| Prudence | Règles absentes/incomplètes/futures, traduction non présente, classification de base absente/conflictuelle et identité ambiguë restent unknown; quotas de même nom normalisé sur impressions multiples |
| Résumé pratique | Quatre options, compteurs par ligne et copie, raisons et prochaine preuve; renvoi à l'export existant, aucune modification du jeu ou du deck joué |
| Cloisonnement | Deux bases PUBLIC en mode ro/query_only; aucune connexion privée, initialisation de base existante ou réseau |
| CI | Marqueur `public_deck_preflight_evidence` issu d'un test exécuté, filtré par liste fixe, rejeté si absent/dupliqué/falsifié; preuves antérieures conservées |

Le retour `legal` qualifie une preuve réglementaire dans son contexte seulement.
Live availability, possession, crédits, fabrication, matchups et readiness
d'import restent inconnus sans preuve. Un total60 ou une liste de tournoi
ne suffit pas. L'absence de restrictions et la rotation ne sont pas promues
en validation universelle. Les observations de catalogue ne sont pas une
certification rétroactive de texte ou une couverture complète des errata.

## Essai réel PUBLIC en lecture seule

Les quatre appels CLI humain/JSON sur les deux plateformes utilisent les
bases PUBLIC explicites. Pendant ces appels, socket/connect, urllib,
constructeur BoundedPages, connect_writable et les résolveurs par défaut
du CLI sont remplacés par des refus. **Zéro appel interdit observé**.

**52 fichiers PUBLIC contrôlés inchangés**, octets, taille et mtime : deux
bases et marqueurs, journal de pages et 47 corps complets référencés.
Les empreintes et rapports détaillés restent locaux, hors Git; seuls
les agrégats ci-dessous sont publiés. Les commandes ne créent aucun fichier.
Le harnais QA écrit ses propres rapports dans un espace ignoré distinct.

| Option | Copies | Lignes d'impression | Résolues | Statut présentiel | Statut Live |
|---|---:|---:|---:|---|---|
| Dragapult581:1 |60|24|0/24|unknown|unknown|
| Basic Box582:13 |60|28|0/28|unknown|unknown|
| Hydrapple581:7 |60|23|0/23|unknown|unknown|
| Dhelmise581:4 |60|22|0/22|unknown|unknown|

**97 lignes interoptions**, non dédupliquées entre decks, et240copies
inconnues sur chaque plateforme. Toutes les97 lignes portent
`SET_CODE_MAPPING_MISSING`. Une requête PUBLIC d'agrégation précise le
contexte :223extensions,118codes TCG Online renseignés,23864impressions;
aucun code demandé par ces lignes n'est mappé. Cela ne démontre pas
l'absence des impressions dans le catalogue historique. Aucune association
de set ou réimpression devinée. Les structures restent inconnues : entrées
non résolues, exceptions de quota et règles spéciales non exhaustives.

Prochaine pièce manquante : correspondance **sourcée** des codes d'extension
des options vers le catalogue PUBLIC; puis réévaluer les impressions et
compléter les règles manquantes dans un futur mandat audité. Aucun nouveau
mandat n'est créé ou lancé ici. Guide :
[`PUBLIC_DECK_LEGALITY_PREFLIGHT.md`](../docs/PUBLIC_DECK_LEGALITY_PREFLIGHT.md).

## QA synthétique

- **133 tests ciblés passés** : nouveau prévol, moteur rules, candidats,
  comparateur et publieur CI. Quatre options inventées, deux DB séparées,
  réimpression et errata, 60 cartes, restrictions, quotas, faux noms,
  ambiguïtés, traductions absentes, codes manquants, dates, sources futures,
  règles incomplètes, classifications inconnues/conflictuelles,
  absence de mutation et refus de réseau/DB privée.
- Le test d'intégration produit une propriété JUnit unique
  `public_deck_preflight_reproduction` :4decks60 synthétiques legal en
  présentiel,4unknown sur Live, preuves de réimpression/errata, deux bases
  PUBLIC inchangées, réseau interdit, aucun accès au propriétaire et aucune
  certification du vrai cache. Ces règles et impressions sont **inventées**.
- Les premières exécutions du nouveau harnais ont révélé des connexions
  de fixture non fermées sous Windows et un mauvais nom de point de patch
  CLI. Corrigés dans les tests avant QA finale; aucun cache réel concerné.
  Les résidus synthétiques ignorés de cette tentative n'ont pas été purgés.
- Compilation, hygiène Git et diff check réussis. Suite complète :
  **845passed/3skipped en343,56s**, Python3.13.15. Deux skips OCR non
  attesté et un symlink non permis sur ce Windows; aucun succès matériel déduit.

## Livraison, CI et STOP

Après QA complète, publier code/tests/docs et RESULT/HANDOFF/NEXT_ACTION/STATE
cohérents `AWAITING_AUDIT`, `execute_now=false`, `consumed=true`.
Inspecter les seuls fichiers préparés explicitement; aucun corpus brut,
SQLite, chemin absolu, donnée personnelle ou empreinte de données en Git.

CI finale **PENDING_AT_COMMIT** : le push crée la CI du HEAD contenant ce
rapport. Lire les deux jobs Windows/Ubuntu au SHA exact et les marqueurs
`public_deck_preflight_evidence`, `competitive_advisor_evidence`,
`competitive_pages_evidence`, `rules_registry_evidence`, `ci_evidence`.
GitHub Actions conserve leur résultat durable; la CI préalable ne remplace
pas celle de livraison. Aucun VERIFIED autoattribué; STOP audit ChatGPT.

**0 GET/recherche fournisseur**. Aucun ancien budget rouvert, acte privé,
OCR/capture, jeu/compte, OS/scheduler, installation, backup, migration,
restauration, purge, merge, reset ou force-push. Aucun test de presse-papiers
TCG Live historiquement FIELD_VALIDATED répété. Les autres objectifs de V1
sont conservés. **V1 NOT_RELEASE_READY**.
