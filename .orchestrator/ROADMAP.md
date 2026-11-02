# PokeMind — roadmap V1 par preuve de valeur (rév. 2026-10-10, cerveau autonome planifié)

**État prioritaire 2026-10-15 : LOT J J0–J6 livré pour audit ChatGPT** sur
`work/pm-v1-lotj-final-readiness-windows`. V1 NOT_RELEASE_READY, A–I conservés.
Voir matrice A–J/QA et plan propriétaire cinq décisions; dernier HEAD/CI exacte
à auditer, pas le seul checkpoint58eb481. OCR PATH fail-closed, prévol FTS mémoire,
couverture actuelle et dry-run Windows renforcés; aucun nouveau supportLinux.
Catalogue/normes/Live/méta/récupération/chiffrement/purge/visionréelle/scheduler
demeurent partiels/bloqués comme détaillé dans LOT_J_ACCEPTANCE_MATRIX.
Pas de LOTK automatique : audit J puis actes terrain précis et travaux ciblés
seulement s'ils ont un défaut/mandat concret. Aucune permission privée implicite.
Les états I/H/G/F/E ci-dessous sont des archives historiques.

**État actif 2026-10-15 : LOT I I0–I7 développé pour audit ChatGPT**, branche I
exclusive, sans repriseA–H. Premier usage synthétique Windows démontré par `demo`;
catalogue/normes/méta, OCR terrain, reprise opérationnelle et scheduler OS restent
partiels/bloqués. Matrice exhaustive : `docs/LOT_I_ACCEPTANCE_MATRIX.md`.
QA : `docs/LOT_I_QA_REPORT.md`; suite proposée uniquement :
`docs/LOT_J_COMPLETION_PLAN.md`. V1 NOT_RELEASE_READY, STOP après publication I
et contrôle CI au SHA final. Aucun nouveau mandat J ni fonction Linux.

**Objectif inchangé :** un cerveau Pokémon TCG Live spécialisé, toujours exploitable dans Codex, connaissant règles, cartes, decks et métagame, améliorant les conseils à partir des combats et capable plus tard d'accompagner les entraînements par images non conservées. « Apprendre » = accumuler des observations et corrections structurées; pas de réentraînement de LLM.

