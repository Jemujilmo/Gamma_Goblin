"""US Stock ticker list for dashboard selector.

Data sources (all free):
- Nasdaq FTP: ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt
- NYSE GitHub: https://github.com/datasets/nyse-listings
- Or use this curated list of most-traded securities
"""

# Popular ETFs and stocks - highly liquid, good for options trading
POPULAR_TICKERS = [
    # Major Index ETFs
    ("SPY", "S&P 500 ETF"),
    ("QQQ", "Nasdaq 100 ETF"),
    ("IWM", "Russell 2000 ETF"),
    ("DIA", "Dow Jones ETF"),
    ("VTI", "Total Stock Market ETF"),
    
    # Sector ETFs
    ("XLF", "Financial Sector"),
    ("XLE", "Energy Sector"),
    ("XLK", "Technology Sector"),
    ("XLV", "Healthcare Sector"),
    ("XLI", "Industrial Sector"),
    
    # Volatility/Bonds
    ("VXX", "VIX Short-Term Futures"),
    ("UVXY", "Ultra VIX Short-Term"),
    ("TLT", "20+ Year Treasury"),
    
    # Mega Cap Tech (FAANG+)
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corp."),
    ("GOOGL", "Alphabet Inc."),
    ("AMZN", "Amazon.com Inc."),
    ("NVDA", "NVIDIA Corp."),
    ("TSLA", "Tesla Inc."),
    ("META", "Meta Platforms"),
    
    # Other Popular Stocks
    ("AMD", "Advanced Micro Devices"),
    ("NFLX", "Netflix Inc."),
    ("BABA", "Alibaba Group"),
    ("DIS", "Walt Disney Co."),
    ("JPM", "JPMorgan Chase"),
    ("BA", "Boeing Co."),
    ("GE", "General Electric"),
]


def get_ticker_list():
    """Returns list of (symbol, name) tuples for dropdown.
    
    Fetches complete Nasdaq + NYSE lists (~3000+ tickers).
    Falls back to popular list if fetch fails.
    """
    import time
    
    print("Fetching complete US stock ticker list...")
    start = time.time()
    
    all_tickers = []
    
    # Fetch Nasdaq tickers
    nasdaq = fetch_all_nasdaq_tickers()
    if nasdaq and len(nasdaq) > 30:  # Only use if we got real data
        all_tickers.extend(nasdaq)
        print(f"Loaded {len(nasdaq)} Nasdaq tickers")
    
    # Fetch NYSE tickers
    nyse = fetch_all_nyse_tickers()
    if nyse and len(nyse) > 30:
        all_tickers.extend(nyse)
        print(f"Loaded {len(nyse)} NYSE tickers")
    
    # Remove duplicates and sort
    if all_tickers:
        # Use dict to deduplicate by symbol
        unique = {}
        for symbol, name in all_tickers:
            if symbol not in unique:
                unique[symbol] = name
        
        all_tickers = [(s, n) for s, n in unique.items()]
        all_tickers.sort(key=lambda x: x[0])
        
        print(f"Total unique tickers: {len(all_tickers)} (loaded in {time.time()-start:.1f}s)")
        return all_tickers
    
    # Fallback to popular list
    print("Failed to fetch full list, using popular tickers only")
    return POPULAR_TICKERS


def fetch_all_nasdaq_tickers():
    """
    Download full Nasdaq ticker list from official source.
    
    Returns list of (symbol, name) tuples
    """
    import requests
    
    try:
        # Nasdaq official API (updated daily)
        url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25000&offset=0&download=true"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            # Fallback to FTP text file
            return fetch_nasdaq_ftp()
        
        data = response.json()
        if not data or 'data' not in data or 'rows' not in data['data']:
            return fetch_nasdaq_ftp()
        
        tickers = []
        for row in data['data']['rows']:
            symbol = row.get('symbol', '').strip()
            name = row.get('name', '').strip()
            
            # Filter out weird symbols
            if symbol and not symbol.startswith('^') and len(symbol) <= 6:
                if '.' not in symbol and '$' not in symbol:  # Remove warrants/special securities
                    tickers.append((symbol, name))
        
        return tickers if tickers else fetch_nasdaq_ftp()
        
    except Exception as e:
        print(f"Nasdaq API failed: {e}, trying FTP...")
        return fetch_nasdaq_ftp()


def fetch_nasdaq_ftp():
    """Fallback FTP source for Nasdaq tickers"""
    import requests
    
    try:
        # FTP mirror on GitHub (updated regularly)
        url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/master/data/nasdaq-listed.csv"
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        
        tickers = []
        lines = response.text.split('\n')
        
        # Skip header
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 2:
                symbol = parts[0].strip().strip('"')
                name = parts[1].strip().strip('"')
                
                if symbol and len(symbol) <= 6 and '.' not in symbol:
                    tickers.append((symbol, name))
        
        return tickers
        
    except Exception as e:
        print(f"Nasdaq FTP failed: {e}")
        return []


def fetch_all_nyse_tickers():
    """
    Fetch NYSE tickers from GitHub dataset.
    
    Returns list of (symbol, name) tuples
    """
    import requests
    
    try:
        url = "https://raw.githubusercontent.com/datasets/nyse-listings/master/data/nyse-listed.csv"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return []
        
        tickers = []
        lines = response.text.split('\n')
        
        # Skip header
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 2:
                symbol = parts[0].strip().strip('"')
                name = parts[1].strip().strip('"')
                
                if symbol and len(symbol) <= 5:
                    tickers.append((symbol, name))
        
        return tickers
        
    except Exception as e:
        print(f"Failed to fetch NYSE tickers: {e}")
        return []


if __name__ == '__main__':
    """Test ticker fetching"""
    print("Testing ticker list...")
    print(f"\nPopular tickers: {len(POPULAR_TICKERS)}")
    for symbol, name in POPULAR_TICKERS[:10]:
        print(f"  {symbol:6} - {name}")
    
    print("\n\nFetching all Nasdaq tickers...")
    nasdaq = fetch_all_nasdaq_tickers()
    print(f"Found {len(nasdaq)} Nasdaq tickers")
    
    print("\n\nFetching all NYSE tickers...")
    nyse = fetch_all_nyse_tickers()
    print(f"Found {len(nyse)} NYSE tickers")
    
    print(f"\n\nTotal tickers available: {len(nasdaq) + len(nyse)}")
