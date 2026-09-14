import os
from pathlib import Path
import ssl
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fetch_data as pipeline


@contextmanager
def temporary_working_directory():
    previous = Path.cwd()
    with tempfile.TemporaryDirectory() as directory:
        os.chdir(directory)
        try:
            yield
        finally:
            os.chdir(previous)


class TickerRefreshTests(unittest.TestCase):
    def test_https_uses_verified_system_context_and_parses_symbols(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b"<table><tr><th>Symbol</th></tr>"
            b"<tr><td>BRK.B</td></tr><tr><td>AAPL</td></tr></table>"
        )
        with patch.object(pipeline, "urlopen", return_value=response) as request:
            symbols = pipeline.fetch_sp500_tickers()
        self.assertEqual(symbols, ["BRK-B", "AAPL"])
        context = request.call_args.kwargs["context"]
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        self.assertEqual(request.call_args.kwargs["timeout"], 30)

    def test_missing_table_and_network_errors_are_fatal(self):
        for error in (OSError("connection failed"), ssl.SSLError("untrusted CA")):
            with self.subTest(error=error), patch.object(
                pipeline, "urlopen", side_effect=error
            ), self.assertRaises(RuntimeError):
                pipeline.fetch_sp500_tickers()
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b"<table><tr><th>Company</th></tr><tr><td>Apple</td></tr></table>"
        )
        with patch.object(pipeline, "urlopen", return_value=response), \
                self.assertRaises(RuntimeError):
            pipeline.fetch_sp500_tickers()

    def test_late_fetch_failure_preserves_all_existing_files(self):
        filenames = [
            pipeline.SP500_LIST_FILE, pipeline.MIDCAP400_LIST_FILE,
            pipeline.NASDAQ100_LIST_FILE, pipeline.DOW30_LIST_FILE,
            pipeline.TICKER_UNIVERSE_FILE,
        ]
        with temporary_working_directory(), ExitStack() as stack:
            for filename in filenames:
                Path(filename).write_text("EXISTING\n", encoding="utf-8")
            stack.enter_context(patch.object(sys, "argv", ["fetch_data.py", "--tickers-only"]))
            for name in ("fetch_sp500_tickers", "fetch_midcap400_tickers", "fetch_nasdaq100_tickers"):
                stack.enter_context(patch.object(pipeline, name, return_value=["AAPL"]))
            stack.enter_context(patch.object(pipeline, "fetch_dow30_tickers", side_effect=RuntimeError("offline")))
            with self.assertRaises(SystemExit) as result:
                pipeline.main()
            self.assertEqual(result.exception.code, 1)
            for filename in filenames:
                self.assertEqual(Path(filename).read_text(), "EXISTING\n")

    def test_tickers_only_merges_extras_without_downloading_prices(self):
        with temporary_working_directory(), ExitStack() as stack:
            Path("extra.txt").write_text("msft, brk.b # comment\n", encoding="utf-8")
            stack.enter_context(patch.object(sys, "argv", ["fetch_data.py", "--tickers-only"]))
            for name in ("fetch_sp500_tickers", "fetch_midcap400_tickers", "fetch_nasdaq100_tickers", "fetch_dow30_tickers"):
                stack.enter_context(patch.object(pipeline, name, return_value=["AAPL", "MSFT"]))
            download = stack.enter_context(patch.object(pipeline, "download_ohlc_data"))
            pipeline.main()
            self.assertEqual(Path("tickers.txt").read_text(), "AAPL\nBRK-B\nMSFT\n")
            self.assertEqual(Path("extra.txt").read_text(), "msft, brk.b # comment\n")
            download.assert_not_called()

    def test_price_download_still_requires_date(self):
        with patch.object(sys, "argv", ["fetch_data.py"]), \
                self.assertRaises(SystemExit) as result:
            pipeline.parse_args()
        self.assertEqual(result.exception.code, 2)
        with patch.object(sys, "argv", ["fetch_data.py", "2026-09-14"]):
            args = pipeline.parse_args()
        self.assertEqual(args.trade_date.isoformat(), "2026-09-14")
        self.assertFalse(args.tickers_only)


if __name__ == "__main__":
    unittest.main()