| Tranche | Livrable concret | État |
|---|---|---|
| PM-0001 | 4 volumes Markdown, index local SQLite FTS5, CLI, tests | ACCEPTÉE POUR SUITE sous réserve prévol; voir `VERIFICATION_PM-0001.md` |
| PM-0002 | Importer 5–10 journaux, profil de deck observé, premières statistiques, bilan prudent et idempotent | LIVRÉE mais NON VERIFIED : voir `VERIFICATION_PM-0002.md` | 
| PM-0002R | Corriger référence joueur, W/L ambigu, attaques prises pour cartes, réimportation sûre | CODE ACCEPTÉ (revue statique); test terrain manquant, voir `VERIFICATION_PM-0002R.md` |
| PM-0002T | Valider avec export réel W et L; corriger divergence observée | LIVRÉE, AUDIT CODE ACCEPTÉ, n=2 rapporté; voir `VERIFICATION_PM-0002T.md` |
| PM-0003 | **Importer une liste de 60 cartes, versionner sans altérer les combats et rendre l'import de journaux simple dans Codex** | **LIVRÉE, NON VERIFIED** : format réel du deck à valider; voir `RESULT.md` |
| PM-0003E | Exporter un deck en .txt prêt à importer dans TCG Live et préparer un candidat de 60 cartes | **FIELD_VALIDATED sur un vrai deck 60/60**, voir `VERIFICATION_PM-0003E-FIELD.md` | 
| PM-0003F | Corriger trois observations suspectes de cartes dans les journaux | CODE ACCEPTÉ après audit; mémoire ancienne PARTIELLE (3/5 originaux), voir `VERIFICATION_PM-0003F.md` |
| PM-0004 | Fondation catalogue TCGdex FR/EN, sync bornée, provenance et recherche offline | **CODE ACCEPTÉ (audit statique), catalogue très PARTIEL**; voir `VERIFICATION_PM-0004.md` |
| PM-0004B | Sync par phases, refresh manuel, couverture FR/EN, schema 5 | **LIVRÉE MAIS CORRECTIF REQUIS** : voir `VERIFICATION_PM-0004B.md` |
| PM-0004B-R1 | Corriger conservation des absences HTTP 404 après refresh; recontrôle uniquement explicite | **CORRECTIF ACCEPTÉ en revue statique** ; voir `VERIFICATION_PM-0004B-R1.md` |
| PM-0005A | Sources Pokémon officielles, moteur de légalité daté, CLI offline | **LIVRÉE — CORRECTION REQUISE** : `VERIFICATION_PM-0005A.md` |
| PM-0005A-R1 | Empêcher un faux verdict deck `legal`; rendre cohérents les statuts source/assertion | **CORRECTIF ACCEPTÉ en revue statique indépendante**, voir `VERIFICATION_PM-0005A-R1.md` |
| PM-0005B | API Limitless Tournament Platform, tournois publics, archétypes et matchups hors ligne | **LIVRÉE — CORRECTIF NÉCESSAIRE**, voir `VERIFICATION_PM-0005B.md` |
| PM-0005B-R1 | Progression inter-sessions simple, refus des tournois privés avant standings, sécurisation redirections et quota | **CODE ACCEPTÉ pour périmètre immédiat, MAIS R2 REQUISE** : `VERIFICATION_PM-0005B-R1.md` |
| PM-0005B-R2 | État scoped de découverte/skip, checkpoint profond et reprise bornée | **ACCEPTÉE EN REVUE STATIQUE** : `VERIFICATION_PM-0005B-R2.md` |
| PM-0006A | Diagnostic de deck/combats en lecture seule, provenance et limites de preuve | **LIVRÉE, CORRECTIF R1 NÉCESSAIRE** : `VERIFICATION_PM-0006A.md` |
| PM-0006A-R1 | Dates de preuves, version historique, erreurs caviardées | **ACCEPTÉE EN REVUE STATIQUE** : `VERIFICATION_PM-0006A-R1.md` |
| PM-0006B | Comparaison factuelle des versions et audit des liens combat→version | **ACCEPTÉE en revue statique** : `VERIFICATION_PM-0006B.md` |
| PM-0006C | Attestation manuelle/révocable combat→version, provenance UTC, tests synthétiques | **ACCEPTÉE EN REVUE STATIQUE** : `VERIFICATION_PM-0006C.md` |
| LOT A V1 | Fondation catalogue TCGdex FR/EN, fiches/reprints, règles structurelles sourcées, métriques Limitless, audit qualité | **ACCEPTÉE en revue statique pour les mécanismes, données PARTIAL** : `VERIFICATION_LOT_A.md` |
| LOT B V1 | B0 quotas TCGdex; B1 collection/crédits; B2 recommandations; B3 leçons; B4 candidats/export; B5 E2E | **LIVRÉ, REVUE STATIQUE AVEC RÉSERVES B2/B4** : `VERIFICATION_LOT_B.md` |
| LOT C V1 | C0 corrections, captures privées, annotations, mémoire textuelle, conseils conditionnels, CLI/E2E | **FONDATION ACCEPTÉE EN REVUE STATIQUE**, C2/C4/C5 PARTIAL : `VERIFICATION_LOT_C.md` |
| LOT D V1 | D0 coach, D1–D4 collecteurs publics/cadence/reprise/offline, D5 scheduler Windows dry-run | **FONDATION ACCEPTÉE EN REVUE STATIQUE AVEC RÉSERVES E0** : `VERIFICATION_LOT_D.md` |
| LOT E V1 | E0 correctifs update; E1–E2 backup/restore/rétention; E3 privacy; E4 CI Windows/Linux; E5 lacunes; E6 V1 readiness | **FONDATION ACCEPTÉE STATIQUEMENT, RESTORE/PURGE RÉELS BLOQUÉS**, V1 NOT_RELEASE_READY : `VERIFICATION_LOT_E.md` |
| LOT F V1 | Sûreté SQLite, adaptateur PNG marqueurs synthétiques, couverture publique partielle, E2E/CI/readiness | **LIVRÉ, FONDATIONS ACCEPTÉES STATIQUEMENT MAIS RESTORE RÉEL BLOQUÉ** : `VERIFICATION_LOT_F.md` |
| **LOT G V1** | **G0 rollback et fail-closed; G1 contrat OCR optionnel; G2 stale/reprise/normes; G3 E2E/CI; G4 toutes portes readiness; G5 passation** | **LIVRÉ POUR AUDIT INDÉPENDANT**, branche `work/pm-v1-lotg-real-vision-readiness`, matrice `docs/LOT_G_ACCEPTANCE_MATRIX.md`; V1 NOT_RELEASE_READY |
| LOT H V1 | H0–H5 : sûreté/fail-closed, corpus OCR, revues, snapshots, prévols et cadence, gates/CI | DÉVELOPPÉ ET LIVRÉ POUR AUDIT CHATGPT; matrice `docs/LOT_H_ACCEPTANCE_MATRIX.md`; V1 NOT_RELEASE_READY |
| PM-0007 | Coach visuel ponctuel en entraînement autorisé, images non archivées, test réel Codex Windows | PLANIFIÉE — mémoire/coach | 
| PM-0008 | Collecteurs publics incrémentaux : vérification quotidienne légère, réconciliation mardi/vendredi, planificateur Windows après opt-in, validation/rollback/offline | PLANIFIÉE — actualisation autonome | 
| PM-0009 | Sauvegarde/restauration SQLite locale, audit confidentialité, bilan source/qualité/méta, tests Windows, préparation V1 | PLANIFIÉE — stabilisation |

