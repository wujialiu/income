import yfinance as yf
import pandas as pd

def get_top_tickers_by_cap(limit=1000):
    # Fetching data for S&P 500 companies as an example; adjust as per actual requirement
    sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500_table = pd.read_html(sp500_url, header=0)[0]
    tickers = sp500_table['Symbol'].tolist()
    
    # Fetching market cap data
    data = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap', None)
        data.append((ticker, market_cap))
    
    # Creating DataFrame and sorting by market cap
    df = pd.DataFrame(data, columns=['Ticker', 'MarketCap'])
    df.dropna(inplace=True)  # Remove any rows without market cap data
    df.sort_values(by='MarketCap', ascending=False, inplace=True)
    
    # Return top 'limit' tickers by market cap
    return df.head(limit)

# Example usage
top_tickers = get_top_tickers_by_cap(1000)
print(top_tickers)

