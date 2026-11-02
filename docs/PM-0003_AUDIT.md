# Audit PM-0003 — exports de deck et Skill Codex (2026-10-10)

## Portée et conclusion

L'audit est ciblé : syntaxe publique d'exports Pokémon TCG Live/Online et mécanisme
de Skills de la version locale de Codex. Aucun catalogue de cartes, contrôle de
légalité, scraping massif ou export privé utilisateur n'a été consulté.

**DECK_FORMAT_NOT_FIELD_VALIDATED** : le parseur est vérifié avec des fixtures
synthétiques anonymisées, mais aucun export réel de deck de l'utilisateur n'était
disponible ni autorisé pendant cette tranche. La validation terrain reste donc à
faire lors du premier import privé, sans publier son contenu.

## Provenance des formes acceptées

- Export Live courant : le projet public MIT
  [`pokemon-tcg-deck-list-generator`](https://github.com/TheLandolorien/pokemon-tcg-deck-list-generator/blob/main/src/pokemon_tcg_deck_list_generator/main.py)
  (consulté le 2026-10-10) traite les sections `Trainer: N` et `Energy: N`, la
  première section étant Pokémon, et des lignes `quantité nom CODE numéro`.
- Export historique Pokémon TCG Online : les tests publics MIT de
  [`ptcgo-parser`](https://github.com/Hamatti/ptcgo-parser/blob/master/spec/parser.spec.js)
  (consultés le 2026-10-10) montrent les bannières, `##Pokémon - N`,
  `##Trainer Cards - N`, `##Energy - N`, l'astérisque facultatif et
  `Total Cards - N`.
- Les formes françaises `Dresseur`, `Énergie` et `Total de cartes` sont prises en
  charge de façon conservatrice pour l'interface française. Elles sont testées avec
  des données synthétiques Unicode, mais ne sont pas déclarées validées sur un export
  utilisateur réel.

Le parseur exige trois sections exactement, compare chaque total annoncé aux
quantités lues et exige 60 cartes. Le pied `Total Cards/Total de cartes` est vérifié
s'il est présent. Les noms restent des chaînes non résolues : code d'extension et
numéro de collection sont conservés lorsqu'ils sont reconnaissables, sans inventer
le nom de l'édition. Deux impressions d'un même nom restent distinctes.

## Stockage et migration

Le schéma SQLite 3 ajoute `deck_versions`, `deck_version_cards` et la table
d'association explicite `battle_deck_versions`. Les versions sont immuables et
dédoublonnées par empreinte canonique de liste; une liste réordonnée ne crée pas une
nouvelle version. La provenance, la date, l'approbation/prise d'effet, SHA de
l'export, SHA canonique, lignes normalisées et numéros de ligne source sont stockés.
Le texte brut et les images ne le sont pas.

La migration ne modifie ni `battle_logs.deck_id`, ni les issues W/L, ni les fiches
`observé partiellement`. Aucune entrée `battle_deck_versions` n'est créée à l'import
d'un deck : une future association demanderait une approbation et une date de prise
d'effet explicites.

## Codex et découverte du Skill

- Installation locale : `codex-cli 0.162.1`.
- Documentation officielle OpenAI consultée le 2026-10-10 :
  [`Build skills`](https://developers.openai.com/codex/skills). Elle confirme le
  fichier `SKILL.md`, le balayage de `$REPO_ROOT/.agents/skills` et l'invocation
  explicite `$skill`.
- Test local sans appel de modèle :
  `codex debug prompt-input '$combat importe le dernier combat et conseille-moi'`
  retourne code 0 et expose `combat` depuis la racine de Skill du dépôt.
- Le validateur fourni par `skill-creator` n'a pas pu démarrer, car `PyYAML` n'est
  pas installé. Aucune dépendance n'a été ajoutée pour contourner ce point; le
  frontmatter minimal a plutôt été confirmé par la découverte native de Codex.

Le Skill appelle uniquement les CLI existantes, ne lit le presse-papiers qu'après
demande explicite, n'interagit pas avec le client et garde les recommandations
exploratoires à partir de `n >= 5`.

## Référence interne consultée

La recherche locale `importer deck 60 cartes journal combat` a notamment retourné
*VOLUME 4 — ENTRAÎNEMENT, ANALYTIQUE ET PARCOURS VERS L'EXCELLENCE*, source
2026-10-09, Markdown, `source_material/markdown/04_entrainement.md:L57-L64` sur
l'exploitation prudente des journaux, ainsi que le même document `L8-L15` sur la
revue après-partie.