Les étapes futures peuvent être réordonnées seulement pour une dépendance réelle démontrée. **L'interface reste Codex uniquement** : ne pas créer de serveur, interface navigateur ou plugin distant sans nouvelle demande de l'utilisateur. **Feu vert permanent de l'utilisateur pour la progression ordinaire :** après audit indépendant de chaque livraison, ChatGPT prépare directement la tranche suivante ou un correctif, sans nouveau « go ». Codex exécute une tâche à la fois. PM-0006C attend son audit indépendant; PM-0006C+ à PM-0009 restent futures; pas de merge, dépense, suppression privée ni installation de tâche Windows sans décision distincte. La cadence quotidienne demeure une cible non installée.

Architectures de référence : `docs/ARCHITECTURE_CERVEAU_AUTONOME.md` et `docs/SOURCES_CONNAISSANCES.md`. Conserver le schéma SQLite/FTS5 existant, le travail hors ligne et l'absence d'images personnelles stockées par PokeMind. À partir des 5 premières parties, rapport prudent; **10 parties et plus améliorent la solidité**, sans garantie statistique. Ne pas inférer la collection complète à partir des cartes vues. Les fiches de decks conservent historique et provenance. Chaque étape est livrée puis vérifiée séparément. PM-0003T : 5 parties (4 W / 1 L) rapportées par Codex; les trois observations suspectes ont été corrigées sous PM-0003F, mais deux vieux journaux demeurent sans original et n'ont pu être réanalysés. Les exports prêts pour TCG Live ne valent pas optimisation des decks ni preuve de légalité ou collection.


## Politique d'autonomie confirmée (2026-10-12)
Le propriétaire veut des **tâches plus grosses, une autonomie Codex accrue, sans sauter ni supprimer une seule fonction V1**. Lire `.orchestrator/AUTONOMY_POLICY.md` et `.orchestrator/V1_BATCH_PLAN.md`. Codex planifie, implémente, teste, corrige et commit plusieurs sous-tâches dans la seule branche du lot; ChatGPT audite **en fin de lot**, pas après chaque petite correction. Aucune fonction partielle ne devient DONE sans preuve. Pas de merge, compte, crédit, suppression privée ni planificateur Windows par autorisation implicite.


## Audit LOT A et héritage intégral (2026-10-13)
`.orchestrator/VERIFICATION_LOT_A.md` accepte les **mécanismes** A1–A5 en revue statique, mais maintient le catalogue mondial et les réimpressions, règles et meta incomplets (`PARTIAL_WITH_EVIDENCE`), Trainer Hill (`BLOCKED_WITH_REASON`). 230 tests réussis rapportés par Codex, pas de CI indépendante. Une correction du budget HTTP TCGdex suivant redirects est imposée comme première sous-tâche **B0** avant sync importante. **Aucune fonctionnalité du LOT A ou des LOTS C/D/E n'est éliminée**; continuer les lacunes publiques et la qualité jusqu'à preuves mesurées. LOT B se livre d'un bloc autonome avec audit ChatGPT final.


