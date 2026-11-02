# LIVRAISON — AWAITING_AUDIT / STOP

2026-10-27 Québec. Le lancement unique du propriétaire a été exécuté : intégration A–G livrée, preuves Windows CODEX_LOCAL_REPORTED et CI AWAITING_EVIDENCE pour budget Actions. execute_now=false, consumed=true; aucune relance automatique. [Résultat](../RESULT.md), [preuves](../EVIDENCE_PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md). **V1 NOT_RELEASE_READY.** Le lancement puis le brouillon ci-dessous sont historiques.

---

# LANCEMENT AUTORISÉ — IN_PROGRESS

Le propriétaire a explicitement validé et déclenché ce mandat dans la session du 2026-10-26 Québec. La portée A–G ci-dessous est active; les mentions de brouillon sont historiques. execute_now=true, consumed=true pour ce lancement, pas de redémarrage automatique. STOP audit indépendant après livraison.

---

# PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001 — mandat majeur proposé

**DRAFT_AWAITING_OWNER_START — execute_now=false — aucune exécution autorisée par ce fichier.**
Branche exclusive : `work/pm-v1-lotj-final-readiness-windows`.
Conception : [UNIFIED_POKEMIND_ASSISTANT_DESIGN](../../docs/UNIFIED_POKEMIND_ASSISTANT_DESIGN.md).
Point de départ audité : [revue de reprise](../VERIFICATION_PM_V1_UNIFIED_ASSISTANT_REPRISE.md), HEAD `693750ce63cc81330c171537c0e75b8866b5c31e`.
Ce mandat remplace fonctionnellement l'ancienne proposition ConPTY à deux conversations, **annulée**.

## Déclenchement et résultat attendu
Une validation explicite du propriétaire du lancement de **ce mandat** permettra à l'orchestrateur de le rendre READY dans STATE/NEXT_ACTION/NEXT_PROMPT. Ensuite, lancement manuel de l'exécuteur. La seule présence du brouillon ou d'un nouveau commit n'est jamais un déclencheur.

Après lancement, l'exécuteur réalise A–G et leurs corrections dans un cycle cohérent, sans approbation par fichier, puis publie et STOP pour audit indépendant. Garder les points internes de reprise dans GitHub. Livrer une application Windows utilisable, avec **une chronologie PokeMind et une boîte de saisie**, six écrans conservés, Codex par défaut, actions réelles et mémoire durable. Aucun moteur métier ni cerveau reconstruit.

## Portée proposée pour ce lancement unique (inactive avant accord)
- Modifier code/tests/docs/scripts du dépôt et les dépendances nécessaires **dans l'environnement projet**; conserver Python/SQLite/FTS5/PySide6. Compilations et build portable, tests et QA GUI native sur Windows; Ubuntu existant seulement en non-régression.
- Réutiliser les comptes/authentifications Codex et Claude existants pour QA sur contenu public ou inventé; aucun secret copié ni nouvelle clé payante supposée. Ollama seulement si déjà disponible, sans téléchargement silencieux.
- Pour valider les références locales réelles **après lancement**, consultation en lecture seule de `data/local/pokemind.sqlite3` et `data/local/battle_logs`, rapports dérivés/Learning Loop sous `data/local/battle-intelligence`, et des caches PUBLIC fixes déjà nommés dans les constantes des moteurs. Vérifier les chemins exacts et redirections avant lecture; pas de scan des autres fichiers/dossiers privés. Si SQLite7, ouverture strictement observationnelle, aucun appel qui initialise/migre/écrit la base. Les statistiques historiques sont à revalider localement avant tout affichage comme chiffres actuels et ne vont pas dans GitHub.
- Écritures dérivées nécessaires via moteurs existants sous `data/local/battle-intelligence`, préférences/historique UI sous `data/local/chat` et caches publics/illustrations déjà prévus. Conserver les versions/snapshots originaux. Imports **nouveaux** de QA dans corpus inventé isolé seulement; les vrais nouveaux journaux seront fournis/sélectionnés explicitement par le propriétaire dans l'UI.
- Réseau public demandé par ce mandat pour qualifier un cycle de collecte et sa persistance : plafond conservateur **150 GET / 32 Mio cumulés / 2 Mio par réponse**, ou borne fournisseur plus stricte. Réutiliser les limiteurs existants; source et période explicites; respecter refus, robots/conditions/licence, 429 et Retry-After. Arrêt n'est pas permission de rouvrir une campagne historique, réinitialiser un budget ou contourner une source bloquée. Les futures recherches utilisateur ont un budget visible propre, pas de surveillance externe.
- Commit/push du code et des preuves **assainies** sur cette branche, contrôle du SHA final/CI, sans merge main, force-push, reset destructif ni publication de données locales.
- **Toujours interdits** : nouvelle sauvegarde, clone/migration7→13, restauration/purge/suppression d'originaux, modification ACL/chiffrement, installation globale/élévation, scheduler/hook/daemon/watch GitHub, facturation/achats/échange de crédits, contrôle du client TCG Live, données privées vers GitHub ou logs bruts automatiquement vers cloud. Les préférences de refresh dans l'application ouverte restent utilisables.

