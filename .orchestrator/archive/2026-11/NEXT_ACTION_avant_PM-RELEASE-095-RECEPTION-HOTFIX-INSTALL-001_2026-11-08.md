# PM-RELEASE-095-RECEPTION-HOTFIX-INSTALL-001 — RESUME_WITH_CODEX (2026-11-07)

**Claude Code interrompu par quota durant le contrôle de la sauvegarde D-293, avant toute confirmation d'une sauvegarde actuelle ou d'une installation.** La capture propriétaire confirme seulement prévol et contrôle initial de SHA. Le propriétaire veut terminer avec Codex. Instruction de reprise exhaustive dans [NEXT_PROMPT.md](NEXT_PROMPT.md), commit `cbaae39`. **Fermer Claude (option 1, sans reprise automatique) avant Codex.** Codex doit refaire vérifications et sauvegarde actuelle, poursuivre installation seulement si préconditions remplies; STOP en cas d'écart. Aucune publication, aucune nouvelle fonction. Le GO d'installation du correctif 0.9.5 demeure limité à cette opération.

---

# PM-RELEASE-095-RECEPTION-HOTFIX-INSTALL-001 — READY_FOR_EXECUTION (2026-11-07)

**GO du propriétaire reçu (« go ») pour installer sur son PC le correctif 0.9.5 de D-294.** Une seule tâche Claude Code : [NEXT_PROMPT.md](NEXT_PROMPT.md), préparée au commit `89c511d`. Prévol `fetch/pull --ff-only`, deux sauvegardes à préserver (D-293 + copie actuelle nouvelle et vérifiée), contrôle SHA-256 Setup `91993E84F0E17050898E11E1345F54E99D8A99420DE04BA321942992133BC212`, installation Inno normale (décocher lancement auto), contrôle EXE installé SHA-256 `45D4EBA935DCA32C1898D18FD942668F4F52DA5A9B77A07A6E1F6234815B8145`, intégrité des fichiers personnels avant ouverture, fumée isolée, rapport privé puis STOP. **Même numéro 0.9.5 : l'empreinte, pas la version, identifie le hotfix.** Réception visuelle par le propriétaire des images Deck Lab et du sélecteur Coach IA reste à obtenir. Publication non autorisée.

---

# PM-RELEASE-095-RECEPTION-HOTFIX-001 — VERIFIED_SOURCE / AWAITING_OWNER_INSTALL_GO (2026-11-07)

**Audit ChatGPT du correctif terminé :** [VERIFICATION_PM-RELEASE-095-RECEPTION-HOTFIX-001_2026-11-07.md](VERIFICATION_PM-RELEASE-095-RECEPTION-HOTFIX-001_2026-11-07.md), commit `c68c227`. Code `00eecb3`, rapport `b74a957`. Causes et correctifs vérifiés dans les sources pour images TCGdex absentes après actualisation du soir (UTC vs date locale) et lisibilité des options « Ce que le coach reçoit ». Deux portes rapportées vertes et candidat Windows non signé créé, non installé. La réception utilisateur reste refusée jusqu'au constat sur la nouvelle installation.

**Prochaine action UNIQUE : attendre le GO explicite de l'utilisateur pour installer le candidat hotfix 0.9.5 local** `dist/installer-candidate-0.9.5-00eecb3/PokeMind-Setup-0.9.5.exe` avec SHA-256 `91993E84F0E17050898E11E1345F54E99D8A99420DE04BA321942992133BC212`. Même numéro 0.9.5 que l'ancien EXE installé : distinguer par empreinte, ne pas passer par mises à jour automatiques. Sauvegarde complète/intègre avant, fermeture de PokeMind, assistant normal, décocher lancement auto, contrôles fichiers et vérification visuelle propriétaire. Aucune installation ni publication sans GO; sauvegardes conservées.

---

# PM-RELEASE-095-RECEPTION-HOTFIX-001 — IMPLEMENTED / REPORTED, AWAITING_CHATGPT_AUDIT (2026-11-07)

**Exécuteur : Claude Code, sur demande directe du propriétaire (réception 0.9.5 non acceptée). Code `00eecb3`, rapport [RESULT.md](RESULT.md), décision D-294.**

