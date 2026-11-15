# RESULT — PM-RELEASE-095-OWNER-INSTALL-001 : PokeMind 0.9.5 installé chez le propriétaire (D-293), 2026-11-07

Exécuteur : Claude Code (Opus 5.5), sur le PC Windows du propriétaire. Mandat : premier bloc de `NEXT_ACTION.md` →
`NEXT_PROMPT.md` (`6cacf42`, activé `f858b9f`), GO explicite du propriétaire (« oui », ChatGPT, 2026-11-07), confirmé dans
la demande de la session (installation réelle autorisée, sous réserve des contrôles de sauvegarde et d'intégrité).
Statut : **INSTALLED_OWNER_VERIFICATION_PENDING**. Réception par le propriétaire **non déclarée acceptée**. Pas VERIFIED,
pas `RELEASE_READY`. Rapport précédent : [archive/2026-11/RESULT_PM-RELEASE-095-WINDOWS-CANDIDATE-001_D292_2026-11-07.md](archive/2026-11/RESULT_PM-RELEASE-095-WINDOWS-CANDIDATE-001_D292_2026-11-07.md).
**STOP pour audit ChatGPT et inspection du propriétaire.**

## 0. Prévol
- `git fetch` + `git pull --ff-only` : `a21e98a` → `f858b9f` (4 commits docs ChatGPT), arbre propre, aucun reset/rebase/force.
- Lus : AGENTS.md, SESSION_CONTINUITY, WORKFLOW_ADOPTION_V2, STATE, NEXT_ACTION, NEXT_PROMPT, HANDOFF, RESULT,
  l'audit `VERIFICATION_PM-RELEASE-095-WINDOWS-CANDIDATE-001`, `packaging/PokeMind.iss`, `data_location.py`, `app.py`.
- Écart d'état constaté : `STATE.json` décrivait encore le mandat précédent (ChatGPT n'avait mis à jour que NEXT_ACTION).
  Retard, pas contradiction : NEXT_ACTION (premier bloc) et l'audit `cff6bdb` concordent; STATE mis à jour ici.
- Aucun changement de code ni d'emballage depuis `24e9cc5` (`git diff 24e9cc5 HEAD -- packaging scripts src` vide).

## 1. Protection des données (bloquante) — OK
- Processus : aucun PokeMind ouvert, mutex `PokeMindDesktopRunning` absent. Une autre session Claude Code (dépôt de
  développement, pas un sous-processus de PokeMind) était présente mais **inactive** depuis le 2026-11-06, sans
  sous-processus : laissée intacte, ni tuée ni utilisée.
