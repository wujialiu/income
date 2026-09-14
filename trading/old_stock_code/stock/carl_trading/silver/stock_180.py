import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots


def make_fallback_data(periods: int = 180, base_level: float = 100.0) -> pd.DataFrame:
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=periods)
    base_price = base_level + np.linspace(-3.0, 8.0, periods)
    seasonal = 4.0 * np.sin(np.linspace(0, 5 * np.pi, periods))
    close = base_price + seasonal
    open_ = np.roll(close, 1)
    open_[0] = close[0] - 0.5
    intraday_range = 1.5 + 0.3 * np.sin(np.linspace(0, 3 * np.pi, periods))
    high = np.maximum(open_, close) + intraday_range
    low = np.minimum(open_, close) - intraday_range
    volume = np.linspace(2_000_000, 4_000_000, periods) + 400_000 * np.cos(np.linspace(0, 4 * np.pi, periods))

    return pd.DataFrame(
        {
            'Open': open_,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': np.maximum(volume.astype(int), 0),
        },
        index=dates,
    )


def load_market_data(symbol: str, fallback_base_level: float, period: str, fallback_periods: int) -> pd.DataFrame:
    data = yf.download(symbol, period=period, interval='1d', progress=False, auto_adjust=False)

    if data.empty:
        print(f"No price data returned for {symbol}. Using fallback sample data instead.")
        return make_fallback_data(periods=fallback_periods, base_level=fallback_base_level)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required_columns = {'Open', 'High', 'Low', 'Close', 'Volume'}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        missing_list = ', '.join(sorted(missing_columns))
        print(f"Missing expected columns from downloaded data: {missing_list}. Using fallback sample data instead.")
        return make_fallback_data(periods=fallback_periods, base_level=fallback_base_level)

    return data


def build_chart(data: pd.DataFrame, ticker: str, benchmark: str) -> go.Figure:
    data = data.copy()
    data['SMA_5'] = data['Close'].rolling(window=5).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['BB_Middle'] = data['Close'].rolling(window=20).mean()
    rolling_std = data['Close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Middle'] + (2 * rolling_std)
    data['BB_Lower'] = data['BB_Middle'] - (2 * rolling_std)
    delta = data['Close'].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(window=14).mean()
    avg_loss = losses.rolling(window=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    data['RSI_14'] = 100 - (100 / (1 + rs))

    if data[['Close', 'Relative_Ratio', 'RSI_14']].dropna().empty:
        raise RuntimeError("Not enough data to compute the chart indicators.")

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.58, 0.22, 0.20],
        specs=[[{"secondary_y": True}], [{}], [{}]],
    )

    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=f'{ticker} price',
            increasing_line_color='green',
            increasing_fillcolor='green',
            decreasing_line_color='red',
            decreasing_fillcolor='red',
        ),
        row=1,
        col=1,
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=data.index, y=data['SMA_5'], name='5-day SMA', line=dict(color='crimson', width=2)),
        row=1,
        col=1,
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['BB_Middle'],
            name='Bollinger middle band (20-day SMA)',
            line=dict(color='purple', width=2, dash='dot'),
        ),
        row=1,
        col=1,
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=data.index, y=data['SMA_50'], name='50-day SMA', line=dict(color='blue', width=2)),
        row=1,
        col=1,
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['BB_Upper'],
            name='Bollinger upper band (20, 2)',
            line=dict(color='seagreen', dash='dash'),
        ),
        row=1,
        col=1,
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['BB_Lower'],
            name='Bollinger lower band (20, 2)',
            line=dict(color='seagreen', dash='dash'),
            fill='tonexty',
            fillcolor='rgba(46, 139, 87, 0.08)',
        ),
        row=1,
        col=1,
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Trading volume',
            marker_color='midnightblue',
            opacity=0.7,
        ),
        row=1,
        col=1,
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['Relative_Ratio'],
            name=f'{ticker}/{benchmark} ratio',
            line=dict(color='black', width=2),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(x=data.index, y=data['RSI_14'], name='RSI (14)', line=dict(color='darkorange', width=2)),
        row=3,
        col=1,
    )

    fig.add_hline(y=80, line=dict(color='firebrick', dash='dot'), row=3, col=1)
    fig.add_hline(y=20, line=dict(color='forestgreen', dash='dot'), row=3, col=1)

    fig.update_layout(
        title=dict(
            text=f'{ticker} Last 180 Days: Price, Bollinger Bands, Relative Strength, and RSI',
            x=0.01,
            xanchor='left',
        ),
        legend=dict(x=0.01, y=1.08, orientation='h'),
        height=900,
        xaxis_rangeslider_visible=False,
    )

    fig.update_yaxes(title_text='Price ($)', row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text='Trading volume', row=1, col=1, secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text=f'{ticker}/{benchmark} ratio', row=2, col=1)
    fig.update_yaxes(title_text='RSI (14)', row=3, col=1, range=[0, 100])
    fig.update_xaxes(title_text='Date', row=3, col=1)

    return fig


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 stock_180.py <ticker>")

    ticker = sys.argv[1].upper()
    benchmark = 'SPY'

    stock_data = load_market_data(ticker, fallback_base_level=100.0, period='180d', fallback_periods=180)
    benchmark_data = load_market_data(benchmark, fallback_base_level=500.0, period='180d', fallback_periods=180)

    data = stock_data.copy()
    data['Benchmark_Close'] = benchmark_data['Close'].reindex(data.index).ffill().bfill()
    data['Relative_Ratio'] = data['Close'] / data['Benchmark_Close']

    fig = build_chart(data, ticker=ticker, benchmark=benchmark)

    try:
        fig.show()
    except Exception as err:
        output_path = Path(__file__).with_name(f"stock_chart_180_{ticker.lower()}.html")
        fig.write_html(output_path, include_plotlyjs='cdn')
        print(f"Interactive renderer unavailable ({err.__class__.__name__}). Chart saved to {output_path}")


if __name__ == '__main__':
    main()
