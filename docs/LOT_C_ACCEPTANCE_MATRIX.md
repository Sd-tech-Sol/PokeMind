# Matrice d’acceptation — LOT C

Date : 2026-10-13. Cette matrice décrit la livraison Codex et ne constitue pas une
vérification indépendante.

| Sous-lot | État | Preuves | Limites / suite |
|---|---|---|---|
| C0-1 temporalité collection/crédits | `DONE` | Dates d’observation + capture locale, même jour Toronto, succession, rollback, vieux schéma, JSON/humain et recommandation historique | Base privée schéma 7 non migrée |
| C0-2 structure/catégorie candidat | `DONE` | Zéro Énergie, zéro Dresseur, Basic présent/absent, catégorie contradictoire/inconnue, réimpression exacte et export prudent | Couverture normative publique reste partielle |
| C1 image privée éphémère | `DONE` | PNG/JPEG/WebP synthétiques, signature/extension, octets, dimensions, pixels, orientation, crop déclaré, traversée/externe/symlink refusés; zéro pixel stocké | Aucun média réel utilisé conformément au mandat |
| C2 contrat de plateau | `PARTIAL_WITH_EVIDENCE` | Contrat v1, deux côtés, actif/banc/main/défausse/Récompenses, provenance, inconnues, erreurs; annotation manuelle fonctionnelle | `VISION_BACKEND_UNAVAILABLE`: ni Pillow ni OCR local fiable installés; extraction réelle non simulée |
| C3 mémoire textuelle multi-tours | `DONE` | Schéma 11 additif, séance aléatoire, 3 tours, 2 séances isolées, déduplication, ordre, correction/révocation/replay, fermeture | Écriture réelle exige toujours `--apply --confirm-owner` |
| C4 conseil explicable | `PARTIAL_WITH_EVIDENCE` | Texte TCGdex exact + énergie visible → option conditionnelle sourcée; contradiction → `not_supported`; hidden `UNKNOWN`; aucune action client | Zéro `verified_possible` tant que règles/effets contextuels et plateau complet ne sont pas prouvés |
| C5 CLI/skills/E2E/audit | `PARTIAL_WITH_EVIDENCE` | 272 tests, CLI `match`, skill identique Codex/Claude, compilation, intégrité/FTS5, migration/rollback, audit Git/secrets | Essai avec vraie capture `BLOCKED_WITH_REASON` par l’interdiction explicite d’utiliser une capture réelle pendant ce lot; validateur officiel du skill bloqué par PyYAML absent |

## Preuves finales

- Baseline : `256 passed`. Fin : `272 passed in 50.79s`.
- `python -m compileall -q src tests` et `git diff --check` : réussis après
  correction des fins de fichier.
- Base personnelle : schéma 7, intégrité `ok`, 0 violation FK, FTS5 sections 87/87
  et catalogue 973/973; SHA-256 identique avant/après l’audit.
- Migration synthétique 10→11 : sauvegarde cohérente et données sentinelles
  conservées. Prévisualisation : aucune création/migration.
- Git : seul `data/local/.gitkeep` est suivi; zéro SQLite, image, journal, clé ou
  motif de secret suivi. `visual_coach.py` n’importe aucun client réseau, outil de
  capture, presse-papiers ou automatisation.
- Skill : les copies `.agents/skills/visual-training-coach/SKILL.md` et
  `.claude/skills/visual-training-coach/SKILL.md` sont byte-identiques et leur
  frontmatter minimal est testé. `quick_validate.py` n’a pas pu démarrer faute du
  module facultatif `yaml`; aucune dépendance n’a été installée.

## Couverture synthétique C5

Les tests couvrent image invalide, extension/signature contradictoire, formats et
dimensions, orientation EXIF, crop déclaré, image externe/symlink, zéro/deux séances,
trois tours, main adverse cachée, Récompenses cachées, actif ambigu, identité absente,
ordre de tour invalide, action contradictoire, correction/révocation, doublon, replay,
fermeture, conseil conservateur et non-persistance des pixels. Toutes les bases et
images sont créées sous `data/local/test-runs`, puis retirées par les fixtures.

## Limites honnêtes

Le mécanisme C1/C3 et le repli manuel C2 sont utilisables, mais aucune reconnaissance
visuelle d’un plateau réel n’est démontrée. Le statut `PARTIAL_WITH_EVIDENCE` demeure
donc pour C2, C4 et C5. Un essai réel manuel en entraînement devra être réalisé dans
une action future explicitement autorisée; il ne doit ni activer un service cloud ni
conserver l’image.
