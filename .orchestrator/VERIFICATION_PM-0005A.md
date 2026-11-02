# VERIFICATION_PM-0005A — audit indépendant ChatGPT (2026-10-11)

## Verdict
**CORRECTION CIBLÉE REQUISE avant de marquer PM-0005A VERIFIED.** Le socle de règles officielles datées est effectivement livré et les sources principales correspondent à l'annonce Pokémon 2026. Mais le contrôle de légalité du deck peut produire un faux verdict positif si la structure du deck n'est pas validée; le moteur accepte aussi des assertions dites « verified » provenant de documents explicitement « non_verified » ou « navigation_only ». Une tranche PM-0005A-R1 doit fermer ces deux chemins sans étendre la portée à Limitless.

## GitHub contrôlé directement
- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0005a-official-rules`, commit Codex **`29afffd911cb3f357730e51e2736acc2bf4dbd79`**, parent préparé `e0a14c5ca9ddb67529c0c764a5a23806e11b57b0`.
- **Un commit en avance, zéro en retard; 19 fichiers changés.** Nouveaux `src/pokemind/rules.py`, `tests/test_rules.py`, `knowledge/curated/official_rules_2026.json`; modification additive `database.py` schéma 6; CLI et documents.
- Revue directe : déclarations JSON des 13 sources, 6 assertions, code des imports, évaluations par date/plateforme et lecture du deck, migration SQLite, tests synthétiques, RESULT/HANDOFF/AUDIT.
- Arbre complet GitHub **111 entrées, truncated=false**, aucun fichier SQLite, journaux personnels, images, sauvegarde ou deck réel suivi; seulement métadonnées de sources publiques.
- Zéro statut CI, zéro workflow PR retourné au HEAD. **99 tests verts** (93 baseline), migration réelle/integrity `ok`, 4 volumes/87 sections, 5 parties et deck confirmé 60 cartes inchangés sont **déclarés par Codex**, pas réexécutés ni observés directement par ChatGPT.
- GitHub : default branch `work/pm-0001`, pas de `main` vérifiable; aucune fusion effectuée.

## Points conformes, à préserver
1. Registre public court sourcé, dates/effets et validation explicites, sans copier manuels/PDF protégés; lecture et chargement hors ligne.
2. Rotation Standard 2026 : la source officielle Pokémon indique marques H/I/J, changement **Live 2026-03-26** et **présentiel 2026-04-10**, exceptions de réimpression; le code borne les assertions temporellement plutôt que d'extrapoler 2027. Voir https://www.pokemon.com/uk/news/2026-pokemon-tcg-standard-format-rotation-announcement.
3. Medicham V (Sword & Shield—Evolving Skies 083/203, 185/203, 186/203), restrictions Expanded actives dès 2026-04-10 selon https://www.pokemon.com/uk/play-pokemon/about/mega-evolution/mega-evolution-perfect-order-banned-list-and-rule-changes-announcement. Pas de mappage fictif des IDs officiels vers ceux TCGdex.
4. Verdict conservateur `unknown` si carte introuvable/identité de réimpression manquante/couverture des bannissements incomplète; Expanded Live et propriété/fabrication séparés.
5. Schéma 6 additif et sauvegarde avant migration existante; tests de migration/restauration synthétiques inclus.
6. Aucun collecteur Limitless, achat, planificateur Windows, modification du jeu ni mode GUI/serveur.

## DÉFAUT 1 — le verdict deck `legal` peut être faux
**Code : `src/pokemind/rules.py`, `check_deck` (environ lignes 376–426).**

- La requête `SELECT id, version_number, total_cards FROM deck_versions WHERE deck_id=? ORDER BY version_number DESC LIMIT 1` **ne filtre pas `exact_confirmed=1`**. Pourtant la commande et la documentation prétendent lire uniquement la « dernière version exacte ».
- Le résultat global est calculé uniquement d'après les statuts cartes : `"legal" if statuses and all(s == "legal" for s in statuses) else "unknown"` (sauf `not_legal`). La fonction **ne valide ni `total_cards == 60`, ni somme des quantités, ni limite de copies par nom, ni présence d'au moins un Pokémon de base, ni les exceptions pertinentes**.
- Contre-exemple théorique déduit du code : une version de 1 carte non confirmée, avec une impression individuelle évaluée `legal` par une source de couverture complète, serait déclarée deck `legal`; de même, un deck synthétique de 60 copies d'un Pokémon ayant lui-même le statut `legal`. Or les règles de construction exigent normalement exactement 60 cartes, maximum 4 exemplaires du même nom hors Énergie de base et au moins un Pokémon de base. Source primaire historique : https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/rulebook/pal_rulebook_en.pdf ; appliquer les exceptions/cas actuels seulement après lecture officielle vérifiée.
- **Le test `test_partial_real_registry_never_false_legal_and_deck_is_read_only` n'exerce que `unknown`**, et crée paradoxalement une ligne synthétique de quantité 60; aucun test de `check_deck` sur toutes cartes individuellement `legal`, mais deck non valide.
- **Correction demandée :** ne jamais déclarer le deck global `legal` si `exact_confirmed` est faux ou si la validité structurelle/quotas de copies/bases/format n'est pas prouvée. Soit appliquer un validateur officiel adapté avec tests et gestion explicite des exceptions, soit retourner `unknown` et `DECK_STRUCTURE_NOT_VERIFIED` (recommandé pour un correctif minimal). Une carte individuellement `not_legal` peut suffire à déclarer un deck `not_legal`, mais ne doit masquer les autres inconnues de structure.

## DÉFAUT 2 — assertion « verified » rattachable à une source non vérifiée
**Code : `src/pokemind/rules.py`, `load_official_registry` (environ lignes 71–174) et `check_card` (253–376).**

- Le validateur vérifie que `assertion.source_id` existe, et que l'assertion possède un `validation_status` permis; il **n'impose aucune cohérence** entre `assertion.validation_status='verified'` et `official_rule_sources.validation_status`.
- Lors de `check_card`, la sélection `restriction`, `rotation`, `reprint_equivalence` et `restriction_coverage` se fonde sur l'assertion `verified`, **sans vérifier la validation de la source JOIN**. Un registre JSON fourni explicitement pourrait donc créer une couverture prétendue complète rattachée à un `official_navigation_portal` ou `official_pdf` déclaré `non_verified`, puis obtenir un faux `legal` pour une carte à marque admissible.
- Le registre livré ne semble pas utiliser cette combinaison : c'est un **risque réel du contrat d'import/versionnement futur**, pas la preuve d'un faux verdict déjà produit sur le deck de l'utilisateur.
- **Correction demandée :** empêcher ou neutraliser tout verdict normatif fondé uniquement sur une source `navigation_only`, `non_verified` ou `conflict`; fixture synthétique source non vérifiée + assertion faussement vérifiée, puis démontrer `unknown` ou rejet clair. Les exceptions ou conflits doivent rester conservateurs.

## Acceptation PM-0005A-R1 (seulement après feu vert utilisateur)
- Ajouter tests synthétiques ciblés : version non exacte, 59 cartes, 60 mais quotas invalides, cartes individuellement `legal`, structure non validée, source non vérifiée avec rotation ou restriction_coverage prétendument `verified`; aucun faux `legal`.
- Préserver les 99 tests annoncés, les faits officiels sourcés, schéma 6 et DB privée, performance de consultation offline et aucune nouvelle requête réseau nécessaire.
- Si une correction complète de la construction de deck exige de nouvelles règles/exceptions, **ne pas étendre R1** : choisir fail-closed `unknown` plutôt qu'une implémentation partielle qui affirme `legal`.
- Cette conclusion est un **audit statique**, pas une preuve que le programme a affiché un faux `legal` sur une vraie carte. Le registre actuel est partiel et produit généralement `unknown`.
- Pas de PM-0005B, Limitless, planificateur, merge ou extraction de données utilisateur avant décision explicite.

## Décision
**PM-0005A : LIVRÉE, NON VERIFIED — correction ciblée nécessaire**. Préparer PM-0005A-R1 lors du prochain feu vert; Codex reste l'exécuteur, ChatGPT vérifie de nouveau GitHub.
