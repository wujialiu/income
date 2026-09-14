# Codex Repository Guide

## Purpose

This repository contains a Python pipeline for building a U.S. stock ticker universe and exporting historical OHLCV data with `yfinance`.

The active code is in the repository root and `silver/`. Treat `old_stock_code/` as archived unless the user explicitly asks to work there.

## Main Commands

Run the data pipeline:

```bash
python3 fetch_data.py 2024-04-06
```

Run with a shorter history window:

```bash
python3 fetch_data.py 2024-04-06 --history-days 60
```

Include market cap labels in the export:

```bash
python3 fetch_data.py 2024-04-06 --market-caps
```

Use a custom output base filename:

```bash
python3 fetch_data.py 2024-04-06 --output my_custom_data.csv
```

Generate stock charts:

```bash
python3 silver/stock_30.py SNDK
python3 silver/stock_180.py SNDK
```

Generate silver charts:

```bash
python3 silver/silver_30.py
python3 silver/silver_180.py
```

## Data Flow

1. Fetch index constituents from Wikipedia: S&P 500, S&P MidCap 400, Nasdaq-100, and Dow 30.
2. Read custom tickers from `extra.txt`.
3. Normalize ticker symbols by trimming whitespace, uppercasing, and replacing `.` with `-`.
4. Deduplicate all ticker sources into `tickers.txt`.
5. Download historical daily OHLCV data before the requested trade date.
6. Write the combined CSV as `OHLC_data_<trade_date>.csv` unless a different output base name is provided.

## Important Files

- `fetch_data.py`: Main CLI and OHLCV pipeline.
- `extra.txt`: User-maintained custom ticker input. Do not overwrite this file from generated data.
- `tickers.txt`: Generated deduped ticker universe.
- `spy500.txt`: Generated S&P 500 ticker list.
- `sp400.txt`: Generated S&P MidCap 400 ticker list.
- `nasdaq100.txt`: Generated Nasdaq-100 ticker list.
- `dow30.txt`: Generated Dow 30 ticker list.
- `OHLC_data_YYYY-MM-DD.csv`: Generated historical data exports.
- `silver/*.py`: Plotly chart scripts for stock/SPY and silver/gold views.
- `silver/*.html`: Generated chart snapshots.

## Dependencies

The code expects these Python packages:

- `pandas`
- `numpy`
- `yfinance`
- `plotly`
- `lxml`

There is currently no `requirements.txt` or lockfile, so verify imports locally before assuming the environment is reproducible.

## Working Notes

- The pipeline relies on live Wikipedia and Yahoo Finance data; constituent lists and OHLCV output can change over time.
- `tickers.txt` is generated through set-based dedupe, so duplicates across index sources are collapsed.
- `extra.txt` is an input source and supports whitespace or comma-separated tickers plus `#` comments.
- Avoid hand-editing generated ticker files unless the user asks for a one-off data change.
- After code changes, run at least a syntax check:

```bash
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('fetch_data.py').read_text()); print('syntax ok')"
```
