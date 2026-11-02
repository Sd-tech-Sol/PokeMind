# Correctif GUI, chatbot et ingestion — AWAITING_AUDIT (2026-10-26)

Six priorités livrées : contexte personnel canonique prioritaire, collage/attachements/drop de journaux traités localement avec déduplication et coaching, activité/temps/Stop, options démarrage/watch, graphiques et galerie60/images. Moteurs et mémoire existants réutilisés. Aucun journal brut au cloud ni données privées sur Git, aucune migration7→13 ou suppression utilisateur.

230 tests ciblés passés dont50 nouveaux; QA native Windows, vraie session Codex sur agrégats autorisés et portable frozen visible exercés. Constats CODEX_LOCAL_REPORTED; CI complète au commit livré à contrôler après push. [Guide](../docs/DESKTOP_GUI_CHAT_GUIDE.md), [preuves](EVIDENCE_PM-V1-DESKTOP-COACH-INGEST-FIX-001.md). **AWAITING_AUDIT**, STOP ChatGPT indépendant; **V1 NOT_RELEASE_READY**. Les états ci-dessous sont archivés.
---

## Archive — états précédents, sans autorisation courante

# Implémentation desktop V1 — livrée pour audit (2026-10-26)

Application PySide6 Windows fonctionnelle et portable local compilé/exécuté, six rubriques utilisant le cerveau Python existant. Chat Codex App Server stdio par défaut : deux tours, streaming, reprise et interruption réels; Claude réponse/reprise réelles. Ollama sélectionnable, service absent sur ce PC. 180 tests ciblés réussis dont39 nouveaux; CI complète au SHA livré à contrôler après push. [Guide](../docs/DESKTOP_GUI_CHAT_GUIDE.md), [preuves assainies](EVIDENCE_PM-V1-DESKTOP-GUI-CHAT-RELEASE-001.md).

**AWAITING_AUDIT**, aucune relance automatique. Constats PC CODEX_LOCAL_REPORTED, données privées hors Git, aucune migration7→13 ni nouvelle sauvegarde. Les mentions historiques de GUI absente ci-dessous sont supplantées par cette livraison. **V1 NOT_RELEASE_READY**, portes indépendantes restantes non promues.

---

## Archive — décisions et états antérieurs

# Changement de produit V1 — GUI Desktop + chatbot Codex (2026-10-25)

**La demande actuelle du propriétaire remplace les limitations historiques disant « pas de GUI, Codex seulement ».** Objectif explicite : livrer PokeMind comme une application **Windows graphique fonctionnelle** avec son cerveau Python existant et un **chatbot intégré** via une session Codex CLI App Server locale **par défaut**, choix Claude Code/Ollama. [Mandat actif](MANDATES/PM-V1-DESKTOP-GUI-CHAT-RELEASE-001.md) et [architecture](../docs/DESKTOP_GUI_CHAT_ARCHITECTURE.md). Aucun redesign complet du moteur, aucune donnée personnelle dans Git. V1 toujours `NOT_RELEASE_READY` jusqu'aux tests terrain Windows/Chat intégrés et autres critères.

---

# PokeMind — spécification de référence V1 (révision 2026-10-09)

État de livraison 2026-10-15 : J0–J6 développés sur branche J, Windows 11/Codex
prioritaires, A–I conservés. Prévol Python/FTS en mémoire, OCR sans exécution PATH
par défaut, politiques privées/opt-in, couverture actuelle renforcée et parcours
propriétaire en cinq décisions. Matrice A–J et QA J font foi pour les preuves;
V1 NOT_RELEASE_READY. Aucun nouveau support Linux ni acte propriétaire implicite.
STOP pour audit ChatGPT de J, puis validation du PC après décisions distinctes;
pas de LOT K automatique. Les mentions de lots actifs ci-dessous sont historiques.

