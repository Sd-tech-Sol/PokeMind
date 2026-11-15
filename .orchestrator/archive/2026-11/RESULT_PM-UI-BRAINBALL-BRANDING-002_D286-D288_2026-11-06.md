# RESULT — PM-UI-BRAINBALL-BRANDING-002 : la carte PokeMind / TCG Coach remplace le logo dessiné (D-286), 2026-11-06

Exécuteur : Claude Code (Opus 5.5). Mandat : premier bloc de `NEXT_ACTION.md` → `NEXT_PROMPT.md` (autorisation du
propriétaire du 2026-11-06). Statut : **IMPLEMENTED / REPORTED** (pas VERIFIED). **STOP pour audit ChatGPT.**
Rapport précédent (D-285, 0.9.3 publiée) : [archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D285_2026-11-05.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D285_2026-11-05.md).

## Commits (branche privée `work/pm-v1-lotj-final-readiness-windows`)
- Code et preuves visuelles : **`8570613`** (`8570613d78f210016a900d32d147b08738897b3c`).
- Rapport : commit suivant (ce fichier, HANDOFF, NEXT_ACTION, STATE, DECISIONS D-286, archive D-285).
- Dépôt public `Sd-tech-Sol/PokeMind` : **inchangé**. Aucun tag, aucune 0.9.4, aucune publication.

## Source graphique
- `assets/branding/pokemind-tcg-coach-original.png` : SHA-256 recalculé
  `30824d84f594be0e1fe33b3e9531f487e497252e17d7a16ff57763b787d7f0f5` = valeur du mandat; 1060×1484; **non modifié**.
- Constat : les 4 coins hors de la carte arrondie sont du **blanc opaque** (jusqu'à 66 px le long d'un bord). Affichés
  tels quels, ils feraient des coins blancs sur le thème foncé.
- Dérivé embarqué, reproductible : `python scripts/make_icon.py --card` vérifie le SHA-256, rend transparent
  **uniquement** ce blanc de page (remplissage depuis chaque coin, limité à un carré de 96 px, seuil « tous canaux
  ≥ 150 », la bordure marine de la carte l'arrête), puis réduit exactement de moitié (530×742, mêmes proportions,
  lissage Qt prémultiplié) → `src/pokemind/desktop/branding/pokemind-card.png` (SHA-256 `293d7c0c…b256`).
- Aucune recoupe, aucun dessin, aucune IA : même à 16 px, c'est la carte entière (silhouette).

