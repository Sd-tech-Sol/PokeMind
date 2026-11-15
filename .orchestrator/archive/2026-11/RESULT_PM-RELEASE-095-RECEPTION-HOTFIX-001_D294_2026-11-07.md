# RESULT — PM-RELEASE-095-RECEPTION-HOTFIX-001 : images du Deck Lab et « Ce que le coach reçoit » (D-294), 2026-11-07

Exécuteur : Claude Code (Opus 5.5). Demande directe du propriétaire après son contrôle visuel de la 0.9.5 installée
(premier bloc de NEXT_ACTION `b669def` : réception visuelle; réception **non acceptée**, deux défauts). Une seule tâche
de correctif, sans nouvelle fonction. Statut : **IMPLEMENTED / REPORTED; AWAITING_CHATGPT_AUDIT**. Pas VERIFIED, pas
`RELEASE_READY`. Rapport précédent : [archive/2026-11/RESULT_PM-RELEASE-095-OWNER-INSTALL-001_D293_2026-11-07.md](archive/2026-11/RESULT_PM-RELEASE-095-OWNER-INSTALL-001_D293_2026-11-07.md).
**STOP pour audit ChatGPT.**

## 0. Prévol
`git fetch` + `git pull --ff-only` : `b319ef7` → `b669def` (2 commits docs ChatGPT), arbre propre, aucun reset/rebase/force.
Lus : NEXT_ACTION, RESULT, STATE, audit `VERIFICATION_PM-RELEASE-095-OWNER-INSTALL-001`. Données réelles : seuls des
fichiers **publics** (catalogue TCGdex, cache d'images, manifestes d'images) et deux champs techniques de préférences
(`card_images`, nombre de clés) ont été lus; aucun deck, journal, conversation ni valeur de confidentialité.