## Audit LOT B — correction intégrée au LOT C (2026-10-13)
`.orchestrator/VERIFICATION_LOT_B.md` : LOT B livré, mécanismes B0–B5 inspectés, mais **B2 recommandations historiques** et **B4 validation structurelle des candidats** ne sont pas entièrement approuvés avant corrections C0. Erreurs : snapshots collection/crédits postérieurs à `--as-of` utilisés comme preuves historiques; exigence infondée des trois sections Pokémon/Trainer/Énergie; catégorie publique incompatible avec la section déclarée non vérifiée. C0 est une porte de qualité **obligatoire avant le parcours de coaching visuel**, exécutée dans le **même grand LOT C** plutôt qu'une microbranche. Catalogue/reprints/règles/méta A partiels, Trainer Hill bloqué, LOTS D et E prévus, aucun objectif supprimé.


## Audit LOT C et dette D0 — 2026-10-13
Audit `.orchestrator/VERIFICATION_LOT_C.md` : C0/C1/C3 acceptés pour la fondation, C2/C4/C5 partiels, aucun moteur de vision installé ni lecture réelle de screenshots prouvée. Corriger D0 dans le grand LOT D (pas microbranche) : ne pas accepter provenance `visual_certain` venant d'une annotation manuelle sans backend; ne pas annoncer ressources d'une attaque suffisantes à partir du seul compte d'énergies sans types; recouper contexte/date/format de séance; assurer corrections/revocations/restauration non faussement dédoublonnées. **Ne pas effacer l'objectif reconnaissance visuelle réelle**. LOTS D/E, couverture cartes/règles/reprints/métagame et Trainer Hill restent obligatoires. Installation de planificateur Windows jamais implicite.


## Livraison Codex LOT D — audit requis, 2026-10-13
Codex livre D0–D5 sur `work/pm-v1-lotd-public-knowledge-updates` : correctifs du coach,
orchestrateur public sans LLM, cycles quotidiens/profonds, cadence `America/Toronto`,
verrou/reprise/alertes/offline, CLI/skills et manifests Windows simulés. La matrice
`docs/LOT_D_ACCEPTANCE_MATRIX.md` conserve les données publiques réelles comme
`PARTIAL_WITH_EVIDENCE`, Trainer Hill et l'installation scheduler comme
`BLOCKED_WITH_REASON`. Aucun statut `VERIFIED`, aucune sync réelle de la base privée,
aucune tâche Windows, aucun merge. LOT E et les limites A/B/C restent obligatoires.


## Audit LOT D et portes qualité du LOT E — 2026-10-13
`.orchestrator/VERIFICATION_LOT_D.md` : D0–D5 mécanismes livrés et fondation acceptée statiquement, mais E0 indispensable avant mise en service : comptes GET sous exceptions de clients internes peuvent annoncer 0 malgré requêtes, les tâches Windows simulées dépendent du fuseau local Windows sans contrôle Toronto. **Scheduler réel NON installé/activé** et doit rester sous consentement spécifique. Catalogue exhaustif, reprints, règles officielles/compatibilité Live, métagame, Trainer Hill, coach avec vraie vision locale, vrai smoke test et migrations sur base personnelle demeurent des objectifs V1 **non terminés**. LOT E NE DOIT PAS les supprimer, les fermer fictivement ou déclarer release V1 entière sans preuves. Rester sur gros lots autonomes, audit ChatGPT à fin de lot.


## LOT E — acceptation honnête et suite possible (2026-10-13)
Après l'audit LOT D `.orchestrator/VERIFICATION_LOT_D.md`, LOT E travaille E0–E6 en un grand lot autonome, correction des compteurs GET après échec, timezone des tâches et **transmission de la date/heure deep** du lanceur à l'historique. Aucun scheduler Windows n'est installé ou activé sans nouvel accord explicite. Les capacités fondamentales incompletes — catalogue FR/EN complet et réimpressions, règles officielles/promos/errata/compatibilité Live, méta, Trainer Hill, **vision locale réelle pour analyser screenshot sans annotation**, vrai smoke test, données propriétaire non attestées — restent obligatoires. **Ne déclarer V1 complète que si les preuves satisfont les critères complets**; sinon préparer LOT F ou suivantes sans supprimer de ligne. La cadence de grande autonomie Codex et audit ChatGPT de fin de lot demeure en vigueur.


## Livraison Codex LOT E — audit requis (2026-10-13)

