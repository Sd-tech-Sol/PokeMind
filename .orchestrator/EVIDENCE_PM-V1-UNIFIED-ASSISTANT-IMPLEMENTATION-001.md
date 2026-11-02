# Preuves — PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001

## Contrôle GitHub après publication du code

HEAD distant confirmé **`f2b54582eccd1bcc244e1f302f074384347a8ec2`**, identique au commit local publié. [Run40451791236](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40451791236) au même SHA : **completed/failure**. Jobs Windows122015978235 et Ubuntu122015977927, chacun **zéro étape**, annotation contrôlée directement : « The job was not started because an Actions budget is preventing further use. » Aucun test CI exécuté; aucun marqueur ni empreinte de cette révision déclaré vérifié. Réception CI AWAITING_EVIDENCE, facturation inchangée. Le commit documentaire qui conserve ce constat ne change pas le code compilé/testé; sa CI au HEAD final doit aussi être lue sans lui substituer un ancien succès.

2026-10-27 Québec. **CODEX_LOCAL_REPORTED / AWAITING_AUDIT**, jamais auto-VERIFIED. Déclenchement manuel explicite du propriétaire le 2026-10-26, [mandat A–G](MANDATES/PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md), activation `d172fd20862ea3d83df3f1a2dddfd046c15349a4`. Branche exclusive `work/pm-v1-lotj-final-readiness-windows`. Ancien mandat ConPTY à deux conversations annulé. **V1 NOT_RELEASE_READY.**

## A–G livrés dans les composants existants

- Une chronologie et une saisie; sous-sessions réelles par fournisseur et canal de permissions. Navigation principale FR/EN, 12 amorces, streaming, temps, arrêt et historique conservés.
- Routage local journal/question/slash/développement; question jointe au journal traitée automatiquement sur la bonne partie. Une instruction dérivée du journal ne peut activer ni outils projet ni commande slash.
- Outils typés de combats, observation, reconstruction, bibliothèque, comparaison, collection, légalité, Learning Loop, candidats et recherche. Contexte privé borné selon préférence; aucune DB parallèle.
- Actions de développement Codex/Claude réelles dans le même fil; sandbox natif choisi, réglage complet volontaire et visible. `/status` officiel sans inférence, champs absents indisponibles, compactage déclaré accepté plutôt que prétendument achevé.
- Reconstruction classée de 1–3 listes60 sourcées compatibles, ou absence explicite; observations/minima/contradictions/inconnues conservés. Pas de probabilités inventées. Version jouée recherchée par l'attestation existante en lecture seule, sans substituer une dernière version non attestée.
- Recherche locale d'abord, puis collecte publique bornée et reçus d'écriture; versions par source, déduplication, refroidissement après refus, cache hors ligne. Pairings acquis par moteur existant dans un nouvel instantané PUBLIC, jamais un ancien lot réactivé.
- Candidat60 distinct du deck joué, copie via Deck Lab; annotation datée/révocable relue au prochain processus et séparée des observations factuelles. Aucune promesse de légalité/Live/collection inconnue.

## Validation locale sur fixtures

Les JUnit et captures ne sont pas publiés : ils peuvent contenir noms de machine et chemins. Résultats techniques assainis ci-dessous.

| Vérification | Résultat et portée |
|---|---|
| Préflight / démo | `RUNTIME_READY`; `SYNTHETIC_REHEARSAL_PASSED`, 79 processus CLI sur corpus inventé. Aucune DB personnelle implicite. |
| Suite principale hors Qt | **1393 réussis, 3 ignorés**, zéro échec/erreur, processus terminé normalement. Exécution complète sur Windows; suivie des tests ciblés après corrections finales. |
| Régressions finales ciblées | **102 réussis** : outils, fournisseurs, mémoire/recherche, services desktop, batch existant, annotation relue au redémarrage. |
| Qt final, processus séparé | **31 réussis**, sortie normale : journal+question, fil conservé, slash sans inférence, permissions non activées par journal, reçu visible, ingestion/galerie/arrêt existants. |
| Meta / public campaign | **80 réussis** après ajout des bornes de réponse/annulation au client existant. |
| Compilation / hygiène | compileall et diff sans erreur; contrôle des fichiers suivis avant publication, aucun artefact privé préparé. |

Un premier passage principal a échoué uniquement dans une fixture de fraîcheur lorsque la journée a changé durant cette longue session. Horloge de fixture stabilisée; le deuxième passage complet ci-dessus a réussi. Les dernières corrections ont ensuite été exercées par les suites ciblée et Qt indiquées; les nombres ne sont pas additionnés pour faire croire à des tests uniques supplémentaires. Aucun échec ignoré ni suite retirée du workflow.

## Vrais moteurs et vraie fenêtre Windows

Environnement qualifié : Windows11, Python3.13.15, PySide6 6.12.0, PyInstaller6.22.3, Codex CLI0.163.0, Claude Code2.1.311. Aucune installation globale ni nouvelle dépendance projet nécessaire. Les schémas officiels générés par le CLI ont servi à qualifier les méthodes disponibles.

`scripts/qa_unified_agent.py` a exercé des dossiers inventés uniquement :

