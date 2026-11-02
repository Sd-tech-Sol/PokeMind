# QA et preuves — LOT G

2026-10-14. Tests locaux rapportés par Codex; audit indépendant ChatGPT non fait.

## Prévol et lecture

Branche G propre et alignée avec `9ad99bbc0a893b1d4a8418828853c4598fa5c4a0`,
contrôle `git ls-remote`; aucune synchronisation ou changement de branche redondant.
NEXT_PROMPT, audit F, autonomie, plan V1, passation/actions/roadmap/décisions/spec,
docs F/readiness/mise en service, README/skills/CI et tous modules/tests imposés ont
été lus intégralement. Les historiques actifs F/PM-0006C ne supplantent pas G.

Baseline locale : **328 passed, 1 skipped** (symlink Windows non permis),
compileall, hygiène et diff check réussis. `status/search` restent en lecture seule;
la recherche technique n’a retourné aucun document. Schéma personnel observé 7;
logiciel toujours 13. Aucune migration personnelle.

## Parcours et injections

- G0 ciblé initial : 50 passed, 1 skipped. Erreurs postpublication de six classes,
  création/remplacement **synthétique** interne, contrôle octet pour octet, rollback
  refusé avec quarantaine intacte, source/manifeste préservés.
- Writer après gate, collision au lien dur, WAL/SHM/journal créés durant préparation,
  session idle ou transactionnelle et WAL sans sidecar : public apply existant
  fermé et clone neuf publié sans écrasement. Mutation externe postpublication :
  cible incertaine conservée avec `RESTORE_ROLLBACK_INCOMPLETE`.
- Manifestes hostiles absolus/relatifs/types invalides; inventaire >1000 refusé;
  keep_last sain revalidé pendant staging; erreur unlink conserve un comptage exact
  des couples détruits et artefacts restants. Purge multifichier non atomique.
- G1 ciblé : 32 passed, 1 skipped OCR absent. Cadres/glyphes/compteurs synthétiques,
  provider TSV simulé, FR Unicode NFC/CRLF, zoom/cadrage et faux noms/HP, ambiguïtés
  et scores invalides. Aucun benchmark de reconnaissance réelle déclaré.
- G2 ciblé : 90 passed. Stale, quotas/reprise initiale, normes datées, sources
  non verified/futures et queue de review sans promotion. Campagne publique
  distincte : `LOT_G_PUBLIC_EVIDENCE.md`, 4 GET TCGdex et 2 GET Limitless.
- G3 E2E : vraie structure **synthétique** schema7 sans tables futures→clone13,
  historiques documents/sections/catalogue/deck/combats octet logiquement identiques,
  intégrité/FK et MATCH FTS. Texte FTS faux à comptes identiques refusé.
- G4 : flags superficiellement verts ne passent pas règles/Live/vision/scheduler/
  restore/audit; n=1 insuffisant; collection/crédits facultatifs non bloquants;
  SQLite corrompue fail-closed et aucune valeur privée dans readiness.

## Clôture locale et CI

Suite complète finale locale : **388 passed, 2 skipped en 85,23 s Windows**.
Skips explicites : OCR absent et création symlink non permise.
`python -m compileall -q src tests scripts`,
`python scripts/check_repo_hygiene.py`, `git diff --check` requis à la clôture.
Les avertissements de normalisation LF→CRLF sont distincts d’un échec diff check.

Durcissement G0 de l’auto-revue finale : une fixture a démontré qu’un fichier de
backup en WAL pouvait avoir SHA principal inchangé tout en étant annoncé verified.
Le correctif refuse WAL/SHM/journal/header côté backup, normalise le snapshot de
copie en DELETE et réatteste contenu/manifeste après les vérifications SQLite.
Quatre tests supplémentaires : WAL non haché refusé, snapshot autonome d’une source
active WAL, variations du contenu et du manifeste pendant vérification refusées.
Ciblé récupération/E2E/readiness : **64 passed, 1 skip** Windows. La nouvelle suite
complète et sa CI de HEAD remplacent le précédent résultat comme preuve de clôture.

La CI Windows/Ubuntu reste hors ligne sur fixtures. Elle génère un JUnit local au
runner, puis `scripts/write_ci_evidence.py` écrit dans le résumé GitHub de chaque
job : SHA exact, OS, tests passés/skips, run et `TECHNICAL_TESTS_GREEN`. Aucun chemin
personnel, montant, carte privée ou image dans cette preuve. Les logs explicitent
les skips. Le HEAD de clôture doit être contrôlé par Actions, pas par un run F ni
par le simple statut conventionnel `statuses:[]`.

La référence définitive de CI du commit final se trouve sur GitHub Actions et dans
les deux résumés de jobs générés **pour ce SHA**, avec résultats agrégés. Le rapport
terminal donne son lien après observation effective. Aucun auto-audit Codex ne
devient un audit ChatGPT, et aucune CI verte ne rend la V1 prête.

### Run de code directement observé, distinct de la clôture documentaire

[`38598030240`](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/38598030240),
SHA `2bf0b7e218360b91fceb6f7ebf71ac683c4ecfa5` : API Actions `completed/success`,
job Ubuntu `115969705202` et job Windows `115969705752` success. Logs directement
consultés : **385 passed, 1 skipped** sur chacun. Le skip est OCR absent;
la création de symlinks passe sur les deux runners, contrairement au Windows local.
Les résumés générés publient ce même SHA. Le commit documentaire suivant doit
également avoir sa propre CI finale; cette référence n’est pas un substitut.
