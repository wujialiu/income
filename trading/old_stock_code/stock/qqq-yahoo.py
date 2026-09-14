#!/usr/bin/env python3
"""
qqq-all-in-one.py

All-in-one improved pipeline:
1) Retrieve QQQ/Nasdaq-100 tickers (Wikipedia) safely (User-Agent + StringIO)
2) Normalize tickers for Yahoo (e.g., BRK.B -> BRK-B)
3) Deduplicate tickers
4) Fetch Yahoo Finance summary fields via yfinance with retries & pacing
5) Save:
   - Full snapshot CSV
   - Clean subset CSV (most useful columns)
   - Run report txt (success/fail/dups)
6) (Optional) Save to SQLite

Deps:
  pip install -U requests lxml pandas yfinance
Optional SQLite export: uses Python stdlib sqlite3 (no extra deps)
"""

import sys
import time
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
import yfinance as yf

# ---------------------------
# Configuration
# ---------------------------

FULL_CSV = "qqq_yahoo_summary_full.csv"
CLEAN_CSV = "qqq_yahoo_summary_clean.csv"
REPORT_TXT = "qqq_run_report.txt"
SQLITE_DB = "qqq_yahoo_summary.sqlite"
SQLITE_TABLE = "qqq_summary"

# polite pacing between Yahoo requests
SLEEP_BETWEEN_TICKERS_SEC = 0.5

# yfinance retry behavior
YF_RETRIES = 3
YF_BACKOFF_BASE_SEC = 0.8  # multiplied by attempt #

# Optional exports
WRITE_SQLITE = False  # set True if you want SQLite output too


# Clean subset columns (keeps only what exists in the data)
CLEAN_KEEP = [
    "ticker",
    "shortName",
    "longName",
    "symbol",
    "exchange",
    "quoteType",
    "currency",

    "sector",
    "industry",
    "fullTimeEmployees",

    "regularMarketPrice",
    "previousClose",
    "open",
    "dayLow",
    "dayHigh",
    "fiftyTwoWeekLow",
    "fiftyTwoWeekHigh",

    "regularMarketVolume",
    "averageVolume",
    "averageVolume10days",

    "marketCap",
    "enterpriseValue",

    "trailingPE",
    "forwardPE",
    "priceToBook",
    "beta",

    "trailingEps",
    "forwardEps",

    "dividendRate",
    "dividendYield",
    "payoutRatio",

    "profitMargins",
    "grossMargins",
    "operatingMargins",
    "ebitdaMargins",

    "revenueGrowth",
    "earningsGrowth",

    "totalRevenue",
    "ebitda",

    "recommendationKey",
    "recommendationMean",
]


# ---------------------------
# Helpers
# ---------------------------

def normalize_ticker_for_yahoo(t: str) -> str:
    # Yahoo uses '-' not '.'
    return t.strip().replace(".", "-")


def get_qqq_tickers_from_wikipedia() -> list[str]:
    """
    Wikipedia can block naive scrapers, so we fetch with a browser UA.
    We then parse tables from HTML via pandas.read_html(StringIO(html)).
    """
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    tables = pd.read_html(StringIO(r.text))

    target = None
    for t in tables:
        cols = [str(c).strip().lower() for c in t.columns]
        if "ticker" in cols and ("company" in cols or "security" in cols):
            target = t
            break

    if target is None:
        for t in tables:
            cols = [str(c).strip().lower() for c in t.columns]
            if "ticker" in cols:
                target = t
                break

    if target is None:
        raise RuntimeError("Could not find Nasdaq-100 constituents table on Wikipedia.")

    tickers = target["Ticker"].astype(str).str.strip().tolist()
    tickers = [normalize_ticker_for_yahoo(x) for x in tickers]
    return tickers


def fetch_yahoo_info(ticker: str) -> dict:
    """
    Fetch Yahoo Finance summary fields via yfinance with retry + backoff.
    """
    last_err = None
    for attempt in range(1, YF_RETRIES + 1):
        try:
            info = yf.Ticker(ticker).info
            if not isinstance(info, dict) or not info:
                raise RuntimeError("Empty info dict (rate-limit or transient failure)")
            info["ticker"] = ticker
            return info
        except Exception as e:
            last_err = e
            time.sleep(YF_BACKOFF_BASE_SEC * attempt)
    raise last_err


def write_report(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def maybe_write_sqlite(df: pd.DataFrame, db_path: str, table: str) -> None:
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)


# ---------------------------
# Main
# ---------------------------

def main():
    start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [f"Run started: {start_ts}"]

    # 1) get tickers
    try:
        tickers_raw = get_qqq_tickers_from_wikipedia()
    except Exception as e:
        print(f"Failed to get QQQ tickers: {e}", file=sys.stderr)
        sys.exit(1)

    report_lines.append(f"Tickers fetched (raw): {len(tickers_raw)}")

    # 2) deduplicate while preserving order
    seen = set()
    tickers = []
    dups = []
    for t in tickers_raw:
        if t in seen:
            dups.append(t)
            continue
        seen.add(t)
        tickers.append(t)

    report_lines.append(f"Tickers after dedup: {len(tickers)}")
    report_lines.append(f"Duplicates removed: {len(dups)}")
    if dups:
        report_lines.append("Duplicate tickers:")
        report_lines.extend([f"  {x}" for x in sorted(set(dups))])

    print(f"Found {len(tickers)} unique QQQ tickers")

    # 3) fetch Yahoo summaries
    rows = []
    failures = []

    for i, t in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching {t}")
            rows.append(fetch_yahoo_info(t))
            time.sleep(SLEEP_BETWEEN_TICKERS_SEC)
        except Exception as e:
            failures.append((t, str(e)))
            print(f"ERROR fetching {t}: {e}", file=sys.stderr)

    report_lines.append(f"Successful tickers: {len(rows)}")
    report_lines.append(f"Failed tickers: {len(failures)}")
    if failures:
        report_lines.append("Failures:")
        for t, err in failures:
            report_lines.append(f"  {t}: {err}")

    if not rows:
        report_lines.append("No data fetched; exiting.")
        write_report(REPORT_TXT, report_lines)
        sys.exit(2)

    # 4) Save full snapshot
    df_full = pd.DataFrame(rows)

    # Ensure ticker first
    cols = ["ticker"] + [c for c in df_full.columns if c != "ticker"]
    df_full = df_full[cols]

    df_full.to_csv(FULL_CSV, index=False)
    report_lines.append(f"Full CSV saved: {FULL_CSV} (rows={len(df_full)}, cols={len(df_full.columns)})")

    # 5) Save clean subset snapshot
    clean_cols = [c for c in CLEAN_KEEP if c in df_full.columns]
    df_clean = df_full[clean_cols].copy()
    df_clean.to_csv(CLEAN_CSV, index=False)
    report_lines.append(f"Clean CSV saved: {CLEAN_CSV} (rows={len(df_clean)}, cols={len(df_clean.columns)})")

    # 6) Optional SQLite
    if WRITE_SQLITE:
        maybe_write_sqlite(df_full, SQLITE_DB, SQLITE_TABLE)
        report_lines.append(f"SQLite saved: {SQLITE_DB} table={SQLITE_TABLE}")

    end_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines.append(f"Run finished: {end_ts}")

    write_report(REPORT_TXT, report_lines)

    print("\nDone.")
    print(f"  Full:  {FULL_CSV}")
    print(f"  Clean: {CLEAN_CSV}")
    print(f"  Report:{REPORT_TXT}")
    if WRITE_SQLITE:
        print(f"  SQLite:{SQLITE_DB} ({SQLITE_TABLE})")


if __name__ == "__main__":
    main()
