# PM-V1-SYNTHETIC-RELEASE-PREFLIGHT-001 — preuves assainies

**Publication contrôlée :** code livré `2c9966d14868b9ef294d0cac1ec2d3328d5f9e7f`, HEAD distant égal au local et worktree propre après push. [CI40499211164](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40499211164) à ce SHA exact : completed/failure, **0 étape Windows/Ubuntu**; annotations des deux jobs relues, budget Actions empêche le démarrage. Aucun test CI exécuté; **AWAITING_EVIDENCE**, sans rerun. Ce complément ne modifie que les rapports; contrôler aussi son dernier HEAD et sa CI après publication, sans succès présumé.

2026-10-27 Québec. **CODEX_LOCAL_REPORTED / AWAITING_AUDIT / V1 NOT_RELEASE_READY.** [Matrice V1](../docs/SYNTHETIC_RELEASE_PREFLIGHT.md). D-237 Option B conserve le risque de développement non isolé; aucune permission personnelle supplémentaire n'en découle.

## Déclenchement et limites

Le propriétaire a dit « go » après avoir reçu le mandat préparé. Branche propre synchronisée en fast-forward jusqu'à `911a50b4192816c9ec4e9694b7800a1dd209d6ef`; lancement IN_PROGRESS enregistré avant les essais. Aucune archive antérieure relancée. Ce lot ne lit pas la DB, les conversations, préférences, sauvegardes, journaux ou caches du propriétaire et ne remplace pas son portable.

Tous les workspaces ont été créés neufs sous `build/synthetic-release-…`, avec marqueur dédié, cartes/listes/journaux/SQLite7 et préférences inventés. Les fonctions de fixtures existantes et les moteurs PokeMind ont été réutilisés. Seuls les comptes CLI habituels ont servi pour les questions publiques ou inventées. Aucun contenu privé fourni au cloud/Git, nouvelle clé, installation globale, privilège, changement Windows, tâche planifiée, OCR du jeu, backup/clone/migration/restauration personnelle ni contrôle TCG Live. La copie de bases dans la fixture ne concerne que les bases fictives générées dans ce même workspace.

## Changements reproductibles

- `Build-PokeMindDesktop.ps1 -SyntheticQaRoot` dirige EXE, fichiers de travail et licences vers une destination dédiée vérifiée, refusant redirections et sortie déjà occupée. Les notices ne partent plus obligatoirement vers le portable du propriétaire. Aucune nouvelle dépendance installée.
- Le mode explicite `POKEMIND_DESKTOP_SMOKE=synthetic-release` valide la forme du workspace et un marqueur exact non aliasé avant construction de la fenêtre. Le harness est embarqué seulement par l'option QA de packaging. Un lancement ordinaire ne l'importe pas et ne démarre aucune QA.
- `qa_unified_desktop.py` prépare la fixture avec les constructeurs déjà présents puis exerce le **véritable MainWindow dans le véritable EXE windowed**, les fournisseurs et les écritures métier existantes. Aucun deuxième moteur ni cerveau factuel; une chronologie et une saisie dans les six pages existantes.
- Le script autonome `qa_unified_agent.py` est aligné sur le paramètre de consentement introduit au lot précédent. Son ancienne mention « protected thread » est corrigée. Il n'a pas été relancé comme campagne additionnelle.

## Réception locale Windows / portable

Python projet3.13.15, PyInstaller6.22.3, environnement desktop existant. Un build exploratoire a qualifié la destination; les builds suivants ont intégré les ajustements du harness. Chaque build a une destination neuve, sans remplacement ni nettoyage des précédents. Les derniers parcours frozen et codes de sortie sont distincts des tests pytest.

| Parcours dans la même fenêtre Windows native | Constat rapporté |
|---|---|
| Application réellement frozen, six pages et une saisie | Oui, EXE windowed construit et exécuté dans son projet fictif |
| Question Pokémon Codex | Réponse réelle, faits disponibles et limites; aucun résultat fournisseur simulé |
| Journal inventé + question en un envoi | Import local et réponse, référence de partie conservée, résumé réel n=2 dans cette fixture |
| Reconstruction60 | Variante(s) de référence sourcées; total60, `is_exact_opponent_deck=false`, probabilité absente, légalité/Live inconnus |
| Brut et identité de journal | Assertions sur le prompt et l'historique coach transmis; journal et identité inventée exclus |
| `/status` | Réponse via RPC Codex officiel, aucun appel d'inférence pour cette commande; absence éventuelle de métrique non inventée |
| Développement dans le même fil | Vraie écriture d'un fichier inventé puis commande Python avec assert et sortie0 |
| Consentement B | Vrai dialogue Qt, Non par défaut; refus conserve brouillon/historique et n'envoie rien; acceptation distincte dans la seule fixture |
| Full / révocation / autre fournisseur | Badge full visible, nouveau consentement requis pour full, après révocation et pour Claude; aucun shell full sur données réelles |
| Mémoire PUBLIC | 3 réponses de transport **inventées** (robots + deux ressources), reçu persistant et provenance, statut unverified; 0 GET réel vers ces sources |
| Changement Codex → Claude | Même chronologie, vraie réponse Claude; pas de deuxième interface ou remplacement silencieux de moteur |
| Deck Lab / presse-papiers | Export vérifié60 de la fixture; illustrations désactivées, aucune image réelle acquise |
| Fermeture/réouverture | Même ID de conversation local, historique conservé; instantanés PUBLIC relus offline avec0GET et disponibles dans le contexte conversationnel |
| SQLite7 fictive | Octets identiques avant/après; aucun passage7→13 ni import SQL principal forcé |

