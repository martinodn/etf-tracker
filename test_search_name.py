import sys
sys.path.insert(0, '/Users/martino/.gemini/antigravity/scratch/etf_tracker')
from utils.finance import search_by_isin

ticker = "SWDA.MI"
print(f"Searching for {ticker}...")
results = search_by_isin(ticker)
print(f"Results: {results}")
