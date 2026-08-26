from pathlib import Path

import csv
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("datasets/baac")
OUTPUT_DIR = Path("reports/baac-2005-2024/tables")
FIGURES_DIR = Path("reports/baac-2005-2024/figures")


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


def accidents_by_year() -> pd.DataFrame:
    rows = []

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

        rows.append(
            {
                "annee": year,
                "accidents": len(df),
            }
        )

    result = pd.DataFrame(rows)

    result["variation_pct"] = (
        result["accidents"]
        .pct_change()
        .mul(100)
    )

    result["variation_depuis_2005_pct"] = (
        result["accidents"]
        .div(result.loc[0, "accidents"])
        .sub(1)
        .mul(100)
    )

    return result


def plot_accidents(result: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = FIGURES_DIR / "accidents_par_annee.png"

    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.plot(
        result["annee"],
        result["accidents"],
        marker="o",
        linewidth=1.8,
    )

    ax.set_title(
        "Accidents corporels enregistrés en France, 2005–2024"
    )
    ax.set_xlabel("Année")
    ax.set_ylabel("Nombre d'accidents corporels")

    ax.set_xticks(range(2005, 2025))
    ax.tick_params(
        axis="x",
        rotation=45,
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    start = int(result.iloc[0]["accidents"])
    end = int(result.iloc[-1]["accidents"])
    change = float(
        result.iloc[-1]["variation_depuis_2005_pct"]
    )

    ax.annotate(
        f"{start:,}".replace(",", " "),
        xy=(2005, start),
        xytext=(2006, start + 2200),
        arrowprops={"arrowstyle": "->"},
    )

    ax.annotate(
        "47 744\n(-18,9 % sur un an)",
        xy=(2020, 47744),
        xytext=(2016.5, 49000),
        arrowprops={"arrowstyle": "->"},
    )

    ax.annotate(
        f"{end:,} ({change:.1f} %)".replace(",", " "),
        xy=(2024, end),
        xytext=(2020.8, 57500),
        arrowprops={"arrowstyle": "->"},
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
    result = accidents_by_year()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = OUTPUT_DIR / "accidents_par_annee.csv"

    result.to_csv(
        output,
        sep=";",
        index=False,
        float_format="%.2f",
    )

    print(result.to_string(index=False))
    print()
    print("Écrit :", output)

    plot_accidents(result)


if __name__ == "__main__":
    main()
