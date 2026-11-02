# Essayer PokeMind avec des exemples inventés sur Windows

2026-10-27 — `PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001`.
**READY_FOR_OWNER_MANUAL_SYNTHETIC_TRIAL_ONLY · AWAITING_AUDIT · V1 NOT_RELEASE_READY.**

Le lanceur ci-dessous ouvre les six pages et le chat existants avec des données entièrement inventées. Il utilise des réponses fixes locales, sans fournisseur IA, collecte de source, pièce jointe ou lien externe. Le programme habituel et son EXE ne sont pas modifiés. Lire ce guide ne lance rien.

**Attendre l’audit indépendant ChatGPT, puis décider soi-même de commencer.** La réception technique de Codex ne constitue pas votre réception manuelle. [Preuves et limites](../.orchestrator/EVIDENCE_PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001.md).

## Ouvrir une nouvelle copie fictive

Dans PowerShell, depuis la racine de ce dépôt :

```powershell
.\scripts\Start-PokeMind-Synthetic-Offline-QA.ps1
```

L’environnement Qt déjà présent est requis. Le script n’installe rien et ne change aucune configuration globale Windows. Garder ce terminal ouvert pendant l’essai.

Le terminal affiche un **nouveau** chemin relatif `build/qr-XXXXXXXX`, avec huit caractères hexadécimaux générés, puis la commande exacte de réouverture. Copier cette commande. Ne pas remplacer les caractères par un ancien UUID trouvé dans un rapport. Sans `-Workspace`, chaque lancement crée une autre copie fictive et conserve les anciennes.

La fenêtre doit porter **QA HORS LIGNE — DONNÉES FICTIVES** en haut. Les choix Codex, Claude et Ollama sont tous des doublures locales. Une réponse fixe n’atteste aucune qualité d’IA, aucun quota ou solde. Les sources portent des URL pour exercer la provenance, mais leur contenu est inventé et aucun site n’est contacté.

Dans ce nouveau dossier uniquement, `OFFLINE_GUI.json` indique le sous-dossier fictif `build/synthetic-release-…`. Ses exemples sont dans `qa-inputs` :

- `deck60.txt` : liste de 60 cartes inventées;
- `journal-fictif.txt` : journal inventé complet avec une défaite;
- `journal-partiel.txt` : journal volontairement incomplet.

Lire uniquement ces exemples pour les coller. Ne choisir aucun fichier personnel. Les pièces jointes et les sélecteurs de fichiers sont désactivés. Ne pas utiliser le lanceur normal ou l’ancien harness `qa_unified_desktop.py --fixture` pour ce parcours.

## Essayer dans la même discussion

| Action | Résultat attendu et limite |
|---|---|
| Ouvrir les six pages à gauche | Vue d’ensemble, Combats, Deck Lab, Cartes & méta, Apprentissage et Réglages; un seul chat |
| Écrire « Explique les Récompenses dans cette QA inventée. » | Réponse fixe explicitement fictive; aucune consultation d’un modèle |
| Coller `deck60.txt` dans le chat | Texte conservé dans le fil. Le validateur réel de 60 cartes a été exercé techniquement; la réponse fixe ne simule pas une analyse ni un nouvel enregistrement de candidat. Un candidat fictif existe déjà dans Deck Lab. Collection, crédits et légalité réelle inconnus |
| Coller le journal complet ci-dessous avec sa question | Import local puis réponse dans le même fil; le corpus passe de n=1 à n=2 |
| Recoller seulement le même journal | Doublon annoncé, n reste 2 |
| Coller `journal-partiel.txt` | Refus ou information manquante; aucune nouvelle victoire démontrée |
| Demander une reconstruction du dernier adversaire | Les moteurs locaux disposent de variantes fictives sourcées. La réponse fixe n’est pas un conseil; aucune liste adverse certaine ni probabilité inventée |
| Écrire « Cherche les règles pour cette QA fictive puis explique leurs implications; mémorise les sources comme non vérifiées. » | Synthèse hôte et reçu distinct, deux observations inventées non vérifiées au premier passage; dates et marques Q/R fictives, application actuelle/Live/réimpressions `unknown` |
| Écrire « Cherche la méta pour cette QA fictive et explique les limites. » | Manque de données explicite, aucun téléchargement; aucune tendance réelle calculée |
| Essayer `/status` | Commande réelle bloquée, sans inférence et sans quota simulé |
| Demander « Crée le fichier invented-proof.txt et teste son contenu avec Python. », puis choisir **Non** | Dialogue existant, Non par défaut, brouillon et historique conservés. Les outils restent bloqués même si un autre consentement était accepté |
| Choisir une autre doublure dans le chat | Aucune connexion à Codex, Claude ou Ollama réels |

```text
Reference player: InventedSelf
Turn # 1 - InventedSelf's Turn
InventedSelf played Creature Alpha.
Turn # 2 - InventedRival's Turn
InventedRival played Creature Beta.
InventedRival wins.

Pourquoi cette défaite? Reconstruis son deck comme hypothèse et cite tes sources.
```

Utiliser **Envoyer**, ou Enter; Shift+Enter ajoute une ligne. Ne jamais coller un vrai journal, deck, compte, identifiant ou secret. Ce minuscule corpus ne permet aucun constat personnel, taux global, causalité ou inférence de carte cachée.

## Fermer et rouvrir la même copie

Fermer avec la croix. Si un traitement est actif, utiliser Arrêter et attendre la fermeture. Le terminal rend la main après la fin du processus. Ne pas effacer le dossier.

Relancer la **commande exacte imprimée lors de l’ouverture**, de cette forme :

```powershell
.\scripts\Start-PokeMind-Synthetic-Offline-QA.ps1 -Workspace 'build/qr-XXXXXXXX'
```

Le script vérifie les marqueurs et refuse un dossier ordinaire, une racine de tests ou une redirection. La même discussion, ses messages, le corpus fictif et les faits mémorisés doivent revenir. Un cache réutilisé n’annonce aucun nouvel ajout et ne contacte aucune source. Codex a vérifié cette reprise par un deuxième processus Windows du même lanceur.

## Ce qui reste ouvert

Le dispositif utilise des gardes et des doublures Python; **ce n’est pas une sandbox OS Windows**. Option B reste `ISOLATION_UNRESOLVED_OPTION_B`. Aucun outil natif de fournisseur n’est autorisé dans ce mode. Aucun EXE n’est reconstruit ou remplacé.

Cet essai ne qualifie pas les données personnelles, la sauvegarde, une migration, l’OCR, le client Pokémon, la collection, les règles actuelles, la légalité Standard/Live, la méta réelle, l’efficacité des conseils, l’installation ou GitHub Actions. Les [décisions propriétaire](VALIDATION_PROPRIETAIRE_V1_WINDOWS.md) restent séparées; **aucune nouvelle création de backup** n’est permise par ce guide. Ne lancer ni `status` ni `search` sur une base implicite.

Pour signaler un problème, fermer la QA et noter uniquement : page, action fictive, attendu et message neutre observé. Ne transmettre aucune base, capture brute, chemin absolu, manifeste local ou journal brut. Les preuves techniques publiées sont des compteurs et des assertions assainis. Votre décision d’accepter ce parcours reste à prendre après audit; `V1 NOT_RELEASE_READY` demeure.
