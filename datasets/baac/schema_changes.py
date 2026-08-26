from pathlib import Path

import pandas as pd

INPUT = Path("datasets/baac/schema_history.csv")


def main() -> None:
    df = pd.read_csv(INPUT, sep=";")

    presence = (
        df.assign(present=True)
        .pivot_table(
            index=["table", "colonne"],
            columns="annee",
            values="present",
            aggfunc="first",
            fill_value=False,
        )
    )

    print("Colonnes apparues ou disparues")
    print("==============================")
    print()

    for (table, column), row in presence.iterrows():
        years = [year for year, present in row.items() if present]

        if len(years) == 20:
            continue

        print(
            f"{table:17} {column:20} "
            f"{min(years)}–{max(years)} "
            f"({len(years)}/20)"
        )


if __name__ == "__main__":
    main()