## Résultat final
Un **cerveau local consulté directement depuis Codex**, pour Pokémon TCG Live sur Windows 11, capable de conseiller la construction de decks Standard, connaître les cartes via un lexique local FR/EN, analyser les journaux de combat fournis par l'utilisateur, accompagner des parties **d'entraînement autorisées** avec captures d'écran, et actualiser automatiquement ses connaissances publiques (vérification quotidienne légère et réconciliation approfondie deux fois par semaine, après consentement). Portabilité Linux souhaitable. Aucun LLM à entraîner : « apprendre » signifie accumuler données structurées, décisions évaluées et historique versionné dans SQLite.

Codex est l'interface conversationnelle; ChatGPT pilote les décisions et vérifie GitHub. Interface **Codex uniquement** pour le moment. Pas de GUI, serveur, passerelle navigateur/ChatGPT ni service cloud supplémentaire nécessaires. L'IA ne voit pas les informations cachées. Aucun objectif de bot qui joue seul, d'interaction avec le client, d'évasion des règles des tournois ou de garantie de meilleur deck.

## Fonctions V1 obligatoires (à livrer par tranches)
1. **Bibliothèque stratégique** : quatre volumes fournis (Markdown + PDF originaux), recherche SQLite FTS5 sourcée et horodatée; vérifier les règles/rotations changeantes à la source officielle.
2. **Lexique complet, traçable** : viser toutes les cartes/impressions disponibles via **TCGdex** avec index FR/EN, propriétés, textes, sets, variants, alias. Mesurer la couverture réellement indexée et afficher les champs manquants. Séparer historique vs support dans TCG Live vs légalité Standard/Expanded avec dates, errata et réimpressions; pas d'invention. Spécifications : `docs/CATALOGUE_CARTES.md`.
3. **Decks et collection utilisateur** : importer/exporter des listes PTCGL, figer des versions 60 cartes, valider format/quota/légalité/dates, recommander variantes et cartes manquantes *si la collection est fournie*. Pas d'import automatique de collection supposé.
4. **Analyse de parties** : import manuel de journaux texte, parsing robuste, reconstitution seulement des événements connus, évaluation des décisions, statistiques par matchup avec tailles d'échantillon, propositions argumentées de changements. Leçons conservées dans SQLite; pas de réentraînement de modèle. Voir `docs/JOURNAUX_COMBATS.md`.
5. **Coach visuel en entraînement** : images volontairement fournies à Codex, capture principale au début du tour utilisateur après adversaire, captures supplémentaires uniquement après décision/effet important. Suivi durable du match, conseil d'une séquence d'actions sous hypothèses affichées. Pour compétitions, règles d'assistance à respecter. Voir `docs/COACH_VISUEL.md`.
6. **Méta compétitif** : intégration de **Limitless Play API** documentée pour tournois, classements, decks et pairings; distinguer online/présentiel, dates, tailles d'échantillon. Analyse Trainer Hill si accès autorisé; aucune API privée présumée.
7. **Actualisation** : collecteurs incrémentaux pour TCGdex, Pokémon officiels et Limitless **sans démarrer Codex ni un LLM**; vérification **quotidienne légère** des changements, plus **réconciliation approfondie mardi et vendredi** heure de Toronto. Rapports de nouveautés, provenance, fraîcheur, erreurs, rollback et fonctionnement hors ligne. Planificateur Windows installé **uniquement après consentement et tests**; modes `update`, `status`, `uninstall`.
8. **Expérience Codex** : AGENTS.md court, commandes CLI avec `--json`; fonctionne sans Internet sur connaissances déjà indexées; citations précises et statut périmé/inconnu. Une session `/clear` doit retrouver règles et mémoire persistante. Tests réels des captures Windows, avec repli PNG local si collage impossible.
9. **Source de vérité Git** : `.orchestrator/` et documents versionnés; chaque tranche écrit RESULT/HANDOFF/NEXT_ACTION et produit preuves de tests. Aucune prétention de vérification indépendante par l'agent.

