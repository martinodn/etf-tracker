import requests
import yfinance as yf
import pandas as pd

def search_by_isin(isin):
    """
    Searches for a ticker by ISIN using Yahoo Finance auto-complete API.
    Returns a list of dictionaries with 'symbol', 'longname', 'exchange'.
    """
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if 'quotes' in data:
            for quote in data['quotes']:
                results.append({
                    'symbol': quote.get('symbol'),
                    'longname': quote.get('longname', quote.get('shortname', 'Unknown')),
                    'exchange': quote.get('exchDisp', quote.get('exchange', 'Unknown')),
                    'type': quote.get('quoteType', 'Unknown')
                })
        return results
    except Exception as e:
        print(f"Error searching ISIN {isin}: {e}")
        return []

def get_etf_data(ticker_symbol, period="1y", change_period="1d"):
    """
    Fetches current data and historical history for a given ticker.
    Tries to append common suffixes if the raw ticker fails.
    
    Args:
        ticker_symbol: The ticker to fetch
        period: Historical data period for chart (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        change_period: Period for calculating percentage change (1d, 1mo, 3mo, 6mo, 1y)
    """
    suffixes_to_try = ["", ".DE", ".MI", ".L", ".PA", ".AS"]
    
    for suffix in suffixes_to_try:
        current_symbol = f"{ticker_symbol}{suffix}"
        try:
            ticker = yf.Ticker(current_symbol)
            
            # Try to get info/price to verify validity
            # fast_info is usually reliable for checking existence
            try:
                info = ticker.fast_info
                current_price = info.last_price
                if current_price is None:
                    raise ValueError("No price data")
            except:
                # If fast_info fails, try history
                hist_check = ticker.history(period="1d")
                if hist_check.empty:
                    continue # Try next suffix
                current_price = hist_check['Close'].iloc[-1]
                info = ticker.fast_info # Still needed for currency if possible

            # Get history for the change period
            change_hist = ticker.history(period=change_period)
            if not change_hist.empty and len(change_hist) > 1:
                previous_price = change_hist['Close'].iloc[0]
                change = current_price - previous_price
                pct_change = (change / previous_price) * 100 if previous_price else 0
            else:
                # Fallback to previous close if change_period fails
                previous_close = info.previous_close
                change = current_price - previous_close if current_price and previous_close else 0
                pct_change = (change / previous_close) * 100 if previous_close else 0
            
            # Get history for charts
            history = ticker.history(period=period)
            
            # Try to get the long name
            try:
                ticker_info = ticker.info
                long_name = ticker_info.get('longName', current_symbol)
            except:
                long_name = current_symbol
            
            return {
                'symbol': current_symbol, # Return the working symbol
                'name': long_name,
                'current_price': current_price,
                'change': change,
                'pct_change': pct_change,
                'history': history,
                'currency': info.currency
            }
            
        except Exception:
            continue # Try next suffix

    print(f"Error fetching data for {ticker_symbol}: All suffixes failed.")
    return None

def get_comparative_data(tickers, start_date):
    """
    Fetches historical closing prices for a list of tickers from a start date.
    Returns a DataFrame with normalized performance (percentage change from start).
    """
    if not tickers:
        return pd.DataFrame()
    
    data = {}
    
    for ticker_symbol in tickers:
        # We need to resolve the symbol again because the portfolio might have the short name
        # but we need the one that works with yfinance (with suffix)
        # However, usually we store the resolved symbol in the portfolio/watchlist.
        # Let's assume the tickers passed are already resolved or try to resolve them.
        
        # Simple resolution logic similar to get_etf_data
        suffixes_to_try = ["", ".DE", ".MI", ".L", ".PA", ".AS"]
        found = False
        
        for suffix in suffixes_to_try:
            # If ticker already has a dot, maybe don't append suffix unless it failed?
            # But get_etf_data logic is robust. Let's try to use the ticker as is first if it has a dot.
            if "." in ticker_symbol and suffix == "":
                 current_symbol = ticker_symbol
            elif "." in ticker_symbol:
                 continue # Don't add another suffix if one exists
            else:
                 current_symbol = f"{ticker_symbol}{suffix}"
            
            try:
                t = yf.Ticker(current_symbol)
                hist = t.history(start=start_date)
                
                if not hist.empty:
                    # Normalize: (Price / Start_Price) - 1 * 100
                    start_price = hist['Close'].iloc[0]
                    if start_price > 0:
                        data[ticker_symbol] = (hist['Close'] / start_price - 1) * 100
                        found = True
                        break
            except:
                continue
        
        if not found:
            print(f"Could not fetch history for {ticker_symbol}")

    return pd.DataFrame(data)