## Zones de marque remplacées (état réel trouvé avant modification)
| Zone | Avant | Après |
|---|---|---|
| Icône de fenêtre / barre des tâches (`app.py`, `window.make_icon`) | `logo_icon()` dessiné | `logo_icon()` = carte, 9 tailles 16–256 |
| Menu : à côté de « PokeMind », icône de « Vue d'ensemble » (`window.py`, `navigation_icon(0)`) | logo dessiné | carte (`logo_pixmap`) |
| Bandeau « À toi de jouer » (`motion.EmblemWidget`) | logo 96 px dans 106×106 | carte entière 104 px dans 110×124 (rotation/rebond sans coupe), nette en haute densité |
| Assistant de bienvenue (`welcome.py`) | logo 120 px | carte entière 150 px |
| Réglages › À propos (`window.py`) | logo 72 px | carte entière 96 px |
| Couverture du classeur (`binder.BinderCover`) | logo + texte « PokeMind » peint | carte entière centrée (le texte peint, redondant, est retiré) |
| Ressource d'icône de `PokeMind.exe` (`Build-PokeMindDesktop.ps1 --icon`) | `.ico` du logo dessiné | `.ico` de la carte; carte embarquée par `--add-data` |
| Installateur (`PokeMind.iss`, `Build-PokeMindInstaller.ps1`) | icône + petite image du logo; grande image Inno par défaut | icône `Setup` = même `.ico`; petite (58 px) et **grande** (164×314) images de la carte, 6 échelles (100–250 %) à la taille exacte de leur zone |
| Raccourcis Bureau / menu Démarrer / Désinstaller | icône de `PokeMind.exe` | idem (ressource de l'EXE remplacée) |
| README public (`docs/assets/pokemind-logo.png`) | logo dessiné | carte entière 240×336 |

Non touchés : cartes Pokémon / illustrations TCGdex, images de decks, légende des cartes sans illustration, couleurs
BrainBall (`palette.json`, `theme.PALETTES`), logique, imports, mémoire, IA, paramètres, bases. L'ancien dessin
(`theme.brain_path`, deux cartes et cerveau) est supprimé du code.

## Fichiers touchés (`8570613`)
`src/pokemind/desktop/{theme,motion,welcome,window,binder}.py`, `src/pokemind/desktop/branding/pokemind-card.png` (nouveau),
`scripts/make_icon.py`, `scripts/Build-PokeMindDesktop.ps1`, `scripts/Build-PokeMindInstaller.ps1`,
`scripts/pokemind_build_backend.py` (la roue inclut `branding/*.png`), `packaging/PokeMind.iss`,
`tests/test_desktop_workflow_qt.py`, `docs/assets/pokemind-logo.png`, `docs/design/pokemind-brainball/README.md`
(section « Dérivés générés »), `docs/design/pokemind-brainball/captures/` (README + 8 captures `branding-*.png`).

## Tests
- Remplacé `test_logo_is_two_cards_with_a_brain…` par `test_logo_is_the_approved_pokemind_card_and_the_exe_icon_holds_every_size` :
  SHA-256 de l'original; ancien dessin absent; dérivé embarqué = régénération depuis l'original (écart ≤ 2 par canal),
  pixels proches de l'original à 2×; coins transparents, bords opaques; logo carré jamais étiré (côtés transparents),
  bouton de la Poké Ball et cerveau rouge aux bons endroits; carte 150 px = 107×150; haute densité ×2; `.ico` 9 entrées
  PNG; image d'installateur 164×314 sur le fond du thème foncé.
- Nouveau `test_brand_card_reaches_every_brand_spot_and_the_windows_build` : bandeau 110×124 qui montre la carte,
  icône de fenêtre et du menu, couverture du classeur, crochets `--add-data`/`--icon`, `SetupIconFile`, `WizardImageFile`.
- **Porte locale complète VERTE** (`python scripts/local_gate.py`, copie sans `data/local`, hors ligne, offscreen),
  sur l'arbre de code de `8570613` : compilation OK, hygiène OK, **Qt 115 réussis**, **cœur 1610 réussis, 0 échec,
  3 ignorés**. (Qt : 114 + 1 nouveau.) Aucune CI GitHub (retirée D-271); ce n'est pas une CI.

## Captures (synthétiques, dans le dépôt : `docs/design/pokemind-brainball/captures/`)
Fixture inventée des tests Qt (« Invented Family »), polices de Windows, foncé à gauche, clair à droite :
`branding-overview.png` (bandeau, menu, navigation, 1280×860), `branding-narrow-collapsed.png` (1100×700, menu
replié), `branding-about.png`, `branding-welcome.png`, `branding-binder-cover.png`, `branding-icons.png` (carte 190/104,
icônes 128→16, agrandissement ×4 de 16/24/32), `branding-installer-wizard.png`, `branding-windows-shell-icons.png`.
Vérifiées à l'œil : carte entière, non coupée, non déformée, coins propres sur les deux thèmes; à 16–32 px la
silhouette (carte bleue bordée d'or, Poké Ball-cerveau rouge et blanche) reste reconnaissable, le texte non (attendu).

## EXE et installateur locaux (hors Git)
- EXE construit par `Build-PokeMindDesktop.ps1 -StagingRoot` dans un staging neuf, depuis l'arbre de `8570613`
  (797 fichiers; carte embarquée `_internal/pokemind/desktop/branding/pokemind-card.png`, même SHA-256 que le dépôt).
- **Ressource PE inspectée** (`pefile`) : `PokeMind.exe` a 1 groupe d'icônes, 9 images 16–256 px (PNG), **9/9
  identiques octet pour octet** aux entrées du `.ico` généré; l'entrée 256 px extraite est la carte.
- **Installateur** `dist/installer-branding-candidate/PokeMind-Setup-0.9.3.exe` (37,8 Mo, **non signé**, SHA-256
  `DED987C87D0029270EADBB6B8B0023CC5E693E684B5B589504BAEFD0EDE528C5`) : groupe `MAINICON`, 9/9 entrées identiques au
  `.ico`. Le nom garde 0.9.3 car la version n'a pas changé (pas de 0.9.4 sans GO); placé dans un **dossier candidat
  séparé** : l'installateur 0.9.3 publié dans `dist/installer/` n'est pas touché. Recherche de chemins de la machine
  de construction (`scan_binary_personal_paths.py --require-archive`) passée.
- **Shell Windows** : copies de l'EXE et du Setup dans un chemin neuf (pour écarter le cache d'icônes de l'Explorateur,
  sans vider de cache ni toucher à explorer.exe), `ExtractAssociatedIcon` → la carte pour les deux.
- **Fumée** de l'EXE gelé (plateforme `windows`, mode autonome, `POKEMIND_DATA_ROOT` synthétique vide dans un dossier
  temporaire, `POKEMIND_DESKTOP_SMOKE=1`, proxy HTTP(S) vers un port fermé) : fenêtre visible, 7 pages, terminal
  disponible, carte affichée dans le bandeau, le menu et la navigation (capture vérifiée). **Code de sortie 2** :
  le critère « prêt » du mode fumée exige rapport, decks et galerie, absents d'un dossier vide (attendu, pas un plantage).
  Aucun lancement en mode projet (il ouvrirait les données du propriétaire).
