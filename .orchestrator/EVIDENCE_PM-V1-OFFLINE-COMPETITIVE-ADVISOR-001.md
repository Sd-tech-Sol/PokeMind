# PM-V1-OFFLINE-COMPETITIVE-ADVISOR-001 — preuves assainies

Exécution manuelle propriétaire,22octobre2026 Québec. V1 NOT_RELEASE_READY.
Les observations sur le cache réel sont **CODEX_LOCAL_REPORTED**;GitHub prouve
les mécanismes et fixtures synthétiques exécutés au SHA de livraison,aucun
inventaire indépendant du PC. Pages/listes complètes,sorties détaillées et
empreintes du cache restent hors Git. Aucun chemin absolu ou nom de joueur
dans ce rapport.

## Prévol

- Branche autorisée `work/pm-v1-lotj-final-readiness-windows`,arbre initial propre.
  Fetch/pull ff-only sans perte de d9e6fda vers
  `ba21871bb8e680dffefebe3474ba284d3ade5f25`. Mandat/STATE/NEXT_ACTION READY
  concordants,ordre manuel reçu,aucun go intermédiaire demandé.
- [CI39876752969](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/39876752969)
  au SHA ba21871 :Windows120164422235,773passed/2skipped;
  Ubuntu120164422494,772passed/3skipped;deux jobs completed/success et marqueurs
  `ci_evidence`/`competitive_pages_evidence` lus avant travail fonctionnel.
- Prévol runtime sans DB personnelle :Python3.13.15,SQLite3.50.4,FTS5 prêt.
  Le rapport antérieur désigne explicitement le cache PUBLIC déjà acquis;
  contrôle lecture seule initial :2événements/32placements,intégritéok/FK0.

## Exigences et résultat

| Exigence | État de portée | Preuve et limites |
|---|---|---|
| A—architecture/prévol | DONE | CI exacte et sync sûres;extension de `competitive.py`,parseur `decks`,identité des `candidates`,`deck_exports.serialize_deck`,connexion PUBLIC lecture seule etCLI existante;aucun nouveau moteur/dépendance |
| B—inventaire distinct | DONE / CODEX_LOCAL_REPORTED |32placements/28compositions/15étiquettes sur2événements;URL réutilisées et compositions identiques sous URL différentes regroupées;dates,éventail de placements et sources conservés |
| B—comparaison60/60 | DONE / CODEX_LOCAL_REPORTED | Dragapult581:1→Basic Box582:1 :15copies partagées,45retirées,45ajoutées;références581:1/582:5 identiques :60/0/0;identité exacte,équivalences inconnues |
| B—shortlist2–4 options | DONE / CODEX_LOCAL_REPORTED |4compositions distinctes :Dragapult581:1,Basic Box582:13,Hydrapple581:7,Dhelmise581:4;familles diverses etmédoïde non pondéré par les placements,aucun score de force |
| B—faits/hypothèses/export | DONE | Sections/Énergies etstades trouvés dans textes déjà cachés séparés des hypothèses;matchups/winrate/BO1/BO3/Live/collection/crédits/compatibilité inconnus;4exports séparés,reparsés60cartes,sans jeu/presse-papiers |
| B—CLI humain/JSON | DONE | Trois nouvelles commandes `competitive-inventory`,`competitive-compare`,`competitive-shortlist`;`--db` PUBLIC etdate obligatoires;JSON sans texte complet de liste,limite de détails explicite et totaux complets |
| C—sources etnon-mutation | DONE / CODEX_LOCAL_REPORTED | Événements,index Standard,listes etempreintes PUBLIC recontrôlés dans les pages déjà présentes;50fichiers PUBLIC identiques avant/après les vraies commandes;sources ambiguës écartées,cache manquant/schéma incomplet bloqués sans réparation/migration |
| C—tests etCI | DONE_LOCAL_QA / PENDING_DELIVERY_CI_AT_COMMIT |99ciblés verts;suite complète804passed/3skipped en325,00s,compilation/hygiène/diffcheck OK;CI de livraison au HEAD exact à lire après push |
| D—publication/STOP | AWAITING_AUDIT | RESULT/HANDOFF/NEXT_ACTION/STATE/NEXT_PROMPT fermés ensemble,permissions consommées;commit/push des seules pièces assainies puis contrôle CI,aucun autre mandat lancé |

## Validation locale du vrai CLI, strictement hors ligne

Appels réels `competitive-inventory`,`competitive-compare`,`competitive-shortlist`
avec le chemin PUBLIC explicite du rapport précédent. Pendant ces appels,
`socket.create_connection`,`socket.socket.connect`,`urllib.request.urlopen`,
le constructeur `BoundedPages`,`connect_writable`,`_db_for` etle résolveur par
défaut sont remplacés par des refus. **Zéro appel interdit observé**.

Le contrôle avant/après couvre le fichierSQLite PUBLIC,son marqueur,son journal
de requêtes etles corps de pages référencés :**50fichiers inchangés**. Les
empreintes etsorties détaillées restent locales;aucune liste de fichiers ou
empreinte réelle copiée dans Git. Les preuves QA etquatre exports sont écrits
dans un nouveau dossier de sortie distinct,à l'extérieur du cache existant.
Les nouvelles commandes elles-mêmes ne créent ni ne modifient de fichier.