E0–E6 sont livrés sur `work/pm-v1-lote-reliability-release` avec backup/restore/
rétention synthétiques, caviardage, E2E et workflow CI Windows/Linux. Les tests Codex
annoncent 313 réussis et 1 skip; la CI no 38504190576 est observée verte sur Windows
et Ubuntu au SHA `3c252f6`, sans remplacer l’audit indépendant.
`docs/V1_READINESS_REPORT.md` conserve le verdict `NOT_RELEASE_READY` : vision locale
réelle absente, connaissances publiques partielles, Trainer Hill bloqué, scheduler
non activé et données owner non appliquées. LOT F reste obligatoire après audit;
aucune fonction V1 n’est retirée.


## Audit indépendant LOT E (2026-10-13)
`.orchestrator/VERIFICATION_LOT_E.md` : **313 passed et 1 skip** selon Codex, **GitHub Actions CI vérifiée verte sur le HEAD final Windows + Linux** (run `38504484245`); mécanismes de récupération et connaissance livrés. **Prohibition de restore apply ou retention apply sur les vraies données** tant que F0 n'a pas corrigé le hash de backup validé seulement après publication, les sidecars SQLite WAL/SHM avec cible ouverte, et le plan de rétention non revalidé par checksum. La V1 reste `NOT_RELEASE_READY` : vision réelle C2, catalogue et règles/Live exhaustifs, Trainer Hill, activation de scheduler et données propriétaire sont toujours PARTIAL/BLOCKED. Le grand LOT F doit continuer ces fonctions; **ne rien supprimer, ne pas déclarer V1 terminée artificiellement**.


## Audit LOT F, porte critique G0 (2026-10-14)
Audit indépendant `.orchestrator/VERIFICATION_LOT_F.md`, code livré `0ad1db0d55173221fd3896135c034c98deb2ae91` ; CI GitHub Actions Windows et Ubuntu verte au SHA final, run `38509791786`; 328 tests verts/1 skip selon Codex. **G0 obligatoire :** après `os.replace(temporary,target)`, `sqlite3.Error` issu de la vérification publiée ne déclenche pas le rollback, et `except OSError` ne restaure l'ancienne cible que quand le nouveau target n'existe pas. Le verrou SQLite exclusif est relâché avant remplacement. **Aucune vraie restauration/purge** tant que ces défauts ne sont pas réparés/audités avec tests d'injection et coordination offline. F1 décode des marqueurs de couleurs synthétiques et non des cartes réelles. Tous les écarts catalogue/règles/reprints/Live/méta et Trainer Hill restent partiels/bloqués, scheduler non activé, vraie collection/parties sous contrôle propriétaire. `V1 NOT_RELEASE_READY`; ne rien supprimer de la roadmap.


## Audit indépendant LOT G et mandat LOT H (2026-10-14)
Le LOT G (G0–G5) est livré au SHA `9b19644ed3990befc569d25a29928e08400b1a42`, run CI `38600129548` Windows et Linux **389 pass/1 skip chacun**. Audit indépendant `.orchestrator/VERIFICATION_LOT_G.md` : mécanismes acceptés pour suite avec réserves; restore cible existante fail-closed, OCR encore seulement contrat mock, TCGdex/normes/reprints/Expanded/Live/méta incomplets, Trainer Hill bloqué et scheduler non activé. **V1 NOT_RELEASE_READY**; aucun objectif n'est abandonné. Grand LOT H H0–H5 préparé sur `work/pm-v1-loth-completion-readiness` avec mandat `.orchestrator/NEXT_PROMPT.md`; actes propriétaire, vraie capture, installation et merge restent interdits sans consentement distinct. Après livraison, audit ChatGPT indépendant et éventuel LOT I+.

## Reprise de publication H — constat local prioritaire (2026-10-14)

Aucune exécution H retrouvée dans le dépôt ouvert : worktree initial propre sur G,
pas de branche locale H ni untracked/stash; après fetch H `74574d6…` ne comporte
que sept commits documentaires de préparation. Objets orphelins anciens, sans H.
Le diagnostic publié dans `docs/LOT_H_RECOVERY_REPORT.md` et sa QA de base
(388 passed/2 skipped) ne constituent pas la livraison H0–H5. Localiser le chemin,
la branche ou le SHA du travail annoncé avant reprise; ne pas recommencer H.
Tous les objectifs et blocages V1 sont conservés, NOT_RELEASE_READY; aucun LOT I
exécuté ou nouvelle permission personnelle inférée.


