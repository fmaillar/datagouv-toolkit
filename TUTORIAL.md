# Tutoriel approfondi de `datagouv`

Ce tutoriel présente `datagouv` progressivement, depuis la découverte du catalogue jusqu'au téléchargement, à l'audit et à l'analyse. L'objectif n'est pas seulement d'apprendre des commandes : il s'agit aussi de comprendre les notions qu'elles représentent — API HTTP, datasets, ressources, métadonnées, JSON, filtrage, reproductibilité et pipeline de données.

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

Une **organisation** représente un producteur de données.

Un **dataset** est un jeu de données au sens documentaire et logique. Il possède un titre, une description, un producteur, des métadonnées et éventuellement plusieurs ressources.

Une **ressource** est un fichier ou un accès concret aux données. Un dataset sur les accidents routiers peut, par exemple, contenir plusieurs fichiers CSV correspondant à différentes tables ou années.

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

- `datagouv` est le programme ;
- `search` est une sous-commande ;
- `"qualité de l'air"` est un argument positionnel.

Une option commence généralement par `-` ou `--` :

```bash
datagouv search "qualité de l'air" --limit 5
```

Ici, `--limit 5` modifie le nombre de résultats affichés.

Cette architecture est analogue à celle de commandes comme `git status`, `git commit` ou `apt install` : un même programme expose plusieurs opérations cohérentes.

### Aide générale et aide locale

L'aide générale donne la liste des sous-commandes :

```bash
datagouv --help
```

Chaque sous-commande possède ensuite sa propre aide :

```bash
datagouv search --help
datagouv dataset --help
datagouv resources --help
datagouv download --help
```

Il est généralement préférable de consulter `--help` plutôt que de mémoriser toutes les options.

## 3. Rechercher un dataset

Commençons par une recherche simple :

```bash
datagouv search "qualité de l'air"
```

`datagouv` interroge l'API publique de data.gouv.fr. Conceptuellement, le dialogue ressemble à ceci :

```text
datagouv
   │
   │ requête HTTP GET
   ▼
API data.gouv.fr
   │
   │ réponse JSON
   ▼
datagouv
   │
   ▼
affichage terminal
```

### API

Une **API** (Application Programming Interface) est ici une interface destinée aux programmes. Au lieu d'ouvrir une page Web et de cliquer dans un navigateur, `datagouv` envoie des requêtes HTTP au serveur et exploite les réponses structurées.

### HTTP GET

`GET` est la méthode HTTP utilisée pour demander une représentation d'une ressource sans la modifier. Le toolkit est conçu ici pour effectuer des opérations de lecture sur l'API catalogue.

### Pagination

On peut limiter l'affichage :

```bash
datagouv search "qualité de l'air" --limit 5
```

Si la CLI indique par exemple qu'un grand nombre de résultats ont été trouvés mais que cinq seulement sont affichés, il faut distinguer :

- le nombre total de résultats correspondant à la requête ;
- le nombre de résultats récupérés ou présentés sur cette page.

Ce mécanisme est appelé **pagination**. Une API évite ainsi de transférer des milliers d'objets lorsqu'une petite partie suffit.

## 4. Recherche textuelle et identifiant stable

Une commande comme :

```bash
datagouv dataset "qualité de l'air"
```

peut correspondre à plusieurs datasets. Une chaîne de caractères destinée aux humains n'identifie pas nécessairement un objet de manière unique.

On distingue donc :

```text
titre lisible
    │
    └── utile aux humains

identifiant
    │
    └── utile pour identifier précisément un objet
```

Lorsque plusieurs datasets correspondent à une recherche, `datagouv` propose une sélection interactive.

Pour un script reproductible, un identifiant stable est généralement préférable à une recherche textuelle : le classement ou le titre des résultats peut évoluer alors que l'identité de l'objet reste la même.

## 5. Réduire l'ambiguïté avec des filtres

Le toolkit permet de préciser notamment le producteur ou le titre :

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Le raisonnement devient :

```text
recherche textuelle
        │
        ▼
datasets candidats
        │
        ├── filtre producteur
        └── filtre titre éventuel
        │
        ▼
dataset retenu
```

C'est une opération de **filtrage** : on part d'un ensemble de candidats et on ne conserve que ceux qui satisfont certains critères.

La même notion se retrouve dans pandas :

```python
df[df["producer"] == "..."]
```

ou en SQL :

```sql
SELECT *
FROM datasets
WHERE producer = '...';
```

La syntaxe change, mais l'opération conceptuelle reste la même.

## 6. `dataset` : obtenir une vue synthétique

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

L'API peut renvoyer un objet riche contenant de nombreux champs. La commande `dataset` en présente une vue adaptée à une lecture humaine.

