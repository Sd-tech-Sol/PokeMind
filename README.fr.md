<p align="center"><img src="docs/assets/pokemind-logo.png" width="120" alt="Logo de PokeMind"></p>

# PokeMind

*Lire en [anglais / in English](README.md).*

**PokeMind est un compagnon Pokémon TCG Live pour Windows.** Il garde en mémoire tes combats, tes decks et
tes cartes sur ton PC, et te permet de les revoir avec un coach IA.

> ## État : préversion
>
> PokeMind **0.9.1** est une préversion publique (la première était 0.9.0). L'installateur Windows n'est
> **pas signé**, et avant ces versions PokeMind n'avait été utilisé **que par son auteur**. Attends-toi à des défauts et à
> des fonctions manquantes, et garde ta propre copie de ce qui compte.

## Auteur

PokeMind est une **création originale de Sébastien Dubé**. Ses seuls emprunts sont les composants libres
et les sources de données publiques listés dans [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

- Auteur et mainteneur : **Sébastien Dubé** — <https://github.com/Sd-tech-Sol>
- Licence : [MIT](LICENSE) — © 2026 Sébastien Dubé
- Décisions et mémoire du projet : [`.orchestrator/DECISIONS.md`](.orchestrator/DECISIONS.md) et
  [`PROJECT_VISION.md`](PROJECT_VISION.md)

## Téléchargement

L'installateur Windows est publié dans les [Releases GitHub](https://github.com/Sd-tech-Sol/PokeMind/releases)
sous le nom `PokeMind-Setup-<version>.exe`, avec son SHA-256 dans `PokeMind-Setup-<version>.exe.sha256`. Il s'installe pour ton compte seulement (sans droits
administrateur) dans `%LOCALAPPDATA%\Programs\PokeMind`, avec un raccourci dans le menu Démarrer.

L'installateur n'est pas encore signé : si Windows affiche « Windows a protégé votre ordinateur », choisis
**Informations complémentaires → Exécuter quand même**. Voir [CODE_SIGNING.md](CODE_SIGNING.md).

## Ce que fait PokeMind

- **Combats** : colle tes journaux TCG Live dans le chat ou dépose des fichiers `.txt` / `.log`. Chaque
  partie reste sur ton PC; les adversaires sont classés par défaites et chaque partie est montrée en frise.
- **Coach** : discute avec ton propre **Codex CLI**, **Claude Code** ou un modèle **Ollama** local. La liste
  à gauche d'**Envoyer** choisit ce que fait le message : **Coach** (mémoire locale, sans Internet),
  **Recherche web** (une collecte publique bornée) ou **Développement** (depuis le dossier des sources).
- **Deck Lab** : enregistre tes decks, compare-les, exporte des listes de 60 cartes à copier dans TCG Live.
- **Cartes & méta** : un classeur de cartes hors ligne (textes FR/EN, impressions, légalité datée) tiré du
  catalogue public TCGdex, et les résultats de tournois gardés sur ton PC.
- **Apprentissage** : les observations sont conservées avec la taille d'échantillon et les hypothèses sont
  révisées; aucun modèle n'est réentraîné.
- **Terminal** : Codex, Claude Code ou PowerShell dans un onglet de l'application.

## Ce que PokeMind ne fait pas

Ces absences sont des **choix de conception** :

- il ne joue **pas** à ta place : pas d'overlay, pas de bot, pas d'automatisation de clics, aucune
  interaction avec le client du jeu;
- il n'est **pas** fait pour les tournois officiels ni pour les endroits où l'assistance est interdite;
- il n'envoie **rien** à un moteur cloud sans ton accord (**Réglages → Coach IA**), et un journal collé
  n'atteint jamais un moteur capable d'exécuter des commandes;
- il n'a **ni compte, ni télémétrie, ni publicité**;
- il n'invente **pas** de taux de victoire, de coût en crédits ni ta collection quand ils sont inconnus.

## Langue

L'interface suit Windows au premier lancement : un Windows en français donne le français, toute autre
langue donne l'anglais. Change-la quand tu veux dans **Réglages → Général**; ton choix est conservé.

## Limites exactes de la version 0.9.1

| Limite | Détail |
|---|---|
| Plateforme | Windows 10 et 11, 64 bits. Ni macOS ni Linux ne sont construits. |
| Distribution | L'installateur n'est **pas signé** : Windows SmartScreen affiche un avertissement. |
| Catalogue de cartes | Un instantané public TCGdex épinglé (environ 25 Mo à télécharger, 175 Mo sur le disque); les nouvelles extensions arrivent avec une version suivante. |
| Coach | Dépend d'un moteur que tu installes toi-même (Codex CLI, Claude Code ou Ollama), avec son compte et ses limites. |
| Analyse des combats | Tirée de ce que montre le journal TCG Live; l'information cachée (main, Récompenses face cachée) reste inconnue. |
| Usage réel | Utilisé par une seule personne; les tests tournent sur des données inventées seulement. |
| Nom | **PokeMind** est un nom de projet de fans non officiel; aucune recherche de marque n'a été faite. |

