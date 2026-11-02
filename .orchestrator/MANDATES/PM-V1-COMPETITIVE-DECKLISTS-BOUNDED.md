# PM-V1-COMPETITIVE-DECKLISTS-BOUNDED — EXÉCUTÉ / AWAITING_AUDIT

**Clôture Codex2026-10-22 :lot exécuté,autorisation consommée,aucune reprise réseau.**
Voir `../EVIDENCE_PM-V1-COMPETITIVE-DECKLISTS-BOUNDED.md`,STATE et premier NEXT_ACTION.
Prochain geste :audit indépendant ChatGPT;V1 NOT_RELEASE_READY.

## Mandat autorisé initial, conservé pour audit

**Ordre explicite du propriétaire, 2026-10-22 : autoriser cette tâche et avancer maintenant.** Statut READY, exécution autorisée pour **un lot complet**, sans demander de nouveau « go » entre les sous-tâches. Exécuteur : Codex ou Claude Code sur le PC, démarré manuellement. V1 NOT_RELEASE_READY.

## Résultat attendu

Réutiliser l'architecture PokeMind existante. Collecter des listes **publiées et complètes de 60 cartes** de **1 à 3 tournois Standard récents** (jusqu'au 2026-10-22); objectif **15 à 45 listes variées si disponibles**, notamment Dragapult ex et au moins deux autres archétypes. Préférer des pages individuelles et une pagination publique documentée plutôt qu'un endpoint énorme. Vérifier URL, date, événement, format, plateforme, placement, liste 60/60, provenance et limitations. Ne pas inventer de statistiques, de légalités ou de listes manquantes.

Intégrer dans le **cache PUBLIC local seulement**, pas dans la DB privée. Conserver les données téléchargées et les listes complètes hors Git. Réaliser une consultation hors ligne et une comparaison concrète, sourcée et datée de Dragapult ex contre d'autres stratégies, avec des listes utilisables via le chemin d'export déjà validé historiquement. Ne pas refaire le test de presse-papiers de Pokémon TCG Live.

## Nouveau budget borné pour ce lot

Maximum **100 requêtes GET**, **64 MiB** au total, **2 MiB par réponse**, **40 opérations de découverte**, **1 seconde minimum par fournisseur**, **une tentative par URL**. Qualifier conditions d'utilisation et robots avant collecte; arrêter le fournisseur sur 401, 403, 429, challenge, protection ou refus. Ne jamais contourner une protection ou reprendre la campagne Limitless précédente arrêtée à 8 MiB. Les autres sources publiques indépendantes peuvent être étudiées avec leurs propres conditions. Aucune API privée, clé, compte, achat ni scraping agressif.

## Exclusions et livraison

Ne lire ni modifier decks, collection, journaux, base personnelle, OCR, captures, client du jeu, planificateur Windows, système, sauvegardes. Aucun merge, force-push, reset destructif, suppression ou installation de service. Aucun fichier personnel, deck brut ou réponse fournisseur dans GitHub.

Au démarrage, lire AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE et le premier NEXT_ACTION; vérifier branche, arbre, synchroniser sans perte, puis CI du HEAD actuel. Ne pas lancer de collecte si la CI préalable échoue; attendre son succès si elle est en cours.

Exécuter toutes les étapes autorisées de manière autonome; résoudre les erreurs techniques ordinaires sans nouvelle demande. Si une source est bloquée, livrer les autres tâches possibles avec limites explicites. Terminer par code/tests, preuves et rapport assainis dans RESULT/HANDOFF/STATE/NEXT_ACTION et documents utiles, commit sur la branche autorisée, vérifier les CI au SHA exact et **AWAITING_AUDIT / STOP**. La prochaine validation indépendante revient à ChatGPT.