C'est une forme de **projection** : on sélectionne une partie utile d'une structure plus vaste au lieu d'exposer systématiquement tous les champs techniques.

Cette séparation est importante dans la conception d'une CLI : le format optimal pour une machine n'est pas nécessairement le format optimal pour un humain.

## 7. `resources` : passer du catalogue aux fichiers

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Un dataset peut référencer plusieurs ressources :

```text
dataset
│
├── resource 1
│     ├── titre
│     ├── format
│     ├── URL
│     └── taille éventuelle
│
├── resource 2
│
└── resource 3
```

Le **catalogue** décrit donc les données, tandis que les **ressources** donnent accès à leur contenu concret.

On peut comparer cela à une bibliothèque : la notice bibliographique décrit un livre, mais elle n'est pas le livre lui-même.

## 8. `metadata` : des données sur les données

```bash
datagouv metadata \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Les **métadonnées** sont des informations décrivant les données : titre, description, producteur, licence, tags, dates, métriques ou autres propriétés publiées dans le catalogue.

Il faut distinguer :

```text
donnée
    un enregistrement décrivant un phénomène observé

métadonnée
    une information décrivant le dataset ou la ressource
```

Cette distinction est centrale en science des données, en archivistique et en science ouverte. Les métadonnées permettent notamment d'évaluer la provenance, l'interprétation et les conditions de réutilisation d'un dataset avant même d'en charger le contenu.

## 9. `stats` : caractériser les ressources

```bash
datagouv stats \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Cette commande produit des statistiques sur les **ressources du dataset**.

Il faut distinguer deux niveaux d'analyse :

```text
statistiques sur les ressources
        │
        └── structure du catalogue

statistiques sur les colonnes d'un CSV
        │
        └── contenu des données
```

`stats` appartient au premier niveau. Elle permet de caractériser un dataset avant ou indépendamment d'une analyse statistique de son contenu.

## 10. `inspect` : observer le JSON brut

Pour obtenir la représentation JSON complète du dataset :

```bash
datagouv inspect \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Cette commande est particulièrement utile pour :

- comprendre la structure de l'API ;
- découvrir un champ qui n'est pas présenté par les vues synthétiques ;
- développer une nouvelle fonctionnalité ;
- déboguer ;
- chaîner `datagouv` avec un autre programme.

Par exemple :

```bash
datagouv inspect \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" | jq
```

Le pipe Unix `|` connecte la sortie standard de `datagouv` à l'entrée standard de `jq` :

```text
datagouv
   │
   │ JSON
   ▼
   |
   ▼
  jq
   │
   ▼
terminal
```

C'est une propriété importante des outils en ligne de commande : plusieurs programmes spécialisés peuvent être composés plutôt que de concentrer toutes les fonctions dans une seule application.

## 11. Comprendre JSON

JSON représente quelques structures fondamentales.

Un objet :

```json
{
  "title": "Exemple",
  "count": 12
}
```

Une liste :

```json
[
  "csv",
  "json",
  "parquet"
]
```

Des valeurs :

```json
"texte"
42
3.14
true
false
null
```

Ces structures correspondent naturellement aux objets Python courants :

```text
JSON        Python
-----------------
objet       dict
liste       list
chaîne      str
entier      int
nombre      float
booléen     bool
null        None
```

Le module métier `datagouv.py` utilise `requests` pour communiquer avec l'API et manipuler les réponses JSON sous forme d'objets Python.

## 12. `organization` : examiner un producteur

```bash
datagouv organization <identifiant>
```

Une organisation est liée aux datasets qu'elle publie. On peut représenter le modèle conceptuel ainsi :

```text
organisation
     │
     │ publie
     ▼
  dataset
     │
     │ contient/référence
     ▼
 ressource
```

Les identifiants permettent de relier ces objets sans dépendre de leur libellé humain.

## 13. `download` : acquérir les données

Après l'exploration du catalogue, on peut télécharger une ressource :

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data
```

Le pipeline conceptuel devient :

```text
catalogue distant
       │
       ▼
résolution du dataset
       │
       ▼
sélection des ressources
       │
       ▼
téléchargement HTTP
       │
       ▼
fichiers locaux
```

Les filtres `--format` et `--resource-title` permettent de sélectionner les ressources pertinentes. `--output` définit le répertoire local de destination.

À ce stade, on passe de la **découverte de données** à leur **acquisition**.

### Une sortie JSON pour les scripts

La sortie humaine est adaptée au terminal. Pour chaîner le téléchargement avec un script ou un autre outil Unix, `download` accepte `--json` :

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data \
  --json
