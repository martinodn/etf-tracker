import yfinance as yf

tickers_to_test = ["SXR8", "SXR8.DE", "SXR8.MI"]

for t in tickers_to_test:
    print(f"Testing {t}...")
    try:
        ticker = yf.Ticker(t)
        # Try to fetch fast_info first
        price = ticker.fast_info.last_price
        print(f"  [fast_info] Price: {price}")
        
        # Try history
        hist = ticker.history(period="1d")
        if not hist.empty:
            print(f"  [history] Last Close: {hist['Close'].iloc[-1]}")
        else:
            print("  [history] Empty")
            
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 20)
