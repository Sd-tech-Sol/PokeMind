# PM-V1-LIVE-FR-EN-UI-001 — preuves assainies de localisation native

2026-10-28 Québec. Départ `7f125bfdb8a140e75abf33376d87ae70d27585cf`, source finale **`51aa92e8cdd04e7e2c7bca4d4a478b29dcb55517`**, branche `work/pm-v1-lotj-final-readiness-windows`. Nouvelle demande manuelle FR/EN sans redémarrage; anciennes autorisations privées non reconduites. Résultats **rapportés localement par Codex**, audit indépendant et réception propriétaire en attente.

## Comportement livré

- Réglages → Langue de l’application : Français (Québec) / English. Effet immédiat et préférence persistante; même fenêtre, mêmes pages, filtres, onglets, brouillon, historique, session, statistiques et position de lecture.
- Catalogue local de 512 équivalents, textes appariés FR/EN et recomposition des seuls segments applicatifs. Libellés de navigation, réglages dont descriptions de confidentialité, tableaux, résultats vides, coach, activités/progressions, états/erreurs, import et reçus publics, statistiques et accessibilité couverts. Source de la carte indépendante du choix de langue UI.
- Repeinture des graphiques sans recalcul du corpus; signaux bloqués pendant la retraduction des listes/tableaux pour éviter requêtes ou changements de sélection. Changement de langue sans réappliquer le thème ni reconstruire le chat.
- Traducteur Qt `qtbase_fr.qm` embarqué : boutons natifs et sélecteurs de fichiers suivent le choix. Aucun service réseau de traduction ni dépendance supplémentaire.
- Noms, textes et événements sourcés, URL, identifiants, exports et contenu historique restent opaques et inchangés. Nouveaux messages applicatifs et réponses locales dans la langue choisie; consigne FR/EN ajoutée aux futures demandes du coach (aucun fournisseur réel appelé ici).
- `assistant/receipts.py` et `public_source_fields.py` acceptent des fonctions de présentation facultatives; validation, provenance, seuils, compteurs, schémas et sortie CLI française par défaut conservés. Aucun import Qt dans ces modules ni dans les services/projections purs.

## Vérifications

| Contrôle | Résultat local final |
| --- | --- |
| Suite native Qt complète (incluant neuf nouveaux tests FR/EN) | 93 réussis, 0 échec/erreur/skip |
| Services et régression des reçus/recherche/champs publics | 67 réussis, 0 échec/erreur/skip |
| Total distinct, sans addition des répétitions | **160 réussis** |
| Échanges en → fr → en → fr, fenêtre/pages identiques | Conforme |
| Brouillon/historique/session/rapport, filtres/onglet/effectifs et défilement | Conservés; aucun load/deck_options/adaptateur déclenché par la langue |
| Dialogues réels Oui/Non, Cancel Qt et choix de fichier simulé | FR/EN conformes; aucun parcours réel de fichiers privés |
| Réouverture sur fixture, anglais + thème/réduction/menu/favoris persistants | Conforme |
| Reçus localisés : nom FR et URL contenant un mot traduisible | Données, compteurs, URL et version CLI originale conservés |
| Vérification visuelle native sombre/clair, cartes/decks/statistiques, retour FR, 1100×700 | Conforme; Envoyer visible |
| Preflight sans DB | RUNTIME_READY, 0 écriture/réseau, base propriétaire non ouverte |
| Demo intégrée sans DB personnelle | SYNTHETIC_REHEARSAL_PASSED, réseau/DB propriétaire false |
| Hygiène et diff préparé | repo_hygiene=ok; diff --check sans erreur après normalisation des espaces du catalogue |

Historique des corrections ordinaires : un premier test modal attendait « Yes/No » sans les accélérateurs natifs `&`; assertion ajustée, boutons/retours standard préservés. Une passe Qt intermédiaire a terminé 91 réussis/1 échec : l’URL fictive du nouveau test contenait une query interdite par le validateur existant, observation correctement rejetée. Fixture corrigée vers une URL admissible, aucune validation relâchée. Revue de code a aussi préservé les variantes des titres de frise lors de l’échappement HTML et le défilement du chat. Passe finale complète **93/93**, suite de régression **67/67**. Espaces terminaux représentés explicitement dans le catalogue, dictionnaire des 512 entrées comparé identique avant/après; aucun changement de sens.

Toutes les suites de cette tranche utilisent des workspaces synthétiques neufs. Reçus finaux : 0 refus de garde, 0 GET source réel, 0 appel fournisseur réel. Pas de prétention d’isolation réseau/OS. Captures, logs, JUnit, workspaces, empreintes et distributions restent locaux et ignorés, non publiés.

## Production Windows et installation

Build production `--onedir --windowed` en staging neuf avec répertoires temporaires dédiés, **exit0**. Comparaison du code embarqué : `window`, `widgets`, `card_art`, `charts`, `insights`, `services`, `motion`, `i18n`, `locale_text`, `translations`, `assistant.receipts`, `public_source_fields`, et entrée `app` : **13 conformes**. Aucun helper QA embarqué; `qtbase_fr.qm` présent.

Vrai EXE frozen lancé uniquement avec une nouvelle fixture indépendante, préférence anglaise et réseau applicatif désactivé. Fenêtre visible, plateforme Windows, six pages, rapport, liste exacte60, galerie, import, activité et réglage démarrage présents; **exit0**. Capture anglaise inspectée. Octets de la DB synthétique schéma7 identiques avant/après; aucune équivalence revendiquée avec une base personnelle.

Distribution installée au même `dist/PokeMind/PokeMind.exe` fermé. Chemins de déplacement résolus à l’intérieur du projet et absence de redirection contrôlés avant les déplacements. Inventaires réservés aux binaires/supports : **788 anciens fichiers conservés**, **788 nouveaux conformes au candidat**. Anciennes distributions retenues, aucune suppression. Aucune création de sauvegarde DB, aucun manifeste privé, aucun lancement propriétaire, aucun inventaire ou comptage personnel. Réception réelle de l’utilisateur **non effectuée**.

## Fin et limites

**REPORTED_COMPLETE_LOCAL / AWAITING_AUDIT**, autorisation consommée; V1 **NOT_RELEASE_READY**, CI **AWAITING_EVIDENCE**. La source testée/compilée est le SHA indiqué en tête; le commit final ne contient ensuite que les rapports. Contrôler après push le HEAD exact et ses jobs/annotations, sans relance de CI ni modification de budget/workflow. L’état antérieur de la CI est un blocage de budget sans étapes exécutées; aucun succès final présumé. Audit indépendant ChatGPT à partir du HEAD publié, puis essai propriétaire du choix de langue dans son EXE habituel seulement. Pas de reprise automatique d’anciens mandats.

## Clôture de session demandée par le propriétaire

2026-10-28 Québec. Livraison publiée `3035d9a712787237c4e4afc50940f30a085b07a8`, HEAD local/distant identiques avant la clôture, dépôt propre. CI exacte : [run 40643154561](https://github.com/Sd-tech-Sol/PokeMind-dev/actions/runs/40643154561), `failure` car budget Actions, Windows/Ubuntu zéro étape (jobs non démarrés). Aucun rerun ni test produit à la clôture. Passation documentaire ajoutée; source `51aa92e8cdd04e7e2c7bca4d4a478b29dcb55517` et distribution livrée inchangées. État **AWAITING_AUDIT** conservé; nouvelle CI documentaire à contrôler au SHA de clôture, sans la présumer réussie.
