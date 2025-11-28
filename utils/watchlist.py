import gspread
from google.oauth2.service_account import Credentials

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

def load_watchlist():
    """Load watchlist from Google Sheets (Sheet 2) or return empty list."""
    client = get_gsheets_client()
    if client:
        try:
            import streamlit as st
            sheet_url = st.secrets.get("PORTFOLIO_SHEET_URL", "")
            if sheet_url:
                sheet = client.open_by_url(sheet_url)
                # Try to get the second worksheet (watchlist)
                try:
                    worksheet = sheet.worksheet("Watchlist")
                except:
                    # Create it if it doesn't exist
                    worksheet = sheet.add_worksheet(title="Watchlist", rows=100, cols=1)
                    worksheet.update('A1', [['Ticker']])
                
                data = worksheet.col_values(1)[1:]  # Skip header
                return [ticker for ticker in data if ticker.strip()]
        except Exception as e:
            print(f"Error loading watchlist from Google Sheets: {e}")
    
    return []

def save_watchlist(watchlist):
    """Save watchlist to Google Sheets (Sheet 2)."""
    client = get_gsheets_client()
    if client:
        try:
            import streamlit as st
            sheet_url = st.secrets.get("PORTFOLIO_SHEET_URL", "")
            if sheet_url:
                sheet = client.open_by_url(sheet_url)
                try:
                    worksheet = sheet.worksheet("Watchlist")
                except:
                    worksheet = sheet.add_worksheet(title="Watchlist", rows=100, cols=1)
                
                worksheet.clear()
                worksheet.update('A1', [['Ticker']] + [[ticker] for ticker in watchlist])
                return True
        except Exception as e:
            print(f"Error saving watchlist to Google Sheets: {e}")
    
    return False
