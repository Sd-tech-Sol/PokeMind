# PM-RELEASE-096-PUBLIC-025 — STOP PUBLICATION 0.9.6 À L'ÉTAPE 4 / DÉCISION DU PROPRIÉTAIRE (2026-11-20, D-320)

**Aucun mandat d'exécution actif.** Le GO D-320 (publier 0.9.6 en préversion) s'est arrêté à l'étape 4 : deux
captures `style-global/06-reglages-4-data-*` montrent un chemin absolu avec le nom du compte Windows. **Rien de
public** : `main` public toujours `295db53`, aucun tag, release ni asset v0.9.6. Commit privé de préparation
`81580b0`; porte 1946 / 0 / 3; Setup `688d8651…d137` revérifié, scan CLEAN. Détails : [RESULT](RESULT.md).
**Prochaine action : décision du propriétaire.** Aucune relance automatique; une nouvelle publication exige un
nouvel ordre explicite.

# Historique — PM-RELEASE-096-LOCAL-INSTALL-024 — 0.9.6 INSTALLÉE LOCALEMENT (2026-11-19, D-319)

Réception du propriétaire faite le 2026-11-20 : **OWNER_GUI_ACCEPTED_096**.

**Aucun mandat d'exécution actif.** D-319 et ses deux extensions exécutés par Claude Code : fusion `1e3d483`, 0.9.6
`215e1f4`, mise en page `5eee9c9`, plantage de la QA native corrigé (`c34f32e`, `8d2bd62`). **SHA source de l'EXE :
`8d2bd62`**. Porte complète verte 1946 / 0 / 3; QA native verte 5 fois de suite à 100 % et 125 %; scan CLEAN; fumée
et QA Inno vertes; sauvegarde et copie 0.9.5 vérifiées; Setup lancé **une fois**, code 0; 0.9.6 installée, données
conservées. Setup SHA256 `688d865144b2bff064778fbfe90ffbd599ce0ccc3c8bf9843d4b961f54bad137`. Détails :
[RESULT](RESULT.md). **Prochaine action : réception par le propriétaire** (ouverture et vérification de 0.9.6), jamais
inférée. Aucune deuxième installation. Publication non autorisée.

Mandat d'origine (D-319) : fusion de
`work/ui-premium-look` dans `work/pm-v1-lotj-final-readiness-windows`, version **0.9.6**, porte locale complète,
build et QA (comme 017 A et B), nouvelle sauvegarde complète vérifiée et copie de l'installation 0.9.5 (comme 017
C), puis **UNE seule** installation locale du Setup de production (comme 017 D), rapport et arrêt.
Toute porte rouge = STOP. **Publication non autorisée** (aucun tag, release ni dépôt public).

# PM-UI-PIPELINE-023 — TERMINÉ / POUSSÉ / EN ATTENTE DU PROPRIÉTAIRE ET DE L’AUDIT (2026-11-18, D-318)

**Aucun mandat d’exécution actif.** Le pipeline autonome en 8 phases (D-318) est terminé sur `work/ui-premium-look`
et poussé vers le dépôt privé. Porte complète verte à `0d0ae08` (1928 réussis / 0 échec / 3 ignorés), aucune phase
annulée. Détails : [RESULT](RESULT.md). Planches : `docs/design/pokemind-brainball/captures/pipeline-023/`.
**Prochaine action : le propriétaire vérifie le résultat, puis audit indépendant.** Aucune fusion, aucun tag, aucune
publication, aucune installation, aucune sauvegarde sans nouvel ordre.

**Suite du 2026-11-19 (GO explicite) :** style des boutons d'idées par défaut partout (`54b41c4`, `43e7678`),
porte complète verte à `43e7678` (1943 réussis / 0 échec / 3 ignorés), planches
`docs/design/pokemind-brainball/captures/style-global/`. Puis gras du Coach à 700 (`0b7c76c`, porte verte,
1943 / 0 / 3). Même prochaine action.

**Audit 019 : passé et clos** (déclaration du propriétaire, 2026-11-18). Le bloc 019 ci-dessous est historique.

# PM-UI-CRITIQUE-022 — TERMINÉ / EN ATTENTE DU PROPRIÉTAIRE (2026-11-18, D-317)

**Aucun mandat d'exécution actif.** Claude Code a appliqué, sur `work/ui-premium-look`, les 10 points de la
critique du look premium (D-317), un commit par point de `7324933` à `f368ad1` (plus `536acc9`), après la refonte 020 (D-315) et
la simplification 021 (D-316). Porte locale complète verte (1900 réussis / 3 ignorés). Planches
avant/après : `docs/design/pokemind-brainball/captures/critique/`. Détails et choix à signaler : [RESULT](RESULT.md).
**Rien n'est poussé.** Prochaine action : **le propriétaire** regarde le résultat et décide (corrections, push,
suite). Aucune donnée personnelle, installation, build ou publication sans nouvel ordre.
L'audit de 019 est depuis passé et clos (D-318).

# PM-V1-PUBLIC-RELEASE-GATE-019 — CONSUMED / AUDIT PASSÉ ET CLOS (2026-11-15, clos le 2026-11-18)

**Historique — audit passé et clos selon le propriétaire (D-318).** Prochaine action d'alors : audit indépendant ChatGPT, sur HEAD privé exact, [RESULT](RESULT.md),
diff, CI exacte et publication [v0.9.5](https://github.com/Sd-tech-Sol/PokeMind/releases/tag/v0.9.5). Verdict local : PUBLISHED_AND_VERIFIED;
ce verdict constate les URLs/assets et ne remplace pas l'audit indépendant.
Deux suites entières vertes, 1885 réussis / 3 ignorés chacune. Public `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac`,
historique conservé, Setup non signé et SHA256 vérifiés après téléchargement.
NEXT_PROMPT **CONSUMED** : aucune exécution Codex/Claude, publication supplémentaire ou modification locale.

# HISTORIQUE — PokeMind V1 v0.9.5 publiée / audit GitHub indépendant passé (2026-11-15, D-315 de la branche de publication)

**Verdict ChatGPT :** [audit indépendant 019](VERIFICATION_PM-V1-PUBLIC-RELEASE-019_2026-11-15.md). Public `Sd-tech-Sol/PokeMind` : `main` et tag `v0.9.5` = `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac`; arbre public identique à l'arbre privé de préparation `f223aaa44f058afd32163a5d57d59b9a74ae70b4`; historique public `v0.9.3` conservé. Release préversion **réelle, non brouillon**, Setup Windows **non signé** avec digest SHA256 GitHub `e31bb4ce40886616cfc4f68a92a4da96fbda3e50a71fc75b2e2349c5b95390a7` et fichier .sha256 présent. **Deux portes locales entières vertes 1885/0/3 chacune rapportées par Codex, NON rejouées par ChatGPT**; 0 CI GitHub au SHA exact. Aucune vérification indépendante de l'ordinateur personnel.

**État : V1 fonctionnelle acceptée par le propriétaire, 0.9.5 publiée en préversion; mandat 019 CONSUMED; D-313/D-314 CONSUMÉS; audit et clôture D-315.** Aucun mandat Codex/Claude actif, aucun prompt à exécuter. `NEXT_PROMPT.md` reste CONSUMED. **Prochaine action : AUCUNE par défaut.** Réouvrir seulement sur problème réel/GO explicite; ne pas entreprendre V2, hotfix, nouvelle installation, donnée privée, release ou version 1.0 par inférence.
