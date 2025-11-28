import pandas as pd
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

PORTFOLIO_FILE = "portfolio.csv"  # Fallback
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_gsheets_client():
    """Initialize Google Sheets client if credentials are available."""
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            credentials_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
            return gspread.authorize(creds)
    except:
        pass
    return None

def load_portfolio():
    """Loads the portfolio from Google Sheets or CSV fallback."""
    expected_cols = ['Date', 'ISIN', 'Ticker', 'Price', 'Quantity']
    
    # Try Google Sheets first
    client = get_gsheets_client()
    if client:
        try:
            import streamlit as st
            sheet_url = st.secrets.get("PORTFOLIO_SHEET_URL", "")
            if sheet_url:
                sheet = client.open_by_url(sheet_url)
                worksheet = sheet.get_worksheet(0)
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                if not df.empty and all(col in df.columns for col in expected_cols):
                    return df
        except Exception as e:
            print(f"Error loading from Google Sheets: {e}")
    
    # Fallback to CSV
    if os.path.exists(PORTFOLIO_FILE):
        try:
            df = pd.read_csv(PORTFOLIO_FILE)
            if not all(col in df.columns for col in expected_cols):
                return pd.DataFrame(columns=expected_cols)
            return df
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    else:
        return pd.DataFrame(columns=expected_cols)

def save_portfolio(df):
    """Saves the portfolio DataFrame to Google Sheets or CSV fallback."""
    # Validate DataFrame before saving
    if df is None:
        print("Error: DataFrame is None, skipping save")
        return
    
    # Try Google Sheets first
    client = get_gsheets_client()
    if client:
        try:
            import streamlit as st
            sheet_url = st.secrets.get("PORTFOLIO_SHEET_URL", "")
            if sheet_url:
                sheet = client.open_by_url(sheet_url)
                worksheet = sheet.get_worksheet(0)
                
                # Only clear and update if we have valid data
                if not df.empty:
                    # Convert to native Python types to avoid JSON serialization errors
                    # and handle dates as strings
                    df_export = df.copy()
                    for col in df_export.columns:
                        if pd.api.types.is_numeric_dtype(df_export[col]):
                            df_export[col] = df_export[col].apply(lambda x: float(x) if pd.notnull(x) else 0)
                        else:
                            df_export[col] = df_export[col].astype(str)
                            
                    worksheet.clear()
                    worksheet.update([df_export.columns.values.tolist()] + df_export.values.tolist())
                else:
                    # If DataFrame is empty, just clear data rows but keep headers
                    worksheet.clear()
                    worksheet.update([['Date', 'ISIN', 'Ticker', 'Price', 'Quantity']])
                return
        except Exception as e:
            print(f"Error saving to Google Sheets: {e}")
    
    # Fallback to CSV
    df.to_csv(PORTFOLIO_FILE, index=False)

def add_transaction(date, isin, ticker, price, quantity):
    """Adds a transaction to the portfolio."""
    # Prepare row data
    row_data = {
        'Date': str(date), # Ensure string for JSON serialization
        'ISIN': str(isin),
        'Ticker': str(ticker),
        'Price': float(price),
        'Quantity': float(quantity)
    }
    
    # Try Google Sheets append first (safer than rewrite)
    client = get_gsheets_client()
    if client:
        try:
            import streamlit as st
            sheet_url = st.secrets.get("PORTFOLIO_SHEET_URL", "")
            if sheet_url:
                sheet = client.open_by_url(sheet_url)
                worksheet = sheet.get_worksheet(0)
                
                # Ensure correct order: Date, ISIN, Ticker, Price, Quantity
                values = [row_data['Date'], row_data['ISIN'], row_data['Ticker'], row_data['Price'], row_data['Quantity']]
                worksheet.append_row(values)
                
                # Return updated portfolio
                return load_portfolio()
        except Exception as e:
            print(f"Error appending to Google Sheets: {e}")

    # Fallback: Load, Concat, Save (Rewrite)
    df = load_portfolio()
    new_row = pd.DataFrame([row_data])
    df = pd.concat([df, new_row], ignore_index=True)
    save_portfolio(df)
    return df

def calculate_performance(portfolio_df, current_prices):
    """
    Calculates performance metrics for the portfolio.
    current_prices: dict {ticker: price}
    """
    if portfolio_df.empty:
        return pd.DataFrame()
    
    # Group by Ticker to get weighted average price and total quantity
    summary = []
    
    for ticker, group in portfolio_df.groupby('Ticker'):
        total_qty = group['Quantity'].sum()
        if total_qty == 0:
            continue
            
        # Calculate average buy price
        # (Price * Quantity).sum() / Total Quantity
        avg_price = (group['Price'] * group['Quantity']).sum() / total_qty
        
        current_price = current_prices.get(ticker, 0)
        
        current_value = total_qty * current_price
        invested_value = total_qty * avg_price
        
        gain_loss = current_value - invested_value
        gain_loss_pct = (gain_loss / invested_value) * 100 if invested_value != 0 else 0
        
        summary.append({
            'Ticker': ticker,
            'Quantity': total_qty,
            'Buy Price': avg_price,
            'Current Price': current_price,
            'Invested Value': invested_value,
            'Current Value': current_value,
            'Gain/Loss': gain_loss,
            'Gain/Loss %': gain_loss_pct
        })
        
    return pd.DataFrame(summary)

def calculate_historical_performance(portfolio_df, price_history_df):
    """
    Calculates daily absolute gain/loss history.
    portfolio_df: DataFrame with transactions
    price_history_df: DataFrame with daily close prices for all tickers (index=Date)
    """
    if portfolio_df.empty or price_history_df.empty:
        return pd.DataFrame()
        
    # Ensure Date is datetime
    portfolio_df = portfolio_df.copy()
    portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
    
    # Sort transactions by date
    portfolio_df = portfolio_df.sort_values('Date')
    
    daily_stats = []
    
    # Iterate through each day in price history
    for date in price_history_df.index:
        # Filter transactions up to this date
        # Convert date to Timestamp to ensure compatible comparison
        date_ts = pd.Timestamp(date)
        mask = portfolio_df['Date'] <= date_ts
        current_transactions = portfolio_df[mask]
        
        if current_transactions.empty:
            continue
            
        # Calculate holdings and invested value
        holdings = {}
        invested_value = 0.0
        
        for _, row in current_transactions.iterrows():
            ticker = row['Ticker']
            qty = row['Quantity']
            price = row['Price']
            
            holdings[ticker] = holdings.get(ticker, 0) + qty
            invested_value += (price * qty)
            
        # Calculate current market value
        current_market_value = 0.0
        for ticker, qty in holdings.items():
            if ticker in price_history_df.columns:
                # Get price for this date
                # If NaN (e.g. holiday for this specific ticker?), use 0 or prev?
                # yfinance usually aligns dates.
                daily_price = price_history_df.loc[date, ticker]
                if pd.notnull(daily_price):
                    current_market_value += (qty * daily_price)
        
        gain_loss = current_market_value - invested_value
        
        daily_stats.append({
            'Date': date,
            'Invested Value': invested_value,
            'Market Value': current_market_value,
            'Gain/Loss': gain_loss
        })
        
    return pd.DataFrame(daily_stats).set_index('Date')
