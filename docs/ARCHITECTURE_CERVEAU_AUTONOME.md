# Mise à jour courante — assistant unifié livré / AWAITING_AUDIT

2026-10-27 Québec. Après lancement explicite, **une conversation** relie Codex App Server par défaut, actions projet Codex/Claude, import+question, reconstruction hypothétique60 et mémoire Web permanente dans le cerveau existant. [Utilisation et contrats](UNIFIED_ASSISTANT_IMPLEMENTATION.md), [preuves](../.orchestrator/EVIDENCE_PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md), [état](../.orchestrator/STATE.json).

Les mentions datées de conception non lancée, terminal séparé ou chat exclusivement en lecture seule ci-dessous sont historiques et supplantées par cette livraison. Le coach conserve ses permissions propres; le développement est sélectionné par demande utilisateur explicite dans le même fil. Cloud ordinaire autorisé et mémorisé, aucun brut de journal envoyé automatiquement. Aucune migration SQLite personnelle ni nouveau backup. **V1 NOT_RELEASE_READY; STOP audit indépendant.** Réception Windows rapportée par l'exécuteur, CI au SHA final limitée par le budget Actions, sans succès présumé.

---

# ARCHITECTURE — Cerveau PokeMind autonome, local, versionné (2026-10-10)

## Décision utilisateur / limites du périmètre

- **Une seule interface conversationnelle : Codex CLI, dans le dossier PokeMind sous Windows.** La connexion navigateur/ChatGPT, un serveur, un plugin distant ou une API vers les données privées sont expressément **reportés**. Ne pas les construire ni les proposer par défaut.
- Trois capacités finales obligatoires : **(A) savoir Pokémon vérifié et extensible**, **(B) mémoire personnelle qui se perfectionne par preuves**, **(C) actualisation automatique incrémentale, localement**.
- « Agent autonome » signifie : collecte publique planifiée, nettoyage, validation, versions, recherche, raisonnement et présentation **sur commande de l'utilisateur dans Codex**. Cela ne signifie ni surveillance du jeu, ni action dans le client, ni entraînement de poids de modèle, ni génération d'une réponse Codex en tâche de fond.
- Fondations déjà réalisées : Python 3.11+, SQLite FTS5, 4 tomes/87 sections; journals TCG Live et profil W/L, deck exact importé quand fourni, Skill `$combat`. Dernier résultat local anonymisé rapporté : n=5, 4W/1L, trois cartes faussement reconnues comme telles (non utilisables pour décisions); ne jamais compter 5 jeux comme preuve de tendance certaine.
- **Ne pas convertir cette architecture en une seule tâche géante.** PM-0003E actuellement autorisée demeure strictement le pont export de decks. Les tâches suivantes nécessitent un nouveau NEXT_PROMPT créé par ChatGPT, une branche par tâche, tests et audit indépendant. 

## Schéma logique

```text
SOURCES PUBLIQUES                         UTILISATEUR (local uniquement)
TCGdex  Pokémon officiels  Limitless        journaux  decks exportés  crédits  captures
   |          |              |                      |
   +----------+--------------+             import explicite/vision autorisée
                  |                                  |
       Collecteurs HTTPS minimaux            Parser/observations fiables
       validation schéma/licence                       |
                  |                                  |
     catalog / source snapshots           memory personnelle SQLite
                  |                                  |
                  +--------------+-------------------+
                                 |
                         SQLite FTS5 + index
                  provenance, dates, confiance, version
                                 |
                         Moteur de requête CLI
                     faits + recherche + contraintes
                                 |
                       Codex + Skills spécifiques
              $combat, $mon-deck, $meilleur-deck, $meta ...
                                 |
               réponse courte + preuve + fichier deck prêt
                     (aucun achat ni clic automatisé)
```

## A. Connaissance universelle — pipeline sourcé