Résultats assainis :2événements,32placements valides,28compositions,
0anomalie de provenance détectée. Comparaison principale15/45/45 etpaire
réutilisée60/0/0. La shortlist descriptive donne les sections :
Dragapult19/32/9,Basic Box20/26/14,Hydrapple21/25/14,Dhelmise25/28/7
(Pokémon/Dresseurs/Énergies). Différences depuis la base :respectivement
60/0/0,16/44/44,15/45/45,20/40/40. Quatre exports reparsés à60cartes.
Voir [guide pratique](../docs/OFFLINE_COMPETITIVE_ADVISOR.md).

Ces mesures ne constituent ni des taux de victoire,ni des matchs,ni une preuve
de disponibilité Live,carte possédée ou légalité. Les stades absents des textes
cachés restent inconnus. Aucun nouveau conseil privé ou changement de deck joué.

## Fiabilité reproductible dans Git/CI

- Source de données limitée par namespace PUBLIC,marqueur,absence de tables
  personnelles peuplées,contrôles reparse/hardlink et lectureSQLite `query_only`.
  Aucun appel au client réseau,aucune initialisation/migration de cache.
- Lecture de pages mutualisée par `cached_page`,sans construire `BoundedPages`
  qui peut gérer un journal de collecte. Relecture d'index/date/format/placement,
  empreinte/instant de collecte etliste source60cartes avant admission.
- Identité de candidat réutilisée pour nom/set/numéro;type etquantité dans la
  composition. Tri indépendant de l'ordre des lignes. Réimpressions/langues
  non fusionnées par supposition. Conflits de noms/types ou familles signalés.
- Comparaison par copies :partagées+retirées=60 etpartagées+ajoutées=60.
  Troncature d'affichage déclarée sans tronquer les totaux;référence demandée
  distincte de la référence canonique d'une composition réutilisée.
- Shortlist :famille Dragapult etalternatives distinctes;médoïde par différences
  de copies sur les compositions uniques,égalité départagée par identité stable.
  Aucun poids de placement ni classement de force. Inconnues systématiques.
- Tests surpages/listes entièrement inventées :déduplication d'URL etcontenu,
  normalisation/ordre/impressions distinctes,variation de quantité,60cartes,
  sources corrompues/ambiguës/futures,schéma incomplet,absence de fallback privé,
  CLI humain/JSON,limites,troncature,base valide,cache inchangé,réseau interdit,
  invariance du représentant quand des placements d'une autre variante sont
  répétés,métadonnées personnelles fictives jamais publiées.
- Propriété JUnit `public_competitive_advisor_reproduction` issue du vrai test
  d'intégration inventé :6placements→4compositions,comparaison59/1/1,
  4options,export/non-mutation etinconnues. Publieur CI fail-closed si preuve
  absente/dupliquée,comptage faux,mutation/réseau autorisé ou cache réel promu.
  Sortie `competitive_advisor_evidence` au SHA exact;anciens marqueurs conservés.

## Limites et arrêt

**Budget fournisseur/Web0 respecté** :aucun GET,API,navigateur,robots ou nouvelle
collecte. Les accès GitHub de synchronisation/publication/contrôle CI sont ceux
exigés par le protocole de livraison;aucun appel fournisseur n'en découle.
Ancienne campagne Limitless close etnon rouverte,aucun reliquat réutilisé.

Le cache comprend des top16 publiés etdes résultats de phase2;ni échantillon
aléatoire,ni tous les participants,ni dénominateur de victoires. La classification
des familles vient des sources etles plans de jeu restent conditionnels. La
comparaison d'impressions n'est pas une attestation des éditions physiques jouées
ou de leur équivalence. Les autres objectifs V1 restent entiers.

Aucun accès à une DB/deck/collection/journal personnels;aucune capture,OCR,
client jeu,compte,crédits,OS/scheduler,installation,service,backup,migration,
restauration,purge,merge,reset ouforce-push. Le test historique PTCGL n'est pas
répété. V1 NOT_RELEASE_READY;aucun VERIFIED autoattribué.

Après push :vérifier le HEAD distant etles **deux jobs CI au SHA exact contenant
ce rapport**,avec `competitive_advisor_evidence`,`competitive_pages_evidence`,
`rules_registry_evidence` et`ci_evidence`. Ne pas substituer le prévol à la CI
de livraison. Puis AWAITING_AUDIT/STOP pour ChatGPT indépendant.

## QA locale finale etCI de livraison

**804passed/3skipped en325,00s**,Python3.13.15,99tests ciblés verts. Deux skips
OCR réel non autorisé/attesté etun symlink non permis surce Windows :aucune
réussite matérielle déduite. Compilation src/tests/scripts,hygiène Git et
`git diff --check` corrects. Le JUnit final contient une preuve advisor unique,
une preuve compétitive antérieure etune preuve des registres officiels.

CI finale **PENDING_AT_COMMIT** :elle sera créée par le push. Le résultat
durable de chaque job est dans GitHub Actions au SHA exact de livraison;les
rapports ne substituent pas la CI de prévol. Contrôler HEAD distant,conclusions
etlogs des deux OS avant l'arrêt de l'exécuteur. Aucun statut VERIFIED attribué
par Codex;cache du PC toujours CODEX_LOCAL_REPORTED,aucun autre mandat lancé.
