# PM-V1-DECK-INTELLIGENCE-PUBLIC-FOUNDATION-001 — AWAITING_AUDIT

Exécution consommée, livraison2026-10-23. STOP exécuteur; seul prochain geste :
audit indépendant ChatGPT au HEAD publié et à sa CI exacte. Aucun budget
réutilisable. Voir RESULT/HANDOFF/NEXT_ACTION/STATE et les preuves assainies.

---

## Contrat initial READY, historique non réexécutable

# PM-V1-DECK-INTELLIGENCE-PUBLIC-FOUNDATION-001 — READY

**22 octobre 2026, Québec.** Exécution autorisée pour **UN LOT COMPLET et fonctionnel** PUBLIC sous la décision durable D-196 (progresser sans micro-go) et [Deck Intelligence — issue #1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1), sections DKI-01 et premier parcours DKI-02. **`READY`, `execute_now=true`; démarrage local manuel Codex ou Claude Code.** Ne pas réintroduire la collecte passée; ne pas ouvrir de données personnelles. V1 `NOT_RELEASE_READY`.

## Objectif produit : rendre les decks de tournoi compréhensibles ET copiables
Donner au joueur via CLI une fiche de deck PUBLIC, datée et sourcée : liste60, rôles des cartes, plan de jeu/installation/combos **lorsque les textes et preuves permettent de les soutenir**, limites/inconnus, références d'événements et commande d'export PTCGL déjà éprouvée. Corriger en priorité **le problème des codes d'extension** qui a laissé 0/97 impressions résolues lors du prévol, sans deviner ou créer de faux verdicts.

### Prévol avant travail
- Vérifier branche `work/pm-v1-lotj-final-readiness-windows`, arbre Git local, ff-only **sans écraser de modifications locales**, lire AGENTS, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, premier NEXT_ACTION, HANDOFF/RESULT, skill exécuteur, [issue #1](https://github.com/Sd-tech-Sol/PokeMind-dev/issues/1), mandat et audit prévol. Inspecter les CI **au HEAD incluant ce mandat**; n'entamer la phase fonctionnelle qu'après `completed/success` Windows/Ubuntu. Ne pas réutiliser la seule CI du commit précédent.
- Inventorier **d'abord** et réutiliser `competitive.py`, `public_deck_preflight.py`, `rules.py`, `cards.py`, `decks.py`, `deck_exports.py`, `recommendations.py` et les tables/FTS PUBLIC actuelles. Écarter doublons/framework/service/GUI inutile.
- Contrats de preuve : distinguer sources officielles Pokémon (normes), TCGdex (description), Limitless (liste/tournoi) et Poképédia (texte communautaire non officiel sous licence); dates par fait, contraintes de redistribution. Aucun champ manquant complété par IA comme si c'était une traduction/règle officielle.

### A — Correspondance codes d'extension PUBLIC, problème bloquant
- Identifier **quels codes d'extension** des 4 listes PUBLIC sont introuvables dans `catalog_sets.tcg_online_code`; déterminer la source de chaque code et les identifiants TCGdex correspondants à partir **des métadonnées déjà en cache**, avant tout accès réseau. Conserver exemplaires et identités originales.
- Construire une **couche d'alias versionnée et sourcée**, dans une table/fixture PUBLIC séparée et optionnelle ou fichier de mapping documenté. L'alias doit être **univoque**, non basé sur une ressemblance de nom seule; croiser identité d'extension, langue, date, numéros de cartes et provenance lorsque disponibles. Ambiguïté ou preuve absente => `UNKNOWN`, aucun alias inventé. Ne jamais altérer les IDs de TCGdex natifs ou `catalog_sets` historique, ne pas modifier la DB PUBLIC existante sans opt-in distinct.
- Réutiliser cette couche à l'endroit commun de résolution du prévol, avec garde-fous sécurité et tests contre fausses correspondances. Produire des mesures **avant/après** avec dénominateurs **lignes uniques vs lignes par option et copies**, statuts `resolved/ambiguous/unresolved`; **ne pas augmenter un compteur artificiellement**. Les décisions réglementaires restent séparées de l'identité.
- **Budget neuf et indépendant** pour consultation ciblée uniquement si le cache n'offre pas de preuves suffisantes : au plus **30 GET / 16 Mio cumulés / 1 Mio par réponse**, maximum **12 actions de découverte**, intervalle ≥1s par fournisseur, une tentative/URL, refus de redirections, challenge, 401/403/429/robots/CGU et aucun contournement. Sources officielles/publiques documentées et permises seulement. **Pas de bulk download**, aucune répétition des campagnes closes; ne pas considérer un budget non utilisé comme transférable.
- Si l'alias ne peut être prouvé sous ces limites, conserver `unknown`, terminer les autres objectifs et indiquer les exemples bloqués. **Ne jamais déclarer `legal` du seul fait d'un set matché.**

### B — Base de connaissances stratégiques par deck
- Créer un **schéma minimal de connaissances PUBLIC sourcées**, extensible pour les six phases de l'issue #1 : `archetype / variant / source_list / card_role / observed_card_text / strategic_claim / uncertainty / dated_provenance`, version/empreinte. Éviter une nouvelle grosse base de données quand une extension PUBLIC isolée suffit. Les données détaillées de decks restent `data/local/`, ignorées de GitHub; fixtures synthétiques seulement en Git.
- Pour les decks PUBLIC déjà acquis, produire une fiche pilote de **Dragapult** et au moins **deux alternatives** disponibles, avec **60/60 prêtes à exporter**, rôle des cartes si texte sourcé, plan de setup, ressources/énergie, enchaînements d'attaque possibles, plans de Récompenses conditionnels, erreurs et contre-stratégies **prudemment formulés**. Distinguer `fact` (texte de carte / source), `inference`, `hypothesis_to_test`, et `unknown`. Pas de stratégies de combos non soutenues par le contenu existant. Si une fiche est insuffisamment documentée, marquer `PARTIAL_WITH_EVIDENCE` et conserver les inconnus.
- Utiliser les classements de tournoi **comme preuve descriptive**, pas un ranking absolu : deux événements et top16 sont un échantillon biaisé. Ne pas annoncer un winrate/matchup, un classement « meilleurs decks présentement » ou disponibilité Live sans preuves quantitatives suffisantes.
- Ajouter `deck knowledge show --selector <event:placement> --as-of ... --db <PUBLIC>` (ou commandes CLI équivalentes intégrées à `meta`), JSON/humain, source/date et liens vers `competitive-export` **déjà valide 60/60**. Le format PTCGL reste `FIELD_VALIDATED` historiquement; ne pas lancer le jeu, modifier le deck personnel ni refaire le test de presse-papiers. Copie clipboard automatisée non autorisée dans ce lot; exporter le texte standard pour copie manuelle.
- Documenter dans `docs/DECK_INTELLIGENCE.md` l'usage et l'approche pour ensuite DKI-02 complet, Opponent Observer, Matchup Analytics et Counter-Deck Lab. Ne pas affirmer que ces modules privés sont déjà faits.

### C — Validation et livraison
- Développer en autonomie tous les sous-travaux ordinaires de ce lot **sans demander de nouveau go**. Tests Python synthétiques (codes vrais/faux/ambiguës, contenus absents, date, provenance, signatures60, source discordante, scénarios de légalité Live inconnue, pas de classement imaginaire), tests Linux/Windows, style/hygiène et `git diff --check`.
- Sur les caches PUBLIC déjà explicitement connus, vérifier **en lecture seule** la consultation et les 4 exports, comparer l'évolution de la résolution; aucune modification du jeu, des sources, de la collection ou des journaux du propriétaire. Rapporter ces résultats `CODEX_LOCAL_REPORTED`; aucune copie de deck réel, HTML brut, noms privés, base ou journal dans Git. Toute table additionnelle nouvelle est dans un emplacement PUBLIC distinct, explicite et sûr, sans migration des deux DB historiques.
- Livrer un **résultat utilisateur vérifiable**, pas seulement un schéma abstrait : au moins une fiche/commande de deck et des sources, ou `PARTIAL_WITH_EVIDENCE` honnête si absence réelle de preuves. Versionner code, tests, rapport de provenance, guide et `.orchestrator/{STATE,NEXT_ACTION,NEXT_PROMPT,RESULT,HANDOFF}` sur **cette branche**, CI deux jobs au SHA exact, puis `AWAITING_AUDIT` et STOP indépendant.
- Garder l'EPIC #1 comme feuille de route et les autres exigences A–J V1 intactes. Ne pas développer encore DKI-03/04 sur les **vraies** parties sans commande locale volontaire; les tests privés doivent rester synthétiques.

## Exclusions permanentes
Aucune lecture automatique du deck `principal`, base personnelle, collection, crédits, journal de bataille ou capture; aucune fuite vers GitHub ou prestataire; aucun accès au compte/client Live, action de jeu, dépense, nouvelle installation OS, scheduler, OCR, backup/restauration, purge, reset destructif, merge ou force-push. Respecter les refus fournisseurs et limites. Le lanceur est **manuel**, sans watcher en arrière-plan. V1 `NOT_RELEASE_READY`.