- Images du Deck Lab : cause exacte = date UTC de récupération du catalogue comparée à la date locale (mise à jour en soirée → toutes les extensions refusées jusqu'à minuit). Corrigé par `local_day()`; reproduit et vérifié sous Windows sur copies publiques du vrai catalogue/cache.
- Réglages › Coach IA › « Ce que le coach reçoit » : choix complet, liste lisible dans les deux thèmes (style windows11), explication pleine largeur.
- Porte complète VERTE; candidat local isolé `dist/installer-candidate-0.9.5-00eecb3/PokeMind-Setup-0.9.5.exe` (`91993E84…C212`), non signé, **non installé, non publié**.

**Prochaine action unique : audit ChatGPT de `00eecb3` et de ce rapport.** Installation du candidat chez le propriétaire = **GO distinct**; numéro de version (0.9.5 ou 0.9.6) à décider; publication = GO distinct après réception acceptée. Aucun autre travail Claude Code/Codex sans nouvelle demande.

---

# PM-RELEASE-095-OWNER-RECEPTION — AWAITING_OWNER_VISUAL_VERIFICATION (2026-11-07)

**Audit indépendant de l'installation terminé** : [VERIFICATION_PM-RELEASE-095-OWNER-INSTALL-001_2026-11-07.md](VERIFICATION_PM-RELEASE-095-OWNER-INSTALL-001_2026-11-07.md), commit `1eeb60b`. Installation 0.9.5 rapportée réussie, sauvegarde 306/306 vérifiée selon Claude, aucun ancien fichier manquant; toutefois 5 fichiers modifiés au lancement (dont fichier de préférences rétréci 406→352 octets), 9 fichiers nouveaux. **Aucune perte logique ni conservation de tous les réglages n'est encore démontrée.**

**Prochaine action UNIQUE : contrôle visuel par le propriétaire des préférences (notamment confidentialité/partage coach IA), langue, thème, decks, deck principal, combats, historique, Deck Lab > Statistiques.** Ne pas changer/restaurer les fichiers sans diagnostic et autorisation distincts; conserver la sauvegarde privée. Aucun nouveau mandat agent, aucune publication/tag/push public sans GO séparé. Statut : `INSTALLED_OWNER_VERIFICATION_PENDING`, `NOT_RELEASE_READY`.

---

# PM-RELEASE-095-OWNER-INSTALL-001 — INSTALLED_OWNER_VERIFICATION_PENDING, AWAITING_CHATGPT_AUDIT (2026-11-07)

**Exécuteur : Claude Code. Aucun changement de code (`24e9cc5`); rapport [RESULT.md](RESULT.md), décision D-293.**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter (aucune seconde installation ni sauvegarde).

- Sauvegarde complète vérifiée **avant** installation : 306/306 fichiers, SHA-256 identiques, source stable, restauration à blanc OK.
- Setup SHA-256 **MATCH**, AppId de production; assistant normal, code 0; PokeMind **0.9.5 installé** (registre, PE, fichiers = distribution).
- Données : aucun fichier préexistant perdu; 5 modifiés et 9 nouveaux par l'application 0.9.5 lancée (case « Lancer » de l'assistant, puis propriétaire).

**Prochaine action unique : audit ChatGPT de ce rapport et inspection visuelle par le propriétaire** (decks, journaux,
réglages, Deck Lab › Statistiques). Retour arrière seulement sur autorisation explicite. Publication / tag `v0.9.5` /
dépôt public : **GO distinct** après réception. Aucun autre travail Claude Code/Codex sans nouvelle demande.

---

## Mandat exécuté (conservé)

# PM-RELEASE-095-OWNER-INSTALL-001 — READY_FOR_EXECUTION (2026-11-07)

**GO explicite reçu du propriétaire** pour installer localement la 0.9.5 (message « oui »). Mandat unique de mise à niveau réelle, sans publication : [NEXT_PROMPT.md](NEXT_PROMPT.md) au commit `6cacf42`. Claude Code doit d'abord sauvegarder complètement les données existantes, vérifier leur intégrité, puis le SHA-256 du Setup local et l'AppId; STOP sans installation si un prérequis échoue. Installer normalement 0.9.5 sans désinstaller 0.9.4, vérifier version/données/statistiques, ne pas restaurer automatiquement, écrire un rapport assaini dans RESULT et STOP pour audit ChatGPT et confirmation utilisateur. **Aucune autorisation de publication.**

---

# PM-RELEASE-095-OWNER-RECEPTION — AWAITING_OWNER_GO (2026-11-07)

**Audit ChatGPT du candidat terminé : VERIFIED_SOURCE / CANDIDATE_READY_FOR_OWNER_RECEPTION / NOT_RELEASE_READY.** Voir [VERIFICATION_PM-RELEASE-095-WINDOWS-CANDIDATE-001_2026-11-07.md](VERIFICATION_PM-RELEASE-095-WINDOWS-CANDIDATE-001_2026-11-07.md), commit `cff6bdb`. Code `24e9cc5`, rapport exécutant `a21e98a`; trois portes vertes, fumées Windows et QA 0.9.3→0.9.5 rapportées, non rejouées par ChatGPT.

