# VERIFICATION_PM-0005B-R2 — audit indépendant ChatGPT (2026-10-12)

## Verdict
**PM-0005B-R2 ACCEPTÉE EN REVUE STATIQUE INDÉPENDANTE POUR SA PORTÉE D1/D2.** Les exclusions de découverte sont désormais scoppées par contexte de demande, et un checkpoint durable avec reprise/recouvrement permet l'exploration après de nombreuses pages connues sous petit budget. Aucun défaut bloquant nouveau n'a été identifié dans ces deux exigences. Cela **n'est pas** la preuve d'exhaustivité de l'API Limitless ni une exécution indépendante de la suite pytest sous Windows.

## Éléments GitHub effectivement vérifiés
- Dépôt privé `Sd-tech-Sol/PokeMind`, branche `work/pm-0005b-r2-resume-scopes`, commit fonctionnel Codex **`064ffb6f84184561a8b4fd8b9f34ab415b44cd87`** et HEAD final de livraison **`d22318ff18fac281bc5807dd78a735a203fd1ba6`**.
- Parent préparé par l'orchestrateur `67245337351c2fa6600028d981db4be2f3f32327`; comparaison GitHub : **2 commits d'avance, 0 de retard, 8 fichiers modifiés/ajoutés** (code `src/pokemind/meta.py`, tests `tests/test_meta.py`, rapports/README).
- Lecture indépendante du diff, `_discovery_scope`, `_load_discovery_checkpoint`, `_save_discovery_checkpoint`, `_known_discovery_ids`, `_refresh_candidates`, `sync_meta`, des scénarios de tests et des preuves Codex `RESULT/HANDOFF/NEXT_ACTION`, audit source.
- Arbre Git complet à `d22318ff...` : **122 entrées, `truncated=false`**, aucun vrai journal, deck personnel, SQLite, sauvegarde, image, token ou fichier privé `data/local/` suivi détecté.
- Aucun statut CI et aucun workflow PR attaché au HEAD dans les réponses du connecteur GitHub. `157` tests au prévol, neuf échecs attendus avant correction et **`171 passed`** au final, compilation, diff check, `PRAGMA integrity_check=ok`, conservation des 4 documents/87 sections, 5 combats, deck 60 cartes versionné et cache privé sont **rapportés par Codex**, non reproduits par ChatGPT. Pas d'API réelle appelée durant R2 selon Codex; le schéma demeure v7.

## D1 — exclusions correctement liées à leur filtre
- Scope construit par `_discovery_scope(format_code, platform_code, online)` : `discovery:PTCG:FORMAT:PLATFORM:0|1`. Les échecs `skipped` sont stockés sous `{scope}:tournament:{ID}` et `_known_discovery_ids(connection, discovery_scope)` ne relit que ce préfixe.
- Les anciens skips R1 non scoppés `tournament:ID` ne sont plus interprétés comme exclusions globales, sans migration destructive; les snapshots déjà `complete` peuvent encore être connus par ID global et les `partial` ne bloquent pas tout contexte.
- `refresh` peut relire les skips correspondant au filtre afin qu'un tournoi privé devenu public soit reconsidéré. Les critères `details` sont toujours contrôlés avant demande de `standings`/`pairings`.
- Tests paramétrés sur online true→false et inverse, plateforme, format, ancien skip, source devenue publique et vraie source privée; ils examinent les appels simulés.

## D2 — exploration profonde et reprise
- `metadata` stocke un JSON validé par scope avec `next_page`, `horizon_page`, `pending_page` (pas de changement SQL nécessaire). Le code ne fait pas de remise à zéro silencieuse des checkpoints après erreur de quota ou budget.
- À la reprise normale, une page de tête et une page de recouvrement sont sondées, suivies de la page profonde; si le traitement d'une page est interrompu faute de budget, celle-ci est relue avant d'avancer. Une dernière page vide ou partielle reste la frontière à revisiter.
- Deux tests importants : **36 IDs déjà archivés, premier lancement à budget 8 va jusqu'à la page 6; deuxième va à la page 7 et importe un inédit**, et **plusieurs lancements à budget 5** finissent par importer l'inédit. Insertions en tête, doublons, snapshot interrompu, 429, frontière réouverte et isolation des checkpoints lors de refresh sont également testés.
- Le budget HTTP initial, redirects/retries, en-têtes RateLimit, confidentialité HMAC et filtre tournois publics précoces restent inchangés par R2; les tests R1 sont conservés.

## Limites restantes (non bloquantes pour R2)
- L'API Limitless utilise une pagination susceptible de bouger; **le recouvrement réduit, mais n'élimine pas, les omissions** si beaucoup d'entrées sont insérées/supprimées entre snapshots.
- Un snapshot marqué `complete` reste identifié globalement par son ID; un fournisseur qui reclassifie le tournoi sous un autre format/plateforme/online peut nécessiter un **refresh explicite de l'ancien filtre** pour invalider le vieux snapshot avant redécouverte ailleurs. Ne pas promettre la découverte immédiate de toutes les reclassifications en mode passif.
- La construction de deck n'est pas encore certifiée légalement; sources normatives, TCGdex et données méta restent très partielles. Pas d'échantillon d'archétypes réel dans le seul essai initial, donc aucune estimation de matchup exploitable pour recommander une carte ou un deck personnel.
- Les tests `171 passed` ne sont pas une CI indépendante. La base locale complète et les données du joueur sont hors accès GitHub, et le contrôle de confidentialité sur l'arbre Git **ne démontre pas** l'absence de toute fuite hors Git.
- Aucune fusion, aucun scheduler Windows, aucune action sur compte TCG Live et aucune dépense de crédits n'a été exécutée.

## Prochaine tranche permise par le feu vert durable
**PM-0006A : socle d'analyse personnelle en lecture seule et contrats de recommandation conservateurs**, d'abord sans moteur autonome qui modifie des listes, sans commande « meilleur deck garanti », sans prétention de légalité ou disponibilité Live lorsque la résolution TCGdex est manquante. Préparer branche/prompt après cet audit; Codex exécute localement et s'arrête pour la prochaine vérification GitHub. Aucun merge ni changement de branche principale.
