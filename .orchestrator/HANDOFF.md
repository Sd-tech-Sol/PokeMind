# Passation ACTIVE — 019 correction du contrôle documentaire puis publication conditionnelle (2026-11-15)

**Audit GitHub indépendant 018 terminé :** `.orchestrator/VERIFICATION_PM-V1-PUBLIC-RELEASE-018_STOP_2026-11-15.md`. HEAD du rapport 018 `529f7647cb4c99bb6bd2426b30e3d6dd7565f2b2`; source produit `66a1ce0a2f974a480485110bbc10e8d7c086368b`, aucune modification produit. Porte 018 **ROUGE** 1884 réussis / 1 échec / 3 ignorés rapportés par Codex; un seul test de version exige `unreleased` tandis que `CHANGELOG.md` annonce la préversion datée, commit docs `2eff8ca`. 018 STOP justifié, prompt archivé et consommé. Dépôt public encore `v0.9.3`, aucun push/tag/upload public.

**Une seule prochaine action = mandat 019 READY_FOR_CODEX High**, D-314 arbitrage de l'échec; même GO propriétaire de publication v0.9.5 D-313, **pas** de nouveau GO 017 installation, ni de 1.0.0. Exécuter le prompt actif `.orchestrator/NEXT_PROMPT.md` intégralement après fast-forward privé, puis corriger uniquement `tests/test_version_metadata.py`, préserver toutes les garanties, obtenir **porte complète verte**. Ensuite seulement scanner/exporter dans un dépôt sans historique privé, conserver historique `main` public par commit fast-forward, publier release `v0.9.5` prerelease + Setup/checksum SHA contrôlé. Aucune installation, aucune donnée personnelle, aucun backup. Si échec, STOP et rapport; si succès, vérifier URL/asset/sha puis STOP audit ChatGPT.

---

# Passation — 018 STOP / AWAITING_AUDIT / NON PUBLIÉ (2026-11-15)

D-313 autorisait une publication conditionnelle 0.9.5 après réception propriétaire 017.
Fast-forward privé vers `79006578d9db62b0454fe62fa8273820b234c423`; produit exact 66a1ce0, inchangé.
Préparation de quatre documents au commit **`2eff8ca23314b9ffdd1239a81e9d189a04b1ffb6`**; aucun code/version modifié.

**Porte isolée complète ROUGE**, une exécution : Qt **191 passed** (149 s), cœur
**1693 passed / 1 failed / 3 skipped** (653 s), total **1884/1/3**, exit 1.
`test_the_unpublished_094_candidate_is_folded_into_095_and_never_presented_as_released`
exige `## [0.9.5] — unreleased (release candidate)`. Codex a daté le titre lors de la préparation.
Échec documentaire introduit dans 018; aucun correctif/retest/poursuite après le STOP.
Le CHANGELOG daté reste une préparation privée non publiée à auditer, pas une release réelle.

Artefact 017 revérifié : Setup SHA e31bb4ce40886616cfc4f68a92a4da96fbda3e50a71fc75b2e2349c5b95390a7,
EXE c180d58daca4d9142506c3dfdfe036c56a7261b1635fb361eb7a1607d28f21a8,
797 fichiers et 328 modules PYZ, scans CLEAN, versions/icônes/licences conformes; non signé.
Scan préalable 770 fichiers/34 binaires et revue des nouvelles images sans constat sensible.
**Aucun export exécuté**, donc aucune porte export ni commit/push/tag/release/upload public.
Public `main` **5629ae220ad996e290b971b31c323102ef258b27**, dernière release **v0.9.3**,
recontrôlés inchangés après échec. Installation 017 et données personnelles non consultées/non touchées.

[RESULT](RESULT.md) fait foi; RESULT 017 et prompt original 018 archivés, prompt actif CONSUMED.
**Prochaine action unique : audit ChatGPT et arbitrage du test/métadonnées**, contrôle HEAD et CI exacts
du rapport privé. Aucun statut CI vert revendiqué. Aucun mandat 019 ou reprise/publication automatique.
