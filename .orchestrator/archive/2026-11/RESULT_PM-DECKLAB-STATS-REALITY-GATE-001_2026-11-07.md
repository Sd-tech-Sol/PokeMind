# RESULT — PM-DECKLAB-STATS-REALITY-GATE-001 : porte complète finale + essai réel borné de l'API Limitless, 2026-11-07

Exécuteur : Claude Code (Opus 5.5). Mandat : premier bloc de `NEXT_ACTION.md` → `NEXT_PROMPT.md` (`7894018`, activé
`d1c06ed`), sur l'audit ChatGPT [`VERIFICATION_PM-DECKLAB-PUBLIC-STATS-001_2026-11-07.md`](VERIFICATION_PM-DECKLAB-PUBLIC-STATS-001_2026-11-07.md) (`3b0d726`).
Statut : **IMPLEMENTED / REPORTED; AWAITING_CHATGPT_AUDIT** (pas VERIFIED). **Aucune modification de code** : aucun défaut
bloquant reproduit. Version inchangée (`0.9.4`); aucune build, installation, tag, publication ni push public.
Rapport précédent (D-291) : [archive/2026-11/RESULT_PM-DECKLAB-PUBLIC-STATS-001_D291_2026-11-07.md](archive/2026-11/RESULT_PM-DECKLAB-PUBLIC-STATS-001_D291_2026-11-07.md).
**STOP pour audit ChatGPT.**

## 0. Prévol
- `git fetch` + `git pull --ff-only` : `06e3e5c` → `d1c06ed` (3 commits docs ChatGPT), arbre propre, aucun reset/rebase/force.
- Arbre de code final = celui de `3a56023` : `git diff --stat 3a56023 d1c06ed -- src tests scripts` = vide.
- Aucune donnée personnelle ouverte : ni `data/local` du dépôt, ni profil, ni vrai deck, ni journal, ni `status/search`.

## 1. Porte locale COMPLÈTE sur l'arbre final exact
`python scripts/local_gate.py` (copie temporaire hors dépôt sans `data/local`, hors ligne, `offscreen`) sur HEAD `d1c06ed`
(code identique à `3a56023`), **code de sortie 0** :
**PORTE LOCALE : VERTE** — compilation OK, hygiène Git OK, tests Qt **121 réussis**, tests du cœur **1634 réussis / 0 échec / 3 ignorés** (HEAD `d1c06ed`, 668 fichiers copiés, 534 s).
Relance identique sur l'arbre du rapport (mêmes sources + ce rapport et les fichiers d'orchestration, 669 fichiers, avant
remplacement des seuls champs de comptes) : **VERTE, Qt 121, cœur 1634 / 0 / 3, code de sortie 0** (507 s).
Aucun test lancé directement dans le dépôt pendant ce mandat (écart signalé à l'audit, non répété).

## 2. Essai réel de l'API Limitless (une seule collecte, publique, bornée)
Méthode : `deck_public_stats.refresh(root, as_of='2026-11-07', manual=False)` — le chemin exact de l'onglet (collecteur
existant `research_matchups` → `run_campaign(meta_budget=8)` → `sync_meta(max_tournaments=1)`), dans un **root synthétique
vide** du dossier temporaire de session (hors dépôt, jamais versionné). Seule instrumentation : journal des URL/statuts/en-têtes
de quota des GET réellement émis. Aucun deck, nom ni liste transmis (la collecte ne reçoit aucune entrée de deck).

| # | Endpoint public contacté (`https://play.limitlesstcg.com`) | HTTP | Octets | Quota annoncé |
|---|---|---|---|---|
| 1 | `/api/games` | 200 JSON | 3 645 | `"50-in-5min"; r=49` |
| 2 | `/api/tournaments?game=PTCG&format=STANDARD&limit=6&page=1` | 200 JSON | 1 097 | r=49 |
| 3 | `/api/tournaments/{id}/details` | 200 JSON | 1 142 | r=48 |
| 4 | `/api/tournaments/{id}/standings` | 200 JSON | 39 992 | r=48 |
| 5 | `/api/tournaments/{id}/pairings` | 200 JSON | 7 496 | r=47 |

- **5 GET au total** (budget 8, quota fournisseur 50 / 5 min), 53 372 octets, aucun 429/403, aucune redirection, aucune
  relance. Second appel automatique immédiat : `CACHE_TODAY`, **0 GET**. `/games/{id}/decks` jamais appelé.
- Statut API : **disponible**, contrat conforme au client : `/games` publie bien `PTCGL` (« Pokémon TCG Live ») et `STANDARD`
  pour `PTCG`; en-tête `RateLimit` au format IETF (`r=`) correctement lu par `meta._rate_limit_remaining` (49 → 49; `r=0` → 0).
- Tournoi public retenu (non personnel) : « Hit Challenge #59 | TCG Live » (id `6ae5e417ae67092a4073fc4f`), **2026-11-07
  18:00 UTC**, `PTCG / STANDARD / PTCGL`, en ligne, public, 23 joueurs, phases **SWISS 5 rondes BO1 + top cut 3 rondes BO1**
  (aucun BO3 dans cet échantillon). Statut de finalisation fournisseur : `unknown` (instantané `complete` : standings + pairings).
