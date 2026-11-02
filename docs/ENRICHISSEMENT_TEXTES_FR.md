# Textes français publiés — complément du catalogue occidental

2026-10-22, `PM-V1-FRENCH-TEXT-ENRICHMENT-001`. Résultat local rapporté par
Codex, **AWAITING_AUDIT**; V1 **NOT_RELEASE_READY**. Demande propriétaire :
seulement du français déjà publié et sourcé; aucune traduction créée par l'agent.

Le [catalogue TCGdex épinglé](CATALOGUE_TCGDEX_SNAPSHOT.md) garde ses valeurs,
statuts natifs `present/absent`, reçus et compteurs. Poképédia fournit des
compléments distincts pour les champs français absents avec valeur EN connue.

| Champs FR | Lacunes initiales | Compléments publiés | Lacunes restantes |
|---|---:|---:|---:|
| Descriptions de Pokémon | 9 681 | 9 605 | 76 |
| Noms de carte | 1 672 | 1 584 | 88 |
| Noms et effets d'attaques | 4 045 | 3 497 | 548 |
| Noms et effets de talents/pouvoirs | 599 | 521 | 78 |
| Effets de Dresseur/Énergie | 240 | 232 | 8 |
| Total de champs | 16 237 | 15 439 | 798 |

L'inventaire concernait 10 712 cartes. **10 556 cartes** reçoivent des compléments;
**395 cartes** gardent au moins une de ces lacunes. Un nom d'attaque et son effet
comptent deux champs. Les descriptions sont les paragraphes descriptifs des Pokémon,
distincts de leurs attaques. Les champs sans valeur EN connue sont hors dénominateur.
Toutes les cartes ne sont donc pas devenues entièrement françaises.

## Source et attribution

Source primaire : [Poképédia](https://www.pokepedia.fr/), API publique MediaWiki.
Les [droits d'auteur](https://www.pokepedia.fr/Pok%C3%A9p%C3%A9dia%3ADroits_d%27auteur)
prévoient **CC BY-NC-SA 3.0 France** : attribution, usage non commercial et partage
des adaptations sous la même licence. Notice complète conservée localement;
la licence TCGdex ne remplace pas celle de ces compléments. Aucun corpus ou texte
réel de carte n'est publié dans le dépôt de code.

Chaque champ garde URL de révision, historique des auteurs, numéro et date de
révision, réception locale, empreinte de réponse, paramètre wiki et licence.
`french_text_supplements.fields` distingue :

- `published_french_transcription` : 10 798 champs transcrits sur une page française;
- `published_community_translation` : 4 567 traductions déjà publiées comme telles;
- `published_parallel_description` : 74 descriptions d'une autre impression avec
  exactement le même paragraphe anglais et les mêmes identifiants nationaux du
  Pokémon; l'impression de référence est indiquée.

Les références parallèles concernent uniquement les descriptions. Elles ne prouvent
aucune équivalence de réimpression, attaque, règle ou légalité. Toutes les catégories
portent `official_text_verified=false` et `french_printing_proven=false` : la
transcription communautaire n'est pas une vérification de l'image officielle FR.

## Consultation hors ligne

Le seul cache enrichi est la base PUBLIC existante, hors Git :

```powershell
$cataloguePublic = 'data/local/public-campaigns/lot-i-catalog-snapshot-20261022/public.sqlite3'
python -m pokemind cards coverage --db $cataloguePublic --json
python -m pokemind cards search Pikachu --lang fr --db $cataloguePublic --json
python -m pokemind cards show ecard3-1 --lang fr --db $cataloguePublic --json
```

`cards show` remplit seulement les champs manquants et ajoute la provenance;
le statut natif peut rester `absent`. `cards search` peut retourner
`text_source=attributed_french_supplement`. `cards coverage` sépare les comptes
natifs et `french_text_supplements`. Ces derniers comptent les champs stockés;
la fraîcheur est revérifiée à chaque fiche/recherche. Un changement du payload
original invalide l'affichage du complément.

L'import Python est manuel et contrôlé, sans téléchargement implicite ou périodique.
Aucun complément n'est ajouté à la base personnelle; decks, parties et collection
n'ont pas été consultés. Les correspondances exigent extension, numéro, identité
et PV concordants lorsque disponibles. Les attaques exigent un nom concordant ou
une signature coût/dégâts unique; aucun appariement par simple rang.

L'acquisition cible les extensions occidentales, dont Pocket séparé de TCG Live.
Aucune carte d'extension japonaise ni champ japonais n'est importé. Les champs
japonais et liens interlangues de certaines pages brutes sont ignorés; aucune
valeur ajoutée ne contient d'écriture japonaise. Les ambiguïtés, modèles inconnus
et contradictions restent inconnus plutôt que forcés.

Les **798 champs** restants ne sont pas résolus par ce corpus; cela ne prouve
pas leur absence sur tout Internet. Aucune ancienne collecte ni API TCGdex relancée.
Budgets clos. [Preuves assainies](../.orchestrator/EVIDENCE_PM-V1-FRENCH-TEXT-ENRICHMENT-001.md).