## A — Baseline, capacités réelles et plan interne
Lire les règles/continuité/STATE/mandat, contrôler absence de divergence et synchroniser ff-only sans perte. Confirmer le HEAD courant. Exécuter préflight/démo et tests sur fixtures sans DB implicite. Le run40441594259 n'a pas démarré : **budget Actions bloquant**; ne pas changer la facturation, masquer les jobs ou prétendre verte la CI d'un autre SHA. Si ce seul blocage externe persiste après lancement, les travaux et preuves locales autorisés peuvent progresser; la réception CI reste AWAITING_EVIDENCE.

Qualifier la version Codex installée et ses schémas officiels sans lire les secrets. Écrire une matrice méthode/capacité/version et ses replis explicites. Revoir la documentation officielle actuelle avant adaptation; aucun nouveau terminal TUI/ConPTY requis par défaut. `dynamicTools` est expérimental : valider le contrat/réponses et refuser honnêtement une capacité non supportée, plutôt que simuler un outil. Aucun changement silencieux de CLI global.

## B — Une conversation, orchestration et outils réels
Étendre les adaptateurs, `desktop/services`, le store et la fenêtre existants; un composant d'orchestration léger peut relier les APIs présentes. Aucun framework d'agents, moteur vectoriel ou deuxième base de connaissances.

Distinguer intention utilisateur, données du journal et sorties d'outils. Outils structurés, arguments validés, références de partie/deck explicites; sélectionner uniquement les faits utiles au contexte. Les journaux/pages/PDF restent du contenu non fiable. Une demande peut enchaîner import, observation, recherche, persistance et réponse dans le même fil avec annulation aux frontières sûres et reçu des opérations accomplies.

Exposer les services de combats/événements/learning, versions/collection, cartes/légalité, méta/matchups, candidats/export60 et refresh public. Réutiliser les fonctions métier; pas de SQL arbitraire ni de chemins fournis par un document externe. Afficher les erreurs réelles sans transformer échec en succès.

Activer les outils de fichiers/tests/Git Codex et Claude pour une demande de développement du propriétaire, avec événements de commandes, changements et résultats dans **la même discussion**. Le réglage de permissions utilise les capacités officielles de la version, un répertoire projet choisi dans la racine et les droits réels Windows. Le mode complet type `--yolo` est volontaire, persistant et clairement visible; il n'est jamais activé pour la QA sur données réelles. Ne pas retirer globalement les protections du conseil Pokémon pour obtenir l'édition de fichiers. Le mode choisi ne doit jamais modifier les autorisations de cette session d'orchestration.

Conserver le fil PokeMind lors d'un changement de fournisseur; lier les sous-sessions par fournisseur et marquer la provenance. Ne pas reprendre un thread privé non admissible ni retransmettre tout l'historique. Redémarrage, reprise, annulation et changement de permissions ne perdent pas la conversation et n'élargissent pas silencieusement les accès.

L'usage cloud ordinaire Codex/Claude est déjà autorisé : mémoriser cette préférence sans confirmations répétées, conserver les choix utilisateur plus restrictifs et distinguer le partage d'agrégats/extraits anonymisés. Les flux automatiques excluent brut/identités/secrets. Un mode shell réellement illimité ne fournit pas à lui seul une garantie d'exclusion de fichiers privés : présenter sa portée réelle et appliquer les barrières techniques disponibles, sans fausse promesse de confidentialité absolue.