- `account/read`, `account/rateLimits/read` et `account/usage/read` ont retourné les vraies données d'interface, sans copier identifiant/email dans le rapport.
- Codex a créé un fichier inventé et exécuté un test de contenu; **exitCode=0 reçu de command/exec**, pas seulement affirmé dans sa réponse. Streaming et événements outils observés.
- Claude a réellement écrit son fichier inventé; son existence/contenu ont été contrôlés hors réponse LLM.
- Deux GET TCGdex ont enregistré deux observations publiques, puis une lecture hors ligne a retrouvé ces connaissances sans GET supplémentaire.

`scripts/qa_unified_desktop.py` a ouvert une **vraie fenêtre Qt Windows visible**, dans un corpus inventé isolé. Réception finale : six pages visibles; brut/identités absents du prompt et de l'historique fournisseur; un envoi import+réponse; `/status` réel sans inférence; fichier modifié et test exécuté dans le même fil; code de sortie affiché; commande longue réellement interrompue; changement de fournisseur conservant le fil; navigation anglaise; candidat copié **60 cartes**; fermeture/réouverture conservant l'historique. Tous ces contrôles ont réussi.

Le contrôle du candidat après Arrêter a d'abord exposé une erreur du script QA : il réutilisait directement un callback d'annulation d'une opération terminée. Le script ouvre désormais correctement la nouvelle opération. Les étapes restantes ont été reprises depuis la fixture inventée en conservant les preuves réelles déjà obtenues, sans répéter leurs appels cloud. Ce n'est pas une réception sur les vraies parties du propriétaire.

Le parcours d'ingestion Windows existant a aussi réussi ses 14 contrôles sur données inventées : doublons exacts/sémantiques, incomplet/ambigu, volumineux, drop et fichiers nouveaux au redémarrage. Les tests de concurrence/pannes restent des reproductions synthétiques.

L'EXE local a été reconstruit après les dernières corrections. Sa réception frozen vérifie fenêtre native visible, six pages, lecture du rapport local autorisé, listes60/galerie et contrôles d'import/activité/démarrage. Les captures et données de réception restent locales. Ce constat est rapporté par l'exécuteur, pas indépendamment certifié par ChatGPT.

### Ajustements établis par les essais réels

Le Windows sandbox de `command/exec` ne résolvait pas un nom d'exécutable comme le terminal interactif : résolution du chemin par `shutil.which` avant l'appel officiel. L'exécution frontend typée évite de dépendre d'un Node REPL indisponible, tout en conservant les permissions natives de Codex. Les sous-processus possédés sont nettoyés à la fermeture; aucun processus de session externe n'est ciblé.

Le mode standard est réellement `workspace-write`, avec réseau autorisé; il ne promet pas de bloquer toutes les lectures privées du shell. Le mode complet correspond à `danger-full-access`, opt-in avec badge. Les garde-fous frontend sont distincts de la portée effective d'un shell. Le mode complet n'a pas été utilisé sur les données privées.

## Consultation locale et collecte publique autorisées

Le rapport local préexistant a été relu dans la portée du lancement. Le diagnostic en lecture seule confirme le schéma7; aucune migration7→13, création de backup, clone ou suppression exécutée. Aucun chiffre personnel, nom de fichier privé, empreinte privée, conversation, journal ou capture publié ici. Préférence d'usage cloud ordinaire mémorisée selon l'ordre propriétaire, réglage de partage existant conservé; accès complet non activé.

Une collecte publique réelle a alimenté les caches existants : **14 GET**, 13 observations révisées provenant du répertoire public de decks; elles restent **non vérifiées normativement**. Le moteur de tournois existant a ensuite effectué **5 GET**, enregistré un nouvel instantané PUBLIC avec **76 pairings admissibles**. **Winrate=null** : ceci ne prouve pas une confrontation classifiée ni la supériorité d'un deck. Ces reçus concernent des données publiques et non le corpus personnel. Les collectes et essais TCGdex restent dans l'enveloppe du mandat, sans images privées ni paramètres personnels.

La persistance après fermeture/réouverture et sans réseau est démontrée avec la fixture de recherche, dont un second processus indépendant, et par la lecture hors ligne des observations TCGdex réellement acquises. Anciennes versions conservées, refus429 sans répétition immédiate, échec de sauvegarde sans reçu mensonger, source inchangée sans doublon testés.

## CI et limites de réception

Baseline vérifiée avant lancement : HEAD de code `2e28b33fa0b58609a211840fd2046ffa953c1af7`, run40408811095 success, Windows1406/2 et Ubuntu1405/3; neuf marqueurs SHA/run et empreintes canoniques contrôlés lors de la reprise. Ce succès ne valide pas les nouveaux changements.

Les runs40441594259 et40444708846 n'ont pas démarré leurs jobs : annotation GitHub **« The job was not started because an Actions budget is preventing further use. »** Aucun résultat de test n'est déduit de cet échec externe. Facturation inchangée; aucun rerun destiné à contourner la limite. Le run du commit portant cette livraison doit être contrôlé au SHA exact après push. Si le même budget le bloque, réception CI **AWAITING_EVIDENCE**, et aucune empreinte/aucun marqueur nouveau n'est déclaré vérifié.

Ollama non installé/disponible dans cette réception : absence honnête, aucun téléchargement de modèle. Aucun contrôle Ubuntu local. Les anciennes portes V1 concernant SQLite legacy, OCR terrain, récupération opérationnelle et installation planifiée ne sont pas closes par ce mandat. Une connaissance/source sans date, classification ou légalité suffisante reste inconnue. **STOP audit indépendant, V1 NOT_RELEASE_READY.**
