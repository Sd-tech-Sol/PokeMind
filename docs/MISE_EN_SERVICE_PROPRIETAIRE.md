# Mise en service propriétaire — actes séparés, préparés en H

**État actif J :** suivre `VALIDATION_PROPRIETAIRE_V1_WINDOWS.md` après audit
ChatGPT du dernier HEAD J. Cinq décisions avec commandes/entrées/effets/rollback/
risques/preuves. OCR sans exécution PATH par défaut; installation et captures
distinctes. Migration dans un nouveau clone seulement, jamais l'original.
Aucun acte personnel réel J. Les parcours H/I ci-dessous sont historiques.

Suite I : `PREMIER_USAGE_WINDOWS.md` fournit une démo sans base personnelle;
`LOT_I_RECOVERY_PROTOCOL.md` et `LOT_I_LOCAL_VISION.md` préparent les décisions
Windows restantes. Aucun acte propriétaire réel supplémentaire exécuté en I.
Collection et crédits restent facultatifs; absence de déclaration = unknown.

Aucun acte réel ci-dessous n'a été exécuté pendant H. Une prévisualisation ou un
prévol réussi ne vaut jamais permission. Garder les rapports contenant des valeurs
ou chemins personnels sous `data/local/`, jamais dans Git/API/CI.

`python -m pokemind owner-plan --step ETAPE --json` prépare une étape : intégrité,
FK/FTS, schéma, backup éventuellement vérifié, nouveau clone éventuellement absent.
Sortie agrégée sans données privées; aucune écriture, migration ni réseau. Le
statut OWNER_ACTION_REQUIRED indique encore l'ordre explicite à obtenir. La
simulation ne produit aucune preuve d'activation ou de capture réelle.

| Acte distinct | Prévol / commande préparée | Validation et annulation |
|---|---|---|
| Premier backup réel | `owner-plan --step backup`; `backup plan --destination DOSSIER`; après ordre, `backup create ... --apply --confirm-owner` | `backup verify`; SHA/SQLite/FK/FTS; abandonner avant apply si erreur; conserver tous résidus |
| Vérification clone éphémère | `restore verify --backup BACKUP --migrate-clone` | écrit uniquement clone temporaire; source réattestée; ordre séparé car lit/copiera le backup personnel |
| Clone neuf persistant | `owner-plan --step clone --backup BACKUP --clone CLONE_NEUF`; `restore plan`; après ordre, `restore apply ... --db CLONE_NEUF --apply --confirm-owner` | intégrité, FK, FTS, historiques; original conservé; activation hors ligne distincte |
| Remplacement cible existante | `owner-plan --step replace_existing` | BLOQUÉ dans le code; fermeture du client/SQLite ne lève pas le refus; aucune commande de contournement |
| Migration réelle 7→13 | `owner-plan --step migration --backup BACKUP` | d'abord backup vérifié et clone migré; ordre portant explicitement sur la vraie base, comparaison avant/après; revenir sur clone de backup si problème, pas d'écrasement automatique |
| Collection facultative | `owner-plan --step collection`; `collection import --help`, dry-run du fichier choisi | ordre distinct pour apply; rollback volontaire conservant audit; observation de combat ≠ possession |
| Crédits facultatifs | `owner-plan --step credits`; `credits set --help`, dry-run | date/montant volontaire, coût de fabrication inconnu sans tarif; aucune dépense automatique |
| Liaison combat/version | `owner-plan --step battle_attestation`; `deck link-battle --help` et `deck unlink-battle --help` | une paire explicitement choisie et attestée; provenance UTC actuelle, révocation séparée; jamais déduite |
| Moteur/calibration vision | `match benchmark-ocr --json`, profil privé | installation de moteur/langues et calibration sont des ordres distincts; pas de téléchargement H |
| Essai réel trois tours | `owner-plan --step vision_trial`; `match start/observe/review/advise/show` | entraînement où assistance permise; image volontaire; inconnues préservées; revoir/rejeter/révoquer l'observation; aucun pixel stocké |
| Scheduler | `owner-plan --step scheduler`; `knowledge scheduler ... --dry-run` | installation réelle reste désactivée; ordre/revue futurs, heures choisies, fuseau Windows attesté; statut OS et désinstallation réels distincts |
| Rétention | `owner-plan --step retention`; `backup retention ...` | preview seulement; apply BLOQUÉ même confirmé; ne pas purger manuellement comme contournement |

Les noms exacts des sous-commandes personnelles se consultent par `--help`;
aucune commande de ce tableau ne doit être copiée comme autorisation globale.
Le prévol vérifie un backup en tant que backup, **ne prouve pas qu'il correspond à
l'état courant du source**. Comparer l'historique et les données dans le clone avant
toute décision de migration/activation réelle. La simulation H teste ces comparaisons
sur une structure historique synthétique, pas sur la base personnelle.

## Répétition synthétique reproductible

`python -m pytest -q tests/test_lot_h_commissioning.py` crée la structure historique
7 sans tables futures, avec corpus/FTS, catalogue, deck de 60 et combat synthétiques.
Elle sauvegarde, restaure/migre seulement un clone 13 et compare les historiques et
les octets du source. Elle exerce trois observations PNG de marqueurs synthétiques
(**pas OCR**), revues textuelles, conseil, révocation, second backup/clone et readiness.
Intégrité/FK et recherche FTS vérifiées, rapport agrégé sans chemins privés.

L'essai propriétaire à trois tours n'est pas simulé en succès. `LOT_H_LOCAL_VISION.md`
décrit ses critères. Les gates restent bloquées pour le moteur/calibration réelle,
l'essai autorisé, la sûreté du remplacement/purge et le scheduler OS.

## Cadence préparée, sans système actif

```text
python -m pokemind knowledge cadence --start-utc 2026-10-31T00:00:00Z --daily-time 01:30 --deep-time 05:00 --days 14 --json
python -m pokemind knowledge scheduler --action install --daily-time 08:15 --deep-time 19:30 --windows-timezone "Eastern Standard Time" --dry-run --json
python -m pokemind knowledge scheduler --action uninstall --dry-run --json
```

Les horaires sont des exemples synthétiques, pas un choix du propriétaire. La
simulation traite Toronto quotidiennement et mardi/vendredi en profondeur,
transmet DeepTime, reporte la minute printanière inexistante à la première valide
et choisit la première occurrence automnale. Le comportement DST réel de Windows
reste à vérifier après autorisation. Annuler/installer/désinstaller en dry-run ne
contacte aucun planificateur; OS demeure OWNER_ACTION_REQUIRED.
