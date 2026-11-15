# Audit indépendant ChatGPT — PM-RELEASE-095-CONTROLLED-DESKTOP-INSTALL-012

Date : 2026-11-12. Dépôt privé `Sd-tech-Sol/PokeMind-dev`, branche `work/pm-v1-lotj-final-readiness-windows`.
Rapport et commit étudiés : `9f28a7897ca1e42d05cda751d4bc5fee4d99a499`; base `8c121924726d3eb08629024a062d8402a0a335a8`. Source du candidat 009 `231e6ebc9b99c2adbba95ca217287542bb3e897c`.

## Verdict

**INSTALL_EXECUTOR_EVIDENCE_ACCEPTED / GITHUB_CHANGE_SCOPE_INDEPENDENTLY_VERIFIED / INSTALLED_PENDING_OWNER_GUI_RECEPTION / NOT_RELEASE_READY.**

L'installation contrôlée du candidat 009 est **techniquement recevable sur la base des preuves consignées par Codex** et ne justifie pas un nouveau cycle de développement ou une réinstallation. **La réception fonctionnelle/visuelle par le propriétaire reste nécessaire**, car aucun agent ni ChatGPT n'a navigué le véritable EXE après l'installation. Ne pas déclarer la V1 publiée, la GUI reçue ou les données vérifiées indépendamment sur le disque.

## Vérifications indépendantes sur GitHub

- `compare 8c121924...9f28a789` : exactement **1 commit**, `ahead_by=1`, `behind_by=0`; **6 fichiers uniquement sous `.orchestrator/`** : RESULT, STATE, NEXT_ACTION, NEXT_PROMPT, HANDOFF et archive de l'ancien RESULT 011. Aucun fichier du produit, de packaging, de version, de données ni de release modifié par 012.
- `RESULT.md` du HEAD et les fichiers d'état concordent : statut `INSTALLED_PENDING_OWNER_GUI_RECEPTION`, prompt 012 `CONSUMED`, installation signalée exécutée une fois, aucune publication, aucune restauration.
- Sur le SHA exact du rapport, GitHub `statuses=[]`, `workflow_runs=[]` : **aucun statut CI vert et aucun run disponible**. Les anciens 1814 tests passés / 3 ignorés appartiennent au candidat source 009, pas à cette installation.

## Résultats Windows rapportés par Codex (non reproduits par ChatGPT)

- Prévol Setup/EXE 0.9.5 : empreintes SHA256 recalculées localement et conformes à celles précédemment auditées. Setup non signé : `ab83f9755c84ff34a3c08b8c3c978236fbfc794e20734daaf5cd51e3627feeac`. EXE de staging et installé : `25ffe17e64b8714e1ffc9fe8de17fb0ad617bbf6d0831c5c7d9bac6598114837`. AppId `{9B4E3B52-6C1D-4E7A-9F3B-5A2C8D1E7F40}`, version PE/Inno 0.9.5, raccourcis 2/2 concordants.
- Sauvegarde de l'arbre desktop **avant** installation via le module existant `data_archive.archive(root=..., dest=..., app=False, parts=None, excluded=())` : **334 fichiers / 362 046 434 octets**, ZIP **81 089 217 octets**, CRC, noms, tailles, SHA256 par fichier comparés aux originaux, source rehachée et stable. **6 bases SQLite réellement présentes**, `PRAGMA quick_check` OK en lecture seule, sans sidecar WAL/SHM/journal. **Aucun besoin d'une SQLite canonique CLI qui est absente**.
- Copie indépendante du programme précédent : **800 fichiers / 134 742 684 octets**, noms/tailles/dates/empreintes concordants. Sauvegardes locales privées protégées par ACL; aucun chemin privé, hash de fichiers personnels ou archive envoyé dans Git.
- Setup 009 exécuté **une fois**, options sans relance, exit **0**. Après installation, **797/797 fichiers** du candidat présents et conformes aux empreintes selon Codex; binaire installé correspond à 009.
- Comparaison du stockage personnel avant/après (programme fermé) : **334/334 fichiers et dossiers inchangés**, chemins/tailles/dates/SHA256 identiques, aucun ajout ou suppression constaté à ce moment. Les deux `synthetic_v2.txt/.json` sont conservés et inclus dans la protection; origine de l'incident 008 non établie.
- Aucune ouverture de PokeMind, navigation GUI, restauration, migration, purge, Coach/LLM, modification de consentement ou publication pendant cette tâche. Ces assertions portent uniquement sur le rapport de Codex.

## Limites

ChatGPT a inspecté l'historique GitHub, non le système de fichiers Windows ni les journaux privés. Le résultat de Codex est précis et cohérent, mais une vérification de SHA/SQLite/ZIP sur le PC ne peut être qualifiée d'**indépendante** ici. **Un démarrage de l'application par le propriétaire et sa vérification manuelle demeurent le contrôle d'acceptation fonctionnelle non satisfait.** Une installation réussie ne prouve pas automatiquement l'affichage des vraies cartes, la navigation ni l'absence de régression en usage.

## Action unique et décision

**Aucune nouvelle tâche Codex/Claude, aucune réinstallation, aucun rollback, aucun nettoyage.** Demander simplement au propriétaire d'ouvrir l'installation PokeMind depuis son raccourci habituel puis de vérifier un parcours minimal, sans import ni nouvelle action destructive : (1) démarrage normal, (2) présence de ses decks/journaux et préférences/consentements, (3) Deck Lab avec vraies illustrations, 2/3 colonnes et sélecteur/boutons accessibles, (4) statistiques et Coach visible. Confirmer **« tout fonctionne »** ou fournir une capture/description d'un défaut bloquant. Un problème sérieux documenté fera l'objet d'UNE correction ciblée; ne pas rouvrir les chantiers esthétiques.

Si le propriétaire valide la GUI, mettre le statut à `OWNER_GUI_ACCEPTED_CANDIDATE_009` puis demander **un GO distinct pour publication publique 0.9.5**. Ce GO n'est **pas** acquis par l'installation. Ancien programme et sauvegarde doivent demeurer conservés jusqu'à validation du propriétaire et décision explicite de rétention.
