import pandas as pd
from utils.portfolio import calculate_performance

# Mock portfolio data
portfolio_data = [
    {'Date': '2025-01-01', 'Ticker': 'SWDA.MI', 'Price': 70.0, 'Quantity': 10},
    {'Date': '2025-02-01', 'Ticker': 'SWDA.MI', 'Price': 80.0, 'Quantity': 5}, # Avg Price should be (700+400)/15 = 73.33
    {'Date': '2025-01-15', 'Ticker': 'SXR8.DE', 'Price': 400.0, 'Quantity': 1}
]
df = pd.DataFrame(portfolio_data)

# Mock current prices
current_prices = {
    'SWDA.MI': 90.0,
    'SXR8.DE': 420.0
}

print("Testing Portfolio Calculation...")
results = calculate_performance(df, current_prices)

print("\nResults:")
print(results[['Ticker', 'Quantity', 'Avg Price', 'Current Price', 'Gain/Loss', 'Gain/Loss %']])

# Expected for SWDA.MI:
# Qty: 15
# Avg Price: 73.333...
# Invested: 1100
# Current Value: 15 * 90 = 1350
# Gain: 250
# Gain %: (250/1100)*100 = 22.72%

# Expected for SXR8.DE:
# Qty: 1
# Avg Price: 400
# Invested: 400
# Current Value: 420
# Gain: 20
# Gain %: 5%
