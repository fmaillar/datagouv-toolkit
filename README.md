# datagouv-toolkit

Outils génériques pour explorer, télécharger, inspecter et analyser des jeux de données publiés sur data.gouv.fr.

## Architecture

- `datagouv.py` : exploration et résolution de datasets data.gouv.fr.
- `download_resources.py` : téléchargement générique de ressources.
- `dataset_workflow.py` : enchaînement résolution → téléchargement → audit CSV.
- `inspect_csv.py` : audit structurel générique d'un CSV.
- `catalog_stats.py` : statistiques reproductibles à partir d'un snapshot du catalogue.
- `normalize.py` : normalisation des métadonnées.
- `tests/` : tests unitaires.
- `datasets/` : pipelines spécifiques à certains jeux de données.
- `datasets/baac/` : premier cas d'usage, données BAAC.

## Exemples

### Rechercher un dataset

```bash
python datagouv.py search "accidents corporels"
```

### Inspecter ses ressources

```bash
python datagouv.py resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

### Télécharger une ressource

```bash
python download_resources.py \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data
```

### Télécharger et auditer automatiquement

```bash
python dataset_workflow.py \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data
```

### Auditer un CSV local

```bash
python inspect_csv.py fichier.csv
```

Pour rediriger un audit volumineux :

```bash
python inspect_csv.py fichier.csv > audit.txt
```

### Analyser un snapshot du catalogue

```bash
python catalog_stats.py "transport" \
  --snapshot snapshot/2026-08-25
```

Filtres disponibles notamment :

```bash
python catalog_stats.py "énergie" \
  --snapshot snapshot/2026-08-25 \
  --license fr-lo-2.0 \
  --frequency annual
```

## Qualité

```bash
ruff check .
mypy .
pytest -q
bandit -q *.py
```