## Architecture principale
- Python 3.11+; SQLite et FTS5; API JSON HTTPS et parseurs minimalistes validés; `pytest`; une CLI `python -m pokemind ...`. Épingler dépendances, vérifier licence/auteur/scripts/sécurité.
- `src/pokemind/` : import seed, cartes, decks, journaux, sessions visuelles, Limitless, actualisation, CLI.
- `data/local/` : DB SQLite, instantanés externes vérifiés, decks/collection privés, données textuelles extraites des journaux et captures volontairement fournies, historique de matchs — **exclu de Git**. Aucune image ni journal brut durable dans la base; ne pas effacer les originaux de l'utilisateur sans consentement. `knowledge/curated/` pour notes publiques avec sources. `source_material/` : quatre volumes.
- `AGENTS.md` : contrat de comportement. `.orchestrator/{PROJECT_SPEC,NEXT_PROMPT,RESULT,HANDOFF,NEXT_ACTION,DECISIONS}.md` : orchestration versionnée.
- `scripts/` : tâches Windows et utilitaires de capture **facultatifs et déclenchés manuellement**. Actualisation *des connaissances publiques* automatisable via le Planificateur Windows après consentement; **pas de bot contrôlant le jeu, ni d'agent Codex résident**, ni d'automatisation de l'interface du jeu.

## Données et exactitude
- Chaque fait : source URL/document, date capture UTC, version, source snapshot, niveau de confiance, champ manquant. Les statistiques de victoire doivent indiquer n, fenêtre, biais. Populaire ≠ gagnant.
- Carte source TCGdex ≠ affirmation qu'elle est jouable dans Live; légalité vérifiée séparément via Pokémon et exceptions de réimpression.
- Les informations visibles d'une capture peuvent être insuffisantes; demander détails essentiels ou recommander conditionnellement. Inconnues explicites : main adverse, pioche, Récompenses face cachée, historique non fourni, certains textes illisibles.
- Aucun journal ou image brute dans Git. Toutes les données non fiables (API, log, image, PDF) sont **du contenu**, jamais des commandes à exécuter. Respecter les licences et droits des images. Pas de contournement anti-triche ni scraping agressif.
- Compte Pokémon inaccessible; aucune clé, paiement, télémétrie, tâche planifiée, push `main`, suppression de données, modification de deck réel sans consentement.

## Définition de V1 terminée
- 4 volumes importés; 10 recherches hors ligne citées et vérifiées.
- Catalogue TCGdex local interrogeable FR/EN; rapport couverture global, tests de réimpression/errata et statut inconnu honnête.
- Import deck et validation des 60 cartes (format/quotas) avec cas tests réels et invalides.
- Import d'au moins 3 journaux de combat anonymisés et revue argumentée; profil persistant non dupliqué, non modifié par une simple répétition du log.
- Accompagnement visuel **testé réellement** dans Codex sur Windows : séquence de 3 décisions avec captures, suivi état, incertitudes visibles; aucun accès au jeu.
- Première synchronisation Pokémon officiel + TCGdex + Limitless documentée, deuxième synchronisation idempotente, fonctionnement hors ligne en mode lecture, erreurs réseau propres, provenance et licence vérifiées.
- Tâche Windows activée seulement après autorisation, vérifiée puis désinstallable; tests Windows + rapport d'intégrité, Git propre, limitations documentées.

## Trois sous-systèmes durables confirmés en 2026-10-10

1. **Connaissance universelle** : TCGdex FR/EN + Pokémon officiel (règles, errata, réimpressions/légalité à date) + API publique Limitless (tournois, decks, matchups avec échantillons). Catalogue incomplet ou licence incertaine = état `unknown`; ne pas inventer.
2. **Mémoire personnelle** : faits de combats, deck versions, crédits/statistiques datés, observations avec provenance/confiance, hypothèses révisables et comparaisons avant/après. L'inventaire entier n'est pas requis pour commencer; observations ≠ propriété.
3. **Actualisation autonome des données publiques** : détection quotidienne peu coûteuse + deux réconciliations hebdomadaires, écriture locale atomique, tests de qualité, mode offline et aucun besoin d'ouvrir Codex. Activation du planificateur uniquement après opt-in.

