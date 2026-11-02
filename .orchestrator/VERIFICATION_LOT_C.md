# VERIFICATION_LOT_C — audit statique indépendant ChatGPT (2026-10-13)

## Verdict
**LOT C livré et FONDATION ACCEPTÉE EN REVUE STATIQUE AVEC RÉSERVES.** C0 (réparations temporelles/candidats), C1 (fichiers image éphémères locaux) et C3 (mémoire textuelle) sont effectivement codés. C2 (lecture visuelle réelle), C4 (conseils fondés sur règles complètes) et C5 (essai réel / validation officielle skill) restent **PARTIAL_WITH_EVIDENCE** ou **BLOCKED_WITH_REASON**. Aucun moteur de vision/OCR installé ou testé sur un vrai plateau : il serait faux d'affirmer que PokeMind reconnaît déjà les cartes sur un screenshot sans annotation.

## Preuves GitHub examinées
- Repo privé `Sd-tech-Sol/PokeMind`, branche `work/pm-v1-lotc-visual-training-coach`, commit livré Codex **`2b21cf659b328b78d1b3d2ee023eae82dcae6f21`**, base `e50da590ecd6311d5441c90a25c3c78739299a4d`. Comparaison : **6 commits, 0 retard, 25 fichiers modifiés/ajoutés**.
- Code et tests inspectés : `src/pokemind/{visual_coach,collection,candidates,recommendations,database,cli}.py`, `tests/test_{visual_coach,collection,candidates}.py`, `docs/{LOT_C_EXECUTION_PLAN,LOT_C_ACCEPTANCE_MATRIX,LOT_C_VISUAL_COACH}.md`, RESULT/HANDOFF/NEXT_ACTION et plan V1.
- Arbre Git : **174 entrées, `truncated=false`**, aucun chemin SQLite/image/log personnel, backup ou secret suivi détecté. Inspection de chemins ne certifie pas tout l'historique Git ni la SQLite Windows.
- Zéro statut CI et zéro workflow PR attachés au HEAD selon GitHub. **272 tests réussis en 50,79 secondes, compilation, diff check, sauvegarde/migration synthétique 10→11, FK/intégrité/FTS5 et vraie base schéma 7 intacte** = **rapports Codex**, pas réexécution indépendante sur le PC par ChatGPT. Aucun merge.

## C0 : deux réserves LOT B réparées en code
- `collection._snapshot_at_date` filtre observation `as_of` ET date de capture locale `recorded_at`, rejoue les enregistrements historiques (y compris rollback) sans sélectionner le seul snapshot actif actuel; `recommend_deck` transmet la date aux trois lecteurs collection/crédits/missing. Les tests synthétiques couvrent dates antérieures, captures mêmes jours, rollback et anciens schémas.
- `candidates._validate_candidate` supprime la fausse règle « au moins une Énergie ET un Dresseur »; Basic obligatoire uniquement avec règle officiellement sourcée active, comparaison catégorie publique de l'impression versus section déclarée et traitement `mismatch/unknown/conflict`. Tests de 0 Énergie/Dresseur, Basic, divergences et reprints. Légalité globale continue à dépendre de registres officiels incomplets, et non d'une déclaration de Codex.

## C1/C2 : contrôle médias et honnêteté du backend
- `inspect_training_image` n'accepte qu'un chemin sous `data/local/` hors symlink connu, limite 25 MiB / 50 Mpx / dimensions, vérifie signatures PNG/JPEG/WebP et EXIF avant de retourner métadonnées sans chemin/hash ni enregistrement. Il **ne décode pas les pixels** en l'absence de bibliothèque de vision : validation de l'entête ne certifie pas à elle seule l'intégrité complète ni un modèle d'image interprétable.
- `observe_training` retourne `VISION_BACKEND_UNAVAILABLE` et `NEEDS_MANUAL_ANNOTATION` pour une image seule, sans créer de DB. Le JSON d'annotation manuelle permet un plateau avec `unknown` et information cachée; pas de prétention de lecture réelle du screenshot.
- Tests synthétiques formats/symlinks/traversée, non-conservation de pixels et absence d'accès au compte.

