import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Step 1: Fetch S&P 500 tickers
sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
sp500_table = pd.read_html(sp500_url, header=0)[0]
tickers = sp500_table['Symbol'].tolist()
names = dict(zip(sp500_table['Symbol'], sp500_table['Security']))
sectors = dict(zip(sp500_table['Symbol'], sp500_table['GICS Sector']))

# Step 2: Fetch market caps
data = []
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap')
        if market_cap:
            data.append((ticker, names.get(ticker), sectors.get(ticker), market_cap/100000000))
    except Exception:
        continue

# Step 3: Create DataFrame
df = pd.DataFrame(data, columns=['Ticker', 'Company', 'Sector', 'MarketCap'])
df.dropna(inplace=True)
df.sort_values(by='MarketCap', ascending=False, inplace=True)

# Step 4: Export to CSV
df.to_csv("top_sp500_by_market_cap.csv", index=False)

# Step 5: Plot top 10 companies
top10 = df.head(10)
plt.figure(figsize=(12, 6))
plt.barh(top10['Company'], top10['MarketCap'] / 1e12, color='skyblue')
plt.xlabel('Market Cap (Trillions USD)')
plt.title('Top 10 S&P 500 Companies by Market Cap')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("top10_market_cap_chart.png")
plt.show()
