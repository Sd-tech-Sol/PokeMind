# RESULT — PM-AUDIT-CLAUDE-PLAN : refonte visuelle et premières pièces de la version publique (D-266), 2026-11-01

Exécuteur : Claude Code (Opus 5.5). Autorisation : D-258; demande du propriétaire en session (captures à l'appui) :
« plus visuel quand il travaille… une fenêtre flottante plus grosse… la touche Entrée… la balle de Pokémon, mais que dans
le milieu ça soit un cerveau… Combats, Cartes & méta, Apprentissage, Réglages… téléchargeable… par défaut en anglais…
pas de GitHub Actions ». Code : **`45a49e2f0492ecaf5b2f01e7cdd21dccc0d7576d`**. Session précédente (D-264, D-265) :
[archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D264-D265_2026-11-01.md](archive/2026-11/RESULT_PM-AUDIT-CLAUDE-PLAN_D264-D265_2026-11-01.md).

## Livré (décision D-266)
| Lot | Commit | Contenu |
|---|---|---|
| Chat | `176e3ae` | carte d'activité animée + chrono au-dessus du champ; Entrée pendant une réponse garde le message; listes complètes sans « … »; « Agrandir » (grande fenêtre flottante); clic sur Terminal = moteur du chat; liens et encadré retirés |
| Logo | `c976707` | Poké Ball avec cerveau 2D, partout; `.ico` multi-tailles généré au build (`scripts/make_icon.py`, `--icon`) |
| Réglages | `a199c5d` | cinq onglets à icônes, une ligne courte par réglage, détails en infobulle et « Voir les détails » |
| CI | `ef6a8c9` | `.github/workflows/ci.yml` retiré (aucune minute GitHub); test Réglages |
| Combats | `817590b` | tuiles (parties, victoires, défaites, adversaire le plus coriace), barre bleu/rouge/jaune, tri par défaites |
| Apprentissage | `66495d0` | tuiles, bilans en barres, plans en cartes, plus de noms internes |
| Cartes & méta | `f4eede5` | classeur original (couverture qui s'ouvre, pochettes, 1 ou 2 pages), cartes visibles d'entrée (`cards.browse_cards`) |
| Terminal | `3340d25` | couleurs de l'app, volet arrondi, en-tête d'une ligne (avis complet en infobulle) |
| Langue | `a1e8a88` | jamais choisie → langue de Windows, anglais sinon; un choix enregistré l'emporte |
| README | `4d2d8d7` | README public anglais + français; ancien README → `docs/HISTORIQUE_README.md` |
| Premier lancement | `45a49e2` | assistant (langue, moteur détecté, consentement cloud, journaux, illustrations), une seule fois, dossier sans préférences |

## Preuves
- Porte locale `python scripts/local_gate.py` **VERTE** à `45a49e2f0492ecaf5b2f01e7cdd21dccc0d7576d` : Qt 90, cœur 1523 réussis, 3 ignorés (total 1613).
  Portes vertes intermédiaires : `ef6a8c9` (1606), `f4eede5` (1610). Une porte ROUGE à `c976707` (assertion « Send » devenue
  « Send ↵ ») corrigée dans `ef6a8c9`.
- Captures sur données inventées (dossier temporaire, aucune donnée personnelle) de chaque page en FR et des Réglages en EN.
- EXE reconstruit depuis `45a49e2f0492ecaf5b2f01e7cdd21dccc0d7576d` : 796 fichiers, 124 Mio, 71/71 modules PokeMind identiques aux sources, aucun module QA;
  fumée `POKEMIND_DESKTOP_SMOKE=1` sur la fixture inventée : sortie 0, 7 pages, terminal disponible, 5 bases inchangées.
  Déployé dans `dist/PokeMind/`; l'ancien est conservé dans `dist/PokeMind-before-visual-refresh-991ad026d23c4e1fb61ffa4678e8aa5a`.
- Le pointeur `%LOCALAPPDATA%\PokeMind\location.json` existe (écrit à 01:22 par l'EXE du propriétaire, réponse à la
  proposition de copie D-264); **contenu non lu**, inchangé par la fumée.

## Limites et suite
- Version publique non terminée : mode autonome sans dossier de projet (données dans `%LOCALAPPDATA%\PokeMind`, premier
  téléchargement borné du catalogue public), installateur en un seul fichier, licence, audit de l'historique Git et des
  droits de `source_material/`, validation du logo (marque Poké Ball). Passage du dépôt en public : GO explicite requis.
- Aucun test sur le PC du propriétaire avec ses vraies données : réception propriétaire requise. V1 NOT_RELEASE_READY.
