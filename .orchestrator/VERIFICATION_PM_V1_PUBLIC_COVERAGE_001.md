# Audit indépendant ChatGPT — PM-V1-PUBLIC-COVERAGE-001

**Date de l'audit : 2026-10-18/19 Québec (selon publication GitHub). Verdict : `VERIFIED_GITHUB_SCOPE_ONLY` pour code/tests/rapports/CI. Progrès public de campagne `RAPPORTÉ_PAR_CODEX_LOCAL` et non relus physiquement depuis son SQLite. V1 `NOT_RELEASE_READY`.**

## Révisions GitHub indépendantes
- Dépôt `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`, base `7c26b84b4b88cbcaa445a061c5a3cc2a2873cb2d`, livraison Codex **`1344adfe772e428eb55934a7c1117ffa68d4a70f`**.
- **Un commit / 13 fichiers** : produits `src/pokemind/{cards,meta,updates,public_campaign}.py`, nouveaux tests `tests/test_public_coverage.py`, docs de sources et matrice J, `.orchestrator/EVIDENCE_PM_V1_PUBLIC_COVERAGE_001.md`, et `.orchestrator/{STATE,RESULT,HANDOFF,NEXT_ACTION,DECISIONS}`. Aucun backup, SQLite propriétaire, image, snapshot de campagne, jeton ou log privé dans ce diff.
- État Codex de livraison : `AWAITING_AUDIT`, `execute_now=false`, lancement consommé, absence d'autorisation pour le lot suivant; ancien plan privé de clone7 toujours `BLOCKED`, `restore plan` personnel zéro.
- Correctif vérifié en code : `stop_on_access_denial` optionnel sur clients TCGdex/Limitless/Official, activé par la seule campagne publique. `401/403/429` déclenchent fermeture/résultat neutre sans retry, puis refus du GET suivant sur la **même instance**; non-JSON et challenges HTML reconnus bloquent également. `public_campaign.py` publie raisons neutres et arrête probes officiels au refus. Comportement ordinaire des clients inchangé par défaut. La détection de challenges n'est **pas exhaustive**, et les refus ne sont pas mémorisés durablement entre nouvelles invocations.
- `tests/test_public_coverage.py` : **10 nouveaux cas** (6 refus 403/429 sur 3 fournisseurs, 3 challenges HTML synthétiques, 1 CLI FR/EN + `rules check-deck` tri-state au calendrier), sockets interdites sur le parcours CLI. Revue statique des tests et du patch effectuée.

## CI au SHA exact, journaux jobs lus
- [GitHub Actions 39188142666](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39188142666) : `completed/success`, `head_sha=1344adfe772e428eb55934a7c1117ffa68d4a70f`.
- Windows job `117854829113` : **499 passed / 2 skipped** en 115,52 s, preuve `ci_evidence=TECHNICAL_TESTS_GREEN os=Windows passed=499 skipped=2 sha=1344adfe...`.
- Ubuntu héritée job `117854828878` : **498 passed / 3 skipped** en 101,83 s, preuve `ci_evidence=TECHNICAL_TESTS_GREEN os=Linux passed=498 skipped=3 sha=1344adfe...`.
- Compilation, `git diff --check` et contrôles d'hygiène réussis dans ces jobs. **CI valide les fixtures GitHub, pas les octets du workspace PUBLIC privé du PC.**

## Résultats de collecte publique, provenance Codex locale
Le rapport `.orchestrator/EVIDENCE_PM_V1_PUBLIC_COVERAGE_001.md` affirme :
- **Une campagne publique neuve** non suivie dans Git, **6 invocations**, **125 GET tentés / 128 alloués / 144 autorisés**, ventilés TCGdex **120**, Limitless **5**, officiel **0**; 15 lectures documentaires web supplémentaires dont le nombre exact de GET physiques n'est pas exposé. Aucune erreur/denial réelle constatée, donc l'arrêt strict n'a été vérifié qu'avec des tests synthétiques.
- Comparaison entre **deux campagnes distinctes** : cartes FR **1 400→3 200** et EN **1 400→3 200 membres observés**, 32 pages/ langue **sans fin de pagination atteinte**; détails frais 1→12 par langue. Sets observés EN **220**, FR **202**, union **223**; détails sets **9/10**; union imprimés **3 578**. **Ne pas additionner les inventaires des campagnes ni prétendre avoir atteint le dénominateur mondial**. Détails de milliers de cartes non acquis, index non complet.
- Limitless : un événement, **72 pairings**, **64 admissibles/classifiables**, 30 placements; finalisation fournisseur **unknown**, mélange de formats de rondes séparé; aucun taux de victoire global/personnel soutenable.
- Officiel : termes de collecte automatisée non vérifiables, pages nav accessibles mais plusieurs documents de normes seulement iframe/timeout. **Zéro assertion normative ajoutée**, bons `PARTIAL_WITH_EVIDENCE`/`BLOCKED_WITH_REASON`; source TCGdex **non normative**. Trainer Hill non consulté.
- Aucune base/ACL/sauvegarde personnelle lue **selon Codex local**. Le périmètre physique réel de ses actions ne peut être attesté par la seule consultation GitHub; seules les données **versionnées** ont été inspectées directement.
- Une amélioration mesurée du catalogue **ne signifie pas** que la V1 est prête ni qu'un deck réel est légal/fabricable/possédé.

## Décision
**ACCEPTED / `VERIFIED_GITHUB_SCOPE_ONLY` pour ce mandat et les correctifs validés par CI.** Les comptes des GET et des membres FR/EN sont des **observations locales assainies rapportées**, pas une nouvelle collecte reproduite par ChatGPT. L'autorisation du mandat est consommée, **ne pas rejouer** les 6 campagnes.

Portes V1 toujours ouvertes : index/détails FR/EN et normes officielles datées exhaustifs, compatibilité Live réelle, tests propriétaire/deck/combats, OCR réel, scheduler OS, stockage/ACL/durabilité, et clone/migration personnelle schéma7→13. L'ancien `PM-V1-CLONE7-PLAN-001` reste `BLOCKED` avec `restore plan=0`, autorisation consommée; `ACL_OBSERVATION_FAILED` cause inconnue; `POST_VERIFY_RESIDUE_OR_UNSAFE_FILE` `CAUSE_NON_RECONSTRUITE`. **`NOT_RELEASE_READY`.**

**Suite technique non privée recommandée :** réutiliser une source de données publique existante plutôt que lancer des milliers de GET individuels. Le dépôt officiel amont [TCGdex cards-database](https://github.com/tcgdex/cards-database) décrit une base multilingue (EN/FR), et [son fichier LICENSE](https://github.com/tcgdex/cards-database/blob/master/LICENSE) indique MIT pour la base. Cela **n'établit pas** automatiquement les droits de redistribution d'illustrations/marques, les schémas exacts, la taille, l'exhaustivité ni l'adéquation d'une ingestion en bloc. Préparer un lot conditionnel de revue/compatibilité/import **purement public** avec limites réseau et taille strictes, fixtures et conformité des données. Si infaisable/licence ambiguë : bloquer proprement cette voie et préserver le parcours API borné.

GitHub reste le registre de mandat, utilisateur relaie les messages Codex ↔ ChatGPT, audits ChatGPT après lots; aucun auto-merge, aucune surveillance autonome.