- Chemin de données effectif : application installée = mode autonome → `%LOCALAPPDATA%\PokeMind` (aucune variable
  `POKEMIND_DATA_ROOT` utilisateur/machine/processus), vérifié dans `data_location.standalone()` et confirmé ensuite
  par le journal technique (« Mode autonome · données dans le dossier de l'application »). Pas sur OneDrive, aucun lien
  symbolique ni point de jonction; espace libre largement suffisant.
- **Sauvegarde complète** : copie (robocopy, code 1 = succès) dans un dossier horodaté privé sous `%LOCALAPPDATA%`, hors
  du dossier de données et hors du dépôt; droits hérités (propriétaire, SYSTEM, Administrateurs; lecture refusée au
  groupe bac à sable Codex). Contenu jamais affiché.
  - **306 / 306 fichiers, 183 206 893 octets**; SHA-256 de chaque fichier source = copie (0 manquant, 0 en trop, 0 différent).
  - Source stable pendant la copie (re-hachage après copie : 0 changement); lecture avec partage en lecture seule (aucun
    fichier tenu en écriture par un autre processus).
  - Restauration à blanc (robocopy `/L` copie → source) : 306 fichiers, 0 à copier, 0 échec.
  - Manifeste SHA-256 privé à côté de la copie (jamais dans Git). Original laissé en place.
- Le dossier d'archives de l'application (1 fichier) est inchangé avant/après.

## 2. Vérification du candidat (bloquante) — MATCH
- `dist/installer-candidate-0.9.5-24e9cc5/PokeMind-Setup-0.9.5.exe` présent, 39 739 700 octets, pas de lien.
- `Get-FileHash -Algorithm SHA256` = `6E7E5CB2D63FA05BB96123E3A9DF6CFACEB37E90D21C9CD7417564526C0D68CB` : **MATCH** avec le
  mandat, le fichier `.sha256` et le RESULT D-292; recalculé juste avant le lancement : identique.
- PE du Setup : `FileVersion = ProductVersion = 0.9.5`; Authenticode : `NotSigned` (attendu).
- AppId de production `{9B4E3B52-6C1D-4E7A-9F3B-5A2C8D1E7F40}` dans `packaging/PokeMind.iss` = clé de désinstallation
  de la 0.9.4 installée = en-tête du `unins000.dat` existant. AppId QA non utilisé. `.iss` : installation par
  utilisateur, `{localappdata}\Programs\PokeMind`; seule suppression : `{app}\_internal` (programme, pas de données).

## 3. Mise à niveau réelle 0.9.4 → 0.9.5
- Avant : registre `DisplayVersion 0.9.4`, `PokeMind.exe` 0.9.4, 800 fichiers programme, raccourcis Menu Démarrer et
  Bureau vers l'EXE installé.
- Assistant Inno **normal, interactif**, seul argument `/LOG` (journal privé hors Git); ni `/SILENT`, ni `/VERYSILENT`,
  ni `/RELAUNCH`; aucune désinstallation préalable. Le propriétaire a fait défiler l'assistant.
  - Journal Inno : Restart Manager « aucune application n'utilise nos fichiers »; « Will append to existing uninstall
    log » (même AppId); « Installation process succeeded »; pas de redémarrage. **Code de sortie 0.**
- Après : registre `DisplayVersion 0.9.5`, **une seule** clé PokeMind; `unins000.*` seulement (pas de `unins001`);
  `PokeMind.exe` `FileVersion = ProductVersion = 0.9.5`, SHA-256 `7121BBEB277594164621DDEECD6FAA3331FAFFB87EABD55024BB2BD6E0E9E6FF`
  = EXE du candidat testé (D-292). Fichiers installés = **exactement** la distribution 0.9.5 de `24e9cc5` : 797/797,
  0 manquant, 0 différent, 0 en trop (hors `unins000.*` et `LICENSE.txt`). Les deux raccourcis pointent vers l'EXE installé.
- Fumée de l'EXE **installé** (mode `POKEMIND_DESKTOP_SMOKE=1`) dans un root inventé **vide**, `LOCALAPPDATA`/`APPDATA`/
  `TEMP` redirigés, proxys fermés, `PATH` réduit : gelé, fenêtre visible, plateforme `windows`, **7 pages**, terminal,
  import et activité disponibles; aucun processus enfant. Code **2 attendu** (root vide : ni rapport ni deck, donc
  `ready` faux). Données réelles non touchées par la fumée (dernière écriture antérieure au lancement).
- **Non fait par l'agent** (contenu personnel, réseau) : ouverture de Deck Lab › Statistiques sur les vraies données,
  collecte Limitless, appel LLM, inspection des decks/journaux/préférences. L'onglet Statistiques de ce même binaire
  (SHA identique) a été fumé en isolé en D-292 (chiffres = oracle; aucun pourcentage sans échantillon).

## 4. Intégrité des données après installation
Comparaison locale au manifeste pré-installation : **0 fichier préexistant manquant**; sauvegarde toujours intacte
(306/306, 0 différence). Changements, tous attribués par horodatage au **PokeMind 0.9.5 lancé**, aucun par l'installateur :
- L'assistant a **lancé PokeMind 0.9.5** à sa fermeture (21:48:59, case « Lancer PokeMind » cochée par défaut), avant
  la comparaison prévue; puis le propriétaire l'a rouvert (21:55:59). L'instance est restée ouverte : non fermée par l'agent.
- Pendant la première session de l'application (21:49–21:55) : catalogue public TCGdex réécrit par la mise à jour de
  catalogue de l'application (2 fichiers préexistants modifiés, données publiques, plus des fichiers de rapport neufs)
  et une nouvelle campagne publique liée au clavardage, avec ses fichiers de contrôle.
- Au second lancement (21:56) : journal technique allongé, un fichier d'état d'analyse réécrit (même taille), un petit
  fichier de réglage à la racine des données réécrit (taille réduite), un nouveau fichier d'application.
- Totaux : 306 → 315 fichiers; 5 préexistants modifiés, 9 nouveaux (types : JSON, SQLite, texte). Rien n'a été restauré
  ni écrasé.

## 5. Anomalies / réserves
1. Lancement automatique par l'assistant avant le contrôle d'intégrité « installation seule ». Effet borné : les écritures
   sont celles de l'application elle-même (horodatages et journal technique), aucun fichier préexistant perdu; la
   sauvegarde vérifiée reste la référence. Pour la suite : décocher « Lancer PokeMind » si un contrôle doit précéder.
2. Le fichier de réglage racine a rétréci au lancement de la 0.9.5 (406 → 352 octets) : migration ou réécriture normale
   probable, **non inspectée** (contenu privé). À confirmer visuellement par le propriétaire (langue, thème, réglages).
3. Mise à jour du catalogue et campagne publique : trafic réseau de l'application déclenché pendant l'usage du
   propriétaire, pas par l'agent.
4. SmartScreen, rendu 125 % DPI et mise à jour silencieuse depuis l'application : non testés (réserves de l'audit).

## 6. À faire par le propriétaire (inspection visuelle, sans capture par l'agent)
Démarrage, langue/thème, Combats (parties et saison), Deck Lab (decks, deck principal) et **Statistiques** (date
d'échantillon, aucun chiffre sous les seuils), historique du coach. En cas de problème grave : ne rien supprimer;
la sauvegarde permet un retour arrière, **sur autorisation explicite seulement** (réinstaller le Setup 0.9.4 conservé
puis recopier la sauvegarde, application fermée).

## 7. Git / publication
Commit unique de rapport (ce fichier, HANDOFF, NEXT_ACTION, NEXT_PROMPT consommé, STATE, DECISIONS D-293, archive).
Aucun fichier local, sauvegarde, journal ou manifeste dans Git. Aucun push public, tag ni release.
