# Matrice d’acceptation — LOT B

Date d’exécution : 2026-10-13. Branche :
`work/pm-v1-lotb-personal-deck-advisor`. Cette matrice décrit la livraison Codex;
elle ne constitue pas une vérification indépendante et n’emploie pas le statut
`VERIFIED`.

## Résumé

| Chantier | État | Preuve principale |
|---|---|---|
| B0 — redirects et quota TCGdex | `DONE` | `src/pokemind/cards.py`, `tests/test_cards.py` |
| B1 — collection et crédits volontaires | `DONE` pour le mécanisme; données réelles non appliquées | `src/pokemind/collection.py`, `tests/test_collection.py` |
| B2 — recommandations prudentes | `PARTIAL_WITH_EVIDENCE` | `src/pokemind/recommendations.py`, `tests/test_recommendations.py` |
| B3 — leçons de combats | `DONE` pour le mécanisme; attribution réelle partielle | `src/pokemind/lessons.py`, `tests/test_recommendations.py` |
| B4 — candidats distincts et export | `DONE` pour le mécanisme; légalité réelle partielle | `src/pokemind/candidates.py`, `tests/test_candidates.py` |
| B5 — parcours, statut et E2E | `DONE`, sauf validateur externe du Skill | `.agents/skills/deck-advisor/SKILL.md`, `tests/test_lot_b_e2e.py` |

## B0 — client TCGdex

| Exigence | État | Preuve et limite |
|---|---|---|
| URL initiale, redirection et URL finale soumises à la même allowlist | `DONE` | HTTPS, hôte exact, aucun credential/port/fragment et seulement `/v2/{en|fr}/{cards|sets}[/ID]`; paramètres de liste bornés. |
| Un débit avant chaque GET réel, incluant retry et redirect | `DONE` | `_reserve_get`; tests de redirect sûr, bloqué et quota épuisé avant transmission. |
| 429/Retry-After, 404, reprise et cache existants conservés | `DONE` | Suite `tests/test_cards.py`, entièrement simulée sans réseau. |
| Sync publique substantielle | `PARTIAL_WITH_EVIDENCE` | Non requise et non lancée dans ce lot; la couverture TCGdex réelle demeure celle du LOT A. |

## B1 — collection et crédits

| Exigence | État | Preuve et limite |
|---|---|---|
| JSON propriétaire déterministe, daté et versionné | `DONE` | Impression, set, numéro, variante, quantité et états `confirmed_owned`, `reported_missing`, `unknown`; schéma documenté dans `docs/LOT_B_GUIDE.md`. |
| Alias FR/EN, identité exacte et ambiguïtés | `DONE` | Résolution locale seulement; conflit ou absence reste `ambiguous/unknown`, sans substitution par nom. |
| Preview/statut/couverture/manquants en lecture seule | `DONE` | Le dry-run peut fonctionner sans créer la base; cartes du deck jamais converties en possession. |
| Apply explicite, transactions, historique et rollback | `DONE` | `--apply --confirm-owner`, schéma 10 additif, sauvegarde SQLite avant migration, un instantané actif et historique conservé. |
| Crédits déclarés et datés, sans dépense | `DONE` | Set/statut/rollback; `credits_spent=0`. |
| Tarif de fabrication actuel et disponibilité après fabrication | `BLOCKED_WITH_REASON` | Aucun tarif officiel actuel, versionné et sourcé n’est disponible dans le dépôt; `craft_cost` et disponibilité restent `unknown`. |
| Import de la vraie collection ou des vrais crédits | `BLOCKED_WITH_REASON` | Interdit pendant le développement; aucune écriture n’a été faite sur la base privée. Action distincte du propriétaire requise. |

## B2 — recommandations

| Exigence | État | Preuve et limite |
|---|---|---|
| Commande datée et hors ligne | `DONE` | `recommend deck ... --format --platform --as-of [--collection]`; lecture seule et aucun réseau. |
| Couches de preuves séparées | `DONE` | Règles officielles, textes TCGdex, Limitless, observations personnelles et hypothèses sont séparés. |
| Refus d’inventer une synergie, un remplacement ou un coût | `DONE` | Sans preuve, `INSUFFICIENT_EVIDENCE`, changement vide et prochaine preuve utile. Une référence textuelle n’est pas promue en preuve stratégique. |
| Candidats conditionnels étayés | `PARTIAL_WITH_EVIDENCE` | Le moteur sait proposer le retrait d’un dépassement de copies démontré, mais laisse le remplacement inconnu. Les effets, identités, légalité et méta réels restent incomplets. |
| Matchups personnalisés | `BLOCKED_WITH_REASON` | Aucun mapping prouvé entre le deck local et un archétype publié; sortie `unknown`, `n=0`, sans taux inventé. |
| Conseil tenant compte d’une vraie collection/crédits | `PARTIAL_WITH_EVIDENCE` | Parcours synthétique testé; aucune déclaration réelle n’a été importée et aucun tarif sourcé n’existe. |

