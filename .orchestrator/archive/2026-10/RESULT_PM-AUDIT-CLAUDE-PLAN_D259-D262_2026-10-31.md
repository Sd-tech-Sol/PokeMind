# RESULT — PM-AUDIT-CLAUDE-PLAN, étape 4 avancée : coach avec les mêmes outils partout (2026-10-29)

Exécuteur : Claude Code (Opus 5.5). Autorisation : D-258; ordre du propriétaire en session (D-259) : rendre le coach
fonctionnel et **identique sous Codex, Claude et un modèle local**. Code : **`9968466d2bf4a2dda259eaec3eac9d33b3998188`**.
Étape 1 : [archive/2026-10/RESULT_PM-AUDIT-CLAUDE-PLAN_etape1_2026-10-29.md](archive/2026-10/RESULT_PM-AUDIT-CLAUDE-PLAN_etape1_2026-10-29.md).

## Symptôme signalé par le propriétaire
« crée-moi un deck puissant qui inclut Charizard » (Codex) : réponse « outils PokeMind indisponibles », deux vieilles
cartes Dracaufeu hors Standard, demande d'une capture. Ce n'était pas normal.

## Causes trouvées (toutes reproduites sur les seuls caches PUBLICS, par copie)
1. **Codex** : `features.code_mode_host=false` → chaque appel d'outil dynamique PokeMind échouait (« code-mode host is disabled »).
2. **Légalité** : les assertions de rotation n'étaient valides que le jour de leur vérification (fenêtre `effective_from = effective_to`);
   depuis le 2026-10-23, toute carte était `unknown`.
3. **`validate_deck`** : appel à `check_deck_entries` sans `total_cards`/`exact_confirmed`/`ordinal` ni alias de codes → échec systématique.
4. **Recherche de cartes du contexte** : 5 premiers mots, FTS « OU », 3 résultats, sans tri par date/format, cartes Pocket incluses.
5. **Claude** : `--tools ''` + `--safe-mode` (qui désactive tout serveur MCP) → aucun outil.
6. **Modèle local (Ollama)** : aucun outil.
7. Erreurs d'outil avalées sans trace.

## Correctifs
- `codex_app_server.py` : `code_mode_host` requis (exécuteur des outils dynamiques de Codex 0.163); `code_mode`, shell et
  `unified_exec` restent coupés; fil coach toujours `read-only`, réseau coupé.
- `rules.py` : `latest_verified_rotation` + `presume_mark` — **légalité présumée** (marques H/I/J en vigueur depuis le
  2026-03-26, dernière vérification le 2026-10-22, confiance moyenne), distincte du verdict strict qui reste `unknown`.
- `coach_cards.py` (nouveau) : recherche FR/EN par mots du nom; exclut TCG Pocket, collections McDonald's `unknown`; jouable d'abord,
  extension principale avant promo; ligne d'export `nom anglais CODE numéro`; énergie de base sans marque = jouable.
- `services.py` : `cards` accepte jusqu'à 15 noms séparés par `;` (un appel au lieu de 15); `validate_deck` corrigé,
  retourne les problèmes ligne par ligne avec une impression jouable de même nom; seules les vraies violations de
  structure comptent (règle absente = structure inconnue); `legality` sans identité → `IDENTITY_REQUIRED`.
- `tools.py` : `run_tool` unique pour les trois moteurs (plafond 24 000 octets, erreurs typées, journal
  `Outil <outil>/<opération> · résultat · taille · durée`, jamais la question ni le contenu).
- `mcp_bridge.py` (nouveau) : serveur MCP HTTP **127.0.0.1 seulement**, jeton aléatoire par session, Host/Origin
  contrôlés, corps ≤ 1 Mo; sert à Claude **les deux mêmes outils** que Codex.
- `provider.py` : texte système coach commun (`COACH_SYSTEM`) avec méthode de construction de deck; Claude coach sans
  `--safe-mode` mais sans outils intégrés, sans fichiers de réglages, sans mémoire automatique ni crochets; Ollama :
  boucle d'outils (8 tours max), repli sans outils si le modèle ne les gère pas.

## Preuves
`python scripts/local_gate.py` (copie hors dépôt, sans `data/local`, hors ligne, Qt `offscreen`) au SHA du code :

| Étape | Résultat |
|---|---|
| Compilation, hygiène Git | OK, OK |
| Tests Qt | **68 passed** |
| Tests du cœur | **1499 passed, 3 skipped (OCR non attesté)** |
| **Total** | **1567 réussis, 0 échec** — PORTE LOCALE : **VERTE** |

Nouveaux tests `tests/test_coach_tool_parity.py` (catalogue et pairs **inventés**) : présomption après fermeture de la
fenêtre, classement et exclusion Pocket, `validate_deck` avec correction, journal sans contenu, pont MCP (403 sans jeton
ou avec `Origin`, 202 notification, `tools/list` = outils Codex), faux Claude qui appelle le pont depuis sa propre
`--mcp-config`, boucle Ollama avec et sans prise en charge des outils.