## 1. Images « Image indisponible » — cause exacte
- **Chaîne** : Deck Lab → `Services.gallery_cards()` résout chaque ligne (code d'extension + numéro + nom) en impression
  TCGdex via le pont `set_code_aliases.build_aliases(as_of=date.today())` → `identity` → `ImageCache.fetch()` (cache
  `data/local/card-images`, puis TCGdex) → `CardTile.set_image()`. Sans `identity`, aucune image n'est demandée et la
  tuile garde son texte de repli « Image indisponible ».
- **Écartés par mesure** : préférence `card_images` = vraie avant et après l'installation (21 clés des deux côtés);
  cache d'images intact (262 fichiers, identique à la sauvegarde); les 131 impressions en cache existent dans l'ancien
  **et** le nouveau catalogue; schéma inchangé.
- **Déclencheur** : au premier lancement de la 0.9.5 (21:54, heure du Québec), la mise à jour automatique du catalogue a
  remplacé le catalogue public (TCGdex `cbddf7e` → `f1c916b`, 23 864 → 24 005 impressions). Ses dates de récupération
  sont écrites en **UTC** : `2026-11-08T02:54Z`.
- **Défaut** : `build_aliases` rejette toute preuve « venant du futur » avec `stamp[:10] > as_of`, et compare donc la
  date UTC `2026-11-08` à la date **locale** `2026-11-07`. Toutes les extensions sont refusées : sur une copie du vrai
  catalogue, `as_of=2026-11-07` donne **0** code d'extension, `as_of=2026-11-08` en donne **183**. Aucune carte n'a donc
  d'identité jusqu'à minuit, heure locale. Une mise à jour faite après 19 h (heure de l'Est) produit le même effet chaque fois.
  Ce n'est ni une panne réseau, ni un défaut du cache, ni un chemin, ni le chargement asynchrone.
- **Correctif minimal** : `database.local_day(stamp)` ramène un horodatage UTC au jour calendaire du PC (une date nue
  reste telle quelle). Il est appliqué aux quatre comparaisons de la date de récupération du catalogue :
  `set_code_aliases` (la cause des images), `deck_knowledge` et `deck_library` (textes de cartes servant au coach),
  `local_ocr`. Les vraies dates futures restent refusées (test existant `future_source` / `future` inchangé).
- **Hors périmètre, signalé et non corrigé** : même famille de comparaison UTC/locale sur des dates écrites par
  l'application (`imported_at` de `matchup_analytics` et `selected_match_review`, `recorded_at` d'`opponent_observer`,
  `revoked_at` de `lessons`). Effet possible : un journal importé en soirée serait ignoré par ces vues jusqu'à minuit.
  Non observé par le propriétaire; à décider par l'audit.

## 2. « Ce que le coach reçoit » — défauts et correctif
Rendus hors écran avec racine inventée, polices Windows, styles **windows11** (celui de Qt 6.12 sur Windows 11, aucun
style imposé par l'app) et Fusion, thèmes sombre et clair, FR et EN, largeurs 1500 et 1100 px.
- **Avant** : choix fermé tronqué (« + mes statistiques a… », « + my anonymous s… », largeur 179 px, le `sizeHint` ne
  compte pas le remplissage et la flèche de la feuille de style); liste ouverte élidée (« + mes stati…es anonymes »);
  en **thème clair**, le style natif windows11 dessinait le choix surligné **en blanc sur bleu pâle** (il ignore
  `selection-color`); à 1100 px, l'explication devenait une colonne de 20 lignes de 12 px.
- **Correctif** (`theme.py`, `window.py`) : éléments de liste dessinés par le thème dans chaque état (normal
  `text/surface`, survol `text/hover`, sélection `selection_text/selection`; contrastes 14,1 / 9,3 / 6,8 en sombre et
  17,1 / 13,8 / 12,8 en clair, tous ≥ 4,5:1); `fit_combo()` dimensionne les menus des Réglages et leur liste d'après le
  choix le plus long, de nouveau après un changement de langue; une explication longue (> 120 caractères) garde toute
  la largeur et le menu passe dessous; texte des explications 12 → 13 px (couleurs inchangées, déjà ≥ 7,3:1). Libellés
  et texte de consentement **inchangés** (D-290).
- **Après** : choix complet (245 px FR, 231 px EN), liste complète et lisible dans les deux thèmes (clair : texte foncé
  sur bleu pâle), état désactivé lisible (pendant une réponse du coach), explication sur 3 lignes à 1500 px et 6 à 1100 px.

## 3. Tests et portes
- Test écrit **d'abord** : `test_alias_kept_after_an_evening_catalog_update` (23:30 locale → UTC du lendemain à l'ouest
  de Greenwich) **échoue** sur le code d'origine (porte filtrée ROUGE, 1 échec), passe après. Plus
  `test_local_day_of_utc_catalog_stamps`, `test_drop_down_choices_are_drawn_by_the_theme_in_every_state` (×2 thèmes),
  `test_qt_coach_sharing_choice_reads_in_full_in_both_languages`.

| Porte (`python scripts/local_gate.py`, copie hors dépôt) | Arbre | Résultat |
|---|---|---|
| Complète | arbre corrigé avant commit (sans la note CHANGELOG) | **VERTE**, code 0 : Qt **122** passés; cœur **1639** passés / 0 échec / 3 ignorés |
| Complète | commit de code `00eecb3` | **VERTE**, code 0 : Qt **122** passés; cœur **1639** passés / 0 échec / 3 ignorés |

## 4. Validation Windows
- **Chemin réel de la galerie** (`gallery_cards` → `populate` → `images.fetch` → `set_image`) sous Windows, style
  windows11, polices réelles, dans une racine inventée contenant **les copies du vrai catalogue mis à jour et du vrai
  cache d'images** (données publiques) et une liste inventée de 60 cartes tirée des impressions en cache; réseau refusé
  (`POKEMIND_TEST_OFFLINE=1`), date locale 2026-11-07 (fenêtre du défaut) :
  - code d'origine (`b669def`) : 0 / 13 lignes identifiées, **13 « Image indisponible »** (reproduit le constat);
  - code corrigé : 12 / 13 identifiées, **12 illustrations affichées depuis le cache local**; 1 repli légitime (énergie de
    base inventée `SVE 2`, déjà non résolue avec l'ancien catalogue : vraie absence).
- **Candidat isolé construit depuis `00eecb3`** (arbre propre), local, non signé, **non installé, non publié** :
  - EXE `build/exe-upgrade-fab6f85c40634a7ea5c37c0964032db5/dist/PokeMind/PokeMind.exe` (797 fichiers),
    SHA-256 `45D4EBA935DCA32C1898D18FD942668F4F52DA5A9B77A07A6E1F6234815B8145`, `FileVersion = ProductVersion = 0.9.5`;
  - Setup `dist/installer-candidate-0.9.5-00eecb3/PokeMind-Setup-0.9.5.exe` (+ `.sha256`),
    SHA-256 `91993E84F0E17050898E11E1345F54E99D8A99420DE04BA321942992133BC212`, version 0.9.5, `NotSigned`;
  - archive PYZ : `local_day` présent dans `database`, `set_code_aliases`, `deck_knowledge`, `deck_library`; `fit_combo`
    dans `desktop.window`; règles `::item` et 13 px dans `desktop.theme`; `__version__` 0.9.5; `deck_public_stats` présent
    (`local_ocr` n'est pas embarqué dans l'app de bureau);
  - `scan_binary_personal_paths.py --require-archive` : `CLEAN` (797 fichiers, 321 modules, 0 constat); aucun
    `.json/.sqlite/.db/.log/.env` dans la distribution;
  - fumée gelée isolée (root inventé vide, `LOCALAPPDATA`/`APPDATA`/`TEMP` redirigés, proxys fermés, `PATH` réduit) :
    gelé, visible, plateforme `windows`, **7 pages**, aucun processus enfant; code 2 attendu (root vide).
- **Non fait** : l'installation chez le propriétaire (le correctif n'est donc pas encore sur sa machine); la galerie du
  Deck Lab n'a pas été pilotée dans l'EXE gelé par UI Automation (le chemin est validé au niveau source sous Windows et
  le code est identique dans l'archive). Installation réelle et nommage de version : décisions distinctes (§6).

## 5. Préservation
Installation réelle inchangée (registre 0.9.5, `PokeMind.exe` `7121BBEB…E6FF`); sauvegarde d'avant installation
intacte et conservée; candidat 0.9.5 initial `24e9cc5` (`6E7E5CB2…68CB`) inchangé; données réelles non modifiées
(lectures seules de copies publiques). Aucune donnée personnelle dans Git.

## 6. Décisions à prendre (audit / propriétaire)
1. **Installer le candidat `00eecb3` chez le propriétaire** : GO distinct (même méthode que D-293 : vérifier le SHA-256,
   assistant normal, décocher « Lancer PokeMind » si un contrôle doit précéder). La sauvegarde existante reste la référence.
2. **Version** : le candidat garde le numéro 0.9.5 (non publiée), identifié par son commit; un passage à 0.9.6 est possible.
3. Les comparaisons UTC/locale signalées au §1 (hors périmètre).

## 7. Git / publication
Commits privés : code `00eecb3`; rapport (ce fichier, HANDOFF, NEXT_ACTION, STATE, DECISIONS D-294, archive). Aucun
push public, tag ni release. `V1 NOT_RELEASE_READY`.
