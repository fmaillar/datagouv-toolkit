from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

DEFAULT_LOW_CARDINALITY = 30


def detect_encoding(path: Path) -> str:
    """Détecte une variante d'encodage courante sans dépendance externe."""
    raw = path.read_bytes()[:100_000]

    for encoding in ("utf-8-sig", "utf-8"):
        try:
            raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return encoding

    return "latin-1"


def detect_separator(path: Path, encoding: str) -> str:
    """Détecte le séparateur CSV à partir d'un échantillon."""
    with path.open("r", encoding=encoding, newline="") as file:
        sample = file.read(64_000)

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|",
        )
    except csv.Error:
        return ","

    return dialect.delimiter


def load_csv(
    path: Path,
    *,
    encoding: str,
    separator: str,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Charge le CSV avec pandas."""
    return pd.read_csv(
        path,
        sep=separator,
        encoding=encoding,
        low_memory=False,
        nrows=nrows,
    )


def print_missing_values(df: pd.DataFrame) -> None:
    """Affiche les valeurs manquantes par colonne."""
    missing = pd.DataFrame(
        {
            "missing": df.isna().sum(),
            "percent": df.isna().mean() * 100,
        }
    ).sort_values(
        ["missing", "percent"],
        ascending=False,
    )

    print(missing.to_string())


def print_cardinalities(df: pd.DataFrame) -> None:
    """Affiche le nombre de valeurs distinctes par colonne."""
    rows = []

    for column in df.columns:
        rows.append(
            {
                "column": column,
                "unique": df[column].nunique(dropna=False),
                "ratio": df[column].nunique(dropna=False) / len(df) if len(df) else 0,
            }
        )

    result = pd.DataFrame(rows).sort_values(
        ["unique", "column"],
        ascending=[False, True],
    )

    print(result.to_string(index=False))


def find_candidate_keys(df: pd.DataFrame) -> list[str]:
    """
    Recherche les colonnes pouvant servir de clé simple.

    Une colonne est considérée candidate si :
    - aucune valeur n'est manquante ;
    - toutes les valeurs sont uniques.
    """
    candidates = []

    for column in df.columns:
        series = df[column]

        if series.isna().any():
            continue

        if series.is_unique:
            candidates.append(column)

    return candidates


def print_low_cardinality(
    df: pd.DataFrame,
    *,
    threshold: int,
) -> None:
    """Affiche les distributions des colonnes à faible cardinalité."""
    for column in df.columns:
        count = df[column].nunique(dropna=False)

        if count > threshold:
            continue

        print()
        print(f"{column} ({count} valeurs)")
        print("-" * 80)

        values = df[column].value_counts(
            dropna=False,
        )

        print(values.to_string())


def inspect_csv(
    path: Path,
    *,
    encoding: str | None = None,
    separator: str | None = None,
    nrows: int | None = None,
    low_cardinality: int = DEFAULT_LOW_CARDINALITY,
) -> None:
    """Produit un audit générique d'un fichier CSV."""
    selected_encoding = encoding or detect_encoding(path)
    selected_separator = separator or detect_separator(
        path,
        selected_encoding,
    )

    df = load_csv(
        path,
        encoding=selected_encoding,
        separator=selected_separator,
        nrows=nrows,
    )

    print("=" * 80)
    print("FICHIER")
    print("=" * 80)
    print(f"Chemin       : {path.resolve()}")
    print(f"Taille       : {path.stat().st_size:,} octets")
    print(f"Encodage     : {selected_encoding}")
    print(f"Séparateur   : {selected_separator!r}")
    print(f"Lignes       : {len(df)}")
    print(f"Colonnes     : {len(df.columns)}")

    if nrows is not None:
        print(f"Limite       : {nrows} lignes")

    print()
    print("=" * 80)
    print("COLONNES ET TYPES")
    print("=" * 80)
    print(df.dtypes.to_string())

    print()
    print("=" * 80)
    print("VALEURS MANQUANTES")
    print("=" * 80)
    print_missing_values(df)

    print()
    print("=" * 80)
    print("DOUBLONS")
    print("=" * 80)
    print(f"Lignes dupliquées : {df.duplicated().sum()}")

    print()
    print("=" * 80)
    print("CARDINALITÉS")
    print("=" * 80)
    print_cardinalities(df)

    print()
    print("=" * 80)
    print("CLÉS SIMPLES CANDIDATES")
    print("=" * 80)

    candidates = find_candidate_keys(df)

    if candidates:
        for column in candidates:
            print(column)
    else:
        print("Aucune")

    print()
    print("=" * 80)
    print(f"COLONNES À FAIBLE CARDINALITÉ (<= {low_cardinality} valeurs)")
    print("=" * 80)

    print_low_cardinality(
        df,
        threshold=low_cardinality,
    )

    print()
    print("=" * 80)
    print("APERÇU")
    print("=" * 80)
    print(df.head().to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit générique d'un fichier CSV.",
    )

    parser.add_argument(
        "file",
        type=Path,
        help="Fichier CSV à analyser.",
    )
    parser.add_argument(
        "--encoding",
        help="Encodage à forcer.",
    )
    parser.add_argument(
        "--sep",
        help="Séparateur à forcer.",
    )
    parser.add_argument(
        "--nrows",
        type=int,
        help="Limiter le chargement aux N premières lignes.",
    )
    parser.add_argument(
        "--low-cardinality",
        type=int,
        default=DEFAULT_LOW_CARDINALITY,
        help=(
            "Nombre maximal de valeurs distinctes pour afficher "
            "la distribution d'une colonne."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.file.is_file():
        raise SystemExit(f"Fichier introuvable : {args.file}")

    inspect_csv(
        args.file,
        encoding=args.encoding,
        separator=args.sep,
        nrows=args.nrows,
        low_cardinality=args.low_cardinality,
    )


if __name__ == "__main__":
    main()