**Essais réels de bout en bout** (vrais moteurs, racine jetable ne contenant que des copies des caches PUBLICS, même
chemin que l'application : `prepare_question` + `read_tool`) sur la question du propriétaire :

| Moteur | Avant | Après |
|---|---|---|
| Codex (`codex-cli 0.163.0`) | 0 outil (« code-mode host is disabled »), aucune liste | **190 s, 29 appels** (`cards`, `legality`, `validate_deck`…) : Méga-Dracaufeu X-ex PFL 013 + Plumeline-ex, 60 cartes en français avec codes, export TCG Live, **validé : 60 cartes, aucun problème** |
| Claude (Claude Code 2.1.312) | aucun outil (`--safe-mode`) | **85 s, 22 appels** : Méga-Dracaufeu X-ex/Y-ex, 60 cartes, export, **validé** |

Le premier essai Codex après correction avait pris 237 s et 53 appels; la recherche groupée (`;`) a ramené à 190 s.
Les deux réponses citent la base de la légalité présumée (H/I/J depuis le 2026-03-26, vérifiée le 2026-10-22) et
gardent collection, crédits et taux de victoire inconnus. Le journal montre une ligne par appel, sans contenu.

GitHub Actions : bloqué par le budget; non revendiqué.

## EXE
- `Build-PokeMindDesktop.ps1 -StagingRoot build/exe-upgrade-<32 hex>` (staging neuf, paramètres de production) : **exit 0, 788 fichiers**.
- Archive figée lue sans exécution : **67/67 modules `pokemind.*` et l'entrée `app` identiques** aux sources de `9968466`
  (dont `coach_cards` et `assistant.mcp_bridge`); **0 module QA**.
- **Smoke du vrai EXE** sur une fixture **inventée** neuve (cloud refusé), seul `POKEMIND_DESKTOP_SMOKE=1` actif : **exit 0**,
  figé, visible, 6 pages, rapport, liste exacte 60, galerie, import, activité : tous vrais; DB synthétique inchangée;
  capture inspectée (interface ordinaire, sans bandeau QA).
- Permutation : première tentative **refusée avant tout déplacement** (application du propriétaire ouverte); après fermeture
  par le propriétaire (« go ») : ancien `dist/PokeMind` (**788 fichiers**) déplacé intact vers `dist/PokeMind-before-coach-…`,
  candidat installé : **788 fichiers identiques** (SHA-256), ancien dossier identique à l'original. `data/local` jamais ciblé.
- **Retour arrière** (non exécuté) : fermer l'app, renommer `dist/PokeMind` en un nom neuf, renommer `dist/PokeMind-before-coach-…` en `dist/PokeMind`.

## Ajout du 2026-10-30 : supprimer une discussion (D-260)
Demande du propriétaire : « est-ce possible de pouvoir supprimer les conversations par après ». Bouton **Supprimer** à
côté de Nouveau/Copier : confirmation Oui/Non (Non par défaut), puis effacement du seul fichier de la discussion affichée
et de son entrée dans l'historique. Les copies gardées par Codex ou Claude dans leurs propres dossiers ne sont pas
touchées (le dialogue le dit). Code **`c09db4ba7203a0aebdf555391b62064effbdaa29`**; porte locale **VERTE : Qt 69 passed,
cœur 1500 passed / 3 skipped, total 1569 / 0 échec**. EXE recompilé depuis `c09db4b` : 67/67 modules identiques, 0 module QA,
smoke exit 0 sur fixture inventée neuve (bouton visible sur la capture), permutation faite application fermée :
788 fichiers installés identiques, ancien dossier conservé (`dist/PokeMind-before-delete-…`).

## Ajout du 2026-10-31 : « fais-moi un deck » atteint enfin le moteur (D-261)
Signalé par le propriétaire : « fais-moi le meilleur deck avec Pikachu » → réponse = « tout ce que j'avais en mémoire »
(sous Claude); sous Codex, « j'appuyais sur Entrée, ça ne marchait pas ». Reproduit dans la vraie fenêtre (racine jetable,
caches PUBLICS copiés seulement, vrais moteurs) :
1. **Cause principale** : `personal_question` jugeait « personnelle » toute phrase contenant `moi`, `je`, `me`, `mon`…
   Avec le partage « connaissances publiques seulement », la question partait en **réponse locale** (bilan de statistiques)
   sans jamais appeler Codex ni Claude. Règle existante avant ce mandat, non introduite par D-259/D-260.