```

La réponse contient notamment le dataset résolu, le répertoire de destination et une liste `resources`. Pour chaque ressource, le résultat expose son chemin local avec `path` et indique avec `downloaded` si le fichier vient réellement d'être téléchargé.

```json
{
  "dataset": {
    "id": "...",
    "title": "..."
  },
  "destination": ".../data",
  "resources": [
    {
      "downloaded": true,
      "path": "data/Caract_2024.csv",
      "resource": {
        "id": "...",
        "title": "Caract_2024.csv"
      }
    }
  ]
}
```

Si un fichier existe déjà et que `--overwrite` n'est pas utilisé, il n'est pas retéléchargé et `downloaded` vaut `false`. Cette distinction est utile pour un pipeline automatisé : le programme appelant peut savoir ce qui a réellement changé sans analyser une phrase destinée à un humain.

La sortie peut être filtrée avec `jq` :

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data \
  --json | jq '.resources[] | {path, downloaded}'
```

On applique ici un principe Unix classique : **stdout transporte la donnée structurée**, ce qui permet de la composer avec d'autres programmes.

## 14. `inspect-csv` : faire du data profiling

Une fois un CSV présent localement :

```bash
datagouv inspect-csv fichier.csv
```

Pour un audit volumineux :

```bash
datagouv inspect-csv fichier.csv > audit.txt
```

Cette étape correspond au **data profiling**, c'est-à-dire à l'examen systématique de la structure et de la qualité apparente d'un fichier avant analyse.

On cherche typiquement à comprendre :

- le nombre de lignes et de colonnes ;
- les noms et types de colonnes ;
- les valeurs manquantes ;
- les distributions ou cardinalités utiles ;
- l'encodage et le séparateur lorsque leur détection est nécessaire.

Un cycle de travail robuste ressemble davantage à :

```text
acquisition
    ↓
inspection
    ↓
nettoyage / normalisation
    ↓
analyse
```

qu'à une analyse immédiate d'un fichier dont on ne connaît pas encore la structure.

## 15. Pourquoi les CSV demandent une inspection

Le terme CSV masque plusieurs variantes.

Un fichier peut utiliser une virgule :

```text
nom,age
Alice,32
Bob,41
```

ou un point-virgule :

```text
nom;age
Alice;32
Bob;41
```

L'encodage peut également varier. UTF-8 est aujourd'hui très courant, mais des fichiers historiques peuvent utiliser d'autres encodages.

Une mauvaise interprétation de l'encodage transforme par exemple des caractères accentués en texte illisible. Une mauvaise interprétation du séparateur peut conduire à lire une ligne entière comme une seule colonne.

L'audit préalable permet donc de détecter des hypothèses de lecture incorrectes avant qu'elles ne contaminent l'analyse.

## 16. `workflow` : automatiser le pipeline

Le projet fournit une commande qui enchaîne téléchargement et audit :

```bash
datagouv workflow \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data \
  --audit-dir audits
```

Le workflow réalise conceptuellement :

```text
résoudre le dataset
        ↓
sélectionner les ressources
        ↓
télécharger
        ↓
identifier les CSV concernés
        ↓
auditer
        ↓
produire les résultats d'audit
```

Le workflow s'appuie sur les mêmes résultats structurés de téléchargement que `download`. Il réutilise donc le chemin local et le statut de téléchargement de chaque ressource au lieu de reconstruire ces informations séparément.

Un **workflow** ou **pipeline** transforme une suite d'opérations manuelles en procédure explicite et répétable.

C'est un premier pas vers les pratiques d'ingénierie des données : acquisition, validation, transformation et analyse sont séparées en étapes dont le comportement peut être contrôlé.

## 17. Reproductibilité

Une manipulation manuelle dans un navigateur peut être facile à réaliser une fois mais difficile à reproduire exactement plusieurs mois plus tard.

Une commande documentée :

```bash
datagouv workflow ...
```

peut au contraire être :

- conservée dans un script ;
- versionnée avec Git ;
- relue ;
- rejouée ;
- testée ;
- documentée avec les résultats qu'elle produit.

La **reproductibilité** ne signifie pas seulement obtenir à nouveau un résultat. Elle implique aussi de conserver suffisamment d'informations sur la procédure pour comprendre comment ce résultat a été produit.

## 18. `catalog-stats` : le catalogue devient lui-même une donnée

Le toolkit peut également analyser un snapshot local du catalogue :

```bash
datagouv catalog-stats "transport" \
  --snapshot snapshot/2026-08-25
```

Avec des filtres :

```bash
datagouv catalog-stats "énergie" \
  --snapshot snapshot/2026-08-25 \
  --license fr-lo-2.0 \
  --frequency annual
```

On change alors de niveau :

```text
données publiées
      ↑
datasets qui les organisent
      ↑
catalogue qui décrit les datasets
      ↑
analyse statistique du catalogue
```

Le catalogue est lui-même traité comme une source de données. On peut ainsi étudier les formats, licences, fréquences ou autres métadonnées disponibles dans le snapshot.