**Prochaine action unique : attendre le GO explicite du propriétaire pour mettre à niveau son installation réelle vers la 0.9.5.** Aucun nouveau prompt agent pour l'instant. Lors du GO : vérifier le SHA-256 du Setup local, sauvegarder les données avant modification, installer prudemment, vérifier démarrage, decks, journaux, préférences et Statistiques. Aucune publication/tag/push public, qui exigera son GO distinct. La 0.9.4 et ses candidats restent conservés.

---

# PM-RELEASE-095-WINDOWS-CANDIDATE-001 — IMPLEMENTED / REPORTED, AWAITING_CHATGPT_AUDIT (2026-11-07)

**Exécuteur : Claude Code. Code `24e9cc5`, rapport [RESULT.md](RESULT.md), décision D-292.**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

- Version **0.9.5** partout (app, pyproject, README FR/EN, CHANGELOG, SECURITY, notes, PE, Inno); 0.9.4 dite jamais publiée.
- Porte complète VERTE sur `24e9cc5` (Qt 121; cœur 1635/0/3), code de sortie 0; même porte VERTE dans l'export dry-run (non poussé).
- Candidat local non signé `dist/installer-candidate-0.9.5-24e9cc5/PokeMind-Setup-0.9.5.exe` (SHA-256 `6E7E5CB2…68CB`);
  fumées gelées isolées (7 pages, Statistiques FR/EN, aucun réseau, aucun Codex/Claude); essai AppId QA 0.9.3 → 0.9.5 →
  désinstallation, données inventées préservées; candidats 0.9.4 et installation du propriétaire inchangés.

**Prochaine action unique : audit indépendant ChatGPT de ce rapport.** Réception chez le propriétaire (installer le
Setup 0.9.5 par-dessus sa vraie installation) = GO distinct; publication / tag `v0.9.5` / dépôt public = GO distinct
ensuite. Aucun autre travail Claude Code/Codex sans nouvelle demande.

---

## Mandat exécuté (conservé)

# PM-RELEASE-095-WINDOWS-CANDIDATE-001 — READY_FOR_EXECUTION (2026-11-07)

**Revue ChatGPT terminée** : porte complète 121 Qt / 1634 cœur (0 échec, 3 ignorés), deux exécutions rapportées; vrai endpoint public Limitless testé en 5 GET et données hors ligne recoupées. Audit [VERIFICATION_PM-DECKLAB-STATS-REALITY-GATE-001_2026-11-07.md](VERIFICATION_PM-DECKLAB-STATS-REALITY-GATE-001_2026-11-07.md), commit `7f7fcbb`. Code du nouvel onglet `3a56023` inchangé.

**Prochaine action UNIQUE : préparer et valider un candidat Windows isolé 0.9.5** via [NEXT_PROMPT.md](NEXT_PROMPT.md), écrit au commit `8efe909`. Claude Code : fetch/pull --ff-only, exécuter intégralement le mandat, tests, build EXE/Setup en staging, rapport RESULT, push privé, STOP audit ChatGPT. Ne pas altérer la 0.9.4 candidate ni l'installation réelle; aucune publication/tag sans GO ultérieur.

---

# PM-DECKLAB-STATS-REALITY-GATE-001 — IMPLEMENTED / REPORTED, AWAITING_CHATGPT_AUDIT (2026-11-07)

**Exécuteur : Claude Code. Aucun changement de code (arbre `3a56023`); rapport [RESULT.md](RESULT.md).**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

- Porte locale COMPLÈTE sur l'arbre final : VERTE (Qt 121; cœur 1634/0/3), deux fois (HEAD `d1c06ed` et arbre du rapport), code de sortie 0.
- API Limitless réelle, une collecte publique bornée dans un root synthétique : **5 GET** (budget 8, quota 50/5 min),
  disponible, contrat conforme (PTCGL/Standard, archétypes publiés 23/23); 1 tournoi BO1 du 2026-11-07, 23 joueurs,
  56 matchs admissibles. Rendu hors ligne vérifié (identifié, ambigu, échantillon insuffisant, non identifié); oracle égal.
- Aucun défaut bloquant reproduit; risque `_snapshots` non reproductible avec le pipeline réel (limite documentée).

**Prochaine action unique : audit indépendant ChatGPT de ce rapport.** Build candidat 0.9.5, installation chez le
propriétaire ou publication : chacun sur GO explicite distinct. Aucun autre travail Claude Code/Codex sans nouvelle demande.

