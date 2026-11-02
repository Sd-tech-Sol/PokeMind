# V1_BATCH_PLAN — tous les objectifs conservés, exécution en lots autonomes

**Décision utilisateur 2026-10-12 :** augmenter la **taille** des tâches et l'**autonomie de Codex**, **sans sauter aucune fonctionnalité V1**. Voir `.orchestrator/AUTONOMY_POLICY.md`. L'ordre demeure guidé par les dépendances; les lots sont des **unités de livraison**, non la permission de déclarer implémenté ce qui reste partiel.

## Où en est-on
- PM-0001 à PM-0006B : livraisons fondation/reporting, statut détaillé et réserves dans `.orchestrator/ROADMAP.md`, `RESULT.md` et `VERIFICATION_*.md`; ne pas confondre une fondation technique avec une couverture réelle exhaustive.
- **PM-0006C en cours chez Codex** : attestations manuelles de version pour les combats. **Ne rien changer sur sa branche en cours.**
- Les données de la base locale PokeMind sont privées et ne peuvent être confirmées par une revue GitHub; selon dernier rapport Codex : un deck exact version 1, cinq combats, aucun lien explicite. Il ne faut pas attribuer une performance à une version non attestée.

## Lots proposés après l'audit PM-0006C

### LOT A — Complétude et exactitude du cerveau de cartes/règles/métagame
**Périmètre intégral :** 
- TCGdex : index étendu FR/EN, impressions, variantes, cartes et textes, identités/alias vérifiés, progression/resume/quotas, priorité à la collection/decks explicitement fournis, métriques d'exhaustivité réellement observée; ne pas prétendre à toutes les cartes si fournisseur incomplet.
- Pokémon officiel : rotations Standard/Expanded datées, restrictions/bans, réimpressions, promos, errata, règles de structure 60 cartes (copies/énergies/Pokémon de base/exceptions), critères de légalité et de compatibilité Live **prouvés**, tri-state `legal/not_legal/unknown`.
- Limitless : compléter la couverture publique autorisée, aligner plateformes/formats/dates/BO, matchups avec provenance et échantillon, raffinement du cache; Trainer Hill **seulement si accessible et autorisé**.
- Qualité croisée : liaison impressions→règles→métagame, tests, références et indicateurs de couverture; éviter qu'une source compétitive serve d'autorité normative.
**Livraison utilisateur :** depuis Codex, une fiche fiable d'une carte, son édition/légalité **quand prouvée**, aperçu pertinent du métagame et un diagnostic clair des données manquantes. Aucun compte client envoyé à une API. Codex doit pouvoir planifier/exécuter plusieurs sous-tâches de ce lot **sans arrêt entre chaque sous-tâche**, et se corriger lui-même. Certains appels publics peuvent rester bornés par quotas; le mécanisme complet et les métriques de couverture sont requis, sans promettre de téléchargement instantané de tout le catalogue.

### LOT B — Deckbuilding, collection et moteur de conseils personnalisé
**Périmètre intégral :**
- Import volontaire de collection/inventaire et crédits; provenance, date, réconciliation avec identités; ne **jamais inférer possession** d'une carte observée en combat ou inventer coûts.
- Moteur de diagnostic stratégique/recommandations contextualisées : forces/faiblesses, synergies, options/contrecoups, substitutions, comparaisons de versions et évaluation de conformité; pas de certitude sur faible échantillon.
- Apprentissage à partir des journaux : causes plausibles vs prouvées, audit de choix de jeu, version explicitement attestée, métriques descriptives avec n, commentaires utiles dans SQLite, données reconstituées uniquement lorsqu'elles sont visibles.
- Suggestions de deck complet 60 cartes, liste exacte exportable en texte PTCG Live après contrôle, distinguer proposition et deck joué, collection/crédits connus et inconnus. Aucun achat/fabrication automatique.
- Commandes/skills Codex compacts pour « analyse mon deck », « améliore selon ma collection », « analyse mon combat », « propose un deck Standard », « compare variantes », avec citations et inconnues.
**Livraison utilisateur :** propositions exploitables sourcées et datées, simulations/analyses argumentées, export volontaire vérifiable, sans promesse de meilleur deck absolu. Codex itère et teste ces parcours dans le même lot.

### LOT C — Coach visuel en parties d'entraînement autorisées
**Périmètre intégral :**
- Entrées images/captures **explicitement fournies** à Codex, extraction d'état sans fausse certitude (main, banc, actif, énergie, tours, Récompenses cachées inconnues).
- Mémorisation textuelle durable du **match** et de l'historique connu, sans conservation prolongée des images et sans confondre les manches/situations.
- Analyse par tour : action conseillée, séquence, alternatives, raisonnement bref, conditions de repli après recherche/pioche/effet, besoin minimal de nouvelle capture, avertissement sur informations cachées.
- Tests de scénarios visuels synthétiques et **essai réel manuel** en entraînement seulement; pas de capture furtive, process hooking, overlay non autorisé ou bot. Portabilité pour les autres moteurs Codex/Claude, sans mécanisme exclusif.
**Livraison utilisateur :** demande « voici mon plateau, que ferais-tu? » et coaching utile sur plusieurs tours d'une partie d'entraînement. Aucun assistant pendant un tournoi où la règle l'interdit.

