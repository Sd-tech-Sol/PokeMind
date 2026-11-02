# Audit intégré des connaissances — LOT A

## Commandes hors ligne

```powershell
python -m pokemind knowledge status --json
python -m pokemind knowledge audit --json
```

Ces commandes ouvrent SQLite en lecture seule, ne migrent pas la base et ne font
aucun appel réseau. `status` sépare catalogue, traductions, réimpressions officielles,
règles de structure et instantanés Limitless. `audit` ajoute intégrité SQLite, clés
étrangères, concordance FTS5 et matrice A1–A5. Une base de schéma antérieur reçoit une
action `MIGRATE_WITH_BACKUP`; elle n'est jamais migrée implicitement par l'audit.

Les actions prioritaires donnent un nombre de GET seulement lorsqu'il est démontrable.
Les détails manquants parmi les impressions déjà découvertes ont un compte exact. La
fin d'un index sans total fournisseur reste `unknown_without_provider_total`; elle
n'est pas convertie en estimation fictive. Une synchronisation Limitless exige un
budget choisi par l'utilisateur.

## Parcours de questions

| Question | Commande locale | Preuve et limite obligatoires |
|---|---|---|
| Cherche cette carte | `cards search "nom" --lang all --json` | langue, ID d'impression et score; homonymes séparés |
| Explique son effet | `cards show ID --lang fr --json` | URL/date/langue; champ absent = `unknown` |
| Quelles impressions/réimpressions? | `cards show ID --json`, puis `cards reprints ID --as-of DATE --json` | même nom = alias de recherche, jamais preuve d'équivalence |
| Légale Standard Live au jour J? | `rules check-card ID --format standard --platform live --as-of DATE --json` | légalité, support Live et possession restent séparés |
| Mon deck respecte-t-il la structure? | `rules check-deck DECK --format standard --platform live --as-of DATE --json` | exact 60 cartes; exceptions incomplètes peuvent imposer `unknown` |
| Métagame de cet archétype? | `meta coverage ...`, puis `meta matchups --archetype ID ...` | contexte, période, `n`, dénominateur, exclusions et biais |
| Quelle source? | lire `sources`/`provenance` dans la sortie concernée | URL et date de consultation/récupération |

Le skill portable `.agents/skills/knowledge/SKILL.md` encode ce routage sans dépendre
d'une API propre à un assistant. Il interdit une sync implicite et la transmission du
deck, de la collection, des journaux, des crédits ou d'un identifiant privé.

## Interprétation

- `DONE` signifie que le mécanisme et ses tests du lot sont terminés.
- `PARTIAL_WITH_EVIDENCE` conserve un objectif dont les données ou preuves ne sont
  pas exhaustives, avec numérateur/dénominateur lorsque le dénominateur est connu.
- `BLOCKED_WITH_REASON` décrit une source inutilisable sans accès public autorisé.

Ce diagnostic est produit par le code livré; il ne remplace pas l'audit indépendant
ChatGPT et ne doit jamais être présenté comme `VERIFIED`.
