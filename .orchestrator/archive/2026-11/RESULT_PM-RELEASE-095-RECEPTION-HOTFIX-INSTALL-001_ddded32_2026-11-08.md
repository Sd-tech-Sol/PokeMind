# RESULT — PM-RELEASE-095-RECEPTION-HOTFIX-INSTALL-001 — BLOCKED après installation (2026-11-08)

Exécuteur : Codex, reprise manuelle explicitement demandée par le propriétaire après fermeture des processus Claude PokeMind.
Code du correctif `00eecb3`, branche privée `work/pm-v1-lotj-final-readiness-windows`.
**Correctif installé; contrôle « données intactes avant premier lancement » non validé. STOP audit ChatGPT.**
[Rapport du premier blocage](archive/2026-11/RESULT_PM-RELEASE-095-RECEPTION-HOTFIX-INSTALL-001_BLOCKED_6c686aa_2026-11-08.md).

## Préconditions

- Fetch puis pull fast-forward : branche déjà à jour sur `6c686aa`, arbre initial propre, dépôt `Sd-tech-Sol/PokeMind-dev` confirmé privé. Mandat complet, dernier RESULT et continuité relus. La demande directe du propriétaire lève le blocage précédent, sans élargir le mandat.
- Processus Claude concernés absents; PokeMind fermé, mutex absent. Aucun processus d'une autre session arrêté par Codex.
- Prévol `RUNTIME_READY`, code 0 : base propriétaire non ouverte, réseau non utilisé, aucune écriture par cette commande.
- Root autonome attendu sans redirection, aucun override de root dans les environnements processus/utilisateur/machine; espace disponible suffisant.
- AppId production `{9B4E3B52-6C1D-4E7A-9F3B-5A2C8D1E7F40}`, une clé de désinstallation, dossier attendu; candidat version 0.9.5 et signature `NotSigned` attendue.

## Sauvegarde actuelle : complète et vérifiée AVANT Setup

Nouvelle copie privée horodatée, hors dépôt/root de données/dossier synchronisé, ACL limitée au propriétaire, SYSTEM et administrateurs. **315/315 fichiers, 359 275 701 octets, 16 sous-dossiers**, tailles et SHA-256 identiques. Tous les fichiers source tenus ouverts en lecture seule pendant la copie pour refuser les écritures concurrentes; re-hachage et horodatages source stables, répertoires identiques.

Robocopy copie : **code 1**, succès; restauration à blanc `/L` : **code 0**, aucune différence. Source et copie revalidées immédiatement avant lancement du Setup. Manifeste et preuves uniquement en local privé, contenu métier non inspecté.

D-293 **306/306 fichiers** et ses fichiers annexes revalidés avant/après : inchangés et conservés. La nouvelle copie 315/315 est également intacte après installation. Aucune ancienne sauvegarde supprimée ni modifiée; aucune commande `pokemind backup create`.

## SHA-256 : attendus = observés

| Binaire | SHA-256 |
|---|---|
| Setup correctif `dist/installer-candidate-0.9.5-00eecb3/PokeMind-Setup-0.9.5.exe` | `91993E84F0E17050898E11E1345F54E99D8A99420DE04BA321942992133BC212` |
| EXE installé avant, candidat initial `24e9cc5` | `7121BBEB277594164621DDEECD6FAA3331FAFFB87EABD55024BB2BD6E0E9E6FF` |
| EXE correctif de distribution ET EXE installé après | `45D4EBA935DCA32C1898D18FD942668F4F52DA5A9B77A07A6E1F6234815B8145` |

Fichier .sha256 du Setup conforme, empreinte recalculée juste avant lancement. Même numéro 0.9.5 avant/après : réussite binaire établie par l'empreinte et la comparaison du payload, pas par la version seule.

## Installation et contrôle binaire

Assistant Inno normal, seul argument `/LOG`, aucune désinstallation préalable, aucun mode silencieux ni `/RELAUNCH`. Journal privé. **Code de sortie 0**, succès Inno, même journal de désinstallation, aucun redémarrage Windows.

Le contrôle Windows échoue avec « Computer Use native pipe is unavailable », malgré les reprises documentées et la seconde interface disponible. Aucun clic automatisé effectué. Le propriétaire termine manuellement l'assistant et répond : « Terminé, lancement décoché et PokeMind fermé ». Codex n'a pas pu observer la case.

Après : **797/797 fichiers du programme identiques à la distribution D-294**, aucun manquant/différent/en trop, hors désinstalleur et licence; registre version 0.9.5, une clé et même AppId; deux raccourcis conformes. PokeMind et mutex absents au contrôle.

## Écart bloquant sur les données

Comparaison avec le manifeste pris immédiatement avant Setup : **315 → 320 fichiers; 0 manquant, 3 préexistants modifiés, 5 nouveaux**. Deux JSON modifiés gardent leurs tailles; un journal augmente. Les cinq nouveaux fichiers sont des JSON/textes. Contenus, préférences, decks et historiques non consultés.

Le journal Inno contient une **entrée Run visant l'EXE installé**; les écritures observées suivent la fermeture de l'installateur. Ces faits sont compatibles avec un lancement de l'application, malgré le décochage rapporté par le propriétaire. La cause exacte de cet écart n'est pas établie : ne pas affirmer que la case était cochée, ni que Setup a lui-même altéré les données.

**Le contrôle avant tout premier lancement n'a donc pas été obtenu.** Aucun fichier manquant ne démontre à lui seul la conservation logique de tous les réglages/données. Une seconde lecture seule confirme la stabilité des 320 fichiers après constat; les deux sauvegardes restent intactes.

## STOP et limites

Conformément au mandat en cas d'écart : **aucune fumée installée**, aucun nouvel essai d'installation, aucune restauration, aucune suppression, aucune modification de préférence/confidentialité/consentement par Codex. Aucune commande de collecte ni requête LLM lancée explicitement par Codex; le trafic éventuellement produit par l'application lancée n'a pas été mesuré.

Statut **BLOCKED_POSTINSTALL_DATA_DIFFERENCE / NOT_RELEASE_READY**, correctif binaire installé. Audit indépendant ChatGPT requis avant nouveau mandat. Réception visuelle propriétaire des images Deck Lab, du menu Coach IA et des préférences encore en attente, non acceptée par ce rapport. Diagnostic ciblé de contenu ou rollback uniquement sur autorisation distincte; ne pas rejouer ce mandat d'installation.

## Git

Rapport et orchestration assainis seulement; dernier RESULT bloqué archivé. Aucun code/version/dépendance modifié, aucun téléchargement/rebuild, aucun push public/tag/release. Porte complète D-294 historique, non rejouée : aucun code poussé. GitHub Actions retirées; HEAD distant et absence de statuts/runs à contrôler au SHA du rapport après push. Constats PC rapportés par Codex local, pas VERIFIED indépendamment.
