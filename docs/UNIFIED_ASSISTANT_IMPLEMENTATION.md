# Assistant unifié — intégration livrée, audit attendu

2026-10-27 Québec. Mandat `PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001`, déclenché explicitement par le propriétaire. **AWAITING_AUDIT; V1 NOT_RELEASE_READY.** Les [preuves assainies](../.orchestrator/EVIDENCE_PM-V1-UNIFIED-ASSISTANT-IMPLEMENTATION-001.md) distinguent tests, opérations Windows rapportées par l'exécuteur et CI. Le [cahier produit](UNIFIED_POKEMIND_ASSISTANT_DESIGN.md), dont §6bis sur la mémoire permanente, demeure la cible fonctionnelle.

## Utilisation

Ouvrir `dist/PokeMind/PokeMind.exe` après construction, dans le projet. Les six écrans conservent la même conversation. **Enter** envoie; **Shift+Enter** ajoute une ligne. Les amorces remplissent cette saisie. Changer de fournisseur conserve le fil et ses messages; chaque fournisseur utilise sa propre sous-session réelle, avec une session distincte pour le développement.

Coller le journal, suivi de « Pourquoi j'ai perdu? Reconstruis son deck et compare au mien. » en un seul envoi. Le parseur, l'enregistrement atomique, la déduplication, les rapports et le Learning Loop restent locaux. La question est ensuite traitée sur la partie importée ou déjà connue. Les pièces jointes `.txt`/`.log` et le glisser-déposer sont conservés. Une frontière ambiguë ou un journal incomplet ne produit pas un nouvel enregistrement validé.

Le journal brut et les identités des joueurs sont exclus du contexte automatique des fournisseurs. Le réglage **statistiques anonymisées** peut partager un extrait borné de cartes, événements, issues et listes utiles. Avec le réglage public seulement, les questions personnelles reçoivent une réponse locale. L'autorisation ordinaire Codex/Claude donnée par le propriétaire est mémorisée; les restrictions de partage existantes sont conservées.

Exemples dans le même fil :

- « Reconstruis le deck de mon dernier adversaire. » Les listes publiques compatibles de 60 cartes sont classées comme hypothèses, avec cartes observées, cartes non confirmées, sources et contradictions. Aucune référence compatible donne un résultat explicite sans inventer une liste.
- « Est-ce statistiquement plus fort actuellement? » Une recherche peut actualiser listes et pairings publics. Les placements et la popularité ne deviennent pas des winrates. Échantillon, période, plateforme, classification et incertitudes restent nécessaires.
- « Cherche les changements récents de la méta et mémorise-les. » La mémoire locale et sa fraîcheur sont consultées d'abord. Un reçu généré par l'application indique les faits ajoutés, révisés, déjà connus et non vérifiés après l'écriture réelle.
- « Prépare un deck60, puis enregistre ce candidat. » L'export est contrôlé à 60 cartes; la légalité Standard et Live est évaluée séparément quand les connaissances le permettent. Le candidat enregistré apparaît dans Deck Lab et peut être copié. Il ne remplace pas le deck joué et n'atteste ni collection, ni crédits, ni légalité inconnue.
- « Annote cette partie… » Une annotation est une hypothèse du propriétaire, datée et révisable/révocable dans le Learning Loop. Elle ne réécrit pas les cartes observées. Les questions suivantes peuvent la relire, même après redémarrage.
- « Corrige ce fichier Python de PokeMind puis lance ses tests. » Une demande explicite de développement sélectionne les outils projet dans la même conversation. Les événements, résultats et codes de sortie réels sont affichés. Une instruction dans un journal ou une sortie d'outil ne sélectionne pas ce canal.

Dans Réglages, choisir un répertoire projet **à l'intérieur du projet ouvert**. Les actions Codex utilisent le sandbox officiel `workspace-write` avec réseau pour ce répertoire. Les droits de lecture réels restent ceux du CLI et de Windows; le libellé ne promet pas une isolation privée que ce sandbox ne fournit pas. L'outil frontend de fichiers refuse notamment `data`, `.git`, `.codex`, les chemins hors projet et les alias de fichiers. Un shell possède sa propre portée effective.

**Frontière de confidentialité non résolue sous Windows.** En standard comme en accès complet, les shells peuvent lire et modifier `data/local`, puis renvoyer ce contenu au fournisseur et à son historique cloud. Un sous-dossier sans données privées ne bloque ni chemins absolus ni alias. Avant la première demande de développement, PokeMind présente cette limite et attend un choix explicite (Non par défaut), distinct du consentement cloud ordinaire. Le choix est mémorisé par fournisseur, projet et mode; les anciennes préférences ne l'activent pas. Un refus conserve le brouillon, sans démarrer le fournisseur. Le bouton **Révoquer les consentements de développement** rétablit cette demande. Le consentement ne constitue pas une isolation; une frontière OS vérifiée reste nécessaire pour une garantie d'exclusion. Voir [preuves de frontière](../.orchestrator/EVIDENCE_PM-V1-DEV-PRIVACY-BOUNDARY-001.md).

Le mode **accès complet**, analogue à l'usage volontaire `--yolo`, est un choix distinct, mémorisé et signalé en permanence. Il utilise réellement `danger-full-access`; il ne contourne pas Windows et ne doit pas être confondu avec le partage de statistiques du coach. Il n'a pas été activé sur les données personnelles pendant la réception. **Arrêter** interrompt le tour et la commande possédée; les fichiers déjà écrits sont conservés.