## B3 — leçons de combats

| Exigence | État | Preuve et limite |
|---|---|---|
| Faits, hypothèses, inconnues et questions de revue | `DONE` | Seulement les événements reconnus; aucun contenu caché ni causalité automatique. Chaque récurrence expose `n_battles`. |
| Dénominateurs et attestations de version à la date ciblée | `DONE` | Comptes séparés `owner_attested`, `legacy_unattested` et `unlinked`; révocations historiques respectées. |
| Notes locales validées, idempotentes et consenties | `DONE` | Preview par défaut, `--apply --confirm-owner`, provenance `owner_validated`, déduplication et source publique optionnelle. |
| Conclusions sur les cinq vraies parties | `PARTIAL_WITH_EVIDENCE` | La base privée contient cinq parties valides mais aucune attestation de version; elles restent exploratoires et non attribuables à la version jouée. |

## B4 — candidats de 60 cartes

| Exigence | État | Preuve et limite |
|---|---|---|
| Proposition distincte du deck joué | `DONE` | Table et cycle de vie séparés; créer/exporter un candidat ne crée aucune `deck_version`. |
| Total 60, sections, Basic, limites et identités | `DONE` | 59/61 rejetés; section vide, absence de Basic prouvée et cinquième copie prouvée rejetées; reprints exacts conservés. |
| Légalité complète | `PARTIAL_WITH_EVIDENCE` | `READY_FOR_REVIEW` exige règles complètes, identités résolues et toutes les cartes légales; sinon `UNKNOWN_LEGALITY`. La base privée au schéma 7 n’a pas le registre de structure. |
| Export TXT/rapport volontaire sous `data/local` | `DONE` | Preview sans fichier, apply confirmé, aller-retour parseur à 60; aucun presse-papiers, compte, achat ou envoi au jeu. |
| Candidat réel du propriétaire | `BLOCKED_WITH_REASON` | Non créé ni exporté pendant ce lot conformément à la séparation des données privées. |

## B5 — navigation, sécurité et qualité

| Exigence | État | Preuve et limite |
|---|---|---|
| Skill portable `deck-advisor` et guide FR Québec | `DONE` | Commandes Python/Markdown sans framework d’agents; garde-fous propriétaire et `unknown` explicites. |
| Validateur officiel du Skill | `PARTIAL_WITH_EVIDENCE` | `quick_validate.py` ne peut démarrer sans le module externe PyYAML. Aucune dépendance installée; frontmatter minimal vérifié par test local. |
| Statut des capacités sans divulguer le montant | `DONE` | `capability status` compte objets, dates et lacunes en lecture seule; `amount_disclosed=false`. |
| E2E collection → combats → conseil → candidat → export | `DONE` | Scénario entièrement synthétique, isolé sous `data/local/test-runs`; 0 puis 5 combats, avec et sans attestation. |
| Confidentialité Git et API | `DONE` | Seul `data/local/.gitkeep` est suivi; aucun binaire/log privé ou motif de secret détecté; aucun appel réseau de données personnelles. |

## Preuves d’exécution

- Baseline LOT A déclarée : 230 tests. Résultat LOT B : **256 tests réussis en
  48,41 s**.
- `python -m compileall -q src tests` et `git diff --check` : réussis.
- Migration/restauration synthétiques ciblées : 2 tests réussis; intégrité de la
  sauvegarde et conservation des sous-systèmes vérifiées.
- Base privée : schéma 7, `PRAGMA integrity_check=ok`, zéro violation FK, FTS5
  interrogeable et SHA-256 identique avant/après les diagnostics. Elle n’a pas été
  migrée.
- Incident corrigé dans le lot : le premier E2E exportait ses fichiers synthétiques
  dans le dossier de drafts global. L’export avec `--db` sous `test-runs` est
  maintenant isolé près de cette base; les deux artefacts synthétiques ont été
  retirés et la suite complète repasse.
- Checkpoints fonctionnels : `0b1981d` (B0), `1478aab` (B1), `d4eaca2` (B2/B3),
  `cf12bfb` (B4), `bc96418` (B5).

## État réel et suite

Le mécanisme B0–B5 est livré. La base privée n’a ni collection/crédits déclarés, ni
attestation combat-version, ni règle de structure migrée, ni archétype méta classé;
les sorties correspondantes restent donc partielles ou bloquées avec raison. Les
LOTS C, D et E, la couverture incomplète du LOT A et Trainer Hill demeurent au
backlog. Arrêt requis ici pour audit indépendant.
