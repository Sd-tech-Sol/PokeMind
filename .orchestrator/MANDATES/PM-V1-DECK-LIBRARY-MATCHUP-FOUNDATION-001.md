# PM-V1-DECK-LIBRARY-MATCHUP-FOUNDATION-001 — AWAITING_AUDIT

Exécution manuelle consommée,livraison2026-10-23. STOP exécuteur.
Audit indépendant ChatGPT au HEAD publié et à sa CI exacte seulement.
Aucun accès réel aux parties personnelles ou réseau fournisseur autorisé.
Voir STATE/RESULT/HANDOFF/NEXT_ACTION et les preuves assainies.

---

## Contrat initial READY — historique non réexécutable

# PM-V1-DECK-LIBRARY-MATCHUP-FOUNDATION-001 — READY

**23 octobre 2026 (Québec).** Sous l'ordre propriétaire durable **D-196** (faire avancer la V1 sans redemander de « go » pour les étapes PUBLIC ordinaires) et [Deck Intelligence — issue #1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1), ce lot **PUBLIC + tests synthétiques exclusivement** est autorisé : `READY`, `execute_now=true`, `consumed=false`. Une seule exécution manuelle par Codex ou Claude Code; poursuivre le **lot complet** sans micro-go. **Aucun accès effectif aux vrais journaux ni aux decks/collection/DB privés** n'est accordé.

## But utilisateur — un cerveau de deck qui apprend, sans inventer
Créer un chemin cohérent de consultation d'une **bibliothèque des playbooks de decks PUBLIC** et préparer le moteur d'analyse des défaites/decks adverses **sur des jeux de test inventés**. Le résultat doit être utilisable localement, documenté, testable et portable entre Codex et Claude Code; V1 `NOT_RELEASE_READY`.

### Prévol
1. Vérifier le HEAD distant `work/pm-v1-lotj-final-readiness-windows` et arbre local, `git fetch`, `pull --ff-only` sans effacer les modifications locales. Lire `AGENTS.md`, `.orchestrator/SESSION_CONTINUITY.md`, `WORKFLOW_ADOPTION_V2.md`, `STATE.json`, premier `NEXT_ACTION.md`, audit `VERIFICATION_PM_V1_DECK_INTELLIGENCE_PUBLIC_FOUNDATION_001.md`, issue #1, skill exécuteur et ce mandat.
2. Attendre et confirmer **Windows+Ubuntu `completed/success` du nouveau HEAD** qui contient ce `READY`. Si CI rouge, corriger seulement un problème lié et autorisé; sans réussite, pas d'action fonctionnelle.
3. Examiner et **réutiliser**, plutôt que recopier, `battle_logs.py`, `battle_sample.py`, `lessons.py`, `recommendations.py`, `decks.py`, `competitive.py`, `deck_knowledge.py`, `set_code_aliases.py` et les tests/DB/CLI actuels. Garder portable Codex/Claude.

### A — Deck Library et guides tactiques PUBLIC (DKI-02)
- En se limitant aux listes et textes **PUBLIQUES déjà en cache** (deux tournois avec32 placements/28 compositions rapportées localement), créer une commande/bibliothèque qui permet recherche par archétype, date, tournoi, version, `list/compare/show/export` ou équivalents. Sélectionner une vraie liste60, expliquer ses cartes par rôles **avec preuves**, setup, contraintes, plans d'attaque/Récompenses, risques, alternatives et contre-jeu *conditionnels*. Commencer avec les quatre fiches pilotes, étendre aux autres compositions si des textes suffisants existent, sans objectif arbitraire de remplir des fiches sans preuve. L'export60 existant doit être réutilisé; copie manuelle, **pas d'accès presse-papiers ni jeu**.
- Pour les **7 impressions MEE non résolues**, chercher uniquement dans les payloads PUBLIC locaux une preuve d'équivalence entre noms d'énergie avec/sans « Basic », qui exige ID/catégorie/numéro/texte cohérents. N'utiliser ni heuristique globale `replace('Basic ', '')` ni équivalence inventée. Si cache insuffisant, garder `unknown`. Réexécuter les contrôles PUBLIC **en lecture seule**, rapporter les progrès et conserver tous les vrais decks comme `unknown` s'il manque des attestations.
- Classement « meilleurs decks » = résultats de tournois **datés et dénominateurs vrais**, pas d'avantage de matchup inventé ni statistiques de victoire sans matchs. Source Limtless pour classement, TCGdex pour description, Pokémon officiel pour normes, communautaire FR séparé. Aucune redistribution du corpus ou des listes brutes dans Git.

