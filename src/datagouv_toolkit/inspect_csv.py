from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

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


def missing_values(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Retourne les valeurs manquantes par colonne."""
    missing = pd.DataFrame(
        {
            "column": [str(column) for column in df.columns],
            "missing": df.isna().sum().astype(int).to_list(),
            "percent": (df.isna().mean() * 100).astype(float).to_list(),
        }
    ).sort_values(
        ["missing", "percent"],
        ascending=False,
    )

    return missing.to_dict(orient="records")


def cardinalities(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Retourne le nombre de valeurs distinctes par colonne."""
    rows = []

    for column in df.columns:
        unique = int(df[column].nunique(dropna=False))
        rows.append(
            {
                "column": str(column),
                "unique": unique,
                "ratio": unique / len(df) if len(df) else 0.0,
            }
        )

    return sorted(
        rows,
        key=lambda row: (-row["unique"], row["column"]),
    )


def print_missing_values(df: pd.DataFrame) -> None:
    """Affiche les valeurs manquantes par colonne."""
    result = pd.DataFrame(missing_values(df)).set_index("column")
    print(result.to_string())


def print_cardinalities(df: pd.DataFrame) -> None:
    """Affiche le nombre de valeurs distinctes par colonne."""
    result = pd.DataFrame(cardinalities(df))
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
            candidates.append(str(column))

    return candidates


def low_cardinality_values(
    df: pd.DataFrame,
    *,
    threshold: int,
) -> list[dict[str, Any]]:
    """Retourne les distributions des colonnes à faible cardinalité."""
    results = []

    for column in df.columns:
        count = int(df[column].nunique(dropna=False))

        if count > threshold:
            continue

        values = df[column].value_counts(dropna=False).rename_axis("value").reset_index(
            name="count"
        )
        records = json.loads(values.to_json(orient="records", force_ascii=False))
        results.append(
            {
                "column": str(column),
                "unique": count,
                "values": records,
            }
        )

    return results


def print_low_cardinality(
    df: pd.DataFrame,
    *,
    threshold: int,
) -> None:
    """Affiche les distributions des colonnes à faible cardinalité."""
    for item in low_cardinality_values(df, threshold=threshold):
        print()
        print(f"{item['column']} ({item['unique']} valeurs)")
        print("-" * 80)
        values = pd.DataFrame(item["values"]).set_index("value")["count"]
        print(values.to_string())


def analyze_csv(
    path: Path,
    *,
    encoding: str | None = None,
    separator: str | None = None,
    nrows: int | None = None,
    low_cardinality: int = DEFAULT_LOW_CARDINALITY,
) -> dict[str, Any]:
    """Analyse un CSV et retourne un résultat structuré sans l'afficher."""
    selected_encoding = encoding or detect_encoding(path)
    selected_separator = separator or detect_separator(path, selected_encoding)

    df = load_csv(
        path,
        encoding=selected_encoding,
        separator=selected_separator,
        nrows=nrows,
    )

    preview = json.loads(df.head().to_json(orient="records", force_ascii=False))

    return {
        "file": {
            "path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "encoding": selected_encoding,
            "separator": selected_separator,
            "rows": len(df),
            "columns": len(df.columns),
            "limit": nrows,
        },
        "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
        "missing_values": missing_values(df),
        "duplicate_rows": int(df.duplicated().sum()),
        "cardinalities": cardinalities(df),
        "candidate_keys": find_candidate_keys(df),
        "low_cardinality": low_cardinality_values(df, threshold=low_cardinality),
        "preview": preview,
    }


def format_csv_audit(audit: dict[str, Any]) -> str:
    """Formate un résultat d'audit structuré en rapport texte."""
    file_info = audit["file"]
    lines = [
        "=" * 80,
        "FICHIER",
        "=" * 80,
        f"Chemin       : {file_info['path']}",
        f"Taille       : {file_info['size_bytes']:,} octets",
        f"Encodage     : {file_info['encoding']}",
        f"Séparateur   : {file_info['separator']!r}",
        f"Lignes       : {file_info['rows']}",
        f"Colonnes     : {file_info['columns']}",
    ]

    if file_info["limit"] is not None:
        lines.append(f"Limite       : {file_info['limit']} lignes")

    lines.extend(
        [
            "",
            "=" * 80,
            "COLONNES ET TYPES",
            "=" * 80,
            pd.Series(audit["dtypes"]).to_string(),
            "",
            "=" * 80,
            "VALEURS MANQUANTES",
            "=" * 80,
            pd.DataFrame(audit["missing_values"])
            .set_index("column")
            .to_string(),
            "",
            "=" * 80,
            "DOUBLONS",
            "=" * 80,
            f"Lignes dupliquées : {audit['duplicate_rows']}",
            "",
            "=" * 80,
            "CARDINALITÉS",
            "=" * 80,
            pd.DataFrame(audit["cardinalities"]).to_string(index=False),
            "",
            "=" * 80,
            "CLÉS SIMPLES CANDIDATES",
            "=" * 80,
        ]
    )

    if audit["candidate_keys"]:
        lines.extend(audit["candidate_keys"])
    else:
        lines.append("Aucune")

    lines.extend(
        [
            "",
            "=" * 80,
            f"COLONNES À FAIBLE CARDINALITÉ (<= {max((item['unique'] for item in audit['low_cardinality']), default=0)} valeurs)",
            "=" * 80,
        ]
    )

    for item in audit["low_cardinality"]:
        lines.extend(
            [
                "",
                f"{item['column']} ({item['unique']} valeurs)",
                "-" * 80,
                pd.DataFrame(item["values"])
                .set_index("value")["count"]
                .to_string(),
            ]
        )

    lines.extend(
        [
            "",
            "=" * 80,
            "APERÇU",
            "=" * 80,
            pd.DataFrame(audit["preview"]).to_string(index=False),
        ]
    )

    return "\n".join(lines)


def inspect_csv(
    path: Path,
    *,
    encoding: str | None = None,
    separator: str | None = None,
    nrows: int | None = None,
    low_cardinality: int = DEFAULT_LOW_CARDINALITY,
) -> dict[str, Any]:
    """Produit un audit générique d'un fichier CSV."""
    audit = analyze_csv(
        path,
        encoding=encoding,
        separator=separator,
        nrows=nrows,
        low_cardinality=low_cardinality,
    )
    print(format_csv_audit(audit))
    return audit


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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Afficher le résultat au format JSON.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.file.is_file():
        raise SystemExit(f"Fichier introuvable : {args.file}")

    if args.json:
        audit = analyze_csv(
            args.file,
            encoding=args.encoding,
            separator=args.sep,
            nrows=args.nrows,
            low_cardinality=args.low_cardinality,
        )
        print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        inspect_csv(
            args.file,
            encoding=args.encoding,
            separator=args.sep,
            nrows=args.nrows,
            low_cardinality=args.low_cardinality,
        )


if __name__ == "__main__":
    main()
