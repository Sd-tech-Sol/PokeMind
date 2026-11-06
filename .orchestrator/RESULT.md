# RESULT — PM-UI-BRAINBALL-THEMES-001 : couleurs BrainBall, thèmes foncé et clair (D-284), 2026-11-05

Exécuteur : Claude Code (Opus 5.5). Mandat : [NEXT_PROMPT.md](NEXT_PROMPT.md), déclenché par le propriétaire.
**État : IMPLEMENTED/REPORTED, non VERIFIED** (audit indépendant ChatGPT à suivre).
Rapport précédent (D-283) : [archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D283_2026-11-05.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D283_2026-11-05.md).

## Prévol
- Branche `work/pm-v1-lotj-final-readiness-windows` à jour (`git pull --ff-only` : déjà à jour, HEAD `4f572fe`).
- Aucune contradiction ni danger relevé dans le mandat. Visuel seulement : aucune logique, donnée, fournisseur IA,
  dépendance, logo, illustration ni publication.

## Fait (code `cdd2fc6`)
- **Source unique** (`desktop/theme.py`) : `PALETTES` reprend **tels quels** tous les jetons de
  `palette.json` (foncé et clair) et `BRAND` ses couleurs de marque. Les ajouts sont déclarés dans `DERIVED` :
  `primary_pressed`, `hero_muted`, `hero_border`, `nav_icon_selected`, `tooltip*`, `overlay`, `field_border`.
  Les objets identiques dans les deux thèmes (classeur, terminal) sont dans `OBJECTS`.
- **Feuille de style** : plus aucune couleur codée en dur; tout vient des jetons (test). Bandeau « À toi de jouer »
  en dégradé royal → électrique, texte blanc, surtitre or. Item de menu sélectionné, onglets cochés et bouton
  principal en bleu primaire (plus de rouge générique). Survol, focus (anneau or en foncé, bleu en clair),
  désactivé, liens, infobulles, barres de défilement horizontales et verticales, champs, tableaux, bandeaux.
- **Résultats** : victoires en bleu, défaites en rouge, inconnues en or (tuiles, barres, beigne, statistiques);
  les graphiques gardent leurs étiquettes texte (« Victoires : 2 », « D=4 · n=6 »).
- **Rouge réservé** aux défaites, erreurs et actions destructrices : « Supprimer », « Tout supprimer » et
  « Réinitialiser » sont en rouge, fond rouge au survol (propriété `destructive`).
- **Icônes dessinées** : menu (or en foncé, bleu en clair; version sélectionnée contrastée), Réglages (teinte
  par rôle du thème; onglet coché en contraste), agrandir/ramener du coach, boutons du Terminal. Toutes
  redessinées au changement de thème (`themed_icons`). Le logo n'a pas changé.
- **Panneau de droite (coach)** : barre de titre, corps, bulles (la vôtre en bleu primaire), liens et puces
  d'outils suivent le thème actif.
- **Listes déroulantes** : chevron dessiné aux couleurs du thème (le bouton natif laissait un trait foncé à
  droite, visible en clair); repli sur la flèche native si le dossier temporaire n'est pas inscriptible.
- **Classeur** : couverture bleu royal et liseré or (au lieu du rouge), pages marine dans les deux thèmes.
  Légende des cartes sans illustration (Pokémon rouge, Dresseur bleu, Énergie or) inchangée.
- **Terminal** : marine `#081C3E` dans les deux thèmes (les programmes console choisissent leurs couleurs ANSI
  pour un fond foncé); sa réponse OSC 11 annonce ce fond.
