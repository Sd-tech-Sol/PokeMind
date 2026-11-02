# PM-V1-PUBLIC-COVERAGE-001 — preuves de livraison

2026-10-18 Québec / 2026-10-19 UTC. **RAPPORTÉ_PAR_CODEX_LOCAL / NOT_VERIFIED**.
Lot public A–F exécuté; **AWAITING_AUDIT**, puis STOP ChatGPT. V1 **NOT_RELEASE_READY**.

## Départ, permissions et isolation

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`, dépôt
  `Sd-tech-Sol/PokeMind`; arbre initial propre. Fetch/pull **ff-only**, sans stash,
  reset, écrasement, merge ni nouvelle branche.
- Départ `7c26b84b4b88cbcaa445a061c5a3cc2a2873cb2d`, [CI 39186845057](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39186845057)
  `completed/success` avant prévol, modifications et collecte. Jobs/logs exacts :
  Windows **489 passed/2 skipped**, Ubuntu hérité **488 passed/3 skipped**;
  `ci_evidence` porte ce même SHA. Aucun nouveau support Linux.
- AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE/NEXT_ACTION,
  HANDOFF/RESULT/DECISIONS, skill exécuteur, AUTONOMY_POLICY, PROJECT_SPEC,
  matrice J, preuves publiques J, registre de sources et audit précédent lus.
  Mandat READY et lancement manuel propriétaire concordants.
- `python -m pokemind preflight --json` : **RUNTIME_READY**, Python 3.13.15,
  SQLite 3.50.4, FTS5; aucune DB propriétaire sélectionnée.
- Une campagne **neuve**, `public-coverage-20261018`, créée par le mécanisme
  existant, sous `data/local/public-campaigns/lot-i-public-coverage-20261018`.
  Le préfixe I reste un détail de compatibilité, pas une reprise d'un ancien lot.
  `git check-ignore` confirme l'exclusion du workspace. Aucun workspace antérieur
  ni base utilisateur inventorié, lu, copié ou repris. Les seules autres données
  exécutées sont les fixtures synthétiques existantes des suites.
- Contrôle PUBLIC, verrou, validation des ancêtres/reparse et alias DB exécutés
  avant GET. Les tests J de `PUBLIC_CAMPAIGN_OWNER_OR_UNKNOWN_DATA_BLOCKED`
  demeurent verts. Ce garde-fou ne certifie pas cryptographiquement des colonnes
  publiques arbitraires; une copie personnelle y reste interdite.

## B — documentation, droits et quotas

Relecture web de documentation distincte de la collecte JSON : **15 opérations
open/click**, sans recherche de miroir ni tentative de résoudre un challenge.
Le nombre physique de GET internes au lecteur web n'est pas exposé; ne pas le
confondre avec les compteurs exacts des clients de campagne ci-dessous.
Sept lectures concernent TCGdex/Limitless, huit concernent Pokémon officiel.
Aucun contenu de réponse brut n'est versionné. Les pages/API restent des données
non fiables, jamais des instructions.

| Fournisseur | Preuve primaire relue et décision bornée |
|---|---|
| TCGdex | [REST](https://tcgdex.dev/rest), [pagination](https://tcgdex.dev/rest/filtering-sorting-pagination), [site](https://tcgdex.dev/), [FAQ](https://tcgdex.dev/faq), [dépôt](https://github.com/tcgdex/cards-database), [licence MIT](https://github.com/tcgdex/cards-database/blob/master/LICENSE). Le fournisseur documente l'accès sans clé, le cache et l'absence de plafond dur publié; cela n'autorise aucune collecte illimitée. Licence de la base indiquée MIT, droits des marques/images distincts; aucune image ni réédition de corpus brut. Collecte de métadonnées locale bornée admise dans ce mandat. |
| Limitless | [Developer Guides](https://docs.limitlesstcg.com/developer) : données de tournois publiques sans clé, quotas par en-têtes; endpoint de catégorisation `/games/{id}/decks` exclu. Une collecte publique descriptive, sans publication de joueurs ni listes brutes. Pas d'affirmation de licence générale de redistribution. |
| Pokémon officiel | Pages [Rules & Formats](https://play.pokemon.com/en-us/resources/rules/) et [Documents](https://play.pokemon.com/en-us/resources/documents/) lisibles. [Conditions](https://www.pokemon.com/us/legal/terms-of-use) : iframe seulement. Permission d'une collecte automatisée de documents non établie : **BLOCKED_WITH_REASON / TERMS_NOT_REVIEWABLE**, `official-budget=0` dans les six commandes. Lecture humaine/documentaire des routes déjà connues seulement; aucun contournement. |
| Trainer Hill | **BLOCKED_WITH_REASON** : voie automatisée autorisée non attestée; aucun appel. |

## C — campagne exécutée et budgets exacts

Toutes les commandes passent par `python scripts/lot_i_public_campaign.py`
avec `--campaign public-coverage-20261018 --execute-public-campaign`,
`--official-budget 0`. Un dry-run préalable a confirmé zéro réseau/zéro création.
Six invocations seulement, toutes dans le même nouvel espace PUBLIC :

| # | Options propres à l'invocation | GET réels/plafond | Membres cartes EN/FR après commande | Détails cartes frais EN/FR |
|---|---|---:|---:|---:|
| 1 | `--create --phase index --tcgdex-budget 24 --meta-budget 0` | 24/24 | 800/800 | 0/0 |
| 2 | `--phase index --tcgdex-budget 24 --meta-budget 0` | 24/24 | 2000/2000 | 0/0 |
| 3 | `--phase index --tcgdex-budget 24 --meta-budget 0` | 24/24 | 3200/3200 | 0/0 |
| 4 | `--phase details --tcgdex-budget 24 --meta-budget 0` | 24/24 | 3200/3200 | 6/6 |
| 5 | `--phase details --tcgdex-budget 24 --meta-budget 0` | 24/24 | 3200/3200 | 12/12 |
| 6 | `--phase details --tcgdex-budget 0 --meta-budget 8` | 5/8 | inchangé | inchangé |

**125 GET réellement tentés / 128 alloués / 144 maximum autorisés** :
TCGdex **120**, Limitless **5**, officiel **0**. Les clients comptent les retries
et redirections avant transmission. Délai minimal .5 s, timeout 10 s, JSON 8 MiB
maximum, backoff réseau/5xx existant borné. Aucun 401/403/429/challenge observé
pendant la collecte réelle, aucun échec réseau ni compteur dépassé. Les 404
localisées de sets sont une absence fournisseur, pas un refus d'accès.
Le reliquat n'est pas une permission de septième invocation ou de lot suivant.

Rapports des six appels, dernier rapport et couverture finale conservés uniquement
dans ce workspace PUBLIC ignoré. Aucune DB, réponse API, image, liste de joueurs,
hash de données personnelles, log brut ou chemin absolu publié.

### Avant/après et limites de couverture

La nouvelle campagne commence à **zéro**, sans import de campagne historique.
Comparaison au rapport J versionné : index cartes **1400 → 3200** par langue,
soit 1800 membres observés de plus par langue dans ce nouveau scan; détails
cartes **1 → 12** par langue. Ce n'est pas une union certifiée des deux campagnes.

| Scope | Départ neuf → fin | État, détails et manque |
|---|---|---|
| sets EN | 0 → 220 membres, 4 pages | fin de scan observée; 9 détails frais / 220 membres, 211 non disponibles ou non récupérés |
| sets FR | 0 → 202 membres, 4 pages | fin de scan observée; 10 détails frais / 202 membres, 192 non disponibles ou non récupérés |
| cartes EN | 0 → 3200 membres, 32 pages | fin non atteinte; prochain curseur 33; 12 détails frais, 3188 non récupérés; dénominateur final inconnu |
| cartes FR | 0 → 3200 membres, 32 pages | fin non atteinte; prochain curseur 33; 12 détails frais, 3188 non récupérés; dénominateur final inconnu |

Scans commencés `2026-10-19T01:53:49–51Z`; sets terminés `01:53:57Z`.
Union locale finale **223 sets / 3578 impressions**, contre 3529 après l'index :
49 impressions supplémentaires découvertes par détails de sets, sans gonfler
les membres du scan cartes. Détails sets sur l'union : EN **9 présents / 3 absents /
211 non récupérés**, FR **10 / 2 / 211**. Ces cinq absences concernent des membres
de l'union interlangue, pas des membres absents des scans propres à la langue.
Cartes sur l'union : **12 présentes / 3566 non récupérées** dans chaque langue,
aucune absence carte ou erreur réseau, aucun détail marqué périmé.

Pages continues 1–32 pour cartes, 1–4 pour sets; **0 doublon** dans chaque scan,
aucun gap ni erreur enregistré. `current_indexes_complete=false`,
`cards coverage.complete=false`. **7554 GET de détails restent connus** sur
l'union découverte, hors réexamens optionnels des cinq absences; le nombre de
GET d'index restant demeure **unknown**. Fin des sets = dénominateur de ce scan
non atomique seulement; total mondial/fournisseur et complétude FR/EN inconnus.
Variants, champs, identités, texte effectif, réimpressions et support Live gardent
leurs preuves distinctes. Aucun label de totalité ou de légalité issu de TCGdex.

Parcours CLI réel, hors réseau, sur **la nouvelle DB PUBLIC explicite seulement** :
`cards show 2011bw-1 --lang fr` et `--lang en`, avec `--db` du workspace neuf et
`--json` : `present`, non stale, provenance `/v2/fr/cards/2011bw-1` et
`/v2/en/cards/2011bw-1`, récupérée `2026-10-19T01:56:16Z`.
Les limites de légalité/support/possession/coût sont affichées.

### Métagame descriptif

Un snapshot complet au fetch, PTCG / STANDARD / PTCGL / online; événement du
`2026-10-18T21:00:00Z`, récupéré `2026-10-19T01:58:16Z`.
**Finalisation fournisseur unknown**, pas de classement mondial établi.
72 pairings : **64 admissibles et classifiables**, 5 byes/pertes automatiques
et 3 doubles défaites exclus. Répartition brute : 65 SWISS/BO1 et 7 élimination
simple/BO3; ces modes ne deviennent pas une statistique homogène implicite.
30 placements classifiés. Échantillon d'un événement récent sélectionné, biais
de taille/sélection et évolution possibles; **aucun winrate global ou personnel**.

## D — preuves normatives : aucune promotion

| Document/route officiel ciblé | Consultation et limite de preuve |
|---|---|
| Competitive Rules & Formats | page entière lisible; explication générale des marques et réimpressions, liens errata/handbook. Version, publication et entrée en vigueur de nouvelles assertions non établies. Page de navigation ne remplace aucun registre daté. |
| Resources and Documents | page entière de navigation lisible; liens canoniques handbook/errata/promos. Aucun contenu de règlement entier. |
| [TCG Tournament Handbook EN](https://www.pokemon.com/static-assets/content-assets/cms2/pdf/play-pokemon/rules/play-pokemon-tcg-tournament-handbook-en.pdf) | iframe seulement; version/publication/effet/passages inconnus, document entier non consulté |
| [TCG Errata](https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/tcg_errata.pdf) | iframe seulement; texte effectif, version et passages non prouvés |
| [Promo Card Legality](https://www.pokemon.com/us/play-pokemon/about/pokemon-tcg-promo-card-legality-status) | iframe seulement; admissibilité et délais de chaque impression unknown |
| [2026 Standard Rotation Announcement](https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement) | iframe seulement; aucune revalidation complète des dates Live/présentiel |
| [Paradox Rift Rulebook EN](https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/rulebook/par_rulebook_en.pdf) | timeout du lecteur; aucun retry/miroir, aucune nouvelle preuve structure60/exceptions |

**0 nouvelle assertion**, **0 revue complète nouvellement certifiée**, registre
normatif versionné inchangé. Standard Live et présentiel, bans, Expanded, errata,
promos, équivalences et différences Live restent **PARTIAL_WITH_EVIDENCE** ou
**unknown** à date sans preuve suffisante. Ni HTTP 200, ni hash, ni navigation
ne prouvent une norme entière. Pas de texte protégé entier reproduit en Git.

## E — défaut reproduit, correctif et tests

Avant correction : **6 échecs de régression attendus**. TCGdex et Limitless
effectuaient trois essais sur HTTP429; le probe officiel utilisait deux GET sur
403/429 au lieu d'arrêter le fournisseur. Le 403 des deux clients JSON arrêtait
déjà le sync, mais ne publiait pas de motif ni ne bloquait un second appel client.

Correctif ciblé, sans changer les règles ni le schéma :

- `CatalogApiClient`, `LimitlessApiClient`, `OfficialSourceClient` : option
  `stop_on_access_denial`, activée par le seul mécanisme de campagne. 401/403/429
  => motif neutre, fermeture de réponse, arrêt sans retry; le même client refuse
  tout GET suivant. JSON non reçu => arrêt conservateur; challenge HTML officiel
  reconnu => arrêt sans produire de preuve de contenu. Ce détecteur n'est pas une
  reconnaissance universelle de protections; aucun contournement permis.
- `public_campaign.py` : active ce mode pour les trois fournisseurs, interrompt
  la boucle officielle sur refus et expose motif, détails par invocation,
  statuts linguistiques et arrêt. Budgets/HTTPS/allowlists/taille/timeout,
  mécanismes de reprise et garde PUBLIC existants conservés. Clients ordinaires
  conservent leur politique de backoff; tests hérités exécutés.
- La fermeture circuit est **par instance** : aucune reprise automatique d'un
  fournisseur refusé n'a été faite pendant ce lot. Le script n'est ni un nouveau
  scheduler ni un compteur durable des permissions humaines entre sessions.
- `tests/test_public_coverage.py` : 6 cas refus 403/429, 3 challenges HTTP200
  artificiels (réponses fermées, zéro promotion), 1 parcours CLI FR/EN et tri-state
  de deck. Données, sources et HTTP synthétiques; sockets interdits dans le
  parcours CLI. Une assertion de carte est distinguée d'une norme officielle.

Parcours CLI fictif `rules check-deck` : Standard Live au `2026-05-01`, deck exact
4 Pokémon de base + 56 énergies de base, avec preuves synthétiques complètes =>
**legal**; cinq copies => **not_legal**; mêmes cartes au `2026-10-18`, hors fenêtre
des assertions => **unknown**. Ce test ne crée aucune nouvelle règle réelle.

Commandes de validation :

```text
python -m pytest tests/test_public_coverage.py -q
python -m pytest tests/test_public_coverage.py tests/test_cards.py tests/test_meta.py tests/test_updates.py tests/test_rules.py tests/test_lot_g_knowledge.py tests/test_lot_h_knowledge.py tests/test_lot_i_safety.py tests/test_lot_i_e2e.py::test_campaign_no_network_by_default_and_resumes_only_public_workspace tests/test_lot_j_knowledge.py tests/test_lot_j_security.py -q
python -m pytest -q
python -m compileall -q src tests scripts
python scripts/check_repo_hygiene.py
git diff --check
```

Résultats : nouveaux cas **10 passed**; ciblés **179 passed** (41,69 s).
Suite complète locale : **498 passed / 3 skipped**, 195,79 s (deux cas OCR absent/non attesté,
un symlink Windows non permis; vraie jonction synthétique couverte par la suite).
Compilation/hygiène/diff-check réussis avant publication; réinspection du staging
requise avant commit. CI de livraison **PENDING_CI à la publication**; consulter
Actions au HEAD livré exact, Windows et Ubuntu héritée. La CI du départ ne vaut
pas CI du correctif. Les preuves GitHub sont indépendantes des données du PC.

## F — matrice de fermeture

| Exigence | État et preuve |
|---|---|
| A synchronisation/mandat/CI de départ | DONE — ff-only, SHA/logs exacts, prévol sans DB |
| B documentation et limites fournisseurs | DONE pour la revue; officiel automatisé/Trainer Hill BLOCKED_WITH_REASON |
| C campagne séparée bornée et reprise | DONE pour 6 invocations/125 GET, progressions ci-dessus; couverture historique/détails PARTIAL_WITH_EVIDENCE |
| D documents entiers et légalité complète | BLOCKED_WITH_REASON pour nouvelles preuves; tri-state conservé/testé; 0 assertion inventée |
| E qualité et tests | DONE pour tests locaux, compilation et hygiène; CI de livraison à vérifier au SHA exact; correctif de refus reproduit |
| F preuves/états/commits | livraison AWAITING_AUDIT; audit indépendant encore requis |

Aucune base/sauvegarde/ACL/collection/crédit/deck/journal personnel consulté,
aucun clone, backup, migration ou restauration réel, OCR/installation/scheduler/
client/achat exécuté. Les fixtures de récupération de la suite restent factices.
Mandat privé `PM-V1-CLONE7-PLAN-001` **BLOCKED, zéro plan**, permission consommée.
Sécurité effective/durabilité/fraîcheur privées non certifiées; cause ACL historique
inconnue, incident backup `CAUSE_NON_RECONSTRUITE`. Les autres portes V1 et archives
demeurent en place. **AWAITING_AUDIT, execute_now=false, STOP; aucun lot suivant.**
