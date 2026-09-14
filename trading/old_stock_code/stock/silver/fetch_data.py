#!/usr/bin/env python3
"""
Fetch adjusted OHLC data for a large set of tickers using yfinance
and export the results to a CSV file.

Fixes:
- Uses explicit start/end dates instead of Yahoo period strings
- Pulls the past N calendar days before the requested trade date
- Guards against impossible requests like 120 days of 30m data
"""

import argparse
from datetime import date, datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import pandas as pd
import yfinance as yf


# =========================
# CONFIGURATION
# =========================

OUTPUT_FILE = "OHLC_data.csv"
SP500_LIST_FILE = "spy500.txt"
EXTRA_LIST_FILE = "extra.txt"
TICKER_UNIVERSE_FILE = "tickers.txt"
DEFAULT_HISTORY_DAYS = 120
INTERVAL = "1d"
WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKIPEDIA_NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
WIKIPEDIA_DOW30_URL = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"

CUSTOM_TICKERS: List[str] = [
]


# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# =========================
# FUNCTIONS
# =========================

def normalize_ticker(symbol: str) -> str:
    return symbol.strip().upper().replace(".", "-")


def fetch_sp500_tickers() -> List[str]:
    try:
        tables = pd.read_html(
            WIKIPEDIA_SP500_URL,
            flavor="lxml",
            storage_options={"User-Agent": "Mozilla/5.0"},
        )
        df = tables[0]
        symbols = df["Symbol"].tolist()
        normalized = [normalize_ticker(symbol) for symbol in symbols]
        logging.info("Fetched %d S&P 500 tickers from Wikipedia.", len(normalized))
        return normalized
    except Exception as e:
        logging.error("Failed to fetch S&P 500 tickers: %s", e)
        return []


def extract_symbols_from_tables(tables: List[pd.DataFrame]) -> List[str]:
    for table in tables:
        for column_name in ("Symbol", "Ticker", "Ticker symbol"):
            if column_name in table.columns:
                symbols = table[column_name].dropna().astype(str).tolist()
                return [normalize_ticker(symbol) for symbol in symbols if symbol.strip()]
    raise KeyError("No supported ticker column found in HTML tables.")


def fetch_index_tickers(url: str, index_name: str) -> List[str]:
    try:
        tables = pd.read_html(
            url,
            flavor="lxml",
            storage_options={"User-Agent": "Mozilla/5.0"},
        )
        symbols = extract_symbols_from_tables(tables)
        logging.info("Fetched %d %s tickers from Wikipedia.", len(symbols), index_name)
        return symbols
    except Exception as e:
        logging.error("Failed to fetch %s tickers: %s", index_name, e)
        return []


def fetch_nasdaq100_tickers() -> List[str]:
    return fetch_index_tickers(WIKIPEDIA_NASDAQ100_URL, "Nasdaq-100")


def fetch_dow30_tickers() -> List[str]:
    return fetch_index_tickers(WIKIPEDIA_DOW30_URL, "Dow 30")


def build_ticker_universe(*ticker_groups: Iterable[str]) -> List[str]:
    combined: Set[str] = set()
    for group in ticker_groups:
        combined.update(
            normalize_ticker(symbol) for symbol in group if str(symbol).strip()
        )
    return sorted(combined)


def parse_trade_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected YYYY-MM-DD."
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch daily adjusted OHLC data and export each ticker to CSV."
    )
    parser.add_argument(
        "trade_date",
        type=parse_trade_date,
        help="Cutoff date in YYYY-MM-DD. Data will be fetched before this trading day.",
    )
    parser.add_argument(
        "--history-days",
        type=int,
        default=DEFAULT_HISTORY_DAYS,
        help="How many calendar days of history to fetch before trade_date. Default: %(default)s",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help="Output CSV filename. Default: %(default)s",
    )
    parser.add_argument(
        "--market-caps",
        action="store_true",
        help="Fetch market caps and include the Capital volume column. Disabled by default.",
    )
    return parser.parse_args()


