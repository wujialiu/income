# CLAUDE.md

for test

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
This repository contains a Python-based pipeline for fetching historical OHLC (Open, High, Low, Close) stock market data using the `yfinance` library and exporting it to CSV format. It automates the process of building a ticker universe (including S&P 500, Nasdaq-100, and Dow 30) and downloading historical price data for a specific target date.

## Common Commands

### Running the Data Pipeline
The main entry point is `fetch_data.py`. It requires a `trade_date` in `YYYY-MM-DD` format.

```bash
# Fetch data for a specific date (default 120 days of history)
python3 fetch_data.py 2024-04-06

# Fetch data with a custom history window
python3 fetch_data.py 2024-04-06 --history-days 60

# Fetch data and include market capitalization information
python3 fetch_data.py 2024-04-06 --market-caps

# Specify a custom output filename
python3 fetch_data.py 2024-04-06 --output my_custom_data.csv
```

## Architecture & Structure

### Pipeline Flow
1.  **Ticker Discovery**: The script fetches the latest S&P 50
00, Nasdaq-100, and Dow 30 symbols by scraping Wikipedia.
2.  **Universe Construction**: It merges discovered indices with custom tickers provided in `extra.txt` and saves the resulting universe to `tickers.txt`.
3.  **Data Fetching**: Uses `yfinance` to download historical OHLC data for the constructed universe for the period preceding the specified `trade_date`.
4.  **Data Processing**: Uses `pandas` to clean, normalize, and format the data (e.g., stripping timezones for Excel compatibility).
5.  **Export**: Writes the processed data into a CSV file, with the filename timestamped with the `trade_date`.

### Key Files
- `fetch_data.py`: The core logic and command-line interface.
- `tickers.txt`: The generated master list of all tickers to be processed.
- `spy500.txt`: The generated list of S&P 500 tickers.
- `extra.txt`: A user-editable file for adding custom tickers to the universe.
- `OHLC_data_YYYY-MM-DD.csv`: The resulting data exports.

### Dependencies
- `pandas`: Data manipulation and CSV export.
- `yfinance`: Interface with Yahoo Finance API.
- `lxml`: Required for parsing Wikipedia HTML tables.
- `numpy`: Underlying numerical computation.
