# Preuves — PM-V1-DECK-LIBRARY-MATCHUP-FOUNDATION-001

## Prévol et portée

Mandat READY concordant avec STATE et décision D-196, démarrage manuel.
Branche `work/pm-v1-lotj-final-readiness-windows`, arbre initial propre.
Fetch/pull ff-only sans perte de9fc5242 vers
`6a1a4f0c6e9c278248393640d5f7ac8292707d9f`.
[Actions39902527654](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39902527654)
au nouveau HEAD : Windows job120247084532 **887 passed/2 skipped**, Ubuntu
job120247084727 **886 passed/3 skipped**, deux completed/success. Logs
`ci_evidence` contrôlés avant développement fonctionnel. Prévol local
`RUNTIME_READY`, Python3.13.15, SQLite/FTS5 sans base personnelle.

## Réutilisation et résultat produit

- `meta deck-library` : filtres d'archétype, tournoi, date et empreinte de
  composition, dénominateurs explicites. Réutilise les pages et listes
  recontrôlées de `competitive._advisor_snapshot`, sans seconde base.
- `meta deck-knowledge` conserve l'export60 et ses preuves; ajoute des
  alternatives de familles distinctes avec différences de quantités. Différence
  de construction ≠ avantage de matchup. `competitive-compare/export` réutilisés.
- Observer : événements du parseur `battle_logs`, attribution des acteurs
  conservatrice, pioches cachées/génériques exclues, occurrences séparées du
  minimum d'un exemplaire; chronologie, hypothèses, références/proxies et export
  adverse exact fourni séparés. Les noms FR/EN supplémentaires exigent des
  payloads natifs vérifiés de même impression. Révisions de classification
  datées, révocables et conservées dans la vue sans écraser les faits.
- Analytics : `conservative_sample`, validation et historique d'attestation de
  `version_evidence`, revue `battle_lessons`. Aucun transfert de lien au
  représentant d'un doublon, aucune attribution par version courante/legacy ou
  date d'import. Révocation/futur/conflit restent inconnus. Les recommandations
  ont été inspectées; leur entrée globale collection/crédits n'est pas invoquée.
- `battle opponent` / `battle matchups`, humain/JSON : base et sélection
  explicites plus `--confirm-owner-read` avant toute inspection implicite.
  Chemins hors du projet local, redirections, alias et sidecars refusés;
  lecture seule sans création/migration. Ces voies ont été exécutées **sur
  fixtures inventées seulement**. Aucune analyse ou import réel effectué.