## C3 : mémoire locale textuelle
- Schéma SQLite **11 additif** (`training_sessions`, `training_observations`), backup avant migration, ses propres sessions `train-...`, ordre de tours, checksum du JSON textuel, corrections append/supersede, révocation et fermeture explicites. `--apply --confirm-owner` pour toute écriture, preview sans migration.
- Limite à corriger lors du prochain grand lot : le contrôle de duplicata `(session_id, turn_number, state_sha256)` dans `save_observation` renvoie `DUPLICATE` même si l'observation identique est **superseded ou revoked**, empêchant de réappliquer volontairement un état déjà vu via `match correct` ; la transition d'une correction à une révision identique ancienne peut échouer sans réactiver l'état voulu. Ajouter test revocation→correction→restoration et distinguer duplicate **actif** vs ancien historique.
- Également, `normalize_board_state` accepte en entrée manuelle `provenance='visual_certain'` même lorsque **aucun backend visuel existe**. Cette provenance doit être validée/sanitizée en `owner_annotated` pour ne jamais présenter comme extraction visuelle une annotation non vérifiée. Les cartes de la main adverse cachée sont bien masquées; assurer la même prudence pour les éléments marqués `hidden` de la défausse.

## C4 : conseils prudents, mais qualification des énergies à durcir
- `advise_turn` utilise texte des attaques TCGdex local, les observations sauvegardées et statuts `conditional/not_supported` ; aucune action envoyée au jeu, zéro option `verified_possible` sans preuve totale, pas de cartes cachées ni « meilleur coup ».
- **Réserve concrète** : l'éligibilité `enough` est calculée comme `sum(visible energies) >= len(attack.cost)` SANS compatibilité de **types d'énergie**, coûts spéciaux, modifications d'attaque, statut/effets; l'option ne devrait jamais être présentée avec `VISIBLE_PREREQUISITES_MET` quand seul le total correspond mais pas le type. Attaque demandant Feu et 1 Énergie Eau doit rester `ENERGY_TYPE_NOT_VERIFIED` / inconnue, pas « prérequis visibles satisfaits », même conditionnellement.
- `advise_turn` reçoit format/platform/as_of mais **ne les recoupe pas** avec le contexte daté enregistré en `training_sessions`, ce qui peut donner une citation/qualification de date déconnectée de la séance. Exiger cohérence ou exposer l'écart comme unknown, sans appliquer un état futur rétroactivement.
- Aucune vraie capture ni backend de reconnaissance : **C2/C4/C5 demeurent PARTIAL**.

## C5 et sécurité
- CLI `match` (start, observe, correct, revoke-correction, show, advise, close), deux skills portables byte-identiques entre Codex/Claude, tests E2E synthétiques. Validateur officiel skill PyYAML absent : seulement tests équivalents du frontmatter; ne pas dire officiellement validé.
- Respecter entraînement où assistance externe permise, aucun bot/overlay, capture furtive, stockage d'images, cloud OCR/LLM, installation Windows scheduler, mutation des cinq combats et aucun merge.

## Décision / suite
**Accepter LOT C comme livraison de fondation statique, avec limitations explicites et garde-fous D0 à corriger.** Conformément à la volonté de l'utilisateur de **grossir les lots et laisser Codex autonome**, ne pas ouvrir une mini-branche isolée : intégrer D0 (provenance annotation, validation énergie/contexte, historique de correction) au début du **LOT D autonome** puis exécuter la collecte publique incrémentale quotidienne et approfondie mardi/vendredi dans le même lot.
**Ne pas remplacer ni abandonner le coach visuel** : une vision locale de vrai plateau et tests avec vraies captures demeurent **PARTIAL/BLOCKED** et doivent rester dans backlog jusqu'à validation et autorisation. Installation/activation planificateur Windows **seulement après opt-in explicite**, même si code et simulations/dry-run sont prêts. LOT E sauvegarde/restauration et QA finale, lacunes catalogue/règles/reprints/méta et Trainer Hill demeurent obligatoires.
