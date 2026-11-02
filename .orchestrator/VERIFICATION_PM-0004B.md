# VERIFICATION_PM-0004B — audit indépendant ChatGPT (2026-10-11)

## Verdict
**CORRECTION CIBLÉE REQUISE avant de qualifier PM-0004B de VERIFIED.** L'architecture de synchronisation et de rafraîchissement a été publiée, mais un défaut confirmé par lecture statique contourne la protection « recheck absent explicite ». Ne pas démarrer PM-0005 ou le planificateur; ouvrir PM-0004B-R1.

## Références vérifiées directement sur GitHub
- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0004b-catalogue-refresh` au HEAD Codex `ccfa33d2ac38da6005610b66b7899d37e7ae77c8`.
- Base préparée par ChatGPT `92210840ffed4053cae338c320972a60eafe5c01`; deux commits Codex, 13 fichiers modifiés/ajoutés, dont `src/pokemind/cards.py`, `database.py`, `cli.py`, `tests/test_cards.py`, documentation et rapports.
- Code inspecté : rafraîchissement manuel à quatre scopes, reprise, pagination, curseurs, index de noms/détails, client HTTP et budget, migration SQLite 4→5 avec backup, priorité deck locale, métriques et tests ajoutés.
- Arbre Git complet : 103 entrées, `truncated=false`, aucun journal, screenshot, deck réel, base personnelle, backup ou cache local suivi. Aucun merge `main`.
- Aucun statut CI et aucun workflow associé au HEAD via les réponses GitHub. `89 passed`, les deux séries de 12 requêtes et l'intégrité SQLite sont **rapportés par Codex**, non réexécutés indépendamment par ChatGPT.

## Fonctions cohérentes à conserver
1. CLI `cards sync --phase index|details|balanced`, `--refresh-index`, `--recheck-absent`, `--prioritize-deck`; pas de tâche installée.
2. Migration v5, empreintes de résumés FR/EN et marquage des détails potentiellement périmés, état de rafraîchissement séparé de discovery et checkpoint transactionnel par page; pas de suppression basée sur l'absence dans une page.
3. Pagination triée par ID pour refresh, vérification par page vide après fin partielle et sondage de tête une fois lors de reprise. Limite admise : pagination non atomique sous mutations concurrentes, donc pas de garantie de découverte exhaustive lors d'un unique scan.
4. Budget réseau borné, HTTPS sur `api.tcgdex.net`, redirections/JSON/tailles/timeout contrôlés, retry 429/5xx, traitement des erreurs.
5. Metrics FR/EN et lecture locale/offline; code priorise uniquement IDs TCGdex de cartes déjà liées par code/numéro/nom à un deck confirmé; aucun contenu privé n'est ajouté aux paramètres HTTP.
6. Selon Codex : cache de 223 sets / 602 impressions / 973 traductions, 4 détails EN et 4 FR seulement; ni discovery ni refresh ni catalogue global complets. Base privée schéma 5 `ok`, quatre volumes/87 sections, 5 combats, deck 60 cartes inchangés.

## DÉFAUT CONFIRMÉ EN REVUE DE CODE — statut absent contourné
### Chaîne de reproduction logique
- Dans `src/pokemind/cards.py`, `_mark_missing_or_error(..., kind='cards', status='absent')` écrit `catalog_translations.status='absent'` après une réponse 404.
- Lors d'un scan ultérieur de l'index contenant le même ID, `_upsert_card_brief(...)` exécute `ON CONFLICT ... status=CASE WHEN catalog_translations.status='present' THEN 'present' ELSE 'not_fetched' END`. **Une traduction auparavant `absent` repasse donc à `not_fetched` sans `--recheck-absent`.**
- L'appel suivant `cards sync --phase details` utilise `_pending_card(..., recheck_absent=False)` et sélectionne la traduction désormais `not_fetched` : la 404 est redemandée malgré la politique explicite de recontrôle sur demande.
- Pour les sets, `_pending_set` sélectionne aussi un état `absent` quand le drapeau `detail_stale` devient 1 après changement d'un bref; pour les cartes, `_pending_card` a le même contournement par `OR p.detail_stale_{lang}=1`. Il faut établir une règle explicite de traitement des absences vérifiées, distincte des détails réellement périmés.
- Les tests `test_recheck_absent_is_explicit_and_does_not_loop` couvrent l'absence sans **rafraîchissement d'index intermédiaire**; ils ne prouvent donc pas que la propriété résiste au scénario d'usage PM-0004B.
- Gravité : **modérée**, n'efface pas le deck et ne perd pas les détails `present`, mais peut causer appels superflus/404 répétées, métriques changeantes, usage de budget et conclusions de présence trompeuses après rafraîchissement.

### Critère de correction minimale
Fixture synthétique : découvrir une carte → détail 404 → rafraîchir l'index (même nom et nom modifié) → `cards coverage` garde absent confirmé et `cards sync --phase details` avec recheck_absent faux émet **zéro** requête pour cet ID → `--recheck-absent` relit sur demande → si fournisseur renvoie maintenant 200, passe à present; idem pour le cas set / indicateur stale. Préserver les cartes `present` et les détails obsolètes à rafraîchir, ne pas neutraliser `detail_stale` dans les autres scénarios. Corriger uniquement avec tests et docs, sans synchronisation massive.

## Suite
Publier **PM-0004B-R1** sur branche corrective séparée, tests de régression et preuve d'un petit test de refresh offline simulé. Cette livraison ne constitue pas une autorisation de lancer Codex sans consigne utilisateur. PM-0005, légalités, méta et automatisation quotidienne demeurent ultérieures.
