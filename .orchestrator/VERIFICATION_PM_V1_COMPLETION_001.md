# Audit indépendant ChatGPT — PM-V1-COMPLETION-001

**2026-10-22 Québec. Verdict : `VERIFIED_GITHUB_IMPLEMENTATION_AND_CI_SCOPE_ONLY`; livraison `PARTIAL`. V1 `NOT_RELEASE_READY`.**

## GitHub et tests réellement vérifiés

- HEAD de branche `work/pm-v1-lotj-final-readiness-windows` au moment de l'audit : [`beed12f9ff70b4495a6928f6982f4276666e0fab`](https://github.com/Sd-tech-Sol/PokeMind-dev/commit/beed12f9ff70b4495a6928f6982f4276666e0fab). Diff avec `7e21676b94262d62090741c99a8b865d50f9088d` : **1 commit, 36 fichiers**, dont corrections de code, tests et rapports. Aucun nom de fichier ou code versionné indiquant une publication de base, captures ou journaux personnels dans le diff inspecté.
- [GitHub Actions 39726173391](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39726173391) **completed/success**, `head_sha=beed12f9ff70b4495a6928f6982f4276666e0fab`, déclenché au push. Jobs et logs lus indépendamment : **Windows606 passed/2 skipped** (`119650463946`) et **Ubuntu605 passed/3 skipped** (`119650464133`), `ci_evidence=TECHNICAL_TESTS_GREEN` au SHA. Passages hygiène et `git diff --check` dans les deux jobs.
- Les **deux tests OCR sont ignorés en CI** faute de moteur attesté dans ces environnements; le troisième skip Ubuntu est un essai de junction Windows. Donc **CI verte ne prouve pas l'exécution réelle de Tesseract**.
- Le prévol antérieur `39714543936` au HEAD `7e21676...` et l'arbre local propre sont rapportés par Codex; leur éventuelle exécution sur le PC ne découle pas des tests GitHub.

## Code lu et constats indépendants

- `decks.show_deck`, `profiles.profile_summary`, `profile_review` utilisent maintenant `connect_readonly`; `database.connect_readonly` encode l'URI avec `Path.as_uri()`, `mode=ro`, `PRAGMA query_only=ON`. Tests dédiés aux cas spéciaux et connexions non mutantes. Ceci corrige le chemin de lecture qui pouvait entraîner une initialisation implicite.
- `battle_sample.conservative_sample` filtre **en mémoire** des équivalences de journaux inter-parseurs de manière conditionnelle (au moins12 événements, 3 tours, métadonnées cohérentes). Exclusion **probable**, pas identité de partie attestée, pas fusion/DELETE ni transfert de version. Analyse/profils/readiness utilisent ce bilan de prudence; ne pas annoncer un taux personnel exact si le doublon n'est pas confirmé.
- `cards.CatalogApiClient` différencie HTTP connu et erreurs neutres, ferme les réponses, applique des plafonds de requêtes et de corps. `scripts/collect_public_catalog.py` exige un **nouvel espace PUBLIC**, plan par défaut sans réseau, budget cumulatif et `maximum_attempts=1`, redirections interdites, marqueur/DB revus, STOP au premier échec; tests synthétiques d'enveloppe et HTTP503 vérifiés en code. Cela **ne garantit pas** la disponibilité ni la stabilité de TCGdex.
- `scripts/pokemind_update.ps1` exige une base explicitement choisie, `--public-only`; le planificateur conserve ses prévisualisations et ne démontre aucune activation Windows réelle.
- La politique OCR étend l'inventaire de confiance aux DLL/TSV et exige une version exacte; **cela ne certifie ni signature du binaire ni taux de reconnaissance réel**.
- Tests/CI démontrent des chemins du code. Pas d'audit indépendant de l'OS ou des fixtures privées.

## Preuve locale Codex, non vérifiable depuis GitHub

- **Campagne PUBLIQUE neuve rapportée** :199GET/50000,1 864 262octets,198pages valides,9500membres de cartes par langue, union10 303 impressions, **0 détail récupéré**; `HTTP503` à `cards:en` page96. La cause fournisseur du 503 et celle de l'ancien échec restent inconnues. Aucun appel après STOP déclaré, **49 801GET restants non autorisés pour nouvelle tentative**. Nombre total actuel de cartes non établi. Les rapports de collecte brute et le cache ne sont pas dans Git; ces compteurs sont donc `RAPPORTÉ_PAR_CODEX_LOCAL`.
- **OCR portable exécuté sur PC selon Codex** : moteur 5.5.3.20260724, eng/fra,55DLL AMD64.22 cas/88champs synthétiques : **88 abstentions,0 champ accepté** au seuil95%. Cela prouve au mieux une exécution contrôlée et un refus prudent, **aucune reconnaissance utile**. Revue des binaires et contrôle hash `operator_reviewed`, signatures/audit supply-chain indépendant non établis. Pas de capture réelle utilisateur ni calibration.
- La demande et les deux permissions spécifiques sont consignées par Codex : « Autoriser OCR portable et tests », « Autoriser cette collecte complète bornée ». **Consommées**, ne valent pas installation d'OS, nouveau GET ou accès privé.
- Deux anciens dossiers de fixtures auraient eu un nettoyage bloqué par la politique locale. Aucun contournement n'est déclaré. GitHub **ne peut pas confirmer leurs états locaux**, mais le diff n'inclut ni leur suppression ni leurs contenus : **pas de commande de purge à réessayer**.

## Décision de l'audit

**Accepter le lot technique dans sa portée code + CI; ne pas accepter la V1 comme prête.** Le format d'import TCG Live reste **`FIELD_VALIDATED` depuis le 2026-10-11**, sans nouveau test. Le produit peut déjà servir à l'analyse et à la proposition prudente de decks avec Codex; les garanties V1 complètes restent bloquées.

Étapes manquantes non artificiellement clôturées : **source catalogue FR/EN et détails**, règles/errata/réimpressions/Live et classements compétitifs vérifiés, **qualité/calibration OCR et3captures d'entraînement autorisé**, **preuve d'installation et de fonctionnement du scheduler Windows après nouvel accord**, **récupération/protection/ACL/rétention réelles et autorisées**, attestations owner et audit release final. L'avis de cadence 08:15 et19:30 mardi/vendredi Toronto n'est pas une permission de configuration OS.

**Prochain état : `BLOCKED_REAL_WORLD_EVIDENCE`**, aucun mandat exécutable sans nouvel ordre précis. Ne pas rejouer les budgets ni l'ancienne campagne, contourner le nettoyage bloqué, simplifier silencieusement la roadmap ou prétendre tester la machine du propriétaire depuis GitHub. Une nouvelle tranche technique pure sur fixtures pourra être autorisée séparément si elle a un objectif concret et vérifiable. **STOP.**
