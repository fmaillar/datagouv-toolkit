#!/usr/bin/env python3

import argparse
import csv
import re
from pathlib import Path

import pandas as pd

YEAR_RE = re.compile(r"(20(?:0[5-9]|1\d|2[0-4]))")

TABLE_PATTERNS = {
    "caracteristiques": ("caract", "caracteristique", "caracteristiques"),
    "lieux": ("lieu", "lieux"),
    "vehicules": ("vehicule", "vehicules"),
    "usagers": ("usager", "usagers"),
}


def detect_year(path: Path) -> int | None:
    """Extrait l'année BAAC 2005–2024 depuis le chemin."""
    match = YEAR_RE.search(str(path))

    if match is None:
        return None

    return int(match.group(1))


def detect_table(path: Path) -> str | None:
    """Détermine la table BAAC à partir du nom du fichier."""
    name = path.stem.lower()

    for table, patterns in TABLE_PATTERNS.items():
        if any(pattern in name for pattern in patterns):
            return table

    return None


def detect_encoding(path: Path) -> str:
    """Détermine un encodage lisible pour le CSV."""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open("r", encoding=encoding) as stream:
                stream.read(8192)
        except UnicodeDecodeError:
            continue

        return encoding

    raise UnicodeError(f"Encodage non reconnu : {path}")


def detect_separator(path: Path, encoding: str) -> str:
    """Détecte le séparateur CSV parmi les séparateurs usuels."""
    with path.open("r", encoding=encoding, newline="") as stream:
        sample = stream.read(8192)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        return ";"

    return dialect.delimiter


def inspect_csv(
    path: Path,
    year: int,
    table: str,
) -> list[dict[str, object]]:
    """Construit l'inventaire du schéma d'un fichier BAAC."""
    encoding = detect_encoding(path)
    separator = detect_separator(path, encoding)

    df = pd.read_csv(
        path,
        sep=separator,
        encoding=encoding,
        low_memory=False,
    )

    # Quelques millésimes contiennent des espaces parasites
    # dans les noms de colonnes.
    df.columns = df.columns.astype(str).str.strip()

    row_count = len(df)
    rows: list[dict[str, object]] = []

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        missing_rate = missing_count / row_count if row_count else 0.0

        rows.append(
            {
                "annee": year,
                "table": table,
                "colonne": column,
                "dtype": str(df[column].dtype),
                "nb_lignes": row_count,
                "nb_na": missing_count,
                "taux_na": missing_rate,
                "fichier": str(path),
                "encoding": encoding,
                "separateur": separator,
            }
        )

    return rows


def discover_files(root: Path) -> list[tuple[Path, int, str]]:
    """Découvre les fichiers CSV BAAC 2005–2024."""
    files: list[tuple[Path, int, str]] = []

    for path in sorted(root.rglob("*.csv")):
        year = detect_year(path)
        table = detect_table(path)

        if year is None or table is None:
            continue

        files.append((path, year, table))

    return files


def build_schema_history(root: Path) -> pd.DataFrame:
    """Construit l'historique des schémas BAAC."""
    files = discover_files(root)

    if not files:
        raise RuntimeError(f"Aucun fichier BAAC 2005–2024 trouvé dans {root}")

    rows: list[dict[str, object]] = []

    for path, year, table in files:
        print(f"{year}  {table:17}  {path}")

        rows.extend(
            inspect_csv(
                path=path,
                year=year,
                table=table,
            )
        )

    history = pd.DataFrame(rows)

    return history.sort_values(
        ["annee", "table", "colonne"],
        ignore_index=True,
    )


def print_summary(history: pd.DataFrame) -> None:
    """Affiche un résumé de l'inventaire."""
    files = history[["annee", "table", "fichier"]].drop_duplicates()

    print()
    print("Résumé")
    print("------")
    print("années   :", history["annee"].nunique())
    print("fichiers :", len(files))
    print("colonnes :", len(history))
    print()

    coverage = files.groupby("annee")["table"].nunique().rename("nb_tables")

    print("Tables détectées par année")
    print("---------------------------")
    print(coverage.to_string())


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Inventorie l'évolution du schéma des fichiers BAAC entre 2005 et 2024."
        )
    )

    parser.add_argument(
        "root",
        type=Path,
        help="Répertoire contenant les CSV BAAC",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets/baac/schema_history.csv"),
        help=("CSV de sortie (défaut: datasets/baac/schema_history.csv)"),
    )

    args = parser.parse_args()

    history = build_schema_history(args.root)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    history.to_csv(
        args.output,
        sep=";",
        index=False,
        float_format="%.6f",
    )

    print_summary(history)

    print()
    print("Écrit :", args.output)


if __name__ == "__main__":
    main()
