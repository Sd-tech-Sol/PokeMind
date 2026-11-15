# RESULT — PM-UI-DECKLAB-VISUAL-POLISH-004 — AWAITING_AUDIT (2026-11-08)

**Prototype retouché, capture et vidéo Qt produites. STOP audit ChatGPT et jugement visuel propriétaire.**
Base `0a613a9c24e99922c4ee065b0ddbcf3f7275b649`, code `4f413de4b4cd6068d2b29dbe406609df9abc0f79`,
branche privée `work/pm-v1-lotj-final-readiness-windows`.
GO direct du propriétaire pour une nouvelle retouche après l'audit source 003; aucune relance de cet ancien mandat.
[RESULT 003 archivé](archive/2026-11/RESULT_PM-UI-DECKLAB-REFERENCE-INTEGRATION-003_bf5a932_2026-11-08.md).

## Ouvrir la preuve visuelle

```powershell
python demos/premium_decklab/reference.py
Start-Process .\build\qa-decklab-polish\decklab-full.png
Start-Process .\build\qa-decklab-polish\preview.mp4
```

Reproduction : `python demos/premium_decklab/reference_preview.py`.
Ancien rendu conservé dans `build/qa-decklab-reference/`; copie locale `build/qa-decklab-polish/baseline-003.png`.
PNG de référence versionné intact; sources de production, version et dépendances inchangées.

| Aspect, même fenêtre 1500 × 970 | Avant 003 | Après 004 |
|---|---|---|
| Largeur peinte d'une carte | ~144 px | ~213 px, **+48 %**; surface ~2,18× |
| Titres / sous-textes externes | 12 px / absents | 17 px / 12 px; repli avec hauteur réservée |
| Six illustrations | 5 puis 1, rangée presque vide | **3 puis 3**; **2 par rangée à 1100 px** |
| Bandeau | Fragment très atténué | Panorama original, créature visible, lumière cyan/or, sélecteur intégré |
| Profondeur | Fond uniforme | Pochettes en dégradé, ombres existantes, sélection or, contours lumineux mesurés |
| Coach à droite | Grand rectangle de texte | Identité renforcée, accueil typographique, trois panneaux explicatifs et composition conservée |

Comparaison visuelle Codex effectuée sur l'ancien PNG, la référence et les deux nouvelles tailles.
**Amélioration locale visible constatée par l'exécuteur; acceptation artistique finale réservée au propriétaire.**
Les trois panneaux Coach expliquent ses commandes existantes; aucune réponse IA, recommandation, statistique
ou nouveau moteur inventé. Navigation réelle à sept rubriques, trois onglets et vrai dock Qt de 355 px conservés.
Le prototype reste une adaptation de présentation isolée; aucun constructeur MainWindow/Services/Store exécuté.

## Fichiers locaux et animation

Dans `build/qa-decklab-polish/`, tous ignorés par Git :

- `decklab-full.png` : fenêtre entière 1500 × 970, 424 162 octets; vue et décodée.
- `decklab-1100.png` : contrôle étroit 1100 × 900, 292 352 octets; vu et décodé.
- `preview.mp4` : H.264, sans audio, 1500 × 970, 20 i/s, 120 images, 6 s, 317 612 octets;
  décodage FFmpeg complet réussi. `preview.gif` : 120 images toutes décodées, 6 000 ms, 1 004 436 octets.
- `recording.json`, `verification.json`, frames : preuve locale de hover, clic/sélection, panneau, onglet Statistiques
  puis Galerie. Capture de vrais QWidget, aucune capture du bureau; curseur ajouté au film uniquement.

Survol réel 220 ms : 0 → 0,5386 → 0,8377 → 0,9678 → 0,9992 → 1, six images distinctes.
Transitions 180 ms et mouvement réduit réutilisés. Panorama peint une fois en mémoire; aucun effet graphique lourd,
animation de géométrie ou timer de boucle ajouté. Aucun test de cadence physique en images/s revendiqué.

## Validation et limites

Prévol RUNTIME_READY, base propriétaire non ouverte, zéro écriture/réseau par le prévol. Ciblée isolée : **5/5**;
native Windows Qt 125 % : **5/5**. Deux défauts détectés lors de la première passe ciblée puis corrigés : titre
long débordant en offscreen, accueil Coach trop court. Contrôles : dock/onglets, tailles, absence de défilement
horizontal, art ≥200 px de largeur, titres lisibles, sélection/clavier, animations/réduction et contraste des tokens.
Contrôle natif supplémentaire à DPR 1,25, 1500 → 1100 → 1500 : art mesuré **212,9 px**,
défilement horizontal **0**, dernière pochette et titre entièrement accessibles par défilement,
accueil Coach sans défilement interne; `native-125.json` local. Aucun réglage DPI Windows modifié.
**Porte complète `python scripts/local_gate.py` VERTE, sortie 0 : 130 Qt + 1650 cœur réussis,
3 ignorés, zéro échec, 1780 réussis au total.** Compilation/hygiène vertes; Qt 73 s, cœur 573 s.
Tous les pytest ont été exécutés en copies isolées, jamais dans le dépôt de travail. Identité des trois
fichiers code/tests modifiés confirmée avec la copie de cette porte avant son nettoyage automatique.

Limites visuelles : art géométrique original plutôt que cartes Pokémon détaillées; défilement vertical nécessaire
pour les grandes cartes et les énergies, particulièrement à 1100 px. Aucun vide de fin de rangée, mais les rangées
inférieures ne sont pas toutes visibles d'un coup. Identité du vrai PokeMind, pas le logo redessiné de la maquette.
Sombre FR-CA seulement; dock fixe; commandes hors aperçu désactivées. Aucun simulateur, filtre, onglet fictif,
impact estimé ou faux résultat Coach. Les contrastes testés concernent les tokens texte/fond, pas une certification
globale sur chaque pixel du bandeau artistique. Le produit réel reste distinct de cette étude de réception.

## Git et STOP

Fast-forward `bf5a932` → `0a613a9`, arbre initial propre, dépôt confirmé privé. Référence inchangée, aucune donnée réelle,
installation, version, sauvegarde, migration, accès au root personnel, nouvelle dépendance ou publication publique.
Code poussé privé et HEAD distant confirmé au SHA exact `4f413de4b4cd6068d2b29dbe406609df9abc0f79`.
GitHub à ce SHA : 0 statut, 0 check, 0 run. Agrégat `pending` sans statut, aucun run en file;
la porte locale n'est pas une CI GitHub verte. Un seul commit de rapport assaini; HEAD distant et
statuts au SHA final contrôlés après push du rapport.
**AWAITING_AUDIT / NOT_RELEASE_READY.** Prochaine action unique : audit ChatGPT au SHA exact et jugement visuel
propriétaire sur le nouveau PNG/film. Aucune intégration produit ou installation autorisée.
