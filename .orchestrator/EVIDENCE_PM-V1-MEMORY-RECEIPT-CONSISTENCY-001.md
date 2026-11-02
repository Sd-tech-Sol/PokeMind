# PM-V1-MEMORY-RECEIPT-CONSISTENCY-001 — preuves assainies

**Publication contrôlée :** code livré `5a72a0d897e6707e9df66f8ccdbaff6b489eeea8`, HEAD distant égal au local et worktree propre après push. [CI40505943526](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40505943526) à ce SHA exact : completed/failure, **0 étape Windows et 0 étape Ubuntu**. SHA de chaque job et annotations des deux jobs relus : budget Actions empêche leur démarrage, aucun test CI exécuté. **AWAITING_EVIDENCE**, sans rerun. Ce complément est documentaire seulement; contrôler également son dernier HEAD et sa CI après push, sans succès présumé.

2026-10-27 Québec. **CODEX_LOCAL_REPORTED / AWAITING_AUDIT; V1 NOT_RELEASE_READY.** Départ synchronisé en fast-forward seulement : `696824fffb0cd9e416f01d9d6184f769ec5dd34d`, branche `work/pm-v1-lotj-final-readiness-windows`. Ordre manuel explicite du propriétaire; aucune archive relancée. Réception finale du portable : **PASS_LOCAL_SYNTHETIC_ONLY**, exit0.

## Défaut reproduit avant correction

Un fournisseur factice retourne « Rien n'a été mémorisé. » alors que le moteur retourne `persisted=true, added=2, unverified=2`. Le nouveau test Qt a d'abord **échoué sur l'ancien code** : la transcription et son contenu sauvegardé associaient ce déni à « 2 faits ajoutés ». Cette reproduction déterministe distingue le problème d'affichage de la réussite réelle du stockage. La cause précise des choix de mots du fournisseur réel n'est pas établie.

## Contrat de réponse corrigé

- Pour un tour de recherche, l'application présente un **résumé déterministe du reçu local**, à la place de tout commentaire généré. Ce remplacement est annoncé dans le message. Le commentaire du modèle n'est ni diffusé dans ce tour ni ajouté à l'historique local; la substitution et le reçu sont conservés dans le même message de la conversation existante. Les réponses ordinaires et les vrais outils de développement gardent leur fonctionnement.
- Les comptes, états et URL proviennent du reçu du moteur. `persisted=false`, résultat inconnu, compte invalide ou reçu incohérent ne permettent pas d'annoncer une écriture réussie. Un cache affiche explicitement zéro nouvelle écriture, même s'il contient des observations utilisables hors ligne.
- Le texte distingue **enregistrement local**, **validation sur la source**, **utilisation par le modèle** et **disponibilité hors ligne**. Un contexte transmis n'atteste pas son utilisation; une observation enregistrée n'est pas une règle validée, actuelle ou légale dans Live.
- Un échec de collecte conserve un résultat d'écriture non confirmé, sans inventer un rollback. Une panne ou interruption du fournisseur après un reçu positif conserve les écritures attestées et annonce l'interruption ou l'indisponibilité séparément.
- Une tentative de recherche par le fournisseur réutilise le reçu de préparation. Elle ne relance pas une collecte et ne remplace pas le reçu positif par un cache hit. Le reçu courant est réinitialisé entre les tours et commandes officielles.
- `memory_receipt` est une projection dans le **fil existant**, pas une seconde base factuelle : état, comptes, sources et nombre d'observations offline. Les snapshots PUBLIC et le Learning Loop existants demeurent les seuls moteurs factuels. Aucun changement de schéma.

La solution ne dépend d'aucune détection générale du langage ni d'un prompt plus insistant. Les anciens historiques personnels ne sont pas ouverts ou réécrits. Le fournisseur peut conserver un récit imparfait dans sa propre session; ce récit n'est pas publié comme résultat de mémorisation par PokeMind.

## Tests et couverture

| Contrôle | Résultat local rapporté |
|---|---|
| Contre-exemple déterministe avant correctif | Échec attendu, déni + reçu positif visibles ensemble |
| Ciblés initiaux, dont Qt natif | 83 passed; inclus dans les totaux, sans double compte |
| Suite complète cerveau, processus distinct | **1409 passed / 3 skipped**, 593,64 s |
| Suite Qt finale Windows native, après correction de rendu | **54 passed / 0 skipped**, 28,60 s |
| Recontrôle final services et harness après ajustements de QA | 30 passed; déjà inclus dans le total cerveau |
| Total distinct | **1463 passed / 3 skipped; 25 nouveaux tests** |
| Prévol technique | RUNTIME_READY; aucune DB propriétaire ouverte, aucun réseau, zéro écriture |
| Démo synthétique | SYNTHETIC_REHEARSAL_PASSED, 79 processus CLI, aucun réseau |
| Compilation / tabnanny / diff / hygiène | Contrôlés avant publication; aucun artefact privé préparé pour Git |

La suite cerveau et les tests Qt sont séparés selon le protocole existant. Le dernier raffinement de défilement concerne seulement la vue Qt : les 54 tests Qt ont tous été réexécutés après ce changement, ainsi que les 30 tests services/harness; les fonctions du cerveau sont inchangées par ce raffinement. Les trois exclusions restent : deux contrôles OCR non installés/non attestés et un test de lien symbolique non permis sur cette machine Windows. Elles ne sont pas transformées en succès.

