# QA LOT I — Windows/Codex, I0–I7

2026-10-15 Québec. Rapport d'exécution Codex, **pas un audit indépendant**.
V1 NOT_RELEASE_READY. Branche unique `work/pm-v1-loti-windows-completion`.

## Prévol et référence

Worktree propre initialement sur H `5d27832`, aucun commit inédit par rapport aux
remotes connus, aucun fichier non suivi. Après `git fetch origin`, branche I
distante découverte,8 commits devant H, au SHA
`ff8f23d25a7dc3ed3be4fbdeab197a431fe2efbd`. Switch avec tracking et
`git pull --ff-only origin work/pm-v1-loti-windows-completion` : déjà à jour.
Aucun travail I perdu à récupérer. Aucun reset, merge ou force-push.

Instructions AGENTS, NEXT_PROMPT/PROJECT_SPEC/HANDOFF, politique d'autonomie,
plans V1/I, audit H, matrices/QA et modules/tests pertinents consultés. Prévol
status/search locaux demandé par AGENTS, puis aucun accès à la base personnelle
pendant le développement/démo/campagne I. Les citations de recherche initiale
portent notamment VOLUME 4, source 2026-10-09, `.md`, lignes 67–70; elles ne portent
pas le mandat technique, qui vient exclusivement de NEXT_PROMPT.

Machine : Windows 11, NT 10.0.26200, Python 3.13.15/SQLite 3.50.4. Baseline :
**415 passed,3 skipped,113,14 s**. Deux skips OCR absent; un skip création de
symlink sans privilège local. Compilation/hygiène/diffcheck baseline réussis.
Aucune dépendance ajoutée ni paquet installé. Schéma logiciel 13 conservé.

## Changements et régressions

- Catalogues : doublons au sein d'une page conservés au lieu de set(), erreur
  de refresh avant première page invalidant l'ancien scan, ratio refusé si durée
  de scan > 7 jours, reprise de tête modifiée reconstruisant les pages. Quatre
  scopes sets/cards EN/FR distincts des unions SQL. Tests 0/unknown/stale/futur,
  pagination/429/timeouts/reprise/404 et champs/variants/reprints hérités conservés.
- Normes : revue liée à une observation ou revue datée dans le futur rendue stale;
  aucune promotion de 200/hash/revue en assertion réglementaire. La contre-lecture
  web retourne seulement un iframe; revue entière impossible sur ces accès.
- OCR : nouveau prévol sans installation/capture/DB, sortie neutre sans chemins,
  version/SHA binaire et langues si présent; origine/PE/packs/calibration inconnus.
  Candidat exige HP, bonne langue et détail non stale. Mauvais set/numéro/HP/langue,
  champ illisible ou identité incomplète→abstention; garde H visual_certain testée.
- Récupération : `atomic_publish=false` dans le plan, limites ACL/multifichier/
  power-loss explicites; reparse Windows refusés. Panne entre backup et manifeste
  laisse un fichier non attesté conservé/inventorié; sidecars/manifeste orphelin/
  locks visibles. Suites G/H de concurrence, collisions, WAL/SHM, fsync, disque,
  hardlinks, rollback et historique 7→13 conservées. Cible existante/purge bloquées.

Une première erreur de démo provenait d'une recherche «talent» sans résultat;
remplacée par «attaque», puis dix citations vérifiées. Un test hérité attendait
le marqueur `probe` sur la sonde de reprise; il est conservé indépendamment du
redémarrage du scan. Ces corrections ont été retestées. Aucun faux succès ajouté.

## Démonstration réellement exécutée

`python -m pokemind demo --json`, sans base fournie ni réseau :44 processus CLI frais,
4 volumes/10 recherches avec citations date/extension/lignes, recherche fictive FR/EN,
2 versions de 60, comparaison/export/réimport PTCGL,3 combats distincts et réimports
idempotents, n=3,0 lien version inféré, collection/crédits inconnus, recommandations
insuffisamment étayées. Trois tours PNG annotés, correction donnant 4 révisions et
3 actives, conflit de contexte refusé, relecture SQLite dans un nouveau processus,
aucun pixel stocké. Actualisation et install/status/uninstall Windows dry-run,
cadence Toronto simulée, readiness NOT_RELEASE_READY. Espace temporaire retiré.
Ce test ne pilote pas `/clear` dans l'interface Codex; il vérifie la mémoire
durable entre processus et la présence des instructions de reprise.

Campagne publique séparée : **31 GET/34 maximum**, base publique cumulable locale;
voir LOT_I_PUBLIC_EVIDENCE. Ni donnée personnelle envoyée aux APIs/CI ni règle
nouvelle vérifiée. Prévol OCR réel : OCR_ENGINE_NOT_INSTALLED, CPU/RSS inconnus.

## Validation locale finale

**428 passed, 3 skipped en 127,19 s** sur Windows local. Treize tests de plus
que la référence; mêmes trois raisons de skip (deux moteurs OCR absents,
création de symlink sans privilège local). Aucun échec ni erreur.
La dernière revue utilise le même refus de reparse points dans la démo sous
Python 3.11, avant toute création de dossier; régression ajoutée et suite complète
relancée. Le checkpoint initial du développement est `f9f6792`; le journal Git
conserve ensuite le correctif Windows et la clôture documentaire, sur I seulement.
JUnit agrégé sous `data/local/lot-i-final-junit.xml`, non versionné.
Commandes : `python -m pytest -q --junitxml=data/local/lot-i-final-junit.xml`,
`python -m compileall -q src tests scripts`,
`python scripts/check_repo_hygiene.py`, `git diff --check`.
Hygiène relancée après staging pour inclure les nouveaux fichiers. Aucun fichier
de `data/local` suivi sauf `.gitkeep`; rapports versionnés exclusivement agrégés.

## CI du dernier HEAD — contrôle obligatoire après push

Le workflow GitHub existant Windows/Ubuntu est conservé, aucune nouvelle fonction
Linux ni test spécialisé Linux ajouté. Après le dernier commit documentaire et
push I, confirmer `git ls-remote origin refs/heads/work/pm-v1-loti-windows-completion`,
puis l'égalité du `head_sha` du run et les DEUX jobs/logs. Chaque log doit contenir
`ci_evidence=TECHNICAL_TESTS_GREEN ... sha=SHA_FINAL`, nombres/skips et succès.
Le lien final et SHA sont donnés au bilan de livraison; les preuves automatiques
liées au même SHA restent dans Actions. Ne pas prétendre placer le SHA d'un commit
dans son propre contenu, ni substituer une CI de checkpoint au dernier HEAD.

Les skips moteurs ne sont jamais présentés comme une précision OCR mesurée.
Les runners peuvent permettre le symlink refusé sur ce PC; comparer les comptes
et raisons, sans inventer ceux de la future CI. Aucun auto-VERIFIED.

## Bornes et suite

Aucune vraie capture/client/compte Pokémon, installation OCR/paquet/modèle,
planificateur OS, achat/crédit, import/migration/backup/clone/attestation/purge
personnel I. Premier usage synthétique prouvé, utilisation réelle encore partielle.
Matrice A–I exhaustive, proposition J+ sans autorisation. STOP audit ChatGPT après
publication et contrôle CI finale; aucune branche suivante créée.
