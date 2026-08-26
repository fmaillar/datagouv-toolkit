from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/baac/2024")

FILES = {
    "caracteristiques": DATA_DIR / "Caract_2024.csv",
    "lieux": DATA_DIR / "Lieux_2024.csv",
    "vehicules": DATA_DIR / "Vehicules_2024.csv",
    "usagers": DATA_DIR / "Usagers_2024.csv",
}


def load_csv(path: Path) -> pd.DataFrame:
    """Charge un fichier BAAC 2024."""
    return pd.read_csv(
        path,
        sep=";",
        low_memory=False,
    )


def inspect_dataframe(name: str, df: pd.DataFrame) -> None:
    print()
    print("=" * 80)
    print(name.upper())
    print("=" * 80)

    print(f"Lignes   : {len(df)}")
    print(f"Colonnes : {len(df.columns)}")

    print("\nTypes")
    print("-" * 80)
    print(df.dtypes.to_string())

    print("\nValeurs manquantes")
    print("-" * 80)

    missing = (
        df.isna()
        .sum()
        .to_frame("missing")
        .assign(percent=lambda x: 100 * x["missing"] / len(df))
        .sort_values("missing", ascending=False)
    )

    print(missing.to_string())

    print("\nDoublons de lignes")
    print("-" * 80)
    print(df.duplicated().sum())

    print("\nAperçu")
    print("-" * 80)
    print(df.head().to_string(index=False))


def main() -> None:
    for name, path in FILES.items():
        df = load_csv(path)
        inspect_dataframe(name, df)


if __name__ == "__main__":
    main()
