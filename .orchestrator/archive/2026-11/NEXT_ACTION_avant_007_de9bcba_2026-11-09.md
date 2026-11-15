# PM-UI-DECKLAB-RESPONSIVE-CONTROLS-007 — READY_FOR_CODEX (2026-11-09)

**Réception visuelle 006 reçue et audit amendé :** le vrai Deck Lab affiche correctement 3 grandes cartes à 1500, 2 à 1100, avec le thème BrainBall. **BLOCAGE à 1100×900 / font 18 / scale 125 % : les actions de la première rangée de sélection du deck sont visiblement TRONQUÉES** (Deck principal, Ajouter mon deck, sélection de titre). Source et captures réelles analysées par ChatGPT; le défaut antérieur avait été documenté par Codex, mais demeure non acceptable avant un Setup. Audit : [VERIFICATION_PM-UI-DECKLAB-REAL-GALLERY-006_2026-11-09.md](VERIFICATION_PM-UI-DECKLAB-REAL-GALLERY-006_2026-11-09.md) annexe de réception, commit `5df7192`.

**Prochaine action UNIQUE — correctif UX privé Codex `PM-UI-DECKLAB-RESPONSIVE-CONTROLS-007` :** mandat complet prêt dans [NEXT_PROMPT.md](NEXT_PROMPT.md), commit `28605b8`. Synchroniser fast-forward, corriger uniquement la disposition responsive de la rangée sélecteur/boutons de `window.py:_decks()`, préserver les mêmes widgets/signaux, rendre le texte intégral à 1100/18/125 %, garder la rangée large si possible à 1500. Tests natifs du vrai `MainWindow` synthétique avec assertions de troncature, captures avant/après, matrice FR/EN clair/sombre/DPI, porte complète locale isolée, rapport et push branche privée puis STOP pour audit ChatGPT. **Ne pas recommencer le design de la galerie ni le Coach.** Le GO privé de développement de l'intégration 006 s'étend à corriger ce blocage constaté en réception, pas à installer.

**Aucune installation, changement de version, build/setup, publication, modification des données/consentements ou sauvegardes autorisés.** Installation hotfix 0.9.5 inchangée, public 0.9.3, `NOT_RELEASE_READY`.

---

# PM-UI-DECKLAB-REAL-GALLERY-006 — VERIFIED_SOURCE / OWNER_REAL_GALLERY_VISUAL_RECEPTION_PENDING (2026-11-09)

**Audit indépendant ChatGPT terminé :** [VERIFICATION_PM-UI-DECKLAB-REAL-GALLERY-006_2026-11-09.md](VERIFICATION_PM-UI-DECKLAB-REAL-GALLERY-006_2026-11-09.md), commit `c2ffd56`. Code privé `d6efdd2`, rapport `8abe226`. La première adaptation de la **vraie** galerie Qt est conforme au mandat de code et n'a pas modifié `window.py`, Coach/permissions, catalogue/cache, stockage, version ni installation. Tests Codex rapportés 138 Qt + 1654 cœur, 1792 réussis/3 ignorés, non rejoués par ChatGPT. GitHub a été contrôlé au SHA code : aucun statut ni run, pas de CI verte.

**Action unique : réception visuelle propriétaire des deux captures du vrai `MainWindow` synthétique** `build/qa-real-decklab-gallery/after-1.25/gallery-1500-dark-fr-14.png` et `gallery-1100-dark-fr-14.png` (et vidéo optionnelle `hover.mp4`). Les sorties locales hors Git n'ont pas été vues indépendamment. À 1100/125 %, Codex signale une rangée de boutons de sélecteur parfois tronquée, problème préexistant hors lot : décider seulement après visionnement si elle bloque une future installation. **Aucun nouveau prompt agent, installation, backup ou publication avant verdict propriétaire.** `NEXT_PROMPT.md` consommé, ne pas relancer.

Installation propriétaire hotfix 0.9.5 inchangée, sauvegardes préservées; public 0.9.3. `NOT_RELEASE_READY`.

---

# PM-UI-DECKLAB-REAL-GALLERY-006 — AWAITING_AUDIT / STOP (2026-11-09)

Mandat D-300 exécuté; [NEXT_PROMPT](NEXT_PROMPT.md) consommé. Code privé `d6efdd2ddbd2b804e1fc1689dfaa243567640005`.
Vraie galerie Qt uniquement : 3/2/1 colonnes, cartes plus grandes, lisibilité et interactions conservées.
[RESULT](RESULT.md), [HANDOFF](HANDOFF.md); résultat précédent et ancien NEXT_ACTION dans `archive/2026-11/`.

**Action unique : audit indépendant ChatGPT au SHA exact**, puis réception visuelle propriétaire des
captures réelles synthétiques dans `build/qa-real-decklab-gallery/after-1.25/` (1500/1100, GIF/MP4).
Porte complète isolée **VERTE : 138 Qt + 1654 cœur = 1792 réussis, 3 ignorés, zéro échec**.
GitHub au SHA code : 0 statut/check/run, NO_GITHUB_STATUS; aucune CI verte revendiquée.

Aucune relance du mandat, autre écran, installation, version, sauvegarde ou publication autorisée.
Données personnelles intactes; installé 0.9.5 hotfix et public 0.9.3 inchangés. **NOT_RELEASE_READY**.
