# Tutoriel approfondi de `datagouv`

Ce tutoriel présente `datagouv` progressivement, depuis la découverte du catalogue jusqu'à la sélection, au handoff et au téléchargement des ressources. L'objectif n'est pas de remplacer R, Python, DuckDB ou d'autres outils d'analyse : `datagouv-toolkit` intervient surtout en amont, pour explorer data.gouv.fr, évaluer ce qui est disponible, sélectionner les bonnes ressources et les transmettre proprement à l'outil de travail choisi.

## 1. Le modèle de données de data.gouv.fr

Avant d'utiliser la CLI, il faut distinguer trois objets.

```text
data.gouv.fr
    │
    ├── organisation
    │     └── publie des datasets
    │
    └── dataset / jeu de données
          │
          ├── métadonnées
          │
          └── ressources
                ├── CSV
                ├── JSON
                ├── ZIP
                ├── PDF
                └── autres fichiers
```

Une **organisation** représente un producteur de données. Un **dataset** est un jeu de données au sens documentaire et logique. Une **ressource** est un fichier ou un accès concret aux données.

Cette distinction est fondamentale : rechercher un dataset dans le catalogue n'est pas encore télécharger ses données.

## 2. Comprendre une CLI à sous-commandes

Après installation du projet en mode éditable :

```bash
python -m pip install -e .
```

la commande principale est :

```bash
datagouv --help
```

Sa forme générale est :

```text
datagouv <commande> [arguments] [options]
```

Par exemple :

```bash
datagouv search "qualité de l'air"
```

Une option commence généralement par `-` ou `--` :

```bash
datagouv search "qualité de l'air" --limit 5
```

Chaque sous-commande possède sa propre aide :

```bash
datagouv search --help
datagouv dataset --help
datagouv resources --help
datagouv download --help
```

## 3. Rechercher un dataset

```bash
datagouv search "qualité de l'air"
```

`datagouv` interroge l'API publique de data.gouv.fr et présente les résultats dans le terminal. Avec `--json`, les résultats peuvent être consommés par un autre programme.

```bash
datagouv search "qualité de l'air" --limit 5 --json | jq .
```

## 4. Recherche textuelle, identifiant stable et `--first`

Une commande comme :

```bash
datagouv dataset "qualité de l'air"
```

peut correspondre à plusieurs datasets. Par défaut, `datagouv` propose alors une sélection interactive.

Pour un usage non interactif, `--first` sélectionne le premier résultat **après** application éventuelle des filtres `--producer` et `--title` :

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --first
```

`--first` est utile dans un shell, un job CI ou un script. Pour une automatisation qui doit être strictement reproductible dans le temps, un identifiant stable de dataset reste préférable à une recherche textuelle.

## 5. Réduire l'ambiguïté avec des filtres

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --title "accidents"
```

Le raisonnement devient :

```text
recherche textuelle
        ↓
datasets candidats
        ↓
filtre producteur / titre
        ↓
sélection interactive ou --first
        ↓
dataset retenu
```

## 6. `dataset` : obtenir une vue synthétique

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

La commande présente une vue adaptée à une lecture humaine. Pour une sortie structurée :

```bash
datagouv dataset "accidents corporels" --first --json | jq .
```

## 7. `resources` : évaluer, filtrer et sélectionner avant téléchargement

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Un dataset peut référencer plusieurs ressources avec un titre, un format, une URL et parfois une taille connue.

La commande `resources` est maintenant l'étape centrale entre la découverte d'un dataset et son acquisition. Elle peut filtrer les ressources :

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "2024" \
  --first
```

Cette étape permet d'évaluer ce qui sera transmis ou téléchargé sans encore écrire les fichiers localement.

### Sortie JSON complète des ressources sélectionnées

```bash
datagouv resources \
  "accidents corporels" \
  --format csv \
  --first \
  --json | jq .
```

### `--urls` : handoff minimal pour les outils Unix

```bash
datagouv resources \
  "accidents corporels" \
  --format csv \
  --first \
  --urls
```

La sortie contient uniquement les URL, une par ligne. Elle peut être directement composée avec d'autres outils :

```bash
datagouv resources \
  "accidents corporels" \
  --format csv \
  --first \
  --urls | xargs -n1 wget
```

Le même principe permet de transmettre les URL à `curl`, `aria2c`, un script Python ou tout autre programme acceptant des URL en entrée.

### `--manifest` : handoff structuré

```bash
datagouv resources \
  "accidents corporels" \
  --format csv \
  --first \
  --manifest | jq .
```

Le manifeste contient un résumé du dataset et, pour chaque ressource sélectionnée :

```json
{
  "dataset": {
    "id": "...",
    "title": "..."
  },
  "resources": [
    {
      "id": "...",
      "title": "...",
      "format": "csv",
      "filesize": 123456,
      "url": "https://..."
    }
  ]
}
```

Ce format est destiné au passage vers des outils externes. `--json`, `--urls` et `--manifest` sont volontairement mutuellement exclusifs.

## 8. `metadata` : des données sur les données

```bash
datagouv metadata \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Les métadonnées permettent d'évaluer la provenance, la licence, les tags, les dates et d'autres propriétés avant de charger le contenu des ressources.

