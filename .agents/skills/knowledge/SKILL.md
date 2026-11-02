---
name: knowledge
description: Consulter et auditer hors ligne les connaissances publiques PokeMind sur les cartes, réimpressions, règles, légalité et métagame, avec provenance et couverture explicites.
---

# Connaissances PokeMind

Utilise ce Skill pour une question sur une carte, son texte FR/EN, ses impressions,
une réimpression, la légalité datée, les règles de construction ou le métagame.

1. Lance `python -m pokemind knowledge status --json`, puis la commande locale la
   plus précise : `cards search`, `cards show`, `cards reprints`, `rules check-card`,
   `rules check-deck`, `meta coverage`, `meta archetypes` ou `meta matchups`.
2. Cite l'ID d'impression, la langue, l'URL source, la date de récupération ou de
   consultation et le contexte format/plateforme/date. Distingue toujours impression,
   identité fonctionnelle, légalité, support TCG Live, possession et métagame.
3. Réponds `unknown` lorsque le cache ou la preuve normative est incomplet. Un même
   nom n'établit jamais une équivalence de réimpression et un échantillon Limitless
   ne représente pas tout le métagame.
4. N'exécute une synchronisation réseau qu'à la demande explicite avec un budget
   borné. Prévisualise d'abord avec
   `python -m pokemind knowledge update --mode daily --dry-run --json` : ce dry-run
   ne fait ni réseau ni écriture. L'application publique exige `--apply
   --confirm-owner`; elle ne transmet jamais deck, collection, journal, crédits ou
   identifiant privé. Consulte ensuite `knowledge update status --json`.
5. Pour vérifier la qualité globale, lance
   `python -m pokemind knowledge audit --json`; ne présente pas ce diagnostic local
   comme une vérification indépendante.
6. La réconciliation profonde est mardi/vendredi en `America/Toronto`, à une heure
   configurée par le propriétaire. Le planificateur Windows reste inactif : pendant
   le LOT D, seule la prévisualisation `knowledge scheduler ... --dry-run` est
   permise; aucune installation ou activation réelle.

Le repli sans découverte du Skill est : « Lance `python -m pokemind knowledge status
--json`, puis interroge la sous-commande locale pertinente et cite ses sources. »
