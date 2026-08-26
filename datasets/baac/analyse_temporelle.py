import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("datasets/baac")
TABLES_DIR = Path("reports/baac-2005-2024/tables")
FIGURES_DIR = Path("reports/baac-2005-2024/figures")

DAY_LABELS = {
    0: "Lundi",
    1: "Mardi",
    2: "Mercredi",
    3: "Jeudi",
    4: "Vendredi",
    5: "Samedi",
    6: "Dimanche",
}


def detect_encoding(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open("r", encoding=encoding) as stream:
                stream.read(8192)
        except UnicodeDecodeError:
            continue

        return encoding

    raise UnicodeError(f"Encodage non reconnu : {path}")


def detect_separator(path: Path, encoding: str) -> str:
    with path.open("r", encoding=encoding, newline="") as stream:
        sample = stream.read(8192)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        return ";"

    return dialect.delimiter


def parse_hour(series: pd.Series) -> pd.Series:
    text = (
        series.astype("string")
        .str.strip()
        .str.replace(":", "", regex=False)
        .str.zfill(4)
    )

    hour = pd.to_numeric(
        text.str[:2],
        errors="coerce",
    )

    return hour.where(hour.between(0, 23))


def load_temporal_data() -> pd.DataFrame:
    frames = []

    for year in range(2005, 2025):
        path = DATA_DIR / str(year) / f"Caract_{year}.csv"

        encoding = detect_encoding(path)
        separator = detect_separator(path, encoding)

        df = pd.read_csv(
            path,
            sep=separator,
            encoding=encoding,
            low_memory=False,
        )

        df.columns = df.columns.astype(str).str.strip()

        dates = pd.to_datetime(
            {
                "year": pd.Series(year, index=df.index),
                "month": pd.to_numeric(df["mois"], errors="coerce"),
                "day": pd.to_numeric(df["jour"], errors="coerce"),
            },
            errors="coerce",
        )

        frame = pd.DataFrame(
            {
                "annee": year,
                "jour_semaine": dates.dt.dayofweek,
                "heure": parse_hour(df["hrmn"]),
            }
        )

        frames.append(frame)

    return pd.concat(
        frames,
        ignore_index=True,
    )


def build_heatmap_table(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.dropna(
        subset=["jour_semaine", "heure"]
    ).copy()

    clean["jour_semaine"] = clean["jour_semaine"].astype(int)
    clean["heure"] = clean["heure"].astype(int)

    table = (
        clean.groupby(
            ["jour_semaine", "heure"]
        )
        .size()
        .unstack(fill_value=0)
        .reindex(
            index=range(7),
            columns=range(24),
            fill_value=0,
        )
    )

    return table


def plot_heatmap(table: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = FIGURES_DIR / "accidents_jour_heure.png"

    fig, ax = plt.subplots(figsize=(12, 5))

    image = ax.imshow(
        table.to_numpy(),
        aspect="auto",
    )

    ax.set_title(
        "Répartition des accidents corporels par jour et heure, 2005–2024"
    )
    ax.set_xlabel("Heure")
    ax.set_ylabel("Jour de la semaine")

    ax.set_xticks(range(24))
    ax.set_xticklabels(range(24))

    ax.set_yticks(range(7))
    ax.set_yticklabels(
        [DAY_LABELS[i] for i in range(7)]
    )

    colorbar = fig.colorbar(
        image,
        ax=ax,
    )
    colorbar.set_label("Nombre d'accidents")

    fig.tight_layout()

    fig.savefig(
        output,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("Écrit :", output)


def main() -> None:
    df = load_temporal_data()

    invalid = df[
        df["jour_semaine"].isna()
        | df["heure"].isna()
    ]

    invalid_by_year = (
        df.assign(
            invalide=df["jour_semaine"].isna() | df["heure"].isna()
        )
        .groupby("annee")["invalide"]
        .agg(["sum", "count"])
    )

    invalid_by_year["pct"] = (
        invalid_by_year["sum"]
        / invalid_by_year["count"]
        * 100
    )

    print(invalid_by_year)

    invalid_causes = (
        df.groupby("annee")
        .agg(
            date_invalide=(
                "jour_semaine",
                lambda x: x.isna().sum(),
            ),
            heure_invalide=(
                "heure",
                lambda x: x.isna().sum(),
            ),
        )
    )

    print()
    print(invalid_causes)
    print()
    
    print("Observations totales :", len(df))
    print("Observations invalides:", len(invalid))
    print()

    table = build_heatmap_table(df)

    TABLES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = TABLES_DIR / "accidents_jour_heure.csv"

    table.rename(
        index=DAY_LABELS,
    ).to_csv(
        output,
        sep=";",
    )

    print("Écrit :", output)

    plot_heatmap(table)


if __name__ == "__main__":
    main()
