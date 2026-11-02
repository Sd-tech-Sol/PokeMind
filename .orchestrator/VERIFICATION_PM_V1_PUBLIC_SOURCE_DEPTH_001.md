# AUDIT CHATGPT — PM-V1-PUBLIC-SOURCE-DEPTH-001

**2026-10-27 Québec — AUDITED_STATIC_SYNTHETIC_SOURCE_DEPTH_DELIVERED_REAL_SOURCE_QUALIFICATION_PENDING_CI_PENDING.**
**V1 NOT_RELEASE_READY; CI AWAITING_EVIDENCE.** Cet audit confirme des mécanismes de code GitHub, pas leur comportement réel sur les pages Pokémon ni le PC Windows.

## Ancrage GitHub
- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotj-final-readiness-windows`.
- Avant lot `ccfce00db806f09434aff9c7a9ae26188e615640`; code livré `27aa7919553809f5b7af29a3437ebb60e50854c0`; HEAD audité `35627627dba24bfc156e5fb6b277ac585cebe045`.
- Comparaison GitHub vérifiée : **2 commits, 18 fichiers ajoutés/modifiés, ahead=2/behind=0**. Code inspecté : `public_source_fields.py`, `meta.py`, `batch_public_research.py`, `receipts.py`, `services.py`, tests `test_public_source_depth.py`, tests Qt et harness `qa_unified_desktop.py`; documents `docs/PUBLIC_SOURCE_DEPTH.md`, RESULT/EVIDENCE/matrice V1.
- Aucune lecture par ChatGPT du disque Windows, bases ou journaux personnels; aucun lancement de test, de collecteur, de fournisseur, du portable QA ou de facturation.

## Constats positifs vérifiés statiquement
1. `extract_official_fields` introduit une grammaire **délibérément restreinte** à une phrase anglaise complète de rotation dans un paragraphe `<article><p>`; exclusion des scripts/navigation, bornes 2 Mio, 64 paragraphes (500 caractères), 8 assertions, et production de champs structurés (plateforme, format, marques, date d'effet, date de publication). Corps et phrase ne sont pas conservés dans les nouveaux instantanés. `qualified_rule_fields` distingue publication/consultation/effet, conflits, effectivité future et incertitude normative.
2. **Rétention fermée par défaut :** `retention_allowed` n'accepte que `mode=derived_fields_only` avec `license=synthetic_author_owned` et référence bornée. Le `Services.prepare_question` ordinaire ne transmet aucune politique : les pages officielles **réelles ne déclenchent donc aucune extraction de règle persistée** par cette nouvelle voie. Cette restriction est intentionnelle, pas une preuve de droits pour des sites publics.
3. `meta_window_comparison` lit la base méta PUBLIC existante, avec fenêtres disjointes, cutoff sur date d'événement et `fetched_at`, contexte Standard/PTCGL/online/public, snapshots complets et exclusion des règles spéciales. Les seuils minimum par fenêtre sont 2 tournois, 10 placements classifiés, couverture >=80% et 5 pairings classifiables. Le calcul est **descriptif** (part des placements classifiés), pas un winrate, test de significativité ou causalité. `public_meta_evidence` consulte le cache marqué, sans nouveau GET.
4. `public_research_answer` réutilise les champs `rule_evidence`/méta validés par forme et requalification, affiche provenance/date/version et limites; `public_research_message` conserve la réponse et le reçu canonique dans **le même message du chat**. Prose brute du fournisseur exclue; aucune seconde mémoire ou collecte parallèle.
5. Les nouvelles batteries de tests contiennent : extraction autorisée/refusée, droits invalides, contenu caché, dates et conflits, transport anti-bot/robots/redirection/taille, déduplication/révision/offline, fenêtres méta valides ou insuffisantes, faux narratif du modèle, Qt Codex/Claude, rendu/sauvegarde/reprise, nouveau gate `source_depth_gate` du portable.
6. Selon preuves **Codex locales uniquement**, `1454 passed / 3 skipped` cerveau + `62 passed Qt Windows` = **1516 passed distincts / 3 skipped**, 32 tests nouveaux, EXE QA native frozen exit0 et trois gates passées, données inventées, 0 GET Internet réel, pas d'EXE utilisateur remplacé. **Non rejoués indépendamment** ici.

## Limites vérifiées — pas encore une capacité métier réelle complète

- La seule licence admise par le prototype est **celle de données inventées**. Aucun droit de rétention réelle pour Pokémon.com ou pour des statistiques tierces n'est établi. Une politique `synthetic_author_owned` donnée artificiellement à un vrai contenu ne constituerait **pas** une autorisation juridique; l'usage doit être explicitement interdit dans un essai live.
- L'extracteur reconnaît une formulation fabriquée. Il **n'est pas testé contre la structure ou la langue actuelle des pages officielles**; on ne peut pas certifier une rotation réelle ni la légalité, les équivalences de réimpression, le support Live ou une date d'application.
- Les fenêtres méta multi-tournois ont été montées sur fixtures : le **cache du chat actuel** ne contient généralement qu'un tournoi et peut manquer les seuils. Il ne faut ni fusionner artificiellement les périodes ni qualifier une tendance générale à partir de cette petite sélection.
- Une extraction révisée ou une comparaison descriptive n'est ni preuve causale d'amélioration d'un deck, ni test avec journal personnel. Aucune nouvelle permission de migration/backup/scheduler/OCR ne résulte de ce lot.
- Déclaration « worktree Windows propre » seulement **rapportée par Codex** (GitHub ne lit pas son disque local).

## CI exacte, indépendante des tests Windows locaux
- Run code [40561047533](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40561047533) au commit `27aa7919553809f5b7af29a3437ebb60e50854c0`, `completed/failure`; jobs Windows `122389827214`, Ubuntu `122389827603`, **steps=[]** chacun.
- Deux runs au HEAD `35627627dba24bfc156e5fb6b277ac585cebe045` : [40561185635](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40561185635) et [40561196478](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40561196478), `completed/failure`; quatre jobs Windows/Ubuntu `steps=[]` vérifiés.
- Budget Actions cité comme cause par Codex, cohérent avec jobs vides; **annotations non vérifiées indépendamment par ChatGPT**. Zéro étape CI réellement exécutée, aucun ancien vert transférable, aucun rerun ni modification facturation.
- Un nouveau commit documentaire d'audit aura son propre SHA et potentiel run, **non déclaré vert par anticipation**.

## Verdict et prochaine action

**AUDITED_STATIC_SYNTHETIC_SOURCE_DEPTH_DELIVERED_REAL_SOURCE_QUALIFICATION_PENDING_CI_PENDING.** Le mandat fictif est audité et ne présente pas de nouvelle erreur bloquante confirmée dans son périmètre statique; la prochaine porte métier est de qualifier la fiabilité, les droits et la faisabilité sur **de vraies sources publiques**. V1 **NOT_RELEASE_READY** : CI, légalités/règles/Live, profondeur réelle, réception avec données du propriétaire, SQLite7 personnelle→13, OCR, restauration/backup, planificateur et Ollama restent ouverts. Option B : shells Codex/Claude non isolés, consentement explicite requis.

Mandat unique `PM-V1-PUBLIC-LIVE-SOURCE-PILOT-001` **préparé, non autorisé** (`execute_now=false`). Il prévoit, seulement si l'utilisateur l'autorise distinctement et consciemment, une reconnaissance **publique bornée à 17 GET/24 Mio maximum**, sans accès privé, sans contournement, sans persistance non licenciée; STOP si droits ou sources insuffisants. La simple publication du présent audit **n'autorise aucun GET**, aucun agent, aucun achat ni exécution.
