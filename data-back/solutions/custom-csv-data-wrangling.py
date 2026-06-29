"""Sales-CSV wrangling: total per product, filter by region, handle NaN.

Pure-Python implementation (no third-party deps) plus the pandas one-liners
shown in comments. Runnable against an in-memory sample so the totals are
verifiable.
"""

import csv
import io
from collections import defaultdict

SAMPLE = """Date,Product,Region,Sales
2023-01-01,Widget A,North,100
2023-01-01,Widget A,East,300
2023-01-01,Widget B,South,150
2023-01-02,Widget A,North,200
2023-01-02,Widget B,South,250
2023-01-03,Widget A,North,50
2023-01-03,Widget B,South,75
2023-01-04,Widget B,South,
"""  # last row has a missing Sales value (NaN)


def totals_per_product(rows, missing="skip"):
    """Sum Sales per Product. `missing` = 'skip' (drop NaN) or 'zero'."""
    totals = defaultdict(float)
    for row in rows:
        raw = (row.get("Sales") or "").strip()
        if not raw:
            if missing == "zero":
                totals[row["Product"]] += 0.0
            continue  # 'skip': leave it out of the sum
        totals[row["Product"]] += float(raw)
    return dict(totals)


def filter_region(rows, region):
    return [r for r in rows if r["Region"] == region]


if __name__ == "__main__":
    rows = list(csv.DictReader(io.StringIO(SAMPLE)))

    # 1) Total sales per product (missing Sales dropped):
    print(totals_per_product(rows))
    # {'Widget A': 650.0, 'Widget B': 475.0}

    # 2) Only North-region rows, then total per product:
    north = filter_region(rows, "North")
    print(totals_per_product(north))
    # {'Widget A': 350.0}

    # 3) Missing-data strategy made explicit:
    print("drop NaN :", totals_per_product(rows, missing="skip"))
    print("fill 0   :", totals_per_product(rows, missing="zero"))

    # pandas equivalents:
    #   import pandas as pd
    #   df = pd.read_csv("sales.csv")
    #   df.groupby("Product")["Sales"].sum()          # totals per product
    #   df[df["Region"] == "North"]                   # filter by region
    #   df.dropna(subset=["Sales"])                   # drop missing
    #   df["Sales"].fillna(0)                         # or fill with 0
    #   df["Sales"].fillna(df["Sales"].mean())        # or impute the mean
