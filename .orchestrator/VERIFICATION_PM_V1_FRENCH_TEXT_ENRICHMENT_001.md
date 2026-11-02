# Vérification indépendante — PM-V1-FRENCH-TEXT-ENRICHMENT-001

**2026-10-22, Québec. Verdict : `VERIFIED_GITHUB_CODE_AND_CI_SCOPE_ONLY`; enrichissement PUBLIC chiffré = `CODEX_LOCAL_REPORTED`. V1 `NOT_RELEASE_READY`.**

## GitHub et CI (contrôles indépendants)

- Branche `work/pm-v1-lotj-final-readiness-windows` au HEAD exact [`87d5eba519b60a241ee95c993e1a27c06d94ae1e`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/87d5eba519b60a241ee95c993e1a27c06d94ae1e) lors de l'audit. Compare depuis l'audit précédent `23dbca251038a2b4deeaa090cb3e37d60734868d` : **1 commit, 21 fichiers** (code, tests, preuves d'orchestration et documentation). Aucun merge/reset/force-push ou changement de base personnelle n'est visible.
- [GitHub Actions `39827634467`](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39827634467) : `completed/success` au SHA `87d5eba519b60a241ee95c993e1a27c06d94ae1e`, les **deux jobs et leurs journaux effectivement lus** :
  - **Windows** job `119995041056` : **706 passed, 2 skipped**, `ci_evidence=TECHNICAL_TESTS_GREEN` au SHA exact.
  - **Ubuntu** job `119995041475` : **705 passed, 3 skipped**, même témoin SHA. Troisième skip : essai de junction propre à Windows.
  - Deux skips OCR par plateforme car moteur portable/opt-in non attestés sur les runners. Les tests CI **ne prouvent pas** l'OCR réel.
  - Hygiène du dépôt et `git diff --check` réussis. Les **705 tests locaux** que Codex rapporte sont distincts des **706 Windows / 705 Ubuntu** observés dans la CI.
- Arbre GitHub récursif : **365 entrées, non tronqué**, **aucune nouvelle DB, texte de carte, corpus ni capture versionnée sous `data/local/`**. Ceci prouve l'absence de publication dans Git, non l'état intégral du PC ni la véracité de `personal_data_accessed=false`.

## Revue du code et portée démontrée

- `src/pokemind/french_text.py` : interpréteur limité des champs textuels de modèles Poképédia, appariements extension/numéro/identité et PV, attaques par nom concordant ou coût+dégâts unique plutôt que par position seule; inconnues et ambiguïtés rejetées, aucune traduction générative.
- `src/pokemind/french_wiki_corpus.py` : corpus PUBLIC local exigé, provenance HTTPS `www.pokepedia.fr/api.php`, reçus SHA-256, limite taille/budget, comparaison des hachages des payloads EN/FR, sélection par set/numéro; références parallèles descriptives limitées à texte EN et identifiants nationaux identiques. Tests synthétiques d'invalidations et ambiguïtés présents.
- `src/pokemind/french_text_store.py` : vérification du namespace PUBLIC, validation avant écriture, garde transactionnelle contre remplacement du natif, tables auxiliaires `catalog_french_text_*`, reçus de provenance par champ, revalidation des payloads au moment de montrer et chercher une fiche. `cards.py` intègre les compléments dans `cards show/search` seulement. Aucun changement démontré du schéma global ni du moteur d'import TCG Live.
- Les tests synthétiques ajoutés démontrent le comportement des modules sur leurs fixtures, **pas l'exactitude de toutes les correspondances wiki/cartes d'un cache de 10 556 cartes**. Les 42 tests ciblés locaux et les cinq CLI privés de Codex ne sont pas reconstituables depuis GitHub.

## Cohérence comptable — chiffres rapportés localement

| Type de champs français | Initialement manquants | Ajoutés (Codex) | Restants |
|---|---:|---:|---:|
| Descriptions de Pokémon | 9 681 | 9 605 | 76 |
| Noms de cartes | 1 672 | 1 584 | 88 |
| Noms/effets d'attaques | 4 045 | 3 497 | 548 |
| Noms/effets talents | 599 | 521 | 78 |
| Effets Dresseur/Énergie | 240 | 232 | 8 |
| **Total** | **16 237** | **15 439** | **798** |

Les sommes correspondent. La provenance est répartie entre **10 798 transcriptions françaises publiées + 4 567 traductions communautaires déjà publiées + 74 descriptions parallèles = 15 439 champs**. `10 556` cartes touchées et `395` cartes présentant au moins une lacune sont cohérentes, **non vérifiées indépendamment**. Les **76 descriptions restantes** sont des champs ciblés avec équivalent anglais connu dans l'inventaire retenu; ne pas extrapoler à toutes les descriptions du monde ou à l'absence sur Internet.

Autres résultats **`CODEX_LOCAL_REPORTED`** : 640 GET de données, 18 424 279 octets, 495 fichiers de réponses, 10 625 pages, 51 tables préexistantes non modifiées, intégrité SQLite/FK/FTS bonne, idempotence deuxième import, 0 traduction artificielle, aucune carte japonaise ou donnée personnelle ajoutée. **GitHub ne donne pas accès au corpus brut, aux transactions disque, ni aux logs HTTP locaux.** L'audit peut uniquement confirmer que les garde-fous existent dans le code.

## Licence, statut de vérité et dépendances

- La [notice Poképédia droits d'auteur](https://www.pokepedia.fr/Pok%C3%A9p%C3%A9dia:Droits_d%27auteur) confirme indépendamment **CC BY-NC-SA 3.0** : crédit source/auteurs, usage non commercial, partage sous les mêmes conditions pour les adaptations. Le projet conserve par champ URL de révision, métadonnées et licence; **respect effectif dans toute redistribution future à revalider**. La licence MIT des données TCGdex ne remplace pas celle des compléments Poképédia.
- Une traduction sur un wiki de communauté **n'est pas la preuve du texte imprimé officiellement en français**, de la légalité Standard, d'une réimpression équivalente ni de la compatibilité du client TCG Live. Les enregistrements portent correctement `official_text_verified=false` et `french_printing_proven=false`.
- Le catalogue anglais/français TCGdex natif conserve ses nombres et statuts selon la livraison; les compléments sont un niveau **distinct et attribué**, non un changement de certification des 23 864 identifiants.

## Verdict et suite

**Accepter l'implémentation, tests/CI et documentation dans la portée GitHub : `VERIFIED_GITHUB_CODE_AND_CI_SCOPE_ONLY`.** Ne pas promouvoir les chiffres des **9 605 descriptions** à une certification d'inventaire indépendamment réalisée; les considérer comme **résultat local étayé et arithmétiquement cohérent**. Pas de nouvelle recherche ou de travail après audit sans ordre ciblé. Les permissions de cette collecte sont consommées : ne pas réutiliser 3 360 GET théoriquement inutilisés, ni relancer une campagne historique.

**Priorité pratique suivante** : raccorder les cartes et textes disponibles à **règles officielles datées, légalités et données de tournoi actuelles**, pour conseiller le joueur, sans envoyer deck, collection ou logs privés à un tiers. L'import texte TCG Live est historiquement `FIELD_VALIDATED`; pas de retest répétitif. Autres gates V1 : OCR/captures, Windows scheduler, récupération/ACL, revues officielles; tous inchangés. **V1 `NOT_RELEASE_READY`, aucun mandat nouveau `READY`. STOP**.