---

## Mandat exécuté (conservé)

# PM-DECKLAB-STATS-REALITY-GATE-001 — READY_FOR_EXECUTION (2026-11-07)

**Audit indépendant D-291 : source implémentée et revue; reste une porte complète sur l'arbre final après modification de fixture et un essai API Limitless réelle, public et borné.** Rapport : [VERIFICATION_PM-DECKLAB-PUBLIC-STATS-001_2026-11-07.md](VERIFICATION_PM-DECKLAB-PUBLIC-STATS-001_2026-11-07.md), commit `3b0d726`.

**Prochaine tâche unique Claude Code** : [NEXT_PROMPT.md](NEXT_PROMPT.md), préparé au commit `7894018`. Relancer tests complets sous isolation, vérifier une collecte Limitless réelle sans données personnelles, noter sources/échantillons, corriger seulement défauts prouvés; pousser rapport privé puis STOP audit ChatGPT. Ne pas modifier, installer ou publier la 0.9.4; aucun build ni publication 0.9.5.

---

# PM-DECKLAB-PUBLIC-STATS-001 — IMPLEMENTED / REPORTED, AWAITING_CHATGPT_AUDIT (2026-11-07)

**Exécuteur : Claude Code. Code `3a56023`, rapport [RESULT.md](RESULT.md), décision D-291. Cible 0.9.5, non publiée.**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

- Deck Lab : onglet **Statistiques** (archétype public du deck, représentation, taux par mode BO1/BO3, matchups, méta
  générale, évolution datée), source Limitless API via le collecteur existant, chiffres vérifiés par oracle indépendant.
- Identification locale par les Pokémon de la liste, jamais par le nom; égalité → non identifié, aucun taux.
- Réseau : au plus 1 tentative auto/jour partagée + Actualiser borné; aucune liste transmise. Porte locale : VERTE (Qt 121, cœur 1634/0/3).

**Prochaine action unique : audit indépendant ChatGPT de `3a56023`.** Build candidat 0.9.5, installation chez le
propriétaire ou publication : chacun sur GO explicite distinct. La 0.9.4 reste en attente de sa réception et de son GO.
Aucun autre travail Claude Code/Codex sans nouvelle demande.

---

## Mandat exécuté (conservé)

# PM-DECKLAB-PUBLIC-STATS-001 — READY_FOR_EXECUTION (2026-11-07)

**Nouvelle demande : statistiques graphiques des decks, via source publique Limitless, avec cache et provenance.** Cible **0.9.5**, pas une modification de la 0.9.4. Mandat unique Claude Code : [NEXT_PROMPT.md](NEXT_PROMPT.md), écrit au commit `3c71b6a`. Lire et exécuter entièrement le mandat après `git pull --ff-only`; tests Qt + cœur, commit/push privés, `RESULT.md`, puis STOP pour audit ChatGPT. Aucune installation ou publication. Vérifier l'association deck→archétype et ne jamais inventer de statistiques ni envoyer des listes privées à Limitless.

---

# PM-RELEASE-094-FINAL-GATE-001 — IMPLEMENTED / REPORTED, AWAITING_CHATGPT_AUDIT (2026-11-07)

**Exécuteur : Claude Code. Code `fae10da`, rapport [RESULT.md](RESULT.md), décision D-290.**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

- Audit local de `8570613`, `358a551`, `6cb86c4`, `5ee8c45` : gardes d'écriture confirmées côté hôte; deux défauts
  corrigés (liste du deck principal envoyée à chaque question / texte de consentement infidèle; EXE sans version Windows).
- Porte locale complète VERTE (Qt 119; cœur 1624/0/3) et même porte VERTE dans l'export public dry-run (non poussé).
- Candidat local `dist/installer-candidate-0.9.4-fae10da/PokeMind-Setup-0.9.4.exe` (SHA-256 `5DE0D9EF…6EAC6`, non signé);
  installation 0.9.3 → mise à niveau 0.9.4 → désinstallation vérifiées avec un AppId QA isolé, données inventées.

**Prochaine action unique : UN audit indépendant ChatGPT de `fae10da` (avec `8570613`, `358a551`, `6cb86c4`, `5ee8c45`)
et réception du propriétaire** (installer le candidat sur sa machine = GO distinct). Publication / tag `v0.9.4` /
mise à jour du dépôt public : **seulement sur GO explicite distinct** après l'audit. Aucun autre travail Claude Code/Codex.

---

## Mandat exécuté (conservé)

# PM-RELEASE-094-FINAL-GATE-001 — READY_FOR_EXECUTION (2026-11-07)