La couverture vérifie réponses **sauvegardées et rendues**, streaming écarté, sources réelles du reçu, `SAVED`, `PARTIAL`, `CACHE_FRESH`, `OFFLINE_STALE_OR_EMPTY` vide et non vide, `SOURCE_COOLDOWN`, `persisted=false`, erreur, interruption, `added=0` et `added>0`, `unverified>0`, faux comptes, changement Codex/Claude, réponse ordinaire, fermeture/réouverture et absence de deuxième recherche. Les tests antérieurs de refus cloud/développement, de consentement fournisseur/projet/mode, de révocation et de journal exclu du cloud sont réexécutés.

## Portable et réception visuelle

Tous les builds utilisent une **nouvelle destination QA marquée**, créée par le préparateur synthétique existant. Le portable personnel n'est ni ciblé, ouvert ni remplacé. Aucun nettoyage des anciennes sorties QA. Python projet 3.13.15 et PyInstaller 6.22.3 existants, aucune nouvelle dépendance installée.

Les deux premières réceptions passent les assertions de texte, stockage et reprise, mais leurs captures montrent un viewport de conversation vide. Elles **ne constituent pas une réception visuelle acceptée**. Le diagnostic sur la seule fixture montre une borne de défilement encore liée à l'ancien HTML, au-delà du texte réel. Le rendu déplace maintenant le curseur à la fin du nouveau document avant de rendre la position visible. Un contrôle de peinture du viewport complète les assertions de texte. La QA capture aussi le tour mémoire lui-même, après peinture native, plutôt qu'un dernier tour sans rapport avec la mémorisation.

Réception finale : **frozen=true, ok=true, exit0**, porte `memory_response_consistency=true`, conservation après fermeture et relecture offline sans nouveau GET. La capture native du reçu a été inspectée : état SAVED, 2 faits ajoutés, 2 non vérifiés, deux observations disponibles hors ligne et validation/utilisation non attestées explicitement visibles. Même chronologie Codex→Claude, statut officiel sans inférence, consentement/refus/révocation et vrais outils dev dans le projet fictif, hypothèse60 non certaine, sources inconnues et SQLite7 fictive inchangée. Trois appels de transport inventé (robots et deux ressources), **zéro GET réel de collecte**.

Le commentaire réel reconnaît deux sources enregistrées non vérifiées : aucun nouveau déni de stockage observé. **Son récit de collecte demeure faux/incomplet** puisqu'il nie une nouvelle recherche malgré le transport synthétique effectué. Ce commentaire est intégralement écarté comme prévu; seule la cohérence du **résultat hôte** est reçue. Aucune affirmation de qualité générale du narratif du modèle. Les captures, commentaires du fournisseur, JUnit et traces fictives restent locaux et ignorés par Git. Les comptes-rendus de Windows et de l'EXE sont rapportés par l'exécuteur, sans vérification indépendante du PC par ChatGPT.

Le harness vérifie le même reçu dans le message final, la transcription, le fichier sauvegardé et la reprise. Une ancienne réponse suffixée d'un compteur échoue à la porte. Un déni de mémorisation connu du fournisseur réel fait explicitement échouer `memory_response_consistency`, même avec un reçu positif; ce détecteur est un filet de QA pour le cas démontré, pas le mécanisme de sécurité du produit. Les assertions et la lecture humaine du commentaire réel sont séparées du résultat hôte.

## Confidentialité et limites

Données PUBLIC entièrement inventées, cartes/deck60/journal/SQLite7 et préférences fictifs, transports de sources remplacés par les réponses synthétiques du harness. Aucun nouveau GET réel de collecte. Les clients Codex et Claude existants servent uniquement aux tours publics ou inventés autorisés. Aucun journal personnel, préférence réelle, compte Pokémon, sauvegarde, clone, migration, OCR réel, client du jeu, automatisation OS ou changement de facturation ciblé. L'Option B reste **ISOLATION_UNRESOLVED_OPTION_B**; les tests de consentement ne certifient pas une exclusion OS du privé.

Le résultat hôte cohérent ne certifie pas la qualité générale des récits du modèle, les sources réelles, la légalité, les données personnelles ni la release. Les portes terrain et permissions distinctes de la [matrice V1](../docs/SYNTHETIC_RELEASE_PREFLIGHT.md) demeurent ouvertes.

## Publication et CI

CI de départ [40500536005](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40500536005), au SHA `696824fffb0cd9e416f01d9d6184f769ec5dd34d` : échec avant démarrage des deux jobs. Annotations Windows et Ubuntu relues : budget Actions empêche l'exécution. Aucun test CI. L'outil connecté de liste des runs filtre les événements pull_request; la liste des runs push est donc consultée par `gh`, puis les jobs et annotations par les interfaces GitHub disponibles.

CI de code relevée ci-dessus au SHA exact : échec sans démarrage. **AWAITING_EVIDENCE**. La CI du HEAD documentaire final reste à contrôler après son push, sans succès présumé. Aucun rerun, désactivation, contournement ou changement de facturation. Contrôle final du HEAD distant et du worktree requis. Après livraison : **AWAITING_AUDIT, execute_now=false, STOP audit indépendant ChatGPT**, aucune nouvelle exécution autorisée.