### Classes de sources avec priorité
1. **Normatif** : Pokémon officiels — règles, errata, cartes interdites, rotation Standard/Expanded, prise d'effet Live vs tournoi, légalité et réimpressions, annonces du client. En cas de divergence avec un article communautaire, le document normatif prioritaire fait autorité.
2. **Données des cartes** : TCGdex v2 (FR et EN) — carte/impression, ID, set, numéro, texte, type, attaques/talents, noms alternatifs, marque de régulation lorsqu'elle existe. Les langues ont des niveaux de couverture différents; `unknown` est une valeur normale. TCGdex ne garantit PAS la légalité PTCGL, la disponibilité ni la fabrication des cartes.
3. **Résultats compétitifs** : Limitless Tournament Platform API — tournois, decklists, standings et pairings accessibles; contexte Standard/Expanded, en ligne vs présentiel, date, taille de tournoi et échantillon. L'endpoint `/games/{id}/decks` de catégorisation exige une clé ou une autorisation spécifique; **ne pas le solliciter sans autorisation**. Aucune clé Limitless nécessaire en principe pour les endpoints publics documentés, mais respecter les rate limits.
4. **Recherche secondaire** : Trainer Hill et autres analyses uniquement si usage explicitement permis par leurs conditions/documentation; forums/Reddit, vidéos, commentaires et listes non officielles servent d'indices, **jamais de vérité normative**. Mettre date et niveau de confiance, pas de scraping agressif/contournement.

### Enregistrement de chaque connaissance
Une observation publique normalisée comporte idéalement : `entity_id`, `kind`, `language`, `source_name`, `source_url`, `retrieved_at`, `published_at`, `effective_from/to`, `source_version/etag`, `sha256`, `license`, `confidence`, `status` (validé/incertain/retiré), `payload_version`. Conserver l'origine et la justification, pas les pages ou médias bruts par défaut.

- Alias FR ↔ EN liés par un identifiant de carte **et impression** stable, non par ressemblance textuelle seule.
- Rotation/légalité : **règle évaluée pour une date et un format**, pas simple booléen intemporel; reprints, exceptions, cartes interdites et délai de légalité doivent être testés.
- Tournois : total de parties, taille d'échantillon, critères d'inclusion, BO1/BO3, online/presentiel, dates et biais avant tout win rate.
- Détecter divergences entre sources, appliquer hiérarchie, conserver conflit non résolu comme `unknown` plutôt qu'une règle inventée.

## B. Mémoire personnelle évolutive (SQLite local)

Entités/relations à construire progressivement :
- `game` → `event` → `card_observation` (self/opponent/inconnu, provenance et confiance).
- `deck` → `deck_version` (exact confirmé 60 cartes ou partiel) → `game` seulement si association explicitement prouvée.
- `profile_snapshot` → statistiques affichées, crédits/cristaux distincts, date et confiance; images fournies à la demande converties en texte, jamais archivées par PokeMind.
- `candidate_recommendation` → sources publiques + cartes confirmées/inconnues + contraintes de crédits à date donnée.
- `hypothesis` → `evidence_games` → `status` proposé/testé/confirmé/infondé. Conserver comparaison avant/après et ne pas présenter l'hypothèse comme connaissance factuelle.
- `decision_review` → séquence d'actions observable / information cachée / alternatives conditionnelles / retour utilisateur.

Règles d'apprentissage :
- Chaque log nouveau est analysé localement, contrôlé contre doublons SHA et fausses cartes; **3 faux positifs historiques connus doivent être corrigés/neutralisés avant la construction automatique**.
- Ratio W/L et tendances : `n`, période, deck-version et adversaire connu; à `n=5` = découverte exploratoire; nouvelles données peuvent infirmer une hypothèse (ne pas accumuler de « leçons » fausses).
- **Une carte vue ≠ possédée; une carte non vue ≠ absente; un export de deck ≠ collection entière.** Solde/crédits issus de la dernière capture peuvent être périmés.
- Pas de journaux/images bruts permanents dans SQLite; fichiers sources enregistrés manuellement par l'utilisateur restent sous son contrôle, non supprimés sans consentement.
- Sauvegardes locales chiffrées et restauration testée, politiques de rétention/configurables et migrations réversibles sont des critères de finition, pas à inventer en PM-0003E.

## C. Autonomie : mises à jour sans Codex actif