**Nouvelle autorisation du propriétaire : « préparer à finir cette version vraiment au complet ».** Une seule mission Claude Code de finalisation V1 vers un **candidat local 0.9.4** : audit des corrections D-286 à D-289, tests complets, contrôle confidentialité, build Windows/installateur/mise à niveau synthétique, préparation dry-run de release; corriger seulement les bloquants V1 prouvés. **Mandat complet : [NEXT_PROMPT.md](NEXT_PROMPT.md)** (rédigé au commit `f8ee810`). Ne pas installer sur le PC réel, ne pas publier/taguer/mettre à jour le dépôt public sans GO distinct. À la fin : STOP audit indépendant ChatGPT.

---

# PM-COACH-LOSS-PRIORITY-001 — IMPLEMENTED / REPORTED, STOP audit ChatGPT

**2026-11-06. Exécuteur : Claude Code. Code `5ee8c45`, rapport [RESULT.md](RESULT.md), décision D-289.**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

- Toutes les parties comptent; un journal collé n'enregistre plus aucun deck adverse (victoire, défaite ou inconnu) sans
  demande explicite du propriétaire. Les défaites alimentent `loss_watch` (dérivé du rapport local, sans second stockage).
- Porte locale complète VERTE (Qt 119; cœur 1621/0/3). EXE candidat **local seulement**, non installé, non publié.
- Anciens decks adverses de « Mes decks » : aucun supprimé; identifiés par leur nom (limite documentée).

**Prochaine action unique : audit indépendant ChatGPT de `5ee8c45`** (avec `8570613`, `358a551`, `6cb86c4` encore en attente),
puis essai du propriétaire. Installation chez lui ou publication 0.9.4 : seulement sur GO explicite distinct.
Aucun autre travail Claude Code/Codex sans nouvelle demande.

---

## Mandat exécuté (conservé)

# PM-COACH-LOSS-PRIORITY-001 — READY_FOR_EXECUTION (2026-11-06)

Nouvelle demande du propriétaire : **ne plus créer de decks adverses automatiquement après ses victoires; prioriser le suivi des défaites, regrouper les matchups problématiques et permettre au coach d'en proposer des contres.** Mandat complet à lire/exécuter : [NEXT_PROMPT.md](NEXT_PROMPT.md), commit `4b72cdc`. **Exécuteur : Claude Code, UNE tâche, puis STOP audit ChatGPT.** Aucune publication publique, aucune suppression de decks existants, aucune lecture des données privées du propriétaire. Conserver ci-dessous l'historique.

---

# PM-UI-BRAINBALL-BRANDING-002 — IMPLEMENTED / REPORTED, STOP audit ChatGPT

**2026-11-06. Exécuteur : Claude Code. Code `8570613`, rapport [RESULT.md](RESULT.md), décision D-286.**
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

- La carte `assets/branding/pokemind-tcg-coach-original.png` (SHA-256 vérifié, non modifiée) remplace le logo dessiné
  dans la fenêtre, le menu, le bandeau, l'accueil, À propos, le classeur, l'icône de l'EXE, l'installateur et le README.
- Porte locale complète VERTE (Qt 115; cœur 1610/0/3). Icône vérifiée dans le PE de l'EXE et du Setup (9/9 entrées).
- Candidat **local seulement** : `dist/PokeMind/` (retour arrière `dist/PokeMind-before-branding-e2ae…`) et
  `dist/installer-branding-candidate/`. Dépôt public inchangé, **pas de 0.9.4 sans GO**.

**D-287 (`358a551`) : coach cloud + statistiques anonymes autorisés par défaut, installé chez le propriétaire.**

**D-288 (`6cb86c4`) : parties collées comptées dans la saison actuelle; « Ajouter mon deck » et « Deck principal ». Installé chez le propriétaire.**

**Prochaine action unique : audit indépendant ChatGPT de `8570613`, `358a551` et `6cb86c4`**, puis retour visuel du propriétaire (EXE local).
Aucun autre travail Claude Code/Codex sans nouvelle demande. La réception Windows de 0.9.3 reste en attente (historique ci-dessous).

---

## Mandat exécuté (conservé)

# PM-UI-BRAINBALL-BRANDING-002 — nouveau mandat actif : carte originale partout

**Autorisation explicite du propriétaire : 2026-11-06. Exécuteur : Claude Code. État : READY_FOR_EXECUTION.**
**Une seule tâche : remplacer l'ancien logo simplifié par la carte PokeMind / TCG Coach exacte dans l'application, les ressources de l'EXE, de l'installateur et des raccourcis.**