def build_output_filename(filename: str, trade_date: Optional[date]) -> str:
    if trade_date is None:
        return filename
    path = Path(filename)
    return str(path.with_name(f"{path.stem}_{trade_date.isoformat()}{path.suffix}"))


def is_intraday_interval(interval: str) -> bool:
    return interval in {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}


def validate_request(history_days: int, interval: str) -> None:
    if is_intraday_interval(interval) and history_days > 60:
        raise ValueError(
            f"Yahoo/yfinance does not support {history_days} days of {interval} data. "
            f"Intraday data is limited to about 60 days. "
            f"Use --interval 1d for 120-day history, or reduce --history-days to 60 or less."
        )


def compute_date_range(trade_date: date, history_days: int) -> tuple[str, str]:
    end_date = trade_date  # exclusive in yfinance
    start_date = trade_date - timedelta(days=history_days)
    return start_date.isoformat(), end_date.isoformat()


def download_batch(
    tickers: List[str],
    start_date: str,
    end_date: str,
    interval: str,
    show_progress: bool,
) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()

    return yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        progress=show_progress,
        threads=False,
    )


def extract_ticker_frame(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        top_level = data.columns.get_level_values(0)
        if ticker not in top_level:
            return pd.DataFrame()
        frame = data[ticker].copy()
    else:
        frame = data.copy()

    return frame.dropna(how="all")


def find_missing_tickers(data: pd.DataFrame, tickers: Iterable[str]) -> List[str]:
    missing = []
    for ticker in tickers:
        frame = extract_ticker_frame(data, ticker)
        if frame.empty:
            missing.append(ticker)
    return missing


def _frame_to_multiindex_columns(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    wrapped = frame.copy()
    wrapped.columns = pd.MultiIndex.from_product([[ticker], wrapped.columns])
    return wrapped


def merge_downloads(primary: pd.DataFrame, retry: pd.DataFrame, tickers: Iterable[str]) -> pd.DataFrame:
    if primary.empty:
        return retry
    if retry.empty:
        return primary

    merged = primary.copy()

    if not isinstance(merged.columns, pd.MultiIndex):
        return merged

    retry_pieces = []
    for ticker in tickers:
        frame = extract_ticker_frame(retry, ticker)
        if frame.empty:
            continue

        try:
            merged = merged.drop(columns=ticker, level=0)
        except (KeyError, ValueError):
            pass

        retry_pieces.append(_frame_to_multiindex_columns(frame, ticker))

    if not retry_pieces:
        return merged

    merged = pd.concat([merged] + retry_pieces, axis=1)
    merged = merged.sort_index(axis=1, level=0)
    return merged


def download_ohlc_data(
    tickers: List[str],
    trade_date: date,
    history_days: int,
    interval: str,
) -> pd.DataFrame:
    validate_request(history_days, interval)
    start_date, end_date = compute_date_range(trade_date, history_days)

    logging.info(
        "Downloading data for %d tickers with start=%s end=%s interval=%s...",
        len(tickers),
        start_date,
        end_date,
        interval,
    )

    data = download_batch(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        show_progress=True,
    )

    missing = find_missing_tickers(data, tickers)

    if missing:
        logging.warning("Retrying %d missing tickers...", len(missing))
        retry = download_batch(
            tickers=missing,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            show_progress=False,
        )
        data = merge_downloads(data, retry, missing)
        still_missing = find_missing_tickers(data, missing)
        if still_missing:
            logging.warning(
                "Still missing %d tickers after retry: %s",
                len(still_missing),
                ", ".join(still_missing),
            )

    return data


def strip_timezones_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    if isinstance(cleaned.index, pd.DatetimeIndex) and cleaned.index.tz is not None:
        cleaned.index = cleaned.index.tz_convert(None)

    for column in cleaned.columns:
        series = cleaned[column]
        if isinstance(series.dtype, pd.DatetimeTZDtype):
            cleaned[column] = series.dt.tz_convert(None)

    return cleaned


def add_ticker_column(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    enriched = df.copy()
    enriched.insert(0, "Ticker", ticker)
    return enriched


def format_market_cap_billions(market_cap: object) -> str:
    try:
        value = float(market_cap)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    return f"{int(round(value / 1_000_000_000))}B"


def fetch_market_caps(tickers: List[str]) -> Dict[str, str]:
    caps: Dict[str, str] = {}
    total = len(tickers)
    if total == 0:
        return caps

    logging.info("Fetching market caps for %d tickers...", total)

    for index, ticker in enumerate(tickers, start=1):
        if index == 1 or index % 25 == 0 or index == total:
            logging.info("Market cap progress: %d/%d (%s)", index, total, ticker)
        cap_value = None
        try:
            ticker_obj = yf.Ticker(ticker)
            fast_info = getattr(ticker_obj, "fast_info", None)
            if fast_info is not None:
                try:
                    cap_value = fast_info.get("marketCap") or fast_info.get("market_cap")
                except Exception:
                    cap_value = None
            if not cap_value:
                info = ticker_obj.info
                cap_value = info.get("marketCap") or info.get("market_cap")
        except Exception as exc:
            logging.warning("Could not fetch market cap for %s: %s", ticker, exc)
            cap_value = None
        caps[ticker] = format_market_cap_billions(cap_value)
    return caps


def write_ticker_list(filename: str, tickers: List[str]) -> None:
    normalized = sorted({normalize_ticker(ticker) for ticker in tickers if str(ticker).strip()})
    with open(filename, "w", encoding="utf-8") as handle:
        handle.write("\n".join(normalized))
        if normalized:
            handle.write("\n")
    logging.info("Wrote %d tickers to %s", len(normalized), filename)


def save_to_csv(data: pd.DataFrame, tickers: List[str], filename: str, market_caps: Optional[Dict[str, str]] = None) -> None:
    logging.info("Writing data to %s...", filename)

    frames: List[pd.DataFrame] = []
    for ticker in tickers:
        try:
            df = extract_ticker_frame(data, ticker)

            if df.empty:
                logging.warning("No data for %s", ticker)
                continue

            df = strip_timezones_for_excel(df)
            df = add_ticker_column(df, ticker)
            if market_caps is not None:
                df["Capital volume"] = ""
                if not df.empty:
                    first_row = df.index[0]
                    df.at[first_row, "Capital volume"] = market_caps.get(ticker, "")
            frames.append(df.reset_index())

        except Exception as e:
            logging.warning("Skipping %s: %s", ticker, e)

    if not frames:
        logging.warning("No ticker data available to write to %s", filename)
        return

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(filename, index=False)


# =========================
# MAIN
# =========================

def main() -> None:
    args = parse_args()
    logging.info("Starting OHLC pipeline...")

    sp500 = fetch_sp500_tickers()
    nasdaq100 = fetch_nasdaq100_tickers()
    dow30 = fetch_dow30_tickers()
    write_ticker_list(SP500_LIST_FILE, sp500)
    write_ticker_list(EXTRA_LIST_FILE, CUSTOM_TICKERS)
    tickers = build_ticker_universe(CUSTOM_TICKERS, sp500, nasdaq100, dow30)
    write_ticker_list(TICKER_UNIVERSE_FILE, tickers)
    logging.info("Built ticker universe with %d unique symbols.", len(tickers))
    market_caps = fetch_market_caps(tickers) if args.market_caps else None

    output_filename = build_output_filename(args.output, args.trade_date)
    data = download_ohlc_data(
        tickers=tickers,
        trade_date=args.trade_date,
        history_days=args.history_days,
        interval=INTERVAL,
    )

    if data.empty:
        logging.error("No data retrieved. Exiting.")
        return

    save_to_csv(data, tickers, output_filename, market_caps=market_caps)
    logging.info("Completed successfully.")


if __name__ == "__main__":
    main()