Intercepter `/status` **avant le routage Pokémon** : account/read et rateLimits/read, usage/read si disponible; état/auth sans secret, modèle et session si exposés, fenêtres/quota/reset, utilisation et contexte séparés. Null/absence/non-support restent indisponibles. `/resume`, `/compact` et autres commandes uniquement avec correspondance officielle réelle; jamais recopier un écran TUI ou demander au LLM d'inventer les chiffres.

## C — Journal et question en une interaction
Conserver parseur FR/EN, publication exclusive atomique, doublons exacts/sémantiques, limites, attachements/drop et pont legacy. **Démontrer le manque avant toute réécriture**. Gérer un journal entouré/suivi d'une demande en séparant localement le bloc reconnu et l'intention, puis importer et répondre automatiquement sur cette partie (y compris doublon). Si frontière ambiguë, demander seulement le minimum sans envoyer le collage brut.

L'UI confirme ajouté/doublon/incomplet/analyse en attente selon les écritures réelles. Rafraîchir combats/statistiques/Learning Loop via les moteurs existants; aucun faux incrément après annulation ou erreur, aucun écrasement. Source et événements du journal demeurent consultables localement, contexte IA borné/anonymisé selon préférence. Exemple obligatoire : « [journal] Pourquoi j'ai perdu? Reconstruis son deck et compare au mien. » en un envoi.

## D — Reconstruction adverse et comparaisons compétitives
Étendre `opponent_observer`, `deck_library`, `competitive`, `counter_deck`, analytics et version_evidence. Classer **1 à 3 listes complètes publiées compatibles ou variantes justifiées**, selon cartes réellement vues, quantités minimales prouvées, identités FR/EN, signatures, format/date/rotation et fraîcheur. Donner sources, couverture, contradictions et limites; un score de similarité n'est pas une probabilité calibrée. S'il n'existe aucune liste compatible, le dire; pas de faux60.

Chaque proposition affiche observé / probable / non confirmé, total60 et statut **RECONSTRUCTION/HYPOTHÈSE**. Inconnues de texte/impression/légalité/Live ne sont pas comblées par un nom approchant. Permettre correction/annotation datée et révocable sans transformer une hypothèse en observation.

Comparer au deck/version réellement attestés; sinon dernière version connue clairement non attestée. Collection/crédits inconnus sans données déclarées. Réutiliser les exports validés60 et la légalité datée; un candidat demeure distinct du deck joué. Distinguer pairings publics avec n/fenêtre/format/BO1-BO3/plateforme et incertitude, placements/popularité et corpus personnel biaisé. Réutiliser `meta_matchups`/Wilson existants; **données insuffisantes** si provenance/classement/sample inadéquats. Aucun winrate ni causalité inventé.

## E — Recherche utile → mémoire durable dans le cerveau existant
Avant réseau, interroger les connaissances locales et leur fraîcheur selon la nature du fait. Raccorder le refresh conversationnel aux modules `cards/meta/rules/updates/batch_public_research/learning_loop` et aux stores déjà présents; ne pas rouvrir une enveloppe historique. Les recherches ne contiennent ni noms de joueur, brut de logs, deck personnel complet ni statistiques privées.

Pour toute donnée utile collectée : normaliser, valider source et schéma, extraire les faits admissibles, conserver source_url/éditeur, dates consultation/publication/effet, langue, format, version/ETag/empreinte, licence, statut et n si pertinent. Réponse du LLM seule n'est pas une source. Conflits et hypothèses restent explicitement conflict/unknown/hypothesis.

Conserver transactionnellement/idempotemment dans les tables/caches/journaux existants; créer seulement les champs/adaptations démontrés manquants dans le stockage PUBLIC, jamais migrer SQLite personnelle. Les versions antérieures restent consultables; supersession/révocation au lieu d'effacement silencieux. Distinguer métadonnées d'observation, fait validé et hypothèse. Les upserts sans historique ne satisfont pas cette exigence.

Retourner un reçu vérifiable d'écriture : faits ajoutés, révisés, déjà connus, rejetés/non vérifiés et sources effectivement consultées. L'UI ne dit « mémorisé » **qu'après succès**. Panne/annulation/429 conserve dernier état valide, indique ce qui a été enregistré et n'affirme aucun succès complet. Réponse suivante après redémarrage et hors ligne retrouve les faits; cache frais évite de répéter les GET.

