from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/baac/2024")

FILES = {
    "caracteristiques": DATA_DIR / "Caract_2024.csv",
    "lieux": DATA_DIR / "Lieux_2024.csv",
    "vehicules": DATA_DIR / "Vehicules_2024.csv",
    "usagers": DATA_DIR / "Usagers_2024.csv",
}


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", low_memory=False)


def inspect_num_acc(name: str, df: pd.DataFrame) -> None:
    print()
    print("=" * 80)
    print(name.upper())
    print("=" * 80)

    print(f"Lignes                  : {len(df)}")
    print(f"Num_Acc uniques         : {df['Num_Acc'].nunique()}")
    print(f"Num_Acc dupliqués       : {df['Num_Acc'].duplicated().sum()}")
    print(f"Num_Acc manquants       : {df['Num_Acc'].isna().sum()}")

    counts = df["Num_Acc"].value_counts()

    print(f"Max lignes / Num_Acc    : {counts.max()}")
    print(f"Accidents avec >1 ligne : {(counts > 1).sum()}")


def main() -> None:
    frames = {name: load(path) for name, path in FILES.items()}

    for name, df in frames.items():
        inspect_num_acc(name, df)

        if "id_vehicule" in df.columns:
            print(f"id_vehicule uniques      : {df['id_vehicule'].nunique()}")
            print(
                "Clé (Num_Acc,id_vehicule) dupliquée : "
                f"{df.duplicated(['Num_Acc', 'id_vehicule']).sum()}"
            )

    print()
    print("=" * 80)
    print("COUVERTURE DES ACCIDENTS")
    print("=" * 80)

    reference = set(frames["caracteristiques"]["Num_Acc"])

    for name, df in frames.items():
        ids = set(df["Num_Acc"])
        print(
            f"{name:18} "
            f"absents={len(reference - ids):5}  "
            f"supplémentaires={len(ids - reference):5}"
        )


if __name__ == "__main__":
    main()
