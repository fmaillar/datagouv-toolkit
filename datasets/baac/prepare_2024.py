from pathlib import Path

import pandas as pd

DATA_DIR = Path("datasets/baac/2024")


def load_tables():
    """Charge les quatre tables BAAC 2024."""
    caracteristiques = pd.read_csv(
        DATA_DIR / "Caract_2024.csv",
        sep=";",
        low_memory=False,
    )
    lieux = pd.read_csv(
        DATA_DIR / "Lieux_2024.csv",
        sep=";",
        low_memory=False,
    )
    vehicules = pd.read_csv(
        DATA_DIR / "Vehicules_2024.csv",
        sep=";",
        low_memory=False,
    )
    usagers = pd.read_csv(
        DATA_DIR / "Usagers_2024.csv",
        sep=";",
        low_memory=False,
    )

    return caracteristiques, lieux, vehicules, usagers


def aggregate_lieux(lieux):
    """
    Agrège Lieux au niveau accident.

    On reste volontairement conservateur :
    - nombre de lignes/voies associées ;
    - vitesse minimale et maximale observée ;
    - nombre de catégories de route distinctes ;
    - nombre de voies distinctes renseignées.
    """
    return (
        lieux.groupby("Num_Acc", as_index=False)
        .agg(
            lieux_count=("Num_Acc", "size"),
            catr_count=("catr", "nunique"),
            voie_count=("voie", "nunique"),
            vma_min=("vma", "min"),
            vma_max=("vma", "max"),
        )
    )


def build_analytic_dataset():
    """
    Construit une table analytique avec une ligne par usager.
    """
    caracteristiques, lieux, vehicules, usagers = load_tables()

    lieux_agg = aggregate_lieux(lieux)

    print("Lignes sources")
    print("--------------")
    print("caracteristiques :", len(caracteristiques))
    print("lieux             :", len(lieux))
    print("vehicules         :", len(vehicules))
    print("usagers           :", len(usagers))
    print()

    df = usagers.merge(
        vehicules,
        on=["Num_Acc", "id_vehicule", "num_veh"],
        how="left",
        validate="many_to_one",
        suffixes=("_usager", "_vehicule"),
    )

    assert len(df) == len(usagers)

    missing_vehicle = df["catv"].isna().sum()
    print("Après merge véhicules")
    print("----------------------")
    print("lignes                  :", len(df))
    print("usagers sans véhicule   :", missing_vehicle)
    print()

    df = df.merge(
        caracteristiques,
        on="Num_Acc",
        how="left",
        validate="many_to_one",
    )

    assert len(df) == len(usagers)

    missing_accident = df["jour"].isna().sum()
    print("Après merge caractéristiques")
    print("-----------------------------")
    print("lignes                  :", len(df))
    print("usagers sans accident   :", missing_accident)
    print()

    df = df.merge(
        lieux_agg,
        on="Num_Acc",
        how="left",
        validate="many_to_one",
    )

    assert len(df) == len(usagers)

    missing_lieux = df["lieux_count"].isna().sum()
    print("Après merge lieux agrégés")
    print("-------------------------")
    print("lignes                  :", len(df))
    print("usagers sans lieux      :", missing_lieux)
    print()

    print("Dataset analytique")
    print("-------------------")
    print("lignes   :", len(df))
    print("colonnes :", len(df.columns))

    return df


def main():
    df = build_analytic_dataset()

    print()
    print("Aperçu")
    print("------")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