## Audit du diagnostic H, exécution initiale H autorisée (2026-10-14)
Le commit `cde321c` et la CI `38650014924` vérifiée Windows/Linux 389 pass/1 skip sont un **diagnostic de recherche**, non un LOT H livré. Le dépôt examiné n'a aucun H0–H5 développé; les suites testées sont héritées de G. Après audit indépendant `.orchestrator/VERIFICATION_LOT_H_RECOVERY.md`, l'action **n'est plus d'attendre un SHA H hypothétique** : démarrer réellement H0–H5 depuis les fondations vérifiées A–G, sur la branche H existante, suivant `.orchestrator/NEXT_PROMPT.md`. Ne pas recommencer le projet ni supprimer une capacité V1. Mise en service propriétaire, captures, installations et merge toujours sous consentement distinct. V1 NOT_RELEASE_READY.

## État actif prioritaire — développement H0–H5 livré (2026-10-14 Québec)

La première exécution H a produit code/tests et plusieurs commits 420a 8 fa, b 056218,
a 1647 fb, puis rapports. Les anciens constats « H non retrouvé/à développer » sont
historiques. Protection fail-closed existante conservée et purge maintenant bloquée,
attestations/publications renforcées; corpus rasterisé 22/88, store de revues,
snapshots datés, revue documentaire, prévol owner-plan, cadence/DST et gates livrés.
Les tests locaux/CI exacts sont dans LOT_H_QA_REPORT et les résumés Actions au HEAD.
V1 NOT_RELEASE_READY; toutes capacités A–H restent dans la matrice. OCR/essai réel,
normes/catalogue/reprints/Live/méta complets, accès Trainer Hill, récupération sûre
et activation propriétaire/OS sont encore PARTIAL/BLOCKED. STOP audit ChatGPT;
LOT_I_COMPLETION_PLAN propose la suite sans la mandater. Aucun acte privé ni merge.


## Audit indépendant LOT H et lancement documentaire LOT I (2026-10-14)
Livraison H0–H5 `5d27832ac8933bb30eaa95430eecfd10fe8cf75e` sur H, CI GitHub Actions `38678350634` au **SHA exact** : Windows+Ubuntu 416 passed/2 skipped chacun dans les vrais logs, 42 fichiers/4 commits depuis le mandat. Verdict `.orchestrator/VERIFICATION_LOT_H.md` : **code technique H accepté pour suite avec réserves**, V1 NOT_RELEASE_READY. Retention apply, restore sur cible existante, vrai OCR/calibration, couverture historique/normative, Trainer Hill, activation Windows et essais propriétaire bloqués/partiels; ne pas les supprimer.

Grand LOT I documentaire créé sur branche `work/pm-v1-loti-windows-completion`, `.orchestrator/NEXT_PROMPT.md`, `docs/LOT_I_EXECUTION_PLAN.md`. **Windows 11/Codex prioritaire**; aucune extension Linux sans demande utilisateur, CI Linux existante conservée pour régressions. Codex exécute I0–I7 sans micro-go puis audit indépendant ChatGPT. Aucun merge ni donnée privée.


## Livraison et audit indépendant LOT I, lancement documentaire J (2026-10-15)
Code LOT I `aade0fd6b3594e0198c304d472931a0fb6793a0b`, branche `work/pm-v1-loti-windows-completion`, 3 commits et 32 fichiers depuis préparation. CI dernier SHA run `38682727093` : Windows et Ubuntu **429 pass/2 skips chacun**, logs lus directement. Audit ChatGPT `.orchestrator/VERIFICATION_LOT_I.md` : **code accepté pour suite avec réserves**, démo synthétique Windows/Codex et protections publiques livrées; **V1 NOT_RELEASE_READY**. OCR réel absent, historique FR/EN/règles non complets, vrai deck/parties/backup/clone/scheduler encore à valider, purge et remplacement existant bloqués. Ne supprimer aucun objectif.

Branche documentaire `work/pm-v1-lotj-final-readiness-windows` et grand mandat J0–J6 : sécurité OCR PATH, couverture/sources autorisées, parcours Windows, protection SQLite, cadence dry-run et plan d'actions consenties pour essais réels. **Windows priorité, aucun élargissement Linux**; conserver seulement CI régression héritée. Après J, si le manque est seulement des permissions/essais propriétaire, demander ces choix plutôt que lancer mécaniquement un nouveau lot.
