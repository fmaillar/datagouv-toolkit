import csv
from pathlib import Path

import pandas as pd

DATA_DIR = Path("datasets/baac")


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


def main() -> None:
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

        values = sorted(df["grav"].dropna().unique().tolist())

        print(f"{year}: {values} n={len(df)}")


if __name__ == "__main__":
    main()