- Archétypes : publiés pour **23/23** placements (`archetype_published`), 12 archétypes dont `Other` (5), `Rocket's Honchkrow`
  (4), `Cynthia's Garchomp` (3). Matchs : 59 dont 56 admissibles, 3 byes exclus, 0 double défaite, 0 doublon de `match_key`.
- Confidentialité : pseudos stockés uniquement en HMAC (64 hex) dans `meta_placements` / `meta_matches`; aucune liste de
  60 cartes; aucun fichier de l'essai n'est versionné.

## 3. Rendu réel du code, ensuite **hors ligne** (sockets désactivés avant import; toute tentative réseau aurait levé)
Decks **synthétiques** faits de noms de cartes publiques (aucun deck du propriétaire), lus par `public_view` puis
`insights.project_public_stats`, et panneau Qt `PublicStatsPanel` rendu hors écran (capture locale non versionnée) :

| Deck synthétique | Statut | Rendu (extraits exacts) |
|---|---|---|
| Murkrow ×4 + Honchkrow ×3 (Team Rocket's) | `OK` | « Archétype public : Rocket's Honchkrow — correspondance par les Pokémon de ta liste (indice, pas une certification) » · « Représentation (tournois BO1) : 17 % (4 / 23 placements classifiés, 1 tournoi(s)) » · « Taux de victoire BO1 : 55 % (IC 95 % 35–73 %) · 12 V / 8 D / 2 N · n=22 matchs admissibles (miroirs exclus : 1) » · « Exclus : byes 3 » |
| Mewtwo ex ×2 + Honchkrow ×2 (Team Rocket's) | `ARCHETYPE_AMBIGUOUS` | « plusieurs archétypes publics correspondent autant (Rocket's Honchkrow, Rocket's Mewtwo). Aucun taux attribué à ce deck. » |
| Cynthia's Gible/Gabite/Garchomp ex | `INSUFFICIENT_MATCHES` | « Représentation … 13 % (3 / 23) » · « Taux de victoire BO1 : données insuffisantes · 5 V / 5 D / 2 N · n=12 » |
| Pikachu ex + Raichu | `ARCHETYPE_UNIDENTIFIED` | « aucun archétype de l'échantillon public ne correspond … Aucun taux attribué; méta publique générale ci-dessous. » |

- Chaque barre de matchup : `n` < 10 → « n trop petit, aucun pourcentage » (toutes, ici). Évolution : « historique insuffisant
  (moins de deux tournois) ». Source + doc officielle, population, fenêtre `2026-10-11 → 2026-11-07`, tournois analysés
  `1 (2026-11-07 → 2026-11-07)`, « Dernière synchronisation réussie : 2026-11-07 23:13 UTC (date de récupération, pas date
  des matchs) », dernière tentative et son résultat : tous affichés.
- **Oracle indépendant** (recompte SQL direct des `meta_matches` admissibles × archétype publié de chaque joueur) :
  Honchkrow 12/8/2, miroir 1; Garchomp 5/5/2, miroir 0; ventilation par adversaire identique à la vue. **Égalité exacte.**
- Garde réseau hors ligne : Actualiser avec horloge simulée à +60 s de la collecte → `REFRESH_TOO_SOON` (540 s), 0 GET; auto → `CACHE_TODAY`;
  annulation avant le 1er GET (root vierge) → `INTERRUPTED`, `PUBLIC_RESEARCH_CANCELLED`, 0 GET, vue `NO_SNAPSHOT`.

## 4. Défauts, reproductions, risque `_snapshots`
- **Aucun défaut bloquant reproduit** → aucun test ni correctif ajouté, dernier snapshot valide intact.
- `_snapshots` (fichier entier écarté si un tournoi chevauche un fichier plus récent) : **non reproductible avec le pipeline
  réel** : `sync_meta(max_tournaments=1)` n'importe qu'un tournoi par base de campagne (vérifié dans le code et sur la base
  réelle : 1 tournoi), donc un chevauchement = même tournoi, et l'écarter est exactement la déduplication voulue. Le risque ne
  naîtrait que si une campagne importait plusieurs tournois; corriger exigerait un filtrage par tournoi dans `meta_*`
  (refonte hors mandat). **Gardé comme limite documentée**, sans correctif.
- Observations non bloquantes (aucun changement fait) : (a) `Other` est un archétype **publié** par Limitless; il compte donc
  comme « classifié » au dénominateur de la représentation et comme adversaire dans les matchups (matchs réels) — un deck ne
  peut pas être identifié « Other »; (b) l'axe du graphique de matchups saute une graduation (0, 1, 2, 4, 5) — cosmétique;
  (c) un tournoi du jour à finalisation `unknown` peut être repris plus complet le lendemain; le plus récent l'emporte.

## 5. Limites de l'échantillon (honnêtes)
1 tournoi, 23 joueurs, BO1 seulement, 56 matchs admissibles : chiffres d'**archétype dans un petit échantillon public
PTCGL en ligne**, jamais « mondiaux » ni « tes 60 cartes ». Le seul taux affichable (Honchkrow, n = 22) a un IC 95 % large
(35–73 %). L'échantillon grossit d'au plus 1 tournoi par jour (collecteur existant); BO3 absent aujourd'hui.

## Prochaine action unique
**Audit indépendant ChatGPT** de ce rapport (code inchangé `3a56023`). Build candidat 0.9.5, installation chez le
propriétaire ou publication : chacun sur GO explicite distinct. La 0.9.4 reste en attente de sa réception et de son GO.