## 9. `stats` : caractériser les ressources

```bash
datagouv stats \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

`stats` caractérise les ressources décrites dans le catalogue. Il ne s'agit pas d'une analyse statistique scientifique du contenu téléchargé.

## 10. `inspect` : observer le JSON brut

```bash
datagouv inspect \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" | jq
```

Cette commande est utile pour comprendre la structure exacte de l'API ou récupérer un champ qui n'est pas exposé par une vue synthétique.

## 11. Comprendre le handoff

Le cœur du workflow est la séparation entre la **phase amont** prise en charge par le toolkit et la **phase d'analyse** confiée à un outil spécialisé :

```text
data.gouv.fr
    ↓
recherche
    ↓
résolution du dataset
    ↓
évaluation des métadonnées
    ↓
filtrage des ressources
    ↓
URL / manifeste / téléchargement
    ↓
R, Python, DuckDB, Julia, Spark, etc.
```

Cette séparation évite de transformer `datagouv-toolkit` en framework généraliste d'analyse. Son rôle est de rendre l'accès à data.gouv.fr reproductible, inspectable et composable.

## 12. `organization` : examiner un producteur

```bash
datagouv organization <identifiant>
```

Une organisation publie des datasets ; ceux-ci référencent ensuite des ressources. Les identifiants permettent de relier ces objets sans dépendre uniquement de leur libellé humain.

## 13. `download` : acquérir les données

Après exploration et sélection :

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data
```

Le pipeline devient :

```text
catalogue distant
       ↓
résolution du dataset
       ↓
sélection des ressources
       ↓
téléchargement HTTP
       ↓
fichiers locaux
       ↓
outil d'analyse externe
```

Pour les scripts :

```bash
datagouv download \
  "accidents corporels" \
  --format csv \
  --resource-title "Caract_2024" \
  --first \
  --output data \
  --json | jq '.resources[] | {path, downloaded}'
```

## 14. `inspect-csv` : audit structurel local

Une fois un CSV présent localement :

```bash
datagouv inspect-csv fichier.csv
```

Cette commande réalise un **data profiling** léger : dimensions, types, valeurs manquantes, doublons, cardinalités, clés candidates et aperçu.

Pour une sortie structurée :

```bash
datagouv inspect-csv fichier.csv --json \
  | jq '.file, .candidate_keys, .duplicate_rows'
```

L'objectif est d'aider à décider comment travailler ensuite avec le fichier, pas de remplacer une analyse réalisée avec pandas, Polars, R, DuckDB ou un autre environnement.

## 15. `workflow` : téléchargement suivi d'un audit CSV

```bash
datagouv workflow \
  "accidents corporels" \
  --format csv \
  --resource-title "Caract_2024" \
  --first \
  --output data \
  --audit-dir audits
```

Cette commande combine résolution, sélection, téléchargement et audit CSV. Elle est utile lorsque l'on souhaite immédiatement obtenir une première description structurelle des fichiers téléchargés.

## 16. `catalog-stats` : explorer un snapshot local du catalogue

```bash
datagouv catalog-stats "transport" \
  --snapshot snapshot/2026-08-25
```

Avec filtres :

```bash
datagouv catalog-stats "énergie" \
  --snapshot snapshot/2026-08-25 \
  --license fr-lo-2.0 \
  --frequency annual \
  --format csv
```

La sortie structurée permet de composer l'exploration avec `jq` :

```bash
datagouv catalog-stats "transport" \
  --snapshot snapshot/2026-08-25 \
  --json | jq '.datasets, .resources, .rankings.formats'
```

Cette commande sert à caractériser le catalogue localement : nombre de datasets et ressources, tailles connues ou inconnues, formats, producteurs, licences et fréquences.

## 17. Un workflow complet avant analyse

Un usage typique peut être résumé ainsi :

```bash
datagouv search "accidents corporels"

datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "2024" \
  --first \
  --manifest | jq .

datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --first \
  --output data

datagouv inspect-csv data/Caract_2024.csv --json | jq .
```

Puis l'analyse proprement dite continue dans l'outil approprié, par exemple Python :

```python
import pandas as pd

df = pd.read_csv("data/Caract_2024.csv")
```

ou R :

```r
df <- read.csv("data/Caract_2024.csv")
```

ou DuckDB :

```sql
SELECT *
FROM read_csv_auto('data/Caract_2024.csv');
```

## 18. Principe de conception

`datagouv-toolkit` suit une logique de toolbox composable :

- les sorties humaines servent à l'exploration interactive ;
- les sorties JSON servent aux scripts ;
- `--urls` fournit un flux minimal pour les pipelines Unix ;
- `--manifest` fournit un contrat compact pour le handoff ;
- `--first` permet une résolution non interactive lorsque c'est souhaité ;
- les outils d'analyse spécialisés prennent le relais après acquisition.

Le projet se concentre donc sur la question : **quelles données de data.gouv.fr faut-il récupérer, comment les sélectionner proprement, et comment les transmettre à l'outil qui les exploitera ensuite ?**
