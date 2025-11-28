import sys
sys.path.insert(0, '/Users/martino/.gemini/antigravity/scratch/etf_tracker')

from utils import portfolio

print("Testing portfolio loading...")
df = portfolio.load_portfolio()
print(f"\nDataFrame shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nData:\n{df}")
print(f"\nData types:\n{df.dtypes}")
