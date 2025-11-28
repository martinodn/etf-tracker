from utils.finance import search_by_isin

isin = "IE00B4L5Y983" # SWDA
print(f"Searching for {isin}...")
results = search_by_isin(isin)
print(f"Results: {results}")

isin2 = "US0378331005" # Apple
print(f"Searching for {isin2}...")
results2 = search_by_isin(isin2)
print(f"Results: {results2}")