### B — Opponent Deck Observer, moteur **sur fixtures uniquement** (DKI-03)
- Construire un composant d'observation de l'adversaire à partir du parseur **déjà existant**, avec des matchs inventés (FR/EN, W/L/unknown, deck version v1/v2, cas incomplet, conflit, doublon). Distinguer clairement **joueur vs adversaire**, cartes vraiment observées vs événements génériques ou main cachée, occurrence/quantité minimale et chronologie/source. Conserver les données brutes séparées des inférences.
- Trois niveaux explicites : `observed_partial` (cartes attestées, parfois sans set), `archetype_hypothesis` (indices et alternatives, confiance prudente), `public_reference_proxy` (liste PUBLIC réelle de60 du même archétype, **jamais présentée comme les60 cartes exactes de l'adversaire**). `exact_confirmed_60` seulement si un export complet du deck adverse est explicitement fourni et validé (fixtures seulement ici).
- Éviter de compter comme cartes vues les attaques génériques, phrases de règles, cartes de main non révélées, mentions multiples d'une seule carte. Ne pas attribuer automatiquement la version du deck du joueur; corrections traçables.
- **Aucune lecture de `data/local/` personnel ni invocation d'import d'un vrai log** dans ce mandat. Les commandes éventuelles pour analyser la vraie partie doivent exiger un chemin/ID **explicitement fourni plus tard par l'utilisateur**; les tests et exemples de ce lot utilisent des fichiers artificiels dans les fixtures isolées.

### C — Matchup Analytics **sur fixtures uniquement** (DKI-04)
- Réutiliser `conservative_sample` et `battle_lessons`; produire un rapport CLI/JSON de test avec `wins/losses/unknown`, `n`, période, **version du deck utilisé confirmée**, adversaire/archétype `observed vs hypothesized`, cartes observées et sources, doublons probables traités avec prudence. Garder distincts l'échantillon de parties personnelles et les placements de tournoi PUBLIC; jamais les mélanger dans un seul taux.
- Exposer une comparaison v1/v2 ou Dragapult vs adversaires **seulement si les versions/outcomes sont effectivement attestés**; indiquer faibles effectifs, biais, `unknown`, et ne pas inférer la cause d'une défaite depuis un seul événement ou un effet non vu. Faire apparaître les hypothèses/actions à tester, aucune automatisation d'achat, craft ou modification Live.
- Fournir un mini scénario entièrement inventé de plusieurs matchs et une réponse vérifiable : « mon deck v1 contre archétype X → 2 défaites confirmées, n=...; cet adversaire a montré ces cartes, voici un proxy PUBLIC éventuel, aucune certitude sur son deck60 ». Préserver l'historique/méthode de déduplication déjà présents, sans purge des enregistrements existants.

### D — Assurance qualité et handoff
- Tests **synthetiques** de bout en bout pour plusieurs langues et decks, séparation joueur/adversaire, profils adverses exact/incomplet/ambigu, decks80? refuser deck incorrect 60, versions incertaines, petits `n`, anti-double-compte, réseau interdit, scopes PUBLIC/PRIVATE et report non-mutation. **Aucun fichier de combat personnel en Git ou un outil externe.**
- Si la commande CLI nécessitera plus tard les vraies données, livrer les contrôles d'opt-in et documenter **comment le propriétaire sélectionnera volontairement un journal**, mais **ne jamais les activer ou les utiliser maintenant**. Pour les diagnostics PUBLIC, cache existant en lecture seule seulement. Aucune nouvelle DB personnelle créée/ouvert; DB synthétiques temporaires permises pour les tests.
- Faire suite complète, hygiène, compilation et `git diff --check`; produire un guide humain (bibliothèque, observer, stats et limites), preuves assainies, références issue #1; publier code/tests et `.orchestrator/STATE,NEXT_ACTION,RESULT,HANDOFF,NEXT_PROMPT,DECISIONS` si nécessaire sur **la même branche**. Vérifier les CI des 2 OS au SHA final; terminer `AWAITING_AUDIT` et STOP ChatGPT. Ne pas demander de « go » entre sous-tâches.

## Limites obligatoires

**Zéro requête fournisseur / zéro API publique nouvelle**. Ancien budget de30GET non utilisé est **clos**. Pas de scans, recherche ou import de vrais combats, deck `principal`, collection, crédits, capture, compte/client Live, presse-papiers ou autre base personnelle sans commande ultérieure spécifique. Aucun accès à des données de tiers personnelles, fournisseur bloqué, installation OS, OCR, scheduler, backup, migration/restauration/purge, reset destructif, force-push ou merge `main`. Pas de service résident. Préserver DKI-05 Counter-Deck Lab, DKI-06 Learning Loop, les portes visuelles/Windows/récupération de V1. **V1 `NOT_RELEASE_READY`.**