- **Exécuter intégralement** [NEXT_PROMPT.md](NEXT_PROMPT.md), après `git fetch` et `git pull --ff-only` sur la branche privée `work/pm-v1-lotj-final-readiness-windows`.
- **Source graphique désormais téléversée, sans aucune modification des octets** : `assets/branding/pokemind-tcg-coach-original.png` (1060 × 1484; SHA-256 `30824d84f594be0e1fe33b3e9531f487e497252e17d7a16ff57763b787d7f0f5`).
- Direction et usage : `docs/design/pokemind-brainball/README.md` ; couleurs BrainBall existantes à conserver : `palette.json`.
- **Aucune publication 0.9.4**, aucun push public, aucune donnée personnelle consultée/modifiée. Reconstruire les binaires **locaux** seulement et publier rapport privé.
- Au terme du mandat : **STOP pour audit indépendant ChatGPT**. Le rapport d'audit du code de 0.9.3 reste valable pour ce qu'il a vérifié; il ne vérifie pas encore ce nouveau branding. L'ancienne réception Windows 0.9.3 demeure en attente, sans être supprimée.

---

## Historique et mandat précédent (conservé)

# PM-UI-BRAINBALL-THEMES-001 — audit GitHub effectué, réception Windows en attente

2026-11-06. **Audit indépendant ChatGPT : VERIFIED_SOURCE (structure du code, palette, contrastes échantillonnés et arbre public), AWAITING_EVIDENCE pour tests Windows/EXE et réception du propriétaire.** Aucun statut CI au commit publié. `v0.9.3` existe et était publiée sur GO; aucune publication supplémentaire autorisée.

**Rapport indépendant** : [VERIFICATION_PM-UI-BRAINBALL-THEMES-001_POST_093_2026-11-06.md](VERIFICATION_PM-UI-BRAINBALL-THEMES-001_POST_093_2026-11-06.md).
Rapports exécuteur : [D-284 BrainBall](archive/2026-11/RESULT_PM-UI-BRAINBALL-THEMES-001_D284_2026-11-05.md), [D-285 0.9.3](RESULT.md).
Mandat [NEXT_PROMPT.md](NEXT_PROMPT.md) : **consommé**, ne pas le réexécuter.

**Prochaine action unique : réception par le propriétaire sur Windows de 0.9.3**, s'il choisit de l'installer : sauvegarde/archives préservées, thèmes foncé et clair sur Vue d'ensemble, Coach, Deck Lab, Réglages, Terminal; changements de thèmes, textes, données intactes et contrôles Mises à jour. Ne pas lancer d'autre travail Claude Code/Codex sans nouvelle demande. **0.9.4 seulement sur GO explicite**, notamment pour une correction post-réception.

Limite de sécurité documentée : installateur 0.9.3 non signé; SHA-256 servi par la même release ne prouve pas indépendamment l'identité de l'éditeur. Aucune compromission démontrée.

---

## Mandat antérieur suspendu — conservation intégrale

# PM-AUDIT-CLAUDE-PLAN — exécution du plan d'audit, suite en prochaine session

2026-10-29 Québec. **Mandat actif. Exécuteur : Claude Code** (propriétaire, D-258 : « tu as toutes mes autorisations… fais tout »).
Plan de référence : [`docs/audits/AUDIT_CLAUDE_2026-10-29.md`](../docs/audits/AUDIT_CLAUDE_2026-10-29.md) §10. Dernière session : voir [RESULT](RESULT.md).

## Demande du propriétaire du 2026-11-01 — refonte visuelle et version publique (D-266 à D-272)
Fait : refonte visuelle (D-266); mode autonome, catalogue et installateur (D-267); licence MIT, logo original et audit
de l'historique (D-268); export public vérifié et signature branchée (D-269); fichiers publics au standard des autres
dépôts publics (D-270); dépôt privé renommé `Sd-tech-Sol/PokeMind-dev` (D-271); **PokeMind 0.9.0 publié** :
dépôt public `Sd-tech-Sol/PokeMind` et préversion `v0.9.0` (D-272).
Reste, sur décision du propriétaire seulement :
1. **Signature** : avec un certificat, `Build-PokeMindInstaller.ps1 -SignArguments …` puis nouvelle version.
2. **Mise à jour publique** : chaque nouvelle version exige un GO; nouvel export appliqué dans le dépôt public,
   jamais de push de l'historique privé (`docs/release-checklist.md`).
3. ~~Actualiser le catalogue~~ : fait par D-283 (mises à jour des cartes et du programme en un clic).