`/status` et « Affiche mon statut Codex. » consultent les méthodes officielles, sans génération LLM. Les champs absents restent indisponibles. `/resume` reprend la session sélectionnée. `/compact` rapporte l'acceptation de `thread/compact/start`; cette acceptation n'atteste pas à elle seule l'achèvement du compactage. Une commande slash inconnue est signalée, jamais traitée comme une question Pokémon.

Le français reste la langue par défaut. Le choix anglais adapte la navigation principale et la langue de réponse demandée au moteur. Certains libellés métier et messages historiques demeurent français; il ne s'agit pas d'une traduction exhaustive de tous les moteurs CLI.

## Contrats et réutilisation

| Liaison | Implémentation et portée |
|---|---|
| Chat persistant | `assistant/sessions.py` conserve une chronologie et des sous-sessions fournisseur/canal. Les anciens fils fournisseur sont préservés mais isolés avant réutilisation des nouveaux outils. |
| Préparation commune | `desktop/services.py` consulte le rapport existant, la partie sélectionnée, la version attestée si disponible et la mémoire publique; contexte borné selon le partage. |
| Outils métier | `assistant/tools.py` définit les arguments typés; appels vers cartes, règles, deck library, observer, analytics, collection et Learning Loop existants. Pas de SQL ni de chemin arbitraire fourni au coach. |
| Codex par défaut | App Server stdio; `dynamicTools` expérimental, méthodes qualifiées sur le CLI installé. Le coach n'obtient pas un shell arbitraire. |
| Développement Codex | `pokemind_project` relie lecture/écriture frontend et `command/exec` officiel. Les exécutables sont résolus avant l'appel Windows. `command/exec/terminate` vise uniquement le processus possédé. |
| Claude Code | Préparation métier commune; développement via les outils natifs Read/Edit/Write/Bash/Glob/Grep. Les capacités de métriques Codex ne sont pas attribuées à Claude. |
| Ollama | Adaptateur local existant, contexte préparé; service/modèle local requis. Aucun outil de développement équivalent annoncé lorsqu'il n'est pas disponible. |
| Version jouée | Correspondance du journal sélectionné puis moteur d'attestation existant en lecture seule. Sans attestation, dernière liste connue explicitement non attestée; aucune migration implicite. |
| Reconstruction | Jusqu'à trois compositions complètes sourcées compatibles; quantités minimales et alias vérifiés. Score de compatibilité distinct d'une probabilité. Impression, légalité et disponibilité Live inconnues restent inconnues. |

## Mémoire Web durable

`batch_public_research.knowledge_view` projette les instantanés et l'index PUBLIC existants. Aucun nouveau cerveau factuel ni moteur vectoriel. Chaque recherche nécessaire ouvre une enveloppe neuve; elle ne réactive pas une campagne historique fermée. Les faits sont versionnés par source et contenu; une révision conserve les versions précédentes. Les annotations personnelles utilisent les journaux Learning Loop existants, séparément des sources publiques.

Les observations incluent URL, éditeur, consultation, version/empreinte publique, ETag/Last-Modified quand exposés, licence et statut de validation. Date de publication/effet, format ou licence non établis restent inconnus. Le texte d'un LLM n'est pas une source. Le HTML dont les droits de conservation ne sont pas établis reste éphémère; seules les observations structurées admissibles sont conservées. La licence MIT des données TCGdex n'est pas attribuée aux images.

Le cache conversationnel utilise une fraîcheur de 30 jours pour les cartes et une journée pour méta/règles. Les refus source ferment les tentatives de la source/enveloppe; un contrôle quotidien évite de répéter le même refus à chaque question. L'annulation, les limites de réponse et les budgets restent explicites. L'état antérieur valide demeure consultable après panne ou hors ligne.

La recherche méta partage un plafond de 150 GET/32 Mio, avec 142 GET/16 Mio pour les pages et 8 GET de 2 Mio maximum pour le moteur de tournois existant. Aucun paramètre privé n'est accepté dans ces APIs publiques. Le contrôle des pairings pointe vers le dernier instantané PUBLIC valide et conserve les instantanés précédents. Des pairings acquis sans classification suffisante ne démontrent aucun winrate de matchup.

Documentation de référence : [Codex App Server](https://developers.openai.com/codex/app-server/), [sécurité Codex](https://developers.openai.com/codex/security/), [TCGdex](https://tcgdex.dev/), [API Limitless](https://docs.limitlesstcg.com/developer/tournaments/). Le contrat exact des méthodes a aussi été contrôlé dans les schémas générés par le CLI installé; l'interface ne suppose pas que toutes les versions exposent toutes les métriques.

## Limites conservées

SQLite personnelle ancienne non migrée; import principal historique toujours distinct du pont dérivé. Les chiffres personnels historiques ne sont pas publiés comme nouveaux. Pas de backup/clone, installation globale, nouveau scheduler, lecture d'autres projets ou automatisation du client TCG Live. Les contrôles OCR terrain, récupération opérationnelle et autres portes V1 antérieures ne sont pas résolus par cette intégration. CI au SHA final et audit indépendant restent requis. **V1 NOT_RELEASE_READY.**
