# PM-0005B-R2 — audit de scopes et reprise Limitless

**Date :** 2026-10-12

**Commit fonctionnel Codex :** `064ffb6f84184561a8b4fd8b9f34ab415b44cd87`

**Portée :** correctif synthétique hors ligne, sans requête Limitless réelle ni
migration SQLite.

## Référence locale consultée

Le cerveau rappelle que Limitless est une source de résultats et de scouting, pas une
autorité de légalité ni un recensement exhaustif : *VOLUME 3 — DECKBUILDING,
MÉTAGAME ET SCOUTING 2026*, source du 2026-10-09, Markdown
`source_material/markdown/03_decks_meta.md`, lignes 63–70 et 173–185.

## Reproduction avant correction

Les nouvelles régressions ont d'abord été exécutées contre R1. Résultat : **9 échecs**.

- D1 : trois transitions de filtre (online, plateforme, format), une exclusion privée
  devenue publique et une ancienne ligne `tournament:ID` échouaient : le second run ne
  demandait pas `details`, ou `refresh` n'avait aucun candidat.
- D2 : les scénarios à 36 snapshots connus ne disposaient d'aucun état `discovery` et
  recommençaient à la tête; l'interruption et le 429 n'avaient aucun checkpoint profond
  vérifiable.

Les échecs ont été conservés dans la sortie locale de test, sans donnée réelle ni accès
réseau. Les fixtures utilisent seulement des IDs, participants et URL synthétiques.

## Correction D1 — exclusions scoppées

- Scope exact : `discovery:PTCG:<FORMAT>:<PLATFORM>:<0|1>`.
- Les exclusions sont enregistrées dans `meta_sync_state` sous
  `<scope>:tournament:<ID>`. Seules les exclusions du scope courant sont terminales.
- Les anciennes lignes R1 `tournament:ID` restent intactes pour compatibilité, mais ne
  sont plus lues comme preuve universelle.
- Un snapshot `complete` est connu globalement par ID. Un snapshot devenu `partial`
  peut être reconsidéré dans un autre contexte après revalidation.
- `refresh` réunit les snapshots du filtre et les exclusions scoppées les plus
  anciennes. Une source corrigée peut ainsi être recontrôlée manuellement, sans boucle
  permanente en mode découverte.
- `details` reste validé avant `standings` et `pairings`; un tournoi privé ou
  incompatible n'entraîne aucun GET de participants.

## Correction D2 — progression persistante

- Un JSON minimal dans la table `metadata` existante conserve `next_page`,
  `horizon_page` et `pending_page` par scope. Aucun schéma 8 n'est requis.
- Une session normale sonde la page 1, relit une page de chevauchement, puis reprend le
  curseur profond. Une page n'est avancée qu'après traitement complet.
- Une coupure de budget au milieu d'un candidat fixe `pending_page`; la prochaine
  session reprend directement cette page, ce qui évite la stagnation avec un budget de
  5 GET. Les erreurs/429 ne remettent jamais le curseur à 1.
- Une page finale vide ou partielle reste la frontière à revisiter. Les doublons entre
  pages et les insertions en tête sont dédupliqués sans casser le curseur profond.
- La sortie JSON expose scope, page initiale/suivante, page en attente, pages demandées
  et horizon observé.

La pagination fournisseur peut bouger entre deux GET et ne forme pas un instantané
atomique. La tête, le chevauchement et la revisite réduisent le risque d'omission, mais
ne prouvent jamais une exhaustivité globale.

## Preuves reproductibles

`tests/test_meta.py` contient **43 tests** Limitless. Les nouveaux cas couvrent :

- `online true → false` et `false → true`, plateformes et formats différents;
- ancienne exclusion non scoppée, tournoi strictement privé et source devenue publique;
- 36 IDs complets, page de 6, nouvel ID en page 7, budgets de 8 puis de 5 GET;
- insertion en tête pendant la reprise profonde, chevauchement et doublon inter-page;
- arrêt pendant un snapshot, frontière vide/partielle puis ajout ultérieur;
- 429 sans remise à zéro et refresh d'un autre filtre sans altérer le checkpoint;
- conservation des tests R1 : confidentialité, redirects, RateLimit, refresh `partial`,
  budgets, payloads et agrégats hors ligne.

Résultats Codex après correction : **171 tests réussis**, `compileall` réussi et
`git diff --check` réussi. Aucun appel réseau Limitless n'a été effectué.

## Confidentialité et intégrité

- Schéma privé maintenu à 7; aucun backup ou migration nécessaire pour R2.
- Base réelle contrôlée en lecture seule avant/après : intégrité `ok`, 4 documents,
  87 sections, 5 combats, 1 deck exact/version de 60 cartes, 1 snapshot Limitless.
- Checkpoints : numéros de page et contexte public seulement. Aucun nom, pseudo, pays,
  handle, decklist, HMAC, collection, crédit ou vrai ID participant n'est ajouté à Git.
- Arbre suivi audité avant livraison; `data/local/`, SQLite, backups, captures, journaux
  et listes de deck demeurent hors Git.

Cette livraison attend l'audit indépendant ChatGPT et ne se déclare pas `VERIFIED`.
