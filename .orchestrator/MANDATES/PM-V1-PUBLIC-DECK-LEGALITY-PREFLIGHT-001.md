# PM-V1-PUBLIC-DECK-LEGALITY-PREFLIGHT-001 — AWAITING_AUDIT / EXÉCUTÉ

Lot exécuté par Codex, permission consommée; STOP audit indépendant ChatGPT.
Voir RESULT/HANDOFF/STATE et les preuves du même ID. Le contrat initial ci-dessous
est conservé pour audit et ne constitue plus un ordre de relance.

## Contrat initial, historique

**2026-10-22 Québec.** Suite ordinaire **PUBLIQUE et hors ligne** autorisée par la décision durable D-196 du propriétaire : poursuivre la V1 par lots utiles sans redemander un « go ». **Statut READY, `execute_now=true`, une exécution manuelle du lot entier par Codex ou Claude Code.** Ce document n'installe ni watcher ni scheduler. V1 `NOT_RELEASE_READY`.

## Objectif produit mesurable
Après l'inventaire/comparaison de 28 compositions, produire un **prévol factuel des listes de60 cartes** recommandé par le conseiller, en liant le cache des listes de tournoi PUBLIC et les sources **PUBLIQUES préexistantes** des cartes/règles. Le joueur doit savoir **ce qui est attesté, ce qui n'est pas légal, et surtout ce qui reste inconnu** avant d'envisager un import TCG Live. Zéro approbation intermédiaire pour correctifs ordinaires **dans cette portée**.

## Prévol
Vérifier `git status`/branche, fetch + pull `ff-only` sans perte; lire AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, premier NEXT_ACTION, STATE, HANDOFF, RESULT, skill exécuteur, règles/candidates/competitive et ce mandat. La CI du nouveau HEAD qui porte ce mandat doit être `completed/success` sur Windows/Ubuntu avant toute opération fonctionnelle; attente bornée sans contournement. Ne pas utiliser la CI historique comme preuve du nouveau HEAD.

## Lot fonctionnel complet
1. **Réutiliser le code existant**, notamment `competitive.py` et ses sélecteurs/exports, `rules.py` (`check_card`, structures, statuts) et les mécanismes de résolution TCGdex PUBLIC. Inspecter les contraintes de schéma et d'identités avant tout nouveau code. N'introduire aucune dépendance, base dupliquée, framework ou interface inutile.
2. Concevoir une commande CLI simple, avec arguments explicites pour la **base compétitive PUBLIC** et la **base de référence PUBLIC** si différentes, `--as-of`, `--format standard`, `--platform in_person|live`, et sélecteur ou liste de références; **aucun fallback vers la DB privée**. Si les bases réelles sont séparées, lire en mode `ro/query_only`; ne pas les fusionner ni copier des enregistrements. Ne pas créer/migrer une base existante. Une absence d'une des bases PUBLIC doit produire une erreur neutre explicite et une piste de preuve manquante, pas un téléchargement.
3. Pour **2 à 4 compositions recommandées** (Dragapult, Basic Box et autres disponibles), restituer un rapport **date + source par affirmation** : total 60, quotas/structure connus, identités cartes résolues ou ambiguës, marque de régulation, preuve de réimpression, texte/errata et date d'effet quand attestés par registre déjà intégré. Distinguer `legal`, `not_legal`, `unknown` au **niveau impression ET deck**, inclure dénominateurs et codes de raisons. Un verdict sur échantillon synthétique ne certifie pas une impression réelle; une liste publiée en tournoi ne prouve pas une disponibilité TCG Live.
4. Être **fail closed** : aucune règle absente « remplie » par supposition; ne jamais convertir une absence de bannissements ou la rotation H/I/J en légalité totale; `Live availability`, collection, crédits, craftability et matchups `unknown` sans preuve spécifique. Le prévol n'a pas besoin de prétendre `legal` pour apporter de la valeur : afficher exactement les pièces bloquantes et les vérifications futures.
5. Créer un résumé pratique humain/JSON **court, lisible**, comparant les quatre options, avec renvoi aux exports déjà existants sans modifier le deck joué, le presse-papiers, le jeu ou les fichiers du cache. Un résultat `PARTIAL_WITH_EVIDENCE` est acceptable avec les inconnues quantifiées. Aucun « meilleur deck » inventé.
6. Ajouter des tests **entièrement synthétiques** sur bases PUBLIC isolées, références valides/invalides, dates/plateformes, réimpression, règle incomplète, provenance, 60 cartes, lecture seule, zéro réseau, et refus de fallback personnel. CI Windows et Ubuntu au SHA exact. Sur le PC, un test **en lecture seule** sur les espaces PUBLIC connus du projet est permis; publier uniquement agrégats et statuts `CODEX_LOCAL_REPORTED`. Aucun contenu brut des vrais decks ni des bases en Git.

## Enveloppe et exclusions
**Budget réseau 0 GET, 0 recherche fournisseur**. Aucun relancement d'une campagne terminée. Aucun accès aux bases, decks, collection, crédits, journaux personnels, captures, OCR, session ou compte TCG Live; aucune écriture/migration sur les bases PUBLIC existantes; aucun achat, système, installation, planificateur Windows, tâche récurrente, nouveau backup, restauration, purge, reset, merge ou force-push. Respecter les droits et la provenance des textes publics.

## Livraison
Exécuter sans micro-go toutes les étapes de ce lot, tests complets et hygiène, puis publier code, tests et rapports assainis sur la branche autorisée : STATE/NEXT_ACTION/RESULT/HANDOFF/DECISIONS si décision nouvelle; docs et preuves sans données brutes. Vérifier HEAD distant et deux jobs CI du SHA livré, annoncer `AWAITING_AUDIT`, STOP pour ChatGPT. Ne supprimer aucun objectif restant de V1; ne pas répéter le test presse-papiers TCG Live historiquement `FIELD_VALIDATED`.
