import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("datasets/baac")
TABLES_DIR = Path("reports/baac-2005-2024/tables")
FIGURES_DIR = Path("reports/baac-2005-2024/figures")

GRAVITY_LABELS = {
    1: "indemnes",
    2: "tues",
    3: "hospitalises",
    4: "legers",
    -1: "non_renseigne",
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


def victims_by_severity() -> pd.DataFrame:
    rows = []

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

        counts = df["grav"].value_counts()

        row = {
            "annee": year,
            "indemnes": int(counts.get(1, 0)),
            "tues": int(counts.get(2, 0)),
            "hospitalises": int(counts.get(3, 0)),
            "legers": int(counts.get(4, 0)),
            "non_renseigne": int(counts.get(-1, 0)),
        }

        row["victimes"] = (
            row["tues"]
            + row["hospitalises"]
            + row["legers"]
        )

        rows.append(row)

    return pd.DataFrame(rows)


def plot_victims(result: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = FIGURES_DIR / "victimes_par_gravite.png"

    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.plot(
        result["annee"],
        result["tues"],
        marker="o",
        label="Tués",
    )

    ax.plot(
        result["annee"],
        result["hospitalises"],
        marker="o",
        label="Blessés hospitalisés",
    )

    ax.plot(
        result["annee"],
        result["legers"],
        marker="o",
        label="Blessés légers",
    )

    ax.axvline(
        2018,
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
    )

    ax.text(
        2018.15,
        ax.get_ylim()[1] * 0.95,
        "Rupture de comparabilité\n(blessés hospitalisés)",
        va="top",
    )
    
    ax.set_title(
        "Victimes d'accidents corporels par gravité, 2005–2024"
    )
    ax.set_xlabel("Année")
    ax.set_ylabel("Nombre de victimes")

    ax.set_xticks(range(2005, 2025))
    ax.tick_params(
        axis="x",
        rotation=45,
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    ax.legend()

    fig.text(
        0.5,
        0.01,
        (
            "À partir de 2018, la série des blessés hospitalisés "
            "n'est plus directement comparable aux années antérieures."
        ),
        ha="center",
        fontsize=9,
    )

    fig.tight_layout(rect=(0, 0.05, 1, 1))

    fig.savefig(
        output,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("Écrit :", output)


def main() -> None:
    result = victims_by_severity()

    TABLES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = TABLES_DIR / "victimes_par_gravite.csv"

    result.to_csv(
        output,
        sep=";",
        index=False,
    )

    print(result.to_string(index=False))
    print()
    print("Écrit :", output)

    plot_victims(result)


if __name__ == "__main__":
    main()
