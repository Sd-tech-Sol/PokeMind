# PM-V1-PUBLIC-RELEASE-018 — STOP / AWAITING_AUDIT / NOT PUBLISHED

2026-11-15 (Québec). D-313, déclenchement manuel; fast-forward privé `bea56af` →
`79006578d9db62b0454fe62fa8273820b234c423`, arbre initial propre. Source applicative exacte
`66a1ce0a2f974a480485110bbc10e8d7c086368b`, inchangée dans src/tests/scripts/packaging/dépendances/version.
Réception 017 **OWNER_GUI_ACCEPTED_017**, déclaration du propriétaire, non rejouée.

## Résultat bloquant réel

**Porte privée complète ROUGE**, une seule exécution de `python scripts/local_gate.py --keep`,
copie isolée sans données personnelles. Compilation/hygiène OK; **191 Qt passés** (149 s),
**1693 cœur passés / 1 échec / 3 ignorés** (653 s), total **1884 passés / 1 échec / 3 ignorés**, exit 1.

Échec : `tests/test_version_metadata.py::test_the_unpublished_094_candidate_is_folded_into_095_and_never_presented_as_released`.
Ce test impose littéralement `## [0.9.5] — unreleased (release candidate)` dans CHANGELOG.
La préparation documentaire autorisée l'a remplacé par une date de préversion :
2026-11-14 dans la copie testée, devenue 2026-11-15 dans le commit documentaire final.
Les deux formes datées échouent à cette même exigence. **Échec introduit par la préparation
documentaire de Codex**, pas un défaut découvert dans le binaire 017 ni un changement de version.
Test et titre conservés pour audit; **aucune réparation, relance de test ni poursuite de publication**.

Commit documentaire privé préparatoire **`2eff8ca23314b9ffdd1239a81e9d189a04b1ffb6`**, quatre fichiers seulement :
README FR/EN, CHANGELOG, notes FR/EN 0.9.5. Rang/taux avant nom, onglet Classement,
statistiques repliables, chat arrondi et reconstruction adverse conditionnelle documentés;
ancienne affirmation « aucun import ne peut ajouter de référence adverse » rectifiée.
La date du CHANGELOG est une **préparation privée non publiée**, pas une preuve de release.

## Contrôles réalisés avant le STOP

- Dépôts/branche/authentification/droits de push conformes. Auteur public et adresse noreply
  vérifiés sur le commit public existant, aucune identité inventée.
- Public `main` vérifié à **`5629ae220ad996e290b971b31c323102ef258b27`**, v0.9.0–v0.9.3 présents,
  dernière préversion **v0.9.3**; v0.9.5 absente au prévol. `main` et releases reconsultés après échec,
  inchangés. Aucune mutation publique effectuée.
- Artefact immuable 017 réutilisable, **aucun nouveau build ni Setup exécuté** :
  `dist/installer-candidate-0.9.5-66a1ce0-fa8e4877/PokeMind-Setup-0.9.5.exe`, **39854926 octets**,
  SHA256 **`e31bb4ce40886616cfc4f68a92a4da96fbda3e50a71fc75b2e2349c5b95390a7`**.
  EXE staging **`c180d58daca4d9142506c3dfdfe036c56a7261b1635fb361eb7a1607d28f21a8`**.
  Distribution **797 fichiers / 128830300 octets**, manifeste égal à 017, **328 modules PYZ**;
  scans distribution/Setup **CLEAN**, modules contrôlés égaux aux sources, PE x64/0.9.5,
  icônes 9/9, branding/9 licences conformes, AppId source inchangé. **Non signé**.
  Copie d'upload et checksum générés localement, concordants; **aucun upload**.
- Scan préalable des **770 fichiers suivis**, dont **34 binaires**, sans constat de secret,
  adresse privée ou identifiant machine interdit; `.orchestrator/`, AGENTS et archives inclus.
  24 nouveaux PNG inspectés visuellement, marque/maquette/fixtures; 30 PNG sans champ texte
  de métadonnées, 4 PDF inchangés par rapport au public. Contextes SHA examinés : binaires/ressources,
  aucun manifeste personnel publié. Ce contrôle préalable **n'est pas un export réussi**.
- Inventaire comparatif préalable : 127 nouveaux chemins, 55 modifiés, zéro suppression
  par rapport au `main` public, avant les quatre corrections documentaires.

## Opérations NON effectuées et état final

**Export public : NON EXÉCUTÉ. Porte dans l'export : NON EXÉCUTÉE.**
**Commit/push public : 0. Tag/release v0.9.5 : 0. Assets publiés : 0.**
Aucune URL de release 0.9.5 n'est revendiquée. La préversion publique vérifiée reste
[v0.9.3](https://github.com/Sd-tech-Sol/PokeMind/releases/tag/v0.9.3).

**Aucun accès au stockage personnel, aux decks/journaux/archives, à l'ancien programme installé
ou à un compte Coach.** Aucune sauvegarde, installation, restauration, migration ou suppression.
Les 480 fichiers personnels et l'installation 017 ne sont ni inventoriés ni revalidés par 018.
Les fumées et QA native 017 restent historiques; pas présentées comme rejouées dans 018.

RESULT 017 et mandat 018 original archivés; prompt actif **CONSUMED / STOP**,
états **AWAITING_AUDIT / STOP_PRIVATE_GATE_FAILED**. Un commit documentaire préparatoire,
puis **un seul commit de rapport assaini privé**. Contrôle HEAD/statuts/checks/runs exacts après push;
aucune CI verte revendiquée. **STOP pour audit ChatGPT** et arbitrage de la contradiction
entre métadonnées de publication et test « unreleased ». Aucun 019 ni reprise automatique.
