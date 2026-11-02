# VERIFICATION_PM-0005B — audit indépendant ChatGPT (2026-10-12 UTC)

## Verdict
**LIVRÉE, NON VERIFIED — PM-0005B-R1 CORRECTION CIBLÉE REQUISE.** Fondation Limitless et tests présents; revue de code indépendante identifie une non-progression de sync entre sessions et la récupération de données de classements/appariements de tournois qui auraient dû être exclus immédiatement après `details`. Renforcer aussi les redirections et la gestion préventive du quota. L'utilisateur autorise la préparation automatique des corrections usuelles sans demande de « go » répétée.

## Éléments GitHub réellement vérifiés
- Repo privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0005b-limitless-meta-foundation`, commit Codex `019ee5348dd9771f9dd30d92dfb079e8c6d65c61`, parent orchestration `bf63ba0c7a12442b34c8d5d3104ac5f816e205dd`.
- Comparaison GitHub : **1 commit en avance, 0 retard; 16 fichiers**. Code `src/pokemind/meta.py` (925 lignes), migration `database.py`, CLI, `tests/test_meta.py` (338 lignes), docs et RESULT examinés. Pas de fusion.
- Arbre Git complet **118 entrées, truncated=false**, aucun SQLite, vrai deck/journal, backup, photo ou secret sous `data/local/` dans l'arbre. La base locale personnelle n'est pas accessible à ChatGPT.
- GitHub a renvoyé **0 statut CI et 0 workflow PR** pour ce SHA. Codex rapporte **128 passed prévol / 143 passed final**, compilation, diff, intégrité SQLite 7 et conservation des invariants, non réexécutés indépendamment.
- Codex rapporte un essai réel de **5 GET**, un tournoi public, 5 placements, 16 appariements dont 9 marqués admissibles, aucun archétype disponible; **aucun matchup réel** ne peut être estimé. Ces résultats proviennent de Codex et ne sont pas reproduits par ChatGPT.

## Fonctions cohérentes et préservables
- HTTP HTTPS GET sur `play.limitlesstcg.com/api`, pas de clé, budget/retry/timeout et limite JSON; `--dry-run` renvoie une prévision sans réseau/écriture. Endpoint `/games/{id}/decks` bloqué dans le constructeur d'URL.
- SQLite schéma 6→7 additive avec `sqlite3.backup()`, transaction/rollback testé, tables `meta_games`, `meta_tournaments`, `meta_phases`, `meta_placements`, `meta_matches`, `meta_sync_state`. Pseudos participants remplacés par HMAC avec une clé locale, salt logique par tournoi; aucune decklist ni identifiant PTCGL stocké.
- Remplacement transactionnel de snapshot de tournoi une fois trois ressources valides; filtre PTCG/format/plateforme/isOnline/public, matchups par tournoi/phase/BO, provenance et fractions `n` avec faible échantillon inconnu. Aucune intégration jeu ni planificateur.

## DÉFAUT CONFIRMÉ 1 — manque de progression entre exécutions
**Code : `src/pokemind/meta.py::sync_meta`, section liste des tournois et boucle `for brief in briefs`, approximativement lignes 588–683.**
- À **chaque invocation**, GET `/tournaments?...&page=1` puis `limit=min(50,max(max_tournaments,max_tournaments*3))`. La boucle de pagination ne s'active que si `len(briefs) < max_tournaments` : avec une première page de 6 IDs uniques et `max_tournaments=2`, elle est déjà fausse. Code itère alors les deux premiers tournois et stoppe.
- Le sync **ne saute pas** les IDs déjà archivés sous `meta_tournaments`, ni ne conserve un curseur durable permettant de reprendre plus loin. Deuxième, troisième exécution avec la même liste importent donc encore les mêmes IDs; **aucun progrès** sur les tournois restant dans la page ou les pages suivantes. Le test `test_listing_pagination_skips_duplicates_within_budget` valide les duplications dans une page, **pas le comportement sur deux exécutions successives**.
- Impact : les scores rafraîchis sont valables pour ces snapshots, mais le catalogue Limitless ne s'enrichit pas comme attendu, et le budget est épuisé sur les mêmes réponses.
- **R1 :** concevoir un état durable de découverte/rafraîchissement ou une stratégie explicite `--mode discover|refresh` et `--refresh-existing` qui fait avancer une session bornée sans perdre le rafraîchissement voulu d'anciens tournois. Tests synthétiques : 6+ IDs en page 1, exécution de budget 5 puis une autre → nouveaux IDs importés; plus de pages, doublons/insertion en tête, filtre tournois non admissibles, interruption/429/reprise, idempotence, version de snapshot corrigée sur demande. Éviter les curseurs naïfs invalidés par l'insertion de nouveaux événements : documenter les limites de pagination non atomique.

## DÉFAUT CONFIRMÉ 2 — interrogation prématurée de standings/pairings privés
**Code : `sync_meta` : les trois GET `details`, `standings`, `pairings` sont déclenchés AVANT la validation `details.isPublic`, `game`, `format`, `platform`, `isOnline` et état annulé.**
- En cas de tournoi privé/non listé, le code demande quand même deux jeux de données potentiellement sensibles, avant de les ignorer; il dépense au moins deux GET inutiles. Il en va de même d'un tournoi manifestement incompatible en format/plateforme.
- **R1 :** lire/valider `details`, décider immédiatement admissibilité, puis demander `standings/pairings` **uniquement pour les tournois publics et compatibles**. La liste peut être publique mais les détails peuvent annoncer `isPublic=false`; ne pas présumer l'admissibilité d'après le brief. Protéger la persistance existante (un ancien snapshot admissible ne doit pas devenir certifié à tort si le fournisseur le rend privé).

## RÉSERVES RÉSEAU à corriger dans le même petit R1
- `_SafeRedirectHandler.redirect_request` n'applique que `https` + hôte; un redirect vers `/api/games/PTCG/decks` serait suivi même si ce chemin est interdit aux appels directs; la validation de l'URL finale ne bloque que hors `/api/`. Appliquer la même allowlist **exacte des endpoints publics** aux destinations de redirects, sans récupération d'endpoint protégé.
- `LimitlessApiClient` récolte les en-têtes `RateLimit`, mais **ne s'arrête pas** lorsque leur restant déclaré est `0` sur une réponse réussie, continuant tant que le budget utilisateur n'est pas épuisé. `Retry-After` est exploité sur erreur; les quotas de succès doivent aussi être respectés sans inventer de politique fixe ou heure. Tests sur en-têtes conformes (et absents/malformés) : ne pas dépasser le quota annoncé; retour erreur/suspension bornée explicite et dernier cache valide conservé.
- Ces réserves sont confirmées par les conditions présentes dans le code, **pas** par une intrusion ou un véritable appel au chemin protégé.

## Métriques et limites à préserver
- `snapshot_status=complete` signifie trois réponses validées, **pas** tournoi terminé ou jeu compétitif exhaustif. Ne pas annoncer 9 vrais matchs de confrontation exploités : 0 archétype publié.
- `meta_matchups.excluded` compte toutes les exclusions des tournois filtrés, **pas spécifiquement celles de l'archetype demandé** : documentation ou libellé doit éviter cette ambiguïté (amélioration bornée possible si tests).
- Le filtre `isOnline` et la plateforme `PTCGL` sont distincts. Les statistiques n'établissent ni légalité officielle, ni rang mondial, ni winrate attendu du deck utilisateur.

## Décision suivante
**PM-0005B-R1 :** correctif de progression des imports, rejet anticipé des détails non publics et sécurisation des redirects/quota. Ne pas démarrer PM-0006 avant audit du correctif. Aucun merge, changement de branche par défaut, achat de crédits, action Pokémon ou planificateur Windows.