L'utilisation d'un **snapshot** est importante pour la reproductibilité : un catalogue en ligne évolue continuellement, tandis qu'une copie datée fournit un état de référence stable pour une analyse.

## 19. Architecture du toolkit

Le dépôt sépare les responsabilités :

```text
cli.py
    interface en ligne de commande unifiée
        │
        ├── datagouv.py
        │     exploration et résolution des datasets
        │
        ├── download_resources.py
        │     téléchargement des ressources
        │
        ├── dataset_workflow.py
        │     orchestration téléchargement + audit
        │
        ├── inspect_csv.py
        │     audit structurel des CSV
        │
        ├── catalog_stats.py
        │     analyse des snapshots du catalogue
        │
        └── normalize.py
              normalisation des métadonnées
```

Cette séparation suit un principe classique de conception logicielle : **séparer l'interface de la logique métier**.

`cli.py` interprète ce que l'utilisateur demande. Les autres modules réalisent les opérations correspondantes. Cette organisation facilite les tests et évite que la logique métier dépende inutilement de la manière dont elle est déclenchée depuis le terminal.

## 20. Parcours pratique recommandé

Pour apprendre le toolkit, on peut prendre le BAAC comme fil rouge et suivre les commandes dans cet ordre.

### Étape 1 — Découvrir

```bash
datagouv search "accidents corporels"
```

Notions : recherche, API, HTTP, pagination.

### Étape 2 — Identifier

```bash
datagouv dataset \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Notions : dataset, identifiant, résolution, filtrage.

### Étape 3 — Comprendre la provenance

```bash
datagouv metadata \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Notions : métadonnées, producteur, provenance.

### Étape 4 — Examiner les fichiers disponibles

```bash
datagouv resources \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Notions : ressource, format, URL, catalogue.

### Étape 5 — Caractériser les ressources

```bash
datagouv stats \
  "accidents corporels" \
  --producer "Ministère de l'intérieur"
```

Notions : statistiques descriptives du catalogue.

### Étape 6 — Descendre au niveau de l'API

```bash
datagouv inspect \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" | jq
```

Notions : JSON, structure d'API, composition Unix.

### Étape 7 — Télécharger

```bash
datagouv download \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data
```

Notions : acquisition, sélection de ressources, fichiers locaux.

Pour automatiser cette étape, la même commande avec `--json` fournit un résultat structuré directement consommable par `jq`, Python ou un autre programme.

### Étape 8 — Auditer

```bash
datagouv inspect-csv data/<fichier.csv>
```

Notions : data profiling, schéma, qualité, valeurs manquantes.

### Étape 9 — Automatiser

```bash
datagouv workflow \
  "accidents corporels" \
  --producer "Ministère de l'intérieur" \
  --format csv \
  --resource-title "Caract_2024" \
  --output data \
  --audit-dir audits
```

Notions : pipeline, automatisation, reproductibilité.

## 21. Du terminal au code Python

Une fois ces notions comprises, il devient plus facile de lire le code du toolkit.

Le trajet conceptuel complet est :

```text
commande shell
      ↓
argparse / cli.py
      ↓
fonction métier
      ↓
requests
      ↓
HTTP
      ↓
API data.gouv.fr
      ↓
JSON
      ↓
dict/list Python
      ↓
filtrage et présentation
      ↓
terminal ou fichier local
```

Pour les données tabulaires, le trajet se poursuit :

```text
ressource distante
      ↓
téléchargement
      ↓
CSV local
      ↓
inspection
      ↓
normalisation éventuelle
      ↓
pandas / NumPy / outils statistiques
      ↓
analyse reproductible
```

Ainsi, les commandes du toolkit ne sont pas des fonctions isolées : elles représentent différentes étapes d'une même chaîne de traitement de données.

## 22. Aller plus loin

Après ce parcours, plusieurs approfondissements deviennent naturels :

1. lire `cli.py` pour comprendre la construction des sous-commandes avec `argparse` ;
2. lire `datagouv.py` pour suivre une requête HTTP et la résolution d'un dataset ;
3. examiner `download_resources.py` pour comprendre le téléchargement robuste de fichiers et ses résultats structurés ;
4. examiner `inspect_csv.py` pour comprendre le profilage tabulaire ;
5. étudier `dataset_workflow.py` pour voir comment plusieurs briques indépendantes sont composées ;
6. utiliser `catalog_stats.py` pour passer de l'exploration d'un dataset à l'analyse reproductible d'un catalogue complet ;
7. consulter `datasets/baac/` comme exemple de pipeline spécialisé construit au-dessus des outils génériques.

Le principe directeur est de conserver des couches distinctes : **découvrir → identifier → comprendre → acquérir → auditer → analyser → reproduire**.