## F — Finition de l'application existante
Une saisie accessible des six pages; même fil et contexte de sélection. Conserver Enter/Shift+Enter, progression réelle/animation/temps écoulé/Stop, galerie/images/zoom/source/cache, Deck Lab60, graphiques et choix FR par défaut/EN disponible. Aucun bouton factice. Les options de refresh au démarrage fonctionnent dans l'application, selon préférence, sans scheduler externe.

Intégrer dans cette saisie les amorces : dernier combat; deck adverse; défaites contre Dragapult; erreurs récurrentes; comparaison aux listes actuelles; trois modifications; deck selon collection; export60; entraînement Banc/Énergies; recherche méta mémorisée; prochaine amélioration PokeMind; statut Codex. Adapter aux données disponibles, garder les inconnues. Une amorce ne lance ni seconde conversation ni opération privée sans l'intention utilisateur.

## G — Réception, preuves et livraison
Tests significatifs sur les nouveaux comportements et les risques modifiés; conserver les régressions existantes. Pas de compte de tests cible ni multiplication de tests miroirs.

| Parcours de réception | Preuve requise |
|---|---|
| Journal FR/EN + question + reconstruction/comparaison en un envoi | Enchaînement réel, bonne référence de partie, aucun brut dans prompt/historique fournisseur. |
| Doublon exact/sémantique, incomplet, concaténé, volumineux, concurrence, panne | Aucun compte indu, original conservé, reprise et statut fidèles. |
| Codex par défaut, Claude/Ollama alternatifs | Streaming/reprise/annulation; absence fournisseur honnête; fil UI conservé au changement. |
| /status | Appels RPC réellement supportés; quota vs activité; champ absent sans chiffre inventé. |
| Demande « corrige un fichier puis teste » | Modification et test réels dans workspace inventé réversible, résultats/approbations dans le même fil. Mode complet vérifié sans l'activer sur privé. |
| Reconstruction60 et version jouée | Variantes classées, incompatibilité/minima, FR/EN, source/date, unknown et version non attestée conservés. |
| Statistiques compétitives | Pairings admissibles et n; placements seuls ou faible qualité → données insuffisantes. |
| Mémoire Web | Une source factice consultée, fait enregistré, processus fermé/rouvert, réponse offline, 0 GET répété si frais. |
| Révision/mémoire en échec | Réimport identique sans doublon; nouvelle version sans perte de l'ancienne; conflit/429/timeout/panne et reçu correct. |
| Données locales et séparation public/privé | SQLite7 non modifiée/migrée, aucun nouveau backup, zéro brut/secret dans Git ou projection publique. |
| UI Windows/portable | Vraie fenêtre interactive et EXE recompilé, six écrans, boutons, presse-papiers60, cartes, arrêt/reprise et historique. |
| Collecte publique réelle bornée | Sources effectivement accessibles, persistance puis seconde lecture offline; absence de statistique/source accessible explicitement rapportée. |

QA terrain sur corpus inventé et données publiques d'abord, puis consultation locale bornée autorisée par le lancement; ne pas injecter de fausses parties dans le corpus propriétaire. Les nouvelles parties réelles passent seulement par collage/sélection du propriétaire. Garder captures/logs privés localement; rapports GitHub assainis distinguent CODEX_LOCAL_REPORTED de preuves CI.

Exécuter tests ciblés puis suites complètes appropriées, compilation, hygiène, diffcheck, build et QA native. Épingler les nouvelles dépendances justifiées et conserver les licences. GitHub Actions : SHA final exact Windows + Ubuntu héritée, neuf marqueurs existants et empreintes canoniques; si budget empêche le lancement, **BLOCKED_EXTERNAL_CI_BUDGET / AWAITING_EVIDENCE**, aucune CI verte ni V1 prête prétendue. Ne pas multiplier les pushes/relances pour contourner le budget.

Publier RESULT/HANDOFF/NEXT_ACTION/STATE cohérents, décisions et preuves, puis vérifier HEAD distant/CI et **STOP audit indépendant ChatGPT**. Aucun auto-VERIFIED. Les portes V1 historiques (OCR, opérations de récupération, activation planifiée, couverture normative/Live, etc.) restent ouvertes selon leurs preuves; ce mandat ne les supprime pas et n'autorise pas leurs opérations privées.
