# Audit indépendant — PM-V1-PUBLIC-DATASET-ALTERNATIVES-001

**2026-10-21 Québec. Verdict : `VERIFIED_GITHUB_REVIEW_SCOPE_ONLY`.** Revue bornée de deux alternatives et décision de retenir le REST TCGdex existant acceptées, **sans certification d'un corpus complet ni d'une intégration nouvelle**. V1 `NOT_RELEASE_READY`.

## Provenance, code et tests

- Branche `work/pm-v1-lotj-final-readiness-windows`, base autorisée `abde47cc2d1736cfabe5b398fa68c483c3ab9ef6` → livraison `249a30158ca02b619dd3dcaa514f025c1e89519e` : **1 commit / 10 fichiers**, 8 documents modifiés/ajoutés et `tests/test_dataset_alternatives.py` ajouté; aucun changement de code produit, schéma, dependency lock, OCR ou planificateur.
- Les sous-tâches A–E sont documentées dans `docs/PUBLIC_DATASET_ALTERNATIVES.md` et `.orchestrator/EVIDENCE_PM-V1-PUBLIC-DATASET-ALTERNATIVES-001.md`. A inventaire, B comparaison, C budget documenté, D décision de repli, E tests. **L'implémentation d'un importeur alternatif reste `BLOCKED_WITH_REASON`** : cette absence est conforme au mandat conditionnel, pas une réussite d'import.
- Sept cas ajoutés : quatre formes étrangères (liste JSON, CSV, objet inconnu sans/avec label MIT) rejetées avant table d'impression/traduction/assertion; deux sources/provenances incohérentes bloquées sans écriture; absence EN non remplacée par FR et reprise sans requête. Tests synthétiques utilisent faux client et bloqueurs socket/DNS; ne démontrent pas un validateur de licence.
- Aucune réponse externe brute, binaire, archive, image, SQL privé, deck ou journal personnel dans le diff. L'absence physique d'opérations privées ou d'autres GET sur le PC ne peut pas être certifiée par GitHub.

## CI exacte, contrôlée dans les journaux

[Run Actions 39699885124](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39699885124) : `push`, `completed/success`, SHA `249a30158ca02b619dd3dcaa514f025c1e89519e`, branche exacte, tentative1.

| Plateforme | Job | Logs vérifiés |
|---|---:|---|
| Windows Python3.11 | 119566278917 | **554 passed, 2 skipped**; `ci_evidence=TECHNICAL_TESTS_GREEN os=Windows passed=554 skipped=2 sha=249a30158ca02b619dd3dcaa514f025c1e89519e` |
| Ubuntu Python3.11 | 119566278729 | **553 passed, 3 skipped**; `ci_evidence=TECHNICAL_TESTS_GREEN os=Linux passed=553 skipped=3 sha=249a30158ca02b619dd3dcaa514f025c1e89519e` |

Sur les deux jobs : checkout au SHA, compilation, hygiène Git, `pytest -q`, `git diff --check`, preuve synthétique, toutes étapes success. Deux skips hérités OCR réel; un skip Ubuntu pour test de jonction Windows. Prévol antérieur [39698192663](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39698192663) également `completed/success` au SHA `abde47cc2d1736cfabe5b398fa68c483c3ab9ef6`. Les **553 passed / 3 skipped Windows Python3.13** et 86 ciblés sont `RAPPORTÉ_PAR_CODEX_LOCAL`, distincts de la CI3.11.

## Vérification des sources et budget

- `PokemonTCG/pokemon-tcg-data` au SHA `39a26a144c8b6ef6c2fb17b2c29d0bb7121e3a11` : README épinglé confirme explicitement source legacy/déconseillée pour nouvel usage, et fin programmée de l'API au 2027-03-01. Un `LICENSE` racine au SHA épinglé renvoie 404. Cela ne prouve PAS l'absence générale de tout droit, mais interdit la conclusion qu'une licence libre a été vérifiée dans la revue.
- `tooniez/pokemoncards_tcg` au SHA `13cf376295d76c60e9842ef4e482f5ffca07ff33` : licence MIT lue; README indique données principalement anglaises et passages génériques sur la provenance. Arbre épinglé non tronqué : `cards.csv` 12 488 295 octets, excède la limite du mandat de 5MiB; FR, fraîcheur et droits amont exhaustifs non démontrés.
- Le rapport énumère **12 GET / 214 753 octets** : somme des douze tailles documentées concordante et inférieure à 5 242 880. **Ce compteur et le refus des redirects/challenges sont rapportés par Codex local, pas prouvés par les logs CI**, qui n'exécutent aucune collecte fournisseur. Aucun droit implicite sur images, marques, règles officielles ou contenus amont.
- Les deux alternatives sont `BLOCKED_WITH_REASON` pour une intégration V1 FR/EN à ce stade; le repli REST TCGdex existant est une décision raisonnable et conserve provenance/identités sans inventer de correspondance. Elle ne prouve pas qu'il n'existe aucune autre source, ni l'exhaustivité du catalogue.

## Décision et limites

**ACCEPTER** le lot de qualification et les tests de frontières, sans promouvoir la couverture FR/EN, la légalité/Live, le coach réel, les sources officielles, Trainer Hill, le planificateur réel ou les opérations propriétaires. L'ancien mandat `PM-V1-PUBLIC-DATASET-ALTERNATIVES-001` est clos **dans le périmètre de la revue seulement**, autorisation 12 GET consommée; ses fournisseurs ne sont pas à reconsulter avec ce budget. Ancien clone privé toujours `BLOCKED`.

**Prochain mandat préparé distinct** `PM-V1-REST-FR-EN-COVERAGE-001` : approfondir prudemment le catalogue réel avec l'API REST déjà intégrée, dans **un espace PUBLIC neuf** seulement. C'est un nouveau plafond autonome de **192 GET maximum**, pas un replay des campagnes consommées; `READY` pour relais manuel propriétaire seulement, aucun lancement automatique, aucun travail sur données privées, et prévol CI obligatoire au nouveau HEAD documentaire. Si conditions d'accès ne sont pas clairement permises, STOP avant tout GET. La V1 reste `NOT_RELEASE_READY`.
