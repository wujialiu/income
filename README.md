# income

Python tools for refreshing a U.S. stock ticker universe, downloading historical
OHLCV data, and generating stock and precious-metal charts. Active code lives in
`trading/`; `trading/old_stock_code/` is archived.

## Setup

Use Python 3.11 or later (tested with 3.13). From the repository root on macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

On Windows, create the environment with `py -3 -m venv .venv` and activate it in
PowerShell with `.venv\Scripts\Activate.ps1`, then run the same pip commands.
Activate this environment again in each new terminal. The environment and Python
caches are ignored by Git; commit `requirements.txt`, not the environment folder.
Direct dependencies are pinned; their transitive dependencies are resolved by pip.

## Refresh tickers

```bash
cd trading
python fetch_data.py --tickers-only
```

This refreshes `spy500.txt`, `sp400.txt`, `nasdaq100.txt`, `dow30.txt`, and the
sorted, deduplicated `tickers.txt`. Put custom symbols in `extra.txt` using spaces,
commas, or newlines; `#` starts a comment. All index sources must succeed before
any ticker file is written. A fetch or parsing failure exits with a nonzero status.

Wikipedia HTTPS requests use the operating system's trusted certificates through
[truststore](https://truststore.readthedocs.io/en/latest/), with certificate and
hostname verification enabled. On a corporate network, its CA must be installed
in the system trust store by your administrator. This applies to constituent
downloads; Yahoo Finance connections are handled separately by `yfinance`.

## Download data and generate charts

Run from `trading/` with the environment active:

```bash
python fetch_data.py 2026-09-14 --history-days 60
python fetch_data.py 2026-09-14 --market-caps
python silver/stock_30.py SNDK
python silver/stock_180.py SNDK
python silver/silver_30.py
python silver/silver_180.py
```

The date is an exclusive cutoff for historical prices. Index membership is fetched
live, not as of that date. CSV output defaults to `OHLC_data_<date>.csv`.

## Checks

From the repository root with the environment active:

```bash
python -m unittest discover -s trading/tests -v
python -m compileall -q trading/fetch_data.py trading/silver
```

The tests use mocked network responses and do not modify the repository's ticker
files. `python fetch_data.py --tickers-only` is the live integration check when run
from `trading/`.
