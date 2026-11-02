# Plan d’exécution — LOT E

Date : 2026-10-13. Branche exclusive :
`work/pm-v1-lote-reliability-release`.

Le lot utilise uniquement des fixtures sous `data/local/test-runs`. La base
personnelle demeure en lecture seule : aucune migration, restauration, purge,
capture réelle ou donnée propriétaire n’est appliquée. Le planificateur Windows
reste bloqué par son verrou logiciel et aucun appel d’installation n’est permis.

## E0 — réserves LOT D

1. Conserver le client TCGdex/Limitless réellement utilisé afin de compter chaque
   GET déjà débité même si le collecteur lève ensuite une exception. Les sorties ne
   reprennent jamais le texte technique de cette exception.
2. Refuser tout manifeste basé sur l’horloge locale Windows tant que le fuseau
   observé n’est pas explicitement `Eastern Standard Time`, équivalent Windows de
   `America/Toronto`. Les simulations hors fuseau échouent sans contact scheduler.
3. Transmettre `DeepTime` du manifeste au lanceur puis `--deep-time` à Python. Une
   échéance profonde terminée porte sa date Toronto et empêche un doublon; après
   arrêt de la machine, seule la plus récente échéance manquée est rattrapée.

## E1–E2 — reprise après incident et durabilité

- Ajouter `backup plan/create/status/verify`, `restore plan/verify/apply` et une
  prévisualisation de rétention. Une action exige `--apply --confirm-owner`.
- Employer `sqlite3.backup()`, un fichier temporaire borné, validation
  intégrité/FK/FTS5, checksum et manifeste sans chemin source ni secret, puis rename
  atomique. Vérifier une restauration sur clone, y compris ancien schéma migré.
- Contrôler espace libre, taille, permissions, liens symboliques, fichiers verrouillés,
  concurrence et verrou stale encore détenu par un processus vivant. En cas d’échec,
  conserver le backup source et restaurer atomiquement la cible mise en quarantaine.
- La rétention reste preview-first et ne touche que des artefacts reconnus; les
  attestations, données normatives et preuves de provenance SQLite ne sont jamais purgées.

## E3–E5 — sécurité, QA et complétude honnête

- Centraliser le caviardage des erreurs CLI et tester chemins, noms et jetons
  synthétiques. Réauditer allowlists, traversées, symlinks, tailles et mode offline.
- Ajouter CI Windows/Linux à permissions minimales, contrôle d’hygiène Git,
  compileall, pytest et E2E synthétique restauration/sécurité/parcours V1.
- Exposer l’état des backends vision locaux optionnels sans téléchargement ni cloud.
  Faute de bibliothèque/modèle disponible, garder la reconnaissance réelle
  `PARTIAL_WITH_EVIDENCE` et documenter l’installation/test futur avec consentement.
- Mesurer sans inventer les restes catalogue/réimpressions/règles/méta, Trainer Hill,
  scheduler opt-in, collection/crédits et attestations propriétaire.

## E6 — clôture et portes release

Publier la matrice A–E complète, le rapport de préparation V1, le guide FR Québec et
les fichiers d’orchestration. Chaque exigence reçoit `DONE`,
`PARTIAL_WITH_EVIDENCE` ou `BLOCKED_WITH_REASON`, avec test, preuve, reste et tranche
post-E. Le statut global demeure `NOT_RELEASE_READY` tant que la vision réelle et les
autres portes fondamentales ne sont pas prouvées. Plusieurs commits sont poussés sur
la branche du lot, puis arrêt pour audit indépendant ChatGPT.

## Checkpoints

1. E0 et tests de protocole.
2. E1–E2 sauvegarde, restauration, rétention et tests de panne.
3. E3–E5 caviardage, diagnostics, CI et E2E.
4. E6 documentation, audits finaux, preuves et passation.