## Retours d'essai du propriétaire du 2026-11-02 (D-273)
Fait à `9a9c6b4` : règle 1 ACE SPEC / 1 Radieux, enregistrement de deck par le coach, bandeau de chargement,
« Tout supprimer », rendu du chat. Reste :
1. **Vitesse au démarrage (M-4)** : obtenir du propriétaire les lignes « Analyse · étape · durée » (Réglages →
   Copier le diagnostic, journal masqué) puis optimiser l'étape la plus lente; ne jamais lire ses données.
2. ~~0.9.1 publique~~ : **publiée** le 2026-11-03 (D-274, préversion `v0.9.1`, commit public `a6446e1`).
   ~~0.9.2 publique~~ : **publiée** le 2026-11-05 (D-282, préversion `v0.9.2`, commit public `afdb0a3`).
   ~~0.9.3 publique~~ : **publiée** le 2026-11-05 (D-285, préversion `v0.9.3`, commit public `5629ae2` :
   mises à jour en un clic D-283 et couleurs BrainBall D-284).
3. **Recherche web du coach (D-275)** faite à `c7f8271`; **réinitialisation complète (D-276)** faite à
   `1593f0b`, puis au choix par type de données (D-277) à `b53eee3`; diagnostic du propriétaire traité (D-278 à `c4338f5` : plantage d'import, analyse plus rapide,
   diagnostic complet), puis 2e diagnostic (D-279 à `4cf50ea` : decks et recherche visibles par le coach,
   analyse réutilisée d'un import à l'autre), puis réinitialisation réparée, scripts d'archive et saisons
   (D-280 à `1cdb9cd`), puis archive et restauration dans l'application (D-281 à `b3c533c`);
   réception propriétaire en cours. Publiés en 0.9.2 (D-282). Toute version publique suivante exige un GO
   (checklist C.0 : récupérer d'abord les modifications faites sur GitHub).

## Réception propriétaire en attente
Ouvrir son `dist/PokeMind/PokeMind.exe` habituel et vérifier :
- **Installateur (D-267, facultatif)** : `dist/installer/PokeMind-Setup-0.9.0.exe` installe une copie autonome pour ton
  compte (`%LOCALAPPDATA%\Programs\PokeMind`, menu Démarrer). Elle utilise `%LOCALAPPDATA%\PokeMind` : si ta copie
  D-264 est à cet endroit, elle ouvre tes données (sans le mode dossier du chat); sinon elle démarre vide avec
  l'assistant de bienvenue et propose le catalogue (25 Mo, environ 1 min). Ne pas ouvrir les deux applications en
  même temps. Désinstaller : Paramètres Windows › Applications › PokeMind (tes données restent).
- **Mode du message (D-269)** : à gauche d'Envoyer, « Coach » (par défaut), « Recherche web » (collecte publique pour
  ce seul message) ou « Développement » (Codex/Claude sur le code). Aucun mot de la phrase ne change plus le mode.
- **Refonte visuelle (D-266)** : pendant une réponse, une carte rouge animée avec chrono apparaît au-dessus du champ;
  Entrée envoie; « Agrandir » (en haut du chat) ouvre la discussion en grande fenêtre et « Ramener » la remet. Les listes
  « Historique » et « Idées de questions » s'ouvrent en entier. Logo original (deux cartes et un cerveau, D-268) dans le
  menu, la barre des tâches et l'icône de l'EXE. Pages Réglages (onglets), Combats (tuiles et barres), Cartes & méta (classeur : la
  couverture s'ouvre, flèches ‹ › pour tourner les pages, clic sur une carte = fiche), Apprentissage, Terminal (un clic
  ouvre le moteur du chat). La langue suit ton choix enregistré, sinon celle de Windows (Réglages → Général pour
  changer); l'assistant de bienvenue ne s'affiche pas pour toi (préférences existantes).
- **Données hors du projet (D-264)** : au premier démarrage, PokeMind demande « Sortir tes données du projet » avec la
  destination (`%LOCALAPPDATA%\PokeMind`), la taille et le nombre de fichiers. Répondre **Oui** : barre de progression,
  puis « Copie vérifiée : N fichiers ». Vérifier ensuite combats, Deck Lab (« Mes decks »), discussions du coach,
  préférences et caches. Réglages → « Dossier de données » montre le nouveau chemin. En cas de problème : Réglages →
  « Revenir au dossier du projet », puis rouvrir. **Ne rien supprimer** : l'original reste dans `data/local` du projet;
  le retirer plus tard est une décision du propriétaire seulement.