2. Entrée pendant l'analyse locale du démarrage : texte laissé dans la zone de saisie, simple message gris.
3. Codex construit un deck en 190 à 264 s; la limite du coach était **300 s** (risque `CODEX_TIMEOUT` avec plus de contexte).
4. Réponse encombrée de lignes « [Outil · … completed] »; texte de travail collé à la réponse (« …validate_deck.J'ai monté »).
5. Test instable découvert par la porte : le pont MCP refusait (403) avant de lire le corps → sous Windows,
   **1 refus sur 7 devenait une coupure de connexion** (800 essais : 108 `WinError 10053`; après correctif : 800 × 403).

Correctifs (code **`50c8f49504bfa28bb16157d381da50864e697d59`**) : données personnelles = mots de données (stats, combats,
défaites, parties, « mes decks »…), plus les pronoms seuls; une demande de construction de deck va toujours au moteur
(statistiques toujours retenues si le partage est public); question en file d'attente pendant l'analyse, envoyée seule
à la fin; limite coach 600 s (Codex et Claude); compteur « Outils PokeMind · consultation N » dans la barre d'activité au
lieu des lignes d'outil; nouveau paragraphe après des appels d'outils; consigne : le champ `standard` de `cards` suffit,
`validate_deck` contrôle chaque ligne; pont MCP : lecture du corps avant tout refus. Réponse locale : indique où activer
le partage des statistiques.

Preuves : porte locale **VERTE : Qt 71 passed, cœur 1502 passed / 3 skipped, 0 échec**. Nouveaux tests : deck « fais-moi »
envoyé au moteur sans statistiques et sans lignes d'outil (compteur vu), question perso toujours locale, Entrée pendant
l'analyse puis envoi automatique, paragraphes Codex/Claude, 300 refus du pont = 300 × 403 (échoue sans le correctif).
Essais réels dans la fenêtre, question exacte du propriétaire : **Claude 75 s**, **Codex 180 s / 25 appels** (avant : 264 s),
deck Pikachu-ex/Magnéton de 60 cartes, validé, sans ligne d'outil. EXE recompilé depuis `50c8f49` : 788 fichiers,
67/67 modules identiques, 0 module QA, smoke exit 0 sur fixture inventée neuve (DB inchangée, capture normale),
permutation application fermée : 788 fichiers installés identiques au candidat, ancien dossier conservé
(`dist/PokeMind-before-coachfix-…`). Une première tentative avec Windows PowerShell 5.1 s'est arrêtée **avant tout
déplacement** (`GetRelativePath` absent); refaite avec PowerShell 7.

## Ajout du 2026-10-31 (soir) : le coach n'attend plus l'analyse des combats (D-262)
Retour du propriétaire avec capture : « ça marche pas, ni Claude ni Codex ». Barre d'état figée sur « 68 / 69 fichiers
traités · analyse locale en cours » et chat sur « Analyse locale en cours; ta question partira… » : l'actualisation au
démarrage réanalyse tout le corpus (non incrémental, M-4) et, après le dernier fichier, enchaîne sans progression
les plans contre-deck, les imports et la mémoire; **toute question attendait la fin**. Liste « Reprendre une
discussion » illisible (titres coupés au milieu dans une boîte étroite).

Correctifs (code **`047f5dc99a1e9da8a8f40a77030c541b012b7f1f`**) : une question part immédiatement pendant l'analyse;
le coach répond avec le rapport déjà chargé (pas de relecture concurrente); seuls un journal collé ou un message pendant
une importation attendent. L'analyse journalise chaque étape avec sa durée (contexte public, base locale, fichiers lus,
familles, chaque plan contre-deck, imports, mémoire), jamais un journal, un nom ou un deck; la barre affiche « 69 / 69 »
dès que les fichiers sont lus; l'arrêt est vérifié entre les plans. Liste des discussions : 420 px à l'ouverture, titre
en premier, coupé à la fin.

Preuves : porte locale **VERTE sur une exécution seule : Qt 72 passed, cœur 1503 passed / 3 skipped, 0 échec**. (Une
exécution précédente arrêtée en cours a continué d'écrire dans le même fichier de sortie; elle n'est pas retenue.)
Nouveaux tests : question pendant l'analyse envoyée sans relecture du rapport, message pendant une importation mis en
file puis envoyé; liste des discussions large, titre d'abord; étapes journalisées avec durée et sans contenu, progression
`(n, n)` après lecture. Capture de la liste ouverte vérifiée (titres complets). EXE recompilé depuis `047f5dc` : 788 fichiers,
67/67 modules identiques, 0 module QA, smoke exit 0 sur fixture inventée neuve (DB inchangée), permutation
application fermée avec PowerShell 7 : 788 fichiers installés identiques, ancien dossier conservé (`dist/PokeMind-before-nowait-…`).

## Non fait / limites
- Aucune donnée personnelle ouverte; `data/local` personnel jamais lu (seuls les caches PUBLIC_ONLY, copiés).
- Ollama n'est pas installé sur ce PC : boucle prouvée sur pair inventé seulement.
- La légalité présumée n'est pas une vérification officielle à jour; la liste proposée reste à tester (collection,
  crédits, taux de victoire inconnus). Le cache compétitif public n'a que 32 listes de 2 tournois (2026-10-22).
- A-8 (mode explicite au lieu des regex) et le contexte minimal complet (A-7) restent à faire; D-261 rend l'aiguillage
  par mots moins piégeux, sans remplacer le sélecteur explicite prévu.
- Les réglages réels du propriétaire (consentement cloud, partage) n'ont pas été lus (`data/local` personnel).
- La lenteur de l'analyse elle-même n'est pas corrigée (M-4, étape 5) : l'étape lente sera visible dans « Copier le
  diagnostic » grâce aux lignes `Analyse · <étape> · <durée>`.
