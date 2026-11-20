# PM-RELEASE-096-PUBLIC-025 — STOP PUBLICATION 0.9.6 À L'ÉTAPE 4 / RIEN DE PUBLIC (D-320)

2026-11-20, Québec. Réception du propriétaire **OWNER_GUI_ACCEPTED_096** (déclaration directe), puis GO explicite
de publier 0.9.6 en préversion (D-320). Exécutant : Claude Code, sur le PC Windows du propriétaire; **aucun audit
indépendant**. Rapport 024 archivé : `archive/2026-11/RESULT_avant_025_f6f9809_2026-11-19.md`.

**Verdict : STOP à l'étape 4 (export public), porte de confidentialité ROUGE.** Aucun push public, aucun tag, aucune
release, aucun asset. Le dépôt public est inchangé : `main` = `295db53d24e67fa656c3cb4b2f2fb1f12d6ef5ac`, pas de
`v0.9.6`.

## Bilan par étape

| Étape | Résultat |
|---|---|
| 1 — prévol | **vert** : arbre propre, `git pull --ff-only` à jour, HEAD `f6f9809`; `src/`, `scripts/`, `packaging/` identiques à `8d2bd62`; public `main` = `295db53`, aucun tag/release/asset v0.9.6 |
| 2 — notes de version | **vert** : commit privé `81580b0` (4 fichiers, documentation seulement); porte locale complète **VERTE : 1946 réussis / 0 échec / 3 ignorés** (Qt 207, cœur 1739) |
| 3 — binaire | **vert** : Setup D-319 réutilisé, 39 961 292 octets, SHA256 `688d865144b2bff064778fbfe90ffbd599ce0ccc3c8bf9843d4b961f54bad137` = son `.sha256`, version 0.9.6; scan `--require-archive` CLEAN (797 fichiers, 331 modules); aucune reconstruction |
| 4 — export public | **ROUGE** : voir ci-dessous. Arrêt avant tout push |
| 5 — release | non exécutée |

## Étape 2 — contenu du commit privé `81580b0`

- `CHANGELOG.md` : `## [0.9.6] — 2026-11-20 (pre-release)`, même format que 0.9.5.
- `docs/RELEASE_NOTES_0.9.6.md` : bloc « Not published yet / Pas encore publiée » remplacé par « Unsigned installer /
  Installateur non signé » et le SHA256 du Setup.
- `README.md` et `README.fr.md`, ligne « Status » : « the latest public one is 0.9.5 » remplacé par « public
  pre-release », comme à la publication 0.9.5 (checklist A5). **Écart par rapport à la liste du mandat**, signalé au
  propriétaire.
- Aucun test ne verrouillait l'ancien libellé « pas encore publiée » : aucun test modifié.
- Ce commit **prépare** la publication; 0.9.6 n'est **pas** publiée.

## Étape 4 — pourquoi la porte est rouge

- `scripts/export_public.py` : EXPORTED, 974 fichiers, arbre `aa1a8bfcd53b00167190900b9829460ea1a95b29` = HEAD
  `81580b0`, un commit local, jamais poussé (dossier temporaire de session, hors dépôt).
- Scan texte de tout l'export (octets ASCII et UTF-16LE, blocs texte des PNG) : nom de compte, profil, chemin du
  dépôt, courriel personnel, jetons, clés, bases SQLite, nom de deck retiré en D-319, dossier de protection 096.
  **Rien de personnel** : les seuls chemins `C:\Users\…` sont des noms inventés dans les tests.
- Revue visuelle des images ajoutées depuis le public (176 nouvelles, 87 vues en planches, une par page et par
  dossier). Toutes montrent des données inventées (« Famille inventée », « Synthétique N », « Deck inventé du
  joueur »), **sauf la page Réglages › Données de `style-global/`** :
  - `docs/design/pokemind-brainball/captures/style-global/06-reglages-4-data-clair.jpg` et
    `06-reglages-4-data-sombre.jpg` affichent en clair, dans le champ « Dossier de données », un chemin absolu du
    dossier temporaire de la porte, **qui contient le nom du compte Windows** du PC. **Confirmé à l'agrandissement.**
  - Les variantes `-1100x700` de la même page montrent le même champ, coupé; non confirmé à l'image.
  - Le scan texte ne pouvait pas le voir : le texte est dessiné dans l'image.
- Le mandat interdit tout nom d'utilisateur et tout chemin absolu dans l'export : **STOP**, sans export, sans push,
  sans correction improvisée. La porte locale de l'export, lancée en parallèle, a été arrêtée sans résultat.

## Ce qui n'a pas été fait ni touché

Données personnelles non lues; aucune sauvegarde, installation, désinstallation ou restauration; dossier de
protection 096 et 0.9.6 installée non touchés; aucune reconstruction du Setup. Rien de privé dans Git.

## Prochaine action

**Décision du propriétaire.** Piste proposée (nouvel ordre requis) : refaire ou retirer les captures
`style-global/06-reglages-4-data-*` avec un dossier de données inventé (sans chemin du profil), vérifier que la page
Données n'apparaît nulle part ailleurs avec un vrai chemin, porte verte, puis nouveau GO de publication (le Setup
`688d8651…d137` reste valable : les captures ne sont pas dans le binaire). Option : faire lire le texte des images
par le scan avant chaque export.
