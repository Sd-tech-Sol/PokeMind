# Audit indépendant — PM-V1-DECK-INTELLIGENCE-PUBLIC-FOUNDATION-001

**23 octobre 2026 (Québec). Verdict : `VERIFIED_GITHUB_CODE_CI_SYNTHETIC_SCOPE_ONLY`; chiffres du vrai cache : `CODEX_LOCAL_REPORTED`. V1 `NOT_RELEASE_READY`.**

## Contrôles distants indépendants

- Livraison [`9fc524285e1a15af9a136e8140357b30d4e39a80`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/9fc524285e1a15af9a136e8140357b30d4e39a80), HEAD confirmé de `work/pm-v1-lotj-final-readiness-windows`. Diff depuis l'audit antérieur `affe7ce4a153633bcb8c43ab3c972ce5198e2305` : **1 commit, 19 fichiers** (nouveau `set_code_aliases.py`, `deck_knowledge.py`, CLI, tests, docs, état). Aucune réécriture `main`, aucun merge/force-push connu.
- [Actions `39901283318`](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39901283318) : **`completed/success`**, event push au **SHA de livraison exact**, jobs et logs lus : **Windows** job `120243209157` **887 passed / 2 skipped** ; **Ubuntu** job `120243209550` **886 passed / 3 skipped**. Hygiène Git et `git diff --check` verts; skips hérités OCR et test propre à Windows.
- Les **deux journaux** contiennent `deck_knowledge_evidence` au SHA et run exacts : `scope=SYNTHETIC_PUBLIC_DECK_KNOWLEDGE_ONLY`, **4 fiches / 4 exports60**, pont sourcé, alias ambigu maintenu unknown, séparation faits/hypothèses, noms non devinés, cache synthétique inchangé, réseau bloqué et base propriétaire non ouverte. `real_public_cache_verified=false`. Preuves CI `public_deck_preflight_evidence`, `competitive_advisor_evidence`, `competitive_pages_evidence`, `rules_registry_evidence` et `ci_evidence` également conservées. Ce sont des tests construits, pas la certification des vrais textes ou decks Windows.
- Arbre Git distant **401 entrées non tronquées** ; seul `data/local/.gitkeep` suivi dans `data/local/`. Aucune base PUBLIC réelle, deck complet, fichier HTML de collecte, journal de parties, nom de joueur ou corpus texte en GitHub. Absence de publication ne garantit pas le comportement réel du PC.

## Revue technique

- `src/pokemind/set_code_aliases.py` : pont **optionnel, dérivé en mémoire**, depuis payload de set TCGdex présent et SHA vérifié + preuve d'origine (Git épinglé ou requête qualifiée), date de sortie et consultation non future, code d'abréviation et appartenance. Vérifie l'unicité de set avec le résolveur commun dans `rules.py`, et numéro/carte/nom dans le contexte. Ne modifie ni IDs TCGdex ni tables historiques. Collision de code ou preuve absente maintient `unknown`. Champ `abbreviation.official` est descriptif chez TCGdex, **pas certification réglementaire Pokémon**.
- `src/pokemind/deck_knowledge.py` : `meta deck-knowledge` exige les chemins compétitifs et référence PUBLIC, sélecteur/date, réutilise `competitive_preflight` et `competitive_export`, vérifie identité de composition et texte60. `verified_payload` + `payload_source` + provenance horodatée pour les textes natifs. Rôles détectés par motifs conservateurs de texte, inférences conditionnelles, hypothèses à tester, plans d'évolution, attaque, énergie et Récompenses. Les modèles `fact/inference/hypothesis_to_test/unknown` sont distincts; ce sont des pistes de stratégie, non une simulation certifiée de match ou une garantie de séquence légale. Sorties humaines et JSON, export **pour copie manuelle**, sans écriture clipboard/jeu.
- Tests `tests/test_deck_knowledge.py` et `tests/test_ci_rules_evidence.py` : scénarios de code faux/ambigu, provenance incompatible, payload falsifié/périmé, dates/sources, noms discordants, export60, absence de réseau ou écriture et restrictions des bases PUBLIC. Revue manuelle du code et CI n'ont pas révélé de motif bloquant dans leur **portée synthétique**.

## Chiffres locaux de Codex, hors certification GitHub

| Mesure | Avant | Après le pont (rapport PC) |
|---|---:|---:|
| Impressions uniques résolues | 0/69 | **62/69** |
| Lignes comptées par option résolues | 0/97 | **87/97** |
| Copies résolues cumulées | 0/240 | **201/240** |
| Lignes ambiguës par option | 0 | 0 |
| Verdicts legal / not_legal / unknown Standard en présentiel | 0/0/4 | **0/0/4** |
| Verdicts legal / not_legal / unknown Live | 0/0/4 | **0/0/4** |

- Les **7 impressions uniques/10 lignes/39 copies restantes** sont déclarées comme Énergies `MEE`; le fournisseur public affiche `… Energy` tandis que le nom TCGdex est `Basic … Energy`. Rien ne justifie de supprimer `Basic` universellement : aucune équivalence inventée. La résolution n'est pas une preuve de légalité; tous les decks restent `unknown`.
- **Quatre fiches pilotes** : Dragapult 21/24 lignes avec texte daté, Basic Box 23/28, Hydrapple 22/23, Dhelmise 21/22; quatre listes export60. Provenance TCGdex et Limitless, pas du texte officiel de règle complet. La description de stratégie est partielle et conditionnelle, `PARTIAL_WITH_EVIDENCE`. Ni matchmaking, winrate, classement absolu, disponibilité réelle dans Live, possession ni crédits certifiés.
- **94 fichiers PUBLIC inchangés, zéro GET/octets/découvertes**, instrumentation sans appels interdits, aucune DB du propriétaire ouverte : vérifications de Codex sur PC **non reproduites par ChatGPT**. L'enveloppe réseau non utilisée est clôturée et ne peut pas être reportée.
- La V1 reste en développement : jeux adverses, analyses des parties et stratégies anti-deck de l'[issue #1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1) toujours à construire, en plus des objectifs OCR/Windows/recovery déjà ouverts. Pas de répétition de l'essai TCG Live `FIELD_VALIDATED`.

## Verdict et passage de relais

**Acceptation technique limitée à la CI, au code et à ses fixtures : `VERIFIED_GITHUB_CODE_CI_SYNTHETIC_SCOPE_ONLY`.** Ne pas prétendre que les 62 résolutions réelles ont été vérifiées depuis GitHub ni que les quatre decks sont légalement jouables.

Selon la demande propriétaire D-196 d'avancer **sans micro-go** sur les lots ordinaires, prochain mandat `PM-V1-DECK-LIBRARY-MATCHUP-FOUNDATION-001` `READY` : **bibliothèque de playbooks PUBLIC**, adaptation conservatrice sur les Énergies encore inconnues **uniquement avec preuve**, **observer d'adversaire et statistiques sur fixtures purement synthétiques** en réutilisant `battle_logs.py`, `battle_sample.py`, `lessons.py`, `recommendations.py` et le nouveau `deck_knowledge.py`. **Aucun vrai journal, deck, collection ou DB personnelle n'est ouvert dans ce lot**; futurs vrais logs seulement sur commande explicite du propriétaire via import volontaire. Zéro GET fournisseur. DKI-05 Counter-Deck et DKI-06 Learning Loop restent dans l'issue #1. Pas d'exécution d'un agent en arrière-plan; démarrage manuel Codex/Claude.

**V1 `NOT_RELEASE_READY`. STOP de l'audit précédent.**
