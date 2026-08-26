import csv
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("datasets/baac")

AGE_BINS = [-1, 14, 17, 24, 34, 44, 54, 64, 74, 200]

AGE_LABELS = [
    "0–14",
    "15–17",
    "18–24",
    "25–34",
    "35–44",
    "45–54",
    "55–64",
    "65–74",
    "75+",
]

TABLES_DIR = Path("reports/baac-2005-2024/tables")
TABLES_DIR.mkdir(parents=True, exist_ok=True)


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


def plot_age_severity(severity_share: pd.DataFrame) -> None:
    output = Path(
        "reports/baac-2005-2024/figures/"
        "gravite_par_classe_age.png"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(10, 5.5))

    severity_share.plot(
        kind="bar",
        stacked=True,
        ax=ax,
    )

    ax.set_title(
        "Gravité des victimes selon la classe d'âge, 2005–2024"
    )
    ax.set_xlabel("Classe d'âge")
    ax.set_ylabel("Part des victimes (%)")

    ax.legend(
        ["Tués", "Blessés hospitalisés", "Blessés légers"]
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        output,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("Écrit :", output)


def main() -> None:
    frames = []

    for year in range(2005, 2025):
        path = DATA_DIR / str(year) / f"Usagers_{year}.csv"

        encoding = detect_encoding(path)
        separator = detect_separator(path, encoding)

        df = pd.read_csv(
            path,
            sep=separator,
            encoding=encoding,
            low_memory=False,
        )

        birth_year = pd.to_numeric(
            df["an_nais"],
            errors="coerce",
        )

        age = year - birth_year

        valid_age = (
            birth_year.notna()
            & age.between(0, 110)
        )

        victims = df["grav"].isin([2, 3, 4])

        clean = df.loc[
            valid_age & victims,
            ["grav"],
        ].copy()

        clean["annee"] = year
        clean["age"] = age.loc[clean.index]

        clean["classe_age"] = pd.cut(
            clean["age"],
            bins=AGE_BINS,
            labels=AGE_LABELS,
        )

        frames.append(clean)

    data = pd.concat(
        frames,
        ignore_index=True,
    )

    result = (
        data.groupby(
            ["classe_age", "grav"],
            observed=True,
        )
        .size()
        .unstack(fill_value=0)
        .rename(
            columns={
                2: "tues",
                3: "hospitalises",
                4: "legers",
            }
        )
        .reindex(AGE_LABELS)
    )

    severity_share = result.div(
        result.sum(axis=1),
        axis=0,
    ).mul(100)

    print()
    print("Répartition de la gravité (%)")
    print(severity_share.round(2))
    
    print(result)

    plot_age_severity(severity_share)

    result.to_csv(
        TABLES_DIR / "victimes_par_classe_age.csv",
        sep=";",
    )

    

if __name__ == "__main__":
    main()