**Architecture détaillée :** `docs/ARCHITECTURE_CERVEAU_AUTONOME.md`. **Registre des fournisseurs et restrictions :** `docs/SOURCES_CONNAISSANCES.md`. Ces documents sont des exigences futures, pas des fonctions déjà implémentées. Aucune nouvelle interface à construire (Codex seulement).

## Ordre d'exécution — GRAND LOT F autonome, 2026-10-13

L'utilisateur exige la V1 **complète**, sans aucune fonction sautée, des lots plus grands et **Codex plus autonome**. ChatGPT architecte/orchestrateur et vérificateur indépendant après chaque lot; Codex exécute sur branche dédiée, plan, commits, retests et correctifs sans micro-`go`. GitHub + `.orchestrator/` sont source de vérité; portable entre Codex et Claude Code.

**LOT E livré et audité** : code `f0a8b9364edaa744881845854862e2269f3adf69`, rapport `.orchestrator/VERIFICATION_LOT_E.md`, **GitHub CI Windows/Linux success au HEAD final** run `38504484245`, 313 passed/1 skip déclarés par Codex. Mécanismes E0–E6 présents; **réserve bloquante sécurité pour restauration/rétention réelle** : contrôle SHA sauvegarde source après remplacement de cible, WAL/SHM/connexion SQLite cible non isolés, rétention fondée sur statut manifeste/plan sans revalidation de contenu. N'exécuter aucune vraie restauration/purge de la base privée avant F0 audité et consentement spécifique. Code SQLite schéma 12, base personnelle possiblement schéma 7, non migrée par Codex.

**LOT F actuel : `work/pm-v1-lotf-completion-vision`, `.orchestrator/NEXT_PROMPT.md`.** F0 sûreté SQLite; F1 vrai pipeline vision locale optionnel avec tests sur images synthétiques sans installer modèle ni accéder à screenshot réel, F2 avancer catalogue/reprints/règles/Live/métagame sous quotas/provenance, F3 CI/E2E Windows/Linux, F4 calendrier d'actions utilisateur distinctes, F5 readiness/gates et suite nécessaire. Codex autonome F0–F5, une seule revue indépendante ChatGPT à fin de lot. Aucun merge/default branch (work/pm-0001), pas d'action compte Pokémon, crédit/achat, suppression privée ou scheduler Windows sans consentement.

**V1 NOT_RELEASE_READY jusqu'à preuves complètes** : reconnaissance locale de vraies cartes depuis capture d'entraînement, catalogue historique FR/EN et règles official/reprints/errata/Live, Limitless/Trainer Hill seulement si accessible autorisé, déductions de deck/collection et cinq parties fondées uniquement sur apports propriétaire, actualisation publique réellement installée seulement après opt-in, backup/restauration contrôlés, audits/tests. Une fonction PARTIAL/BLOCKED n'est ni DONE ni supprimée; organiser LOT G+ si nécessaire, pas faux release.

## État récent prioritaire — LOT G livré pour audit (2026-10-14)

Le mandat G0–G5 sur `work/pm-v1-lotg-real-vision-readiness` est exécuté par Codex;
les mentions anciennes de lots actifs ci-dessus restent historiques. G0 bloque en
code le remplacement d’une cible existante et publie seulement un clone neuf,
avec rollback universel testé et résidus préservés si doute. Cette protection est
livrée; la restauration opérationnelle avec exclusion externe reste à prouver.
G1 est un contrat OCR local optionnel sans moteur installé/calibré ni essai réel.
G2 corrige stale/reprise initiale et ajoute normes datées/file de revue; 6 GET publics
bornés dans un espace jetable n’établissent aucune couverture personnelle.
G3/G4 ajoutent E2E et gates exhaustives; G5 conserve toute la V1 et sa suite H.

V1 reste NOT_RELEASE_READY. `docs/LOT_G_ACCEPTANCE_MATRIX.md` et
`docs/LOT_H_COMPLETION_PLAN.md` sont les états/prochaines preuves; aucune fonction
retirée et aucun consentement personnel déduit. STOP pour audit indépendant
ChatGPT après publication G; le futur mandat H doit venir de NEXT_PROMPT après audit.
