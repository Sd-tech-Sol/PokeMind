# PM-V1-OWNER-SELECTED-MATCH-REVIEW-UX-001 — preuves de livraison

Portée **CODEX_LOCAL_REPORTED / INVENTED_MATCHES_ONLY**, à auditer par ChatGPT.
Ce rapport ne vérifie aucune donnée personnelle du PC. **V1 NOT_RELEASE_READY.**

## Prévol et autorisation

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`, arbre initial
  propre. Fetch puis pull ff-only sans perte de `1317c37` à
  `57bf4f9d16c1bdcf97fe3a22596e5d8e0d9619db`; divergence 0/1 avant pull.
- Mandat courant cohérent STATE/NEXT_ACTION/NEXT_PROMPT, READY,
  execute_now=true, consumed=false; démarrage manuel par le propriétaire.
- [CI39911865926](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39911865926)
  au SHA autorisant exact : Windows job120276476808, **995 passed/2 skipped**;
  Ubuntu job120276476513, **994 passed/3 skipped**, tous deux completed/success.
  Jobs et logs consultés. Le connecteur ne listant que les runs de PR, `gh`
  a servi à retrouver les runs de push; aucun appel fournisseur Pokémon.
- Issue #1 et audit précédent lus; aucune reprise des audits historiques.
  Prévol mémoire `RUNTIME_READY`, Python3.13.15, SQLite3.50.4, FTS5 disponible,
  owner_database_opened=false, writes_to_disk=0.

## Fonctionnalité et limites

`battle review-selected` : un fichier ou un ID, base/deck/date explicites,
dry-run ou apply obligatoire; trois consentements distincts vérifiés avant
les métadonnées. Aucune base implicite ni découverte privée. Tous les chemins
sont confinés lexicalement à `data/local`; base existante au schéma13 exigée,
absence de sidecars/liens/reparse points/liens matériels; fichier texte borné
à2Mo, encodages et partie unique reconnus. Le handle ouvert est contrôlé avant
lecture du contenu; les métadonnées sont revérifiées après la lecture.
Ce lot ne certifie pas une exclusion Windows contre un processus hostile
concurrent; les protections SQLite existantes sont réutilisées.

Assemblage des moteurs existants sans nouveau schéma/service/dépendance :
import_battle_log, attestations, Observer, conservative_sample/Matchup Analytics,
Deck Knowledge, Counter-Deck Lab, competitive_export/serializer et Learning Loop.
Le rapport fournit l'issue de la partie, cartes visibles, hypothèses/alternatives,
proxy PUBLIC distinct de l'adversaire exact, version attestée ou unknown,
statistiques historiques par version, fiches et exports60, protocole et journal
de valeurs Learning Loop. Sans cible univoque ou sans caches sélectionnés,
absence de plan signalée explicitement. Différences de construction comparées
à la base PUBLIC du Counter-Deck Lab, pas au deck personnel implicitement.

Import et attestation interdits dans la même commande. Correction de version
en deux gestes : retrait daté puis nouvelle attestation; motif conservé comme
note propriétaire datée/idempotente dans battle_lessons. Aucun changement au
schéma ni aux contraintes des attestations. Conserver Learning Loop demande
un chemin JSON explicite et le consentement d'attestation, sans écrasement;
reprise identique idempotente. Des instantanés différents demandent des chemins
différents; aucune mise à jour de fichier ou apprentissage automatique cachés.

L'importeur garde sa transaction; une panne pendant l'insertion rollback.
Une panne après commit produit PARTIAL_LOCAL_REVIEW_REQUIRED, code2, ID et
étapes déjà terminées; les analyses potentiellement antérieures sont signalées.
Réimport exact sans doublon, aucun reparse/suppression/rollback des preuves
commises. Un fichier JSON interrompu est conservé; jamais écrasé pour reprendre.

Guide : [OWNER_SELECTED_MATCH_REVIEW](../docs/OWNER_SELECTED_MATCH_REVIEW.md).
Les modèles de commandes réelles sont documentaires seulement. Aucun vrai
journal, deck, collection, crédit, base privée ou cache PUBLIC personnel
n'a été ouvert. Les catalogues et listes utilisés sont tous inventés.

## Démonstration et cas négatifs

Commande reproductible :
`python -m pytest -q -s tests/test_owner_selected_match_review.py::test_synthetic_demo`.

Scénario inventé : cinq matchs et deux versions, puis sélection d'un journal
FR, aperçu inchangé, import sans attestation, panne après commit, reprise
idempotente = six matchs. v2 attestée avec date jouée distincte de l'import,
retrait motivé/répétable, correction v1; quatre exports60 reparsés, fiches et
plan conditionnel; Learning Loop sauvegardée seulement sur demande, seconde
écriture identique évitée. Pioches cachées exclues, proxy jamais deck adverse60,
petits ratios masqués et aucune amélioration causale. Les deux caches PUBLIC
artificiels et le journal source sont contrôlés inchangés.

Régressions : absence de permission/DB/source/deck/date refusée avant I/O avec
monkeypatch qui échoue au premier accès; autorisations combinées/abusives,
chemins extérieurs/../ADS, sidecars3, hardlinks, parent redirigé sans resolve,
handle substitué, taille/extension, contrôle ASCII invalide/texte incomplet,
plusieurs parties, import inactif, schéma ancien sans migration, mauvais
deck/ID/date, doublon exact sur un autre deck, version conflictuelle,
historique avant/après retrait, issue inconnue, archétype ambigu, absence de
caches, doublon probable interparseurs sans transfert de version, échec
transactionnel puis reprise, sortie JSON interrompue et refus d'écrasement,
CLI humaine/JSON et erreurs neutres. Réseau/socket, collecte, presse-papiers,
subprocess et sélection de DB par défaut interdits dans la démonstration.

## SHA256 des registres — cause CRLF/LF confirmée

Lecture des logs de CI39910221412 au SHA1317c37 et conversion **en mémoire**
des fichiers versionnés, sans modification des registres ou revalidation web :

| Registre PUBLIC | LF = Ubuntu historique | CRLF = Windows historique |
|---|---|---|
| official_rules_2026.json | 5ccd9a85a123438c51fc01085564b6b8af7f610c4359ec981b3aa0c5fa7f9c90 | 37b367c87ecaf31d319acf776a613bf0e6a3492a3e9f0375220eb2bf69121e6e |
| official_rules_20261022.json | 1c60e2ba9e7c94442016c49101be0dd02c477b1a4a9cf0c3d17265142158dfdd | 25378df16831837b45f0125aa3267e0b5c77d5e375f463b35095be5c02a81b11 |

Empreintes canoniques attendues, indépendantes de LF/CRLF/indentation/ordre
des clés, sensibles aux valeurs et à l'ordre des tableaux :

- official_rules_2026.json :
  `6039ba349a5dcb3a0af605fb2b2834108a0c5c58b1fb5e1b610ea22cf996b7ba`.
- official_rules_20261022.json :
  `330790df14d7d5474503d04b31c29c36eddd1ba8b003736271ab82704f55e3d7`.

Algorithme interne JSON_UTF8_SORTED_KEYS_COMPACT_UNESCAPED_UNICODE_V1
réutilisant cards._canonical_sha256. L'ancien registry_sha256 des octets reste
obligatoire; registry_canonical_sha256 est ajouté et contrôlé par le publisher,
qui filtre les champs inattendus. Aucun nouveau fait normatif, ni modification
des sources officielles, ni certification rétroactive du PC/decks/Live.

## QA et preuve finale

Suite locale complète : **1049 passed/3 skipped en485,52s**; OCR non attesté2
et symlink Windows non autorisé1. **112 ciblés finaux en55,30s**, démo1pass
en14,53s; compilation/tabnanny/hygiène/diffcheck et8propriétés JUnit validés.
La suite complète a été collectée avant le garde du handle ouvert/son test,
l’affichage humain et les horloges de fixture;112ciblés valident ces derniers
ajustements. La CI finale doit collecter le code entier au SHA publié.
La démonstration Windows a aussi révélé une flèche Unicode incompatible avec
le stdout CP1252 par défaut dans son résumé; remplacement par ASCII, commande
exacte ci-dessus réussie ensuite. Aucun effet sur l'import ou les sources.

Neuf marqueurs doivent être inspectés dans **les deux logs au SHA de livraison** :
`selected_match_review_evidence`, `counter_learning_evidence`,
`deck_library_matchup_evidence`, `deck_knowledge_evidence`,
`public_deck_preflight_evidence`, `competitive_advisor_evidence`,
`competitive_pages_evidence`, `rules_registry_evidence`, `ci_evidence`.
Le nouveau marqueur est obligatoire, de portée
SYNTHETIC_OWNER_SELECTED_MATCH_REVIEW_ONLY, champs et types filtrés; absence,
doublon, preuve réelle/permission unique ou réseau autorisé refusent la
publication TECHNICAL_TESTS_GREEN. Comparer les empreintes canoniques des deux OS.

CI de livraison PENDING à l'écriture du commit; l'état durable après push se
trouve dans GitHub Actions au SHA exact de ce commit. Ne pas substituer la CI
de départ39911865926. L'exécuteur doit attendre et vérifier les deux jobs et
les neuf marqueurs avant son compte rendu final, puis STOP audit ChatGPT.

Zéro GET fournisseur, OS/jeu/compte/clipboard/OCR/scheduler/installation,
backup/migration/restauration/purge, merge ou force-push. Aucun fichier privé,
base, log brut, chemin absolu ou empreinte personnelle publié. Les empreintes
ci-dessus appartiennent uniquement aux deux registres PUBLIC versionnés.
AWAITING_AUDIT, execute_now=false, consumed=true. Aucun mandat suivant lancé;
DKI personnels et portes A–J inchangés. **V1 NOT_RELEASE_READY.**
