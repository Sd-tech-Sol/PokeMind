# Audit indépendant ChatGPT — publication PokeMind v0.9.5 / lot 019

**Date : 2026-11-15 (Québec). Verdict : `VERIFIED_GITHUB_RELEASE_095_AND_SOURCE_SCOPE / CODEX_LOCAL_TESTS_REPORTED_ONLY`.** 019 est terminé, aucune tâche supplémentaire active. Cette vérification porte sur GitHub (références, contenu, metadata d'assets), **pas** sur l'exécution de Windows, le téléchargement indépendant des octets, le PC personnel ou une revue exhaustive de tous les fichiers binaires.

## Références GitHub directement vérifiées

- Dépôt public : [Sd-tech-Sol/PokeMind](https://github.com/Sd-tech-Sol/PokeMind), branche `main` = `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac`. Commit public unique intitulé `PokeMind 0.9.5`, **parent direct** `5629ae220ad996e290b971b31c323102ef258b27` (v0.9.3). L'historique de la branche publique a été préservé sans réécriture.
- Objet Git du commit public : arbre `e908741ce5024daa4af36c16332fa7498d4cf940`. Objet Git du commit privé de préparation `f223aaa44f058afd32163a5d57d59b9a74ae70b4` : **exactement le même arbre** `e908741ce5024daa4af36c16332fa7498d4cf940`. L'histoire privée n'est pas le parent du commit public; les métadonnées du commit public ont leur propre histoire.
- Tag `refs/tags/v0.9.5` -> exactement `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac`. Release [v0.9.5](https://github.com/Sd-tech-Sol/PokeMind/releases/tag/v0.9.5) : `prerelease=true`, `draft=false`, publiée `2026-11-15T06:18:25Z`; notes FR/EN présentes. Releases plus anciennes v0.9.0, v0.9.1, v0.9.2 et v0.9.3 toujours répertoriées.
- Asset GitHub `PokeMind-Setup-0.9.5.exe` : id `750047876`, état `uploaded`, **39 854 926 octets**, SHA256 annoncé par l'API GitHub `sha256:e31bb4ce40886616cfc4f68a92a4da96fbda3e50a71fc75b2e2349c5b95390a7`. Même empreinte que celle rapportée par Codex pour le Setup 017. Le programme est **non signé**.
- Asset `PokeMind-Setup-0.9.5.exe.sha256` : id `750047874`, état `uploaded`, **92 octets**, digest propre GitHub `sha256:6c7b216962e6787dce4fd462ab6bb8ebaa5a093a8e92a2e255d2ba715f985f79`. Codex rapporte téléchargement des **deux** assets et correspondance du checksum. Le contenu du fichier .sha256 et les octets EXE **n'ont pas été retéléchargés indépendamment par ChatGPT**; l'API GitHub établit leurs noms, tailles et empreintes déclarées.
- Dépôt privé `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows` : HEAD exact du rapport Codex `8084a91fdd2d9f84d7e0bd8dfc8a6ff5bcbd5c90`, `.orchestrator/RESULT.md` et `STATE/HANDOFF/NEXT_ACTION` contrôlés. `NEXT_PROMPT.md` 019 consommé.
- `compare 66a1ce0a2f974a480485110bbc10e8d7c086368b...f223aaa44f058afd32163a5d57d59b9a74ae70b4` dans privé : changements à `tests/test_version_metadata.py` **seulement** parmi `src/`, `scripts/`, `packaging/`, `tests/`; le reste = suivi et documentation publique de sortie. Donc le code applicatif installé/audité avant publication n'a pas été changé.
- Commit test `f223aaa44f058afd32163a5d57d59b9a74ae70b4` inspecté : un seul fichier `tests/test_version_metadata.py`, +8/-1. L'assertion de CHANGELOG accepte strictement l'entrée `unreleased (release candidate)` ou une vraie date ISO `YYYY-MM-DD (pre-release)`, refuse multiples titres et dates invalides, conserve 0.9.4 `never published` et ordre des versions. Fichier public test = même Git blob que le privé. CHANGELOG public contient `2026-11-15 (pre-release)`.
- Aucun statut CI, check-run ou workflow-run au SHA public `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac` ou au SHA privé du rapport `8084a91fdd2d9f84d7e0bd8dfc8a6ff5bcbd5c90` : **aucune CI GitHub verte vérifiée**.

## Preuves seulement rapportées par Codex local

- Porte privée complète : **1 885 réussis, 0 échec, 3 ignorés** (191 Qt / 1694 cœur); porte complète sur export public : **1 885 réussis, 0 échec, 3 ignorés**; toutes deux sont des exécutions Windows isolées rapportées, non rejouées par ChatGPT.
- Scan de 773 fichiers suivis, 34 binaires, ressources et métadonnées, absence d'indices sensibles selon Codex; revue indépendante exhaustive des données éventuellement publiées **non réalisée**.
- Installateur 017 et dist revalidés selon Codex, aucun nouveau build/Setup. Codex rapporte que les deux assets téléchargés ont des SHA concordants.
- Aucune donnée personnelle, base, deck, journal, sauvegarde, application Windows installée ou archive touchée **selon Codex**; ChatGPT n'a pas accès au disque local pour attester ces faits. Réception de la GUI 017 = déclaration du propriétaire, sans nouveau test de l'application installée pendant 019.

## Conclusion et clôture

Publication v0.9.5 **confirmée indépendamment sur GitHub** et structure source/historique du dépôt conforme au mandat D-313/D-314. La V1 fonctionnelle était acceptée par son propriétaire; **0.9.5 reste une préversion et n'est pas 1.0 stable**. 019 et permissions de publication consommés. **Aucune nouvelle tâche de développement, hotfix, installation personnelle, sauvegarde, restauration, ou publication autorisée** par cette clôture. En cas de nouveau défaut observé, produire une nouvelle décision/autorisation spécifique. Sinon STOP, pas de prompt Codex.
