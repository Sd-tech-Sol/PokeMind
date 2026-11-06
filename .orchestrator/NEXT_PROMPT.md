# PM-UI-BRAINBALL-THEMES-001 — Refonte couleurs PokeMind (thèmes foncé + clair)

**Exécuteur : Claude Code. Autorisation du propriétaire : demande explicite du 2026-11-05.**
**État : IMPLEMENTED/REPORTED le 2026-11-05 (D-284, voir `RESULT.md`); ne pas réexécuter. Audit ChatGPT à suivre.**
**Une seule tâche : réharmoniser les couleurs de la GUI existante sans changer le comportement.**

## 0. Prévol obligatoire

1. Tu es dans le dépôt **privé** `Sd-tech-Sol/PokeMind-dev`. Branche autorisée : `work/pm-v1-lotj-final-readiness-windows`. Ne touche PAS au dépôt public `Sd-tech-Sol/PokeMind` et ne publie aucune nouvelle release, même si une version locale est reconstruite.
2. Synchronise cette branche : `git fetch` puis `git pull --ff-only`. Si divergence, modifications locales non commitées ou branche non conforme, STOP sans reset, rebase ni force push.
3. Lis `AGENTS.md`, `CLAUDE.md` s'il existe, `.orchestrator/SESSION_CONTINUITY.md`, `.orchestrator/WORKFLOW_ADOPTION_V2.md`, `.orchestrator/STATE.json`, le **premier bloc** de `.orchestrator/NEXT_ACTION.md`, `.orchestrator/HANDOFF.md`, `.orchestrator/RESULT.md`, les décisions pertinentes et ce mandat au complet.
4. Lis et applique intégralement **`docs/design/pokemind-brainball/palette.json`** (source HEX foncé/clair), **`docs/design/pokemind-brainball/README.md`** (direction artistique), et utilise **`docs/design/pokemind-brainball/palette-preview.svg`** comme aperçu.
5. Fais l'état réel de l'interface et des tests avant de modifier les sources. La dernière inspection a confirmé Python **PySide6/Qt** et `src/pokemind/desktop/theme.py` avec `PALETTES`, `colors()`, `palette()`, `stylesheet()`. De nombreux styles QSS contiennent des HEX figés. Vérifie les sources actuelles.

## 1. Objectif graphique

Référence principale : **carte PokeMind TCG Coach verticale originale**, avec cerveau-Pokéball, vortex **bleu électrique et royal**, cyan lumineux, or vif, rose/rouge limité au cerveau. Les valeurs de la palette annexée servent de référence exécutable, même sans image d'origine.

Le **troisième fond d'écran panoramique** est une référence secondaire d'ambiance. Ne pas recopier son violet dominant ni intégrer un fond d'écran illustré derrière les panneaux.

- Thème **foncé** : fond bleu nuit `#07142F`, menu `#081E4A`, cartes `#102652`, texte `#F7FAFF`, action primaire bleue `#0054C7`, accent or `#FFD54F`.
- Thème **clair** : fond `#F1F7FF`, panneaux blancs `#FFFFFF`, menu `#E0EDFF`, texte `#081B3A`, action primaire bleu royal `#003EA6`.
- Bandeau « À toi de jouer » : **dégradé bleu royal → bleu électrique**, texte blanc, détails or, pas de rouge omniprésent.
- **Victoires : bleu**. **Défaites : rouge**. **Inconnu/neutre : or / bleu gris**. Le rouge peut aussi marquer une action destructrice ou une erreur; aucun bouton principal générique rouge.
- Fidélité au logo existant : ne pas recréer ou remplacer le logo, ni les illustrations de cartes. Pas de polices téléchargées ni de nouvelles dépendances.

## 2. Implémentation (réutiliser avant de développer)

1. Auditer `theme.py`, palettes Qt, QSS, icônes `QPainter`, vues, dialogues, widgets, tableaux, graphique(s), Deck Lab/classeur, onglets, Réglages, chat/HTML, dock Coach, terminal et messages de chargement. Ne changer **que** les styles et tests qui les couvrent.
2. Centraliser les couleurs sémantiques dans le système existant `PALETTES`/`colors()`. Garder les anciennes clés utilisées par l'application et ajouter celles de `palette.json` au besoin. Supprimer les HEX visuels codés en dur seulement quand requis pour les deux thèmes. Ne pas refactoriser la logique métier ni les données.
3. Harmoniser navigation active/inactive, hover, focus clavier, disabled, boutons primary/danger, liens, dialogues, scrollbars, infobulles, champs, tableaux, statistiques, graphiques, pages, chat, terminal et binder. Assurer que l'ensemble du panneau de droite utilise effectivement le thème actif.
4. Respecter le choix de thème/langue et les préférences enregistrées. Si le changement de thème se fait déjà à chaud, le maintenir sur toutes les vues. Éviter les styles qui figent le thème foncé lorsqu'on passe en clair.
5. Contrôler le contraste sur **fond réel** : texte normal WCAG AA ≥4.5:1 et gros texte/éléments non textuels essentiels ≥3:1. Ajuster au besoin **en documentant précisément l'écart** dans RESULT.md. Pour les petits textes blancs, ne pas choisir un cyan ou bleu lumineux trop pâle. Les graphiques doivent comporter des étiquettes, pas uniquement des couleurs.
6. Valider au moins ces écrans dans **les deux thèmes** : Vue d'ensemble, Coach/dock, Deck Lab/classeur, Réglages, Terminal, graphiques, dialogues et fenêtre redimensionnée. Vérifier 100 % et 125 % DPI si disponibles.
7. Ajouter des tests ciblés palette/contraste/persistance du thème et ses styles critiques. Utiliser **uniquement** des fixtures synthétiques; ne jamais inspecter la base personnelle, `data/local`, les vrais journaux, ni des secrets.

## 3. Vérifications et livraison

- Exécuter la **porte complète existante** `python scripts/local_gate.py` selon `AGENTS.md` (isolation des tests impérative). Les tests ciblés seuls ne suffisent pas.
- Produire des captures **synthétiques** des thèmes foncé et clair dans la vue d'ensemble et le Coach (si réalisable). Éviter toute image contenant des données personnelles.
- Si la porte est verte, reconstruire l'EXE **local de développement** avec les scripts déjà prévus, et confirmer qu'il démarre. **Ne pas installer ni publier de nouvelle version publique** et ne pas écraser/supprimer des données utilisateur.
- Commit/push sur la **branche privée autorisée uniquement**, sans force. Écrire un rapport court mais vérifiable dans `.orchestrator/RESULT.md` : HEAD de code, fichiers changés, tests et nombres précis, captures, limites, EXE reconstruit ou non, données non consultées. Mettre à jour HANDOFF/NEXT_ACTION/STATE selon la méthode du dépôt; préserver la réception de 0.9.2 comme tâche antérieure en attente.
- **Statut : IMPLEMENTED/REPORTED, jamais VERIFIED** (audit indépendant ChatGPT à suivre). Une fois ce mandat terminé, STOP. Ne pas enchaîner vers une autre grosse fonction.

## Critères d'acceptation

La GUI présente des couleurs cohérentes dans ses deux thèmes, fidèle à la carte PokeMind originalement choisie; les zones importantes gardent leurs contrastes et le changement de thème ne laisse pas de fonds gris/rouges résiduels inappropriés. Aucun changement métier, données privées, fournisseur IA, dépendance visuelle, release publique ou comportement fonctionnel.

**Ce fichier constitue le mandat intégral. Aucun prompt supplémentaire ni discussion de brainstorming requis.**