- **Chat dans le dossier PokeMind (D-265)** : Réglages → « Le chat travaille dans le dossier PokeMind » est cochée.
  Écrire dans le chat comme à Claude Code : la première fois, accepter l'avertissement de confidentialité. Codex ou
  Claude répondent selon les règles du dossier, peuvent lire et modifier les fichiers du projet (mode Standard ou
  Accès complet) et gardent les outils du coach. Un journal collé reste traité par le coach isolé (deck enregistré
  comme avant). Décocher la case rend le coach isolé d'avant.
- **Coach (D-259, D-261)** : « fais-moi le meilleur deck avec Pikachu » avec **Codex**, puis avec **Claude** : un deck
  de 60 cartes en français avec codes et export TCG Live, validé (Codex : environ 3 minutes, compteur « Outils PokeMind ·
  consultation N » pendant l'attente), et non plus un bilan de statistiques. Réglages : la case d'envoi cloud doit être cochée.
  La réponse doit venir **même si la barre du bas indique une analyse en cours** (D-262); la liste « Reprendre une
  discussion » montre les titres complets.
- **Journal collé** (D-263) : Réglages → cocher l'envoi cloud et choisir « Ajouter statistiques… »; coller le journal
  d'une défaite (avec ou sans question) : le coach nomme le deck adverse, sépare cartes vues / déduites, valide 60 cartes
  et l'ajoute à **Deck Lab** (en tête, « Mon deck »). Barre du bas : « Deck ajouté à Mes decks : … ».
- **Terminal** (D-263, menu de gauche, dernier) : « Codex · yolo » ou « Claude Code · toutes permissions » → accepter
  l'avertissement de confidentialité une fois → écrire comme dans PowerShell. Ctrl+V colle, Ctrl+C copie la sélection
  (sinon interrompt), clic droit copie ou colle. Codex peut proposer une mise à jour : « Skip » garde la version éprouvée.
- **Supprimer** (D-260) : choisir une discussion, cliquer Supprimer, répondre Non puis Oui; elle disparaît de l'historique.
- Réglages (« Copier le diagnostic » montre maintenant une ligne par appel d'outil), fluidité du chat, mode développement.
Signaler tout écart; un retour arrière reste possible (anciens dossiers conservés sous `dist/`, voir RESULT).

## Prochaines étapes, dans l'ordre (une par session, `/clear` entre chacune)
1. ~~EXE à jour~~ : **fait le 2026-10-29**; reste la réception propriétaire ci-dessus.
2. ~~Données hors du dépôt~~ : **code fait le 2026-11-01 (D-264)**, copie vérifiée proposée au démarrage de l'EXE, original
   jamais touché; le CLI suit le même dossier. Reste la validation du propriétaire ci-dessus. Suites possibles : scripts
   autonomes de `scripts/`, EXE installé hors de `dist/` du dépôt, fixture `local_tmp` des tests hors de `data/local/test-runs`.
3. **Mode développement v2** (audit §4) : ~~terminal embarqué lançant `codex`/`claude` tels quels~~ **fait le 2026-10-31
   (D-263, ConPTY + pyte au lieu de xterm.js)**; reste éventuellement le client riche du chat (processus Claude persistant).
4. **Coach** : ~~outils et parité Codex/Claude/Ollama~~ **faits le 2026-10-29 (D-259)**; ~~A-8 mode explicite~~ et
   ~~A-7 contexte allégé~~ **faits le 2026-11-02 (D-269)**; reste éventuellement les permissions d'écriture du coach
   (annotation, proposition, decks privés) encore fondées sur les mots, à remplacer par une confirmation dans l'UI.
5. **Mémoire restante** (M-2 fin, M-4) : cache de `public_context`, analyse incrémentale par `semantic_identity`.
6. **Maintenabilité / publication** (§7, §9) : `ruff`, découpage de `cli.main`/`window.py`, client HTTP unique,
   crochets QA hors de l'EXE de production, licence et droits sur `source_material/`.

## Règles du mandat
- Porte locale `python scripts/local_gate.py` **VERTE** avant chaque push de code; comptes exacts dans RESULT.
- Aucune lecture/ouverture de `data/local` personnel ni de la copie sous `%LOCALAPPDATA%\PokeMind` par un agent; la copie
  se fait seulement dans l'EXE, sur « Oui » du propriétaire (D-264). Jamais de suppression de données ou de distribution précédente.
- V1 `NOT_RELEASE_READY`.

---

## Archives
Les mandats antérieurs (jusqu'à `PM-V1-LIVE-FR-EN-UI-001`) sont dans
[archive/2026-10/NEXT_ACTION_avant_2026-10-29.md](archive/2026-10/NEXT_ACTION_avant_2026-10-29.md). Aucune permission courante.