Les assertions natives ne certifient pas l'absence universelle d'exfiltration : elles portent sur les parcours fictifs exécutés. Les dialogues Oui de QA ne changent pas les préférences/consentements du propriétaire. D-237 reste un risque accepté du produit, **pas une isolation OS**. Ollama : diagnostic réel du loopback indique service indisponible; aucun modèle téléchargé ni succès réel revendiqué.

Les captures sont celles de notre propre fenêtre fictive, conservées localement et exclues de Git. La réception Windows et le build restent **rapportés par Codex**, non indépendamment vérifiés par ChatGPT. Le portable du propriétaire n'a pas été ouvert, reconstruit ni remplacé par ce lot; le binaire de QA n'est pas une release distribuée.

**Réserve qualitative observée à l'inspection visuelle finale :** la réponse générée au tour de recherche a indiqué qu'aucune mémorisation n'avait été effectuée, alors que le reçu canonique affichait deux observations non vérifiées réellement enregistrées. La persistance, les snapshots, le reçu et la relecture offline sont vérifiés séparément; cette formulation contradictoire n'est pas comptée comme une réception correcte de la réponse du modèle. Cause non établie par cette sonde, aucune correction de prompt non qualifiée ni succès conversationnel sur cette affirmation prétendus. Réserve explicite de la matrice pour audit indépendant.

## Corrections et essais préliminaires

La première réception source a correctement signalé l'absence de référence PUBLIC qualifiée : copier seulement les DB gardait un marqueur lié à l'ancien nom de campagne et omettait le ledger/pages. Le constructeur copie maintenant les pièces PUBLIC indexées de la seule fixture, réémet son attestation au nouveau chemin et exige un index de références valide **avant** la GUI. Une régression couvre cette préparation. Aucun filtre de provenance ni contrôle de reconstruction n'a été affaibli pour faire passer le test.

La préparation du test a aussi révélé un parent absent puis une profondeur de chemins excessive sous Windows quand deux workspaces étaient imbriqués. Le test utilise désormais le layout dédié réel et ne retire que son propre répertoire, contrôlé explicitement. Un premier run complet a été interrompu pour intégrer cette correction de fixture; il n'est pas compté comme suite réussie. Le run complet final et les tests ciblés sont rapportés séparément, sans double compte. Le champ `frozen=false` d'un parcours source n'est pas une panne fonctionnelle; seul le parcours EXE avec `frozen=true` qualifie la porte portable.

La capture finale attend le prochain cycle de peinture Qt après le dernier tour; le texte de la conversation est également vérifié comme visible/non vide. Les captures brutes et traces locales ne sont pas publiées.

## Tests et contrôles

- Prévol : RUNTIME_READY, owner_database_opened=false, writes_to_disk=0; démo : SYNTHETIC_REHEARSAL_PASSED,79processus CLI, aucun réseau et workspace temporaire retiré.
- Ciblés existants :58passés (`unified_assistant`, fournisseurs, ingestion), repris dans le total complet;3nouveaux tests de marqueur/alias/préparation/mémoire, également inclus dans le total. Leur réexécution ciblée après ajustement du harness n'augmente pas le nombre de tests distincts.
- Qt natif Windows :34passés, processus séparé du cerveau pour conserver le protocole existant.
- Suite cerveau complète finale : **1404 passed / 3 skipped**,619,09s;34Qt natif Windows réussis, soit **1438 tests distincts réussis / 3 ignorés**. Ignorés : deux attestations OCR absentes et création de symlink Windows non permise. Dernier portable QA : frozen=true, ok=true, exit0; historique visible inspecté dans la capture fictive locale. Compilation, tabnanny, hygiène et diff contrôlés au code final.
- Refus réel d'un deuxième build vers une sortie QA occupée : oui; binaire QA inchangé avant/après. Aucun contrôle du binaire du propriétaire n'a été nécessaire.

## CI et portes ouvertes

Point de départ `911a50b4192816c9ec4e9694b7800a1dd209d6ef`, [run40494978441](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40494978441) : completed/failure, zéro étape Windows/Ubuntu. Aucun test CI exécuté. CI de code et du dernier commit de publication à consulter aux SHAs exacts; **AWAITING_EVIDENCE**, aucun rerun, facturation ou fournisseur de remplacement.

SQLite personnelle legacy, sources réelles/légalité/Live, OCR terrain, récupération, tâches Windows, réception du propriétaire et audit indépendant restent des portes séparées. Aucune fixture ne les ferme. STOP après publication assainie et vérification HEAD/CI, execute_now=false et AWAITING_AUDIT.
