# Mandat exécuteur — PM-V1-USER-JOURNEY-E2E-001

**Objectif : rendre vérifiable le parcours utilisateur central de PokeMind V1 sans toucher aux données personnelles.** Lot autonome conséquent A–F, plutôt que de répéter des micro-tests. **Statut READY**, après succès de la CI Windows+Ubuntu au SHA exact du dernier HEAD de préparation. GitHub est la mémoire canonique, l'utilisateur transmet seulement le message, Codex développe, ChatGPT audite après STOP.

## A — Prévol et inventaire
- Branche `work/pm-v1-lotj-final-readiness-windows`, `git status`, `fetch`, `pull --ff-only` si sûr; aucun reset/force-push. Lire `AGENTS.md`, `.orchestrator/SESSION_CONTINUITY.md`, `STATE.json`, le premier `NEXT_ACTION.md`, skill exécuteur, `.orchestrator/AUTONOMY_POLICY.md`, `docs/LOT_J_ACCEPTANCE_MATRIX.md`, `docs/VALIDATION_PROPRIETAIRE_V1_WINDOWS.md` et README/GUIDE CLI. Vérifier Windows+Ubuntu CI `completed/success` sur le **dernier HEAD exact**, sinon STOP. Ne pas exécuter d'instructions archivées.
- Inventorier les commandes réelles de PokeMind par `--help` et les tests; ne pas inventer de flags ou de parcours. Réutiliser `demo`, fixtures existantes, guides, outils de prévol et tests au lieu de recoder leurs fonctions.

## B — Parcours utilisateur **hors ligne, bout en bout, sur fixtures jetables**
- Dans un espace temporaire **synthétique explicitement créé par les tests** et séparé de `data/local/pokemind.sqlite3`, prouver en séquence : premier usage/FTS et recherche; découverte/affichage bilingue FR/EN (avec source ou fixture PUBLIC synthétique, sans GET réel); import d'un export fictif **exact de 60 cartes**; import répété de 5 à 10 journaux de combats fictifs avec preuve de dédoublonnage; liens explicites combat/version et révocation sur données fictives; profil statistique conservateur (pas d'inférence si ambigu), conseil et candidat 60 cartes, export et réimport éventuel **sur fichier jetable uniquement**.
- Faire apparaître les états `legal/not_legal/unknown` dans les contrôles du deck selon pièces **strictement synthétiques**; aucune règle datée du Pokémon réel ne doit être inventée. Prouver que `unknown` n'est pas converti en `legal`; ne jamais confondre un candidat, un deck joué ou la collection.
- Tester le coach visuel **avec champs/images synthétiques déjà prévus dans les tests**, sans image du propriétaire, ni téléchargement de moteur OCR, sans exécution de binaire OCR non attesté. Tester la mémoire multi-tours, les avertissements, les corrections et l'absence de persistance image. Si le vrai OCR reste absent, le dire explicitement.
- Tester les mises à jour/cadences en **dry-run uniquement** sans réseau ni planificateur Windows réel; tester backup/clone/migration seulement si des fixtures isolées et appels publics préexistants permettent des essais non destructifs. **Jamais** ouvrir, inventorier ou restaurer les backups/base utilisateur ou ACL réelles.
- Lister chaque étape avec commande réelle (sans chemin absolu privé), état, erreurs, nombre de preuves, éléments inconnus; regrouper dans un **rapport de parcours reproductible de l'utilisateur**, pas seulement une somme de `pytest`.

## C — Correction de défauts concrets seulement
- Reproduire toute rupture E2E de connexion entre modules (interfaces CLI, provenance carte/langue, tri-state légalité, deck/version/log, recommandations, visual coach, dates/fuseaux, reprise et erreurs) sous fixtures, puis effectuer les **correctifs minimaux** avec tests de régression. Si parcours déjà fonctionnel, ne créer aucune fonctionnalité artificielle.
- Préserver les gardes `PUBLIC_ONLY`, la transactionnalité, le mode offline, la confidentialité, les états `unknown`, la limite d'un propriétaire par acte privé, et les preuves de provenance. Pas de réécriture massive du schéma/moteur.
- Ajouter au besoin un **script de démonstration jetable hors ligne** qui montre un véritable parcours utilisateur reproductible et lisible sur Windows, sans sélectionner implicitement une vraie base. Par défaut : dry-run/fixtures; interdire chemin DB propriétaire et absence de fichier de sortie privé.

## D — Qualité et preuves
- Tests ciblés E2E, suite complète locale, compilation, hygiène, `git diff --check`, inspecter les fichiers suivis pour données personnelles. Aucune connexion réseau dans le test E2E; bloquer DNS/sockets sur fixtures. CI Windows+Ubuntu au SHA exact de la livraison.
- Mettre à jour uniquement les lignes justifiées dans `docs/LOT_J_ACCEPTANCE_MATRIX.md` et la documentation premier usage. Ne jamais marquer `RELEASE_READY` ni `DONE` sur OCR terrain, légalité mondiale, planificateur Windows ou migration personnelle juste avec fixtures.

## E — Rapport de progression V1 concret
- Publier `.orchestrator/EVIDENCE_PM_V1_USER_JOURNEY_E2E_001.md` avec le nombre d'étapes passées/échouées, commandes réelles, tests et sorties synthétiques utiles; distinguer observations CI, local et terrain propriétaire. Identifier **les portes V1 restantes qui exigent un acte de l'utilisateur** (données de combats/deck, OCR réel et permission d'installation, scheduler, clone7→13 personnel), sans les exécuter.
- Fournir un ordre d'acceptation terrain réalisable avec checkpoints/rollback, sans supprimer aucune exigence ni déclarer les fonctionnalités absentes comme non nécessaires. Décrire les éventuels défauts produit corrigés et la valeur pour le joueur.

## F — Clôture GitHub
- Commit/push code/tests/docs sur **cette branche J uniquement**; aucun merge `main`, reset, force-push. Mettre à jour `.orchestrator/{STATE.json,RESULT.md,HANDOFF.md,NEXT_ACTION.md}` (DECISIONS si décision nouvelle) avec `AWAITING_AUDIT`, `execute_now=false`, budget privé = zéro, provenance des essais.
- Vérifier SHA distant et statut CI **sur le SHA de livraison**, signaler PENDING_CI si nécessaire. **STOP pour audit ChatGPT**, sans lancer lot suivant et sans relancer anciens mandats.

### Interdictions absolues
Aucun accès/lecture/métadonnée/écriture de la base, des decks, logs, archives, sauvegardes, ACL ou images réelles du propriétaire; aucun restore plan/apply réel, clone/migration personnelle, install OCR/planificateur OS, édition des privilèges, achat, connexion au compte TCG Live, réseau externe ni publication de données privées. Aucun retrait silencieux des fonctionnalités A–J ou de l'objectif de connaissance Pokemon actualisée. **V1 `NOT_RELEASE_READY`.**
