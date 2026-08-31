# datagouv-toolkit

Toolbox en ligne de commande pour découvrir, évaluer, sélectionner et télécharger des jeux de données publiés sur data.gouv.fr, puis transmettre proprement les ressources retenues à des outils comme R, Python, DuckDB ou d'autres outils Unix.

Le projet n'a pas vocation à remplacer ces outils d'analyse. Il se concentre sur la phase amont : exploration du catalogue, résolution d'un dataset, inspection des métadonnées, sélection des ressources, téléchargement et audit structurel léger.

## Installation

Depuis un clone du dépôt :

```bash
python -m pip install -e .
```

L'installation fournit une commande principale unique :

```bash
datagouv --help
```

Les anciens points d'entrée spécialisés (`datagouv-download`, `datagouv-workflow`, `datagouv-inspect-csv` et `datagouv-catalog-stats`) restent disponibles pour compatibilité.

## Tutoriel

Pour une prise en main progressive avec explications des notions d'API HTTP, JSON, datasets, ressources, métadonnées, filtrage, sélection non interactive, handoff, data profiling et reproductibilité :

- [Tutoriel approfondi de `datagouv`](TUTORIAL.md)

## Workflow cible

```text
explorer le catalogue
        ↓
résoudre un dataset
        ↓
évaluer et filtrer ses ressources
        ↓
sélectionner sans interaction si nécessaire
        ↓
obtenir des URL ou un manifeste
        ↓
télécharger éventuellement
        ↓
R / Python / DuckDB / jq / autres outils
```

## Utilisation

### Rechercher un dataset

```bash
datagouv search "accidents corporels"
```

### Résoudre un dataset sans interaction

Lorsque plusieurs résultats correspondent à une recherche, le comportement par défaut reste interactif. Pour un script, `--first` choisit le premier résultat après application éventuelle des filtres `--producer` et `--title` :

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --first
```

Pour les automatisations sensibles à la reproductibilité, un identifiant stable de dataset reste préférable à une recherche textuelle.

### Inspecter et sélectionner ses ressources

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

La commande `resources` peut filtrer les ressources avant téléchargement :

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "2024" \
  --first
```

Pour obtenir uniquement les URL sélectionnées, une par ligne :

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --first \
  --urls
```

Cette sortie est conçue pour les pipelines Unix, par exemple :

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --first \
  --urls | xargs -n1 wget
```

Pour obtenir un manifeste JSON compact décrivant le dataset et les ressources sélectionnées :

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --first \
  --manifest | jq .
```

Le manifeste contient pour chaque ressource son identifiant, son titre, son format, sa taille connue et son URL. `--json` reste disponible pour exposer les objets ressource sélectionnés plus largement. Les modes `--json`, `--urls` et `--manifest` sont exclusifs.

### Afficher les métadonnées

```bash
datagouv metadata \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Pour obtenir le JSON brut du dataset :

```bash
datagouv inspect \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

### Télécharger une ressource

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data
```

Pour obtenir un résultat exploitable par une machine, ajouter `--json` :

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data \
  --json | jq '.resources[] | {path, downloaded}'
```

La sortie JSON contient le dataset résolu, le répertoire de destination et le résultat de chaque ressource, notamment son chemin local et le booléen `downloaded`.

### Télécharger et auditer automatiquement

```bash
datagouv workflow \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data \
  --audit-dir audits
```

Le workflow résout le dataset, sélectionne les ressources, les télécharge puis audite automatiquement les fichiers CSV. Sa sortie structurée est disponible avec `--json`.

### Auditer un CSV local

```bash
datagouv inspect-csv fichier.csv
```

L'audit structurel est également disponible comme objet JSON :

```bash
datagouv inspect-csv fichier.csv --json \
  | jq '.file, .candidate_keys, .duplicate_rows'
```

Cette commande aide à évaluer un fichier avant son traitement avec un outil d'analyse externe. Elle expose notamment dimensions, types, valeurs manquantes, cardinalités, clés candidates, distributions à faible cardinalité, doublons et aperçu.

### Caractériser les ressources d'un dataset

```bash
datagouv stats \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

### Explorer un snapshot du catalogue

```bash
datagouv catalog-stats "transport" \
  --snapshot snapshot/2026-08-25
```

Avec filtres et sortie structurée :

```bash
datagouv catalog-stats "transport" \
  --snapshot snapshot/2026-08-25 \
  --format csv \
  --json | jq '.datasets, .resources, .rankings.formats'
```

Cette commande sert à explorer et caractériser un snapshot local du catalogue avant de cibler des datasets ou ressources ; elle n'a pas vocation à effectuer l'analyse scientifique des données téléchargées.

## Commandes disponibles

```text
datagouv search         Recherche dans le catalogue
datagouv dataset        Résumé et résolution d'un dataset
datagouv resources      Sélection et handoff des ressources
datagouv metadata       Métadonnées structurées
datagouv stats          Caractérisation des ressources
datagouv inspect        JSON brut du dataset
datagouv organization   Informations sur une organisation
datagouv download       Téléchargement de ressources
datagouv workflow       Téléchargement + audit CSV
datagouv inspect-csv    Audit structurel d'un CSV local
datagouv catalog-stats  Exploration d'un snapshot du catalogue
```

## Architecture

- `cli.py` : interface en ligne de commande unifiée `datagouv`.
- `datagouv.py` : client et fonctions d'exploration/résolution de datasets data.gouv.fr.
- `download_resources.py` : sélection et téléchargement génériques de ressources.
- `dataset_workflow.py` : enchaînement résolution → téléchargement → audit CSV.
- `inspect_csv.py` : audit structurel générique d'un CSV.
- `catalog_stats.py` et `catalog_report.py` : exploration et caractérisation reproductibles d'un snapshot du catalogue.
- `normalize.py` : normalisation des métadonnées.
- `tests/` : tests unitaires.
- `datasets/` : cas d'usage et pipelines spécifiques, hors cœur générique du toolkit.

## Réutilisations

- [20 ans d’accidents corporels en France — BAAC 2005–2024](reports/baac-2005-2024/)

## Qualité

La vérification locale complète est centralisée dans le `Makefile` :

```bash
make check
```

Cette cible exécute Ruff, mypy, Bandit, les tests avec couverture, la construction des distributions, `twine check` et un smoke test de la CLI installée.