### LOT D — Actualisation autonome des connaissances publiques
**Périmètre intégral :**
- Mise à jour incrémentale indépendante du LLM des données publiques : TCGdex, règles officielles, Limitless, métadonnées, reprints, rotation, fiabilité et fraîcheur, respect des quotas et de la provenance.
- Contrôles **quotidiens légers** et réconciliation approfondie **mardi/vendredi** (heure locale de Toronto selon la spécification existante); logs anonymes, états, reprise/rollback, alertes significatives et fonctionnement hors ligne.
- Installation du planificateur Windows ou d'un service local **uniquement après l'accord spécifique du propriétaire**; Codex peut construire/tester en simulations/dry-run sans activer la planification. Pas d'API/compte privé nécessaire par défaut.
**Livraison utilisateur :** PokeMind sait signaler les changements de connaissance, les erreurs et la dernière mise à jour; la planification tourne localement une fois explicitement activée.

### LOT E — Stabilisation V1 complète
**Périmètre intégral :**
- Sauvegardes/restauration SQLite privées vérifiables, tests de restauration, sauvegarde avant migration, résilience aux corruptions/pertes, fonctionnement offline, contrôle de taille/disque, confidentialité.
- Couverture des fichiers skills/instructions Codex, commandes d'entrée, guides FR Québec et portabilité CLI Windows/Linux lorsque faisable sans sacrifier l'environnement cible.
- Tests end-to-end de tous les parcours V1 sur fixtures et **smoke tests locaux** lorsque autorisés, audit complet des interfaces/data/invariants/CI, documentation technique et utilisateur.
- Matrice des fonctions **DONE/PARTIAL/BLOCKED**, liens des vérifications, preuve de couverture catalogue et règle, limites; corrections des bugs de libération dans ce lot par Codex de manière autonome.
**Livraison utilisateur :** V1 utilisable sur Windows, récupérable après incident, avec procédures et limites explicites. Aucune GUI/web imposée (l'interface reste Codex), aucun merge sans décision explicite.

## Règles de progression
1. **Ne supprimer aucune tâche** : si un fournisseur public ne permet pas d'obtenir la totalité du catalogue ou si une capacité requiert une autorisation/collection non fournie, maintenir la ligne dans la matrice comme `PARTIAL/BLOCKED`, indiquer la prochaine action et ne pas dire V1 terminée.
2. **Ne plus imposer un audit ChatGPT après chaque sous-tâche ordinaire.** L'audit se fait après le **lot complet**. Codex est autorisé à faire plusieurs commits/checkpoints, auto-revue, retests et fixes dans sa seule branche sans approbation intermédiaire.
3. Bloquer uniquement pour comptes/accès tiers, achat ou crédit, risque de modification/destruction des données personnelles, merge/changement de branche principale, installation du scheduler ou décision produit significative : actions irréversibles demandent confirmation spécifique.
4. Suivre le plan complet depuis `.orchestrator/ROADMAP.md` **ET** cette matrice. Les phases déjà livrées restent des fondations à approfondir dans les lots selon leurs dépendances.
5. Ne pas promettre de délai, d'indexation totale ou de conformité certaine avant mesures/tests. Les sorties rendent les `unknown` visibles et n'inventent aucune preuve.
6. Cette politique est **à appliquer au prochain lot APRÈS PM-0006C**. La branche active de Codex reste inchangée pour ne pas créer de conflit.

## Après livraison LOT G — 2026-10-14

G0–G5 exécutés d’un bloc autonome sur la branche G. Matrice A–G exhaustive dans
`docs/LOT_G_ACCEPTANCE_MATRIX.md`, mécanismes et produits partiels distingués.
La V1 NOT_RELEASE_READY conserve restauration réelle sûre, OCR réel/calibration,
catalogue/règles/reprints/promos/errata/Expanded/Live/méta, Trainer Hill autorisé et
cadence OS sous opt-in. `docs/LOT_H_COMPLETION_PLAN.md` détaille les critères H0–H5;
ce plan n’autorise pas leur exécution avant audit G et prochain NEXT_PROMPT ChatGPT.
Aucun acte propriétaire (backup/clone/migration/import/attestation, capture,
installation ou scheduler) n’a été exécuté pendant G.


## Après audit ChatGPT LOT G — mandat LOT H (2026-10-14)
Audit indépendant `.orchestrator/VERIFICATION_LOT_G.md` : G accepté pour suite sous limites, CI Windows/Linux run `38600129548` (389 pass/1 skip chacun au SHA `9b19644e...`). **LOT H H0–H5 autorisé seulement en mode autonome sur branche H** par `.orchestrator/NEXT_PROMPT.md`, sans aucun acte sur vraies données, OCR installé, image propriétaire, planificateur Windows ou merge. Priorités sûreté restore/fail-closed, benchmark OCR synthétique sans faux succès, catalogue/règles/méta sources, parcours propriétaire préparés, cadence dry-run, gates et tests. Les blocages ne sont jamais supprimés, V1 `NOT_RELEASE_READY` jusqu'aux preuves terrain et consentements nécessaires.


## LOT H livré et prochain LOT I actif (2026-10-14)
LOT H `5d27832ac8933bb30eaa95430eecfd10fe8cf75e` accepté en revue indépendante ChatGPT pour continuation, `.orchestrator/VERIFICATION_LOT_H.md`, CI au dernier SHA Windows/Linux 416 pass/2 skips chacun; V1 **NOT_RELEASE_READY**. LOT I **I0–I7** sur branche `work/pm-v1-loti-windows-completion` et `.orchestrator/NEXT_PROMPT.md`. Parcours utilisateurs Windows/Codex et preuves complètes; aucune addition de fonctionnalité Linux. Les objectifs des lots A–H non démontrés restent ouverts; jamais de faux release ou acte privé implicite.
