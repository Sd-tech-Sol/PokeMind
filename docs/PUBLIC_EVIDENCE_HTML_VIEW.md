# Consulter les preuves PUBLIC en HTML hors ligne

Depuis la racine PokeMind, la même commande que les vues humaine et JSON peut
produire un document HTML autonome sur la sortie standard :

```powershell
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --html
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --selector 581:1 --html
```

`--html` et `--json` sont mutuellement exclusifs. Sans ces options, la vue humaine
existante reste disponible. La commande ne crée aucun fichier, ne démarre aucun
serveur et ne lance aucun navigateur. Le HTML n’exécute aucun JavaScript et ne
charge ni image, police, feuille de style ni ressource réseau.

Pour ouvrir le rapport dans un navigateur local, **la sauvegarde est une action
manuelle distincte de l’utilisateur**. Par exemple, choisir un nom de fichier
neuf, puis lancer soi-même :

```powershell
# Action manuelle : crée le fichier nommé; choisir un nom non occupé.
python -m pokemind meta public-identity-explain --as-of 2026-10-23 --html | Out-File -Encoding UTF8 -NoClobber rapport-public.html
```

Ouvrir ensuite manuellement ce fichier dans le navigateur, en mode `file://`,
sans serveur. Vérifier le code de retour de la CLI : `0` signifie que le rapport
est disponible, `2` que la consultation est bloquée. Un échec de lecture avec
`--html` produit lui aussi une page complète, sur stdout, avec la raison neutre.
Un conflit d’options est refusé avant toute lecture et signalé sur stderr.

Le tableau de couverture sépare le **cache complet** de la **vue sélectionnée**.
Un filtre garde les dénominateurs de la composition choisie et ses placements
équivalents. Les liens de sélecteurs naviguent seulement à l’intérieur du
document produit; ils ne relancent aucune commande et ne téléchargent rien.

Utiliser Tab pour atteindre les liens et les sections « Consulter… », puis
Entrée ou Espace pour ouvrir les composants natifs `details/summary`. Un lien
d’évitement mène au rapport; les tableaux peuvent recevoir le focus pour leur
défilement horizontal. Les en-têtes, légendes et contours de focus sont intégrés.
La structure est vérifiée automatiquement; aucun essai réel de navigateur ou
de lecteur d’écran sur le PC n’est certifié par ces tests.

Chaque composition présente ses identités inconnues, ses sources datées comme
texte brut, puis les blocages et prochaines preuves séparés pour le présentiel
(`in_person`) et Pokémon TCG Live (`live`). La matrice rassemble les candidats
des éditions sans en choisir une. Les chaînes issues des caches sont échappées;
les liens générés ne contiennent que des fragments internes. Une CSP restrictive
interdit les ressources par défaut, les bases d’URL et les soumissions de formulaire.
Les URLs avec paramètres, identifiants ou schéma non admissible restent masquées.

**SOURCE_UNREVALIDATED / BLOCKED_SOURCE_SCOPE** reste visible, même sur une page
vide ou bloquée. La légalité demeure **unknown** pour les deux plateformes.
Une correspondance descriptive de catalogue ne prouve ni l’identité exacte,
ni une réimpression équivalente, ni la disponibilité Live. Les chiffres du cache
du PC sont `CODEX_LOCAL_REPORTED`; les tests GitHub portent sur des fixtures
inventées. **V1 NOT_RELEASE_READY** et les exigences A–J restent inchangées.

La consultation réutilise exactement le lecteur borné des deux SQLite PUBLIC
fixes autorisées, en lecture seule. Aucun autre cache, page, ledger, marqueur,
fichier personnel, deck joué, collection, journal ou compte n’est consulté.
Il n’y a aucun GET fournisseur. Une source absente ou non admissible arrête la
lecture sans recherche de remplacement. La stabilité observée des deux fichiers
ne garantit pas l’exclusion d’un écrivain concurrent ni l’isolement du système
de fichiers. Aucun export de données personnelles ou essai de partie réelle
n’est autorisé par cette fonctionnalité.