### Cadence proposée (installation seulement après consentement)
- **Tous les jours, courte vérification** HTTP conditionnelle lorsque permis : nouveautés TCGdex (sets/cartes modifiés), publications officielles règles/errata, derniers tournois Limitless. La quotidienne ne doit pas recalculer *tout* le métagame ni télécharger toutes les cartes si rien n'a changé.
- **Deux fois/semaine, réconciliation approfondie** : ensembles/versions, nouveaux decks, méta roulante par fenêtre pertinente, anomalies de classification, contrôle qualité et rapport synthétique.
- **À la demande** : `pokemind knowledge update`, `knowledge status`, `knowledge diff`, `knowledge sources`, `knowledge rollback` (nom définitif à décider/tester), fonctionne offline pour status/recherche avec « dernières données au ».
- Windows Task Scheduler lance **un petit script Python déterministe**, pas Codex, pas LLM, pas de connexion au compte TCG Live, aucune capture ni lecture des journaux personnels. Installer la tâche seulement sur demande explicite de l'utilisateur. `install`, `status`, `disable/uninstall`, journaux d'exécution redigés.
- Transactions atomiques/idempotentes : importer dans tables de staging, vérifier structure, valider champs clés/volumes/signatures/compteurs/limites et déplacer seulement données validées; si réseau indisponible, 429, données corrompues ou changement majeur de schéma => rollback, conserver dernière bonne connaissance, signaler échec.
- HTTP : User-Agent descriptif, HTTPS seulement, timeouts, backoff exponentiel, `Retry-After`, ETag/If-Modified-Since quand supporté, limite de pages et budgets d'appels, `304` = aucun changement, pas de contournement des limites.
- Indicateurs : fraîcheur par source, dernière réussite/échec, nombre d'objets ajoutés/modifiés/retirés, pourcentage de couverture FR/EN, anomalies de validation, durée, taille stockage, résultat du test offline; préservation du dernier état valide.

### Bornes opérationnelles
- Aucun composant principal ne dépend d'une connexion permanente à Internet. Les recherches utilisent cache local + références datées.
- GitHub versionne **code, règles de collecte et docs**, pas la base personnelle, les journaux, captures, secrets, ni snapshots contenant des informations utilisateur. Des connaissances publiques sous forme de résumés non personnels peuvent être versionnées si licence/autorisations le permettent; sinon cache local.
- Séparer documentation à long terme de `AGENTS.md` concis et des Skills à activation à la demande pour ne pas saturer le contexte Codex.
- **Zéro achat/fabrication automatique** : le joueur choisit « Exchange All » dans TCG Live et vérifie le coût; PokeMind propose des decks avec coût estimé seulement si les chiffres de fabrication sont vérifiés et actuels.
- Pas de surveillance de partie ou avantage déloyal. Coach visuel seulement en entraînement/jeu autorisé et sans inférence d'information cachée.

## D. Interface Codex et trajectoire de livraison

Conserver Codex **unique** et les commandes courtes. Les Skills sont des procédures et ne doivent pas reproduire toutes les données du catalogue dans le contexte. Utiliser CLI `--json` + SQLite FTS5. Exemples **futurs**, pas des capacités existantes :
- `$combat` : import du journal → résumé + W/L + observations corroborées.
- `$mon-deck` : état d'une version 60 cartes et des cartes observées.
- `$meilleur-deck` : proposer 3 options sourcées (performance méta, couverture observée et coût **si connue**), exporter le fichier .txt importable, séparer absent vs inconnu.
- `$meta` : état actuel/à date avec fraîcheur et qualité de l'échantillon.
- `$apprendre` : vérification/actualisation à la demande, afficher statut par source.
- `$coach` : captures temporaires lors d'entraînements autorisés.

Un seul moteur de données partagé; pas six sous-agents autonomes séparés. L'agent peut décider **quels outils consulter** pour la demande, mais jamais faire une dépense ou modifier le jeu sans utilisateur.

## E. Critères d'acceptation transversaux

1. Jeu de tests anonymes sur événements, cartes FR/EN, versions, rotation, réimpressions, limites Standard/Expanded, nouveaux sets et descriptions manquantes.
2. Simulations HTTP : aucun changement/304, nouvelle carte, erratum officiel, données incohérentes, quota 429, timeout, panne partielle, corruption de cache, rollback, double exécution.
3. Retour au mode hors ligne après mise à jour, conservation DB personnelle et tous les journaux, absence de fuite GitHub.
4. Recommandations cite sources et dates, échantillons, inconnues, légalité à date et séparation pratique/méta/collecte.
5. Démonstration d'une mise à jour réelle suivie d'une mise à jour idempotente, puis test Windows planifié **uniquement après autorisation**.
6. Bilan local quotidien succinct, sans envoi réseau de statistiques privées.

Cette architecture est **la cible**, non la liste des fonctions déjà livrées. Lire ROADMAP pour les tranches, `SOURCES_CONNAISSANCES.md` pour les connecteurs et leurs restrictions.
