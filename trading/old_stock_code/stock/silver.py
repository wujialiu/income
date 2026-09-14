import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# Load silver futures data
symbol = 'SI=F'
data = yf.download(symbol, period='6mo', interval='1d')

# Compute 30-day rolling realized volatility
data['Return'] = np.log(data['Close'] / data['Close'].shift(1))
data['Realized Volatility'] = data['Return'].rolling(window=30).std() * np.sqrt(252)
data.dropna(inplace=True)

# Simulated monthly SIVL data
sivl_dates = pd.date_range(end=data.index[-1], periods=6, freq='ME')
sivl_values = [0.31, 0.29, 0.28, 0.34, 0.33, 0.32]
sivl_df = pd.DataFrame({'SIVL': sivl_values}, index=sivl_dates)
data['SIVL'] = sivl_df['SIVL'].reindex(data.index, method='ffill')

# Begin plotting
fig = go.Figure()

# Silver Price
fig.add_trace(go.Scatter(
    x=data.index, y=data['Close'], name='Price ($)', yaxis='y1',
    line=dict(color='blue')
))

# Volume
fig.add_trace(go.Bar(
    x=data.index, y=data['Volume'], name='Volume',
    marker_color='lightgray', yaxis='y2', opacity=0.4
))

# Realized Volatility
fig.add_trace(go.Scatter(
    x=data.index, y=data['Realized Volatility'], name='30D Realized Vol',
    yaxis='y3', line=dict(color='green')
))

# Implied Volatility (SIVL)
fig.add_trace(go.Scatter(
    x=data.index, y=data['SIVL'], name='Implied Vol (SIVL)',
    yaxis='y3', line=dict(color='orange', dash='dot'), mode='lines+markers'
))

# Layout with 3 axes
fig.update_layout(
    title='Silver Futures: Price, Volume, Realized & Implied Volatility',
    xaxis=dict(title='Date'),
    yaxis=dict(title='Price ($)', side='left'),
    yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False),
    yaxis3=dict(title='Volatility', anchor='free', overlaying='y', side='left', position=0.05, showgrid=False),

    legend=dict(x=0.01, y=1.15, orientation='h'),
    xaxis_rangeslider_visible=True,
    height=650
)

fig.show()