[Guide humain](../docs/DECK_LIBRARY_MATCHUPS.md), feuille de route
[EPIC#1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1).

## PC — bibliothèque PUBLIC, CODEX_LOCAL_REPORTED uniquement

| Vérification | Résultat local |
|---|---:|
| Événements / placements / compositions | 2 /32 /28 |
| Étiquettes d'archétype | 15 |
| Fiches JSON et humaines générées | 28 chacune |
| Fiches avec payloads descriptifs natifs sourcés | 28 |
| Lignes de fiches, comptées par composition | 698 |
| Lignes avec payload natif daté/provenance vérifiés | 626 /698 |
| Exports reparsés et comparés à la composition source | 32 /32, tous60 |
| Compositions uniques exportables | 28 /28 |
| Fichiers PUBLIC protégés inchangés | 94 |
| GET fournisseur / appels interdits instrumentés | 0 /0 |
| Vrais journaux ou bases personnelles ouverts | 0 |

Les fiches restent `PARTIAL_WITH_EVIDENCE`; aucun ratio de succès, classement
absolu, effet absent ou texte communautaire promu en norme. Les28 listes
complètes, fiches et rapports détaillés sont dans le nouvel espace PUBLIC local
ignoré, sans copie dans Git. Les filtres tournoi/archétype/version ont été
recoupés : tournoi581 =16 placements, Hydrapple =3 compositions, version choisie
=1 composition. Deux tournois/top16 restent un échantillon biaisé.

Les7 impressions MEE pilotes ont été examinées dans leurs payloads locaux
présents : IDs/catégorie/numéros cohérents, mais **aucune équivalence explicite
du nom et aucun texte corroborant**; pas de page carte MEE de l'autre fournisseur
en cache. Aucune heuristique globale de suppression de « Basic ». **Pas de
progrès de résolution inventé** : pilotes62/69 uniques,87/97 lignes par option,
201/240 copies; quatre decks `unknown` présentiel et Live.

Instrumentation des CLI PUBLIC : sockets/URL/réseau, connexion writable,
repli DB, presse-papiers et sélection privée interdits. Connexions limitées
aux deux caches PUBLIC explicites avec `query_only`. Octets/taille/mtime des94
fichiers contrôlés avant/après. Ces opérations du PC ne sont **pas certifiées
indépendamment par GitHub**.

## Scénario Observer/Analytics inventé, reproductible en CI

4 compositions /6 placements PUBLIC **artificiels**,4 exports60,5 matchs
inventés FR/EN, versions v1/v2 confirmées volontairement dans une base de test.

| Groupe synthétique | W | L | Unknown | n décidé | Parties |
|---|---:|---:|---:|---:|---:|
| v1 / hypothèse Hydrapple | 0 | 2 | 1 | 2 | 3 |
| v2 / hypothèse Hydrapple | 1 | 0 | 0 | 1 | 1 |
| Version non attestée / archétype ambigu | 0 | 1 | 0 | 1 | 1 |

Synthetic Delta vu plusieurs fois =au moins1 exemplaire, pas3. Carte du joueur,
main générique, pioche cachée et attaque ne deviennent pas une carte adverse.
Le proxy60 PUBLIC synthétique a une source et n'est pas le deck exact adverse.
Tous les petits ratios sont inconnus; v2 n'est pas déclarée améliorée.

Autres cas : export80 rejeté; export complet incohérent ou identité des
participants absente maintenus inconnus; hypothèse ambiguë; retrait d'une
annotation sans effacer l'hypothèse initiale; confirmation future/révoquée,
lien legacy/conflit, version non60/future et gagnant non corroboré refusés pour
l'attribution. Doublon exact non réimporté, doublon interparseurs exclu
provisoirement sans transférer son attestation. Période sur date attestée,
dates inconnues dénombrées hors filtre. Un autre scénario inventé vérifie le
ratio descriptif3/5 avec1issue inconnue distincte, sans causalité inférée.

## QA, confidentialité et fermeture

**191 tests ciblés verts** avant la suite complète; résultats finaux dans
RESULT/STATE. Compilation, hygiène et diff check exécutés. Nouvelle propriété
JUnit unique `public_deck_library_matchup_reproduction`, publiée via
`deck_library_matchup_evidence` avec whitelist fixe; rejet absence/doublon,
fausse portée privée, compteurs, preuve réseau/visibilité/proxy/version/MEE
incompatible. Champs libres filtrés. Les cinq autres preuves restent requises.

La CI finale doit être `completed/success` **sur les deux OS au SHA de livraison
exact**, après push. Résultat durable dans Actions, pas substitution par le
prévol39902527654 ni auto-VERIFIED. La preuve synthétique ne certifie aucune
partie, DB, cache ou légalité sur le PC.

Enveloppe fournisseur **0GET**, aucun ancien budget rouvert. Aucune vraie partie,
deck principal, collection, crédit, compte/client Live, capture/presse-papiers,
installation OS, OCR, scheduler, sauvegarde, migration/restauration/purge,
merge ou force-push. Aucune nouvelle DB personnelle; seules les bases de test
isolées sont créées puis retirées par les fixtures habituelles.

`AWAITING_AUDIT`, execute_now=false, consumed=true. **STOP audit indépendant
ChatGPT**, aucun prochain lot lancé. DKI-05/06 et portes A–J conservés.
**V1 NOT_RELEASE_READY.**
