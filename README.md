# datagouv-toolkit

Outils génériques pour explorer, télécharger, inspecter et analyser des jeux de données publiés sur data.gouv.fr.

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

## Utilisation

### Rechercher un dataset

```bash
datagouv search "accidents corporels"
```

### Inspecter ses ressources

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

### Afficher ses métadonnées

```bash
datagouv metadata \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Pour obtenir le JSON brut :

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

Le workflow résout le dataset, sélectionne les ressources, les télécharge puis audite automatiquement les fichiers CSV.

### Auditer un CSV local

```bash
datagouv inspect-csv fichier.csv
```

Pour rediriger un audit volumineux :

```bash
datagouv inspect-csv fichier.csv > audit.txt
```

### Statistiques sur les ressources d'un dataset

```bash
datagouv stats \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

### Analyser un snapshot du catalogue

```bash
datagouv catalog-stats "transport" \
  --snapshot snapshot/2026-08-25
```

Avec filtres :

```bash
datagouv catalog-stats "énergie" \
  --snapshot snapshot/2026-08-25 \
  --license fr-lo-2.0 \
  --frequency annual
```

## Commandes disponibles

```text
datagouv search         Recherche dans le catalogue
datagouv dataset        Résumé d'un dataset
datagouv resources      Liste des ressources
datagouv metadata       Métadonnées structurées
datagouv stats          Statistiques sur les ressources
datagouv inspect        JSON brut du dataset
datagouv organization   Informations sur une organisation
datagouv download       Téléchargement de ressources
datagouv workflow       Téléchargement + audit CSV
datagouv inspect-csv    Audit d'un CSV local
datagouv catalog-stats  Analyse d'un snapshot du catalogue
```

## Architecture

- `cli.py` : interface en ligne de commande unifiée `datagouv`.
- `datagouv.py` : client et fonctions d'exploration/résolution de datasets data.gouv.fr.
- `download_resources.py` : téléchargement générique de ressources.
- `dataset_workflow.py` : enchaînement résolution → téléchargement → audit CSV.
- `inspect_csv.py` : audit structurel générique d'un CSV.
- `catalog_stats.py` : statistiques reproductibles à partir d'un snapshot du catalogue.
- `normalize.py` : normalisation des métadonnées.
- `tests/` : tests unitaires.
- `datasets/` : pipelines spécifiques à certains jeux de données.
- `datasets/baac/` : premier cas d'usage, données BAAC.

## Réutilisations

- [20 ans d’accidents corporels en France — BAAC 2005–2024](reports/baac-2005-2024/)

## Qualité

```bash
ruff check .
mypy . --ignore-missing-imports
pytest -q
bandit -q *.py
```