- **Animations** : halo de transition or et cyan (au lieu d'or et rouge); sablier en bleu lumineux et or.
- Assistant de premier lancement : reste en thème foncé (inchangé).

## Contraste sur fond réel (WCAG 2)
Mesures (`theme.contrast`), foncé / clair :

| Paire | Foncé | Clair |
|---|---|---|
| texte / fond | 17.5 | 15.9 |
| texte atténué / panneau | 10.2 | 7.3 |
| texte atténué / menu | 11.2 | 6.2 |
| texte sur bouton primaire | 6.8 | 9.4 |
| rouge / panneau | 5.4 | 6.1 |
| bleu / panneau | 7.4 | 7.3 |
| or (jaune) / panneau | 10.5 | 7.2 |
| surtitre or / début du bandeau | 7.5 | 7.5 |
| texte blanc / fin du bandeau | 7.3 | 7.3 |
| avertissement / son fond | 10.4 | 7.0 |
| contour de champ / champ | 3.8 | 3.5 |
| icône sélectionnée / primaire | 4.8 | 9.4 |
| terminal | 16.1 | 16.1 |

**Écart documenté — un seul** : `border` de `palette.json` (foncé `#335A8E`, clair `#B7CBE7`) donne 2.40:1 et
1.59:1 autour des champs, sous le 3:1 exigé pour un élément essentiel. Il reste la bordure **décorative** (cartes,
panneaux, séparateurs). Les champs, boutons radio et poignées de défilement prennent le jeton dérivé
`field_border` (foncé `#4F79B0`, clair `#7088AD`, de 3.3 à 4.1:1 sur fond, panneau et champ). Aucun jeton de
`palette.json` n'a été modifié.

## Tests
- Nouveau `tests/test_desktop_theme.py` (7 tests) : jetons identiques à `palette.json` et seuls dérivés
  déclarés; contrastes ≥4.5 (texte) et ≥3 (graphiques, focus, contours, teintes des Réglages) sur les fonds
  réels; feuille de style sans jeton résiduel ni couleur hors thème, bouton primaire bleu, bandeau en dégradé,
  aucun ancien rouge; sens des couleurs (bleu, rouge, or) dans les deux thèmes.
- Qt : `test_qt_theme_switch_redraws_the_drawn_icons_and_the_chat` (préférence enregistrée, feuille de style,
  icônes du menu et des Réglages, bulle du coach, dans les deux sens). Ajustés : barre victoires/défaites
  (rouge du thème), réponse OSC du terminal.
- **Porte locale complète VERTE** sur l'arbre de code de `cdd2fc6` : Qt 114, cœur 1610 réussis, 0 échec,
  3 ignorés. Porte finale au HEAD du rapport : voir HANDOFF.

## Captures (synthétiques)
Fixture inventée des tests Qt (« Invented Family », question inventée), sans aucune donnée personnelle.
Dans le dépôt : `docs/design/pokemind-brainball/captures/` :
- `overview-coach.png` : vue d'ensemble + coach, foncé et clair (1280×860, bandeau de mise à jour visible);
- `pages-dark.png`, `pages-light.png` : Combats, Deck Lab, Cartes & méta (classeur), Apprentissage, Réglages
  (Général, Mises à jour), Terminal, fenêtre étroite 900×700;
- `overview-125.png` : vue d'ensemble à 125 %; `dialogs.png` : boîte de dialogue dans les deux thèmes.
Vérifiés à l'œil dans les deux thèmes : vue d'ensemble, Combats, Deck Lab, Cartes & méta (classeur),
Apprentissage, Réglages (Général, Mises à jour), Terminal, coach (dans chaque capture), bandeau de mise à jour,
dialogue, fenêtre étroite 900×700, et 125 % (`QT_SCALE_FACTOR=1.25`).

## EXE local
**Reconstruit** depuis `cdd2fc6` (arbre propre), avec les scripts existants (`Build-PokeMindDesktop.ps1`,
`Build-PokeMindInstaller.ps1`) :
- 83 modules `pokemind` identiques aux sources, aucun module QA; aucun nom d'utilisateur Windows dans les
  799 fichiers produits (EXE, bibliothèques, installateur);
- **démarre** : fumées en mode projet, en mode autonome (`POKEMIND_DATA_ROOT` synthétique) et dans une copie
  installée temporairement, sortie 0 (fenêtre visible, 7 pages, terminal disponible); base synthétique
  inchangée; installation et désinstallation temporaires propres; dossier de données du propriétaire non ouvert;
- déployé dans `dist/PokeMind/` (798 fichiers, identiques au candidat testé); l'ancienne copie est conservée
  sous `dist/PokeMind-before-brainball-<id>`; PokeMind était fermé;
- `dist/installer/PokeMind-Setup-0.9.3.exe` remplacé (non signé, SHA-256
  `4768ED25DF88EC91F8C62363D2CCBC2333ADBC62C21A6E6211F0AF761240AD3C`); l'installateur 0.9.3 précédent est
  gardé sous `PokeMind-Setup-0.9.3-mises-a-jour.exe`. Tout cela est hors Git. **Rien n'est installé chez le
  propriétaire, rien n'est publié.**

## Limites
- 125 % simulé par `QT_SCALE_FACTOR` sur la plateforme hors écran, pas sur un écran réel à 125 %.
- Les captures sont rendues hors écran (polices de Windows), pas dans une session de bureau.
- Les boîtes de dialogue système (sélecteur de fichiers Windows) gardent l'apparence de Windows.
- Le chevron des listes est un petit PNG écrit une fois dans `%TEMP%\pokemind-theme` (aucune donnée).

## Données
Aucune lecture de `data/local`, de `%LOCALAPPDATA%\PokeMind`, de journaux, de decks ou de secrets. Tests et
captures sur fixtures synthétiques dans des copies temporaires; fumée de l'EXE avec `POKEMIND_DATA_ROOT`
synthétique. Aucune écriture dans le dépôt public, aucune publication. 0.9.3 toujours en attente du GO.
