# PM-V1-PLAYABLE-DECK-REVIEW-001 — Jouer réellement : deck existant, journaux, listes importables

**Statut READY pour relais manuel propriétaire dans Codex Windows uniquement.** Cette tâche est un **premier usage personnel en lecture seule**, PAS un déblocage du `RELEASE_READY`. Objectif concret : évaluer un deck déjà enregistré, résumer les parties déjà présentes et produire au moins une proposition de liste de 60 cartes au format de presse-papiers Pokémon TCG Live, si les sources disponibles permettent de la justifier.

## A — Prévol et droits (aucun effet local implicite)

1. Sur la branche `work/pm-v1-lotj-final-readiness-windows` : `git status` et synchronisation fetch/pull --ff-only sans écraser; lire AGENTS, SESSION_CONTINUITY, adoption V2, STATE, **premier** NEXT_ACTION, HANDOFF/RESULT, AUTONOMY_POLICY, skill github-executor et présent mandat.
2. Contrôler ID unique READY, `execute_now=true`, `consumed=false`, branche et permissions. GitHub Actions Windows + Ubuntu **`completed/success` au SHA HEAD exact actuel**; si queued/in_progress → WAIT_CI_NO_FUNCTIONAL_WORK, 25min max/sondages ≥30s, sans travail fonctionnel; échec/timeout/HEAD divergent → STOP assaini.
3. L'acte du propriétaire de **transmettre manuellement ce nouveau prompt à Codex** constitue le déclenchement ciblé : **lecture seule** des fichiers texte réguliers directement sous `data/local/battle_logs` du dépôt Windows et du **deck existant `principal`** via l'emplacement normal de DB dans `data/local`, seulement si un chemin DB explicite et reconnu peut être établi sans explorer d'autres données privées. Aucune recherche de fichiers dans le reste du lecteur/disque, ni récursion, lien symbolique/reparse, dossier inconnu, ancienne sauvegarde ou clone. Si le deck actif n'est pas `principal`, ne pas deviner et indiquer le blocage sans scanner des DB alternatives. Ne jamais enregistrer le contenu privé dans Git, prompts GitHub, CI ou API externe.
4. **Aucun import, réanalyse `--reparse`, update, création de clone, backup, migration, écriture SQLite, `--apply`, accès au client Live, OCR, installation, planificateur ou collecte HTTP** dans cette tâche. Prévol/lecture seule et analyse in-memory. Si une commande inspectée n'est pas strictement lecture seule, ne pas la lancer.

## B — Deck actuel : audit utile

- Vérifier la commande existante `deck show` et les fonctions `decks.show_deck`, `deck export`, `analyze deck`/résolution en mode **lecture seule** avant leur appel; privilégier lecture explicite contrôlée de la base, jamais un comportement créant/migrant implicitement.
- Vérifier si le deck `principal` possède une version `exact_confirmed` de **60 cartes**. Relever ses catégories et quantités; détecter doublons, ratios, main de départ, conditions de victoire, moteur d'énergie, draw/search, sorties, difficultés probables. Vérifier identifiants par le catalogue local seulement; **carte inconnue = inconnue**, ne pas en fabriquer un code de set.
- Conserver toutes ces conclusions et la liste réelle exclusivement **dans la réponse locale Codex**, pas dans un rapport GitHub.

## C — Parties déjà enregistrées : audit sans réimport

- Répertoire exact de travail **`data/local/battle_logs`**, déjà nommé par le propriétaire. Uniquement fichiers réguliers directement contenus de type `.txt` ou `.log`, sans récursion, maximum **100 fichiers** (ordre déterministe), maximum2MiB/fichier et20MiB cumulés; si dépassés, analyser l'échantillon permis et dire combien restent non lus **localement**.
- Réutiliser le parseur existant **en mémoire** : aucun `log import` (écrit), aucun `--reparse` ni modification de la DB. Dédupliquer les parties observables par hash **seulement en mémoire**, reconnaître W/L/unknown, attribution du joueur et deck uniquement si prouvée. Si la DB active contient déjà des combats/profils et que les commandes correspondantes sont bien lecture seule, utiliser uniquement la vue du deck `principal`, sans regrouper implicitement toutes les parties des fichiers avec lui.
- Produire **dans Codex** un bilan clair : n valides, W/L/inconnus, matchups attestés, cartes et erreurs/situations répétées, suggestions appuyées par une preuve de log; incertitudes explicites si une cause ou version de deck n'est pas observable. Ne pas inventer les cartes cachées ni les causalités.

## D — Propositions concrètes prêtes à jouer

- Comparer au **métagame et aux règles déjà présents localement** avec dates, sources et fenêtres d'échantillonnage. Aucun GET nouveau dans ce lot. Si les preuves récentes ou officielles sont absentes, indiquer précisément que la recommandation est **provisoire**, légalité Standard/Live `UNKNOWN`; ne jamais déclarer « le meilleur deck actuel du monde » sans preuves.
- Priorité à **UNE version améliorée du deck principal**, et jusqu'à **DEUX autres archétypes** quand une liste de 60 cartes exacte peut être fondée; sinon fournir seulement les versions justifiées, sans inventer les identifiants. Ne pas supposer la collection et les crédits, ni simuler un achat.
- Chaque deck effectivement proposé : **exactement 60**, texte **dans le format d'import Pokémon TCG Live** dans un bloc facile à copier depuis Codex, avec un bilan des changements, justification et limites. Valider la structure avec le parseur/exporteur existant **en mémoire**, sans créer une version dans la vraie DB, sans clipboard Windows automatique et sans commande au client Live.

## E — Livraison et STOP

**Livrable principal : réponse détaillée privée dans la session Codex** comprenant résumé de parties, diagnostic deck et liste(s) de60 cartes copiables, ou un blocage exact si les éléments sont insuffisants. Aucun rapport privé ne doit transiter dans GitHub, GitHub Actions, les commits, une issue, ni le clavardage ChatGPT. Aucune métadonnée identifiante, deck, carte personnelle, filename privé, hash de fichier personnel, chemin absolu ou contenu du joueur dans la preuve publique.

Publier **uniquement** un état assaini (ex. `PRIVATE_READ_ONLY_REVIEW_DONE`, `PARTIAL_WITH_REASON`, nombre de propositions diffusées **sans leurs contenus** et limites de source génériques), plus les documents STATE/RESULT/HANDOFF/NEXT_ACTION cohérents `AWAITING_AUDIT` et permission consommée. Tests ciblés **sans données privées**, compilation/hygiène seulement si code versionné changé (aucune modification produit prévue); commit/push docs non sensibles sur branche autorisée; CI exacte; STOP audit indépendant. Aucun nouveau mandat par l'exécuteur.

**Rappels :** Le STOP de `PM-V1-REST-FR-EN-COVERAGE-001` n'autorise aucune nouvelle requête TCGdex, même pour les 129 GET inutilisés. Données personnelles seulement dans les limites explicites ci-dessus et **uniquement au relais manuel**. Aucune certification totale V1; `NOT_RELEASE_READY`.
