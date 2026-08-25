from pathlib import Path

import pandas as pd
from prepare_2024 import build_analytic_dataset

OUTPUT = Path("datasets/baac/2024/baac_2024_clean.csv")

def parse_decimal_comma(series: pd.Series) -> pd.Series:
    """Convertit une série texte avec virgule décimale en float."""
    return pd.to_numeric(
        series.astype("string").str.replace(",", ".", regex=False),
        errors="coerce",
    )


def clean_baac_2024(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie uniquement les types techniques du dataset analytique."""
    cleaned = df.copy()

    cleaned["lat"] = parse_decimal_comma(cleaned["lat"])
    cleaned["long"] = parse_decimal_comma(cleaned["long"])

    cleaned["an_nais"] = pd.to_numeric(
        cleaned["an_nais"],
        errors="coerce",
    ).astype("Int64")

    cleaned["occutc"] = pd.to_numeric(
        cleaned["occutc"],
        errors="coerce",
    ).astype("Int64")

    parsed_time = pd.to_datetime(
        cleaned["hrmn"],
        format="%H:%M",
        errors="coerce",
    )

    cleaned["heure"] = parsed_time.dt.hour.astype("Int64")
    cleaned["minute"] = parsed_time.dt.minute.astype("Int64")

    cleaned = cleaned.drop(columns="hrmn")

    return cleaned


def main() -> None:
    df = build_analytic_dataset()
    cleaned = clean_baac_2024(df)

    print()
    print("Nettoyage")
    print("---------")
    print("lignes   :", len(cleaned))
    print("colonnes :", len(cleaned.columns))


    for column in ("lat", "long", "an_nais", "occutc", "heure", "minute"):
        print(f"{column:10} : {cleaned[column].dtype}")

    cleaned.to_csv(
        OUTPUT,
        sep=";",
        index=False,
    )

    print()
    print("Écrit :", OUTPUT)


if __name__ == "__main__":
    main()
