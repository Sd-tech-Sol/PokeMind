# PM-0003F — audit anonymisé de précision des journaux

## Verdict d'exécution

**PARTIAL_NEEDS_INPUT.** Les trois observations signalées ont été reproduites,
corrigées et retirées du profil local. Elles proviennent de **deux classes de
parsing**, pas de trois bugs indépendants : deux lignes composées « piocher puis
jouer » et une pioche de mulligan sans identité de carte. Aucun nom n'a été corrigé
par supposition et aucune liste noire n'a été ajoutée.

La réparation ciblée de la base est terminée. La réanalyse historique complète reste
partielle : 3 originaux sur 5 étaient présents et correspondaient à leur empreinte;
les 2 originaux absents n'ont pas été reconstruits ni réanalysés. Ils ne contenaient
aucune des trois observations déjà stockées et signalées, mais leur texte ne peut
plus être audité sans que l'utilisateur le fournisse de nouveau.

## Compteurs anonymisés

- Observations suspectes reproduites : **3**.
- Classes de cause prouvées : **2**.
- Observations corrigées dans les originaux vérifiés : **3**.
- Observations signalées encore suspectes après réanalyse : **0**.
- Lignes d'observation retirées/ajoutées : **3 / 2**; la troisième devient une
  action sans nom de carte et n'alimente plus `card_observations`.
- Originaux intégraux vérifiés par SHA : **3/3 disponibles**; couverture historique
  des originaux : **3/5**.
- Journaux réanalysés avec la CLI : **3**; parser `pm0003f-1`.

## Invariants et confidentialité

- Sauvegarde privée créée sous `data/local/backups/` avec `sqlite3.backup()`;
  intégrité de la sauvegarde et de la base finale : `ok`.
- Cinq identifiants de partie, résultats 4 W / 1 L, validité, deck, tours et
  horodatages historiques inchangés.
- Deck exact version 1, total 60, contenu/version et zéro association rétroactive
  inchangés.
- Aucun original, extrait identifiable, pseudo, nom de carte utilisateur, empreinte,
  chemin privé, capture, crédit ou SQLite ajouté à Git.
- Recherche locale consultée : *VOLUME 4 — ENTRAÎNEMENT, ANALYTIQUE ET PARCOURS VERS
  L'EXCELLENCE*, source du 2026-10-09, Markdown
  `source_material/markdown/04_entrainement.md:L57-L64`.

## Preuves automatisées

- Baseline : `68 passed`.
- Après correction : `73 passed`.
- Les fixtures sont synthétiques et anonymisées : FR/EN, tours numérotés/non
  numérotés, acteur adverse, lignes composées, actions sans nom de carte, W/L,
  idempotence, rollback, confidentialité et deck exact de 60 cartes inchangé.
- Contrôles finaux à consigner dans `RESULT.md`; aucune prétention `VERIFIED`.