- Déploiement : `dist/PokeMind/` remplacé par ce candidat (797 fichiers, `PokeMind.exe` SHA-256 `06D3A3B5…D641B`);
  **copie de retour arrière** `dist/PokeMind-before-branding-e2ae20299cc54b76a1f07b9170f3cb87/`. PokeMind était fermé.
  (Installé ensuite chez le propriétaire, sur son ordre : voir plus bas.)

## Installation chez le propriétaire (ajout du 2026-11-06, sur son ordre)
Le propriétaire voyait encore l'ancienne icône : ses raccourcis Bureau et menu Démarrer ouvrent la copie **installée**
(`%LOCALAPPDATA%\Programs\PokeMind`, 0.9.3 publiée), pas `dist/PokeMind`. Sur son ordre explicite (« touche à mon
installation, je m'en fous, c'est des tests »), le candidat a été installé par-dessus en silencieux (sortie 0, PokeMind
fermé). `PokeMind.exe` installé = candidat (SHA-256 `06D3A3B5…D641B`), carte embarquée, icône PE 9/9 identique au `.ico`,
icône extraite par le Shell = la carte. Cache d'icônes rafraîchi (`ie4uinit -show`, notification du Shell); explorer.exe
non redémarré. Données `%LOCALAPPDATA%\PokeMind` non lues ni touchées (l'installateur ne les modifie pas).
Retour arrière : réinstaller `dist/installer/PokeMind-Setup-0.9.3.exe` (publié).

## Ajout D-287 (même session, ordre du propriétaire) : coach cloud autorisé par défaut
Le journal collé était reconnu (doublon conservé) mais le coach ne cherchait pas le deck adverse : consentement cloud et
« + mes statistiques anonymes » désactivés. Sur ordre (« J'autorise tout par défaut »), code **`358a551`** : défauts
`cloud_consent=True`, `sharing='aggregates'`; message d'aide corrigé; tests de confidentialité partant explicitement du
refus; nouveau test des défauts. **Porte locale complète VERTE** : Qt 116, cœur 1610 réussis, 0 échec, 3 ignorés.
EXE et installateur reconstruits depuis `358a551` (`dist/installer-candidate-358a551/PokeMind-Setup-0.9.3.exe`, non signé,
SHA-256 `6FE31F2D62BCB1A8AE1BCA80BDE11F7555F5E46346BB6F72D7A5E71F0CCD049D`), **installés chez le propriétaire** (sortie 0,
EXE installé = build) et déployés dans `dist/PokeMind/` (retour arrière `dist/PokeMind-before-consent-acef…`).
Préférences de la copie installée : `cloud_consent` était déjà vrai, `sharing` passé de `public` à `aggregates`;
sauvegarde `preferences.before-consent-<horodatage>.json` à côté; seuls ces deux champs ont été lus.

## Ajout D-288 (même session, demandes du propriétaire) : saison à 0 corrigée, mes decks et deck principal
Code **`6cb86c4`**. Cause du 0 et correctif : voir DECISIONS D-288 (date d'ajout `added_on` portée par chaque partie du
rapport affiché, sans nom de fichier). Deck Lab : « ＋ Ajouter mon deck… » et « Deck principal ». Tests : non-régression
saison (`test_pasted_logs_count_in_the_current_season_of_the_overview`), saisie de deck et deck principal (Qt), validation
de la préférence. **Porte locale complète VERTE** : Qt 118, cœur 1611 réussis, 0 échec, 3 ignorés.
EXE et installateur reconstruits depuis `6cb86c4` (`dist/installer-candidate-6cb86c4/PokeMind-Setup-0.9.3.exe`, non signé,
SHA-256 `643B2F66C8451A7D6006B208C306374D8439F8041300C1A1A7DC6CA2498A6815`), module `deck_entry` embarqué, fumée de l'EXE gelé
(fenêtre visible, 7 pages; sortie 2 = dossier synthétique vide), **installés chez le propriétaire** (sortie 0, EXE installé =
build) et dans `dist/PokeMind/` (retour arrière `dist/PokeMind-before-seasons-fix-6bb3…`). Données du propriétaire non lues :
ses parties déjà collées doivent maintenant apparaître dans « Saison actuelle » à l'ouverture (à confirmer par lui).

## Limites
- Retour visuel du propriétaire à faire, sur son écran (captures hors écran; 125 % non recapturé pour ce mandat).
- Assistant d'installation non lancé ni installé (même AppId que l'installation éventuelle du propriétaire); ses images
  sont vérifiées comme fichiers et l'icône dans le PE. Raccourcis : ils pointent vers `PokeMind.exe`, dont la ressource
  est vérifiée; non créés réellement.
- L'Explorateur du propriétaire peut afficher l'ancienne icône depuis son cache pour un EXE déjà vu au même chemin; ce
  n'est pas une mauvaise ressource (vérifiée dans le PE et sur chemin neuf).
- Le nouveau build n'a pas `libssl-3-x64.dll` / `libcrypto-3-x64.dll` (797 fichiers = 798 précédents − ces 2 DLL + la
  carte) : DLL optionnelles du module TLS OpenSSL de Qt, que PyInstaller avait prises sur le PATH de
  l'ancienne session. PokeMind n'utilise pas QtNetwork; le HTTPS Python (`_ssl.pyd` + `libssl-3.dll`/`libcrypto-3.dll`)
  est présent. À confirmer par la réception (Mises à jour, catalogue) — non corrigé, hors mandat.
- Installateur non signé (inchangé).

## Données
Aucune lecture de `data/local`, de `%LOCALAPPDATA%\PokeMind`, de journaux, de decks ou de secrets. Tests et captures sur
fixtures synthétiques dans des copies temporaires; fumée avec un dossier de données synthétique temporaire.
