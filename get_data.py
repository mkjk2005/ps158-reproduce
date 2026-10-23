"""Download the Survey of Consumer Finances summary extracts (1989-2025) and
compute family net worth by education of the reference person.

Source: Federal Reserve Board, https://www.federalreserve.gov/econres/scfindex.htm
The summary extract files are already in 2025 dollars.

Output: data/networth_by_education.csv with one row per survey year and group.
"""

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE_URL = "https://www.federalreserve.gov/econres/files"
YEARS = list(range(1989, 2026, 3))  # 1989, 1992, ..., 2025
HISTORIC_TABLES = "scf2025_tables_public_real_historical.xlsx"

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/networth_by_education.csv")

# EDCL: education of the reference person
GROUPS = {
    "No high school diploma": [1],
    "High school diploma": [2],
    "Some college": [3],
    "College degree": [4],
    "High school or less": [1, 2],
    "All families": [1, 2, 3, 4],
}


def download(filename):
    path = RAW_DIR / filename
    if not path.exists():
        print(f"downloading {filename}")
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        response = requests.get(f"{BASE_URL}/{filename}", timeout=120)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def read_extract(year):
    with zipfile.ZipFile(download(f"scfp{year}excel.zip")) as z:
        (name,) = [n for n in z.namelist() if n.lower().endswith(".csv")]
        df = pd.read_csv(io.BytesIO(z.read(name)))
    df.columns = df.columns.str.upper()
    df = df.rename(columns={"XX1": "YY1"})  # 1989 uses XX1 for the family ID
    return df[["YY1", "WGT", "EDCL", "NETWORTH"]]


def weighted_median(x, w):
    order = np.argsort(x)
    x, w = np.asarray(x)[order], np.asarray(w)[order]
    cum = np.cumsum(w)
    return x[np.searchsorted(cum, cum[-1] / 2)]


def summarize(year, df):
    # Each family appears five times (one per imputation); pooling all five
    # implicates with WGT reproduces the Fed's published estimates.
    total_weight = df["WGT"].sum()
    rows = []
    for group, codes in GROUPS.items():
        g = df[df["EDCL"].isin(codes)]
        rows.append({
            "year": year,
            "group": group,
            "median_networth": weighted_median(g["NETWORTH"], g["WGT"]),
            "mean_networth": np.average(g["NETWORTH"], weights=g["WGT"]),
            "share_of_families": g["WGT"].sum() / total_weight,
            "n_families": g["YY1"].nunique(),
        })
    return rows


def check_against_fed(results):
    """Compare our estimates with Table 4 of the Fed's historic tables."""
    table = pd.read_excel(download(HISTORIC_TABLES), sheet_name="Table 4", header=None)
    years = [v for v in table.iloc[2] if isinstance(v, int)]
    for group in ["All families", "No high school diploma", "High school diploma",
                  "Some college", "College degree"]:
        row = table[table[0].astype(str).str.strip() == group].iloc[0, 1:].tolist()
        for year, fed_median, fed_mean in zip(years, row[0::2], row[1::2]):
            ours = results.query("year == @year and group == @group").iloc[0]
            assert abs(ours.median_networth / 1000 - fed_median) < 0.01, (year, group, "median")
            assert abs(ours.mean_networth / 1000 - fed_mean) < 0.01, (year, group, "mean")
    print("all medians and means match the Fed's published Table 4")


def main():
    rows = []
    for year in YEARS:
        rows += summarize(year, read_extract(year))
    results = pd.DataFrame(rows)
    check_against_fed(results)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT_FILE, index=False, float_format="%.2f")
    print(f"wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
