---
name: deck-advisor
description: Analyser un deck PokeMind, comparer ses versions, consulter collection/crédits déclarés, tirer des leçons de combats et préparer un candidat de 60 cartes sans modifier le deck joué.
---

# Conseiller un deck avec PokeMind

Utilise ce Skill pour « analyse mon deck », « propose des améliorations », « compare
deux versions », « analyse mes derniers combats », « quelles cartes me manquent? »
ou « prépare une proposition de 60 cartes ».

1. Lance `python -m pokemind capability status --json`, puis fixe explicitement le
   deck, le format, la plateforme et la date. Utilise `analyze deck`, `recommend
   deck`, `deck compare`, `battle lessons` ou `collection missing` selon la demande.
2. Cite les sources et dénominateurs retournés. Sépare règles officielles, textes de
   cartes, Limitless, déclarations du propriétaire, observations de combats et
   hypothèses. Garde `unknown` lorsqu'une identité, la légalité, la disponibilité
   Live, la collection, le tarif ou le lien combat→version manque.
3. Pour une proposition, demande un fichier privé de changements contrôlés sous
   `data/local/`, puis prévisualise avec `deck candidate-create --changes ...
   --dry-run --json`. N'applique et n'exporte qu'à la demande explicite du
   propriétaire avec `--apply --confirm-owner`. Un candidat ne devient jamais une
   version jouée automatiquement.
4. Pour une collection ou des crédits, prévisualise d'abord. Ne déduis jamais la
   possession d'un deck, d'un journal ou du catalogue; ne calcule aucun coût si le
   tarif sourcé manque. N'effectue aucun achat, fabrication ou action dans TCG Live.
5. Réponds en français (Québec) avec contexte, faits, limites, `n`, changements
   conditionnels et prochaine preuve utile. Cinq combats demeurent exploratoires.

Les formats privés et exemples de commandes sont dans `docs/LOT_B_GUIDE.md`. Ne
transmets jamais deck, collection, crédits ou combats à TCGdex, Limitless ou un autre
service.