## Sécurité et confidentialité

- Tes données restent dans `%LOCALAPPDATA%\PokeMind`, hors du dossier du programme; la désinstallation les
  conserve.
- L'usage du réseau est explicite : téléchargement unique du catalogue, illustrations de l'API publique
  TCGdex (désactivables), messages en **Recherche web**, et les moteurs cloud que tu autorises.
- Les journaux bruts, identités de joueurs et chemins de fichiers ne font jamais partie du contexte
  automatique du coach.
- Toutes les données de ce dépôt sont inventées; les tests ne lisent jamais un vrai dossier utilisateur.
- Les binaires de release sont vérifiés pour qu'aucun chemin de la machine de construction n'en sorte.

Détails : [SECURITY.md](SECURITY.md) et [PRIVACY.md](PRIVACY.md).

## Prérequis de développement

- Windows 10 ou 11, 64 bits;
- Python 3.13 (3.11 ou plus récent);
- pour l'installateur : [Inno Setup 6](https://jrsoftware.org/isinfo.php)
  (`winget install --id JRSoftware.InnoSetup -e --scope user`);
- facultatif : `signtool` du SDK Windows pour la signature.

## Installer et vérifier

```powershell
.\scripts\Install-PokeMindDesktop.ps1   # crée .venv-desktop avec les dépendances de l'application
.\scripts\Start-PokeMindDesktop.ps1     # lance l'application depuis les sources
python scripts\local_gate.py            # copie le dépôt dans un dossier temporaire puis lance toute la suite
```

Ne lance jamais la suite de tests directement dans le dépôt : certains tests écrivent sous `data/local`.
Tous les tests tournent localement sous Windows.

### Construire une release

```powershell
.\scripts\Build-PokeMindDesktop.ps1     # construit dist\PokeMind\PokeMind.exe
.\scripts\Build-PokeMindInstaller.ps1   # le vérifie, puis crée dist\installer\PokeMind-Setup-<version>.exe et son .sha256
```

`Build-PokeMindInstaller.ps1` échoue si `scripts/scan_binary_personal_paths.py` trouve le nom du compte, le
profil utilisateur ou le chemin du dépôt dans les fichiers du programme. La signature est facultative, voir
[CODE_SIGNING.md](CODE_SIGNING.md). La liste complète est dans
[docs/release-checklist.md](docs/release-checklist.md).

Guides : [anglais](docs/user-guide-en.md) · [français](docs/user-guide-fr.md).

## Contribuer

Lis [CONTRIBUTING.md](CONTRIBUTING.md) et le [code de conduite](CODE_OF_CONDUCT.md). Une règle passe avant
toutes les autres : **aucune contribution ne contient de vraies données personnelles** — pas de vrai journal
avec des noms de joueurs, pas de capture de compte, pas de chemin personnel.

Les issues et pull requests peuvent être rédigées en anglais ou en français.

## Développement assisté par IA

PokeMind est un projet original de Sébastien Dubé : l'idée, la vision produit, les exigences, les priorités,
ainsi que toutes les approbations et décisions finales, lui appartiennent. Le développement a été assisté
par IA : OpenAI ChatGPT pour l'architecture et les audits indépendants, OpenAI Codex et Anthropic Claude Code
pour l'implémentation, les tests, les audits, la documentation et les revues, sous sa direction et sa
relecture. Aucun outil d'IA n'est auteur, propriétaire ou mainteneur du projet, et leur utilisation n'implique
aucune affiliation avec OpenAI ou Anthropic, ni aucune approbation de leur part. La responsabilité et la
maintenance finales reviennent à Sébastien Dubé. Voir [AI_ASSISTANCE.md](AI_ASSISTANCE.md).

## Organisation du dépôt

Les notes de travail internes sont en français : [`.orchestrator/`](.orchestrator/) (décisions, passations,
résultats) et les plans `docs/LOT_*` racontent comment le projet a été construit; leur lecture n'est pas
nécessaire pour utiliser PokeMind ou y contribuer. L'historique des livraisons internes est dans
[docs/HISTORIQUE_README.md](docs/HISTORIQUE_README.md).

## Mentions légales

PokeMind est un projet de fans non officiel, sans lien avec Nintendo, The Pokémon Company, Creatures ou
GAME FREAK, ni approuvé par eux. Pokémon est une marque de ses propriétaires respectifs. Le logo de PokeMind
est une création originale. Les textes et images des cartes appartiennent à leurs propriétaires et sont
affichés depuis des sources publiques, avec leur attribution.

## Licence

[MIT](LICENSE) — © 2026 Sébastien Dubé. Le catalogue de cartes téléchargé par PokeMind provient de
[TCGdex](https://github.com/tcgdex/cards-database) (licence MIT).
