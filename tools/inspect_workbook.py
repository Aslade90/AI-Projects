from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


WORKBOOK = Path(r"C:\Users\sladeand\Desktop\Codex Manufacturing Data.xlsx")


def main() -> None:
    xls = pd.ExcelFile(WORKBOOK)
    print(json.dumps({"sheets": xls.sheet_names}, ensure_ascii=True))

    for sheet in xls.sheet_names:
        df = pd.read_excel(WORKBOOK, sheet_name=sheet)
        print(
            "SHEET_SUMMARY",
            json.dumps(
                {
                    "sheet": sheet,
                    "rows": len(df),
                    "ncols": len(df.columns),
                    "cols": [str(col) for col in df.columns[:20]],
                },
                ensure_ascii=True,
            ),
        )

    long_df = pd.read_excel(WORKBOOK, sheet_name="Long Format")
    print("LONG_COLS", json.dumps(list(long_df.columns), ensure_ascii=True))

    for column in ["Category", "Measurement Type", "Construct"]:
        values = sorted(str(value) for value in long_df[column].dropna().unique())
        print(column, json.dumps(values, ensure_ascii=True))

    long_df["Project"] = long_df["Batch"].astype(str).str.extract(r"^([A-Z]\d{4}-\d{2})")
    print("PROJECTS", json.dumps(sorted(long_df["Project"].dropna().unique()), ensure_ascii=True))
    print(
        "BATCHES_TAIL",
        json.dumps(sorted(long_df["Batch"].dropna().astype(str).unique())[-20:], ensure_ascii=True),
    )
    print(
        "COUNTS_BY_MEAS",
        json.dumps(long_df.groupby(["Measurement Type"]).size().sort_index().to_dict(), ensure_ascii=True),
    )

    input_like = [
        col
        for col in long_df.columns
        if re.search(r"input|recent|highlight|current", str(col), re.IGNORECASE)
    ]
    print("INPUT_LIKE_LONG_COLUMNS", json.dumps(input_like, ensure_ascii=True))


if __name__ == "__main__":
    main()
